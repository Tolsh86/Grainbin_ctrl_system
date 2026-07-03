"""二类费用台账表 t_secondary_cost_ledgers"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class SecondaryCostLedger(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_secondary_cost_ledgers"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目",
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="单位名称（检测/设计/监理/咨询）")
    cost_type: Mapped[str | None] = mapped_column(String(50), comment="费用类型")
    contract_amount: Mapped[int | None] = mapped_column(BigInteger, comment="合同金额（分）")
    payment_nodes: Mapped[dict | None] = mapped_column(JSONB, comment="支付节点定义（节点名称、比例、交付物）")
    paid_amount: Mapped[int | None] = mapped_column(BigInteger, comment="已支付金额（分）")
    unpaid_amount: Mapped[int | None] = mapped_column(BigInteger, comment="未支付金额（分）")
    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="未支付", comment="支付状态: 未支付 / 部分支付 / 已支付",
    )
    next_payment_node: Mapped[str | None] = mapped_column(String(100), comment="下一支付节点名称")
    expected_payment_date: Mapped[date | None] = mapped_column(Date, comment="预计支付日期")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<SecondaryCostLedger {self.company_name} project={self.project_id}>"
