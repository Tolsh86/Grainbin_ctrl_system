"""公共 Pydantic Schema：分页、消息响应"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    items: list[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    pages: int = Field(..., description="总页数")


class MessageResponse(BaseModel):
    """通用消息响应"""

    message: str = Field(..., description="响应消息")
    detail: str | None = Field(None, description="详细信息")
