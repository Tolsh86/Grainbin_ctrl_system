"""进度款审核业务逻辑：ProgressPaymentReview CRUD + 状态变更 (Phase2 改造)

Phase2 变更：
- 适配新字段（period_id, contract_id 必填）
- 状态值对齐 draft/submitted/reviewed
- 创建审核时自动复制合同费用分项模板为 fee_items 快照
- PUT 更新支持嵌套 fee_items 更新（报送值 + 审定值共用）
- 确认审定时汇总 fee_items → 写台账 → 联动期次状态
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.progress_review import ProgressPaymentReview
from app.models.review_fee_item import ReviewFeeItem
from app.models.contract_fee_item import ContractFeeItem
from app.models.contract import ContractMonthlyDetail
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewStatusUpdate
from app.core.exceptions import NotFound, BadRequest
from app.utils.db import paginate
from app.services.period_service import _auto_transition_period


# ── 审核状态转移规则 (Phase2: draft/submitted/reviewed) ──
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["submitted"],                         # 草稿 → 已报送
    "submitted": ["reviewed", "draft"],             # 已报送 → 已审核 / 回退草稿
    "reviewed": ["draft"],                          # 已审核 → 回退草稿
}


def _validate_status_transition(current: str, target: str) -> None:
    """校验状态转移是否合法。"""
    if current == target:
        return
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise BadRequest(
            detail=f"状态转移不合法：{current} → {target}。允许的目标：{allowed}"
        )


# ═══════════════════════════════════════════════════════════════════
# 进度款审核 CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_reviews(
    db: AsyncSession,
    project_id: uuid.UUID | None = None,
    period_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    review_type: str | None = None,
    audit_status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[ProgressPaymentReview], int]:
    """分页查询审核记录，支持按项目或期次筛选。"""
    conditions = []
    if project_id:
        conditions.append(ProgressPaymentReview.project_id == project_id)
    if period_id:
        conditions.append(ProgressPaymentReview.period_id == period_id)

    if not conditions:
        raise BadRequest(detail="必须提供 project_id 或 period_id 进行查询")

    stmt = select(ProgressPaymentReview).where(*conditions).order_by(
        ProgressPaymentReview.created_at.desc()
    )
    count_stmt = select(func.count(ProgressPaymentReview.id)).where(*conditions)

    if review_type:
        stmt = stmt.where(ProgressPaymentReview.review_type == review_type)
        count_stmt = count_stmt.where(ProgressPaymentReview.review_type == review_type)
    if audit_status:
        stmt = stmt.where(ProgressPaymentReview.audit_status == audit_status)
        count_stmt = count_stmt.where(ProgressPaymentReview.audit_status == audit_status)
    if keyword:
        like = f"%{keyword}%"
        cond = (ProgressPaymentReview.applicant_unit.ilike(like) |
                ProgressPaymentReview.review_type.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    return await paginate(db, stmt, page=page, page_size=page_size, model=ProgressPaymentReview, count_stmt=count_stmt, auto_active=False)


async def get_review(db: AsyncSession, review_id: uuid.UUID) -> ProgressPaymentReview | None:
    """按 ID 获取审核记录（含 fee_items）。"""
    result = await db.execute(
        select(ProgressPaymentReview)
        .options(selectinload(ProgressPaymentReview.fee_items))
        .where(ProgressPaymentReview.id == review_id)
    )
    return result.scalar_one_or_none()


async def create_review(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ReviewCreate,
    user_id: uuid.UUID | None = None,
) -> ProgressPaymentReview:
    """创建一条审核记录（含费用分项快照）。

    自动从 data.fee_items 创建 ReviewFeeItem 子记录。
    """
    review = ProgressPaymentReview(
        project_id=project_id,
        contract_id=data.contract_id,
        period_id=data.period_id,
        review_type=data.review_type,
        applicant_unit=data.applicant_unit,
        contract_amount=data.contract_amount,
        cumulative_reported_output=data.cumulative_reported_output,
        current_audited_output=data.current_audited_output,
        cumulative_audited_output=data.cumulative_audited_output,
        cumulative_audited_payable=data.cumulative_audited_payable,
        extra_fields=data.extra_fields,
        remark=data.remark,
        tax_rate=data.tax_rate,
        submit_date=data.submit_date,
    )
    if user_id:
        review.audited_by = user_id

    db.add(review)
    await db.flush()

    # 创建费用分项快照
    for fi_data in data.fee_items:
        fee_item = ReviewFeeItem(
            review_id=review.id,
            fee_item_id=fi_data.fee_item_id,
            item_name=fi_data.item_name,
            payment_ratio=fi_data.payment_ratio,
            reported_amount=fi_data.reported_amount or 0,
            reviewed_amount=fi_data.reviewed_amount or 0,
            remark=fi_data.remark,
        )
        db.add(fee_item)

    await db.flush()
    await db.refresh(review)
    logger.info(f"审核记录创建成功: project={project_id}, period={data.period_id}, type={data.review_type}, fee_items={len(data.fee_items)}")
    return review


async def update_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    data: ReviewUpdate,
) -> ProgressPaymentReview | None:
    """更新审核记录（支持嵌套费用分项值更新）。

    1. 更新主表字段
    2. 如果提供了 fee_items，逐个匹配 id 更新子表
    3. 自动触发期次状态 draft → in_progress
    """
    review = await get_review(db, review_id)
    if not review:
        return None

    # 分离 fee_items 和主表字段
    update_data = data.model_dump(exclude_unset=True)
    fee_items_data = update_data.pop("fee_items", None)

    # 更新主表
    for key, value in update_data.items():
        setattr(review, key, value)

    # 更新费用分项子表
    if fee_items_data is not None:
        for fi_data in fee_items_data:
            fi_id = fi_data.get("id")
            if not fi_id:
                continue
            # 查找并更新
            for fi in review.fee_items:
                if fi.id == fi_id:
                    if "reported_amount" in fi_data and fi_data["reported_amount"] is not None:
                        fi.reported_amount = fi_data["reported_amount"]
                    if "reviewed_amount" in fi_data and fi_data["reviewed_amount"] is not None:
                        # 审定值不能为负数
                        if fi_data["reviewed_amount"] < 0:
                            raise BadRequest(detail=f"审定金额不能为负数：{fi.item_name}")
                        fi.reviewed_amount = fi_data["reviewed_amount"]
                    if "remark" in fi_data:
                        fi.remark = fi_data.get("remark")
                    break

    await db.flush()

    # 自动推进期次状态（draft → in_progress）
    if review.period_id:
        await _auto_transition_period(db, review.period_id)

    await db.refresh(review)
    return review


async def update_review_status(
    db: AsyncSession,
    review_id: uuid.UUID,
    data: ReviewStatusUpdate,
) -> ProgressPaymentReview | None:
    """更新审核状态（带状态转移校验）。

    draft → submitted → reviewed（支持回退到 draft）
    确认审核（→ reviewed）时：
      1. 汇总 fee_items → 写入 current_audited_output / cumulative_audited_payable
      2. 自动写入月度台账 t_contract_monthly_detail
      3. 自动推进期次状态（in_progress → reviewed，当所有 review 都已确认）
    """
    review = await get_review(db, review_id)
    if not review:
        return None

    _validate_status_transition(review.audit_status, data.audit_status)

    review.audit_status = data.audit_status

    if data.audit_status == "reviewed":
        review.audited_at = datetime.now(UTC)
        # 汇总 fee_items 写入冗余汇总字段
        await _sync_review_totals(db, review)
        # 写入月度台账
        await _write_monthly_ledger(db, review)
    elif data.audit_status == "draft":
        review.audited_at = None

    await db.flush()

    # 自动推进期次状态
    if review.period_id:
        await _auto_transition_period(db, review.period_id)

    await db.refresh(review)
    logger.info(f"审核状态更新: id={review_id}, → {data.audit_status}")
    return review


async def _sync_review_totals(db: AsyncSession, review: ProgressPaymentReview) -> None:
    """从 fee_items 汇总写入 current_audited_output 和 cumulative_audited_payable。"""
    total_output = 0
    total_payable = 0
    for fi in review.fee_items:
        total_output += fi.reviewed_amount or 0
        total_payable += int((fi.reviewed_amount or 0) * (fi.payment_ratio or 0))

    review.current_audited_output = total_output
    review.cumulative_audited_payable = total_payable
    await db.flush()


async def _write_monthly_ledger(
    db: AsyncSession, review: ProgressPaymentReview
) -> None:
    """确认审定时自动写入月度台账 t_contract_monthly_detail。

    按月 × 合同去重：同一(contract_no, detail_month)存在则更新，否则新增。
    """
    from app.models.reporting_period import ReportingPeriod

    # 获取期次月份
    period = await db.get(ReportingPeriod, review.period_id)
    if not period:
        logger.warning(f"期次不存在，跳过台账写入: period_id={review.period_id}")
        return

    try:
        detail_month = date.fromisoformat(period.period_month + "-01")
    except (ValueError, TypeError):
        logger.warning(f"期次月份格式异常: {period.period_month}")
        return

    # 获取合同编号
    from app.models.contract import Contract
    contract = await db.get(Contract, review.contract_id)
    contract_no = contract.contract_no if contract else "UNKNOWN"

    # 构建费用分项明细 JSONB
    cost_items_detail = {
        "items": [
            {
                "fee_item_id": str(fi.fee_item_id) if fi.fee_item_id else None,
                "name": fi.item_name,
                "reported_amount": fi.reported_amount or 0,
                "reviewed_amount": fi.reviewed_amount or 0,
                "payment_ratio": float(fi.payment_ratio) if fi.payment_ratio else 0,
                "payable": int((fi.reviewed_amount or 0) * (fi.payment_ratio or 0)),
            }
            for fi in review.fee_items
        ]
    }

    # 查找是否已有同合同+同月的台账记录
    result = await db.execute(
        select(ContractMonthlyDetail).where(
            ContractMonthlyDetail.contract_id == review.contract_id,
            ContractMonthlyDetail.detail_month == detail_month,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # 更新已有记录
        existing.output_amount = review.current_audited_output
        existing.source = "auto"
        existing.status = "confirmed"
        existing.cost_items_detail = cost_items_detail
        logger.info(f"台账更新: contract={contract_no} month={period.period_month}")
    else:
        # 新增
        detail = ContractMonthlyDetail(
            contract_id=review.contract_id,
            contract_no=contract_no,
            detail_month=detail_month,
            output_amount=review.current_audited_output,
            source="auto",
            status="confirmed",
            cost_items_detail=cost_items_detail,
        )
        db.add(detail)
        logger.info(f"台账写入: contract={contract_no} month={period.period_month}")

    await db.flush()


async def copy_fee_items_from_contract(
    db: AsyncSession, contract_id: uuid.UUID
) -> list[dict]:
    """从合同的费用分项模板生成快照数据（用于创建审核草稿时填充 fee_items）。

    Returns:
        list of dicts 可直接传给 ReviewFeeItemCreate。
    """
    result = await db.execute(
        select(ContractFeeItem)
        .where(ContractFeeItem.contract_id == contract_id)
        .order_by(ContractFeeItem.sort_order)
    )
    templates = result.scalars().all()
    return [
        {
            "fee_item_id": t.id,
            "item_name": t.item_name,
            "payment_ratio": float(t.current_ratio) if t.current_ratio else None,
            "reported_amount": 0,
            "reviewed_amount": 0,
            "remark": None,
        }
        for t in templates
    ]
