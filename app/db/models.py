from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
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


class BatchTruthTaskMap(Base):
    __tablename__ = "batch_truth_task_map"
    __table_args__ = (UniqueConstraint("batch_id", "task_id", name="uq_batch_truth_task_map_batch_task"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False)
    doc_key: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class BatchTruthDocumentField(Base):
    __tablename__ = "batch_truth_document_fields"
    __table_args__ = (UniqueConstraint("batch_id", "doc_key", name="uq_batch_truth_document_fields_batch_doc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False)
    doc_key: Mapped[str] = mapped_column(String(120), nullable=False)
    archive_no: Mapped[str | None] = mapped_column(String(200), nullable=True)
    doc_no: Mapped[str | None] = mapped_column(String(200), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pages: Mapped[str | None] = mapped_column(String(20), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class BatchQARecord(Base):
    __tablename__ = "batch_qa_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="minimax")
    model: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    raw_usage: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    support_level: Mapped[str] = mapped_column(String(20), nullable=False, default="insufficient")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citations_json: Mapped[list | dict] = mapped_column(JSONB, nullable=False, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class BatchQAFeedback(Base):
    __tablename__ = "batch_qa_feedback"
    __table_args__ = (
        UniqueConstraint("batch_id", "qa_record_id", name="uq_batch_qa_feedback_batch_qa"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(100), nullable=False)
    qa_record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)  # helpful / not_helpful
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_evidence_json: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
