"""清洗流水线 Schema：批次/行/错误/映射"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════
# 字段映射
# ═══════════════════════════════════════════════

class FieldMappingRule(BaseModel):
    """单条映射规则"""

    user_header: str = Field(..., description="用户表头名")
    system_field: str = Field(..., description="系统字段名")
    converter: str = Field("", description="转换器名称")


class FieldMappingCreate(BaseModel):
    """创建字段映射"""

    mapping_name: str = Field(..., min_length=1, max_length=200)
    project_id: uuid.UUID | None = None
    file_format: str = Field(..., pattern=r"^(xlsx|xls|csv|pdf|image)$")
    header_row: int = Field(1, ge=1)
    sheet_index: int = Field(0, ge=0)
    rules: list[FieldMappingRule] = Field(..., min_length=1, description="映射规则列表")
    is_active: bool = True


class FieldMappingResponse(BaseModel):
    """字段映射响应"""

    id: uuid.UUID
    mapping_name: str
    project_id: uuid.UUID | None = None
    file_format: str
    header_row: int
    sheet_index: int
    rules: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# 批次
# ═══════════════════════════════════════════════

class IngestBatchResponse(BaseModel):
    """批次响应"""

    id: uuid.UUID
    project_id: uuid.UUID
    source_doc: str
    source_path: str
    source_type: str
    file_format: str
    period_start: date | None = None
    period_end: date | None = None
    mapping_id: uuid.UUID | None = None
    total_rows: int
    parsed_rows: int
    valid_rows: int
    error_rows: int
    quality_score: float | None = None
    status: str
    committed_at: datetime | None = None
    rolled_back_at: datetime | None = None
    uploaded_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════
# 清洗行
# ═══════════════════════════════════════════════

class IngestRowResponse(BaseModel):
    """清洗行响应"""

    id: uuid.UUID
    batch_id: uuid.UUID
    row_no: int
    raw_payload: dict
    normalized: dict
    mapped: dict
    project_id: uuid.UUID
    data_date: date | None = None
    category: str | None = None
    item_name: str | None = None
    planned_quantity: int | None = None
    actual_quantity: int | None = None
    unit: str | None = None
    unit_price: int | None = None
    amount: int | None = None
    cost_type: str | None = None
    validation_flags: dict
    quality_score: float | None = None
    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None
    target_data_row_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestRowUpdate(BaseModel):
    """清洗行修正 — 可修改已映射的字段"""

    data_date: date | None = None
    category: str | None = None
    item_name: str | None = None
    planned_quantity: int | None = None
    actual_quantity: int | None = None
    unit: str | None = None
    unit_price: int | None = None
    amount: int | None = None
    cost_type: str | None = None


# ═══════════════════════════════════════════════
# 错误
# ═══════════════════════════════════════════════

class IngestErrorResponse(BaseModel):
    """错误响应"""

    id: uuid.UUID
    batch_id: uuid.UUID
    row_id: uuid.UUID | None = None
    error_stage: str
    error_code: str
    error_message: str
    error_field: str | None = None
    error_value: str | None = None
    severity: str
    resolved: bool
    resolved_by: uuid.UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
