import logging
import traceback
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse, FileResponse

from app.api.routes import router as ocr_router
from app.db.database import init_db
from config import BASE_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")
    # 模型改为懒加载：首次识别时自动初始化，避免启动慢
    logger.info("服务就绪！模型将在首次使用时自动加载。")
    yield


app = FastAPI(
    title="PaddleOCR 文档识别系统",
    description="基于 PaddleOCR 3.0 的文档识别 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 注册 API 路由
app.include_router(ocr_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error("Unhandled exception:\n%s", "".join(tb))
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(BASE_DIR / "static" / "favicon.ico"), media_type="image/x-icon")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
