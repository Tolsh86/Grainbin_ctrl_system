"""进度款审核路由：ProgressPaymentReview CRUD + 状态变更

路由设计对应业务文档 5.7 节：
- /api/v1/projects/{project_id}/reviews         → 审核列表 + 新建
- /api/v1/reviews/{review_id}                   → 详情/编辑/状态变更
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewStatusUpdate, ReviewResponse
from app.services import review as review_service

router = APIRouter(tags=["进度款审核"])


# ═══════════════════════════════════════════════════════════════════
# 进度款审核 CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get(
    "/projects/{project_id}/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
async def list_reviews(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    review_type: str | None = Query(None, description="按审核类型筛选（自由文本，如'施工单位''监理过控'）"),
    audit_status: str | None = Query(None, description="按审核状态筛选：pending/auditing/audited/paid"),
    period_no: int | None = Query(None, description="按期次筛选"),
    keyword: str | None = Query(None, description="搜索关键词（申请单位/审核类型/期数）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取项目下所有审核记录（分页+多维筛选）。

    review_type 是自由文本 VARCHAR(20)，不做枚举限制。
    前端可根据 review_type 动态渲染 extra_fields 中的特有字段。
    """
    items, total = await review_service.get_reviews(
        db, project_id=project_id, page=page, page_size=page_size,
        review_type=review_type, audit_status=audit_status,
        period_no=period_no, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[ReviewResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post(
    "/projects/{project_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    project_id: uuid.UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """手动录入一条审核记录（需 operator 及以上权限）。

    review_type 为自由文本，系统不做枚举限制。
    前端根据选择的合同类型给出默认建议，用户可修改为任何值。
    特有字段通过 extra_fields JSONB 传递。
    """
    review = await review_service.create_review(db, project_id, data, user_id=current_user_id)
    return review


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取单条审核记录详情。"""
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
    """编辑审核记录（需 operator 及以上权限）。"""
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
    """更新审核状态（需 operator 及以上权限）。

    状态流转：
      pending → auditing → audited → paid
      支持回退（audited → auditing → pending）
      已付（paid）为终态，不可变更
    """
    review = await review_service.update_review_status(db, review_id, data)
    if not review:
        from app.core.exceptions import NotFound
        raise NotFound(detail="审核记录不存在")
    return review
