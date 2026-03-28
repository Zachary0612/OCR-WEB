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
    search_tasks,
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
        task = await create_task(db, file.filename, file_path, file_type, mode=mode)
        logger.info("创建任务 %d: %s (mode=%s)", task.id, file.filename, mode)

        task = await run_ocr_task(db, task.id, mode=mode)

        detail = await get_task_detail(db, task.id)
        return OCRTaskDetail.model_validate(detail).model_dump(mode='json')
    except Exception as e:
        logger.exception("OCR 处理失败: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan-folder")
async def scan_folder(path: str = Query(..., description="本地文件夹路径")):
    """扫描本地文件夹，返回支持的图片/PDF文件列表（递归）"""
    import os
    ACCEPTED = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'}
    folder = Path(path)
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"路径不存在或不是文件夹: {path}")
    files = []
    for root, dirs, filenames in os.walk(folder):
        dirs.sort()
        for name in sorted(filenames):
            ext = Path(name).suffix.lower()
            if ext in ACCEPTED:
                full = Path(root) / name
                rel = str(full.relative_to(folder))
                files.append({
                    "name": name,
                    "path": str(full),
                    "rel_path": rel,
                    "size": full.stat().st_size,
                })
    return {"folder": str(folder), "count": len(files), "files": files}


@router.post("/upload-from-path")
async def upload_from_path(
    body: dict,
    mode: str = Query("vl", pattern="^(vl|layout|ocr)$"),
    db: AsyncSession = Depends(get_db),
):
    """从服务器本地路径直接识别文件（无需上传）"""
    file_path_str = body.get("file_path", "")
    file_path = Path(file_path_str)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"文件不存在: {file_path_str}")
    file_type = file_path.suffix.lower()
    ACCEPTED = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'}
    if file_type not in ACCEPTED:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")
    try:
        task = await create_task(db, file_path.name, str(file_path), file_type, mode=mode)
        task = await run_ocr_task(db, task.id, mode=mode)
        detail = await get_task_detail(db, task.id)
        # 即使 OCR 失败，也返回任务信息（status=failed），前端可据此跳过
        return OCRTaskDetail.model_validate(detail).model_dump(mode='json')
    except Exception as e:
        logger.exception("本地路径识别失败: %s", str(e))
        # 返回错误信息但不崩溃，让批量处理继续
        return {"error": str(e), "file_path": file_path_str, "status": "failed"}


@router.get("/tasks/search")
async def search_tasks_api(
    q: str = Query("", min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """搜索已识别文档（按文件名、识别文本、JSON内容模糊匹配，含表格）"""
    tasks, total = await search_tasks(db, q, page, page_size)
    task_list = []
    for t in tasks:
        item = OCRTaskOut.model_validate(t).model_dump(mode='json')
        snippet = _extract_snippet(t, q)
        item['snippet'] = snippet
        task_list.append(item)
    return {"total": total, "tasks": task_list}


def _extract_snippet(task, keyword: str, ctx: int = 50) -> str:
    """从 full_text 和 result_json 中提取包含关键词的片段"""
    kw = keyword.lower()

    # 1. Try full_text first
    if task.full_text and kw in task.full_text.lower():
        return _cut_around(task.full_text, kw, ctx)

    # 2. Try extracting from result_json (regions content + table html)
    if task.result_json:
        pages = task.result_json if isinstance(task.result_json, list) else [task.result_json]
        for page in pages:
            if not isinstance(page, dict):
                continue
            for region in page.get("regions", []):
                content = region.get("content", "") or ""
                if kw in content.lower():
                    return _cut_around(content, kw, ctx)
                html = region.get("html", "") or ""
                if kw in html.lower():
                    # Strip HTML tags for clean snippet
                    import re
                    clean = re.sub(r'<[^>]+>', ' ', html)
                    if kw in clean.lower():
                        return _cut_around(clean, kw, ctx)
            for line in page.get("lines", []):
                text = line.get("text", "") or ""
                if kw in text.lower():
                    return _cut_around(text, kw, ctx)

    # 3. Filename match
    if kw in (task.filename or "").lower():
        return f"文件名匹配: {task.filename}"

    return ""


def _cut_around(text: str, kw: str, ctx: int = 50) -> str:
    """Cut a snippet around the keyword with context"""
    idx = text.lower().index(kw)
    start = max(0, idx - ctx)
    end = min(len(text), idx + len(kw) + ctx)
    s = text[start:end].replace('\n', ' ')
    return ('...' if start > 0 else '') + s + ('...' if end < len(text) else '')


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
    return FileResponse(file_path, media_type=media_type)
