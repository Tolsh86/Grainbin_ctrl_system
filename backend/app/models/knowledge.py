"""知识库文档表 + 文档分块表

t_knowledge_docs   — 上传文件管理（含向量嵌入）
t_knowledge_chunks — RAG 文档分块（含 pgvector 嵌入 + FTS）
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base

# pgvector — 仅在安装了 pgvector Python 包后可用
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import NullType as Vector  # type: ignore[assignment]


class KnowledgeDoc(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_knowledge_docs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), index=True,
        comment="关联项目（NULL = 通用文档）",
    )
    doc_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="contract / drawing / visa / meeting / standard / weekly_report / monthly_report / contract_ledger",
    )
    doc_title: Mapped[str] = mapped_column(String(500), nullable=False, comment="文档标题")
    file_path: Mapped[str | None] = mapped_column(String(500), comment="MinIO 文件存储路径")
    file_size: Mapped[int | None] = mapped_column(BigInteger, comment="文件大小（字节）")
    doc_summary: Mapped[str | None] = mapped_column(Text, comment="AI 生成摘要")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024), comment="向量嵌入（pgvector，用于语义搜索）",
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", comment="分块数量")
    parse_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending",
        comment="pending / parsing / ready / failed",
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="上传人")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="上传时间",
    )

    # ── 关系 ──
    project: Mapped["Project | None"] = relationship("Project", lazy="selectin")  # noqa: F821
    chunks: Mapped[list["KnowledgeChunk"]] = relationship("KnowledgeChunk", back_populates="doc", lazy="selectin")

    def __repr__(self) -> str:
        return f"<KnowledgeDoc {self.doc_title} category={self.doc_category}>"


class KnowledgeChunk(Base, UUIDMixin):
    __tablename__ = "t_knowledge_chunks"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_knowledge_docs.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="关联文档",
    )
    chunk_no: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="分块序号",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="分块文本",
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024), comment="BGE-M3 向量嵌入",
    )
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR, comment="PostgreSQL FTS 全文搜索索引",
    )
    source_span: Mapped[str | None] = mapped_column(
        String(100), comment="来源位置（如 p12#tbl3:r4-r7）",
    )

    # ── 关系 ──
    doc: Mapped["KnowledgeDoc"] = relationship("KnowledgeDoc", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<KnowledgeChunk doc={self.doc_id} chunk={self.chunk_no}>"
