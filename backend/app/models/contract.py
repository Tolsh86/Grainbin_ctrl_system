"""合同相关表 (V2.0)

t_contracts                  — 合同主表（来源：文件1 合同台账 Sheet）
t_contract_payment_stages    — 合同支付阶段（G~K 列 → 阶段子表）
t_contract_monthly_detail    — 合同月度明细（P~AO 列 → 纵向）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


# ═══════════════════════════════════════════════════════════════════
# 合同主表
# ═══════════════════════════════════════════════════════════════════

class Contract(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_contracts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"
    )

    # ── 业务字段 (对应 Excel 列 A~F) ──
    seq: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="行序号"
    )
    contract_no: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True, comment="合同编号（CX001~CX018，业务主键）"
    )
    supplier_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="供应商/承包单位名称"
    )
    contract_desc: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="合同内容/类型描述"
    )
    sign_date: Mapped[date | None] = mapped_column(
        Date, comment="签订日期"
    )
    contract_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="合同金额（分）⚠ 源数据此列多数为空"
    )

    # ── 合同分类 ──
    contract_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="secondary",
        comment="合同类型：main(主合同)/secondary(二类费用)/supplementary(补充)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
        comment="状态：active(执行中)/expired(已到期)/terminated(已终止)"
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", back_populates="contracts", lazy="selectin")  # noqa: F821
    payment_stages: Mapped[list["ContractPaymentStage"]] = relationship(
        "ContractPaymentStage", back_populates="contract", lazy="selectin"
    )
    monthly_details: Mapped[list["ContractMonthlyDetail"]] = relationship(
        "ContractMonthlyDetail", back_populates="contract", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Contract {self.contract_no} {self.contract_desc}>"


# ═══════════════════════════════════════════════════════════════════
# 合同支付阶段表 (替代 V1.0 的 t_contract_versions + t_contract_clauses)
# ═══════════════════════════════════════════════════════════════════

class ContractPaymentStage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_contract_payment_stages"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )
    contract_no: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="冗余 contract_no"
    )

    # ── 支付阶段 ──
    stage_order: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="阶段序号（1=施工前/预付款, 2=施工中, 3=竣工, 4=结算后, 5=质保尾款, 0=汇总行）"
    )
    stage_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="阶段名称（施工前阶段/施工中阶段/竣工阶段/尾款阶段）"
    )
    payment_terms: Mapped[str | None] = mapped_column(
        Text, comment="支付条款原文"
    )

    # ── 汇总数据 (仅在 stage_order=0 时有意义) ──
    cumulative_paid: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="累计已付（分）"
    )
    remaining_unpaid: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="剩余未付（分）"
    )
    paid_ratio: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="已付比例（可能为 NULL，源数据有 #DIV/0!）"
    )
    remaining_ratio: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="剩余未付比例"
    )

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", back_populates="payment_stages")

    def __repr__(self) -> str:
        return f"<PaymentStage {self.contract_no} stage={self.stage_order} {self.stage_name}>"


# ═══════════════════════════════════════════════════════════════════
# 合同月度明细表 (横向月份列 → 纵向存储)
# ═══════════════════════════════════════════════════════════════════

class ContractMonthlyDetail(Base, UUIDMixin):
    __tablename__ = "t_contract_monthly_detail"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )
    contract_no: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="冗余 contract_no"
    )

    # ── 月份 ──
    detail_month: Mapped[date] = mapped_column(
        Date, nullable=False, comment="月份（如 2026-01-01）。源数据为 Excel 日期序列值"
    )

    # ── 支付金额 (来自 合同支付情况 Sheet，单位：分) ──
    payment_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="当月支付金额（分）"
    )

    # ── 产值金额 (来自 产值情况 Sheet，单位：分) ──
    output_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="当月产值（分）"
    )
    est_cumulative_payable: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="预估累计应支付（分）"
    )
    actual_cumulative_paid: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="实际累计已支付（分）"
    )
    est_remaining_unpaid: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="预估剩余未支付（分）"
    )
    cumulative_completed: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="累计已完成产值（分）"
    )
    remaining_uncompleted: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="剩余未完成产值（分）"
    )
    completed_ratio: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="已完比例"
    )
    remaining_ratio: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="剩余未完比例"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", back_populates="monthly_details")

    __table_args__ = (
        UniqueConstraint("contract_no", "detail_month", name="uq_contract_monthly"),
    )

    def __repr__(self) -> str:
        return f"<MonthlyDetail {self.contract_no} {self.detail_month}>"
