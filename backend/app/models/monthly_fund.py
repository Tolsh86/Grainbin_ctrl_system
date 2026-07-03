"""月报及资金相关表 (V2.0)

t_monthly_province_progress — 省市重点项目月进度（来源：文件7 2026年省市重点项目6月进度.xlsx）
t_monthly_target_plan        — 月度目标计划（来源：文件6 川西项目目标计划表，横向月份列转纵向）
t_fund_breakdown             — 资金来源分解（来源：文件5 续投项目Sheet M~R + U~Z 列）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


# ═══════════════════════════════════════════════════════════════════
# 省市重点项目月度进度
# ═══════════════════════════════════════════════════════════════════

class MonthlyProvinceProgress(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_monthly_province_progress"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    report_month: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="报告月份（如 2026-06-01）"
    )
    seq: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="序号（1~49）"
    )

    # ── 项目基础信息（冗余，方便单表查询）──
    project_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="项目名称"
    )
    construction_period: Mapped[str | None] = mapped_column(
        String(50), comment="建设起止年（如'2025-2027年'）"
    )
    construction_scale: Mapped[str | None] = mapped_column(
        Text, comment="建设内容及规模"
    )

    # ── 投资数据（单位：分。源数据：万元→×1,000,000）──
    planned_total_invest: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="计划总投资（分）"
    )
    cumulative_invest_by_2025: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="截至2025年底累计完成投资（分）"
    )
    planned_invest_2026: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="2026年预计投资（分）"
    )
    completed_invest_1_5m: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="1-5月完成投资（分）"
    )
    completed_invest_6m: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="6月完成投资-单月（分）"
    )
    completed_invest_1_6m: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="1-6月完成投资-半年度累计（分）"
    )
    completion_rate: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="完成率（1-6月/年度预计）"
    )

    # ── 形象进度描述 ──
    progress_apr: Mapped[str | None] = mapped_column(Text, comment="4月进度")
    progress_jun: Mapped[str | None] = mapped_column(Text, comment="6月进度")
    progress_target_2026: Mapped[str | None] = mapped_column(Text, comment="2026年工程形象进度-全年目标")

    # ── 参建单位 ──
    owner_unit: Mapped[str | None] = mapped_column(String(200), comment="业主单位")
    responsible_unit: Mapped[str | None] = mapped_column(String(200), comment="责任单位")
    remark: Mapped[str | None] = mapped_column(String(100), comment="备注（省重点项目级别标注）")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="monthly_progress", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ProvinceProgress {self.report_month} {self.project_name}>"


# ═══════════════════════════════════════════════════════════════════
# 月度目标计划（横向月份列 → 纵向存储）
# ═══════════════════════════════════════════════════════════════════

class MonthlyTargetPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_monthly_target_plan"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    plan_month: Mapped[date] = mapped_column(
        Date, nullable=False, comment="计划月份（如 2026-01-01）"
    )

    # ── 月度计划 ──
    monthly_planned_invest: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="月度计划投资额（分）。源数据：万元→×1,000,000。Row 8 数值"
    )
    monthly_planned_progress: Mapped[str | None] = mapped_column(
        Text, comment="月度计划形象进度（Row 7 长文本）"
    )

    # ── 月度实际 ──
    monthly_actual_invest: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="月度实际完成投资（分）"
    )
    monthly_actual_progress: Mapped[str | None] = mapped_column(
        Text, comment="月度实际形象进度"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="monthly_plans", lazy="selectin")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("project_id", "plan_month", name="uq_monthly_plan"),
    )

    def __repr__(self) -> str:
        return f"<MonthlyPlan {self.plan_month} invest={self.monthly_planned_invest}>"


# ═══════════════════════════════════════════════════════════════════
# 资金来源分解
# ═══════════════════════════════════════════════════════════════════

class FundBreakdown(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_fund_breakdown"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    fund_year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="资金所属年度（如 2025）"
    )
    fund_scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default="total",
        comment="资金范围：total(总投资来源)/annual_plan(年度计划来源)"
    )

    # ── 六类资金来源（单位：分。源数据：万元→×1,000,000）──
    central_province_fund: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="中省资金-中央+省级财政（分）"
    )
    special_general_bond: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="专项债/一般债（分）"
    )
    national_bond_fund: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="国债/基金（分）"
    )
    self_owned_fund: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="自有资金（分）"
    )
    financing_fund: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="融资资金-银行贷款等（分）"
    )
    other_fund: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="其他资金（分）"
    )

    # ── 汇总 ──
    cumulative_completed_invest: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="累计完成投资（分）"
    )
    annual_planned_invest: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="年度计划投资（分）"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="fund_breakdowns", lazy="selectin")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("project_id", "fund_year", "fund_scope", name="uq_fund_breakdown"),
    )

    def __repr__(self) -> str:
        return f"<FundBreakdown {self.fund_year} {self.fund_scope}>"
