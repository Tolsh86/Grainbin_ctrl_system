"""用户表 t_users

字段：email, password_hash, full_name, role（admin/manager/editor/viewer）, is_active
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, TimestampMixin, Base


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True, comment="邮箱（登录账号）")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="bcrypt 密码哈希")
    full_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="姓名")
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="viewer",
        comment="角色: admin / manager / editor / viewer",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
