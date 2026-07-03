"""分页工具"""

from __future__ import annotations

import math
from typing import Any


def paginate_items(
    items: list[Any],
    page: int,
    page_size: int,
) -> dict:
    """对已加载的列表做内存分页。

    Args:
        items: 数据列表
        page: 页码（从 1 开始）
        page_size: 每页条数

    Returns:
        {"items": [...], "total": int, "page": int, "page_size": int, "pages": int}
    """
    total = len(items)
    pages = math.ceil(total / page_size) if page_size > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
