"""数据库公共工具：分页查询、软删除过滤、金额转换

提供：
- active_filter / paginate: 数据库层分页查询与软删除自动过滤
- fen_to_yuan / yuan_to_fen / fen_to_wan_yuan / wan_yuan_to_fen: 金额分/元/万元互转

Usage::

    from app.utils.db import paginate, fen_to_wan_yuan

    # 分页 + 软删除自动过滤
    stmt = select(Project).where(Project.status == "active").order_by(Project.created_at.desc())
    items, total = await paginate(db, stmt, model=Project, page=1, page_size=20)

    # 金额展示
    amount = fen_to_wan_yuan(project.total_investment)  # 分 → 万元
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


# ══════════════════════════════════════════════════════════════
# 软删除自动过滤
# ══════════════════════════════════════════════════════════════

def active_filter(stmt: Select, model: type) -> Select:
    """为查询自动追加软删除过滤条件 ``deleted_at IS NULL``。

    Args:
        stmt: SELECT 语句。
        model: ORM 模型类（用于检测是否含有 ``deleted_at`` 字段）。

    Returns:
        追加过滤条件后的 SELECT 语句。

    只对混入了 :class:`SoftDeleteMixin` 的模型生效。
    如果模型不含 ``deleted_at`` 字段，返回原语句。

    Usage::

        # 之前：每次都手写
        stmt = select(Project).where(Project.deleted_at.is_(None), ...)

        # 之后
        stmt = active_filter(select(Project).where(...), Project)
    """
    if hasattr(model, "deleted_at"):
        return stmt.where(model.deleted_at.is_(None))
    return stmt


# ══════════════════════════════════════════════════════════════
# 通用异步分页查询
# ══════════════════════════════════════════════════════════════

def calc_pages(total: int, page_size: int) -> int:
    """计算总页数。

    Args:
        total: 总记录数。
        page_size: 每页条数。

    Returns:
        总页数（0 表示无记录或 page_size 不合法）。

    Usage::

        pages = calc_pages(total, page_size)
        # 等价于 (total + page_size - 1) // page_size
    """
    if page_size <= 0:
        return 0
    return (total + page_size - 1) // page_size


async def paginate(
    db: AsyncSession,
    stmt: Select,
    *,
    page: int = 1,
    page_size: int = 20,
    auto_active: bool = True,
    model: type | None = None,
    count_stmt: Select | None = None,
    unique: bool = False,
) -> tuple[Sequence[T], int]:
    """通用异步分页查询。

    对 SELECT 语句自动执行 COUNT 统计和分页取数。
    返回值签名 ``(items, total)`` 与现有 service 层一致，可直接替换。

    Args:
        db: 数据库异步会话。
        stmt: 查询语句（可含 WHERE、ORDER BY、JOIN、options 等）。
        page: 页码，从 1 开始。
        page_size: 每页条数，默认 20。
        auto_active: 为 ``True`` 时自动追加 ``deleted_at IS NULL`` 过滤。
        model: ORM 模型类（``auto_active=True`` 时需要）。
        count_stmt: 自定义 COUNT 语句（覆盖自动生成的子查询统计）。
        unique: 为 ``True`` 时对结果去重（应对 ``joinedload`` 产生的重复行）。

    Returns:
        (items, total) — 模型实例序列与总记录数。

    Raises:
        ValueError: ``auto_active=True`` 但未提供 ``model``。

    Usage::

        # ── 基础用法 ──────────────────────────────────
        stmt = select(Project).where(
            Project.project_status == "active",
        ).order_by(Project.created_at.desc())
        items, total = await paginate(db, stmt, model=Project, page=1, page_size=20)

        # ── 带关系加载 ────────────────────────────────
        from sqlalchemy.orm import selectinload
        stmt = select(Project).options(selectinload(Project.contracts))
        items, total = await paginate(db, stmt, model=Project, page=1)

        # ── 复杂查询：需要自定义 COUNT ────────────────
        from sqlalchemy import func
        count_stmt = select(func.count(Project.id)).where(Project.project_status == "active")
        items, total = await paginate(db, stmt, model=Project, count_stmt=count_stmt)

        # ── 不需要软删除过滤（如字典表） ───────────────
        items, total = await paginate(db, stmt, auto_active=False)
    """
    if auto_active:
        if model is None:
            raise ValueError("auto_active=True 时必须提供 model 参数")
        stmt = active_filter(stmt, model)

    # ── 统计总数 ──────────────────────────────────────
    if count_stmt is not None:
        total = (await db.execute(count_stmt)).scalar_one()
    else:
        # 去除 ORDER BY 后做子查询统计，兼容 JOIN / GROUP BY 场景
        subq = stmt.order_by(None).subquery()
        total = (await db.execute(select(func.count()).select_from(subq))).scalar_one()

    # ── 分页取数 ──────────────────────────────────────
    if total == 0:
        return [], 0

    paged = await db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    )
    items = paged.unique().scalars().all() if unique else paged.scalars().all()

    return items, total


# ══════════════════════════════════════════════════════════════
# 金额转换（分 / 元 / 万元）
# ══════════════════════════════════════════════════════════════
# 数据库约定：金额以「分」为存储单位（BIGINT），避免浮点精度问题。
# 本模块提供展示层（分 → 元/万元）和入库层（元/万元 → 分）的双向转换。
# 数据清洗/导入侧的转换见 app.utils.converter（处理 Excel 日期、别名等）。

def fen_to_yuan(fen: int) -> float:
    """分 → 元（展示用）。

    将数据库存储的「分」值转换为界面展示的「元」。
    适用于详情页、列表页的单个金额字段展示。

    Example::

        >>> fen_to_yuan(12345)
        123.45
        >>> fen_to_yuan(100)
        1.0
        >>> fen_to_yuan(0)
        0.0
    """
    return fen / 100


def fen_to_wan_yuan(fen: int) -> float:
    """分 → 万元（展示用）。

    将数据库存储的「分」值转换为「万元」显示。
    用于财务报表、概览面板、统计图表等大额金额场景。

    Example::

        >>> fen_to_wan_yuan(123456789)
        12345.6789
        >>> fen_to_wan_yuan(100000000)  # 1 亿元 = 10000 万元
        10000.0
    """
    return fen / 100 / 10000


def yuan_to_fen(yuan: float | Decimal | str) -> int:
    """元 → 分（入库用）。

    将用户输入或接口提交的「元」金额转换为数据库存储的「分」。
    支持千分位逗号格式（中文/英文逗号），自动取整。

    Args:
        yuan: 元金额，可以是 float、Decimal 或字符串（如 ``"1,234.56"``）。

    Returns:
        整数分。

    Example::

        >>> yuan_to_fen(123.45)
        12345
        >>> yuan_to_fen("1,234.56")
        123456
        >>> yuan_to_fen(0)
        0
    """
    return int(Decimal(str(yuan).replace(",", "").replace("，", "")) * 100)


def wan_yuan_to_fen(wan_yuan: float | Decimal | str) -> int:
    """万元 → 分（入库用）。

    将概览面板或 Excel 导入中的「万元」金额转换为数据库存储的「分」。
    支持千分位逗号格式，自动取整。

    Args:
        wan_yuan: 万元金额，可以是 float、Decimal 或字符串。

    Returns:
        整数分。

    Example::

        >>> wan_yuan_to_fen(123.4567)
        123456700
        >>> wan_yuan_to_fen("12,345.67")
        12345670000
        >>> wan_yuan_to_fen(0.0)
        0
    """
    return int(Decimal(str(wan_yuan).replace(",", "").replace("，", "")) * 100 * 10000)
