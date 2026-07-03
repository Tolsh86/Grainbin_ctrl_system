"""JWT 令牌生成与验证 + bcrypt 密码哈希"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── 密码哈希 ────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对明文密码做 bcrypt 哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ────────────────────────────────────────


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """签发 JWT 访问令牌。

    Args:
        data: 载荷字典（至少包含 "sub" = user_id）。
        expires_delta: 过期时长，默认使用 settings 配置。
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码并校验 JWT 令牌，返回载荷字典。

    Raises:
        JWTError: 令牌无效或已过期。
    """
    payload: dict = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if "sub" not in payload:
        raise JWTError("Token missing 'sub' claim")
    return payload


def token_to_user_id(token: str) -> uuid.UUID:
    """从 JWT 中便捷提取 user_id。"""
    payload = decode_access_token(token)
    return uuid.UUID(payload["sub"])
