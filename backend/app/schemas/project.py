"""项目 Schema：请求/响应模型"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── 请求 ──

class ProjectCreate(BaseModel):
    """创建项目"""

    project_name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    project_code: str = Field(..., min_length=1, max_length=50, description="项目编码")
    construction_scale: str | None = Field(None, max_length=50, description="建设规模")
    total_investment: int | None = Field(None, ge=0, description="总投资额（分）")
    owner_unit: str | None = Field(None, max_length=200, description="业主单位")
    supervision_unit: str | None = Field(None, max_length=200, description="监理单位")
    design_unit: str | None = Field(None, max_length=200, description="设计单位")
    constructor_unit: str | None = Field(None, max_length=200, description="施工单位")
    start_date: date | None = Field(None, description="开工日期")
    planned_end_date: date | None = Field(None, description="计划竣工日期")
    actual_end_date: date | None = Field(None, description="实际竣工日期")
    project_status: str = Field("前期", pattern=r"^(前期|施工中|已竣工|停工)$", description="项目状态")
    description: str | None = Field(None, description="项目描述")


class ProjectUpdate(BaseModel):
    """更新项目 — 所有字段可选"""

    project_name: str | None = Field(None, min_length=1, max_length=200, description="项目名称")
    project_code: str | None = Field(None, min_length=1, max_length=50, description="项目编码")
    construction_scale: str | None = Field(None, max_length=50, description="建设规模")
    total_investment: int | None = Field(None, ge=0, description="总投资额（分）")
    owner_unit: str | None = Field(None, max_length=200, description="业主单位")
    supervision_unit: str | None = Field(None, max_length=200, description="监理单位")
    design_unit: str | None = Field(None, max_length=200, description="设计单位")
    constructor_unit: str | None = Field(None, max_length=200, description="施工单位")
    start_date: date | None = Field(None, description="开工日期")
    planned_end_date: date | None = Field(None, description="计划竣工日期")
    actual_end_date: date | None = Field(None, description="实际竣工日期")
    project_status: str | None = Field(None, pattern=r"^(前期|施工中|已竣工|停工)$", description="项目状态")
    description: str | None = Field(None, description="项目描述")


# ── 响应 ──

class ProjectResponse(BaseModel):
    """项目响应"""

    id: uuid.UUID
    project_name: str
    project_code: str
    construction_scale: str | None = None
    total_investment: int | None = None
    owner_unit: str | None = None
    supervision_unit: str | None = None
    design_unit: str | None = None
    constructor_unit: str | None = None
    start_date: date | None = None
    planned_end_date: date | None = None
    actual_end_date: date | None = None
    project_status: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
