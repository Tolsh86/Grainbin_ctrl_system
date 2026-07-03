"""用户 Schema：请求/响应模型

与 t_users 模型字段完全对齐。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── 请求 ──

class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=2, max_length=50, description="登录名")
    password: str = Field(..., min_length=6, max_length=128, description="密码（6-128位）")
    real_name: str = Field(..., min_length=1, max_length=100, description="真实姓名")
    email: str | None = Field(None, max_length=200, description="邮箱")
    role: str = Field("operator", description="角色")
    is_active: bool = Field(True, description="是否启用")


class UserUpdate(BaseModel):
    """更新用户 — 所有字段可选"""
    username: str | None = Field(None, min_length=2, max_length=50, description="登录名")
    password: str | None = Field(None, min_length=6, max_length=128, description="密码")
    real_name: str | None = Field(None, min_length=1, max_length=100, description="真实姓名")
    email: str | None = Field(None, max_length=200, description="邮箱")
    role: str | None = Field(None, description="角色")
    is_active: bool | None = Field(None, description="是否启用")


class UserLogin(BaseModel):
    """用户登录"""
    username: str = Field(..., max_length=50, description="登录名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


# ── 响应 ──

class UserResponse(BaseModel):
    """用户信息响应"""
    id: uuid.UUID
    username: str
    real_name: str
    email: str | None = None
    role: str
    project_permissions: dict | list | None = None
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT 令牌"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")
