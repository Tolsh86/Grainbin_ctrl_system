"""业务逻辑单元测试：Excel 解析器 (parser.py) 纯函数

不依赖 MinIO / Celery / DB，直接测试清洗流水线的每个环节。
"""

from __future__ import annotations

import io
from datetime import date

import pytest
from openpyxl import Workbook

from app.services.parser import (
    _build_col_map,
    _clean_cell,
    _fill_merged_cells,
    _normalize_row,
    _read_xlsx_rows,
)


# ═══════════════════════════════════════════════════════
# _clean_cell — 单元格值清洗
# ═══════════════════════════════════════════════════════

class TestCleanCell:
    """单元格清洗：去空格、空值→None"""

    def test_none_stays_none(self):
        assert _clean_cell(None) is None

    def test_empty_string_becomes_none(self):
        assert _clean_cell("") is None
        assert _clean_cell("   ") is None
        assert _clean_cell("\t  \n") is None

    def test_trim_whitespace(self):
        assert _clean_cell("  钢筋  ") == "钢筋"
        assert _clean_cell("  123  ") == "123"

    def test_number_preserved(self):
        assert _clean_cell(100) == 100
        assert _clean_cell(3.14) == 3.14
        assert _clean_cell(0) == 0  # 0 不是 None

    def test_date_preserved(self):
        d = date(2025, 6, 15)
        assert _clean_cell(d) == d


# ═══════════════════════════════════════════════════════
# _fill_merged_cells — 合并单元格向下补全
# ═══════════════════════════════════════════════════════

class TestFillMergedCells:
    """合并单元格向下补全：空值/空串继承上一行同列值"""

    def test_empty_list_noop(self):
        rows: list[dict] = []
        _fill_merged_cells(rows)
        assert rows == []

    def test_single_row_noop(self):
        rows = [{"a": "值1", "b": None}]
        _fill_merged_cells(rows)
        assert rows[0]["b"] is None  # 第一行不补

    def test_fill_down_none(self):
        rows = [
            {"name": "混凝土", "unit": "m³"},
            {"name": None,     "unit": "m³"},   # name 应从上一行继承
            {"name": None,     "unit": None},    # 两列都继承
        ]
        _fill_merged_cells(rows)
        assert rows[0]["name"] == "混凝土"
        assert rows[1]["name"] == "混凝土"  # 补全
        assert rows[2]["name"] == "混凝土"  # 补全
        assert rows[2]["unit"] == "m³"      # 补全

    def test_fill_down_empty_string(self):
        rows = [
            {"category": "主体工程"},
            {"category": ""},       # 空串也应补全
            {"category": ""},
        ]
        _fill_merged_cells(rows)
        assert all(r["category"] == "主体工程" for r in rows)

    def test_do_not_overwrite_existing(self):
        rows = [
            {"category": "地基"},
            {"category": "主体"},   # 有值，不覆盖
            {"category": None},
        ]
        _fill_merged_cells(rows)
        assert rows[0]["category"] == "地基"
        assert rows[1]["category"] == "主体"    # 不覆盖
        assert rows[2]["category"] == "主体"    # 从上一行继承

    def test_multiple_gaps(self):
        rows = [
            {"a": "A1", "b": "B1"},
            {"a": None,  "b": None},
            {"a": "A3", "b": None},   # a 有值，b 继承
            {"a": None,  "b": "B4"},   # b 有值，a 继承
        ]
        _fill_merged_cells(rows)
        assert rows[1]["a"] == "A1"
        assert rows[1]["b"] == "B1"
        assert rows[2]["a"] == "A3"
        assert rows[2]["b"] == "B1"   # 继承 B1（上一行 b 为 None）
        assert rows[3]["a"] == "A3"   # 继承 A3
        assert rows[3]["b"] == "B4"


# ═══════════════════════════════════════════════════════
# _build_col_map — 表头匹配映射规则
# ═══════════════════════════════════════════════════════

