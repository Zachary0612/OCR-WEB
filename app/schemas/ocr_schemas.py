from datetime import datetime
from typing import Any
from pydantic import BaseModel


class OCRTaskOut(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    page_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OCRTaskDetail(OCRTaskOut):
    full_text: str | None = None
    result_json: Any = None

    model_config = {"from_attributes": True}


class OCRTaskList(BaseModel):
    total: int
    tasks: list[OCRTaskOut]
