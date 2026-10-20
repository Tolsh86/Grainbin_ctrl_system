"""合同费用分项定义表 t_contract_fee_items (Phase2)

每份合同预先定义自己的费用分项（如施工合同有"建安工程费"+"安全文明施工费"、
监理合同有"监理服务费"+"造价咨询费"+"结算服务费"）。
审核时以此为模板生成 t_review_fee_items 的快照值。
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


class ContractFeeItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_contract_fee_items"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"
    )
    item_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="费用分项名称"
    )
    contract_amount: Mapped[int | None] = mapped_column(
        BigInteger, default=0, comment="该分项的合同金额（分）"
    )
    current_ratio: Mapped[float | None] = mapped_column(
        Numeric(6, 4), comment="当前期次付款比例（如 0.1000=10%），随审核进度可变"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="排序序号"
    )
    remark: Mapped[str | None] = mapped_column(Text, comment="备注说明")

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", lazy="selectin")  # noqa: F821
    review_items: Mapped[list["ReviewFeeItem"]] = relationship(
        "ReviewFeeItem", back_populates="fee_item", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ContractFeeItem {self.item_name} contract={self.contract_id}>"