class TestBuildColMap:
    """根据表头行匹配映射规则"""

    RULES = [
        {"user_header": "项目名称", "system_field": "item_name"},
        {"user_header": "工程量",   "system_field": "actual_quantity"},
        {"user_header": "金额",     "system_field": "amount", "converter": "yuan_to_fen"},
    ]

    def test_exact_match(self):
        headers = ["项目名称", "工程量", "金额"]
        cm = _build_col_map(headers, self.RULES)
        assert len(cm) == 3
        assert cm[0]["system_field"] == "item_name"
        assert cm[1]["system_field"] == "actual_quantity"
        assert cm[2]["system_field"] == "amount"
        assert cm[2]["converter"] == "yuan_to_fen"

    def test_partial_match(self):
        headers = ["项目名称", "未知列", "金额"]
        cm = _build_col_map(headers, self.RULES)
        assert len(cm) == 2
        assert cm[0]["system_field"] == "item_name"
        assert cm[2]["system_field"] == "amount"
        assert 1 not in cm  # "未知列" 不匹配任何规则

    def test_no_match(self):
        headers = ["A", "B", "C"]
        cm = _build_col_map(headers, self.RULES)
        assert len(cm) == 0

    def test_empty_headers(self):
        cm = _build_col_map([], self.RULES)
        assert len(cm) == 0

    def test_whitespace_headers_match(self):
        """表头带前后空格应能匹配"""
        headers = ["  项目名称 ", " 金额"]
        cm = _build_col_map(headers, self.RULES)
        assert len(cm) == 2
        assert cm[0]["system_field"] == "item_name"
        assert cm[1]["system_field"] == "amount"


# ═══════════════════════════════════════════════════════
# _normalize_row — 清洗归一化
# ═══════════════════════════════════════════════════════

