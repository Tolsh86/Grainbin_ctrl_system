"""导入字段映射 CRUD + 表头预览接口"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.schemas.api_response import ApiResponse
from app.schemas.common import PaginatedResponse
from app.schemas.mapping import (
    MappingCreate,
    MappingResponse,
    MappingUpdate,
    PreviewResponse,
)
from app.services import mapping as mapping_service

router = APIRouter(prefix="/import/mapping", tags=["导入字段映射"])


@router.get("", response_model=PaginatedResponse[MappingResponse])
async def list_mappings(
    biz_type: str | None = Query(None, description="业务类型: weekly/monthly/progress_payment"),
    keyword: str | None = Query(None, description="模板名称模糊搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """分页查询映射模板列表（自动过滤软删除）。"""
    items, total = await mapping_service.list_mappings(db, biz_type, keyword, page, page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[MappingResponse.model_validate(m) for m in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{mapping_id}", response_model=MappingResponse)
async def get_mapping(
    mapping_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """获取映射模板详情。"""
    obj = await mapping_service.get_mapping(db, mapping_id)
    return MappingResponse.model_validate(obj)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: MappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """新建映射模板。"""
    obj = await mapping_service.create_mapping(db, data)
    return ApiResponse(data=MappingResponse.model_validate(obj).model_dump())


@router.put("/{mapping_id}", response_model=ApiResponse)
async def update_mapping(
    mapping_id: uuid.UUID,
    data: MappingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新映射模板（部分更新）。"""
    obj = await mapping_service.update_mapping(db, mapping_id, data)
    return ApiResponse(data=MappingResponse.model_validate(obj).model_dump())


@router.delete("/{mapping_id}", response_model=ApiResponse)
async def delete_mapping(
    mapping_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """软删除映射模板。"""
    await mapping_service.delete_mapping(db, mapping_id)
    return ApiResponse(message="映射模板已删除")


@router.post("/presets", response_model=ApiResponse)
async def init_presets(
    override: bool = Query(False, description="是否覆盖已有模板"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """初始化预置映射模板（周报/月报/进度款各一套）。"""
    await mapping_service.seed_presets(db, override=override)
    return ApiResponse(message="预置模板已初始化")


@router.post("/preview", response_model=ApiResponse)
async def preview_headers(
    mapping_id: uuid.UUID = Form(..., description="映射模板 ID"),
    file: UploadFile = File(..., description="待预览 Excel 文件"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """预览 Excel 表头与模板的匹配结果。

    上传 Excel 文件后，对照指定模板的映射规则返回每列表头的匹配情况。
    """
    file_data = await file.read()
    if not file_data:
        from app.core.exceptions import BadRequest
        raise BadRequest(detail="上传文件为空")
    result = await mapping_service.preview_headers(db, mapping_id, file_data, file.filename or "unknown")
    return ApiResponse(data=result.model_dump())
