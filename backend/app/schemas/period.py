"""报送期次 Schema：请求/响应模型 (Phase2)

t_reporting_periods — 审核模块的核心驱动表。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PeriodCreate(BaseModel):
    """创建期次"""
    period_month: str = Field(..., max_length=7, pattern=r"^\d{4}-\d{2}$", description="期次月份 YYYY-MM")
    period_no: int = Field(..., ge=1, description="期次编号（同一项目下不重复）")
    contract_ids: list[uuid.UUID] = Field(..., min_length=1, description="参与审核的合同 ID 列表")
    remark: str | None = Field(None, description="备注说明")


class PeriodUpdate(BaseModel):
    """更新期次 — 所有字段可选"""
    period_month: str | None = Field(None, max_length=7, pattern=r"^\d{4}-\d{2}$", description="期次月份")
    contract_ids: list[uuid.UUID] | None = Field(None, min_length=1, description="参与审核的合同 ID 列表")
    remark: str | None = Field(None, description="备注说明")


class PeriodStatusUpdate(BaseModel):
    """期次状态更新"""
    status: str = Field(..., description="状态：draft/in_progress/reviewed/closed")
    # submitted/reviewed 状态支持回退到 draft


class PeriodResponse(BaseModel):
    """期次 — 响应"""
    id: uuid.UUID
    project_id: uuid.UUID
    period_no: int
    period_month: str
    status: str
    remark: str | None = None
    created_at: datetime
    updated_at: datetime

    # 聚合统计（由 service 层计算填入）
    contract_count: int | None = Field(None, description="关联合同数")
    review_count: int | None = Field(None, description="关联审核记录数")

    model_config = {"from_attributes": True}


class PeriodDetailResponse(PeriodResponse):
    """期次详情 — 含合同列表和审核概况"""
    contract_ids: list[uuid.UUID] = Field(default_factory=list, description="关联的合同 ID 列表")
