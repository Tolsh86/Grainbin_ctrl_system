"""文件上传业务逻辑：校验、MinIO 存储、批次编号"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequest
from app.schemas.upload import BatchUploadResponse, FileUploadResult
from app.utils.minio_client import minio_client

# 常见可执行文件魔数前缀（用于基础安全拦截）
_EXEC_MAGIC_PREFIXES = (
    b"MZ",           # PE (exe/dll)
    b"\x7fELF",      # ELF
    b"\xca\xfe\xba\xbe",  # Mach-O 32
    b"\xcf\xfa\xed\xfe",  # Mach-O 64
    b"\xff\xd8\xff",      # JPEG — 伪装为图片的实际攻击载荷
)

# Excel 文件魔数校验
_EXCEL_MAGIC = {
    "xlsx": b"PK\x03\x04",    # Office Open XML
    "xls":  b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",  # OLE2
    "csv":  None,  # CSV 为纯文本，不做魔数校验
}


def _check_virus_signature(data: bytes) -> None:
    """检查文件头是否为可执行文件魔数，拦截伪装上传。"""
    for prefix in _EXEC_MAGIC_PREFIXES:
        if data[:len(prefix)] == prefix:
            raise BadRequest(detail="文件内容包含可执行代码特征，禁止上传")


def _check_magic_bytes(data: bytes, ext: str) -> None:
    """根据后缀校验文件魔数。"""
    expected = _EXCEL_MAGIC.get(ext)
    if expected is None:
        return
    if len(data) < len(expected) or data[:len(expected)] != expected:
        raise BadRequest(
            detail=f"文件格式与 .{ext} 后缀不匹配，请确认文件未损坏",
        )


def _generate_batch_no() -> str:
    """生成批次临时编号: YYYYMMDD-短UUID。"""
    now = datetime.now(UTC)
    short_uuid = str(uuid.uuid4())[:8]
    return f"{now.strftime('%Y%m%d')}-{short_uuid}"


def _build_storage_path(batch_no: str, original_name: str) -> str:
    """构建 MinIO 存储路径: upload/{batch_no}/{uuid}_{original}。"""
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    return f"upload/{batch_no}/{unique_name}"


def _validate_file(file_name: str, file_size: int, file_data: bytes) -> str:
    """文件校验：后缀、大小、空文件、魔数。返回小写扩展名。"""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise BadRequest(detail=f"不支持的文件格式: .{ext}，仅支持 {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}")

    if file_size > settings.MAX_UPLOAD_SIZE:
        mb = settings.MAX_UPLOAD_SIZE / 1024 / 1024
        raise BadRequest(detail=f"文件大小超过限制（最大 {mb:.0f}MB）")

    if file_size == 0:
        raise BadRequest(detail="空文件，请检查文件内容")

    _check_virus_signature(file_data)
    _check_magic_bytes(file_data, ext)
    return ext


async def upload_single(
    file_name: str,
    file_data: bytes,
    file_size: int,
    batch_no: str | None = None,
) -> FileUploadResult:
    """上传单个文件到 MinIO，返回文件元信息。

    Args:
        file_name: 原始文件名。
        file_data: 文件字节内容。
        file_size: 文件大小。
        batch_no: 批次编号，不传则自动生成。

    Returns:
        FileUploadResult
    """
    _validate_file(file_name, file_size, file_data)
    batch_no = batch_no or _generate_batch_no()
    storage_path = _build_storage_path(batch_no, file_name)

    content_type_map = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls":  "application/vnd.ms-excel",
        "csv":  "text/csv",
    }
    ext = file_name.rsplit(".", 1)[-1].lower()

    minio_client.upload_bytes(
        key=storage_path,
        data=file_data,
        content_type=content_type_map.get(ext, "application/octet-stream"),
        metadata={
            "original_name": file_name,
            "uploaded_at": datetime.now(UTC).isoformat(),
        },
    )

    logger.info(f"文件上传成功: {file_name} → {storage_path} ({file_size} bytes, batch={batch_no})")

    return FileUploadResult(
        file_name=file_name,
        file_path=storage_path,
        file_size=file_size,
        file_format=ext,
        batch_no=batch_no,
        uploaded_at=datetime.now(UTC),
    )


async def upload_batch(
    files: list[tuple[str, bytes, int]],
) -> BatchUploadResponse:
    """批量上传文件（分片处理，避免一次性加载）。

    Args:
        files: [(file_name, file_data, file_size), ...] 列表。

    Returns:
        BatchUploadResponse
    """
    batch_no = _generate_batch_no()
    results: list[FileUploadResult] = []
    total_size = 0

    # 分片处理：每次最多处理 10 个文件，避免海量文件同时加载
    chunk_size = 10
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i + chunk_size]
        for file_name, file_data, file_size in chunk:
            result = await upload_single(file_name, file_data, file_size, batch_no=batch_no)
            results.append(result)
            total_size += file_size

    return BatchUploadResponse(
        batch_no=batch_no,
        files=results,
        total=len(results),
        total_size=total_size,
    )
