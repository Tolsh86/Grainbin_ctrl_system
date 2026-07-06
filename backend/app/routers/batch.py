"""导入批次管理路由"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.schemas.api_response import ApiResponse
from app.schemas.common import PaginatedResponse
from app.schemas.ingest import IngestBatchResponse, IngestErrorResponse, IngestRowResponse
from app.services import batch_service

router = APIRouter(prefix="/import/batch", tags=["导入批次管理"])


@router.get("/{batch_id}", response_model=IngestBatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """批次详情：返回总行数、错误行数、成功行数、当前状态。"""
    batch = await batch_service.get_batch(db, batch_id)
    return IngestBatchResponse.model_validate(batch)


@router.post("/{batch_id}/parse", response_model=ApiResponse)
async def trigger_parse(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """触发异步解析任务。

    仅 pending / failed 状态可触发。
    状态原子更新后分发 Celery 异步处理。
    """
    await batch_service.parse_batch(db, batch_id)
    return ApiResponse(message=f"批次 {batch_id} 解析任务已提交")


@router.get("/{batch_id}/rows", response_model=PaginatedResponse[IngestRowResponse])
async def list_batch_rows(
    batch_id: uuid.UUID,
    is_valid: bool | None = Query(None, description="按校验状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """批次清洗行分页查询。"""
    batch = await batch_service.get_batch(db, batch_id)
    items, total = await batch_service.get_batch_rows(db, batch, page, page_size, is_valid)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[IngestRowResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{batch_id}/errors", response_model=PaginatedResponse[IngestErrorResponse])
async def list_batch_errors(
    batch_id: uuid.UUID,
    severity: str | None = Query(None, description="按严重级别筛选: error/warning/info"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """批次错误日志分页查询。"""
    items, total = await batch_service.get_batch_errors(db, batch_id, page, page_size, severity)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[IngestErrorResponse.model_validate(e) for e in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )
