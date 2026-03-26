import logging
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.ocr_schemas import OCRTaskOut, OCRTaskDetail, OCRTaskList
from app.services.ocr_service import (
    save_upload_file,
    create_task,
    run_ocr_task,
    get_task_list,
    get_task_detail,
    delete_task,
)
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post("/upload")
async def upload_and_recognize(
    file: UploadFile = File(...),
    mode: str = Query("vl", pattern="^(vl|layout|ocr)$"),
    db: AsyncSession = Depends(get_db),
):
    """上传文件并执行 OCR 识别
    
    mode: layout=PP-StructureV3版面解析(含表格), ocr=PP-OCRv5基础识别(快速)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大，最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB")

    try:
        file_path, file_type = await save_upload_file(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        task = await create_task(db, file.filename, file_path, file_type)
        logger.info("创建任务 %d: %s (mode=%s)", task.id, file.filename, mode)

        task = await run_ocr_task(db, task.id, mode=mode)

        detail = await get_task_detail(db, task.id)
        return OCRTaskDetail.model_validate(detail).model_dump(mode='json')
    except Exception as e:
        logger.exception("OCR 处理失败: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=OCRTaskList)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取识别任务列表"""
    tasks, total = await get_task_list(db, page, page_size)
    return OCRTaskList(total=total, tasks=[OCRTaskOut.model_validate(t) for t in tasks])


@router.get("/tasks/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务详情"""
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        return OCRTaskDetail.model_validate(task).model_dump(mode='json')
    except Exception as e:
        logger.exception("序列化任务 %d 失败: %s", task_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, body: dict, db: AsyncSession = Depends(get_db)):
    """更新已保存任务的识别结果（编辑后保存）"""
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if "result_json" in body:
        task.result_json = body["result_json"]
    if "full_text" in body:
        task.full_text = body["full_text"]
    await db.commit()
    await db.refresh(task)
    logger.info("更新任务 %d 的识别结果", task_id)
    return OCRTaskDetail.model_validate(task).model_dump(mode='json')


@router.delete("/tasks/{task_id}")
async def remove_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    success = await delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "删除成功"}


@router.get("/tasks/{task_id}/export")
async def export_task(
    task_id: int,
    fmt: str = Query("txt", pattern="^(txt|json)$"),
    db: AsyncSession = Depends(get_db),
):
    """导出识别结果"""
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if fmt == "txt":
        return PlainTextResponse(
            content=task.full_text or "",
            headers={"Content-Disposition": f'attachment; filename="{task.filename}.txt"'},
        )
    else:
        export_data = {
            "filename": task.filename,
            "page_count": task.page_count,
            "full_text": task.full_text,
            "result_json": task.result_json,
        }
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": f'attachment; filename="{task.filename}.json"'},
        )


@router.get("/tasks/{task_id}/file")
async def get_task_file(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的原始文件（用于前端预览）"""
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    file_path = Path(task.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".bmp": "image/bmp",
        ".tiff": "image/tiff", ".tif": "image/tiff",
        ".pdf": "application/pdf",
    }
    ext = file_path.suffix.lower()
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(file_path, media_type=media_type, filename=task.filename)
