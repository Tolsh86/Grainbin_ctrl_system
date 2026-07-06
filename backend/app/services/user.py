"""用户业务逻辑：注册、登录、CRUD"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, TokenResponse, UserResponse
from app.utils.db import paginate


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """按登录名查找用户。"""
    result = await db.execute(select(User).where(User.username == username, User.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """按 ID 查找用户。"""
    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
    role: str | None = None,
    keyword: str | None = None,
) -> tuple[list[User], int]:
    """分页查询用户列表，支持筛选。"""
    stmt = select(User).order_by(User.created_at.desc())
    count_stmt = select(func.count(User.id))

    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
        count_stmt = count_stmt.where(User.is_active.is_(is_active))

    if role:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)

    if keyword:
        like = f"%{keyword}%"
        filter_cond = or_(User.username.ilike(like), User.real_name.ilike(like), User.email.ilike(like))
        stmt = stmt.where(filter_cond)
        count_stmt = count_stmt.where(filter_cond)

    return await paginate(db, stmt, page=page, page_size=page_size, model=User, count_stmt=count_stmt)


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """创建新用户。"""
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        email=data.email,
        role=data.role,
        is_active=data.is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> User | None:
    """更新用户信息。"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """软删除用户。"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def toggle_user_active(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """切换用户启用/停用状态。"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = not user.is_active
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """验证用户名和密码，返回用户或 None。"""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def login(db: AsyncSession, username: str, password: str) -> TokenResponse | None:
    """用户登录，返回 JWT + 用户信息。"""
    user = await authenticate_user(db, username, password)
    if not user:
        return None

    # 更新最后登录时间
    user.last_login_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(user, ["updated_at", "last_login_at"])

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
