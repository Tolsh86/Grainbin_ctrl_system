"""文件上传响应 Schema"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FileUploadResult(BaseModel):
    """单文件上传结果"""

    file_name: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="MinIO 存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    file_format: str = Field("", description="文件格式: xlsx/xls/csv")
    batch_no: str = Field(..., description="批次临时编号")
    batch_id: str | None = Field(None, description="IngestBatch ID（创建批次后返回）")
    uploaded_at: datetime = Field(..., description="上传时间")

    model_config = {"from_attributes": True}


class BatchUploadResponse(BaseModel):
    """批量上传响应"""

    batch_no: str = Field(..., description="本次上传批次号")
    files: list[FileUploadResult] = Field(..., description="文件列表")
    total: int = Field(..., description="本次上传文件数")
    total_size: int = Field(..., description="总大小（字节）")
