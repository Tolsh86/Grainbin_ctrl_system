"""文件上传路由：上传 → 创建 IngestBatch"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.api_response import ApiResponse
from app.schemas.upload import BatchUploadResponse
from app.services import upload as upload_service
from app.services.ingest import create_batch

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post("/file", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="待上传文件（xlsx/xls/csv）"),
    project_id: uuid.UUID = Form(..., description="目标项目 ID"),
    mapping_id: uuid.UUID | None = Form(None, description="字段映射模板 ID（可选，后续可绑定）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """上传文件 → MinIO 存储 → 创建 IngestBatch。

    完整流程：upload → (batch pending) → 绑定 mapping → batch/parse 触发解析。
    """
    file_data = await file.read()
    file_name = file.filename or "unknown"
    file_size = len(file_data)

    upload_result = await upload_service.upload_single(file_name, file_data, file_size)

    batch = await create_batch(
        db=db,
        project_id=project_id,
        source_doc=file_name,
        source_path=upload_result.file_path,
        file_format=upload_result.file_format,
        uploaded_by=current_user_id,
        mapping_id=mapping_id,
    )

    return ApiResponse(data={
        "batch_id": str(batch.id),
        "file_name": upload_result.file_name,
        "file_path": upload_result.file_path,
        "file_format": upload_result.file_format,
        "file_size": upload_result.file_size,
        "batch_no": upload_result.batch_no,
        "uploaded_at": upload_result.uploaded_at.isoformat(),
    })


@router.post("/files", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: list[UploadFile] = File(..., description="批量上传文件列表（xlsx/xls/csv）"),
    project_id: uuid.UUID = Form(..., description="目标项目 ID"),
    mapping_id: uuid.UUID | None = Form(None, description="字段映射模板 ID"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """批量上传 → 每个文件单独创建 IngestBatch。"""
    payload: list[tuple[str, bytes, int]] = []
    for f in files:
        data = await f.read()
        payload.append((f.filename or "unknown", data, len(data)))

    results = await upload_service.upload_batch(payload)

    batch_ids: list[str] = []
    for r in results.files:
        batch = await create_batch(
            db=db,
            project_id=project_id,
            source_doc=r.file_name,
            source_path=r.file_path,
            file_format=r.file_format,
            uploaded_by=current_user_id,
            mapping_id=mapping_id,
        )
        batch_ids.append(str(batch.id))

    return ApiResponse(data={
        "batch_ids": batch_ids,
        "files": [r.model_dump() for r in results.files],
        "total": results.total,
    })
