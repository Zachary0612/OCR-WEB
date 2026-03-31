import re
from collections import defaultdict
from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_cache import cache_get, cache_set
from app.db.models import ArchiveRecord, OCRTask
from app.services.excel_export import extract_fields
from app.services.llm_field_extraction_service import (
    call_minimax_same_document_judgement,
    compare_rule_and_llm_fields_for_content,
)


SAME_DOCUMENT_CONFIDENCE_THRESHOLD = 0.90
TITLE_STRONG_MATCH_THRESHOLD = 0.97
TITLE_HINT_THRESHOLD = 0.62
FILENAME_HINT_THRESHOLD = 0.78
MISSING_TEXT_REASON = "Task full_text is empty."
NOT_DONE_REASON = "Task is not finished yet."
MERGE_CACHE_PREFIX = "batch_ai_merge:"
MERGE_CACHE_TTL = 1800

_PUNCT_PATTERN = re.compile(r"[\s,.;:!?\-_/\\，。；：！？（）()《》【】\[\]]+")
_FILENAME_SEQ_PATTERNS = [
    re.compile(r"第\s*(\d+)\s*(?:册|卷|部分|篇)"),
    re.compile(r"(?:part|vol|volume|册|卷|p)[\s_-]*(\d+)", re.IGNORECASE),
    re.compile(r"(?:^|[_\-\s])(\d{1,4})(?:$|[_\-\s])"),
]


@dataclass(slots=True)
class TaskCandidate:
    task: OCRTask
    rule_fields: dict[str, str]
    title_norm: str
    doc_no_norm: str
    doc_no_prefix: str
    responsible_norm: str
    date_norm: str
    filename_norm: str
    sequence: int | None


@dataclass(slots=True)
class PositiveEdge:
    left_id: int
    right_id: int
    confidence: float
    reason: str


class _UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, index: int) -> int:
        if self.parent[index] != index:
            self.parent[index] = self.find(self.parent[index])
        return self.parent[index]

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            self.parent[root_left] = root_right
            return
        if self.rank[root_left] > self.rank[root_right]:
            self.parent[root_right] = root_left
            return
        self.parent[root_right] = root_left
        self.rank[root_left] += 1


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_text(value: Any) -> str:
    return _PUNCT_PATTERN.sub("", _coerce_text(value)).lower()


