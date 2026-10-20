"""报送期次业务逻辑 (Phase2)

核心流程：
1. 创建期次 → 写入期次-合同关联 → 遍历合同生成审核草稿（含费用分项快照）
2. 期次状态与审核记录联动
"""

from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reporting_period import ReportingPeriod, PeriodContract
from app.models.contract import Contract
from app.models.progress_review import ProgressPaymentReview
from app.models.review_fee_item import ReviewFeeItem
from app.models.contract_fee_item import ContractFeeItem
from app.core.exceptions import NotFound, BadRequest
from app.utils.db import paginate


# ── 期次状态转移规则 ──
# draft → in_progress（自动：任意 review 有数据变更时）
# in_progress → reviewed（自动：所有 review 都已 reviewed 时）
# reviewed → closed（手动：过控点"关闭本期"，不可逆）
PERIOD_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["in_progress"],       # 自动触发（不能手动）
    "in_progress": ["reviewed"],    # 自动触发（所有 review 确认后联动）
    "reviewed": ["closed"],         # 手动关闭
    "closed": [],                   # 终态
}

# 手动允许的状态转移（API 层面：reviewed→closed）
MANUAL_PERIOD_TRANSITIONS: dict[str, list[str]] = {
    "reviewed": ["closed"],
}


def _validate_period_transition(current: str, target: str) -> None:
    """手动状态转移校验（仅 reviewed → closed）。"""
    if current == target:
        return
    allowed = MANUAL_PERIOD_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise BadRequest(
            detail=f"期次状态转移不合法：{current} → {target}。允许的目标：{allowed}"
        )


async def _auto_transition_period(db: AsyncSession, period_id: uuid.UUID) -> None:
    """自动推进期次状态（内部调用，不校验手动转移规则）。

    - draft → in_progress：任意 review 有数据变更时
    - in_progress → reviewed：所有 review 都已 reviewed 时
    """
    period = await db.get(ReportingPeriod, period_id)
    if not period or period.status in ("closed",):
        return

    # 统计该期次下 review 状态分布
    from sqlalchemy import func as sa_func
    total = await db.execute(
        select(sa_func.count(ProgressPaymentReview.id)).where(
            ProgressPaymentReview.period_id == period_id
        )
    )
    total_count = total.scalar() or 0
    if total_count == 0:
        return

    reviewed_count = await db.execute(
        select(sa_func.count(ProgressPaymentReview.id)).where(
            ProgressPaymentReview.period_id == period_id,
            ProgressPaymentReview.audit_status == "reviewed",
        )
    )
    reviewed = reviewed_count.scalar() or 0

    if period.status == "draft":
        # draft → in_progress：任意 review 不再全是 draft 时
        draft_count = await db.execute(
            select(sa_func.count(ProgressPaymentReview.id)).where(
                ProgressPaymentReview.period_id == period_id,
                ProgressPaymentReview.audit_status == "draft",
            )
        )
        if (draft_count.scalar() or 0) < total_count:
            period.status = "in_progress"
            logger.info(f"期次自动推进: {period_id} draft → in_progress")
    elif period.status == "in_progress":
        # in_progress → reviewed：所有 review 都 reviewed
        if reviewed == total_count:
            period.status = "reviewed"
            logger.info(f"期次自动推进: {period_id} in_progress → reviewed")


# ═══════════════════════════════════════════════════════════════════
# 期次 CRUD
# ═══════════════════════════════════════════════════════════════════

async def get_periods(
    db: AsyncSession,
    project_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[ReportingPeriod], int]:
    """分页查询期次列表。"""
    conditions = [ReportingPeriod.project_id == project_id]
    if status:
        conditions.append(ReportingPeriod.status == status)

    stmt = select(ReportingPeriod).where(*conditions).order_by(ReportingPeriod.period_no.desc())
    count_stmt = select(func.count(ReportingPeriod.id)).where(*conditions)

    periods, total = await paginate(
        db, stmt, page=page, page_size=page_size, model=ReportingPeriod, count_stmt=count_stmt, auto_active=False
    )

    # 填充聚合统计
    for p in periods:
        p.contract_count = await _count_period_contracts(db, p.id)
        p.review_count = await _count_period_reviews(db, p.id)

    return periods, total


async def get_period(
    db: AsyncSession, period_id: uuid.UUID
) -> ReportingPeriod | None:
    """获取单个期次详情（含关联合同列表）。"""
    result = await db.execute(
        select(ReportingPeriod)
        .options(selectinload(ReportingPeriod.period_contracts))
        .where(ReportingPeriod.id == period_id)
    )
    period = result.scalar_one_or_none()
    if period:
        period.contract_count = len(period.period_contracts)
        period.review_count = await _count_period_reviews(db, period.id)
        # 动态属性：contract_ids
        period.contract_ids = [pc.contract_id for pc in period.period_contracts]
    return period


