import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 缓存目录配置（避免占用 C 盘）
CACHE_DIR = BASE_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR / "huggingface")
os.environ["PADDLE_PDX_CACHE_HOME"] = str(CACHE_DIR / "paddlex")
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"  # 使用百度 BOS 下载模型，避免 HuggingFace 网络问题
os.environ["FLAGS_json_format_model"] = "0"  # PP-StructureV3 版面解析需要此设置

# 数据库配置（PostgreSQL）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:123456@localhost:5432/ocr_db"
)

# 上传文件目录
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"}

# 单文件最大大小 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# OCR 配置
OCR_USE_GPU = True
OCR_LANG = "ch"  # ch=中英混合, en=英文
