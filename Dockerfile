FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddle:3.3.0-gpu-cuda12.6-cudnn9.5

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PADDLE_PDX_CACHE_HOME=/app/.cache/paddlex \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
    PADDLE_PDX_MODEL_SOURCE=bos \
    FLAGS_json_format_model=0 \
    HF_HOME=/app/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.docker.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.docker.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY config.py ./
COPY main.py ./
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/
COPY init_archive_db.py ./
COPY scripts/ ./scripts/

RUN mkdir -p /app/uploads /app/.cache /app/logs /app/static/vue

# 预下载全部 3 个 OCR 模型（PP-OCRv5 / PP-StructureV3 / PaddleOCR-VL-1.5）
# 模型文件会缓存在 /app/.cache 中，使镜像可完全离线运行
RUN python scripts/prefetch_models.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
