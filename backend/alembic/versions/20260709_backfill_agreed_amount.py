"""V2.3 — 回填 payment_stages 中为 NULL 的 agreed_amount

现有数据中，部分 payment_stages 的 agreed_amount 为 NULL（在自动计算逻辑
上线前创建的节点）。对于 contract_amount 和 agreed_ratio 都存在的记录，
可以计算 agreed_amount = contract_amount × agreed_ratio。

Revision ID: 20260709_backfill_agreed_amount
Revises: 20260709_drop_fee_items
Create Date: 2026-07-09

变更:
1. 回填 t_contract_payment_stages 中 agreed_amount IS NULL 且合同有金额的记录
"""

from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa


revision: str = "20260709_backfill_agreed_amount"
down_revision: Union[str, None] = "20260709_drop_fee_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 回填 agreed_amount = contract_amount × agreed_ratio
    # 只更新同时满足条件的记录：
    #   - payment_stages.agreed_amount IS NULL
    #   - payment_stages.agreed_ratio > 0
    #   - 关联 contract.contract_amount > 0
    op.execute(
        """
        UPDATE t_contract_payment_stages ps
        SET agreed_amount = CAST(c.contract_amount * ps.agreed_ratio AS BIGINT)
        FROM t_contracts c
        WHERE ps.contract_id = c.id
          AND ps.agreed_amount IS NULL
          AND ps.agreed_ratio > 0
          AND c.contract_amount > 0
        """
    )


def downgrade() -> None:
    # 回滚：将自动计算的 agreed_amount 恢复为 NULL
    # 注：无法区分哪些是回填的、哪些是用户手动设置的，所以不回滚
    pass
