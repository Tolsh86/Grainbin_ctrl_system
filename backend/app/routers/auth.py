"""认证路由：登录、注册

- 使用 username 登录（非 email）
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import Conflict, Unauthorized
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services import user as user_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """注册新用户。"""
    existing = await user_service.get_user_by_username(db, data.username)
    if existing:
        raise Conflict(detail=f"用户名 '{data.username}' 已存在")
    user = await user_service.create_user(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录，返回 JWT 令牌。"""
    token = await user_service.login(db, data.username, data.password)
    if not token:
        raise Unauthorized(detail="用户名或密码错误")
    return token
