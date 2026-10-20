"""应用配置 - 基于 Pydantic Settings 的环境变量管理"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 文件和环境变量加载配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 应用 ───────────────────────────────
    APP_NAME: str = "兴天华过控智能平台"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    # 本地开发可保留免登录；公网环境必须通过环境变量显式关闭。
    AUTH_BYPASS_ENABLED: bool = True
    # 公网演示仅使用预置管理员账号，不开放自助注册。
    PUBLIC_REGISTRATION_ENABLED: bool = True

    # ── 数据库 ─────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/grainbin"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres123@localhost:5432/grainbin"

    # ── Redis ──────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── MinIO ──────────────────────────────
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "grainbin"
    MINIO_SECURE: bool = False

    # ── 文件上传 ──────────────────────────
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set[str] = {"xlsx", "xls", "csv"}

    # ── JWT ────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 小时

    @property
    def minio_endpoint_url(self) -> str:
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"


settings = Settings()
