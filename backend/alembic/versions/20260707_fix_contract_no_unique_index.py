"""V2.2 — 修复 ix_t_contracts_contract_no 仍然是唯一索引的问题

Revision ID: 20260707_fix_contract_no_idx
Revises: 20260707_subtype_to_review_mode
Create Date: 2026-07-07

unique=True 在 PostgreSQL 生成两个东西：
1. UNIQUE CONSTRAINT → 上一迁移已删
2. UNIQUE INDEX → 没删，导致 t_contracts.contract_no 仍全局唯一

此迁移将唯一索引替换为普通索引。
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "20260707_fix_contract_no_idx"
down_revision: Union[str, None] = "20260707_subtype_to_review_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_t_contracts_contract_no")
    op.execute("CREATE INDEX ix_t_contracts_contract_no ON t_contracts (contract_no)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_t_contracts_contract_no")
    op.execute("CREATE UNIQUE INDEX ix_t_contracts_contract_no ON t_contracts (contract_no)")
