"""Initial schema — V2.0 全部表

Revision ID: 20260703_v2_initial
Revises: None
Create Date: 2026-07-03

创建 18 张核心表 + 10 张字典表 + 全部索引与约束。
基于数据字典 V2.0（7 个 Excel 源文件的分析结果）。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260703_v2_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 扩展 ──
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"vector\"")

    # ═══════════════════════════════════════════════════════════════
    # 字典表 (10 张)
    # ═══════════════════════════════════════════════════════════════
    _create_dict_table("dict_project_nature", "项目性质：功能性项目/商业性项目")
    _create_dict_table("dict_invest_timing", "投资时序：新投项目/续投项目")
    _create_dict_table("dict_invest_nature", "投资性质：固定资产投资/股权投资/其他投资")
    _create_dict_table("dict_invest_structure", "投资结构：基础设施类/民生和社会事业类/生态环保类")
    _create_dict_table("dict_invest_field", "投资领域：装备制造/食品饮料/材料化工/...")
    _create_dict_table("dict_project_level", "项目级别：省重点项目/市重点项目/子项")
    _create_dict_table("dict_location", "工程部位：5#平房仓/工作塔区域/...")
    _create_dict_table("dict_owner_unit", "业主单位：产投/发展/商投/...")
    _create_dict_table("dict_supplier", "供应商/承包单位")
    _create_dict_table("dict_review_type", "审核类型：设备/设计/施工/监理过控")

    # ═══════════════════════════════════════════════════════════════
    # 系统表 (3 张)
    # ═══════════════════════════════════════════════════════════════
    _create_users_table()
    _create_audit_logs_table()
    _create_ai_tasks_table()

    # ═══════════════════════════════════════════════════════════════
    # 业务核心表 (15 张)
    # ═══════════════════════════════════════════════════════════════
    _create_projects_table()
    _create_contracts_table()
    _create_contract_payment_stages_table()
    _create_contract_monthly_detail_table()
    _create_progress_payment_review_table()
    _create_weekly_progress_report_table()
    _create_weekly_progress_metrics_table()
    _create_monthly_province_progress_table()
    _create_monthly_target_plan_table()
    _create_fund_breakdown_table()
    _create_data_rows_table()
    _create_report_templates_table()
    _create_reports_table()
    _create_knowledge_docs_table()
    _create_knowledge_chunks_table()

    # ═══════════════════════════════════════════════════════════════
    # 数据导入流水线 (4 张) — 依赖 t_projects + t_data_rows
    # ═══════════════════════════════════════════════════════════════
    _create_ingest_tables()

    # ═══════════════════════════════════════════════════════════════
    # 自定义索引
    # ═══════════════════════════════════════════════════════════════
    _create_custom_indexes()


def downgrade() -> None:
    tables = [
        "t_knowledge_chunks", "t_knowledge_docs",
        "t_reports", "t_report_templates",
        "t_data_rows",
        "t_fund_breakdown", "t_monthly_target_plan", "t_monthly_province_progress",
        "t_weekly_progress_metrics", "t_weekly_progress_report",
        "t_progress_payment_review",
        "t_contract_monthly_detail", "t_contract_payment_stages", "t_contracts",
        # ingest pipeline (depends on t_data_rows + t_projects)
        "t_ingest_errors", "t_ingest_rows", "t_ingest_batches", "t_field_mappings",
        "t_projects",
        "t_ai_tasks", "t_audit_logs", "t_users",
    ]
    dict_tables = [
        "dict_review_type", "dict_supplier", "dict_owner_unit", "dict_location",
        "dict_project_level", "dict_invest_field", "dict_invest_structure",
        "dict_invest_nature", "dict_invest_timing", "dict_project_nature",
    ]
    for t in dict_tables + tables:
        op.drop_table(t)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _pk():
    return sa.Column("id", postgresql.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()"))

def _ts():
    """created_at + updated_at columns."""
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="更新时间"),
    ]

def _fk(target, nullable=False, comment=""):
    """UUID FK column with index."""
    return sa.Column(
        f"{target}_id", postgresql.UUID,
        sa.ForeignKey(f"t_{target}s.id"),  # simplified: always adds 's'
        nullable=nullable, comment=comment,
    )


def _create_dict_table(name, comment):
    op.create_table(
        name,
        _pk(),
        sa.Column("code", sa.String(50), unique=True, nullable=False, index=True, comment="字典编码"),
        sa.Column("name", sa.String(100), nullable=False, comment="显示名称"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序序号"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        comment=comment,
    )


def _create_users_table():
    op.create_table(
        "t_users",
        _pk(),
        sa.Column("username", sa.String(50), unique=True, nullable=False, comment="登录名"),
        sa.Column("password_hash", sa.String(255), nullable=False, comment="bcrypt哈希"),
        sa.Column("real_name", sa.String(100), nullable=False, comment="真实姓名"),
        sa.Column("email", sa.String(200), unique=True, comment="邮箱"),
        sa.Column("role", sa.String(30), nullable=False, comment="admin/project_manager/auditor/operator/viewer"),
        sa.Column("project_permissions", postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), comment="数据权限（项目ID数组）"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), comment="最后登录时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除"),
        *_ts(),
        comment="用户与权限表",
    )
    op.create_index("ix_users_username", "t_users", ["username"])


def _create_audit_logs_table():
    op.create_table(
        "t_audit_logs",
        _pk(),
        sa.Column("table_name", sa.String(50), nullable=False, comment="操作的表名"),
        sa.Column("record_id", postgresql.UUID, comment="操作记录ID"),
        sa.Column("field_name", sa.String(100), comment="修改的字段名"),
        sa.Column("old_value", sa.Text, comment="修改前值"),
        sa.Column("new_value", sa.Text, comment="修改后值"),
        sa.Column("operation_type", sa.String(20), nullable=False, comment="INSERT/UPDATE/DELETE/CONFIRM/EXPORT"),
        sa.Column("modified_by", postgresql.UUID, comment="操作人"),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="修改时间"),
        sa.Column("source", sa.String(30), comment="manual/ai_recognition/system"),
        comment="审计日志表",
    )
    op.create_index("ix_audit_logs_table_record", "t_audit_logs", ["table_name", "record_id"])
    op.create_index("ix_audit_logs_modified_at", "t_audit_logs", [sa.text("modified_at DESC")])


def _create_ai_tasks_table():
    op.create_table(
        "t_ai_tasks",
        _pk(),
        sa.Column("task_type", sa.String(50), nullable=False, comment="data_recognition/weekly_report/payment_audit/qa/excel_parse"),
        sa.Column("status", sa.String(20), server_default="pending", comment="pending/running/success/failed/cancelled"),
        sa.Column("input_refs", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="输入引用"),
        sa.Column("output", postgresql.JSONB, comment="任务输出"),
        sa.Column("error_message", sa.Text, comment="错误消息"),
        sa.Column("started_at", sa.DateTime(timezone=True), comment="开始时间"),
        sa.Column("finished_at", sa.DateTime(timezone=True), comment="完成时间"),
        sa.Column("duration_ms", sa.Integer, comment="执行耗时（毫秒）"),
        sa.Column("operator_id", postgresql.UUID, comment="操作人"),
        sa.Column("project_id", postgresql.UUID, comment="所属项目"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        comment="AI任务表",
    )


def _create_projects_table():
    op.create_table(
        "t_projects",
        _pk(),
        sa.Column("project_name", sa.String(200), nullable=False, comment="项目名称"),
        sa.Column("project_code", sa.String(50), unique=True, nullable=False, index=True, comment="项目编码（业务唯一标识）"),
        # 项目分类
        sa.Column("project_nature", sa.String(50), nullable=False, server_default="功能性项目", comment="项目性质"),
        sa.Column("invest_timing", sa.String(20), nullable=False, server_default="续投项目", comment="投资时序"),
        sa.Column("invest_nature", sa.String(50), comment="投资性质"),
        sa.Column("invest_structure", sa.String(50), comment="投资结构"),
        sa.Column("invest_field", sa.String(100), comment="投资领域"),
        sa.Column("implement_body", sa.String(200), comment="实施主体"),
        sa.Column("implement_period", sa.String(50), comment="实施时间"),
        sa.Column("expected_return", sa.Text, comment="投资预期收益"),
        sa.Column("business_class", sa.String(20), comment="业务划分"),
        sa.Column("region", sa.String(20), nullable=False, server_default="市内", comment="区域"),
        # 行政属性
        sa.Column("importance", sa.String(10), comment="重要性"),
        sa.Column("supervising_dept", sa.String(200), comment="行业归口主管部门"),
        sa.Column("project_level_remark", sa.String(100), comment="项目级别备注"),
        sa.Column("responsible_unit", sa.String(200), comment="责任单位"),
        # 建设内容
        sa.Column("construction_content", sa.Text, comment="项目内容"),
        sa.Column("construction_scale", sa.Text, comment="建设内容及规模"),
        sa.Column("construction_period", sa.String(50), comment="建设周期"),
        # 投资金额（分）
        sa.Column("planned_total_invest", sa.BigInteger, nullable=False, server_default="0", comment="计划总投资（分）"),
        sa.Column("planned_invest_2026", sa.BigInteger, server_default="0", comment="2026年计划投资（分）"),
        # 参建单位
        sa.Column("owner_unit", sa.String(200), comment="业主单位"),
        # 质量安全
        sa.Column("quality_target", sa.String(50), nullable=False, server_default="合格", comment="质量目标"),
        sa.Column("safety_target", sa.String(100), comment="安全目标"),
        # 状态
        sa.Column("project_status", sa.String(20), nullable=False, server_default="preparing", comment="preparing/constructing/completed/suspended"),
        # 时间戳
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除"),
        *_ts(),
        comment="项目主表（V2.0 — 30+字段）",
    )


def _create_contracts_table():
    op.create_table(
        "t_contracts",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("seq", sa.Integer, nullable=False, comment="行序号"),
        sa.Column("contract_no", sa.String(20), unique=True, nullable=False, index=True, comment="合同编号（CX001~CX018）"),
        sa.Column("supplier_name", sa.String(200), nullable=False, comment="供应商"),
        sa.Column("contract_desc", sa.String(500), nullable=False, comment="合同内容描述"),
        sa.Column("sign_date", sa.Date, comment="签订日期"),
        sa.Column("contract_amount", sa.BigInteger, server_default="0", comment="合同金额（分）⚠ 源数据多数为空"),
        sa.Column("contract_type", sa.String(30), nullable=False, server_default="secondary", comment="main/secondary/supplementary"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="active/expired/terminated"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除"),
        *_ts(),
        comment="合同主表（V2.0）",
    )


def _create_contract_payment_stages_table():
    op.create_table(
        "t_contract_payment_stages",
        _pk(),
        sa.Column("contract_id", postgresql.UUID, sa.ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"),
        sa.Column("contract_no", sa.String(20), nullable=False, index=True, comment="冗余"),
        sa.Column("stage_order", sa.Integer, nullable=False, comment="阶段序号"),
        sa.Column("stage_name", sa.String(50), nullable=False, comment="阶段名称"),
        sa.Column("payment_terms", sa.Text, comment="支付条款原文"),
        sa.Column("cumulative_paid", sa.BigInteger, server_default="0", comment="累计已付（分）"),
        sa.Column("remaining_unpaid", sa.BigInteger, server_default="0", comment="剩余未付（分）"),
        sa.Column("paid_ratio", sa.Numeric(8, 4), comment="已付比例"),
        sa.Column("remaining_ratio", sa.Numeric(8, 4), comment="剩余未付比例"),
        *_ts(),
        comment="合同支付阶段表",
    )


def _create_contract_monthly_detail_table():
    op.create_table(
        "t_contract_monthly_detail",
        _pk(),
        sa.Column("contract_id", postgresql.UUID, sa.ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同"),
        sa.Column("contract_no", sa.String(20), nullable=False, index=True, comment="冗余"),
        sa.Column("detail_month", sa.Date, nullable=False, comment="月份"),
        # 支付
        sa.Column("payment_amount", sa.BigInteger, server_default="0", comment="当月支付金额（分）"),
        # 产值
        sa.Column("output_amount", sa.BigInteger, server_default="0", comment="当月产值（分）"),
        sa.Column("est_cumulative_payable", sa.BigInteger, server_default="0", comment="预估累计应支付（分）"),
        sa.Column("actual_cumulative_paid", sa.BigInteger, server_default="0", comment="实际累计已支付（分）"),
        sa.Column("est_remaining_unpaid", sa.BigInteger, server_default="0", comment="预估剩余未支付（分）"),
        sa.Column("cumulative_completed", sa.BigInteger, server_default="0", comment="累计已完成产值（分）"),
        sa.Column("remaining_uncompleted", sa.BigInteger, server_default="0", comment="剩余未完成产值（分）"),
        sa.Column("completed_ratio", sa.Numeric(8, 4), comment="已完比例"),
        sa.Column("remaining_ratio", sa.Numeric(8, 4), comment="剩余未完比例"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        sa.UniqueConstraint("contract_no", "detail_month", name="uq_contract_monthly"),
        comment="合同月度明细表",
    )


def _create_progress_payment_review_table():
    op.create_table(
        "t_progress_payment_review",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("contract_id", postgresql.UUID, sa.ForeignKey("t_contracts.id"), index=True, comment="关联合同"),
        sa.Column("review_type", sa.String(20), nullable=False, index=True, comment="设备/设计/施工/监理过控"),
        sa.Column("period_month", sa.String(50), nullable=False, comment="期数/月份"),
        sa.Column("period_no", sa.Integer, nullable=False, server_default="1", comment="期次编号"),
        sa.Column("applicant_unit", sa.String(200), nullable=False, comment="申请单位"),
        # 通用金额（分）
        sa.Column("contract_amount", sa.BigInteger, nullable=False, server_default="0", comment="合同金额（分）"),
        sa.Column("cumulative_reported_output", sa.BigInteger, nullable=False, server_default="0", comment="累计报送产值（分）"),
        sa.Column("payment_ratio", sa.Numeric(6, 4), comment="付款比例"),
        sa.Column("current_audited_output", sa.BigInteger, nullable=False, server_default="0", comment="本期审核产值（分）"),
        sa.Column("cumulative_audited_output", sa.BigInteger, nullable=False, server_default="0", comment="累计审核产值（分）"),
        sa.Column("cumulative_audited_payable", sa.BigInteger, nullable=False, server_default="0", comment="累计审核应付款（分）"),
        # 施工特有
        sa.Column("constr_install_fee", sa.BigInteger, server_default="0", comment="建筑安装工程费（分）"),
        sa.Column("safety_civil_fee", sa.BigInteger, server_default="0", comment="安全文明施工费（分）"),
        sa.Column("constr_install_pay_ratio", sa.Numeric(6, 4), comment="建安付款比例"),
        sa.Column("safety_civil_pay_ratio", sa.Numeric(6, 4), comment="安全文明付款比例"),
        # 监理过控特有
        sa.Column("supervision_fee", sa.BigInteger, server_default="0", comment="工程监理服务费（分）"),
        sa.Column("cost_consult_fee", sa.BigInteger, server_default="0", comment="造价咨询服务费（分）"),
        sa.Column("settlement_fee", sa.BigInteger, server_default="0", comment="竣工结算服务费（分）"),
        sa.Column("supervision_pay_ratio", sa.Numeric(6, 4), comment="监理付款比例"),
        sa.Column("cost_consult_pay_ratio", sa.Numeric(6, 4), comment="造价咨询付款比例"),
        sa.Column("settlement_pay_ratio", sa.Numeric(6, 4), comment="结算付款比例"),
        # 备注
        sa.Column("remark", sa.Text, comment="备注"),
        sa.Column("tax_rate", sa.Numeric(4, 2), comment="税率"),
        # 审核状态
        sa.Column("audit_status", sa.String(20), nullable=False, server_default="pending", comment="pending/auditing/audited/paid"),
        sa.Column("submit_date", sa.Date, comment="申报日期"),
        sa.Column("audited_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="审核人"),
        sa.Column("audited_at", sa.DateTime(timezone=True), comment="审核时间"),
        *_ts(),
        comment="进度款审核表（V2.0 — 4类单位共用）",
    )


def _create_weekly_progress_report_table():
    op.create_table(
        "t_weekly_progress_report",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("report_date", sa.Date, nullable=False, index=True, comment="周报日期"),
        sa.Column("seq", sa.Integer, nullable=False, comment="序号"),
        sa.Column("location_id", postgresql.UUID, sa.ForeignKey("dict_location.id"), comment="FK→dict_location"),
        sa.Column("location_name", sa.String(100), nullable=False, comment="形象部位"),
        # 本周
        sa.Column("weekly_progress_desc", sa.Text, comment="本周形象描述"),
        sa.Column("weekly_output_reported", sa.BigInteger, server_default="0", comment="本周产值-施工上报（分）"),
        sa.Column("weekly_output_audited", sa.BigInteger, server_default="0", comment="本周产值-过控复核（分）"),
        # 累计
        sa.Column("cumulative_output_reported", sa.BigInteger, server_default="0", comment="累计产值-施工上报（分）"),
        sa.Column("cumulative_output_audited", sa.BigInteger, server_default="0", comment="累计产值-过控复核（分）"),
        sa.Column("type2_expense", sa.BigInteger, server_default="0", comment="二类费用（分）"),
        sa.Column("total_amount", sa.BigInteger, server_default="0", comment="合计（分）"),
        sa.Column("cumulative_progress_desc", sa.Text, comment="累计形象描述"),
        sa.Column("review_date", sa.Date, comment="复核日期"),
        *_ts(),
        comment="周报-形象进度（V2.0）",
    )
    op.create_index("ix_weekly_report_project_date", "t_weekly_progress_report", ["project_id", "report_date"])


def _create_weekly_progress_metrics_table():
    op.create_table(
        "t_weekly_progress_metrics",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("report_week", sa.Date, nullable=False, index=True, comment="周报日期"),
        sa.Column("data_scope", sa.String(50), nullable=False, server_default="标准口径", comment="数据口径"),
        sa.Column("metric_name", sa.String(200), nullable=False, comment="指标名称"),
        sa.Column("metric_value", sa.Numeric(18, 6), nullable=False, comment="指标值"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        sa.UniqueConstraint("project_id", "report_week", "data_scope", "metric_name", name="uq_weekly_metrics"),
        comment="周报-投资指标（V2.0）",
    )


def _create_monthly_province_progress_table():
    op.create_table(
        "t_monthly_province_progress",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("report_month", sa.Date, nullable=False, index=True, comment="报告月份"),
        sa.Column("seq", sa.Integer, nullable=False, comment="序号"),
        sa.Column("project_name", sa.String(200), nullable=False, comment="项目名称"),
        sa.Column("construction_period", sa.String(50), comment="建设起止年"),
        sa.Column("construction_scale", sa.Text, comment="建设内容及规模"),
        # 投资（分）
        sa.Column("planned_total_invest", sa.BigInteger, nullable=False, server_default="0", comment="计划总投资（分）"),
        sa.Column("cumulative_invest_by_2025", sa.BigInteger, server_default="0", comment="截至2025累计（分）"),
        sa.Column("planned_invest_2026", sa.BigInteger, server_default="0", comment="2026年预计（分）"),
        sa.Column("completed_invest_1_5m", sa.BigInteger, server_default="0", comment="1-5月完成（分）"),
        sa.Column("completed_invest_6m", sa.BigInteger, server_default="0", comment="6月完成（分）"),
        sa.Column("completed_invest_1_6m", sa.BigInteger, server_default="0", comment="1-6月完成（分）"),
        sa.Column("completion_rate", sa.Numeric(8, 4), comment="完成率"),
        # 形象进度
        sa.Column("progress_apr", sa.Text, comment="4月进度"),
        sa.Column("progress_jun", sa.Text, comment="6月进度"),
        sa.Column("progress_target_2026", sa.Text, comment="2026年目标"),
        # 参建单位
        sa.Column("owner_unit", sa.String(200), comment="业主单位"),
        sa.Column("responsible_unit", sa.String(200), comment="责任单位"),
        sa.Column("remark", sa.String(100), comment="备注"),
        *_ts(),
        comment="省市重点项目月进度（V2.0）",
    )


def _create_monthly_target_plan_table():
    op.create_table(
        "t_monthly_target_plan",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("plan_month", sa.Date, nullable=False, comment="计划月份"),
        sa.Column("monthly_planned_invest", sa.BigInteger, server_default="0", comment="月度计划投资额（分）"),
        sa.Column("monthly_planned_progress", sa.Text, comment="月度计划形象进度"),
        sa.Column("monthly_actual_invest", sa.BigInteger, server_default="0", comment="月度实际投资（分）"),
        sa.Column("monthly_actual_progress", sa.Text, comment="月度实际形象进度"),
        sa.UniqueConstraint("project_id", "plan_month", name="uq_monthly_plan"),
        *_ts(),
        comment="月度目标计划（V2.0）",
    )


def _create_fund_breakdown_table():
    op.create_table(
        "t_fund_breakdown",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目"),
        sa.Column("fund_year", sa.Integer, nullable=False, comment="资金年度"),
        sa.Column("fund_scope", sa.String(20), nullable=False, server_default="total", comment="total/annual_plan"),
        # 六类资金（分）
        sa.Column("central_province_fund", sa.BigInteger, server_default="0", comment="中省资金（分）"),
        sa.Column("special_general_bond", sa.BigInteger, server_default="0", comment="专项债/一般债（分）"),
        sa.Column("national_bond_fund", sa.BigInteger, server_default="0", comment="国债/基金（分）"),
        sa.Column("self_owned_fund", sa.BigInteger, server_default="0", comment="自有资金（分）"),
        sa.Column("financing_fund", sa.BigInteger, server_default="0", comment="融资资金（分）"),
        sa.Column("other_fund", sa.BigInteger, server_default="0", comment="其他资金（分）"),
        # 汇总
        sa.Column("cumulative_completed_invest", sa.BigInteger, server_default="0", comment="累计完成投资（分）"),
        sa.Column("annual_planned_invest", sa.BigInteger, server_default="0", comment="年度计划投资（分）"),
        sa.UniqueConstraint("project_id", "fund_year", "fund_scope", name="uq_fund_breakdown"),
        *_ts(),
        comment="资金来源分解（V2.0）",
    )


def _create_data_rows_table():
    op.create_table(
        "t_data_rows",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, comment="关联项目"),
        sa.Column("data_date", sa.Date, nullable=False, comment="数据日期"),
        sa.Column("category", sa.String(100), nullable=False, comment="分部工程类别"),
        sa.Column("item_name", sa.String(200), nullable=False, comment="分项名称"),
        sa.Column("planned_quantity", sa.BigInteger, server_default="0", comment="计划工程量"),
        sa.Column("actual_quantity", sa.BigInteger, server_default="0", comment="实际工程量"),
        sa.Column("unit", sa.String(20), comment="单位"),
        sa.Column("unit_price", sa.BigInteger, server_default="0", comment="单价（分）"),
        sa.Column("amount", sa.BigInteger, server_default="0", comment="金额（分）"),
        sa.Column("cost_type", sa.String(50), nullable=False, comment="费用类型"),
        sa.Column("source_doc", sa.String(500), comment="来源文档"),
        sa.Column("source_type", sa.String(30), nullable=False, comment="constructor/reviewer/ai/system"),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default="false", comment="是否已确认"),
        sa.Column("raw_data", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="AI原始快照"),
        sa.Column("confirmed_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="确认人"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), comment="确认时间"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), comment="软删除"),
        *_ts(),
        comment="数据流水表（系统核心）",
    )


def _create_report_templates_table():
    op.create_table(
        "t_report_templates",
        _pk(),
        sa.Column("template_name", sa.String(200), nullable=False, comment="模板名称"),
        sa.Column("report_type", sa.String(20), nullable=False, comment="weekly/monthly/weekly_metrics/monthly_province/payment_report"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1", comment="模板版本号"),
        sa.Column("schema_json", postgresql.JSONB, nullable=False, comment="JSON Schema定义"),
        sa.Column("word_template_path", sa.String(500), comment="Word模板MinIO路径"),
        sa.Column("ppt_template_path", sa.String(500), comment="PPT模板MinIO路径"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false", comment="是否启用"),
        *_ts(),
        comment="报告模板表",
    )


def _create_reports_table():
    op.create_table(
        "t_reports",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, comment="关联项目"),
        sa.Column("template_id", postgresql.UUID, sa.ForeignKey("t_report_templates.id"), nullable=False, comment="关联模板"),
        sa.Column("report_type", sa.String(20), nullable=False, comment="weekly/monthly"),
        sa.Column("period_start", sa.Date, nullable=False, comment="报告周期开始"),
        sa.Column("period_end", sa.Date, nullable=False, comment="报告周期结束"),
        sa.Column("data_payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"), comment="报告数据快照"),
        sa.Column("report_status", sa.String(20), server_default="draft", comment="draft/pending/confirmed/published"),
        sa.Column("ai_generated_content", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="AI生成内容快照"),
        sa.Column("created_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="创建人"),
        sa.Column("reviewed_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="审核人"),
        sa.Column("review_comment", sa.Text, comment="审核意见"),
        *_ts(),
        comment="报告实例表",
    )


def _create_knowledge_docs_table():
    op.create_table(
        "t_knowledge_docs",
        _pk(),
        sa.Column("project_id", postgresql.UUID, comment="关联项目（NULL=通用）"),
        sa.Column("doc_category", sa.String(50), nullable=False, comment="contract/drawing/visa/meeting/standard/weekly_report/monthly_report/contract_ledger"),
        sa.Column("doc_title", sa.String(500), nullable=False, comment="文档标题"),
        sa.Column("file_path", sa.String(500), nullable=False, comment="MinIO路径"),
        sa.Column("file_size", sa.BigInteger, comment="文件大小（字节）"),
        sa.Column("doc_summary", sa.Text, comment="AI摘要"),
        sa.Column("chunk_count", sa.Integer, server_default="0", comment="分块数量"),
        sa.Column("parse_status", sa.String(20), server_default="pending", comment="pending/parsing/ready/failed"),
        sa.Column("uploaded_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="上传人"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"), comment="上传时间"),
        comment="知识库文档表",
    )


def _create_knowledge_chunks_table():
    op.create_table(
        "t_knowledge_chunks",
        _pk(),
        sa.Column("doc_id", postgresql.UUID, sa.ForeignKey("t_knowledge_docs.id", ondelete="CASCADE"), nullable=False, comment="关联文档"),
        sa.Column("chunk_no", sa.Integer, nullable=False, comment="分块序号"),
        sa.Column("content", sa.Text, nullable=False, comment="分块文本"),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), comment="向量嵌入"),  # pgvector
        sa.Column("tsv", postgresql.TSVECTOR, comment="FTS全文搜索"),
        sa.Column("source_span", sa.String(100), comment="来源位置"),
        sa.UniqueConstraint("doc_id", "chunk_no", name="uq_knowledge_chunks"),
        comment="文档分块表",
    )


def _create_custom_indexes():
    # t_data_rows
    op.create_index("ix_data_rows_project_date", "t_data_rows", ["project_id", sa.text("data_date DESC")])
    op.create_index("ix_data_rows_confirmed", "t_data_rows", ["project_id"], postgresql_where=sa.text("is_confirmed = true AND deleted_at IS NULL"))

    # t_contracts
    op.create_index("ix_contracts_project", "t_contracts", ["project_id"])
    op.create_index("ix_contracts_no", "t_contracts", ["contract_no"])

    # t_contract_payment_stages
    op.create_index("ix_payment_stages_contract", "t_contract_payment_stages", ["contract_id"])
    op.create_index("ix_payment_stages_no", "t_contract_payment_stages", ["contract_no"])

    # t_contract_monthly_detail
    op.create_index("ix_monthly_detail_month", "t_contract_monthly_detail", ["detail_month"])

    # t_progress_payment_review
    op.create_index("ix_payment_review_project_type", "t_progress_payment_review", ["project_id", "review_type"])
    op.create_index("ix_payment_review_status", "t_progress_payment_review", ["audit_status"])

    # t_monthly_province_progress
    op.create_index("ix_monthly_province_date", "t_monthly_province_progress", ["project_id", "report_month"])

    # t_fund_breakdown
    op.create_index("ix_fund_breakdown_project_year", "t_fund_breakdown", ["project_id", "fund_year"])

    # t_reports
    op.create_index("ix_reports_project_type", "t_reports", ["project_id", "report_type", "period_start"])

    # t_knowledge_docs
    op.create_index("ix_knowledge_docs_project_cat", "t_knowledge_docs", ["project_id", "doc_category"])

    # t_ai_tasks
    op.create_index("ix_ai_tasks_project_type", "t_ai_tasks", ["project_id", "task_type", "status"])


# ═══════════════════════════════════════════════════════════════════
# Ingest 流水线表 (4 张)
# ═══════════════════════════════════════════════════════════════════

def _create_ingest_tables():
    """t_field_mappings → t_ingest_batches → t_ingest_rows → t_ingest_errors"""

    op.create_table(
        "t_field_mappings",
        _pk(),
        sa.Column("mapping_name", sa.String(200), nullable=False, comment="映射名"),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), comment="适用项目（NULL=通用）"),
        sa.Column("file_format", sa.String(20), nullable=False, comment="适用文件类型"),
        sa.Column("header_row", sa.Integer, nullable=False, server_default="1", comment="表头行号"),
        sa.Column("sheet_index", sa.Integer, server_default="0", comment="Sheet索引"),
        sa.Column("rules", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"), comment="映射规则数组"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        *_ts(),
        comment="字段映射配置",
    )

    op.create_table(
        "t_ingest_batches",
        _pk(),
        sa.Column("project_id", postgresql.UUID, sa.ForeignKey("t_projects.id"), nullable=False, index=True, comment="目标项目"),
        sa.Column("source_doc", sa.String(500), nullable=False, comment="原始文件名"),
        sa.Column("source_path", sa.String(500), nullable=False, comment="MinIO路径"),
        sa.Column("source_type", sa.String(30), nullable=False, server_default="upload", comment="upload/email/api/ocr"),
        sa.Column("file_format", sa.String(20), nullable=False, comment="xlsx/xls/csv/pdf/image"),
        sa.Column("period_start", sa.Date, comment="业务周期起"),
        sa.Column("period_end", sa.Date, comment="业务周期止"),
        sa.Column("mapping_id", postgresql.UUID, sa.ForeignKey("t_field_mappings.id"), comment="字段映射"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0", comment="原始行数"),
        sa.Column("parsed_rows", sa.Integer, nullable=False, server_default="0", comment="解析成功行数"),
        sa.Column("valid_rows", sa.Integer, nullable=False, server_default="0", comment="校验通过行数"),
        sa.Column("error_rows", sa.Integer, nullable=False, server_default="0", comment="错误行数"),
        sa.Column("quality_score", sa.Numeric(5, 2), comment="批次质量分"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True,
                  comment="pending/parsing/normalized/validated/review/committing/committed/rolled_back/failed"),
        sa.Column("committed_at", sa.DateTime(timezone=True), comment="确认入库时间"),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), comment="撤回时间"),
        sa.Column("uploaded_by", postgresql.UUID, sa.ForeignKey("t_users.id"), comment="上传人"),
        *_ts(),
        comment="数据导入批次",
    )
    op.create_index("ix_ingest_batches_project", "t_ingest_batches", ["project_id", "created_at"])
    op.create_index("ix_ingest_batches_status", "t_ingest_batches", ["status"])

    op.create_table(
        "t_ingest_rows",
        _pk(),
        sa.Column("batch_id", postgresql.UUID, sa.ForeignKey("t_ingest_batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("row_no", sa.Integer, nullable=False, comment="原始行号"),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"), comment="原始数据"),
        sa.Column("normalized", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="归一化后"),
        sa.Column("mapped", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="映射后"),
        sa.Column("project_id", postgresql.UUID, nullable=False, comment="目标项目"),
        sa.Column("data_date", sa.Date, comment="数据日期"),
        sa.Column("category", sa.String(100), comment="分部工程类别"),
        sa.Column("item_name", sa.String(200), comment="分项名称"),
        sa.Column("planned_quantity", sa.BigInteger, comment="计划工程量"),
        sa.Column("actual_quantity", sa.BigInteger, comment="实际工程量"),
        sa.Column("unit", sa.String(20), comment="单位"),
        sa.Column("unit_price", sa.BigInteger, comment="单价（分）"),
        sa.Column("amount", sa.BigInteger, comment="金额（分）"),
        sa.Column("cost_type", sa.String(50), comment="费用类型"),
        sa.Column("validation_flags", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), comment="校验明细"),
        sa.Column("validation_status", sa.String(20), comment="校验状态：normal/warning/error/suspicious"),
        sa.Column("quality_score", sa.Numeric(5, 2), comment="单行质量分"),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="false", comment="校验通过"),
        sa.Column("error_code", sa.String(50), comment="错误码"),
        sa.Column("error_message", sa.Text, comment="错误描述"),
        sa.Column("target_data_row_id", postgresql.UUID, sa.ForeignKey("t_data_rows.id"), comment="入库数据行"),
        sa.UniqueConstraint("batch_id", "row_no"),
        *_ts(),
        comment="清洗明细行",
    )
    op.create_index("ix_ingest_rows_valid", "t_ingest_rows", ["batch_id", "is_valid"])
    op.create_index("ix_ingest_rows_date", "t_ingest_rows", ["project_id", "data_date"])
    op.create_index("ix_ingest_rows_status", "t_ingest_rows", ["validation_status"])

    op.create_table(
        "t_ingest_errors",
        _pk(),
        sa.Column("batch_id", postgresql.UUID, sa.ForeignKey("t_ingest_batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("row_id", postgresql.UUID, sa.ForeignKey("t_ingest_rows.id"), comment="关联清洗行"),
        sa.Column("error_stage", sa.String(20), nullable=False, comment="parse/normalize/map/validate"),
        sa.Column("error_code", sa.String(50), nullable=False, index=True, comment="错误码"),
        sa.Column("error_message", sa.Text, nullable=False, comment="错误说明"),
        sa.Column("error_field", sa.String(100), comment="出错字段"),
        sa.Column("error_value", sa.Text, comment="出错原始值"),
        sa.Column("severity", sa.String(20), nullable=False, comment="error/warning/info"),
        sa.Column("resolved", sa.Boolean, nullable=False, server_default="false", comment="是否已修正"),
        sa.Column("resolved_by", postgresql.UUID, comment="修正人"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), comment="修正时间"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False, comment="创建时间"),
        comment="清洗错误明细",
    )
    op.create_index("ix_ingest_errors_unresolved", "t_ingest_errors", ["batch_id", "resolved"])
    op.create_index("ix_ingest_errors_code", "t_ingest_errors", ["error_code"])
