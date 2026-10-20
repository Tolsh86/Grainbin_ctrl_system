"""进度款审核路由：ProgressPaymentReview CRUD + 状态变更 (Phase2 改造)

路由设计：
- GET  /api/v1/periods/{period_id}/reviews             → 期次下的审核列表
- GET  /api/v1/projects/{project_id}/reviews           → 项目下的审核列表
- POST /api/v1/periods/{period_id}/reviews             → 在期次下新建审核
- GET  /api/v1/reviews/{review_id}                     → 审核详情
- PUT  /api/v1/reviews/{review_id}                     → 编辑审核
- PUT  /api/v1/reviews/{review_id}/aggregate-daily     → 建安费用：从日报汇总
- PATCH /api/v1/reviews/{review_id}/status              → 状态变更
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewStatusUpdate, ReviewResponse
from app.services import review as review_service
from app.models.contract import Contract, ContractMonthlyDetail
from app.models.review_fee_item import ReviewFeeItem
from app.models.reporting_period import ReportingPeriod

router = APIRouter(tags=["进度款审核"])


# ═══════════════════════════════════════════════════════════════════
# 项目维度的审核查询
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
async def list_reviews_by_project(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    review_type: str | None = Query(None, description="按审核类型筛选"),
    audit_status: str | None = Query(None, description="按审核状态筛选：draft/submitted/reviewed"),
    keyword: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下所有审核记录（分页+筛选）。"""
    items, total = await review_service.get_reviews(
        db, project_id=project_id, page=page, page_size=page_size,
        review_type=review_type, audit_status=audit_status, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ReviewResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


# ═══════════════════════════════════════════════════════════════════
# 期次维度的审核查询 + 新建
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/periods/{period_id}/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
async def list_reviews_by_period(
    period_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    review_type: str | None = Query(None, description="按审核类型筛选"),
    audit_status: str | None = Query(None, description="按审核状态筛选"),
    keyword: str | None = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取期次下的审核记录列表（分页+筛选）。"""
    items, total = await review_service.get_reviews(
        db, period_id=period_id, page=page, page_size=page_size,
        review_type=review_type, audit_status=audit_status, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ReviewResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post(
    "/periods/{period_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review_in_period(
    period_id: uuid.UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """在期次下手动新增一条审核记录（需 operator 权限）。

    创建时会自动从 data.fee_items 生成费用分项快照。
    """
    from app.models.reporting_period import ReportingPeriod
    period = await db.get(ReportingPeriod, period_id)
    if not period:
        from app.core.exceptions import NotFound
        raise NotFound(detail="期次不存在")

    review = await review_service.create_review(db, period.project_id, data, user_id=current_user_id)
    return review


# ═══════════════════════════════════════════════════════════════════
# 单条审核操作
# ═══════════════════════════════════════════════════════════════════

@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取单条审核记录详情（含费用分项）。"""
    review = await review_service.get_review(db, review_id)
    if not review:
        from app.core.exceptions import NotFound
        raise NotFound(detail="审核记录不存在")
    return review


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: uuid.UUID,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """编辑审核记录（需 operator 权限）。"""
    review = await review_service.update_review(db, review_id, data)
    if not review:
        from app.core.exceptions import NotFound
        raise NotFound(detail="审核记录不存在")
    return review


@router.patch("/reviews/{review_id}/status", response_model=ReviewResponse)
async def update_review_status(
    review_id: uuid.UUID,
    data: ReviewStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新审核状态（需 operator 权限）。

    状态流转：draft → submitted → reviewed（支持回退到 draft）
    确认审核（→ reviewed）时自动：
    - 汇总 fee_items 写入 current_audited_output / cumulative_audited_payable
    - 写入月度台账 t_contract_monthly_detail
    - 联动推进期次状态（所有 review 确认后 → reviewed）
    """
    review = await review_service.update_review_status(db, review_id, data)
    if not review:
        from app.core.exceptions import NotFound
        raise NotFound(detail="审核记录不存在")
    return review


# ═══════════════════════════════════════════════════════════════════
# 建安费用：从日报自动汇总（daily_aggregate 专用）
# ═══════════════════════════════════════════════════════════════════

@router.put("/reviews/{review_id}/aggregate-daily", response_model=ReviewResponse)
async def aggregate_daily_to_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """建安费用专用：从当月日报汇总报送值。

    查询 t_contract_monthly_detail 中该合同当月的 output_amount 合计，
    写入 review 的 cumulative_reported_output 和各 fee_items 的 reported_amount。

    仅对 review_mode=daily_aggregate 的合同有效。
    """
    review = await review_service.get_review(db, review_id)
    if not review:
        from app.core.exceptions import NotFound
        raise NotFound(detail="审核记录不存在")

    # 获取合同 review_mode
    contract = await db.get(Contract, review.contract_id)
    if not contract:
        from app.core.exceptions import NotFound
        raise NotFound(detail="关联合同不存在")
    if contract.review_mode != "daily_aggregate":
        from app.core.exceptions import BadRequest
        raise BadRequest(detail="非建安费用合同不支持日报自动汇总（review_mode != daily_aggregate）")

    # 获取期次月份
    period = await db.get(ReportingPeriod, review.period_id)
    if not period:
        from app.core.exceptions import BadRequest
        raise BadRequest(detail="关联期次不存在")

    detail_month = date.fromisoformat(period.period_month + "-01")

    # 查询该月日报数据
    result = await db.execute(
        select(func.coalesce(func.sum(ContractMonthlyDetail.output_amount), 0))
        .where(
            ContractMonthlyDetail.contract_id == review.contract_id,
            ContractMonthlyDetail.detail_month == detail_month,
        )
    )
    monthly_total = result.scalar() or 0

    # 写入累计报送产值
    review.cumulative_reported_output = monthly_total

    # 如果有 fee_items，按比例分配汇总值到各分项
    if review.fee_items and monthly_total > 0:
        # 简单策略：按比例均分（有 cost_items_detail 则按明细）
        total_ratio = sum((fi.payment_ratio or 0) for fi in review.fee_items)
        if total_ratio > 0:
            for fi in review.fee_items:
                ratio = (fi.payment_ratio or 0) / total_ratio
                fi.reported_amount = int(monthly_total * ratio)
        else:
            # 无比例则均分
            per_item = monthly_total // max(len(review.fee_items), 1)
            for fi in review.fee_items:
                fi.reported_amount = per_item

    await db.flush()
    await db.refresh(review)
    from loguru import logger
    logger.info(f"日报汇总完成: review={review_id}, month_total={monthly_total}")
    return review
