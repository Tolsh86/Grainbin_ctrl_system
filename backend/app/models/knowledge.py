"""知识库文档表 t_knowledge_docs

使用 pgvector 扩展存储向量嵌入 (VECTOR(1024))，用于语义搜索。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin, Base

# pgvector 的 VECTOR 类型 —— 仅在安装了 pgvector Python 包后可用
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # 兜底：用 NullType 占位，允许在不安装 pgvector 包时导入 models
    from sqlalchemy import NullType as Vector  # type: ignore[assignment]


class KnowledgeDoc(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "t_knowledge_docs"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("t_projects.id"), index=True,
        comment="关联项目（NULL 表示通用文档）",
    )
    doc_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="类型：合同/图纸/签证/变更/会议纪要/规范/制度",
    )
    doc_title: Mapped[str] = mapped_column(String(500), nullable=False, comment="文档标题")
    file_path: Mapped[str | None] = mapped_column(String(500), comment="MinIO 文件存储路径")
    file_size: Mapped[int | None] = mapped_column(BigInteger, comment="文件大小（字节）")
    doc_summary: Mapped[str | None] = mapped_column(Text, comment="AI 生成摘要")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024), comment="向量嵌入（pgvector 类型，用于语义搜索）",
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), comment="上传人")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="上传时间",
    )

    # ── 关系 ──
    project: Mapped["Project | None"] = relationship("Project", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<KnowledgeDoc {self.doc_title} category={self.doc_category}>"
