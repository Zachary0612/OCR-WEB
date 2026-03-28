import gc
import logging
import uuid
from pathlib import Path

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ocr_engine import ocr_document
from app.db.models import OCRTask
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


async def save_upload_file(filename: str, file_content: bytes) -> tuple[str, str]:
    """
    保存上传文件，返回 (存储路径, 文件类型)
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}")

    # 使用 UUID 避免文件名冲突
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / unique_name
    save_path.write_bytes(file_content)
    return str(save_path), ext


async def create_task(db: AsyncSession, filename: str, file_path: str, file_type: str, mode: str = "layout") -> OCRTask:
    """创建 OCR 任务"""
    task = OCRTask(
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        mode=mode,
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def run_ocr_task(db: AsyncSession, task_id: int, mode: str = "layout") -> OCRTask:
    """执行 OCR 任务 (mode: layout=版面解析+表格, ocr=基础识别)"""
    task = await db.get(OCRTask, task_id)
    if not task:
        raise ValueError(f"任务不存在: {task_id}")

    task.status = "processing"
    await db.commit()

    try:
        result = ocr_document(task.file_path, mode=mode)

        # 直接以 JSON 存储完整识别结果
        task.result_json = result["pages"]
        task.full_text = result["full_text"]
        task.page_count = result["page_count"]
        task.status = "done"
        await db.commit()
        await db.refresh(task)
        logger.info("任务 %d 识别完成，共 %d 页", task.id, task.page_count)

    except Exception as e:
        logger.error("任务 %d 识别失败: %s", task.id, str(e))
        task.status = "failed"
        task.error_message = str(e)
        await db.commit()
        await db.refresh(task)
    finally:
        # 强制释放内存，防止批量处理时 OOM
        gc.collect()
        try:
            import paddle
            paddle.device.cuda.empty_cache()
        except Exception:
            pass

    return task


async def get_task_list(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list[OCRTask], int]:
    """获取任务列表（分页）"""
    total_result = await db.execute(select(func.count(OCRTask.id)))
    total = total_result.scalar() or 0

    stmt = (
        select(OCRTask)
        .order_by(desc(OCRTask.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())
    return tasks, total


async def get_task_detail(db: AsyncSession, task_id: int) -> OCRTask | None:
    """获取任务详情（含 JSON 识别结果）"""
    return await db.get(OCRTask, task_id)


async def search_tasks(db: AsyncSession, keyword: str, page: int = 1, page_size: int = 20) -> tuple[list[OCRTask], int]:
    """搜索任务：在 filename、full_text 和 result_json(含表格内容) 中模糊匹配"""
    from sqlalchemy import or_, cast, String as SAString
    like_pattern = f"%{keyword}%"
    condition = or_(
        OCRTask.filename.ilike(like_pattern),
        OCRTask.full_text.ilike(like_pattern),
        cast(OCRTask.result_json, SAString).ilike(like_pattern),
    )

    total_result = await db.execute(select(func.count(OCRTask.id)).where(condition))
    total = total_result.scalar() or 0

    stmt = (
        select(OCRTask)
        .where(condition)
        .order_by(desc(OCRTask.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())
    return tasks, total


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    """删除任务及其关联文件"""
    task = await db.get(OCRTask, task_id)
    if not task:
        return False

    # 删除文件
    try:
        Path(task.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    await db.delete(task)
    await db.commit()
    return True
