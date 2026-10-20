"""报送期次表 t_reporting_periods + 期次-合同关联表 t_period_contracts (Phase2)

期次是审核模块的核心驱动表。一期 = 汇总表中一个月内所有供应商的审核数据集合。
PeriodContract 是纯中间表，记录每期选了哪些合同参与审核。
"""

from __future__ import annotations

import uuid

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.models.base import UUIDMixin, TimestampMixin, Base


class ReportingPeriod(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_reporting_periods"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    period_no: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="期次编号（1-based）"
    )
    period_month: Mapped[str] = mapped_column(
        String(7), nullable=False, comment="期次月份 YYYY-MM"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="状态：draft/in_progress/reviewed/closed"
    )
    remark: Mapped[str | None] = mapped_column(Text, comment="备注说明")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821
    period_contracts: Mapped[list["PeriodContract"]] = relationship(
        "PeriodContract", back_populates="period", lazy="selectin"
    )
    progress_reviews: Mapped[list["ProgressPaymentReview"]] = relationship(
        "ProgressPaymentReview", back_populates="period", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "period_no", name="uq_period_project_no"),
    )

    def __repr__(self) -> str:
        return f"<ReportingPeriod project={self.project_id} no={self.period_no} {self.period_month}>"


class PeriodContract(Base, UUIDMixin):
    """期次-合同关联表（纯中间表，无时间戳）"""

    __tablename__ = "t_period_contracts"

    period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_reporting_periods.id"), nullable=False, index=True, comment="关联期次"
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )

    # ── 关系 ──
    period: Mapped["ReportingPeriod"] = relationship("ReportingPeriod", back_populates="period_contracts")
    contract: Mapped["Contract"] = relationship("Contract", lazy="selectin")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("period_id", "contract_id", name="uq_period_contract"),
    )

    def __repr__(self) -> str:
        return f"<PeriodContract period={self.period_id} contract={self.contract_id}>"
