"""Phase2 #2 — 创建期次-合同关联表 t_period_contracts

记录每个期次选了哪些合同参与审核。创建期次时根据用户勾选写入。

Revision ID: 20260710_p2_period_contracts
Revises: 20260710_p2_reporting_periods
Create Date: 2026-07-10
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260710_p2_period_contracts"
down_revision: Union[str, None] = "20260710_p2_reporting_periods"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "t_period_contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"), comment="主键"),
        sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("t_reporting_periods.id"), nullable=False, index=True, comment="关联期次"),
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"),
    )
    op.create_unique_constraint("uq_period_contract", "t_period_contracts", ["period_id", "contract_id"])


def downgrade() -> None:
    op.drop_table("t_period_contracts")
