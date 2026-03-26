from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OCRTask(Base):
    __tablename__ = "ocr_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/processing/done/failed
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # OCR 结果 JSON
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
