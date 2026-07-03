"""ORM 模型包 — 导入所有模型供 Alembic 自动发现 (V2.1)

Usage:
    from app.models import Base  # 含全部表的 metadata
    from app.models import User, Project, DataRow, ...
"""

from app.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, DictMixin

# ── 系统表 ──
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.ai_task import AiTask

# ── 业务核心 (V2.0) ──
from app.models.project import Project
from app.models.data_row import DataRow
from app.models.contract import Contract, ContractPaymentStage, ContractMonthlyDetail
from app.models.contract_payment import ContractPayment
from app.models.progress_review import ProgressPaymentReview
from app.models.weekly_progress import WeeklyProgressReport, WeeklyProgressMetrics
from app.models.monthly_fund import MonthlyProvinceProgress, MonthlyTargetPlan, FundBreakdown

# ── 字典表 (V2.0) ──
from app.models.dict_tables import (
    DictProjectNature, DictInvestTiming, DictInvestNature,
    DictInvestStructure, DictInvestField, DictProjectLevel,
    DictLocation, DictOwnerUnit, DictSupplier, DictReviewType,
)

# ── 报告 + 知识库 ──
from app.models.report import ReportTemplate, Report
from app.models.knowledge import KnowledgeDoc, KnowledgeChunk

# ── 数据导入流水线 ──
from app.models.ingest import (
    IngestBatch, IngestRow, IngestError, FieldMapping,
)

__all__ = [
    # 基类
    "Base", "UUIDMixin", "TimestampMixin", "SoftDeleteMixin", "DictMixin",
    # 系统
    "User", "AuditLog", "AiTask",
    # 业务
    "Project", "DataRow",
    "Contract", "ContractPaymentStage", "ContractMonthlyDetail", "ContractPayment",
    "ProgressPaymentReview",
    "WeeklyProgressReport", "WeeklyProgressMetrics",
    "MonthlyProvinceProgress", "MonthlyTargetPlan", "FundBreakdown",
    # 字典
    "DictProjectNature", "DictInvestTiming", "DictInvestNature",
    "DictInvestStructure", "DictInvestField", "DictProjectLevel",
    "DictLocation", "DictOwnerUnit", "DictSupplier", "DictReviewType",
    # 报告 + 知识库
    "ReportTemplate", "Report",
    "KnowledgeDoc", "KnowledgeChunk",
    # 数据导入
    "IngestBatch", "IngestRow", "IngestError", "FieldMapping",
]
