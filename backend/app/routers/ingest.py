"""清洗流水线路由：上传、批次管理、映射管理"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.ingest import (
    FieldMappingCreate,
    FieldMappingResponse,
    IngestBatchResponse,
    IngestErrorResponse,
    IngestRowResponse,
    IngestRowUpdate,
)
from app.models.ingest import IngestError, FieldMapping
from app.services import ingest as ingest_service

router = APIRouter(prefix="/ingest", tags=["数据入库"])


# ── 上传 ──────────────────────────────────────────

@router.post("/upload", response_model=IngestBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    project_id: uuid.UUID = Form(..., description="目标项目 ID"),
    file: UploadFile = File(..., description="上传文件"),
    mapping_id: uuid.UUID = Form(None, description="字段映射 ID"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("editor")),
):
    """上传文件并创建清洗批次。

    文件保存到 MinIO 后创建批次记录，异步启动清洗流水线。
    返回 batch_id，前端轮询批次状态。
    """
    # 判断文件格式
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    format_map = {
        "xlsx": "xlsx", "xls": "xls", "csv": "csv",
        "pdf": "pdf", "png": "image", "jpg": "image", "jpeg": "image",
    }
    file_format = format_map.get(ext, "unknown")
    if file_format == "unknown":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: .{ext}",
        )

    # TODO: 上传到 MinIO，获取 source_path
    # 当前阶段使用占位路径
    source_path = f"ingest/{project_id}/{uuid.uuid4()}/{filename}"

    # 创建批次
    batch = await ingest_service.create_batch(
        db=db,
        project_id=project_id,
        source_doc=filename,
        source_path=source_path,
        file_format=file_format,
        uploaded_by=current_user_id,
        mapping_id=mapping_id,
    )

    # TODO: 触发 Celery 异步任务 process_ingest_batch.delay(str(batch.id))

    return batch


# ── 批次 ──────────────────────────────────────────

@router.get("/batches", response_model=PaginatedResponse[IngestBatchResponse])
async def list_batches(
    project_id: uuid.UUID = Query(None, description="按项目筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取批次列表。"""
    items, total = await ingest_service.get_batches(db, project_id, page, page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[IngestBatchResponse.model_validate(b) for b in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/batches/{batch_id}", response_model=IngestBatchResponse)
async def get_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取批次详情。"""
    batch = await ingest_service.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="批次不存在")
    return batch


@router.get("/batches/{batch_id}/rows", response_model=PaginatedResponse[IngestRowResponse])
async def list_batch_rows(
    batch_id: uuid.UUID,
    is_valid: bool = Query(None, description="按校验状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取批次中的清洗行。"""
    items, total = await ingest_service.get_batch_rows(db, batch_id, is_valid, page, page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[IngestRowResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post("/batches/{batch_id}/commit", response_model=MessageResponse)
async def commit_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("editor")),
):
    """确认入库：将校验通过的行写入 t_data_rows。"""
    batch = await ingest_service.commit_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批次不存在或状态不允许入库",
        )
    return MessageResponse(message=f"批次 {batch_id} 已入库")


@router.post("/batches/{batch_id}/rollback", response_model=MessageResponse)
async def rollback_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """整批撤回：将已入库的数据软删除。"""
    batch = await ingest_service.rollback_batch(db, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批次不存在或未入库，无法撤回",
        )
    return MessageResponse(message=f"批次 {batch_id} 已撤回")


# ── 字段映射 ──────────────────────────────────────

@router.get("/mappings", response_model=PaginatedResponse[FieldMappingResponse])
async def list_mappings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取字段映射列表。"""
    from sqlalchemy import func, select

    total = (await db.execute(select(func.count(FieldMapping.id)))).scalar_one()
    items = (
        await db.execute(
            select(FieldMapping)
            .order_by(FieldMapping.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[FieldMappingResponse.model_validate(m) for m in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post("/mappings", response_model=FieldMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: FieldMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("editor")),
):
    """新建字段映射。"""
    mapping = FieldMapping(
        mapping_name=data.mapping_name,
        project_id=data.project_id,
        file_format=data.file_format,
        header_row=data.header_row,
        sheet_index=data.sheet_index,
        rules={"rules": [r.model_dump() for r in data.rules]},
        is_active=data.is_active,
    )
    db.add(mapping)
    await db.flush()
    await db.refresh(mapping)
    return mapping
