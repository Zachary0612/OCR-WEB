import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.auth_routes import router as auth_router
from app.api.routes import router as ocr_router
from app.db.database import init_db
from app.services.task_queue import start_task_worker, stop_task_worker
from config import (
    BASE_DIR,
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_ENABLED,
    MINIMAX_MODEL,
    _mask_secret,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting service bootstrap...")
    logger.info(
        "Python runtime: executable=%s, prefix=%s, base_prefix=%s",
        sys.executable,
        sys.prefix,
        sys.base_prefix,
    )
    logger.info(
        "MiniMax config: enabled=%s, base_url=%s, model=%s, api_key=%s",
        MINIMAX_ENABLED,
        MINIMAX_BASE_URL,
        MINIMAX_MODEL,
        _mask_secret(MINIMAX_API_KEY),
    )
    logger.info("Startup checkpoint: init_db begin")
    await init_db()
    logger.info("Startup checkpoint: init_db complete")
    logger.info("Startup checkpoint: task worker begin")
    await start_task_worker()
    logger.info("Startup checkpoint: task worker complete")
    logger.info("Service is ready.")
    try:
        yield
    finally:
        logger.info("Service shutdown: stopping task worker...")
        await stop_task_worker()
        logger.info("Service shutdown complete.")


app = FastAPI(
    title="PaddleOCR Document Service",
    description="OCR task submission, retrieval, search, and archive export APIs.",
    version="2.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_router)
app.include_router(ocr_router)

VUE_DIST = BASE_DIR / "static" / "vue"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error("Unhandled exception on %s:\n%s", request.url.path, "".join(traceback_lines))
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    favicon_path = BASE_DIR / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path), media_type="image/x-icon")
    return JSONResponse(status_code=404, content={"detail": "favicon.ico not found"})


@app.get("/old")
async def old_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/{full_path:path}")
async def serve_vue(request: Request, full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found."})

    if full_path:
        candidate = VUE_DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))

    vue_index = VUE_DIST / "index.html"
    if vue_index.exists():
        return HTMLResponse(vue_index.read_text(encoding="utf-8"))

    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
