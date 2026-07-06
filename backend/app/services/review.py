"""进度款审核业务逻辑：ProgressPaymentReview CRUD + 状态变更"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress_review import ProgressPaymentReview
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewStatusUpdate
from app.core.exceptions import NotFound, BadRequest
from app.utils.db import paginate


# ── 审核状态转移规则 ──
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["auditing", "audited"],           # 待审 → 审核中 / 已审
    "auditing": ["audited", "pending"],           # 审核中 → 已审 / 回退待审
    "audited": ["paid", "auditing"],              # 已审 → 已付 / 回退审核中
    "paid": [],                                   # 已付 — 终态，不可变更
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
    project_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    review_type: str | None = None,
    audit_status: str | None = None,
    period_no: int | None = None,
    keyword: str | None = None,
) -> tuple[list[ProgressPaymentReview], int]:
    """分页查询审核记录，支持多维筛选。

    设计原则：review_type 是自由文本 VARCHAR(20)，不做枚举限制。
    """
    stmt = select(ProgressPaymentReview).where(
        ProgressPaymentReview.project_id == project_id
    ).order_by(ProgressPaymentReview.period_no.desc(), ProgressPaymentReview.created_at.desc())
    count_stmt = select(func.count(ProgressPaymentReview.id)).where(
        ProgressPaymentReview.project_id == project_id
    )

    if review_type:
        stmt = stmt.where(ProgressPaymentReview.review_type == review_type)
        count_stmt = count_stmt.where(ProgressPaymentReview.review_type == review_type)
    if audit_status:
        stmt = stmt.where(ProgressPaymentReview.audit_status == audit_status)
        count_stmt = count_stmt.where(ProgressPaymentReview.audit_status == audit_status)
    if period_no:
        stmt = stmt.where(ProgressPaymentReview.period_no == period_no)
        count_stmt = count_stmt.where(ProgressPaymentReview.period_no == period_no)
    if keyword:
        like = f"%{keyword}%"
        cond = (ProgressPaymentReview.applicant_unit.ilike(like) |
                ProgressPaymentReview.review_type.ilike(like) |
                ProgressPaymentReview.period_month.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

    return await paginate(db, stmt, page=page, page_size=page_size, model=ProgressPaymentReview, count_stmt=count_stmt, auto_active=False)


async def get_review(db: AsyncSession, review_id: uuid.UUID) -> ProgressPaymentReview | None:
    """按 ID 获取审核记录。"""
    result = await db.execute(
        select(ProgressPaymentReview).where(ProgressPaymentReview.id == review_id)
    )
    return result.scalar_one_or_none()


async def create_review(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ReviewCreate,
    user_id: uuid.UUID | None = None,
) -> ProgressPaymentReview:
    """手动录入一条审核记录。

    review_type 是自由文本（VARCHAR(20)），不做枚举限制。
    系统不预测审核类型——合同是上游，审核是下游。
    前端根据合同类型给出建议（施工合同→"施工单位"），用户可修改为任何值。
    """
    review = ProgressPaymentReview(
        project_id=project_id,
        **data.model_dump(),
    )
    if user_id:
        review.audited_by = user_id

    db.add(review)
    await db.flush()
    await db.refresh(review)
    logger.info(f"审核记录创建成功: project={project_id}, type={data.review_type}, period={data.period_no}")
    return review


async def update_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    data: ReviewUpdate,
) -> ProgressPaymentReview | None:
    """更新审核记录。"""
    review = await get_review(db, review_id)
    if not review:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
    await db.flush()
    await db.refresh(review)
    return review


async def update_review_status(
    db: AsyncSession,
    review_id: uuid.UUID,
    data: ReviewStatusUpdate,
) -> ProgressPaymentReview | None:
    """更新审核状态（带状态转移校验）。"""
    review = await get_review(db, review_id)
    if not review:
        return None

    # 状态转移校验
    _validate_status_transition(review.audit_status, data.audit_status)

    review.audit_status = data.audit_status
    if data.audited_by:
        review.audited_by = data.audited_by

    # 记录审核时间
    if data.audit_status in ("audited", "paid"):
        review.audited_at = datetime.now(UTC)
    elif data.audit_status == "pending":
        review.audited_at = None

    await db.flush()
    await db.refresh(review)
    logger.info(f"审核状态更新: id={review_id}, {review.audit_status} → {data.audit_status}")
    return review
