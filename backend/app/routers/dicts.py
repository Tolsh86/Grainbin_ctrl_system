"""字典 CRUD 接口

读取（GET）沿用现有缓存逻辑；
写入（POST/PUT/DELETE/PATCH）直接操作 DB 后使缓存失效。

端点设计：
  GET    /dicts                            → 全量字典（缓存）
  GET    /dicts/{name}                     → 单张字典（缓存）
  GET    /dicts/{name}/items               → 字典条目分页（含已停用，可筛选 is_active）
  GET    /dicts/{name}/items/{item_id}     → 单条字典条目
  POST   /dicts/{name}/items               → 创建（需 operator 以上）
  PUT    /dicts/{name}/items/{item_id}     → 更新（需 operator 以上）
  DELETE /dicts/{name}/items/{item_id}     → 删除（需 operator 以上）
  PATCH  /dicts/{name}/items/{item_id}/toggle-active → 启用/停用（需 operator 以上）
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.dict_item import DictItemCreate, DictItemUpdate, DictItemResponse
from app.services import dict_service

router = APIRouter(prefix="/dicts", tags=["字典管理"])


# ── 缓存读取（原有接口） ──

@router.get("")
async def list_all_dicts(db: AsyncSession = Depends(get_db)):
    """获取所有字典表的缓存数据（仅活跃条目）。"""
    data = await dict_service.get_all_dicts(db)
    return data


@router.get("/{name}")
async def get_dict(name: str, db: AsyncSession = Depends(get_db)):
    """获取单张字典表缓存（仅活跃条目，按 sort_order 排序）。"""
    data = await dict_service.get_dict_by_name(name, db)
    if data is None:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    return data


@router.post("/refresh")
async def refresh_dicts(
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("admin")),
):
    """刷新所有字典缓存（admin 权限）。"""
    from app.services import dict_service
    await dict_service._refresh_cache(db)
    return MessageResponse(message="字典缓存已刷新")


# ── 字典条目 CRUD ──

@router.get("/{name}/items", response_model=PaginatedResponse[DictItemResponse])
async def list_dict_items(
    name: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=200, description="每页条数"),
    is_active: bool | None = Query(None, description="按启用状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """分页查询字典条目（包含已停用条目，支持 is_active 筛选）。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")

    items, total = await dict_service.list_dict_items(db, name, is_active=is_active, page=page, page_size=page_size)
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[DictItemResponse.model_validate(item) for item in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{name}/items/{item_id}", response_model=DictItemResponse)
async def get_dict_item(
    name: str,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user),
):
    """获取单条字典条目。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    item = await dict_service.get_dict_item(db, name, item_id)
    if not item:
        from app.core.exceptions import NotFound
        raise NotFound(detail="字典条目不存在")
    return item


@router.post("/{name}/items", response_model=DictItemResponse, status_code=status.HTTP_201_CREATED)
async def create_dict_item(
    name: str,
    data: DictItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """创建字典条目（需 editor 及以上权限）。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    item = await dict_service.create_dict_item(db, name, data)
    return item


@router.put("/{name}/items/{item_id}", response_model=DictItemResponse)
async def update_dict_item(
    name: str,
    item_id: uuid.UUID,
    data: DictItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """更新字典条目（需 editor 及以上权限）。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    item = await dict_service.update_dict_item(db, name, item_id, data)
    if not item:
        from app.core.exceptions import NotFound
        raise NotFound(detail="字典条目不存在")
    return item


@router.delete("/{name}/items/{item_id}", response_model=MessageResponse)
async def delete_dict_item(
    name: str,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """删除字典条目（需 editor 及以上权限）。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    ok = await dict_service.delete_dict_item(db, name, item_id)
    if not ok:
        from app.core.exceptions import NotFound
        raise NotFound(detail="字典条目不存在")
    return MessageResponse(message="字典条目已删除")


@router.patch("/{name}/items/{item_id}/toggle-active", response_model=DictItemResponse)
async def toggle_dict_item_active(
    name: str,
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(require_role("operator")),
):
    """切换字典条目启用/停用（需 editor 及以上权限）。"""
    if name not in dict_service.DICT_MODELS:
        from app.core.exceptions import NotFound
        raise NotFound(detail=f"字典表 '{name}' 不存在")
    item = await dict_service.toggle_dict_item_active(db, name, item_id)
    if not item:
        from app.core.exceptions import NotFound
        raise NotFound(detail="字典条目不存在")
    return item
