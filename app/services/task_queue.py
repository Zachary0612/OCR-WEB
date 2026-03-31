import asyncio
import logging
from dataclasses import dataclass

from app.core.redis_cache import TASK_TTL, cache_delete, cache_set, invalidate_lists
from app.db.database import async_session
from app.schemas.ocr_schemas import OCRTaskDetail
from app.services.ocr_service import finalize_task_outputs, get_task_detail, run_ocr_task


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OCRJob:
    task_id: int
    mode: str
    excel_path: str = ""
    excel_init: int = 0
    output_dir: str = ""
    batch_id: str = ""


_queue: asyncio.Queue[OCRJob] | None = None
_worker_task: asyncio.Task | None = None


async def start_task_worker() -> None:
    global _queue, _worker_task
    if _queue is None:
        _queue = asyncio.Queue()
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker_loop(), name="ocr-task-worker")
        logger.info("OCR task worker started.")


async def stop_task_worker() -> None:
    global _worker_task
    if _worker_task is None:
        return
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    logger.info("OCR task worker stopped.")
    _worker_task = None


async def enqueue_task(job: OCRJob) -> None:
    if _queue is None:
        await start_task_worker()
    assert _queue is not None
    await _queue.put(job)
    cache_delete(f"task:{job.task_id}")
    invalidate_lists()


async def _worker_loop() -> None:
    assert _queue is not None
    while True:
        job = await _queue.get()
        try:
            await _process_job(job)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to process OCR task %s.", job.task_id)
        finally:
            _queue.task_done()


async def _process_job(job: OCRJob) -> None:
    async with async_session() as db:
        cache_delete(f"task:{job.task_id}")
        task = await run_ocr_task(db, job.task_id, mode=job.mode)
        task = await finalize_task_outputs(
            db,
            task,
            excel_path=job.excel_path,
            excel_init=job.excel_init,
            output_dir=job.output_dir,
            batch_id=job.batch_id,
        )
        detail = await get_task_detail(db, task.id)
        if detail is None:
            return
        payload = OCRTaskDetail.model_validate(detail).model_dump(mode="json")
        if detail.status in {"done", "failed"}:
            cache_set(f"task:{detail.id}", payload, TASK_TTL)
        else:
            cache_delete(f"task:{detail.id}")
        invalidate_lists()
