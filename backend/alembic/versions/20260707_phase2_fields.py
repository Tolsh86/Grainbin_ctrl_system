"""V2.2 — 第二阶段字段：合同分组/费用分项/日报关联合同/月度台账状态

Revision ID: 20260707_phase2_fields
Revises: 20260706_v2_2_business_phase1
Create Date: 2026-07-07

变更:
1. t_contracts 新增 3 个字段:
   - contract_group (合同编号组)
   - contract_sub_type (合同分项类型)
   - fee_items (费用分项明细 JSONB)
2. t_contract_payment_stages 新增 4 个字段:
   - fee_item_id (关联费用分项ID)
   - triggered_at (节点触发时间)
   - reported_amount (累计报送产值)
   - reviewed_amount (累计审定产值)
3. t_contract_monthly_detail 新增 3 个字段:
   - source (数据来源)
   - status (确认状态)
   - cost_items_detail (分项级产值明细 JSONB)
4. t_data_rows 新增 3 个字段:
   - contract_id (关联合同)
   - status (审核状态)
   - cost_sub_type (费用分项类型)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "20260707_phase2_fields"
down_revision: Union[str, None] = "20260706_v2_2_business_phase1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ════════════════════════════════════════════════
    # 1. t_contracts 新增字段
    # ════════════════════════════════════════════════
    op.add_column(
        "t_contracts",
        sa.Column("contract_group", sa.String(50), nullable=True, comment="合同编号组，用于归组同项目下多份独立合同"),
    )
    op.add_column(
        "t_contracts",
        sa.Column("contract_sub_type", sa.String(50), nullable=True, server_default=sa.text("'construction'"), comment="合同分项类型：construction(建安)/equipment(设备)/design(设计)/supervision(监理)/cost_consult(造价)/settlement(结算)/survey(勘察)/testing(检测)/migrant_worker(农民工专户)"),
    )
    op.add_column(
        "t_contracts",
        sa.Column("fee_items", JSONB(), nullable=True, comment="费用分项明细 [{id, name, amount, ratio}]，咨询服务类合同必填。id 为前端生成的 UUID，支付节点通过 fee_item_id 关联"),
    )

    # ════════════════════════════════════════════════
    # 2. t_contract_payment_stages 新增字段
    # ════════════════════════════════════════════════
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("fee_item_id", UUID(as_uuid=True), nullable=True, comment="关联费用分项ID，对应 t_contracts.fee_items[].id"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("triggered_at", sa.Date(), nullable=True, comment="节点触发时间。咨询类合同节点达到后填入当月，下月查询时排除已触发的节点"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("reported_amount", sa.BigInteger(), nullable=True, server_default=sa.text("0"), comment="累计报送产值（施工方报送，单位：分）"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("reviewed_amount", sa.BigInteger(), nullable=True, server_default=sa.text("0"), comment="累计审定产值（过控审定，单位：分）"),
    )

    # ════════════════════════════════════════════════
    # 3. t_contract_monthly_detail 新增字段
    # ════════════════════════════════════════════════
    op.add_column(
        "t_contract_monthly_detail",
        sa.Column("source", sa.String(20), nullable=False, server_default=sa.text("'auto'"), comment="数据来源：auto(系统汇总)/manual(人工审定)"),
    )
    op.add_column(
        "t_contract_monthly_detail",
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'"), comment="确认状态：pending/confirmed"),
    )
    op.add_column(
        "t_contract_monthly_detail",
        sa.Column("cost_items_detail", JSONB(), nullable=True, comment="分项级产值明细 {items: [{fee_item_id, name, output, ratio, payable}]}"),
    )

    # ════════════════════════════════════════════════
    # 4. t_data_rows 新增字段
    # ════════════════════════════════════════════════
    op.add_column(
        "t_data_rows",
        sa.Column("contract_id", UUID(as_uuid=True), sa.ForeignKey("t_contracts.id"), nullable=True, comment="关联合同"),
    )
    op.add_column(
        "t_data_rows",
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'draft'"), comment="审核状态：draft/submitted/reviewed/rejected/confirmed"),
    )
    op.add_column(
        "t_data_rows",
        sa.Column("cost_sub_type", sa.String(50), nullable=True, comment="费用分项类型：construction/safety_civilization/..."),
    )
    op.create_index(op.f("ix_t_data_rows_contract_id"), "t_data_rows", ["contract_id"], unique=False)


def downgrade() -> None:
    # ── 4. t_data_rows 回滚 ──
    op.drop_index(op.f("ix_t_data_rows_contract_id"), table_name="t_data_rows")
    op.drop_column("t_data_rows", "cost_sub_type")
    op.drop_column("t_data_rows", "status")
    op.drop_column("t_data_rows", "contract_id")

    # ── 3. t_contract_monthly_detail 回滚 ──
    op.drop_column("t_contract_monthly_detail", "cost_items_detail")
    op.drop_column("t_contract_monthly_detail", "status")
    op.drop_column("t_contract_monthly_detail", "source")

    # ── 2. t_contract_payment_stages 回滚 ──
    op.drop_column("t_contract_payment_stages", "reviewed_amount")
    op.drop_column("t_contract_payment_stages", "reported_amount")
    op.drop_column("t_contract_payment_stages", "triggered_at")
    op.drop_column("t_contract_payment_stages", "fee_item_id")

    # ── 1. t_contracts 回滚 ──
    op.drop_column("t_contracts", "fee_items")
    op.drop_column("t_contracts", "contract_sub_type")
    op.drop_column("t_contracts", "contract_group")
