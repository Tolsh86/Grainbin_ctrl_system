"""AI 任务表 t_ai_tasks

追踪所有 AI 异步任务（文档解析、报告生成、审核分析）的执行状态。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import UUIDMixin, Base


class AiTask(Base, UUIDMixin):
    __tablename__ = "t_ai_tasks"

    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="data_recognition / weekly_report / payment_audit / qa / excel_parse / progress_audit",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending / running / success / failed / cancelled",
    )
    input_refs: Mapped[dict | None] = mapped_column(
        JSONB, default=dict, comment="输入引用（文件ID、表ID等）"
    )
    output: Mapped[dict | None] = mapped_column(
        JSONB, comment="任务输出结果"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, comment="错误消息"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="开始时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, comment="执行耗时（毫秒）"
    )
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), comment="操作人"
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), comment="所属项目"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间"
    )

    def __repr__(self) -> str:
        return f"<AiTask {self.task_type} status={self.status}>"
