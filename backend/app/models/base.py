"""ORM 基类与公共 Mixin

提供:
- Base: SQLAlchemy 2.0 声明式基类
- UUIDMixin: UUID 主键
- TimestampMixin: created_at / updated_at
- SoftDeleteMixin: 软删除 deleted_at
- DictMixin: 字典表通用 Mixin
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """声明式基类 - 所有 ORM 模型从此继承。"""
    pass


class UUIDMixin:
    """UUID 主键 Mixin。"""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="主键",
    )


class TimestampMixin:
    """创建时间 + 更新时间 Mixin。"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


class SoftDeleteMixin:
    """软删除 Mixin。"""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="软删除时间",
    )


class DictMixin:
    """字典表通用 Mixin — 统一结构 (code, name, sort_order, is_active)。"""

    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="字典编码"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="显示名称"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序序号"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
