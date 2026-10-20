"""审核费用分项值表 t_review_fee_items (Phase2)

每条审核记录（t_progress_payment_review）下的费用分项实际填写值。
报送值和审定值分列存储，始终保留原始报送数据。
item_name 和 payment_ratio 是快照，fee_item_id 为可空 + ON DELETE SET NULL。
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, Base


class ReviewFeeItem(Base, UUIDMixin):
    __tablename__ = "t_review_fee_items"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_progress_payment_review.id"), nullable=False, index=True, comment="关联审核记录"
    )
    fee_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contract_fee_items.id", ondelete="SET NULL"),
        nullable=True, index=True, comment="关联费用分项模板（模板被删时置NULL）"
    )
    item_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="快照：费用分项名称"
    )
    payment_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="快照：本期付款比例"
    )
    reported_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="报送金额（分）"
    )
    reviewed_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="审定金额（分）"
    )
    remark: Mapped[str | None] = mapped_column(Text, comment="备注说明")

    # ── 关系 ──
    review: Mapped["ProgressPaymentReview"] = relationship("ProgressPaymentReview", back_populates="fee_items")
    fee_item: Mapped["ContractFeeItem | None"] = relationship("ContractFeeItem", back_populates="review_items")

    def __repr__(self) -> str:
        return f"<ReviewFeeItem {self.item_name} review={self.review_id}>"
