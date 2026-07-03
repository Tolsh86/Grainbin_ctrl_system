"""用户路由：完整 CRUD + 启停控制"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取当前登录用户信息。"""
    user = await user_service.get_user_by_id(db, current_user_id)
    if not user:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在")
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """当前用户修改个人信息（不允许改角色和启用状态）。"""
    # 不允许用户自己改角色和启用状态
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("role", None)
    update_data.pop("is_active", None)
    safe_update = UserUpdate(**update_data)
    user = await user_service.update_user(db, current_user_id, safe_update)
    if not user:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在")
    return user


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    is_active: bool | None = Query(None, description="启用状态筛选"),
    role: str | None = Query(None, description="角色筛选"),
    keyword: str | None = Query(None, description="搜索关键词（用户名/姓名/邮箱）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """获取用户列表（需 admin 权限）。"""
    items, total = await user_service.get_users(
        db, page=page, page_size=page_size,
        is_active=is_active, role=role, keyword=keyword,
    )
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """获取单个用户详情（需 admin 权限）。"""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """创建新用户（需 admin 权限）。"""
    existing = await user_service.get_user_by_username(db, data.username)
    if existing:
        from app.core.exceptions import Conflict
        raise Conflict(detail=f"用户名 '{data.username}' 已存在")
    user = await user_service.create_user(db, data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """更新用户信息（需 admin 权限）。"""
    # 如果改了用户名，检查是否已存在
    if data.username is not None:
        existing = await user_service.get_user_by_username(db, data.username)
        if existing and existing.id != user_id:
            from app.core.exceptions import Conflict
            raise Conflict(detail=f"用户名 '{data.username}' 已被使用")
    user = await user_service.update_user(db, user_id, data)
    if not user:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在")
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """删除用户（软删除，需 admin 权限）。"""
    ok = await user_service.delete_user(db, user_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在或已删除")
    return MessageResponse(message="用户已删除")


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """切换用户启用/停用状态（需 admin 权限）。"""
    # 不能停用自己
    if user_id == current_user_id:
        from app.core.exceptions import BadRequest
        raise BadRequest(detail="不能停用自己的账号")
    user = await user_service.toggle_user_active(db, user_id)
    if not user:
        from app.core.exceptions import NotFound
        raise NotFound(detail="用户不存在")
    return user
