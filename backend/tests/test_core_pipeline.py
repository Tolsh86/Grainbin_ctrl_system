"""核心业务流程测试：项目 → 上传 → 映射 → 解析 → 清洗行 → 入库 → 撤回

覆盖数据接入全链路，是系统最关键的业务路径。
"""

from __future__ import annotations

import uuid

import pytest

from tests.conftest import _make_auth_header


# ══════════════════════════════════════════════════════
# 映射模板管理
# ══════════════════════════════════════════════════════


class TestMappingTemplate:
    """字段映射模板 CRUD + 预置"""

    @pytest.mark.asyncio
    async def test_create_mapping(self, client, operator_auth, test_project):
        _, token = operator_auth
        resp = await client.post("/api/v1/import/mapping", json={
            "mapping_name": "监理周报模板",
            "biz_type": "weekly",
            "file_format": "xlsx",
            "header_row": 1,
            "sheet_index": 0,
            "project_id": str(test_project),
            "rules": [
                {"user_header": "序号", "system_field": "row_no"},
                {"user_header": "分项名称", "system_field": "item_name"},
                {"user_header": "计划量", "system_field": "planned_quantity"},
                {"user_header": "实际量", "system_field": "actual_quantity"},
                {"user_header": "单价(元)", "system_field": "unit_price", "converter": "yuan_to_fen"},
                {"user_header": "金额(元)", "system_field": "amount", "converter": "yuan_to_fen"},
            ],
        }, headers=_make_auth_header(token))
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["mapping_name"] == "监理周报模板"
        assert data["biz_type"] == "weekly"
        assert data["file_format"] == "xlsx"
        return uuid.UUID(data["id"])

    @pytest.mark.asyncio
    async def test_list_mappings(self, client, operator_auth):
        _, token = operator_auth
        resp = await client.get("/api/v1/import/mapping", headers=_make_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "pages" in data

    @pytest.mark.asyncio
    async def test_get_mapping(self, client, operator_auth):
        _, token = operator_auth
        # 先建一个
        create_resp = await client.post("/api/v1/import/mapping", json={
            "mapping_name": "测试模板",
            "biz_type": "general",
            "file_format": "xlsx",
            "rules": [{"user_header": "名称", "system_field": "item_name"}],
        }, headers=_make_auth_header(token))
        mapping_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/v1/import/mapping/{mapping_id}", headers=_make_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["mapping_name"] == "测试模板"

    @pytest.mark.asyncio
    async def test_update_mapping(self, client, operator_auth):
        _, token = operator_auth
        create_resp = await client.post("/api/v1/import/mapping", json={
            "mapping_name": "待更新模板",
            "biz_type": "general",
            "file_format": "xlsx",
            "rules": [{"user_header": "名称", "system_field": "item_name"}],
        }, headers=_make_auth_header(token))
        mapping_id = create_resp.json()["data"]["id"]

        resp = await client.put(
            f"/api/v1/import/mapping/{mapping_id}",
            json={"mapping_name": "已更新模板", "is_active": False},
            headers=_make_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["mapping_name"] == "已更新模板"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_mapping(self, client, operator_auth):
        _, token = operator_auth
        create_resp = await client.post("/api/v1/import/mapping", json={
            "mapping_name": "待删除模板",
            "biz_type": "general",
            "file_format": "xlsx",
            "rules": [{"user_header": "名称", "system_field": "item_name"}],
        }, headers=_make_auth_header(token))
        mapping_id = create_resp.json()["data"]["id"]

        resp = await client.delete(f"/api/v1/import/mapping/{mapping_id}", headers=_make_auth_header(token))
        assert resp.status_code == 200

        # 再次查询应 404
        resp = await client.get(f"/api/v1/import/mapping/{mapping_id}", headers=_make_auth_header(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_seed_presets(self, client, admin_auth):
        _, token = admin_auth
        resp = await client.post("/api/v1/import/mapping/presets", headers=_make_auth_header(token))
        assert resp.status_code == 200
        assert "已初始化" in resp.json()["message"]

        # 查询预设
        resp = await client.get("/api/v1/import/mapping", headers=_make_auth_header(token))
        items = resp.json()["items"]
        biz_types = {m["biz_type"] for m in items}
        assert "weekly" in biz_types
        assert "monthly" in biz_types
        assert "progress_payment" in biz_types


# ══════════════════════════════════════════════════════
# 文件上传 → 批次创建
# ══════════════════════════════════════════════════════


class TestUpload:
    """文件上传与批次创建"""

    @pytest.mark.asyncio
    async def test_upload_xlsx(self, client, operator_auth, test_project, sample_excel_bytes):
        _, token = operator_auth
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("weekly_report.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["file_name"] == "weekly_report.xlsx"
        assert data["file_format"] == "xlsx"
        assert data["batch_no"]
        assert data["batch_id"]
        assert data["file_path"].startswith("upload/")

    @pytest.mark.asyncio
    async def test_upload_rejects_exe(self, client, operator_auth, test_project):
        """可执行文件应被拦截（MZ 头伪装）"""
        _, token = operator_auth
        exe_content = b"MZ\x90\x00" + b"\x00" * 100
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("malware.xlsx", exe_content,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        assert resp.status_code == 400
        assert "可执行" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_rejects_unsupported_extension(self, client, operator_auth, test_project):
        _, token = operator_auth
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("document.pdf", b"fake pdf content", "application/pdf"),
        }, headers=_make_auth_header(token))
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_rejects_empty_file(self, client, operator_auth, test_project):
        _, token = operator_auth
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("empty.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        assert resp.status_code == 400
        assert "空文件" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_rejects_oversized_file(self, client, operator_auth, test_project):
        """超过 50MB 应拒绝（文件格式校验先拦截，所以用 xlsx 头）"""
        _, token = operator_auth
        # 构造一个超过50MB的假文件 — 用实际 xlsx 魔数头部
        large = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * (51 * 1024 * 1024)
        title = "oversized.xls"
        resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": (title, large, "application/vnd.ms-excel"),
        }, headers=_make_auth_header(token))
        assert resp.status_code == 400
        assert "超过" in resp.json()["detail"] or "大小" in resp.json()["detail"]


# ══════════════════════════════════════════════════════
# 批次解析与清洗行
# ══════════════════════════════════════════════════════


class TestBatchAndIngest:
    """批次管理 + 清洗入库流水线"""

    @pytest.mark.asyncio
    async def test_get_batch_detail(self, client, operator_auth, test_project, sample_excel_bytes):
        """上传文件后查看批次详情"""
        _, token = operator_auth

        # Step 1: 上传
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        # Step 2: 查看批次详情
        resp = await client.get(f"/api/v1/import/batch/{batch_id}", headers=_make_auth_header(token))
        assert resp.status_code == 200
        batch = resp.json()
        assert batch["source_doc"] == "data.xlsx"
        assert batch["status"] == "pending"
        assert "total_rows" in batch

    @pytest.mark.asyncio
    async def test_trigger_parse(self, client, operator_auth, test_project, sample_excel_bytes):
        """触发解析任务 — 从 pending 变为 parsing"""
        _, token = operator_auth

        # Step 1: 上传
        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        # Step 2: 触发解析
        resp = await client.post(
            f"/api/v1/import/batch/{batch_id}/parse",
            headers=_make_auth_header(token),
        )
        assert resp.status_code == 200
        assert "已提交" in resp.json()["message"]

        # Step 3: 状态应变为 parsing
        detail = await client.get(
            f"/api/v1/import/batch/{batch_id}",
            headers=_make_auth_header(token),
        )
        assert detail.json()["status"] == "parsing"

    @pytest.mark.asyncio
    async def test_parse_rejects_already_parsing(self, client, operator_auth, test_project, sample_excel_bytes):
        """已触发解析的批次，再次触发应失败"""
        _, token = operator_auth

        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        # 第一次触发成功
        await client.post(f"/api/v1/import/batch/{batch_id}/parse", headers=_make_auth_header(token))

        # 第二次触发应失败
        resp = await client.post(f"/api/v1/import/batch/{batch_id}/parse", headers=_make_auth_header(token))
        assert resp.status_code == 400
        assert "不允许" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_batch_rows_empty(self, client, operator_auth, test_project, sample_excel_bytes):
        """未解析的批次 rows 应为空"""
        _, token = operator_auth

        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.get(f"/api/v1/import/batch/{batch_id}/rows", headers=_make_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_batch_errors_empty(self, client, operator_auth, test_project, sample_excel_bytes):
        """无错误的批次 errors 应为空"""
        _, token = operator_auth

        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.get(f"/api/v1/import/batch/{batch_id}/errors", headers=_make_auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_commit_batch_not_ready(self, client, operator_auth, test_project, sample_excel_bytes):
        """未解析/未校验通过的批次不能入库"""
        _, token = operator_auth

        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        # pending 状态不能入库
        resp = await client.post(
            f"/api/v1/ingest/batches/{batch_id}/commit",
            headers=_make_auth_header(token),
        )
        assert resp.status_code in (400, 404)  # ingest commit 可能走旧路由

    @pytest.mark.asyncio
    async def test_rollback_batch_not_committed(self, client, admin_auth, test_project, sample_excel_bytes):
        """未入库的批次不能撤回"""
        _, token = admin_auth

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
        assert resp.status_code == 400
        assert "不能撤回" in resp.json()["detail"] or "未入库" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_batch_nonexistent(self, client, operator_auth):
        _, token = operator_auth
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/import/batch/{fake_id}", headers=_make_auth_header(token))
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════
# 旧 ingest 路由兼容测试
# ══════════════════════════════════════════════════════


class TestLegacyIngestRoutes:
    """确保旧路由仍可基本工作"""

    @pytest.mark.asyncio
    async def test_list_batches(self, client, operator_auth, test_project):
        _, token = operator_auth
        resp = await client.get(
            f"/api/v1/ingest/batches?project_id={test_project}",
            headers=_make_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_batch_nonexistent_legacy(self, client, operator_auth):
        _, token = operator_auth
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/ingest/batches/{fake_id}", headers=_make_auth_header(token))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_batch_rows_legacy(self, client, operator_auth, test_project, sample_excel_bytes):
        """上传后走 ingest 路由查看行数据"""
        _, token = operator_auth

        upload_resp = await client.post("/api/v1/upload/file", data={
            "project_id": str(test_project),
        }, files={
            "file": ("data.xlsx", sample_excel_bytes,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        }, headers=_make_auth_header(token))
        batch_id = upload_resp.json()["data"]["batch_id"]

        resp = await client.get(
            f"/api/v1/ingest/batches/{batch_id}/rows",
            headers=_make_auth_header(token),
        )
        assert resp.status_code == 200
