"""V2.2 — 补全支付节点字段、审核extra_fields、新建节点模板、注册台账表

Revision ID: 20260706_v2_2_business_phase1
Revises: 20260706_v2_2_field_mappings
Create Date: 2026-07-06

变更:
1. t_contract_payment_stages 新增 6 个字段:
   - node_name (节点名称)
   - agreed_ratio (约定支付比例)
   - agreed_amount (约定应支付金额)
   - planned_pay_date (预计支付日期)
   - is_completed (节点完成标记)
   - completed_at (完成时间)
2. t_progress_payment_review 新增 extra_fields JSONB 列
3. 新建 t_node_templates 表 (节点模板)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "20260706_v2_2_business_phase1"
down_revision: Union[str, None] = "20260706_v2_2_field_mappings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ════════════════════════════════════════════════
    # 1. t_contract_payment_stages 补字段
    # ════════════════════════════════════════════════
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("node_name", sa.String(100), nullable=True, comment="节点名称（如'合同签订''竣工验收'）"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("agreed_ratio", sa.Numeric(6, 4), nullable=True, comment="合同约定的该节点支付比例（如 0.1000 = 10%）"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("agreed_amount", sa.BigInteger(), nullable=True, comment="约定应支付金额（分）= contract_amount × agreed_ratio"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("planned_pay_date", sa.Date(), nullable=True, comment="预计支付日期（合同签订日 + 偏移天数）"),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false"),
            comment="该节点是否已完成（用户手动标记）",
        ),
    )
    op.add_column(
        "t_contract_payment_stages",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"),
    )

    # ════════════════════════════════════════════════
    # 2. t_progress_payment_review 补 extra_fields
    # ════════════════════════════════════════════════
    op.add_column(
        "t_progress_payment_review",
        sa.Column(
            "extra_fields", JSONB(), nullable=True,
            comment="审核类型特有的动态字段。施工审核示例: {\"建安工程费\": xxx, \"安全文明费\": xxx}",
        ),
    )

    # ════════════════════════════════════════════════
    # 3. 新建 t_node_templates 表
    # ════════════════════════════════════════════════
    op.create_table(
        "t_node_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()"), comment="主键"),
        sa.Column("template_name", sa.String(100), nullable=False, comment="模板名称（如'监理合同标准节点'）"),
        sa.Column("biz_type", sa.String(30), nullable=False, comment="业务类型: supervision/design/testing/construction/custom"),
        sa.Column("description", sa.Text(), nullable=True, comment="模板描述"),
        sa.Column("is_preset", sa.Boolean(), nullable=False, server_default=sa.text("false"), comment="True=系统预置, False=用户自定义"),
        sa.Column("stages", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb"), comment="节点配置数组 JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="软删除时间"),
    )
    op.create_index("ix_node_templates_biz_type", "t_node_templates", ["biz_type"])


def downgrade() -> None:
    # ── 3. 删除表 ──
    op.drop_index("ix_node_templates_biz_type")
    op.drop_table("t_node_templates")

    # ── 2. 删除 extra_fields ──
    op.drop_column("t_progress_payment_review", "extra_fields")

    # ── 1. 删除 t_contract_payment_stages 新增字段 ──
    op.drop_column("t_contract_payment_stages", "completed_at")
    op.drop_column("t_contract_payment_stages", "is_completed")
    op.drop_column("t_contract_payment_stages", "planned_pay_date")
    op.drop_column("t_contract_payment_stages", "agreed_amount")
    op.drop_column("t_contract_payment_stages", "agreed_ratio")
    op.drop_column("t_contract_payment_stages", "node_name")
