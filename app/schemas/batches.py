from typing import Any

from pydantic import BaseModel


class AIExtractFieldsRequest(BaseModel):
    persist: bool = False
    include_evidence: bool = True


class AIFieldConflict(BaseModel):
    rule: str
    llm: str
    evidence: str | None = None


class AIFieldAgreement(BaseModel):
    matched: int
    total: int
    ratio: float
    matched_fields: list[str]
    mismatch_fields: list[str]


class AIExtractFieldsResponse(BaseModel):
    task_id: int
    rule_fields: dict[str, Any]
    llm_fields: dict[str, Any]
    recommended_fields: dict[str, str]
    conflicts: dict[str, AIFieldConflict]
    agreement: AIFieldAgreement
    provider: str
    model: str
    raw_usage: dict[str, Any]


class AIBatchMergeExtractRequest(BaseModel):
    persist: bool = False
    include_evidence: bool = True
    force_refresh: bool = False


class AIBatchSkippedTask(BaseModel):
    task_id: int
    filename: str
    status: str
    reason: str


class AIBatchGroup(BaseModel):
    group_id: str
    task_ids: list[int]
    filenames: list[str]
    same_document_confidence: float
    decision_reasons: list[str]


class AIBatchDocument(BaseModel):
    group_id: str
    merged_page_count: int
    rule_fields: dict[str, Any]
    llm_fields: dict[str, Any]
    recommended_fields: dict[str, str]
    conflicts: dict[str, AIFieldConflict]
    agreement: AIFieldAgreement


class AIBatchSummary(BaseModel):
    total_tasks: int
    done_tasks: int
    eligible_tasks: int
    skipped_tasks: list[AIBatchSkippedTask]
    groups_count: int
    documents_count: int


class AIBatchMergeExtractResponse(BaseModel):
    batch_id: str
    groups: list[AIBatchGroup]
    documents: list[AIBatchDocument]
    provider: str
    model: str
    raw_usage: dict[str, Any]
    summary: AIBatchSummary
    generated_at: str | None = None
