"""数据转换器注册表

内置转换器用于清洗流水线中的归一化步骤。
所有转换器签名：Callable[[Any], Any]
"""

from __future__ import annotations

import re
from datetime import date, datetime


# ═══════════════════════════════════════════════════
# 金额转换
# ═══════════════════════════════════════════════════

def yuan_to_fen(value: str | float | int) -> int:
    """元 → 分（乘以 100，取整）。"""
    return int(float(str(value).replace(",", "").replace("，", "")) * 100)


def wan_yuan_to_fen(value: str | float | int) -> int:
    """万元 → 分（乘以 10000 × 100 取整）。"""
    return int(float(str(value).replace(",", "").replace("，", "")) * 10000 * 100)


def fen_to_yuan(value: int) -> float:
    """分 → 元（除以 100），供展示使用。"""
    return value / 100


# ═══════════════════════════════════════════════════
# 日期转换
# ═══════════════════════════════════════════════════

_CHINESE_DATE_RE = re.compile(
    r"(?P<year>\d{4})\s*[年/\-]\s*(?P<month>\d{1,2})\s*[月/\-]\s*(?P<day>\d{1,2})\s*日?"
)
_ISO_DATE_RE = re.compile(r"(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})")


def chinese_date_to_iso(value: str) -> date | None:
    """中文日期 → ISO date: '2024年12月31日' → date(2024,12,31)。"""
    m = _CHINESE_DATE_RE.search(str(value).strip())
    if not m:
        return None
    return date(int(m["year"]), int(m["month"]), int(m["day"]))


def iso_date(value: str) -> date | None:
    """YYYY-MM-DD 或 YYYY/MM/DD → date。"""
    m = _ISO_DATE_RE.search(str(value).strip())
    if not m:
        return None
    return date(int(m["year"]), int(m["month"]), int(m["day"]))


def excel_serial_to_date(value: int | float) -> date | None:
    """Excel 日期序列号 → date。

    Excel 的日期以 1899-12-30 为第 0 天（Windows 下的 Excel 默认）。
    """
    from datetime import timedelta

    try:
        days = int(float(value))
        # Excel epoch: 1899-12-30
        base = date(1899, 12, 30)
        return base + timedelta(days=days)
    except (TypeError, ValueError):
        return None


# ═══════════════════════════════════════════════════
# 字符串清洗
# ═══════════════════════════════════════════════════

def normalize_whitespace(value: str) -> str:
    """规范化空白字符：多空格合并、去除首尾空白。"""
    return " ".join(str(value).split())


def trim(value: str) -> str:
    return str(value).strip()


def lowercase(value: str) -> str:
    return str(value).strip().lower()


# ═══════════════════════════════════════════════════
# 别名映射（施工类别的常见别名 → 规范名）
# ═══════════════════════════════════════════════════

# 预留：后续从 t_category_dict 或配置文件加载
CATEGORY_ALIASES: dict[str, str] = {
    "混凝土": "混凝土",
    "砼": "混凝土",
    "c30": "混凝土",
    "c35": "混凝土",
    "商混": "混凝土",
    "钢筋": "钢筋",
    "钢肋": "钢筋",
    "模板": "模板工程",
    "支模": "模板工程",
    "土方": "土方工程",
    "挖土": "土方工程",
    "回填": "土方工程",
}


def category_alias_to_canonical(value: str) -> str:
    """施工类别别名 → 规范名。"""
    key = str(value).strip().lower()
    return CATEGORY_ALIASES.get(key, value)


# ═══════════════════════════════════════════════════
# 单位转换
# ═══════════════════════════════════════════════════

# 主单位换算系数（目标单位 = 源值 × 系数）
UNIT_CONVERSIONS: dict[str, float] = {
    "吨": 1.0,
    "t": 1.0,
    "千克": 0.001,
    "kg": 0.001,
    "克": 1e-6,
    "g": 1e-6,
    "立方米": 1.0,
    "m³": 1.0,
    "m3": 1.0,
    "升": 0.001,
    "l": 0.001,
    "平方米": 1.0,
    "m²": 1.0,
    "m2": 1.0,
    "米": 1.0,
    "m": 1.0,
    "厘米": 0.01,
    "cm": 0.01,
    "毫米": 0.001,
    "mm": 0.001,
    "万元": 10000,
}


def decimal_to_base_unit(value: float, from_unit: str) -> float:
    """将工程量的值从 from_unit 换算到主单位。

    Args:
        value: 原始数值
        from_unit: 原始单位（如 '千克', 'kg'）
    Returns:
        换算为主单位后的数值
    """
    unit_key = str(from_unit).strip().lower()
    factor = UNIT_CONVERSIONS.get(unit_key, 1.0)
    return float(value) * factor


# ═══════════════════════════════════════════════════
# 转换器注册表
# ═══════════════════════════════════════════════════

CONVERTER_REGISTRY: dict[str, object] = {
    # 金额
    "yuan_to_fen": yuan_to_fen,
    "wan_yuan_to_fen": wan_yuan_to_fen,
    # 日期
    "chinese_date_to_iso": chinese_date_to_iso,
    "excel_serial_to_date": excel_serial_to_date,
    "iso_date": iso_date,
    # 字符串
    "trim": trim,
    "lowercase": lowercase,
    "normalize_whitespace": normalize_whitespace,
    # 别名
    "category_alias_to_canonical": category_alias_to_canonical,
    # 单位
    "decimal_to_base_unit": decimal_to_base_unit,
}


def apply_converter(value: object, converter_name: str) -> object:
    """按名称调用转换器。"""
    converter = CONVERTER_REGISTRY.get(converter_name)
    if converter is None:
        raise ValueError(f"未注册的转换器: {converter_name}")
    # 支持 "decimal_to_base_unit:ton" 语法
    if converter_name.startswith("decimal_to_base_unit:"):
        unit = converter_name.split(":", 1)[1]
        return decimal_to_base_unit(float(str(value)), unit)
    fn = converter
    if callable(fn):
        return fn(value)
    return value
