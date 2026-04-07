#!/usr/bin/env bash
# ============================================
# 构建 Docker 镜像并导出为 tar 文件
# 在有网络的 Ubuntu 服务器上运行此脚本
# 产出: ocr-images.tar.gz（可直接交付甲方）
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log()  { echo -e "${GREEN}[构建]${NC} $*"; }
warn() { echo -e "${YELLOW}[提示]${NC} $*"; }

OUTPUT_FILE="${1:-ocr-images.tar.gz}"

log "============================================"
log "  开始构建 OCR 系统 Docker 镜像"
log "  （含全部 3 个 OCR 模型，预计 20~40 分钟）"
log "============================================"

# 检查 Docker
if ! command -v docker &>/dev/null; then
    echo "错误: Docker 未安装" >&2
    exit 1
fi

# 1. 构建后端镜像（含模型预下载）
log ""
log "[1/4] 构建后端镜像（含 PP-OCRv5 / PP-StructureV3 / PaddleOCR-VL-1.5）..."
docker build -t ocr-backend:latest -f Dockerfile .

# 2. 构建前端镜像
log ""
log "[2/4] 构建前端镜像..."
docker build -t ocr-frontend:latest -f frontend/Dockerfile .

# 3. 拉取基础设施镜像
log ""
log "[3/4] 拉取 PostgreSQL 和 Redis 镜像..."
docker pull postgres:15-alpine
docker pull redis:7-alpine

# 4. 导出全部镜像
log ""
log "[4/4] 导出全部镜像到 ${OUTPUT_FILE}..."
docker save \
    ocr-backend:latest \
    ocr-frontend:latest \
    postgres:15-alpine \
    redis:7-alpine \
    | gzip > "${OUTPUT_FILE}"

SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)

log ""
log "============================================"
log "  构建导出完成！"
log "  文件: ${OUTPUT_FILE}"
log "  大小: ${SIZE}"
log "============================================"
log ""
log "交付给甲方的文件清单:"
log "  1. ${OUTPUT_FILE}    （Docker 镜像，含全部模型）"
log "  2. .env.example       （环境配置模板）"
log "  3. run.sh             （一键启动脚本）"
log "  4. stop.sh            （停止脚本）"
log ""
log "甲方服务器运行命令:"
log "  docker load < ${OUTPUT_FILE}"
log "  cp .env.example .env && nano .env"
log "  chmod +x run.sh && sudo ./run.sh"