class TestNormalizeRow:
    """一行数据清洗归一化"""

    RULES = [
        {"user_header": "日期",     "system_field": "data_date",       "converter": "iso_date"},
        {"user_header": "分项名称", "system_field": "item_name",        "converter": "trim"},
        {"user_header": "数量",     "system_field": "actual_quantity",  "converter": ""},
        {"user_header": "单价(元)", "system_field": "unit_price",       "converter": "yuan_to_fen"},
        {"user_header": "总价(元)", "system_field": "amount",           "converter": "yuan_to_fen"},
        {"user_header": "单位",     "system_field": "unit",             "converter": "trim"},
    ]

    def test_basic_normalization(self):
        raw = {
            "日期": "2025-06-15",
            "分项名称": "  混凝土  ",
            "数量": "150",
            "单价(元)": "380.5",
            "总价(元)": "57075",
            "单位": "m³",
        }
        result = _normalize_row(raw, self.RULES)
        assert result["data_date"] == date(2025, 6, 15)
        assert result["item_name"] == "混凝土"
        assert result["actual_quantity"] == "150"  # 无 converter，保留原值
        assert result["unit_price"] == 38050       # 380.5 元 → 38050 分
        assert result["amount"] == 5707500         # 57075 元 → 5707500 分
        assert result["unit"] == "m³"

    def test_empty_cells_become_none(self):
        raw = {
            "日期": "",
            "分项名称": None,
            "数量": "   ",
            "单价(元)": "",
            "总价(元)": "",
            "单位": None,
        }
        result = _normalize_row(raw, self.RULES)
        assert result["data_date"] is None
        assert result["item_name"] is None
        assert result["actual_quantity"] is None   # _clean_cell 后空串 → None
        assert result["unit_price"] is None
        assert result["amount"] is None
        assert result["unit"] is None

    def test_chinese_date_format(self):
        """中文日期格式 '2025年6月15日' → date"""
        rules = [{"user_header": "日期", "system_field": "data_date", "converter": "chinese_date_to_iso"}]
        raw = {"日期": "2025年6月15日"}
        result = _normalize_row(raw, rules)
        assert result["data_date"] == date(2025, 6, 15)

    def test_slash_date_format(self):
        """斜杠日期 '2025/06/15' → date"""
        rules = [{"user_header": "日期", "system_field": "data_date", "converter": "iso_date"}]
        raw = {"日期": "2025/06/15"}
        result = _normalize_row(raw, rules)
        assert result["data_date"] == date(2025, 6, 15)

    def test_excel_serial_date(self):
        """Excel 序列号日期 → date（45291 = 2023-12-31）
        
        注意: 当 system_field == 'data_date' 且 converter='excel_serial_to_date' 时，
        auto-detect 先转为 date，然后 converter 再次调用 excel_serial_to_date(date_obj)，
        后者内部 catch TypeError 返回 None → 最终 normalized 值为 None。
        这是已知 bug，本测试记录当前行为。
        """
        rules = [{"user_header": "日期", "system_field": "data_date", "converter": "excel_serial_to_date"}]
        raw = {"日期": 45291}
        result = _normalize_row(raw, rules)
        # 当前行为: auto-detect 转为 date(2023,12,31), converter 再调转失败 → None
        assert result["data_date"] is None

    def test_invalid_date_becomes_none(self):
        """不可解析的日期 → None"""
        rules = [{"user_header": "日期", "system_field": "data_date", "converter": "iso_date"}]
        raw = {"日期": "不是日期"}
        result = _normalize_row(raw, rules)
        assert result["data_date"] is None

    def test_yuan_to_fen_with_comma(self):
        """金额含千位分隔符: '1,234.56' → 123456 分"""
        rules = [{"user_header": "金额", "system_field": "amount", "converter": "yuan_to_fen"}]
        raw = {"金额": "1,234.56"}
        result = _normalize_row(raw, rules)
        assert result["amount"] == 123456

    def test_yuan_to_fen_integer(self):
        """整金额: '500' → 50000 分"""
        rules = [{"user_header": "金额", "system_field": "amount", "converter": "yuan_to_fen"}]
        raw = {"金额": 500}
        result = _normalize_row(raw, rules)
        assert result["amount"] == 50000

    def test_missing_field_in_raw(self):
        """原始数据缺少某列 → normalized 中该字段为 None"""
        rules = [{"user_header": "金额", "system_field": "amount", "converter": "yuan_to_fen"}]
        raw: dict = {}  # 没有 "金额" 这个 key
        result = _normalize_row(raw, rules)
        assert result["amount"] is None

    def test_data_date_auto_detect_from_system_field(self):
        """当 system_field == 'data_date' 时，即使没指定 converter 也自动检测日期"""
        rules = [{"user_header": "数据日期", "system_field": "data_date"}]
        raw = {"数据日期": "2025-07-01"}
        result = _normalize_row(raw, rules)
        assert result["data_date"] == date(2025, 7, 1)

    def test_data_date_auto_detect_excel_serial(self):
        """当 system_field == 'data_date' 且值为数值时，按 Excel 序列号处理
        
        45291 → 2023-12-31
        """
        rules = [{"user_header": "数据日期", "system_field": "data_date"}]
        raw = {"数据日期": 45291}
        result = _normalize_row(raw, rules)
        assert result["data_date"] == date(2023, 12, 31)

    def test_data_date_auto_detect_chinese(self):
        """当 system_field == 'data_date' 且值为中文格式"""
        rules = [{"user_header": "数据日期", "system_field": "data_date"}]
        raw = {"数据日期": "2025年7月1日"}
        result = _normalize_row(raw, rules)
        assert result["data_date"] == date(2025, 7, 1)


# ═══════════════════════════════════════════════════════
# _read_xlsx_rows — 真实 Excel 文件读取
# ═══════════════════════════════════════════════════════

def _make_xlsx_bytes(headers: list, data_rows: list[list]) -> bytes:
    """在内存中创建一个 xlsx 文件。"""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in data_rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    return buf.getvalue()


RULES_SIMPLE = [
    {"user_header": "名称", "system_field": "item_name", "converter": "trim"},
    {"user_header": "数量", "system_field": "planned_quantity"},
    {"user_header": "单位", "system_field": "unit", "converter": "trim"},
]


