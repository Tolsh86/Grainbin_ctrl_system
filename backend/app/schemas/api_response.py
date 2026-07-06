"""标准 API 响应封装"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一成功响应"""

    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Any = None
