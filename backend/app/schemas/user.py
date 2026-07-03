"""用户 Schema：注册/登录/响应/令牌"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── 请求 ──

class UserCreate(BaseModel):
    """注册新用户"""

    email: str = Field(..., max_length=255, description="邮箱（登录账号）")
    password: str = Field(..., min_length=6, max_length=128, description="密码（6-128位）")
    full_name: str = Field(..., min_length=1, max_length=100, description="姓名")
    role: str = Field("viewer", pattern=r"^(admin|manager|editor|viewer)$", description="角色")


class UserLogin(BaseModel):
    """用户登录"""

    email: str = Field(..., max_length=255, description="邮箱")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


# ── 响应 ──

class UserResponse(BaseModel):
    """用户信息"""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT 令牌"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")