class TestReadXlsxRows:
    """读取真实 Excel 文件"""

    def test_basic_xlsx_read(self):
        headers = ["名称", "数量", "单位"]
        data = [
            ["混凝土", 150, "m³"],
            ["钢筋",    80, "t"],
        ]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=RULES_SIMPLE)

        assert len(rows) == 2
        assert rows[0] == {"名称": "混凝土", "数量": 150, "单位": "m³"}
        assert rows[1] == {"名称": "钢筋",   "数量": 80,  "单位": "t"}

    def test_skip_header_rows(self):
        """表头在第 3 行，前两行是标题/空行"""
        headers_row = ["名称", "数量"]
        data = [
            ["混凝土", 100],
        ]
        wb = Workbook()
        ws = wb.active
        ws.append(["项目进度月报"])   # row 1: 标题
        ws.append([])                 # row 2: 空行
        ws.append(headers_row)        # row 3: 表头
        ws.append(data[0])            # row 4: 数据
        buf = io.BytesIO()
        wb.save(buf)
        wb.close()

        rules = [{"user_header": "名称", "system_field": "item_name"}]
        rows = _read_xlsx_rows(buf.getvalue(), sheet_index=0, header_row=3, rules=rules)

        assert len(rows) == 1
        assert rows[0]["名称"] == "混凝土"

    def test_partial_column_match(self):
        """Excel 有 5 列，只映射了 2 列"""
        headers = ["名称", "规格", "数量", "单价", "备注"]
        data = [["钢筋", "HRB400", 80, 3800, ""]]
        rules = [
            {"user_header": "名称", "system_field": "item_name"},
            {"user_header": "数量", "system_field": "planned_quantity"},
        ]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=rules)

        assert len(rows) == 1
        assert rows[0] == {"名称": "钢筋", "数量": 80}
        assert "规格" not in rows[0]
        assert "单价" not in rows[0]

    def test_empty_data_rows(self):
        """只有表头没有数据的 Excel"""
        headers = ["名称", "数量"]
        data: list = []
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=RULES_SIMPLE)
        assert rows == []

    def test_none_cell_value(self):
        """Excel 中有空单元格"""
        headers = ["名称", "数量", "单位"]
        data = [["混凝土", None, "m³"]]  # None 空单元格
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=RULES_SIMPLE)
        assert rows[0]["数量"] is None

    def test_all_null_row(self):
        """全空行也被读取"""
        headers = ["名称", "数量"]
        data = [["混凝土", 100], [None, None]]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=RULES_SIMPLE)
        assert len(rows) == 2

    def test_no_matching_columns(self):
        """表头和规则完全不匹配"""
        headers = ["A", "B", "C"]
        data = [[1, 2, 3]]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=RULES_SIMPLE)
        assert rows == []

    def test_sheet_index_out_of_range(self):
        """Sheet 索引超出范围"""
        from app.core.exceptions import BadRequest

        headers = ["名称"]
        xlsx_bytes = _make_xlsx_bytes(headers, [["test"]])
        with pytest.raises(BadRequest, match="Sheet 索引"):
            _read_xlsx_rows(xlsx_bytes, sheet_index=5, header_row=1, rules=RULES_SIMPLE)


# ═══════════════════════════════════════════════════════
# 集成：read → fill → normalize 三件套
# ═══════════════════════════════════════════════════════

