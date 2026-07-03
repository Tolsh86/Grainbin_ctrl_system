"""ORM 模型包 — 导入所有模型供 Alembic 自动发现

Usage:
    from app.models import Base  # 含全部表的 metadata
    from app.models import User, Project, DataRow, ...
"""

from app.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.project import Project
from app.models.data_row import DataRow
from app.models.contract import Contract, ContractVersion, ContractClause
from app.models.report import ReportTemplate, Report
from app.models.payment_audit import PaymentAudit
from app.models.secondary_cost import SecondaryCostLedger
from app.models.knowledge import KnowledgeDoc
from app.models.audit_log import AuditLog
from app.models.ingest import (
    IngestBatch,
    IngestRow,
    IngestError,
    FieldMapping,
)

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    "User",
    "Project",
    "DataRow",
    "Contract",
    "ContractVersion",
    "ContractClause",
    "ReportTemplate",
    "Report",
    "PaymentAudit",
    "SecondaryCostLedger",
    "KnowledgeDoc",
    "AuditLog",
    "IngestBatch",
    "IngestRow",
    "IngestError",
    "FieldMapping",
]
