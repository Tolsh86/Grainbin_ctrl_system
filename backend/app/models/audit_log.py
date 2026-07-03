"""数据操作审计日志表 t_audit_logs"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, Base


class AuditLog(Base, UUIDMixin):
    __tablename__ = "t_audit_logs"

    table_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="操作表名")
    record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, comment="操作记录 ID")
    field_name: Mapped[str | None] = mapped_column(String(100), comment="修改字段名")
    old_value: Mapped[str | None] = mapped_column(Text, comment="旧值")
    new_value: Mapped[str | None] = mapped_column(Text, comment="新值")
    operation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="操作类型: INSERT/UPDATE/DELETE/CONFIRM",
    )
    modified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="操作人")
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="操作时间",
    )
    source: Mapped[str | None] = mapped_column(
        String(30), comment="来源: manual / ai_recognition / system",
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.operation_type} {self.table_name}.{self.field_name}>"
