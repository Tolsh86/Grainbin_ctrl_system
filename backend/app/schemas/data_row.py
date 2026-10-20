"""过控数据流水行 Schema：t_data_rows 请求/响应模型"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class DataRowStatusUpdate(BaseModel):
    """数据行状态更新（PATCH /data-rows/{row_id}/status）"""
    status: str = Field(..., description="审核状态：draft/submitted/reviewed/rejected/confirmed")
    remark: str | None = Field(None, description="审核备注")


class DataRowAggregateItem(BaseModel):
    """数据行聚合项（按月/合同）"""
    month: str
    contract_id: uuid.UUID | None = None
    contract_no: str | None = None
    total_amount: int = 0
    row_count: int = 0


class DataCreate(BaseModel):
    """创建数据行"""
    project_id: uuid.UUID = Field(..., description="关联项目ID")
    data_date: date | None = Field(None, description="数据发生日期")
    category: str | None = Field(None, max_length=100, description="分部工程类别")
    item_name: str | None = Field(None, max_length=200, description="分项名称")
    planned_quantity: int | None = Field(None, ge=0, description="计划工程量")
    actual_quantity: int | None = Field(None, ge=0, description="实际工程量")
    unit: str | None = Field(None, max_length=20, description="单位")
    unit_price: int | None = Field(None, ge=0, description="单价（分）")
    amount: int | None = Field(None, ge=0, description="金额（分）")
    cost_type: str | None = Field(None, max_length=50, description="费用类型")
    source_doc: str | None = Field(None, max_length=500, description="来源文档名称")
    source_type: str | None = Field(None, max_length=30, description="来源类型")
    raw_data: dict | None = Field(None, description="AI识别的原始数据快照")
    # ── V2.2 第二阶段新增 ──
    contract_id: uuid.UUID | None = Field(None, description="关联合同ID")
    status: str = Field("draft", description="审核状态：draft/submitted/reviewed/rejected/confirmed")
    cost_sub_type: str | None = Field(None, max_length=50, description="费用分项类型")


class DataRowResponse(BaseModel):
    """数据行响应 — 对应 t_data_rows"""

    id: uuid.UUID
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
    source_doc: str | None = None
    source_type: str | None = None
    raw_data: dict | None = None
    is_confirmed: bool = False
    confirmed_by: uuid.UUID | None = None
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # ── V2.2 第二阶段新增 ──
    contract_id: uuid.UUID | None = None
    status: str = "draft"
    cost_sub_type: str | None = None

    model_config = {"from_attributes": True}
