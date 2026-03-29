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
    mode: Mapped[str] = mapped_column(String(20), default="layout")  # vl/layout/ocr
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


class ArchiveRecord(Base):
    __tablename__ = "archive_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)           # 关联 ocr_tasks.id，外部导入时为 NULL
    batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True)      # 批次标识，前端生成
    batch_folder: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 源文件夹路径
    archive_no: Mapped[str | None] = mapped_column(String(200), nullable=True)    # 档号
    doc_no: Mapped[str | None] = mapped_column(String(200), nullable=True)        # 文号
    responsible: Mapped[str | None] = mapped_column(String(500), nullable=True)   # 责任者
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)        # 题名
    date: Mapped[str | None] = mapped_column(String(50), nullable=True)           # 日期
    pages: Mapped[str | None] = mapped_column(String(20), nullable=True)          # 页数
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True) # 密级
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)      # 备注
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
