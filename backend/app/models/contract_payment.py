"""合同支付记录表 t_contract_payments (V2.1)

来源：需求文档 二类费用 §7.4 支付台账
每笔实际支付记录对应一个支付节点，支持逐笔标记支付、上传凭证。
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
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

    # ── 支付信息 ──
    payment_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="实际支付日期"
    )
    payment_amount: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="本次支付金额（分）"
    )
    payment_voucher: Mapped[str | None] = mapped_column(
        String(500), comment="支付凭证（文件路径或编号）"
    )
    payer: Mapped[str | None] = mapped_column(
        String(200), comment="付款方"
    )
    payee: Mapped[str | None] = mapped_column(
        String(200), comment="收款方"
    )
    remark: Mapped[str | None] = mapped_column(
        Text, comment="备注"
    )

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ContractPayment {self.contract_no} {self.payment_date} amount={self.payment_amount}>"
