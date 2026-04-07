#!/usr/bin/env bash
# ============================================
# 人社档案智能整理系统 - docker run 一键启动
# 用法: chmod +x run.sh && sudo ./run.sh
# ============================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log()  { echo -e "${GREEN}[启动]${NC} $*"; }
warn() { echo -e "${YELLOW}[提示]${NC} $*"; }

# ---------- 配置（可按需修改）----------
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ocr123456}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_PORT="${REDIS_PORT:-6379}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"
NET="ocr-net"

# ---------- 检测 GPU ----------
HAS_GPU=false
GPU_FLAG=""
if command -v nvidia-smi &>/dev/null && docker info 2>/dev/null | grep -q "nvidia"; then
    HAS_GPU=true
    GPU_FLAG="--gpus all"
    log "检测到 GPU，将启用 GPU 加速"
else
    warn "未检测到 GPU，使用 CPU 模式（OCR 较慢）"
fi

if [ "$HAS_GPU" = true ]; then
    OCR_USE_GPU="true"
    OCR_DEVICE="gpu:0"
else
    OCR_USE_GPU="false"
    OCR_DEVICE="cpu"
fi

# ---------- 创建网络 ----------
docker network create "$NET" 2>/dev/null || true

# ---------- 创建数据卷 ----------
docker volume create ocr_postgres_data 2>/dev/null || true
docker volume create ocr_redis_data 2>/dev/null || true
docker volume create ocr_uploads 2>/dev/null || true
docker volume create ocr_cache 2>/dev/null || true

# ---------- 1. 启动 PostgreSQL ----------
log "[1/4] 启动 PostgreSQL..."
docker rm -f ocr-postgres 2>/dev/null || true
docker run -d \
    --name ocr-postgres \
    --network "$NET" \
    --restart unless-stopped \
    -e POSTGRES_USER=ocruser \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB=ocr_db \
    -v ocr_postgres_data:/var/lib/postgresql/data \
    -p "${POSTGRES_PORT}:5432" \
    postgres:15-alpine

# 等待 PostgreSQL 就绪
log "  等待 PostgreSQL 就绪..."
for i in $(seq 1 30); do
    if docker exec ocr-postgres pg_isready -U ocruser -d ocr_db &>/dev/null; then
        break
    fi
    sleep 1
done
log "  PostgreSQL 已就绪"

# ---------- 2. 启动 Redis ----------
log "[2/4] 启动 Redis..."
docker rm -f ocr-redis 2>/dev/null || true
docker run -d \
    --name ocr-redis \
    --network "$NET" \
    --restart unless-stopped \
    -v ocr_redis_data:/data \
    -p "${REDIS_PORT}:6379" \
    redis:7-alpine \
    redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

# ---------- 3. 启动后端 ----------
log "[3/4] 启动后端服务（OCR 引擎）..."
docker rm -f ocr-backend 2>/dev/null || true
docker run -d \
    --name ocr-backend \
    --network "$NET" \
    --restart unless-stopped \
    --shm-size 8g \
    $GPU_FLAG \
    -e DATABASE_URL="postgresql+asyncpg://ocruser:${POSTGRES_PASSWORD}@ocr-postgres:5432/ocr_db" \
    -e REDIS_URL="redis://ocr-redis:6379/0" \
    -e UPLOAD_DIR=/app/uploads \
    -e CACHE_DIR=/app/.cache \
    -e OCR_USE_GPU="$OCR_USE_GPU" \
    -e OCR_DEVICE="$OCR_DEVICE" \
    -e OCR_LANG=ch \
    -e AUTH_ENABLED=false \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -v ocr_uploads:/app/uploads \
    -v ocr_cache:/app/.cache \
    -p "${BACKEND_PORT}:8000" \
    ocr-backend:latest

# 等待后端就绪
log "  等待后端服务启动（首次启动约 30~60 秒）..."
for i in $(seq 1 120); do
    if curl -sf http://localhost:${BACKEND_PORT}/api/health &>/dev/null; then
        break
    fi
    sleep 2
done
log "  后端服务已就绪"

# ---------- 4. 启动前端 ----------
log "[4/4] 启动前端..."
docker rm -f ocr-frontend 2>/dev/null || true
docker run -d \
    --name ocr-frontend \
    --network "$NET" \
    --restart unless-stopped \
    -p "${FRONTEND_PORT}:80" \
    ocr-frontend:latest

# ---------- 完成 ----------
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
log "============================================"
log "  全部服务启动完成！"
log "============================================"
echo ""
log "访问地址:"
log "  http://localhost:${FRONTEND_PORT}"
log "  http://${LOCAL_IP}:${FRONTEND_PORT}"
echo ""
log "4 个容器状态:"
docker ps --filter "name=ocr-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
log "常用命令:"
log "  查看日志:  docker logs -f ocr-backend"
log "  停止全部:  ./stop.sh"
log "  重启后端:  docker restart ocr-backend"
