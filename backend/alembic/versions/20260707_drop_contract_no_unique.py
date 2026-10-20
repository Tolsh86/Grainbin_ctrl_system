"""V2.2 — 移除 contract_no 全局唯一约束，改为 (project_id, contract_no, contract_sub_type) 联合唯一

Revision ID: 20260707_drop_contract_no_unique
Revises: 20260707_phase2_fields
Create Date: 2026-07-07

变更:
  t_contracts.contract_no — 移除 unique=True，允许不同项目下同编号合同共存
  (project_id, contract_no, contract_sub_type) 联合唯一由 service 层保证
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260707_drop_contract_no_unique"
down_revision: Union[str, None] = "20260707_phase2_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop the unique constraint (auto-named by SQLAlchemy)
    op.execute(
        "DO $$ BEGIN "
        "  ALTER TABLE t_contracts DROP CONSTRAINT t_contracts_contract_no_key; "
        "EXCEPTION WHEN undefined_object THEN NULL; "
        "END $$;"
    )
    # Step 2: Drop the unique index and recreate as plain (non-unique) index
    # unique=True also creates a unique index ix_t_contracts_contract_no
    op.execute(
        "DO $$ BEGIN "
        "  DROP INDEX IF EXISTS ix_t_contracts_contract_no; "
        "  CREATE INDEX ix_t_contracts_contract_no ON t_contracts (contract_no); "
        "END $$;"
    )


def downgrade() -> None:
    op.create_unique_constraint("t_contracts_contract_no_key", "t_contracts", ["contract_no"])