def _normalize_doc_no_prefix(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\d+", "", value)[:12]


def _extract_filename_sequence(filename: str) -> int | None:
    stem = Path(filename or "").stem
    if not stem:
        return None
    for pattern in _FILENAME_SEQ_PATTERNS:
        match = pattern.search(stem)
        if not match:
            continue
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            continue
    return None


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(a=left, b=right).ratio()


def _filename_sort_key(candidate: TaskCandidate) -> tuple[int, datetime, int]:
    sequence = candidate.sequence if candidate.sequence is not None else 10**9
    created_at = candidate.task.created_at or datetime.min
    return sequence, created_at, candidate.task.id


def _merge_usage(total: dict[str, Any], usage: dict[str, Any]) -> None:
    for key, value in (usage or {}).items():
        if isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value
            continue
        if key not in total:
            total[key] = value


def _merge_cache_key(batch_id: str) -> str:
    return f"{MERGE_CACHE_PREFIX}{batch_id}"


def _strip_evidence_in_result(payload: dict[str, Any]) -> None:
    for document in payload.get("documents", []):
        llm_fields = document.get("llm_fields")
        if isinstance(llm_fields, dict):
            llm_fields.pop("evidence", None)


async def _load_batch_tasks(db: AsyncSession, batch_id: str) -> list[OCRTask]:
    stmt = (
        select(OCRTask)
        .join(ArchiveRecord, ArchiveRecord.task_id == OCRTask.id)
        .where(ArchiveRecord.batch_id == batch_id)
        .order_by(OCRTask.created_at.asc(), OCRTask.id.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    unique_tasks: list[OCRTask] = []
    seen: set[int] = set()
    for task in rows:
        if task.id in seen:
            continue
        seen.add(task.id)
        unique_tasks.append(task)
    return unique_tasks


def _build_task_candidate(task: OCRTask) -> TaskCandidate:
    fields = extract_fields(task.filename, task.full_text or "", task.result_json, task.page_count)
    title = _normalize_text(fields.get("题名", ""))
    doc_no = _normalize_text(fields.get("文号", ""))
    responsible = _normalize_text(fields.get("责任者", ""))
    date = _normalize_text(fields.get("日期", ""))
    filename_norm = _normalize_text(Path(task.filename or "").stem)
    return TaskCandidate(
        task=task,
        rule_fields=fields,
        title_norm=title,
        doc_no_norm=doc_no,
        doc_no_prefix=_normalize_doc_no_prefix(doc_no),
        responsible_norm=responsible,
        date_norm=date,
        filename_norm=filename_norm,
        sequence=_extract_filename_sequence(task.filename),
    )


def _rule_decision(left: TaskCandidate, right: TaskCandidate) -> tuple[bool | None, float, str]:
    if left.doc_no_norm and right.doc_no_norm:
        if left.doc_no_norm == right.doc_no_norm:
            return True, 1.0, "文号完全一致。"
        return False, 0.0, "文号不一致。"

    title_similarity = _similarity(left.title_norm, right.title_norm)
    filename_similarity = _similarity(left.filename_norm, right.filename_norm)
    same_date = bool(left.date_norm and right.date_norm and left.date_norm == right.date_norm)
    same_responsible = bool(
        left.responsible_norm and right.responsible_norm and left.responsible_norm == right.responsible_norm
    )

    if left.title_norm and right.title_norm and title_similarity >= TITLE_STRONG_MATCH_THRESHOLD:
        if same_date:
            return True, 0.97, "题名高度一致且日期一致。"
        if same_responsible:
            return True, 0.94, "题名高度一致且责任者一致。"

    if left.title_norm and right.title_norm and title_similarity <= 0.35 and left.date_norm and right.date_norm:
        if left.date_norm != right.date_norm:
            return False, 0.0, "题名差异较大且日期不一致。"

    hints: list[str] = []
    if title_similarity >= TITLE_HINT_THRESHOLD:
        hints.append("题名相似")
    if filename_similarity >= FILENAME_HINT_THRESHOLD:
        hints.append("文件名相似")
    if same_date:
        hints.append("日期一致")
    if same_responsible:
        hints.append("责任者一致")
    if left.doc_no_prefix and right.doc_no_prefix and left.doc_no_prefix == right.doc_no_prefix:
        hints.append("文号前缀一致")

    if hints:
        return None, 0.0, f"规则存在不确定信号：{'、'.join(hints)}。"
    return False, 0.0, "缺少可支持同文档的规则信号。"


def _collect_group_edges(group_ids: set[int], edges: list[PositiveEdge]) -> list[PositiveEdge]:
    return [
        edge
        for edge in edges
        if edge.left_id in group_ids and edge.right_id in group_ids
    ]


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for reason in reasons:
        if not reason or reason in seen:
            continue
        seen.add(reason)
        result.append(reason)
    return result


def _build_merged_text(candidates: list[TaskCandidate]) -> tuple[str, int, list[dict[str, Any]]]:
    parts: list[str] = []
    merged_pages: list[dict[str, Any]] = []
    page_count = 0

    for candidate in candidates:
        task = candidate.task
        parts.append(
            "\n".join(
                [
                    f"--- 文件片段开始: {task.filename} (task_id={task.id}) ---",
                    task.full_text or "",
                    f"--- 文件片段结束: {task.filename} (task_id={task.id}) ---",
                ]
            )
        )
        page_count += max(task.page_count or 0, 0)

        result_json = task.result_json
        if isinstance(result_json, list):
            merged_pages.extend(page for page in result_json if isinstance(page, dict))
        elif isinstance(result_json, dict):
            merged_pages.append(result_json)

    return "\n\n".join(parts), page_count, merged_pages


async def batch_merge_extract_fields(
    db: AsyncSession,
    *,
    batch_id: str,
    include_evidence: bool = True,
) -> dict[str, Any] | None:
    tasks = await _load_batch_tasks(db, batch_id)
    if not tasks:
        return None

    skipped_tasks: list[dict[str, Any]] = []
    eligible_tasks: list[OCRTask] = []
    done_tasks = 0
    for task in tasks:
        if task.status == "done":
            done_tasks += 1
        if task.status != "done":
            skipped_tasks.append(
                {
                    "task_id": task.id,
                    "filename": task.filename,
                    "status": task.status,
                    "reason": NOT_DONE_REASON,
                }
            )
            continue
        if not _coerce_text(task.full_text):
            skipped_tasks.append(
                {
                    "task_id": task.id,
                    "filename": task.filename,
                    "status": task.status,
                    "reason": MISSING_TEXT_REASON,
                }
            )
            continue
        eligible_tasks.append(task)

    if not eligible_tasks:
        return None

    candidates = [_build_task_candidate(task) for task in eligible_tasks]
    union_find = _UnionFind(len(candidates))
    positive_edges: list[PositiveEdge] = []
    raw_usage: dict[str, Any] = {}
    provider = "minimax"
    model = ""

    for left_index in range(len(candidates)):
        for right_index in range(left_index + 1, len(candidates)):
            left = candidates[left_index]
            right = candidates[right_index]
            merge, confidence, reason = _rule_decision(left, right)
            if merge is True:
                union_find.union(left_index, right_index)
                positive_edges.append(
                    PositiveEdge(
                        left_id=left.task.id,
                        right_id=right.task.id,
                        confidence=confidence,
                        reason=reason,
                    )
                )
                continue
            if merge is False:
                continue

            llm_decision = await call_minimax_same_document_judgement(
                left_filename=left.task.filename,
                left_page_count=left.task.page_count,
                left_full_text=left.task.full_text or "",
                left_rule_fields=left.rule_fields,
                right_filename=right.task.filename,
                right_page_count=right.task.page_count,
                right_full_text=right.task.full_text or "",
                right_rule_fields=right.rule_fields,
            )
            _merge_usage(raw_usage, llm_decision.get("raw_usage", {}))
            provider = llm_decision.get("provider") or provider
            model = model or (llm_decision.get("model") or "")

            if llm_decision.get("same_document") and llm_decision.get("confidence", 0) >= SAME_DOCUMENT_CONFIDENCE_THRESHOLD:
                union_find.union(left_index, right_index)
                evidence = _coerce_text(llm_decision.get("evidence"))
                llm_reason = f"LLM高置信判定同文档（{llm_decision.get('confidence', 0):.2f}）。"
                if evidence:
                    llm_reason = f"{llm_reason} 证据：{evidence}"
                positive_edges.append(
                    PositiveEdge(
                        left_id=left.task.id,
                        right_id=right.task.id,
                        confidence=float(llm_decision.get("confidence", 0)),
                        reason=f"{reason} {llm_reason}".strip(),
                    )
                )

    grouped_indexes: dict[int, list[int]] = defaultdict(list)
    for index in range(len(candidates)):
        grouped_indexes[union_find.find(index)].append(index)

    groups_payload: list[dict[str, Any]] = []
    documents_payload: list[dict[str, Any]] = []
    group_members: dict[str, list[TaskCandidate]] = {}

    ordered_group_indexes = sorted(
        grouped_indexes.values(),
        key=lambda members: min(candidates[index].task.created_at or datetime.min for index in members),
    )

    for group_number, member_indexes in enumerate(ordered_group_indexes, start=1):
        members = sorted((candidates[index] for index in member_indexes), key=_filename_sort_key)
        group_id = f"group-{group_number}"
        group_members[group_id] = members
        member_task_ids = [member.task.id for member in members]
        member_filenames = [member.task.filename for member in members]
        edge_candidates = _collect_group_edges(set(member_task_ids), positive_edges)
        if edge_candidates:
            confidence = min(edge.confidence for edge in edge_candidates)
            reasons = _dedupe_reasons([edge.reason for edge in edge_candidates])
        else:
            confidence = 1.0
            reasons = ["单文件组，无需合并判定。"]

        groups_payload.append(
            {
                "group_id": group_id,
                "task_ids": member_task_ids,
                "filenames": member_filenames,
                "same_document_confidence": round(float(confidence), 4),
                "decision_reasons": reasons,
            }
        )

    for group in groups_payload:
        members = group_members[group["group_id"]]
        merged_text, merged_page_count, merged_pages = _build_merged_text(members)
        if merged_page_count <= 0:
            merged_page_count = len(merged_pages)
        merged_filename = (
            members[0].task.filename
            if len(members) == 1
            else f"{Path(members[0].task.filename).stem}_merged_{len(members)}"
        )
        comparison = await compare_rule_and_llm_fields_for_content(
            filename=merged_filename,
            page_count=merged_page_count,
            full_text=merged_text,
            result_json=merged_pages,
            include_evidence=include_evidence,
        )
        _merge_usage(raw_usage, comparison.get("raw_usage", {}))
        provider = comparison.get("provider") or provider
        model = model or (comparison.get("model") or "")
        documents_payload.append(
            {
                "group_id": group["group_id"],
                "merged_page_count": merged_page_count,
                "rule_fields": comparison["rule_fields"],
                "llm_fields": comparison["llm_fields"],
                "recommended_fields": comparison["recommended_fields"],
                "conflicts": comparison["conflicts"],
                "agreement": comparison["agreement"],
            }
        )

    return {
        "batch_id": batch_id,
        "groups": groups_payload,
        "documents": documents_payload,
        "provider": provider,
        "model": model,
        "raw_usage": raw_usage,
        "summary": {
            "total_tasks": len(tasks),
            "done_tasks": done_tasks,
            "eligible_tasks": len(eligible_tasks),
            "skipped_tasks": skipped_tasks,
            "groups_count": len(groups_payload),
            "documents_count": len(documents_payload),
        },
    }


async def get_batch_merge_extract_result(
    db: AsyncSession,
    *,
    batch_id: str,
    include_evidence: bool = True,
    force_refresh: bool = False,
) -> dict[str, Any] | None:
    cache_key = _merge_cache_key(batch_id)
    if not force_refresh:
        cached = cache_get(cache_key)
        if isinstance(cached, dict):
            payload = deepcopy(cached)
            if not include_evidence:
                _strip_evidence_in_result(payload)
            return payload

    computed = await batch_merge_extract_fields(
        db,
        batch_id=batch_id,
        include_evidence=True,
    )
    if not computed:
        return None

    computed["generated_at"] = datetime.now(timezone.utc).isoformat()
    cache_set(cache_key, computed, MERGE_CACHE_TTL)
    payload = deepcopy(computed)
    if not include_evidence:
        _strip_evidence_in_result(payload)
    return payload
