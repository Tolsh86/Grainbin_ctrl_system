"""认证模块测试：注册、登录、Token 校验"""

from __future__ import annotations

import pytest

from tests.conftest import _make_auth_header


# ══════════════════════════════════════════════════════
# 注册
# ══════════════════════════════════════════════════════


class TestRegister:
    """用户注册"""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "password": "pass123456",
            "real_name": "新用户",
            "role": "operator",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["real_name"] == "新用户"
        assert data["role"] == "operator"
        assert data["is_active"] is True
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client):
        await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "password": "pass123456",
            "real_name": "重复用户",
            "role": "operator",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": "dupuser",
            "password": "pass999999",
            "real_name": "重复用户2",
            "role": "admin",
        })
        assert resp.status_code == 409
        assert "已存在" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "username": "shortpw",
            "password": "12345",
            "real_name": "短密码",
            "role": "operator",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_required(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "username": "noreal",
        })
        assert resp.status_code == 422


# ══════════════════════════════════════════════════════
# 登录
# ══════════════════════════════════════════════════════


class TestLogin:
    """用户登录"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, admin_auth):
        user_id, token = admin_auth
        assert len(token) > 20
        assert isinstance(user_id, type(user_id))  # UUID

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, admin_auth):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/v1/auth/login", json={
            "username": "ghost",
            "password": "whatever",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_returns_token_with_user_info(self, client):
        """登录返回 token + 用户信息"""
        # 先注册一个用户
        await client.post("/api/v1/auth/register", json={
            "username": "info_tester",
            "password": "info123456",
            "real_name": "信息测试",
            "role": "admin",
        })
        resp = await client.post("/api/v1/auth/login", json={
            "username": "info_tester",
            "password": "info123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        assert data["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_disabled_user(self, client, admin_auth):
        """用户被禁用后无法登录"""
        admin_uid, admin_token = admin_auth
        # 注册一个待禁用用户
        await client.post("/api/v1/auth/register", json={
            "username": "tobedisabled",
            "password": "pass123456",
            "real_name": "待禁用",
            "role": "operator",
        })
        # 查询用户列表找到该用户
        list_resp = await client.get("/api/v1/users", headers=_make_auth_header(admin_token))
        users = list_resp.json()["items"]
        target = next(u for u in users if u["username"] == "tobedisabled")
        # 切换启用状态
        await client.patch(
            f"/api/v1/users/{target['id']}/toggle-active",
            headers=_make_auth_header(admin_token),
        )
        # 被禁用后无法登录
        resp = await client.post("/api/v1/auth/login", json={
            "username": "tobedisabled",
            "password": "pass123456",
        })
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════
# Token 校验
# ══════════════════════════════════════════════════════


class TestTokenAuth:
    """Token 校验边界"""

    @pytest.mark.asyncio
    async def test_missing_token(self, client):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        resp = await client.get("/api/v1/users/me", headers={
            "Authorization": "Bearer invalid.token.here",
        })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, client, admin_auth):
        user_id, token = admin_auth
        resp = await client.get("/api/v1/users/me", headers=_make_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
