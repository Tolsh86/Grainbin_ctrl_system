"""报告相关表

t_report_templates — 动态报告模板配置
t_reports          — 报告实例
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class ReportTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_report_templates"

    template_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="模板名称")
    report_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="类型: weekly / monthly / payment_report",
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="版本号")
    schema_json: Mapped[dict | None] = mapped_column(JSONB, comment="JSON Schema 定义（字段、校验规则、布局）")
    word_template_path: Mapped[str | None] = mapped_column(String(500), comment="Word 模板文件存储路径")
    ppt_template_path: Mapped[str | None] = mapped_column(String(500), comment="PPT 模板文件存储路径")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否为当前启用版本")

    def __repr__(self) -> str:
        return f"<ReportTemplate {self.template_name} v{self.version}>"


class Report(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目",
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_report_templates.id"), comment="关联模板",
    )
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="类型: weekly / monthly")
    period_start: Mapped[date | None] = mapped_column(Date, comment="报告周期开始")
    period_end: Mapped[date | None] = mapped_column(Date, comment="报告周期结束")
    data_payload: Mapped[dict | None] = mapped_column(JSONB, comment="报告全部字段数据（动态结构）")
    report_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="草稿", comment="状态: 草稿 / 待审核 / 已确认 / 已发布",
    )
    ai_generated_content: Mapped[dict | None] = mapped_column(JSONB, comment="AI 生成的文字建议快照")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="编制人")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="审核人")
    review_comment: Mapped[str | None] = mapped_column(Text, comment="审核意见")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821
    template: Mapped["ReportTemplate | None"] = relationship("ReportTemplate", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Report {self.report_type} project={self.project_id}>"
