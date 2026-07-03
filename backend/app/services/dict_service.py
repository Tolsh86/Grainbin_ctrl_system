"""字典表 CRUD 服务

提供全部 10 张字典表的增删改查操作，写操作自动失效 Redis 缓存。
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dict_tables import (
    DictProjectNature, DictInvestTiming, DictInvestNature,
    DictInvestStructure, DictInvestField, DictProjectLevel,
    DictLocation, DictOwnerUnit, DictSupplier, DictReviewType,
    _BaseDict,
)
from app.schemas.dict_item import DictItemCreate, DictItemUpdate
from app.utils.redis_client import redis_client

# ── 字典表注册 ────────────────────────────────────

DICT_MODELS: dict[str, type[_BaseDict]] = {
    "project_nature": DictProjectNature,
    "invest_timing": DictInvestTiming,
    "invest_nature": DictInvestNature,
    "invest_structure": DictInvestStructure,
    "invest_field": DictInvestField,
    "project_level": DictProjectLevel,
    "location": DictLocation,
    "owner_unit": DictOwnerUnit,
    "supplier": DictSupplier,
    "review_type": DictReviewType,
}

CACHE_KEY_ALL = "dict:all"
CACHE_KEY_PREFIX = "dict:"
CACHE_TTL = 3600


# ── 内部辅助 ────────────────────────────────────

def _get_model(name: str) -> type[_BaseDict] | None:
    return DICT_MODELS.get(name)


def _cache_key(name: str) -> str:
    return f"{CACHE_KEY_PREFIX}{name}"


async def _invalidate_cache(name: str) -> None:
    """使指定表和全量字典的缓存失效。"""
    await redis_client.delete(_cache_key(name))
    await redis_client.delete(CACHE_KEY_ALL)


# ── 读取（带缓存） ──────────────────────────────

async def get_all_dicts(db: AsyncSession) -> dict[str, list[dict]]:
    """获取所有字典表（仅活跃条目）。"""
    cached = await redis_client.json_get(CACHE_KEY_ALL)
    if cached is not None:
        return cached
    return await _refresh_cache(db)


async def get_dict_by_name(name: str, db: AsyncSession) -> list[dict] | None:
    """获取单张字典表。"""
    model = _get_model(name)
    if model is None:
        return None

    cached = await redis_client.json_get(_cache_key(name))
    if cached is not None:
        return cached

    return await _load_table(db, model)


async def _load_table(db: AsyncSession, model: type[_BaseDict]) -> list[dict]:
    """从 DB 加载一张字典表（仅活跃条目，按 sort_order 排序）。"""
    stmt = (
        select(model)
        .where(model.is_active.is_(True))
        .order_by(model.sort_order, model.code)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {"code": r.code, "name": r.name, "sort_order": r.sort_order}
        for r in rows
    ]


async def _refresh_cache(db: AsyncSession) -> dict[str, list[dict]]:
    """从 DB 重新加载并写入 Redis。"""
    data: dict[str, list[dict]] = {}
    for key, model in DICT_MODELS.items():
        items = await _load_table(db, model)
        data[key] = items
        await redis_client.json_set(_cache_key(key), items, expire=CACHE_TTL)
    await redis_client.json_set(CACHE_KEY_ALL, data, expire=CACHE_TTL)
    return data


# ── CRUD 写入操作（不经过缓存，直接操作 DB） ──

async def list_dict_items(
    db: AsyncSession,
    name: str,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list, int]:
    """分页查询字典条目（含已停用），支持 is_active 筛选。"""
    model = _get_model(name)
    if model is None:
        return [], 0

    stmt = select(model).order_by(model.sort_order, model.code)
    count_stmt = select(func.count(model.id))

    if is_active is not None:
        stmt = stmt.where(model.is_active.is_(is_active))
        count_stmt = count_stmt.where(model.is_active.is_(is_active))

    total = (await db.execute(count_stmt)).scalar_one()
    items = (
        await db.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
    ).scalars().all()

    return list(items), total


async def get_dict_item(db: AsyncSession, name: str, item_id: uuid.UUID):
    """获取字典单条记录。"""
    model = _get_model(name)
    if model is None:
        return None
    result = await db.execute(select(model).where(model.id == item_id))
    return result.scalar_one_or_none()


async def create_dict_item(db: AsyncSession, name: str, data: DictItemCreate):
    """创建字典条目。"""
    model = _get_model(name)
    if model is None:
        return None
    item = model(code=data.code, name=data.name, sort_order=data.sort_order, is_active=data.is_active)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    await _invalidate_cache(name)
    return item


async def update_dict_item(db: AsyncSession, name: str, item_id: uuid.UUID, data: DictItemUpdate):
    """更新字典条目。"""
    model = _get_model(name)
    if model is None:
        return None
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    await _invalidate_cache(name)
    return item


async def delete_dict_item(db: AsyncSession, name: str, item_id: uuid.UUID) -> bool:
    """删除字典条目。"""
    model = _get_model(name)
    if model is None:
        return False
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.flush()
    await _invalidate_cache(name)
    return True


async def toggle_dict_item_active(db: AsyncSession, name: str, item_id: uuid.UUID):
    """切换字典条目启用/停用。"""
    model = _get_model(name)
    if model is None:
        return None
    result = await db.execute(select(model).where(model.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return None
    item.is_active = not item.is_active
    await db.flush()
    await db.refresh(item)
    await _invalidate_cache(name)
    return item
