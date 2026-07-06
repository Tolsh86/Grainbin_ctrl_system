"""V2.2 — t_field_mappings 增加 deleted_at/biz_type 字段

Revision ID: 20260706_v2_2_field_mappings
Revises: 20260703_v2_1_payments
Create Date: 2026-07-06

变更:
- t_field_mappings 新增 biz_type (业务类型) + deleted_at (软删除)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260706_v2_2_field_mappings"
down_revision: Union[str, None] = "20260703_v2_1_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── biz_type ──
    op.add_column(
        "t_field_mappings",
        sa.Column(
            "biz_type",
            sa.String(50),
            server_default="general",
            nullable=False,
            comment="业务类型: weekly/monthly/progress_payment/general",
        ),
    )
    op.create_index("ix_field_mappings_biz_type", "t_field_mappings", ["biz_type"])

    # ── deleted_at ──
    op.add_column(
        "t_field_mappings",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            default=None,
            comment="软删除时间",
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_field_mappings_biz_type")
    op.drop_column("t_field_mappings", "biz_type")
    op.drop_column("t_field_mappings", "deleted_at")
