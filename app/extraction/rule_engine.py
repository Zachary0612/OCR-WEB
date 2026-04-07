"""
规则引擎 — 基于正则/关键词的字段提取

从 excel_export.py 中提取的纯业务逻辑，不包含 Excel I/O。
现有代码通过 excel_export.extract_fields() 调用此处逻辑。
"""
from typing import Any


def extract_fields_by_rules(
    filename: str,
    full_text: str,
    result_json: Any,
    page_count: int,
) -> dict[str, str]:
    """
    使用规则引擎从 OCR 结果中提取归档字段

    Returns:
        {"档号": "...", "文号": "...", "责任者": "...", ...}
    """
    # 委托到现有实现（保持兼容）
    from app.services.excel_export import extract_fields
    return extract_fields(filename, full_text, result_json, page_count)
