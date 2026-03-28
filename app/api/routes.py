import logging
from pathlib import Path

import json as _json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import OCRTask
from app.schemas.ocr_schemas import OCRTaskOut, OCRTaskDetail, OCRTaskList
from app.services.excel_export import (
    extract_fields,
    append_to_excel,
    init_excel,
    resolve_excel_output_path,
    clear_excel_data,
)
from app.services.ocr_service import (
    save_upload_file,
    create_task,
    run_ocr_task,
    get_task_list,
    get_task_detail,
    delete_task,
    search_tasks,
)
from app.core.redis_cache import (
    cache_get, cache_set, cache_delete,
    invalidate_task, invalidate_lists,
    TASK_TTL, LIST_TTL, SEARCH_TTL,
)
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ocr", tags=["OCR"])


def _apply_post_exports(result: dict, detail, source_path: Path, excel_path: str, excel_init: int, output_dir: str):
    if detail.status != "done":
        return result

    if output_dir:
        try:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = source_path.stem
            json_out = out_dir / f"{stem}.json"
            json_out.write_text(
                _json.dumps(detail.result_json, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            txt_out = out_dir / f"{stem}.txt"
            txt_out.write_text(detail.full_text or "", encoding="utf-8")
            result["output_saved"] = str(out_dir)
            logger.info("识别结果已保存: %s -> %s", detail.filename, out_dir)
        except Exception as ex:
            logger.warning("保存结果文件失败: %s", ex)
            result["output_saved"] = False

    if excel_path:
        actual_excel_path = excel_path
        try:
            actual_excel_path = resolve_excel_output_path(excel_path)
            ep = Path(actual_excel_path)
            if not ep.exists():
                init_excel(actual_excel_path)
            elif excel_init:
                clear_excel_data(actual_excel_path)
                logger.info("已清空Excel旧数据: %s", actual_excel_path)
            fields = extract_fields(
                detail.filename, detail.full_text or "",
                detail.result_json, detail.page_count
            )
            append_to_excel(actual_excel_path, fields)
            result["excel_exported"] = True
            result["excel_path"] = actual_excel_path
            logger.info("已写入归档Excel: %s -> %s", detail.filename, actual_excel_path)
        except Exception as ex:
            logger.warning("写入Excel失败: %s", ex)
            result["excel_exported"] = False
            result["excel_path"] = actual_excel_path

    return result


@router.post("/upload")
async def upload_and_recognize(
    file: UploadFile = File(...),
    relative_path: str = Form(""),
    mode: str = Query("vl", pattern="^(vl|layout|ocr)$"),
    excel_path: str = Query("", description="可选：自动写入归档Excel的路径"),
    excel_init: int = Query(0, description="为1时先清空Excel数据行（批次第一个文件传入）"),
    output_dir: str = Query("", description="可选：识别结果输出目录，将生成 .json 和 .txt 文件"),
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
        file_path, file_type = await save_upload_file(file.filename, content, relative_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        task = await create_task(db, file.filename, file_path, file_type, mode=mode)
        logger.info("创建任务 %d: %s (mode=%s)", task.id, file.filename, mode)

        task = await run_ocr_task(db, task.id, mode=mode)

        detail = await get_task_detail(db, task.id)
        result = OCRTaskDetail.model_validate(detail).model_dump(mode='json')
        result = _apply_post_exports(result, detail, Path(file.filename), excel_path, excel_init, output_dir)
        cache_set(f"task:{detail.id}", result, TASK_TTL)
        invalidate_lists()
        return result
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
    excel_path: str = Query("", description="可选：自动写入归档Excel的路径"),
    excel_init: int = Query(0, description="为1时先清空Excel数据行（批次第一个文件传入）"),
    output_dir: str = Query("", description="可选：识别结果输出目录，将生成 .json 和 .txt 文件"),
    db: AsyncSession = Depends(get_db),
):
    """从服务器本地路径直接识别文件（无需上传），可选自动写入归档Excel和结果目录"""
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
        result = OCRTaskDetail.model_validate(detail).model_dump(mode='json')
        result = _apply_post_exports(result, detail, file_path, excel_path, excel_init, output_dir)
        cache_set(f"task:{detail.id}", result, TASK_TTL)
        invalidate_lists()

        return result
    except Exception as e:
        logger.exception("本地路径识别失败: %s", str(e))
        invalidate_lists()
        return {"error": str(e), "file_path": file_path_str, "status": "failed"}


@router.get("/tasks/search")
async def search_tasks_api(
    q: str = Query("", min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """搜索已识别文档（按文件名、识别文本、JSON内容模糊匹配，含表格）"""
    cache_key = f"search:{q}:{page}:{page_size}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    tasks, total = await search_tasks(db, q, page, page_size)
    task_list = []
    for t in tasks:
        item = OCRTaskOut.model_validate(t).model_dump(mode='json')
        snippet = _extract_snippet(t, q)
        item['snippet'] = snippet
        task_list.append(item)
    resp = {"total": total, "tasks": task_list}
    cache_set(cache_key, resp, SEARCH_TTL)
    return resp


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


@router.get("/tasks/folders")
async def list_folders(db: AsyncSession = Depends(get_db)):
    """获取所有任务的源文件夹列表（用于前端分组显示）"""
    from sqlalchemy import text as sa_text
    cached = cache_get("folders")
    if cached:
        return cached
    # Order by created_at DESC so first task seen per folder is the latest
    result = await db.execute(sa_text(
        "SELECT id, file_path, created_at FROM ocr_tasks ORDER BY created_at DESC"
    ))
    rows = result.fetchall()
    folders: dict = {}
    for id_, file_path, created_at in rows:
        if not file_path:
            continue
        p = Path(file_path)
        folder = str(p.parent)
        if folder not in folders:
            folders[folder] = {"folder": folder, "count": 0, "last_time": None, "latest_task_id": id_}
        folders[folder]["count"] += 1
        if created_at and (folders[folder]["last_time"] is None or created_at > folders[folder]["last_time"]):
            folders[folder]["last_time"] = created_at
            folders[folder]["latest_task_id"] = id_
    from datetime import datetime as _dt
    result_list = sorted(folders.values(), key=lambda x: x["last_time"] or _dt.min, reverse=True)
    cache_set("folders", result_list, LIST_TTL)
    return result_list


@router.delete("/tasks/by-folder")
async def delete_tasks_by_folder(
    folder: str = Query(..., description="要删除的文件夹路径"),
    db: AsyncSession = Depends(get_db),
):
    """删除指定文件夹下的所有任务"""
    from sqlalchemy import delete as sa_delete, func, or_
    base = folder.rstrip("/\\")
    result = await db.execute(
        sa_delete(OCRTask).where(
            or_(
                func.starts_with(OCRTask.file_path, base + "\\"),
                func.starts_with(OCRTask.file_path, base + "/"),
            )
        )
    )
    await db.commit()
    invalidate_lists()
    logger.info("删除文件夹任务: %s (%d 条)", folder, result.rowcount)
    return {"deleted": result.rowcount, "folder": folder}


@router.get("/tasks", response_model=OCRTaskList)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    folder: str = Query("", description="按源文件夹过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取识别任务列表"""
    cache_key = f"list:{page}:{page_size}:{folder}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    tasks, total = await get_task_list(db, page, page_size, folder=folder)
    resp = OCRTaskList(total=total, tasks=[OCRTaskOut.model_validate(t) for t in tasks])
    cache_set(cache_key, resp.model_dump(mode='json'), LIST_TTL)
    return resp


@router.get("/tasks/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务详情"""
    cached = cache_get(f"task:{task_id}")
    if cached:
        return cached
    task = await get_task_detail(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = OCRTaskDetail.model_validate(task).model_dump(mode='json')
        cache_set(f"task:{task_id}", result, TASK_TTL)
        return result
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
    invalidate_task(task_id)
    return OCRTaskDetail.model_validate(task).model_dump(mode='json')


@router.delete("/tasks/{task_id}")
async def remove_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    success = await delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    invalidate_task(task_id)
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
