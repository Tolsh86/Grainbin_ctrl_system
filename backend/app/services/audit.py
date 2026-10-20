"""审核工作台业务逻辑

合同审核模式分叉逻辑：
- review_mode = daily_aggregate → 建安合同：聚合 DataRow 日报分项
- review_mode = node_judge → 咨询合同：合同本身即费用分项，聚合 PaymentStage 节点累计
- review_mode = none → 无产值，不参与审核工作台
"""

from __future__ import annotations

import uuid
from datetime import date

from loguru import logger
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound, BadRequest
from app.models.contract import Contract, ContractMonthlyDetail, ContractPaymentStage
from app.models.data_row import DataRow
from app.schemas.audit import (
    AuditSummaryResponse,
    ConstructionAggItem,
    ConstructionAuditResponse,
    ConsultingFeeItemDetail,
    ConsultingFeeNode,
    ConsultingAuditResponse,
)
from app.services.monthly import upsert_monthly_detail


# ═══════════════════════════════════════════════════════════════════
# 1. 当月合同审核概览
# ═══════════════════════════════════════════════════════════════════

async def get_audit_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
    month: date,
) -> AuditSummaryResponse:
    """获取项目当月合同待审/已审数量概览。

    统计逻辑：
    - total_contracts: 项目下未删除合同总数
    - pending_count: 当月月度明细 status=pending 的合同数
    - confirmed_count: 当月月度明细 status=confirmed 的合同数
    """
    total = await db.scalar(
        select(func.count(Contract.id)).where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
        )
    )

    detail_counts = await db.execute(
        select(
            ContractMonthlyDetail.status,
            func.count(ContractMonthlyDetail.id.distinct()),
        )
        .join(Contract, Contract.contract_no == ContractMonthlyDetail.contract_no)
        .where(
            Contract.project_id == project_id,
            Contract.deleted_at.is_(None),
            ContractMonthlyDetail.detail_month == month,
        )
        .group_by(ContractMonthlyDetail.status)
    )
    status_map = {r[0]: r[1] for r in detail_counts.all()}

    return AuditSummaryResponse(
        total_contracts=total or 0,
        pending_count=status_map.get("pending", 0),
        confirmed_count=status_map.get("confirmed", 0),
    )


# ═══════════════════════════════════════════════════════════════════
# 2. 合同审核详情（按合同类型分叉）
# ═══════════════════════════════════════════════════════════════════

async def get_audit_contract_detail(
    db: AsyncSession,
    contract_id: uuid.UUID,
    month: date,
) -> ConstructionAuditResponse | ConsultingAuditResponse:
    """获取合同审核详情，按 review_mode 分发到对应处理逻辑。"""
    result = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.deleted_at.is_(None),
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFound(detail="合同不存在")

    if contract.review_mode == "daily_aggregate":
        return await _get_construction_detail(db, contract, month)
    if contract.review_mode == "node_judge":
        return await _get_consulting_detail(db, contract, month)

    raise BadRequest(
        detail=f"合同 review_mode '{contract.review_mode}' 不支持审核工作台"
    )


async def _get_construction_detail(
    db: AsyncSession,
    contract: Contract,
    month: date,
) -> ConstructionAuditResponse:
    """建安合同：按 DataRow 日报数据聚合分项产值。

    聚合维度：category + cost_sub_type + item_name + unit + unit_price
    汇总同一分项下所有 confirmed 状态的数据行。
    """
    rows = await db.execute(
        select(
            DataRow.category,
            DataRow.cost_sub_type,
            DataRow.item_name,
            DataRow.unit,
            DataRow.unit_price,
            func.coalesce(func.sum(DataRow.actual_quantity), 0).label("total_qty"),
            func.coalesce(func.sum(DataRow.amount), 0).label("total_amount"),
            func.count(DataRow.id).label("row_count"),
        )
        .where(
            DataRow.contract_id == contract.id,
            DataRow.deleted_at.is_(None),
            DataRow.status == "confirmed",
            extract("year", DataRow.data_date) == month.year,
            extract("month", DataRow.data_date) == month.month,
        )
        .group_by(
            DataRow.category,
            DataRow.cost_sub_type,
            DataRow.item_name,
            DataRow.unit,
            DataRow.unit_price,
        )
        .order_by(DataRow.cost_sub_type, DataRow.category)
    )

    items = [
        ConstructionAggItem(
            category=r.category,
            cost_sub_type=r.cost_sub_type,
            item_name=r.item_name,
            unit=r.unit,
            unit_price=r.unit_price,
            total_quantity=r.total_qty or 0,
            total_amount=r.total_amount or 0,
            row_count=r.row_count or 0,
        )
        for r in rows.all()
    ]

    total_output = sum(it.total_amount for it in items)

    # 查当月月度明细获取支付金额
    monthly = await db.scalar(
        select(ContractMonthlyDetail).where(
            ContractMonthlyDetail.contract_no == contract.contract_no,
            ContractMonthlyDetail.detail_month == month,
        )
    )

    return ConstructionAuditResponse(
        contract_id=contract.id,
        contract_no=contract.contract_no,
        review_mode=contract.review_mode,
        contract_amount=contract.contract_amount,
        detail_month=month,
        items=items,
        total_output=total_output,
        total_payable=monthly.payment_amount if monthly else 0,
    )


