#!/usr/bin/env bash
# ============================================
# 人社档案智能整理系统 - Ubuntu 服务器一键部署脚本
# 用法: chmod +x deploy.sh && sudo ./deploy.sh
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[部署]${NC} $*"; }
warn() { echo -e "${YELLOW}[警告]${NC} $*"; }
err()  { echo -e "${RED}[错误]${NC} $*" >&2; }

# ========== 1. 检查 Docker ==========
log "检查 Docker 环境..."
if ! command -v docker &>/dev/null; then
    warn "Docker 未安装，开始自动安装..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    log "Docker 安装完成"
else
    log "Docker 已安装: $(docker --version)"
fi

# ========== 2. 检查 Docker Compose ==========
if ! docker compose version &>/dev/null; then
    err "docker compose 不可用，请确认 docker-compose-plugin 已安装"
    exit 1
fi
log "Docker Compose: $(docker compose version --short)"

# ========== 3. 检查 NVIDIA Docker 支持（可选） ==========
HAS_GPU=false
if command -v nvidia-smi &>/dev/null; then
    log "检测到 NVIDIA GPU:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
    if docker info 2>/dev/null | grep -q "nvidia"; then
        HAS_GPU=true
        log "NVIDIA Container Toolkit 已就绪"
    else
        warn "检测到 GPU 但 NVIDIA Container Toolkit 未安装"
        warn "请参考: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        warn "安装后重新运行此脚本即可启用 GPU 加速"
    fi
else
    warn "未检测到 NVIDIA GPU，将以 CPU 模式运行（OCR 速度会较慢）"
fi

# ========== 4. 环境配置 ==========
if [ ! -f .env ]; then
    log "从 .env.example 创建 .env 配置文件..."
    cp .env.example .env
    warn "请编辑 .env 文件配置数据库密码、AI 模型等参数"
    warn "  nano $SCRIPT_DIR/.env"
fi

# 如果没有 GPU，自动切换为 CPU 模式
if [ "$HAS_GPU" = false ]; then
    if grep -q "OCR_USE_GPU=true" .env; then
        log "自动切换为 CPU 模式..."
        sed -i 's/OCR_USE_GPU=true/OCR_USE_GPU=false/' .env
        sed -i 's/OCR_DEVICE=gpu:0/OCR_DEVICE=cpu/' .env
    fi
fi

# ========== 5. 选择 Compose 配置 ==========
COMPOSE_FILES="-f docker-compose.yml"

# 如果没有 GPU，使用无 GPU 的覆盖配置
if [ "$HAS_GPU" = false ] && [ -f docker-compose.cpu.yml ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.cpu.yml"
    log "使用 CPU 模式 compose 配置"
fi

# ========== 6. 构建镜像 ==========
log "开始构建 Docker 镜像（首次构建约需 10~30 分钟）..."
docker compose $COMPOSE_FILES build

# ========== 7. 启动服务 ==========
log "启动所有服务..."
docker compose $COMPOSE_FILES up -d

# ========== 8. 等待健康检查 ==========
log "等待服务启动..."
MAX_WAIT=180
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker compose $COMPOSE_FILES ps --format json 2>/dev/null | grep -q '"healthy"'; then
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo -n "."
done
echo ""

# ========== 9. 输出状态 ==========
echo ""
log "============================================"
log "       部署完成！服务状态如下："
log "============================================"
echo ""
docker compose $COMPOSE_FILES ps
echo ""

FRONTEND_PORT=$(grep "FRONTEND_PORT" .env 2>/dev/null | cut -d= -f2 || echo "80")
FRONTEND_PORT=${FRONTEND_PORT:-80}
LOCAL_IP=$(hostname -I | awk '{print $1}')

log "访问地址:"
log "  本机: http://localhost:${FRONTEND_PORT}"
log "  局域网: http://${LOCAL_IP}:${FRONTEND_PORT}"
echo ""

if [ "$HAS_GPU" = true ]; then
    log "GPU 模式已启用，OCR 识别将使用 GPU 加速"
else
    warn "当前为 CPU 模式，如需 GPU 加速请安装 NVIDIA Container Toolkit 后重新部署"
fi

echo ""
log "常用命令:"
log "  查看日志:   docker compose logs -f"
log "  重启服务:   docker compose restart"
log "  停止服务:   docker compose down"
log "  查看状态:   docker compose ps"
echo ""
