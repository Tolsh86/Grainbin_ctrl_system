"""周报相关表 (V2.0)

t_weekly_progress_report   — 周报-形象进度（来源：文件4 周报描述7-1.xlsx）
t_weekly_progress_metrics  — 周报-投资指标（来源：文件3 周报百分比计算表格.xlsx，2列 K-V 布局）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


# ═══════════════════════════════════════════════════════════════════
# 周报 — 形象进度
# ═══════════════════════════════════════════════════════════════════

class WeeklyProgressReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_weekly_progress_report"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    report_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="周报日期（如 2026-07-01）"
    )
    seq: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="序号（1~13）"
    )

    # ── 工程部位 ──
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dict_location.id"), comment="FK → dict_location"
    )
    location_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="形象部位（冗余，如'5#平房仓'）"
    )

    # ── 本周数据 ──
    weekly_progress_desc: Mapped[str | None] = mapped_column(
        Text, comment="本周形象描述"
    )
    weekly_output_reported: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="本周产值-施工单位上报（分）。源数据：万元→×1,000,000"
    )
    weekly_output_audited: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="本周产值-过控单位复核（分）"
    )

    # ── 累计数据 ──
    cumulative_output_reported: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="累计产值-施工上报（分）"
    )
    cumulative_output_audited: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="累计产值-过控复核（分）"
    )
    type2_expense: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="二类费用（分）"
    )
    total_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="合计=建安+二类费用（分）"
    )
    cumulative_progress_desc: Mapped[str | None] = mapped_column(
        Text, comment="累计形象描述"
    )
    review_date: Mapped[date | None] = mapped_column(
        Date, comment="复核日期"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="weekly_reports", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<WeeklyReport {self.report_date} seq={self.seq} {self.location_name}>"


# ═══════════════════════════════════════════════════════════════════
# 周报 — 投资指标（2列 K-V 布局转纵向）
# ═══════════════════════════════════════════════════════════════════

class WeeklyProgressMetrics(Base, UUIDMixin):
    __tablename__ = "t_weekly_progress_metrics"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    report_week: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="周报日期"
    )
    data_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, default="标准口径",
        comment="数据口径：标准口径/含设备购置费"
    )
    metric_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="指标名称（Col B 原文，12种枚举见数据字典）"
    )
    metric_value: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, comment="指标值（可能是百分比或金额）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="weekly_metrics", lazy="selectin")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("project_id", "report_week", "data_scope", "metric_name", name="uq_weekly_metrics"),
    )

    def __repr__(self) -> str:
        return f"<WeeklyMetric {self.report_week} {self.metric_name}={self.metric_value}>"
