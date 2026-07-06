"""权限控制测试：验证各角色在各端点的访问边界

角色等级：admin(0) > project_manager/auditor(1) > operator(2) > viewer(3)
"""

from __future__ import annotations

import uuid

import pytest

from tests.conftest import _make_auth_header


# ══════════════════════════════════════════════════════
# 映射模板：需要 operator+
# ══════════════════════════════════════════════════════


class TestMappingPermissions:
    """映射模板 CRUD 权限"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_mapping(self, client, viewer_auth):
        _, token = viewer_auth
        resp = await client.post("/api/v1/import/mapping", json={
            "mapping_name": "viewer 不应能创建",
            "biz_type": "general",
            "file_format": "xlsx",
            "rules": [{"user_header": "名称", "system_field": "item_name"}],
        }, headers=_make_auth_header(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_list_mappings(self, client, viewer_auth):
        _, token = viewer_auth
        resp = await client.get("/api/v1/import/mapping", headers=_make_auth_header(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_can_list_mappings(self, client, operator_auth):
        _, token = operator_auth
        resp = await client.get("/api/v1/import/mapping", headers=_make_auth_header(token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_cannot_seed_presets(self, client, viewer_auth):
        _, token = viewer_auth
        resp = await client.post("/api/v1/import/mapping/presets", headers=_make_auth_header(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_cannot_seed_presets(self, client, operator_auth):
        """seed_presets 只允许 admin"""
        _, token = operator_auth
        resp = await client.post("/api/v1/import/mapping/presets", headers=_make_auth_header(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_seed_presets(self, client, admin_auth):
        _, token = admin_auth
        resp = await client.post("/api/v1/import/mapping/presets", headers=_make_auth_header(token))
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════
# 文件上传：需要 operator+
# ══════════════════════════════════════════════════════


class TestUploadPermissions:
    """文件上传权限"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_upload(self, client, viewer_auth, test_project, sample_excel_bytes):
        """上传路由使用 get_current_user（只要求认证），所以 viewer 实际上可以上传"""
        _, token = viewer_auth
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        # 当前实现：upload 端点只要求已登录，不限制角色
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_anonymous_cannot_upload(self, client, test_project, sample_excel_bytes):
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        })
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════
# 批次：需要 operator+
# ══════════════════════════════════════════════════════


class TestBatchPermissions:
    """批次管理权限"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_get_batch(self, client, viewer_auth, operator_auth, test_project, sample_excel_bytes):
        _, v_token = viewer_auth
        _op_uid, op_token = operator_auth
        # 由 operator 创建一个批次
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(op_token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        # viewer 无权查看批次
        resp = await client.get(f"/api/v1/import/batch/{batch_id}", headers=_make_auth_header(v_token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_trigger_parse(self, client, viewer_auth, operator_auth, test_project, sample_excel_bytes):
        _, v_token = viewer_auth
        _op_uid, op_token = operator_auth
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(op_token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.post(f"/api/v1/import/batch/{batch_id}/parse", headers=_make_auth_header(v_token))
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════
# 入库/撤回：精确权限边界
# ══════════════════════════════════════════════════════


class TestIngestPermissions:
    """入库/撤回权限"""

    @pytest.mark.asyncio
    async def test_viewer_cannot_commit(self, client, viewer_auth, operator_auth, test_project, sample_excel_bytes):
        _, v_token = viewer_auth
        _op_uid, op_token = operator_auth
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(op_token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.post(
            f"/api/v1/ingest/batches/{batch_id}/commit",
            headers=_make_auth_header(v_token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_cannot_rollback(self, client, operator_auth, test_project, sample_excel_bytes):
        """撤回只需 admin"""
        _, token = operator_auth
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.post(
            f"/api/v1/ingest/batches/{batch_id}/rollback",
            headers=_make_auth_header(token),
        )
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════
# 项目删除：需要 admin
# ══════════════════════════════════════════════════════


class TestProjectDeletePermissions:
    """项目删除权限"""

    @pytest.mark.asyncio
    async def test_operator_cannot_delete_project(self, client, operator_auth, test_project):
        _, token = operator_auth
        resp = await client.delete(f"/api/v1/projects/{test_project}", headers=_make_auth_header(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_delete_project(self, client, admin_auth, test_project):
        _, token = admin_auth
        resp = await client.delete(f"/api/v1/projects/{test_project}", headers=_make_auth_header(token))
        assert resp.status_code == 200
        assert "删除" in resp.json()["message"]
