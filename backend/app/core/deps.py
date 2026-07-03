"""FastAPI 依赖注入：数据库会话 + 当前用户"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token

# ── 鉴权方案 ────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


# ── 角色等级映射（数字越小权限越高） ──────────────
ROLE_HIERARCHY: dict[str, int] = {
    "admin": 0,
    "manager": 1,
    "editor": 2,
    "viewer": 3,
}


def require_role(minimum_role: str):
    """工厂函数：生成权限依赖，要求用户角色 >= minimum_role。

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(current_user = Depends(require_role("admin"))):
            ...
    """

    async def role_checker(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> uuid.UUID:
        user_id = await _get_user_id_from_token(credentials)
        # 延迟导入避免循环依赖
        from app.models.user import User

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

        user_level = ROLE_HIERARCHY.get(user.role, 99)
        required_level = ROLE_HIERARCHY.get(minimum_role, 99)
        if user_level > required_level:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

        return user.id

    return role_checker


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    """获取当前登录用户 ID（仅要求已登录）。"""
    return await _get_user_id_from_token(credentials)


async def _get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> uuid.UUID:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证令牌")
    try:
        payload = decode_access_token(credentials.credentials)
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期")
