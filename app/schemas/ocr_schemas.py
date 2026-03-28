from datetime import datetime
from typing import Any
from pydantic import BaseModel


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
        # Build result_data from result_json for Vue frontend
        if self.result_data is None and self.result_json:
            pages = self.result_json if isinstance(self.result_json, list) else [self.result_json]
            self.result_data = {"pages": pages}


class OCRTaskList(BaseModel):
    total: int
    tasks: list[OCRTaskOut]
