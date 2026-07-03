"""合同相关表

t_contracts          — 合同主表
t_contract_versions  — 合同版本历史
t_contract_clauses   — 合同条款明细
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base


class Contract(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_contracts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="关联项目",
    )
    contract_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="合同名称")
    contract_code: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, comment="合同编号")
    contract_type: Mapped[str | None] = mapped_column(String(50), comment="合同类型：施工/监理/设计/采购/其他")
    party_a: Mapped[str | None] = mapped_column(String(200), comment="甲方（业主）")
    party_b: Mapped[str | None] = mapped_column(String(200), comment="乙方（承包方）")
    contract_amount: Mapped[int | None] = mapped_column(BigInteger, comment="合同金额（分）")
    signed_date: Mapped[date | None] = mapped_column(Date, comment="签订日期")
    start_date: Mapped[date | None] = mapped_column(Date, comment="合同开始日期")
    end_date: Mapped[date | None] = mapped_column(Date, comment="合同结束日期")
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="当前版本号")

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821
    versions: Mapped[list["ContractVersion"]] = relationship("ContractVersion", back_populates="contract", lazy="selectin")
    clauses: Mapped[list["ContractClause"]] = relationship("ContractClause", back_populates="contract", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Contract {self.contract_code or self.id}>"


class ContractVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_contract_versions"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同",
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号")
    change_summary: Mapped[str | None] = mapped_column(Text, comment="变更摘要")
    content_snapshot: Mapped[dict | None] = mapped_column(JSONB, comment="合同内容快照（JSONB）")
    changed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="变更人")
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="变更时间",
    )

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", back_populates="versions")

    __table_args__ = (
        Index("ix_contract_versions_contract_version", "contract_id", "version_no", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ContractVersion contract={self.contract_id} v{self.version_no}>"


class ContractClause(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_contract_clauses"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_contracts.id"), nullable=False, index=True, comment="关联合同",
    )
    clause_no: Mapped[str | None] = mapped_column(String(50), comment="条款编号")
    clause_title: Mapped[str | None] = mapped_column(String(200), comment="条款标题")
    clause_content: Mapped[str | None] = mapped_column(Text, comment="条款内容")
    clause_type: Mapped[str | None] = mapped_column(String(50), comment="条款类型：付款/工期/违约/质保/其他")
    is_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否关键条款")

    # ── 关系 ──
    contract: Mapped["Contract"] = relationship("Contract", back_populates="clauses")

    def __repr__(self) -> str:
        return f"<ContractClause {self.clause_no} {self.clause_title}>"
