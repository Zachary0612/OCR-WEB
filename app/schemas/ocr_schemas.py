from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.core.result_validation import normalize_result_pages


class OCRTaskOut(BaseModel):
    id: int
    filename: str

    file_path: str | None = None
    file_type: str
    mode: str = "layout"
    status: str
    page_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OCRTaskDetail(OCRTaskOut):
    full_text: str | None = None
    result_json: Any = None
    result_data: Any = None  # structured: {"pages": [...]}

    model_config = {"from_attributes": True}

    def model_post_init(self, __context):
        raw_pages = None
        if self.result_data and isinstance(self.result_data, dict) and self.result_data.get("pages"):
            raw_pages = self.result_data.get("pages")
        elif self.result_json:
            raw_pages = self.result_json

        if not raw_pages:
            return

        try:
            pages = normalize_result_pages(raw_pages)
        except Exception:
            pages = raw_pages if isinstance(raw_pages, list) else [raw_pages]

        self.result_json = pages
        self.result_data = {"pages": pages}


class OCRTaskList(BaseModel):
    total: int
    tasks: list[OCRTaskOut]


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


class BatchEvaluationTruthTaskItem(BaseModel):
    task_id: int
    doc_key: str


class BatchEvaluationTruthDocumentItem(BaseModel):
    doc_key: str
    fields: dict[str, str]


class BatchEvaluationTruthGetResponse(BaseModel):
    batch_id: str
    tasks: list[BatchEvaluationTruthTaskItem]
    documents: list[BatchEvaluationTruthDocumentItem]
    truth_updated_at: str | None = None


class BatchEvaluationTruthPutRequest(BaseModel):
    tasks: list[BatchEvaluationTruthTaskItem] = Field(default_factory=list)
    documents: list[BatchEvaluationTruthDocumentItem] = Field(default_factory=list)


class BatchEvaluationMetricsResponse(BaseModel):
    batch_id: str
    operational_metrics: dict[str, Any]
    truth_metrics: dict[str, Any] | None = None
    compare_targets: list[str]
    generated_at: str | None = None
    truth_updated_at: str | None = None


class BatchEvaluationAiReportResponse(BaseModel):
    batch_id: str
    summary: str
    strengths: list[str]
    risks: list[str]
    recommendations: list[str]
    provider: str
    model: str
    generated_at: str | None = None
    raw_usage: dict[str, Any]


class BatchQARequest(BaseModel):
    question: str
    top_k: int = Field(default=6, ge=1, le=10)


class BatchQAEvidenceItem(BaseModel):
    task_id: int
    filename: str
    snippet: str
    score: float


class BatchQAResponse(BaseModel):
    batch_id: str
    question: str
    answer: str
    evidence: list[BatchQAEvidenceItem]
    provider: str
    model: str
    raw_usage: dict[str, Any]
    generated_at: str | None = None
