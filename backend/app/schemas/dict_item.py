"""字典通用 Schema"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DictItemCreate(BaseModel):
    """创建字典条目"""
    code: str = Field(..., min_length=1, max_length=50, description="字典编码")
    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    sort_order: int = Field(0, description="排序序号")
    is_active: bool = Field(True, description="是否启用")


class DictItemUpdate(BaseModel):
    """更新字典条目"""
    code: str | None = Field(None, min_length=1, max_length=50, description="字典编码")
    name: str | None = Field(None, min_length=1, max_length=100, description="显示名称")
    sort_order: int | None = Field(None, description="排序序号")
    is_active: bool | None = Field(None, description="是否启用")


class DictItemResponse(BaseModel):
    """字典条目响应"""
    id: uuid.UUID
    code: str
    name: str
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
