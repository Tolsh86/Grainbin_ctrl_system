"""入库前清洗流水线表（4 张）

t_ingest_batches   — 批次主表
t_ingest_rows      — 清洗明细行
t_ingest_errors    — 错误明细
t_field_mappings   — 字段映射配置
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, Base


# ═══════════════════════════════════════════════
# 批次主表
# ═══════════════════════════════════════════════

class IngestBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_ingest_batches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), nullable=False, index=True, comment="目标项目",
    )
    source_doc: Mapped[str] = mapped_column(String(500), nullable=False, comment="原始文件名")
    source_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="MinIO 路径")
    source_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="upload", comment="来源: upload/email/api/ocr",
    )
    file_format: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="文件格式: xlsx/xls/csv/pdf/image",
    )
    period_start: Mapped[date | None] = mapped_column(Date, comment="业务周期起")
    period_end: Mapped[date | None] = mapped_column(Date, comment="业务周期止")
    mapping_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_field_mappings.id"), comment="本批次使用的字段映射",
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="原始行数")
    parsed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="解析成功行数")
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="校验通过行数")
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="错误行数")
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), comment="批次质量分（0-100）")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending/parsing/normalized/validated/review/committing/committed/rolled_back/failed",
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="确认入 t_data_rows 时间")
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="撤回时间")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_users.id"), comment="上传人",
    )

    # ── 关系 ──
    project: Mapped["Project"] = relationship("Project", lazy="selectin")  # noqa: F821
    mapping: Mapped["FieldMapping | None"] = relationship("FieldMapping", lazy="selectin")
    rows: Mapped[list["IngestRow"]] = relationship("IngestRow", back_populates="batch", lazy="selectin")
    errors: Mapped[list["IngestError"]] = relationship("IngestError", back_populates="batch", lazy="selectin")

    __table_args__ = (
        Index("ix_ingest_batches_project", "project_id", "created_at"),
        Index("ix_ingest_batches_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<IngestBatch {self.id} status={self.status}>"


# ═══════════════════════════════════════════════
# 清洗明细行
# ═══════════════════════════════════════════════

class IngestRow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_ingest_rows"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_ingest_batches.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    row_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="原始行号（用于人工定位）")
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="原始单元格内容")
    normalized: Mapped[dict] = mapped_column(JSONB, default=dict, comment="归一化后的字段值")
    mapped: Mapped[dict] = mapped_column(JSONB, default=dict, comment="字段映射后的键值对")
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="目标项目")
    data_date: Mapped[date | None] = mapped_column(Date, comment="数据日期")
    category: Mapped[str | None] = mapped_column(String(100), comment="分部工程类别")
    item_name: Mapped[str | None] = mapped_column(String(200), comment="分项名称")
    planned_quantity: Mapped[int | None] = mapped_column(BigInteger, comment="计划工程量（主单位）")
    actual_quantity: Mapped[int | None] = mapped_column(BigInteger, comment="实际工程量（主单位）")
    unit: Mapped[str | None] = mapped_column(String(20), comment="单位")
    unit_price: Mapped[int | None] = mapped_column(BigInteger, comment="单价（分）")
    amount: Mapped[int | None] = mapped_column(BigInteger, comment="金额（分）")
    cost_type: Mapped[str | None] = mapped_column(String(50), comment="费用类型")
    validation_flags: Mapped[dict] = mapped_column(JSONB, default=dict, comment="校验项明细：每项含 rule/level/message")
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), comment="单行清洗质量分")
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="校验是否通过")
    error_code: Mapped[str | None] = mapped_column(String(50), comment="错误码")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误描述")
    target_data_row_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_data_rows.id"), comment="确认后映射到的流水表行",
    )

    # ── 关系 ──
    batch: Mapped["IngestBatch"] = relationship("IngestBatch", back_populates="rows")

    __table_args__ = (
        UniqueConstraint("batch_id", "row_no"),
        Index("ix_ingest_rows_valid", "batch_id", "is_valid"),
        Index("ix_ingest_rows_date", "project_id", "data_date"),
    )

    def __repr__(self) -> str:
        return f"<IngestRow batch={self.batch_id} row={self.row_no} valid={self.is_valid}>"


# ═══════════════════════════════════════════════
# 错误明细
# ═══════════════════════════════════════════════

class IngestError(Base, UUIDMixin):
    __tablename__ = "t_ingest_errors"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_ingest_batches.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    row_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_ingest_rows.id"), comment="关联的清洗行",
    )
    error_stage: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="parse/normalize/map/validate",
    )
    error_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="HEADER_NOT_FOUND / TYPE_MISMATCH / AMOUNT_OUT_OF_RANGE 等",
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=False, comment="详细说明")
    error_field: Mapped[str | None] = mapped_column(String(100), comment="出错字段")
    error_value: Mapped[str | None] = mapped_column(Text, comment="出错原始值")
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="error/warning/info",
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否已修正")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="修正人")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="修正时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间",
    )

    # ── 关系 ──
    batch: Mapped["IngestBatch"] = relationship("IngestBatch", back_populates="errors")

    __table_args__ = (
        Index("ix_ingest_errors_unresolved", "batch_id", "resolved"),
        Index("ix_ingest_errors_code", "error_code"),
    )

    def __repr__(self) -> str:
        return f"<IngestError {self.error_code} stage={self.error_stage}>"


# ═══════════════════════════════════════════════
# 字段映射配置
# ═══════════════════════════════════════════════

class FieldMapping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "t_field_mappings"

    mapping_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="映射名（如'监理月报标准表头'）")
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), comment="适用项目（NULL = 通用）",
    )
    file_format: Mapped[str] = mapped_column(String(20), nullable=False, comment="适用文件类型")
    header_row: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="表头所在行号")
    sheet_index: Mapped[int] = mapped_column(Integer, default=0, comment="Sheet 索引（多 Sheet 用）")
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="字段映射规则数组")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    # ── 关系 ──
    project: Mapped["Project | None"] = relationship("Project", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<FieldMapping {self.mapping_name}>"
