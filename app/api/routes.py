import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, or_, select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_auth
from app.core.path_security import PathSecurityError, ensure_allowed_path
from app.core.preview import build_thumbnail
from app.core.redis_cache import (
    LIST_TTL,
    SEARCH_TTL,
    TASK_TTL,
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    invalidate_lists,
    invalidate_task,
)
from app.core.result_validation import ResultValidationError, normalize_result_pages, serialize_pages_text
from app.db.database import get_db
from app.db.models import ArchiveRecord, OCRTask
from app.schemas.ocr_schemas import (
    AIBatchMergeExtractRequest,
    AIBatchMergeExtractResponse,
    AIExtractFieldsRequest,
    AIExtractFieldsResponse,
    BatchQAFeedbackRequest,
    BatchQAFeedbackResponse,
    BatchQAHistoryResponse,
    BatchQAMetricsResponse,
    BatchQARequest,
    BatchQAResponse,
    BatchEvaluationAiReportResponse,
    BatchEvaluationMetricsResponse,
    BatchEvaluationTruthGetResponse,
    BatchEvaluationTruthPutRequest,
    OCRTaskDetail,
    OCRTaskList,
    OCRTaskOut,
)
from app.services.batch_evaluation_service import (
    get_batch_evaluation_ai_report,
    get_batch_evaluation_metrics,
    get_batch_evaluation_truth,
    save_batch_evaluation_truth,
)
from app.services.batch_qa_service import (
    answer_batch_question,
    get_batch_qa_history,
    get_batch_qa_metrics,
    submit_batch_qa_feedback,
)
from app.services.batch_merge_extraction_service import get_batch_merge_extract_result
from app.services.archive_service import get_archive_records, import_from_excel, records_to_excel
from app.services.archive_service import save_archive_record
from app.services.excel_export import extract_fields
from app.services.llm_field_extraction_service import MiniMaxServiceError, compare_rule_and_llm_fields
from app.services.ocr_service import (
    create_task,
    delete_task,
    delete_tasks_by_folder,
    get_task_detail,
    get_task_list,
    save_upload_file,
    search_tasks,
)
from app.services.task_queue import OCRJob, enqueue_task
from config import MAX_FILE_SIZE


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/ocr",
    tags=["OCR"],
    dependencies=[Depends(require_auth)],
)
TERMINAL_STATUSES = {"done", "failed"}


def _task_payload(task: OCRTask) -> dict:
    return OCRTaskDetail.model_validate(task).model_dump(mode="json")


def _extract_snippet(task: OCRTask, keyword: str, context: int = 50) -> str:
    lowered = keyword.lower()

    if task.full_text and lowered in task.full_text.lower():
        return _cut_around(task.full_text, lowered, context)

    if task.result_json:
        pages = task.result_json if isinstance(task.result_json, list) else [task.result_json]
        for page in pages:
            if not isinstance(page, dict):
                continue
            for region in page.get("regions", []):
                content = str(region.get("content", "") or "")
                if lowered in content.lower():
                    return _cut_around(content, lowered, context)
            for line in page.get("lines", []):
                text = str(line.get("text", "") or "")
                if lowered in text.lower():
                    return _cut_around(text, lowered, context)

    if lowered in (task.filename or "").lower():
        return f"Filename match: {task.filename}"

    return ""