async def _get_consulting_detail(
    db: AsyncSession,
    contract: Contract,
    month: date,
) -> ConsultingAuditResponse:
    """咨询合同（N 记录模型）：合同本身就是一条费用分项。

    每条 Contract 记录对应一个独立结算单元（如监理/造价/结算），
    其所有支付节点的累计产值即为该分项的审定/报送数据。

    返回结构：
    - fee_items[*]: 单条，contract_desc 为名称，contract_amount 为金额
    - fee_items[*].nodes: 该合同下所有支付节点的阶段信息 + reported/reviewed 累计值
    """
    stages = await db.execute(
        select(ContractPaymentStage).where(
            ContractPaymentStage.contract_id == contract.id,
        ).order_by(ContractPaymentStage.stage_order)
    )
    stages_list = list(stages.scalars().all())

    nodes = [
        ConsultingFeeNode(
            node_name=s.node_name,
            stage_order=s.stage_order,
            stage_name=s.stage_name,
            agreed_ratio=s.agreed_ratio,
            agreed_amount=s.agreed_amount,
            reported_amount=s.reported_amount,
            reviewed_amount=s.reviewed_amount,
            is_completed=s.is_completed,
            triggered_at=s.triggered_at,
        )
        for s in stages_list
    ]

    cumulative_reported = sum((n.reported_amount or 0) for n in nodes)
    cumulative_reviewed = sum((n.reviewed_amount or 0) for n in nodes)

    fee_item_details = [ConsultingFeeItemDetail(
        fee_item_id="",
        name=contract.contract_desc or "",
        contract_amount=contract.contract_amount,
        agreed_ratio=None,
        nodes=nodes,
        cumulative_reported=cumulative_reported,
        cumulative_reviewed=cumulative_reviewed,
    )]

    return ConsultingAuditResponse(
        contract_id=contract.id,
        contract_no=contract.contract_no,
        review_mode=contract.review_mode,
        contract_amount=contract.contract_amount,
        detail_month=month,
        fee_items=fee_item_details,
        total_reported=cumulative_reported,
        total_reviewed=cumulative_reviewed,
    )


# ═══════════════════════════════════════════════════════════════════
# 3. 审核确认
# ═══════════════════════════════════════════════════════════════════

async def confirm_audit(
    db: AsyncSession,
    contract_id: uuid.UUID,
    detail_month: date,
    items: list[dict],
    status: str = "confirmed",
) -> ContractMonthlyDetail | None:
    """接收分项审定数据，校验后写入月度台账。

    校验规则：
    1. 合同必须存在
    2. 各分项 payable 之和不超过合同金额（contract_amount 为空时跳过）
    3. 各分项 ratio 在 [0, 1]

    写入策略：
    - 调用 upsert_monthly_detail 以 source="auto" 写入
    - 若已有 manual 记录，upsert_monthly_detail 会跳过并返回 None
    """
    result = await db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.deleted_at.is_(None),
        )
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise NotFound(detail="合同不存在")

    total_payable = 0
    total_output = 0

    for item in items:
        fi = item if isinstance(item, dict) else item.model_dump()
        ratio = float(fi.get("ratio", 0))
        if ratio < 0 or ratio > 1:
            raise BadRequest(
                detail=f"分项 '{fi.get('name', 'unknown')}' 比例无效: {ratio}"
            )
        total_payable += int(fi.get("payable", 0))
        total_output += int(fi.get("output", 0))

    if contract.contract_amount and total_payable > contract.contract_amount:
        raise BadRequest(
            detail=f"应付总额 {total_payable} 分超出合同金额 {contract.contract_amount} 分"
        )

    # 计算完成比例
    completed_ratio: float | None = None
    if contract.contract_amount and contract.contract_amount > 0:
        total_cumulative = total_output  # 本次为当月累计
        completed_ratio = round(total_cumulative / contract.contract_amount, 4)

    cost_items_detail = {"items": items}

    detail = await upsert_monthly_detail(
        db,
        contract_id=contract_id,
        detail_month=detail_month,
        payment_amount=total_payable,
        output_amount=total_output,
        completed_ratio=completed_ratio,
        cost_items_detail=cost_items_detail,
        status=status,
    )

    if detail is None:
        raise BadRequest(
            detail=f"合同 {contract.contract_no} 的 {detail_month} 已有人工审定数据，无法自动覆盖"
        )

    logger.info(
        f"审核确认: contract={contract.contract_no}, month={detail_month}, "
        f"output={total_output}, payable={total_payable}"
    )
    return detail
