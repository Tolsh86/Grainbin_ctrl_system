"""用户表 t_users

字段：username, password_hash, real_name, email, role, project_permissions,
      is_active, last_login_at, deleted_at
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="登录名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="bcrypt 密码哈希"
    )
    real_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="真实姓名"
    )
    email: Mapped[str | None] = mapped_column(
        String(200), unique=True, comment="邮箱"
    )
    role: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="admin / project_manager / auditor / operator / viewer",
    )
    project_permissions: Mapped[dict | None] = mapped_column(
        JSONB, default=list, comment="数据权限（项目ID数组）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="最后登录时间"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role}>"
