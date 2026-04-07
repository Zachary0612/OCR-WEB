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


class TaskProgressRequest(BaseModel):
    task_ids: list[int] = Field(default_factory=list)


class TaskProgressItem(BaseModel):
    id: int
    status: str
    error_message: str | None = None


class TaskProgressResponse(BaseModel):
    total: int
    done_count: int
    failed_count: int
    processing_count: int
    pending_count: int
    tasks: list[TaskProgressItem]
