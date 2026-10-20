"""合同支付记录表 t_contract_payments (V2.2 Refactor)

每笔支付记录对应一个支付节点，支持报送→批准→确认流程。
- reported_amount: 用户手动填写的报送金额
- approved_amount: 系统根据规则自动计算的批准金额
- status: pending(待确认) / confirmed(已确认) / rejected(已驳回)
- confirmed_at: 确认时间
- reject_reason: 驳回原因（status=rejected 时填写）
- payment_voucher: 确认支付时可上传的凭证编号
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


class ContractPayment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_contract_payments"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )
    contract_no: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="冗余 contract_no"
    )
    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contract_payment_stages.id"), index=True, comment="关联支付节点（可选）"
    )

    # ── 金额 ──
    reported_amount: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="报送金额（用户手动填，单位：分）"
    )
    approved_amount: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="批准金额（系统自动算，单位：分）"
    )

    # ── 凭证与备注 ──
    payment_voucher: Mapped[str | None] = mapped_column(
        String(500), comment="支付凭证编号（确认支付时上传）"
    )
    remark: Mapped[str | None] = mapped_column(
        Text, comment="备注"
    )

    # ── 台账分组（冗余自合同） ──
    ledger_group: Mapped[str | None] = mapped_column(
        String(20), comment="台账分组：construction/equipment/service/none"
    )

    # ── 审核确认 ──
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="状态：pending(待确认)/confirmed(已确认)/rejected(已驳回)"
    )
    reject_reason: Mapped[str | None] = mapped_column(
        Text, comment="驳回原因（status=rejected 时填写）"
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="确认时间（status=confirmed 时写入）"
    )

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", lazy="selectin")  # noqa: F821
    stage: Mapped["ContractPaymentStage | None"] = relationship(  # noqa: F821
        "ContractPaymentStage", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<ContractPayment {self.contract_no} "
            f"reported={self.reported_amount} approved={self.approved_amount} "
            f"status={self.status}>"
        )
