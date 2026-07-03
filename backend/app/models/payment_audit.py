"""进度款审核台账表 t_payment_audits"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class PaymentAudit(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_payment_audits"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目",
    )
    period_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="第几期次")
    constructor_name: Mapped[str | None] = mapped_column(String(200), comment="施工单位名称")
    declare_amount: Mapped[int | None] = mapped_column(BigInteger, comment="申报金额（分）")
    ai_suggest_amount: Mapped[int | None] = mapped_column(BigInteger, comment="AI 建议审核金额（分）")
    final_amount: Mapped[int | None] = mapped_column(BigInteger, comment="终审金额（分）")
    deduct_amount: Mapped[int | None] = mapped_column(BigInteger, comment="核减金额（分）")
    deduct_reason: Mapped[dict | None] = mapped_column(JSONB, comment="核减原因列表（AI 生成加人工补充）")
    items_json: Mapped[dict | None] = mapped_column(JSONB, comment="工程量清单明细 JSON")
    ai_findings: Mapped[dict | None] = mapped_column(JSONB, comment="AI 审核发现异常项列表")
    audit_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="待审核", comment="状态: 待审核 / 已审核 / 已支付",
    )
    submit_date: Mapped[date | None] = mapped_column(Date, comment="提交日期")
    audited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="审核人")
    audited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="审核时间")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PaymentAudit project={self.project_id} period={self.period_no}>"