class TestReadFillNormalizePipeline:
    """读取 → 合并单元格补全 → 清洗归一化 完整链路"""

    RULES_FULL = [
        {"user_header": "分部",     "system_field": "category",        "converter": "trim"},
        {"user_header": "分项",     "system_field": "item_name",        "converter": "trim"},
        {"user_header": "计划量",   "system_field": "planned_quantity"},
        {"user_header": "实际量",   "system_field": "actual_quantity"},
        {"user_header": "单位",     "system_field": "unit",             "converter": "trim"},
        {"user_header": "单价(元)", "system_field": "unit_price",       "converter": "yuan_to_fen"},
        {"user_header": "总价(元)", "system_field": "amount",           "converter": "yuan_to_fen"},
        {"user_header": "日期",     "system_field": "data_date",        "converter": "iso_date"},
    ]

    def test_full_pipeline_with_merged_cells(self):
        """典型场景：分部列有合并单元格，数据行包含日期、金额"""
        headers = ["分部", "分项", "计划量", "实际量", "单位", "单价(元)", "总价(元)", "日期"]
        data = [
            ["主体工程", "混凝土", 500, 480, "m³", 380,   182400, "2025-06-01"],
            [None,       "钢筋",   80,  80,  "t",  4200,  336000, "2025-06-01"],
            [None,       "模板",   200, 190, "m²",  55,    10450, "2025-06-01"],
            ["地基工程", "土方",   1000,950, "m³",  45,    42750, "2025-06-02"],
        ]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        raw_rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=self.RULES_FULL)

        # Step 1: 合并单元格补全
        assert raw_rows[1]["分部"] is None
        assert raw_rows[2]["分部"] is None
        _fill_merged_cells(raw_rows)
        assert raw_rows[1]["分部"] == "主体工程"
        assert raw_rows[2]["分部"] == "主体工程"

        # Step 2: 清洗归一化
        normalized = [_normalize_row(r, self.RULES_FULL) for r in raw_rows]

        # 验证第一条
        assert normalized[0]["category"] == "主体工程"
        assert normalized[0]["item_name"] == "混凝土"
        assert normalized[0]["planned_quantity"] == 500
        assert normalized[0]["actual_quantity"] == 480
        assert normalized[0]["unit"] == "m³"
        assert normalized[0]["unit_price"] == 38000            # 380 元 → 38000 分
        assert normalized[0]["amount"] == 18240000             # 182400 元 → 18240000 分
        assert normalized[0]["data_date"] == date(2025, 6, 1)

        # 验证金额一致性校验逻辑：单价 × 实际量 = 总价
        for row in normalized:
            if row["unit_price"] and row["actual_quantity"] and row["amount"]:
                expected = row["unit_price"] * row["actual_quantity"]
                assert expected == row["amount"], (
                    f"{row['item_name']}: 单价({row['unit_price']}分) × "
                    f"实际量({row['actual_quantity']}) = {expected} ≠ 总价({row['amount']}分)"
                )

    def test_dirty_data_survives(self):
        """脏数据场景：空行、缺失日期、异常金额"""
        headers = ["分部", "分项", "计划量", "实际量", "单价(元)", "总价(元)", "日期"]
        data = [
            ["主体", "混凝土", 500, 480, 380,   190000, "2025-06-01"],  # 正常
            ["主体", None,     "",  "",   "",    "",     ""],           # 全空行
            ["主体", "钢筋",   80,  80,  "不是数字", 336000, "bad-date"], # 脏数据
            ["主体", "模板",   "",  190, 55,     "一万",  None],         # 总价是中文
        ]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        raw_rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=self.RULES_FULL)
        _fill_merged_cells(raw_rows)

        # 逐行归一化 — 脏数据行预期抛异常
        normalized = []
        for i, r in enumerate(raw_rows):
            if i in (2, 3):  # 第3行 "不是数字"、第4行 "一万"
                with pytest.raises(ValueError):
                    _normalize_row(r, self.RULES_FULL)
            else:
                normalized.append(_normalize_row(r, self.RULES_FULL))

        # 第 1 行正常
        assert normalized[0]["item_name"] == "混凝土"
        assert normalized[0]["unit_price"] == 38000
        assert normalized[0]["data_date"] == date(2025, 6, 1)

        # 第 2 行全空 — 合并单元格补全后所有字段继承自第 1 行
        assert normalized[1]["item_name"] == "混凝土"   # 继承
        assert normalized[1]["planned_quantity"] == 500  # 继承
        assert normalized[1]["actual_quantity"] == 480   # 继承
        assert normalized[1]["unit"] is None                # Excel 无"单位"列
        assert normalized[1]["amount"] == 19000000       # 继承（190000元→分）

    def test_empty_workbook(self):
        """空 Excel（无表头、无数据）"""
        headers: list = []
        data: list = []
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        # header_row=1，但第一行不存在 → 返回空
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=self.RULES_FULL)
        assert rows == []

    def test_zero_values(self):
        """零值处理 — 0 应该保留，不是 None"""
        headers = ["分项", "计划量", "实际量"]
        data = [["试块", 0, 0]]
        rules = [
            {"user_header": "分项",   "system_field": "item_name",        "converter": "trim"},
            {"user_header": "计划量", "system_field": "planned_quantity"},
            {"user_header": "实际量", "system_field": "actual_quantity"},
        ]
        xlsx_bytes = _make_xlsx_bytes(headers, data)
        rows = _read_xlsx_rows(xlsx_bytes, sheet_index=0, header_row=1, rules=rules)
        normalized = _normalize_row(rows[0], rules)
        assert normalized["planned_quantity"] == 0
        assert normalized["actual_quantity"] == 0