async def create_period(
    db: AsyncSession,
    project_id: uuid.UUID,
    period_month: str,
    period_no: int,
    contract_ids: list[uuid.UUID],
    remark: str | None = None,
) -> ReportingPeriod:
    """创建期次 + 关联合同 + 自动生成审核草稿。

    流程：
    1. 创建 t_reporting_periods 记录
    2. 为每个选中的合同创建 t_period_contracts 关联
    3. 为每个合同创建一条 draft 状态的 ProgressPaymentReview
    4. 为每条 review 复制该合同的费用分项模板为 ReviewFeeItem 快照
    """
    # 校验期次号唯一性
    existing = await db.execute(
        select(ReportingPeriod).where(
            ReportingPeriod.project_id == project_id,
            ReportingPeriod.period_no == period_no,
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequest(detail=f"项目下期次号 {period_no} 已存在")

    # 校验合同存在且属于该项目
    for cid in contract_ids:
        contract = await db.get(Contract, cid)
        if not contract:
            raise NotFound(detail=f"合同 {cid} 不存在")
        if contract.project_id != project_id:
            raise BadRequest(detail=f"合同 {cid} 不属于该项目")

    # 1. 创建期次
    period = ReportingPeriod(
        project_id=project_id,
        period_no=period_no,
        period_month=period_month,
        status="draft",
        remark=remark,
    )
    db.add(period)
    await db.flush()

    # 2. 创建合同关联
    for cid in contract_ids:
        pc = PeriodContract(period_id=period.id, contract_id=cid)
        db.add(pc)

    await db.flush()

    # 3. 为每个合同创建审核草稿 + 费用分项快照
    review_count = 0
    for cid in contract_ids:
        contract = await db.get(Contract, cid)
        if not contract:
            continue

        # 确定 review_type（从合同类型推断）
        review_type = _infer_review_type(contract)

        review = ProgressPaymentReview(
            project_id=project_id,
            contract_id=cid,
            period_id=period.id,
            review_type=review_type,
            applicant_unit=contract.supplier_name,
            contract_amount=contract.contract_amount or 0,
            audit_status="draft",
        )
        db.add(review)
        await db.flush()

        # 4. 复制费用分项模板为快照
        fee_templates = await db.execute(
            select(ContractFeeItem)
            .where(ContractFeeItem.contract_id == cid)
            .order_by(ContractFeeItem.sort_order)
        )
        for t in fee_templates.scalars():
            fee_snapshot = ReviewFeeItem(
                review_id=review.id,
                fee_item_id=t.id,
                item_name=t.item_name,
                payment_ratio=float(t.current_ratio) if t.current_ratio else None,
                reported_amount=0,
                reviewed_amount=0,
                remark=None,
            )
            db.add(fee_snapshot)

        review_count += 1

    await db.flush()
    await db.refresh(period)
    logger.info(
        f"期次创建成功: project={project_id}, period_no={period_no}, "
        f"contracts={len(contract_ids)}, reviews={review_count}"
    )
    return period


async def update_period(
    db: AsyncSession,
    period_id: uuid.UUID,
    period_month: str | None = None,
    contract_ids: list[uuid.UUID] | None = None,
    remark: str | None = None,
) -> ReportingPeriod | None:
    """更新期次信息（仅 draft 状态可编辑）。"""
    period = await get_period(db, period_id)
    if not period:
        return None

    if period.status != "draft":
        raise BadRequest(detail=f"期次状态为 {period.status}，只能编辑 draft 状态的期次")

    if period_month is not None:
        period.period_month = period_month
    if remark is not None:
        period.remark = remark

    # 如果更新了合同列表，重建关联
    if contract_ids is not None:
        # 删除旧关联
        await db.execute(
            delete(PeriodContract).where(PeriodContract.period_id == period_id)
        )
        # 创建新关联
        for cid in contract_ids:
            pc = PeriodContract(period_id=period_id, contract_id=cid)
            db.add(pc)

    await db.flush()
    await db.refresh(period)
    return period


async def update_period_status(
    db: AsyncSession,
    period_id: uuid.UUID,
    status: str,
) -> ReportingPeriod | None:
    """更新期次状态（带转移校验）。"""
    period = await get_period(db, period_id)
    if not period:
        return None

    _validate_period_transition(period.status, status)
    period.status = status

    await db.flush()
    await db.refresh(period)
    logger.info(f"期次状态更新: id={period_id}, → {status}")
    return period


async def delete_period(
    db: AsyncSession, period_id: uuid.UUID
) -> bool:
    """删除期次（仅 draft 状态可删，同时删除关联的审核记录和费用分项）。"""
    period = await get_period(db, period_id)
    if not period:
        return False

    if period.status != "draft":
        raise BadRequest(detail=f"期次状态为 {period.status}，只能删除 draft 状态的期次")

    # 查找关联的 review IDs
    reviews = await db.execute(
        select(ProgressPaymentReview.id).where(ProgressPaymentReview.period_id == period_id)
    )
    review_ids = [r[0] for r in reviews.all()]

    # 删除 review fee items
    if review_ids:
        await db.execute(
            delete(ReviewFeeItem).where(ReviewFeeItem.review_id.in_(review_ids))
        )
    # 删除 reviews
    await db.execute(
        delete(ProgressPaymentReview).where(ProgressPaymentReview.period_id == period_id)
    )
    # 删除 period contracts
    await db.execute(
        delete(PeriodContract).where(PeriodContract.period_id == period_id)
    )
    # 删除 period
    await db.delete(period)
    await db.flush()

    logger.info(f"期次删除成功: id={period_id}, reviews_deleted={len(review_ids)}")
    return True


# ═══════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════

def _infer_review_type(contract: Contract) -> str:
    """根据合同类型推断审核类型。"""
    desc = (contract.contract_desc or "").lower()
    contract_type = (contract.contract_type or "").lower()
    supplier = (contract.supplier_name or "").lower()

    if "施工" in desc or "建安" in desc or "建筑" in desc:
        return "施工"
    if "监理" in desc or "监理" in supplier:
        return "监理过控"
    if "设计" in desc or "设计" in supplier:
        return "设计"
    if "设备" in desc or "设备" in supplier:
        return "设备"

    # 兜底：按合同类型
    if contract_type == "main":
        return "施工"
    return "施工"  # 默认


async def _count_period_contracts(db: AsyncSession, period_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(PeriodContract.id)).where(PeriodContract.period_id == period_id)
    )
    return result.scalar() or 0


async def _count_period_reviews(db: AsyncSession, period_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(ProgressPaymentReview.id)).where(ProgressPaymentReview.period_id == period_id)
    )
    return result.scalar() or 0
