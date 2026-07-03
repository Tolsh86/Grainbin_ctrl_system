"""MinIO 文件存储工具类

提供：
- MinioClient: 文件上传/下载/删除/列表
- FastAPI 依赖注入 (get_minio)
- 自动建桶
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urljoin

from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinioClient:
    """MinIO 客户端封装"""

    def __init__(self):
        self._client: Minio | None = None
        self._bucket: str = settings.MINIO_BUCKET

    async def init(self) -> None:
        """初始化 MinIO 客户端并确保桶存在。"""
        self._client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info(f"📦 桶 '{self._bucket}' 已创建")
            else:
                logger.info(f"📦 桶 '{self._bucket}' 已存在")
        except S3Error as e:
            logger.warning(f"⚠️ MinIO 桶操作失败: {e}")

    @property
    def client(self) -> Minio:
        if self._client is None:
            raise RuntimeError("MinioClient 未初始化，请先调用 init()")
        return self._client

    # ── 上传 ──────────────────────────────────────

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """上传字节流，返回文件访问路径。

        Args:
            key: 对象键名（含路径），如 reports/2024/xx.pdf
            data: 文件字节内容
            content_type: MIME 类型
            metadata: 自定义元数据

        Returns:
            文件的存储路径（key）
        """
        length = len(data)
        self.client.put_object(
            bucket_name=self._bucket,
            object_name=key,
            data=io.BytesIO(data),
            length=length,
            content_type=content_type,
            metadata=metadata or {},
        )
        logger.info(f"📤 上传成功: {key} ({length} bytes)")
        return key

    async def upload_file(
        self,
        key: str,
        file_path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """上传本地文件，返回文件路径。"""
        import os

        stat = os.stat(file_path)
        self.client.fput_object(
            bucket_name=self._bucket,
            object_name=key,
            file_path=file_path,
            content_type=content_type,
            metadata=metadata or {},
        )
        logger.info(f"📤 上传文件: {key} ({stat.st_size} bytes)")
        return key

    # ── 下载 ──────────────────────────────────────

    def download_bytes(self, key: str) -> bytes:
        """下载文件到内存。"""
        response = self.client.get_object(self._bucket, key)
        try:
            data = response.read()
            logger.info(f"📥 下载成功: {key}")
            return data
        finally:
            response.close()
            response.release_conn()

    def download_file(self, key: str, local_path: str) -> str:
        """下载文件到本地。"""
        self.client.fget_object(self._bucket, key, local_path)
        logger.info(f"📥 下载文件: {key} → {local_path}")
        return local_path

    # ── 删除 ──────────────────────────────────────

    def delete(self, key: str) -> None:
        """删除一个对象。"""
        self.client.remove_object(self._bucket, key)
        logger.info(f"🗑️ 删除文件: {key}")

    def delete_multi(self, *keys: str) -> None:
        """批量删除对象。"""
        for key in keys:
            self.delete(key)

    # ── 列表 ──────────────────────────────────────

    def list_files(self, prefix: str = "", recursive: bool = True) -> list[dict[str, Any]]:
        """列出桶内文件。

        Returns:
            [{object_name, size, last_modified, content_type, etag}, ...]
        """
        objects = self.client.list_objects(self._bucket, prefix=prefix, recursive=recursive)
        result = []
        for obj in objects:
            result.append({
                "object_name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                "etag": obj.etag,
            })
        return result

    # ── 工具 ──────────────────────────────────────

    def get_url(self, key: str) -> str:
        """获取文件的外部访问 URL（不提供 presigned）。"""
        protocol = "https" if settings.MINIO_SECURE else "http"
        return urljoin(f"{protocol}://{settings.MINIO_ENDPOINT}/{self._bucket}/", key)

    def exists(self, key: str) -> bool:
        """判断对象是否存在。"""
        try:
            self.client.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False


# ── 全局单例 ──────────────────────────────────────

minio_client = MinioClient()


# ── 依赖注入 ─────────────────────────────────────


async def get_minio() -> MinioClient:
    """FastAPI 依赖注入：获取 MinIO 客户端。"""
    return minio_client
