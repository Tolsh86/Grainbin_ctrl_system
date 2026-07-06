"""导入字段映射 Schema"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MappingRuleItem(BaseModel):
    """单条映射规则"""

    user_header: str = Field(..., description="Excel 表头名")
    system_field: str = Field(..., description="系统数据库字段名")
    converter: str = Field("", description="转换器名称，如 wan_yuan_to_fen / excel_serial_to_date")
    default_value: str | None = Field(None, description="当值为空时使用的默认值")


class MappingCreate(BaseModel):
    """创建映射模板"""

    mapping_name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    biz_type: str = Field(
        "general", pattern=r"^(weekly|monthly|progress_payment|general)$",
        description="业务类型: weekly/monthly/progress_payment/general",
    )
    file_format: str = Field("xlsx", pattern=r"^(xlsx|xls|csv)$", description="适用文件格式")
    header_row: int = Field(1, ge=1, le=20, description="表头行号")
    sheet_index: int = Field(0, ge=0, description="Sheet 索引")
    project_id: uuid.UUID | None = Field(None, description="适用项目（NULL=通用）")
    is_active: bool = True
    rules: list[MappingRuleItem] = Field(..., min_length=1, description="映射规则列表")


class MappingUpdate(BaseModel):
    """更新映射模板（所有字段可选）"""

    mapping_name: str | None = Field(None, min_length=1, max_length=200)
    biz_type: str | None = Field(None, pattern=r"^(weekly|monthly|progress_payment|general)$")
    file_format: str | None = Field(None, pattern=r"^(xlsx|xls|csv)$")
    header_row: int | None = Field(None, ge=1, le=20)
    sheet_index: int | None = Field(None, ge=0)
    project_id: uuid.UUID | None = Field(None)
    is_active: bool | None = None
    rules: list[MappingRuleItem] | None = Field(None, min_length=1)


class MappingResponse(BaseModel):
    """映射模板响应"""

    id: uuid.UUID
    mapping_name: str
    biz_type: str
    file_format: str
    header_row: int
    sheet_index: int
    project_id: uuid.UUID | None = None
    is_active: bool
    rules: dict
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class MappingQuery(BaseModel):
    """映射模板查询参数"""

    biz_type: str | None = Field(None, description="按业务类型筛选")
    keyword: str | None = Field(None, description="按名称模糊搜索")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class HeaderMatchResult(BaseModel):
    """单列表头匹配结果"""

    user_header: str = Field(..., description="Excel 中的原始表头")
    matched: bool = Field(..., description="是否匹配到系统字段")
    system_field: str | None = Field(None, description="匹配的系统字段名")
    converter: str = Field("", description="建议使用的转换器")


class PreviewResponse(BaseModel):
    """表头预览匹配响应"""

    mapping_id: uuid.UUID = Field(..., description="使用的映射模板 ID")
    mapping_name: str = Field(..., description="模板名称")
    total_headers: int = Field(..., description="Excel 表头总数")
    matched: int = Field(..., description="匹配到的表头数")
    unmatched: int = Field(..., description="未匹配的表头数")
    headers: list[HeaderMatchResult] = Field(..., description="匹配明细")
