"""Phase2 #4 — 创建审核费用分项值表 t_review_fee_items

每条审核记录下的费用分项实际填写值。报送值和审定值分列存储。
item_name 和 payment_ratio 是快照，fee_item_id 为可空 + ON DELETE SET NULL。

Revision ID: 20260710_p2_review_fee_items
Revises: 20260710_p2_contract_fee_items
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_p2_review_fee_items"
down_revision: Union[str, None] = "20260710_p2_contract_fee_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "t_review_fee_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), comment="主键"),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("t_progress_payment_review.id"), nullable=False, index=True, comment="关联审核记录"),
        sa.Column(
            "fee_item_id", UUID(as_uuid=True),
            sa.ForeignKey("t_contract_fee_items.id", ondelete="SET NULL"),
            nullable=True, index=True,
            comment="关联费用分项模板（模板被删时置NULL）"
        ),
        sa.Column("item_name", sa.String(100), nullable=False, comment="快照：费用分项名称"),
        sa.Column("payment_ratio", sa.Numeric(6, 4), nullable=True, comment="快照：本期付款比例"),
        sa.Column("reported_amount", sa.BigInteger(), server_default="0", comment="报送金额（分）"),
        sa.Column("reviewed_amount", sa.BigInteger(), server_default="0", comment="审定金额（分）"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注说明"),
    )


def downgrade() -> None:
    op.drop_table("t_review_fee_items")
