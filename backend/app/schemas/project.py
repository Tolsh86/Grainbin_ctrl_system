"""项目 Schema：请求/响应模型

与 t_projects 模型字段完全对齐（V2.0 数据字典 30+ 字段）。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── 请求 ──

class ProjectCreate(BaseModel):
    """创建项目"""
    project_name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    project_code: str = Field(..., min_length=1, max_length=50, description="项目编码（业务唯一标识）")

    # 项目分类
    project_nature: str = Field("功能性项目", description="项目性质")
    invest_timing: str = Field("续投项目", description="投资时序")
    invest_nature: str | None = Field(None, description="投资性质")
    invest_structure: str | None = Field(None, description="投资结构")
    invest_field: str | None = Field(None, description="投资领域")
    implement_body: str | None = Field(None, description="实施主体")
    implement_period: str | None = Field(None, description="实施时间")
    expected_return: str | None = Field(None, description="投资预期收益")
    business_class: str | None = Field(None, description="业务划分")
    region: str = Field("市内", description="区域")

    # 行政属性
    importance: str | None = Field(None, description="重要性")
    supervising_dept: str | None = Field(None, description="行业归口主管部门")
    project_level_remark: str | None = Field(None, description="项目级别备注")
    responsible_unit: str | None = Field(None, description="责任单位")

    # 建设内容
    construction_content: str | None = Field(None, description="项目内容/建设内容")
    construction_scale: str | None = Field(None, description="建设内容及规模")
    construction_period: str | None = Field(None, description="建设周期/起止年")

    # 投资金额（分）
    planned_total_invest: int = Field(0, ge=0, description="计划总投资（分）")
    planned_invest_2026: int | None = Field(None, ge=0, description="2026年计划投资（分）")

    # 参建单位
    owner_unit: str | None = Field(None, description="业主单位/建设单位")

    # 质量安全
    quality_target: str = Field("合格", description="质量目标")
    safety_target: str | None = Field(None, description="安全目标")

    # 状态
    project_status: str = Field("preparing", description="状态：preparing/constructing/completed/suspended")


class ProjectUpdate(BaseModel):
    """更新项目 — 所有字段可选"""
    project_name: str | None = Field(None, min_length=1, max_length=200, description="项目名称")
    project_code: str | None = Field(None, min_length=1, max_length=50, description="项目编码")
    project_nature: str | None = Field(None, description="项目性质")
    invest_timing: str | None = Field(None, description="投资时序")
    invest_nature: str | None = Field(None, description="投资性质")
    invest_structure: str | None = Field(None, description="投资结构")
    invest_field: str | None = Field(None, description="投资领域")
    implement_body: str | None = Field(None, description="实施主体")
    implement_period: str | None = Field(None, description="实施时间")
    expected_return: str | None = Field(None, description="投资预期收益")
    business_class: str | None = Field(None, description="业务划分")
    region: str | None = Field(None, description="区域")
    importance: str | None = Field(None, description="重要性")
    supervising_dept: str | None = Field(None, description="行业归口主管部门")
    project_level_remark: str | None = Field(None, description="项目级别备注")
    responsible_unit: str | None = Field(None, description="责任单位")
    construction_content: str | None = Field(None, description="项目内容")
    construction_scale: str | None = Field(None, description="建设内容及规模")
    construction_period: str | None = Field(None, description="建设周期")
    planned_total_invest: int | None = Field(None, ge=0, description="计划总投资（分）")
    planned_invest_2026: int | None = Field(None, ge=0, description="2026年计划投资（分）")
    owner_unit: str | None = Field(None, description="业主单位")
    quality_target: str | None = Field(None, description="质量目标")
    safety_target: str | None = Field(None, description="安全目标")
    project_status: str | None = Field(None, description="状态")


# ── 响应 ──

class ProjectResponse(BaseModel):
    """项目响应"""
    id: uuid.UUID

    # 基本信息
    project_name: str
    project_code: str

    # 项目分类
    project_nature: str
    invest_timing: str
    invest_nature: str | None = None
    invest_structure: str | None = None
    invest_field: str | None = None
    implement_body: str | None = None
    implement_period: str | None = None
    expected_return: str | None = None
    business_class: str | None = None
    region: str

    # 行政属性
    importance: str | None = None
    supervising_dept: str | None = None
    project_level_remark: str | None = None
    responsible_unit: str | None = None

    # 建设内容
    construction_content: str | None = None
    construction_scale: str | None = None
    construction_period: str | None = None

    # 投资金额
    planned_total_invest: int
    planned_invest_2026: int | None = None

    # 参建单位
    owner_unit: str | None = None

    # 质量安全
    quality_target: str
    safety_target: str | None = None

    # 状态
    project_status: str

    # 时间戳
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    total: int = Field(0, description="项目总数")
    by_status: dict[str, int] = Field(default_factory=dict, description="按状态分组")
    by_nature: dict[str, int] = Field(default_factory=dict, description="按项目性质分组")
    by_region: dict[str, int] = Field(default_factory=dict, description="按区域分组")
    total_investment: int = Field(0, description="计划总投资合计（分）")
