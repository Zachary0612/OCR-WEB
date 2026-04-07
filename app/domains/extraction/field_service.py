"""Field extraction domain operations."""

from __future__ import annotations

from app.services import excel_export as legacy_excel_export
from app.services import llm_field_extraction_service as legacy_llm_extraction
from app.shared.contracts import FieldExtractionResult


def extract_fields(filename: str, full_text: str, result_json, page_count: int) -> dict[str, str]:
    raw_fields = legacy_excel_export.extract_fields(filename, full_text, result_json, page_count)
    return {str(key): str(value or "") for key, value in (raw_fields or {}).items()}


def build_field_extraction_result(fields: dict[str, str]) -> FieldExtractionResult:
    review_recommendation = {
        key: "review" if not str(value or "").strip() else "accepted"
        for key, value in fields.items()
    }
    return FieldExtractionResult(
        fields=fields,
        confidence={},
        review_recommendation=review_recommendation,
    )


async def compare_rule_and_llm_fields(task, *, include_evidence: bool = True) -> dict:
    return await legacy_llm_extraction.compare_rule_and_llm_fields(task, include_evidence=include_evidence)


__all__ = ["build_field_extraction_result", "compare_rule_and_llm_fields", "extract_fields"]