def _cut_around(text: str, keyword: str, context: int = 50) -> str:
    index = text.lower().index(keyword)
    start = max(0, index - context)
    end = min(len(text), index + len(keyword) + context)
    snippet = text[start:end].replace("\n", " ")
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def _raise_bad_request(error: Exception) -> None:
    if isinstance(error, PathSecurityError):
        status_code = status.HTTP_403_FORBIDDEN if "outside allowed roots" in str(error) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(error)) from error
    if isinstance(error, ResultValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    if isinstance(error, MiniMaxServiceError):
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    raise error


@router.post("/upload", response_model=OCRTaskDetail, status_code=status.HTTP_202_ACCEPTED)
async def upload_and_enqueue(
    file: UploadFile = File(...),
    relative_path: str = Form(""),
    mode: str = Query("vl", pattern="^(vl|layout|ocr)$"),
    excel_path: str = Query(""),
    excel_init: int = Query(0),
    output_dir: str = Query(""),
    batch_id: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE // 1024 // 1024}MB.")

    try:
        file_path, file_type = await save_upload_file(file.filename, content, relative_path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    task = await create_task(db, file.filename, file_path, file_type, mode=mode)
    await enqueue_task(
        OCRJob(
            task_id=task.id,
            mode=mode,
            excel_path=excel_path,
            excel_init=excel_init,
            output_dir=output_dir,
            batch_id=batch_id,
        )
    )
    invalidate_lists()
    return _task_payload(task)


@router.get("/scan-folder")
async def scan_folder(path: str = Query(..., description="Absolute path under an allowed root.")):
    try:
        folder = ensure_allowed_path(path, expect_dir=True)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    files = []
    for root, directories, filenames in os.walk(folder):
        directories.sort()
        for filename in sorted(filenames):
            full_path = Path(root) / filename
            extension = full_path.suffix.lower()
            if extension not in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"}:
                continue
            files.append(
                {
                    "name": filename,
                    "path": str(full_path),
                    "rel_path": str(full_path.relative_to(folder)),
                    "size": full_path.stat().st_size,
                }
            )

    return {"folder": str(folder), "count": len(files), "files": files}


@router.post("/upload-from-path", response_model=OCRTaskDetail, status_code=status.HTTP_202_ACCEPTED)
async def upload_from_path(
    body: dict,
    mode: str = Query("vl", pattern="^(vl|layout|ocr)$"),
    excel_path: str = Query(""),
    excel_init: int = Query(0),
    output_dir: str = Query(""),
    batch_id: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    try:
        file_path = ensure_allowed_path(body.get("file_path", ""), expect_file=True)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    file_type = file_path.suffix.lower()
    if file_type not in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")

    task = await create_task(db, file_path.name, str(file_path), file_type, mode=mode)
    await enqueue_task(
        OCRJob(
            task_id=task.id,
            mode=mode,
            excel_path=excel_path,
            excel_init=excel_init,
            output_dir=output_dir,
            batch_id=batch_id,
        )
    )
    invalidate_lists()
    return _task_payload(task)


@router.get("/archive-records/export")
async def export_archive_records(
    folder: str = Query(""),
    batch_id: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    records, _ = await get_archive_records(db, folder=folder, batch_id=batch_id, page=1, page_size=10000)
    if not records:
        raise HTTPException(status_code=404, detail="No archive records found.")

    file_descriptor, temp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(file_descriptor)
    try:
        records_to_excel(list(records), temp_path)
        return FileResponse(
            temp_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="archive_records.xlsx",
        )
    except Exception as error:  # noqa: BLE001
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Export failed: {error}") from error


@router.get("/archive-records")
async def list_archive_records(
    folder: str = Query(""),
    batch_id: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    records, total = await get_archive_records(db, folder=folder, batch_id=batch_id, page=page, page_size=page_size)
    return {
        "total": total,
        "records": [
            {
                "id": record.id,
                "task_id": record.task_id,
                "batch_id": record.batch_id,
                "batch_folder": record.batch_folder,
                "archive_no": record.archive_no,
                "doc_no": record.doc_no,
                "responsible": record.responsible,
                "title": record.title,
                "date": record.date,
                "pages": record.pages,
                "classification": record.classification,
                "remarks": record.remarks,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
            for record in records
        ],
    }


@router.post("/archive-records/import-excel")
async def import_archive_from_excel(body: dict, db: AsyncSession = Depends(get_db)):
    file_path = body.get("file_path", "")
    batch_id = body.get("batch_id", "")
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required.")
    try:
        count = await import_from_excel(db, file_path, batch_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ImportError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Import failed: {error}") from error
    return {"imported": count, "file_path": file_path}


@router.delete("/archive-records")
async def delete_archive_records(
    folder: str = Query(""),
    batch_id: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    query = sa_delete(ArchiveRecord)
    if folder:
        query = query.where(ArchiveRecord.batch_folder == folder)
    if batch_id:
        query = query.where(ArchiveRecord.batch_id == batch_id)
    result = await db.execute(query)
    await db.commit()
    return {"deleted": result.rowcount}


@router.get("/tasks/search")
async def search_tasks_api(
    q: str = Query("", min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"search:{q}:{page}:{page_size}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    tasks, total = await search_tasks(db, q, page, page_size)
    payload = {
        "total": total,
        "tasks": [
            {
                **OCRTaskOut.model_validate(task).model_dump(mode="json"),
                "snippet": _extract_snippet(task, q),
            }
            for task in tasks
        ],
    }
    cache_set(cache_key, payload, SEARCH_TTL)
    return payload


@router.get("/tasks/folders")
async def list_folders(db: AsyncSession = Depends(get_db)):
    cached = cache_get("folders")
    if cached:
        return cached

    rows = (
        await db.execute(sa_text("SELECT id, file_path, created_at FROM ocr_tasks ORDER BY created_at DESC"))
    ).fetchall()
    folders: dict[str, dict] = {}
    for task_id, file_path, created_at in rows:
        if not file_path:
            continue
        folder = str(Path(file_path).parent)
        if folder not in folders:
            folders[folder] = {
                "folder": folder,
                "count": 0,
                "last_time": None,
                "latest_task_id": task_id,
            }
        folders[folder]["count"] += 1
        if created_at and (folders[folder]["last_time"] is None or created_at > folders[folder]["last_time"]):
            folders[folder]["last_time"] = created_at
            folders[folder]["latest_task_id"] = task_id

    from datetime import datetime

    result = sorted(folders.values(), key=lambda item: item["last_time"] or datetime.min, reverse=True)
    cache_set("folders", result, LIST_TTL)
    return result


@router.delete("/tasks/by-folder")
async def delete_tasks_for_folder(
    folder: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_tasks_by_folder(db, folder)
    cache_delete_pattern("task:*")
    invalidate_lists()
    return {"deleted": deleted, "folder": folder}


@router.get("/tasks", response_model=OCRTaskList)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    folder: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"list:{page}:{page_size}:{folder}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    tasks, total = await get_task_list(db, page, page_size, folder=folder)
    payload = OCRTaskList(total=total, tasks=[OCRTaskOut.model_validate(task) for task in tasks]).model_dump(mode="json")
    cache_set(cache_key, payload, LIST_TTL)
    return payload


@router.get("/tasks/{task_id}", response_model=OCRTaskDetail)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    cached = cache_get(f"task:{task_id}")
    if cached and cached.get("status") in TERMINAL_STATUSES:
        return cached

    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    payload = _task_payload(task)
    if task.status in TERMINAL_STATUSES:
        cache_set(f"task:{task_id}", payload, TASK_TTL)
    else:
        cache_delete(f"task:{task_id}")
    return payload


@router.put("/tasks/{task_id}", response_model=OCRTaskDetail)
async def update_task(task_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.status not in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Task result cannot be edited while it is still processing.")

    try:
        if "result_json" in body:
            pages = normalize_result_pages(body["result_json"])
            task.result_json = pages
            task.full_text = serialize_pages_text(pages)
            task.page_count = len(pages)
        elif "full_text" in body:
            task.full_text = str(body["full_text"] or "")
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    await db.commit()
    await db.refresh(task)
    if task.result_json:
        existing_record = (
            await db.execute(select(ArchiveRecord).where(ArchiveRecord.task_id == task.id))
        ).scalar_one_or_none()
        fields = extract_fields(task.filename, task.full_text or "", task.result_json, task.page_count)
        await save_archive_record(
            db,
            task.id,
            existing_record.batch_id if existing_record else "",
            existing_record.batch_folder if existing_record else str(Path(task.file_path).parent),
            fields,
        )
    invalidate_task(task_id)
    return _task_payload(task)


@router.post("/tasks/{task_id}/ai-extract-fields", response_model=AIExtractFieldsResponse)
async def ai_extract_fields(
    task_id: int,
    body: AIExtractFieldsRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    body = body or AIExtractFieldsRequest()
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.status != "done":
        raise HTTPException(status_code=409, detail="AI extraction is only available after OCR is finished.")

    try:
        comparison = await compare_rule_and_llm_fields(task, include_evidence=body.include_evidence)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if body.persist:
        if comparison["conflicts"]:
            raise HTTPException(
                status_code=409,
                detail="AI extraction conflicts with rule extraction. Resolve conflicts before persisting.",
            )

        existing_record = (
            await db.execute(select(ArchiveRecord).where(ArchiveRecord.task_id == task.id))
        ).scalar_one_or_none()
        await save_archive_record(
            db,
            task.id,
            existing_record.batch_id if existing_record else "",
            existing_record.batch_folder if existing_record else str(Path(task.file_path).parent),
            comparison["recommended_fields"],
        )

    return comparison


@router.post("/batches/{batch_id}/ai-merge-extract", response_model=AIBatchMergeExtractResponse)
async def ai_merge_extract_batch(
    batch_id: str,
    body: AIBatchMergeExtractRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    body = body or AIBatchMergeExtractRequest()
    if body.persist:
        raise HTTPException(
            status_code=400,
            detail="persist=true is not supported for batch AI merge extraction in phase 1.",
        )

    try:
        result = await get_batch_merge_extract_result(
            db,
            batch_id=batch_id,
            include_evidence=body.include_evidence,
            force_refresh=body.force_refresh,
        )
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No eligible completed tasks were found for this batch.",
        )

    return result


@router.get("/batches/{batch_id}/evaluation-truth", response_model=BatchEvaluationTruthGetResponse)
async def get_batch_truth(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    payload = await get_batch_evaluation_truth(db, batch_id=batch_id)
    return payload


@router.put("/batches/{batch_id}/evaluation-truth", response_model=BatchEvaluationTruthGetResponse)
async def put_batch_truth(
    batch_id: str,
    body: BatchEvaluationTruthPutRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await save_batch_evaluation_truth(
            db,
            batch_id=batch_id,
            tasks=[item.model_dump(mode="python") for item in body.tasks],
            documents=[item.model_dump(mode="python") for item in body.documents],
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return payload


@router.get("/batches/{batch_id}/evaluation-metrics", response_model=BatchEvaluationMetricsResponse)
async def get_batch_metrics(
    batch_id: str,
    force_refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await get_batch_evaluation_metrics(
            db,
            batch_id=batch_id,
            force_refresh=force_refresh,
        )
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if not payload:
        raise HTTPException(status_code=404, detail="No eligible completed tasks were found for this batch.")
    return payload


@router.get("/batches/{batch_id}/evaluation-report", response_model=BatchEvaluationAiReportResponse)
async def get_batch_ai_report(
    batch_id: str,
    force_refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await get_batch_evaluation_ai_report(
            db,
            batch_id=batch_id,
            force_refresh=force_refresh,
        )
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if not payload:
        raise HTTPException(status_code=404, detail="No eligible completed tasks were found for this batch.")
    return payload


@router.post("/batches/{batch_id}/qa", response_model=BatchQAResponse)
async def batch_qa(
    batch_id: str,
    body: BatchQARequest,
    db: AsyncSession = Depends(get_db),
):
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty.")

    try:
        payload = await answer_batch_question(
            db,
            batch_id=batch_id,
            question=question,
            top_k=body.top_k,
            persist=body.persist,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if not payload:
        raise HTTPException(status_code=404, detail="No eligible completed tasks were found for this batch.")
    return payload


@router.get("/batches/{batch_id}/qa/history", response_model=BatchQAHistoryResponse)
async def batch_qa_history(
    batch_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await get_batch_qa_history(
            db,
            batch_id=batch_id,
            page=page,
            page_size=page_size,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)
    return payload


@router.post("/batches/{batch_id}/qa/{qa_id}/feedback", response_model=BatchQAFeedbackResponse)
async def batch_qa_feedback(
    batch_id: str,
    qa_id: int,
    body: BatchQAFeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await submit_batch_qa_feedback(
            db,
            batch_id=batch_id,
            qa_id=qa_id,
            rating=body.rating,
            reason=body.reason,
            comment=body.comment,
            corrected_answer=body.corrected_answer,
            corrected_evidence=[item.model_dump(mode="python") for item in body.corrected_evidence],
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    if not payload:
        raise HTTPException(status_code=404, detail="QA record not found for this batch.")
    return payload


@router.get("/batches/{batch_id}/qa/metrics", response_model=BatchQAMetricsResponse)
async def batch_qa_metrics(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = await get_batch_qa_metrics(db, batch_id=batch_id)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)
    return payload


@router.delete("/tasks/{task_id}")
async def remove_task(task_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found.")
    invalidate_task(task_id)
    return {"message": "Deleted"}


@router.get("/tasks/{task_id}/export")
async def export_task(
    task_id: int,
    fmt: str = Query("txt", pattern="^(txt|json)$"),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if fmt == "txt":
        return PlainTextResponse(
            content=task.full_text or "",
            headers={"Content-Disposition": f'attachment; filename="{task.filename}.txt"'},
        )

    return JSONResponse(
        content={
            "filename": task.filename,
            "page_count": task.page_count,
            "full_text": task.full_text,
            "result_json": task.result_json,
        },
        headers={"Content-Disposition": f'attachment; filename="{task.filename}.json"'},
    )


@router.get("/tasks/{task_id}/file")
async def get_task_file(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    try:
        file_path = ensure_allowed_path(task.file_path, expect_file=True)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".pdf": "application/pdf",
    }
    return FileResponse(file_path, media_type=media_types.get(file_path.suffix.lower(), "application/octet-stream"))


@router.get("/tasks/{task_id}/thumbnail")
async def get_task_thumbnail(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    try:
        file_path = ensure_allowed_path(task.file_path, expect_file=True)
    except Exception as error:  # noqa: BLE001
        _raise_bad_request(error)

    return Response(content=build_thumbnail(file_path), media_type="image/png")
