"""进度款审核表 t_progress_payment_review (V2.0 → Phase2 改造)

4 类单位（设备/设计/施工/监理过控）共用单表，通过 review_type 区分。
金额单位：分（源数据为元，导入时 ×100）。

Phase2 变更：
- 删除 13 个硬编码列（period_month, period_no, payment_ratio, 10 个费用/比例列）
- 新增 period_id（NOT NULL, FK → t_reporting_periods）
- contract_id 改为 NOT NULL
- audit_status default 改为 'draft'
- 新增 fee_items 关系（费用分项拆分到 t_review_fee_items）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


class ProgressPaymentReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_progress_payment_review"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_reporting_periods.id"), nullable=False, index=True, comment="关联期次"
    )

    # ── 审核标识 ──
    review_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="审核类型：设备/设计/施工/监理过控"
    )
    applicant_unit: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="申请单位"
    )

    # ── 通用金额字段 (所有 review_type 共有，单位：分) ──
    contract_amount: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="合同金额（分）"
    )
    cumulative_reported_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="累计报送产值（分）"
    )
    current_audited_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="本期审定产值（分）= Σ 各分项 reviewed_amount（确认审定时由 service 从 fee_items 汇总写入）"
    )
    cumulative_audited_output: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="累计审定产值（分）"
    )
    cumulative_audited_payable: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="累计审定应付款（分）= Σ 各分项 reviewed_amount × payment_ratio（确认审定时由 service 从 fee_items 汇总写入）"
    )

    # ── 审核类型特有动态字段 ──
    extra_fields: Mapped[dict | None] = mapped_column(
        JSONB, comment="审核类型特有的动态字段"
    )

    # ── 备注 & 税率 ──
    remark: Mapped[str | None] = mapped_column(Text, comment="备注")
    tax_rate: Mapped[float | None] = mapped_column(
        Numeric(4, 2), comment="税率（如 9.00=9%）"
    )

    # ── 审核状态 ──
    audit_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="审核状态：draft/submitted/reviewed"
    )
    submit_date: Mapped[date | None] = mapped_column(Date, comment="申报日期")
    audited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_users.id"), comment="审核人"
    )
    audited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="审核时间"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="progress_reviews", lazy="selectin")  # noqa: F821
    contract: Mapped["Contract"] = relationship("Contract", lazy="selectin")  # noqa: F821
    period: Mapped["ReportingPeriod"] = relationship("ReportingPeriod", back_populates="progress_reviews")
    fee_items: Mapped[list["ReviewFeeItem"]] = relationship(
        "ReviewFeeItem", back_populates="review", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ProgressReview {self.review_type} period_id={self.period_id}>"
