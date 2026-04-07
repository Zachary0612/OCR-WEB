#!/bin/bash
# OCR 项目一键启动脚本（容器内使用）
set -e

echo "=========================================="
echo "  OCR 服务启动脚本"
echo "=========================================="

# ---- 1. GPU keepalive ----
if ! pgrep -f gpu_keepalive.sh > /dev/null 2>&1; then
    if [ -f /root/gpu_keepalive.sh ]; then
        nohup /root/gpu_keepalive.sh > /dev/null 2>&1 &
        echo "[✓] GPU keepalive 已启动 (PID: $!)"
    else
        echo "[!] /root/gpu_keepalive.sh 不存在，跳过 GPU keepalive"
    fi
else
    echo "[✓] GPU keepalive 已在运行"
fi

# ---- 2. 启动 PostgreSQL ----
if ! pg_isready -q 2>/dev/null; then
    service postgresql start
    sleep 1
    echo "[✓] PostgreSQL 已启动"
else
    echo "[✓] PostgreSQL 已在运行"
fi

# ---- 3. 启动 Redis ----
if ! redis-cli ping > /dev/null 2>&1; then
    redis-server --daemonize yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    echo "[✓] Redis 已启动"
else
    echo "[✓] Redis 已在运行"
fi

# ---- 4. 环境变量 ----
export DATABASE_URL="postgresql+asyncpg://ocruser:ocr123456@localhost:5432/ocr_db"
export REDIS_URL="redis://localhost:6379/0"
export UPLOAD_DIR="/root/OCR/uploads"
export CACHE_DIR="/root/OCR/.cache"
export OCR_DEVICE="gpu:0"
export OCR_LANG="ch"
export AUTH_ENABLED="false"
export PADDLE_PDX_CACHE_HOME="/root/OCR/.cache/paddlex"
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
export FLAGS_json_format_model=0
export HF_HOME="/root/OCR/.cache/huggingface"

# ---- 5. 确保目录存在 ----
mkdir -p /root/OCR/uploads /root/OCR/.cache /root/OCR/logs

# ---- 6. 检查 GPU ----
GPU_COUNT=$(python -c "import paddle; print(paddle.device.cuda.device_count())" 2>/dev/null || echo "0")
if [ "$GPU_COUNT" -gt 0 ]; then
    echo "[✓] GPU 可用 (数量: $GPU_COUNT)"
else
    echo "[!] GPU 不可用，将自动降级为 CPU 模式"
    export OCR_DEVICE="cpu"
fi

echo "=========================================="
echo "  启动 uvicorn (port 8000)..."
echo "=========================================="

cd /root/OCR
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
