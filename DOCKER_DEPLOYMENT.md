# OCR 档案识别系统 - Docker 部署指南

> **适用场景**：使用 Docker Compose 一键部署 OCR 档案识别系统  
> **预计耗时**：30 分钟（不含镜像下载时间）  
> **最后更新**：2026-03-30

---

## 目录

1. [系统要求](#1-系统要求)
2. [安装 Docker](#2-安装-docker)
3. [安装 NVIDIA Container Toolkit（GPU）](#3-安装-nvidia-container-toolkitgpu)
4. [获取项目代码](#4-获取项目代码)
5. [配置环境变量](#5-配置环境变量)
6. [启动服务](#6-启动服务)
7. [验证部署](#7-验证部署)
8. [初始数据导入](#8-初始数据导入)
9. [日常运维](#9-日常运维)
10. [数据备份与恢复](#10-数据备份与恢复)
11. [更新部署](#11-更新部署)
12. [CPU 模式部署](#12-cpu-模式部署)
13. [常见问题](#13-常见问题)

---

## 1. 系统要求

### 1.1 硬件要求

| 组件 | GPU 模式 | CPU 模式 |
|------|----------|----------|
| **GPU** | NVIDIA GPU（显存 ≥ 8GB） | 不需要 |
| **CPU** | 4 核 | 8 核及以上 |
| **内存** | 16 GB | 32 GB |
| **磁盘** | 50 GB SSD | 50 GB SSD |

### 1.2 软件要求

| 软件 | 版本 |
|------|------|
| **操作系统** | Ubuntu 20.04/22.04 LTS、CentOS 7/8、Debian 11+ |
| **Docker** | 24.0+ |
| **Docker Compose** | V2（内置于 Docker） |
| **NVIDIA 驱动** | 535+ （GPU 模式） |
| **NVIDIA Container Toolkit** | 最新版（GPU 模式） |

### 1.3 端口占用

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | 前端入口 |
| 8000 | 后端 API | FastAPI 服务 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |

---

## 2. 安装 Docker

### Ubuntu / Debian

```bash
# 卸载旧版本
sudo apt remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# 添加 Docker 官方 GPG 密钥
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 添加仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动并设为开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组（避免每次 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

### CentOS / RHEL

```bash
# 卸载旧版本
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 安装依赖
sudo yum install -y yum-utils

# 添加仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动
sudo systemctl start docker
sudo systemctl enable docker

# 加入 docker 组
sudo usermod -aG docker $USER
```

### 配置镜像加速（国内推荐）

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com"
  ]
}
EOF

sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 3. 安装 NVIDIA Container Toolkit（GPU）

> **注意**：仅 GPU 模式需要此步骤，CPU 模式跳过。

### 3.1 前提条件

确保已安装 NVIDIA 驱动：

```bash
nvidia-smi
```

如果未安装驱动，请先安装：

```bash
# Ubuntu
sudo apt install -y nvidia-driver-535

# 重启后验证
sudo reboot
nvidia-smi
```

### 3.2 安装 NVIDIA Container Toolkit

```bash
# 添加仓库
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 安装
sudo apt update
sudo apt install -y nvidia-container-toolkit

# 配置 Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 3.3 验证 GPU 支持

```bash
docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi
```

应显示 GPU 信息。

---

## 4. 获取项目代码

### 方式一：Git 克隆（推荐）

```bash
# 创建部署目录
sudo mkdir -p /opt/ocr
sudo chown $USER:$USER /opt/ocr

# 克隆代码
git clone https://github.com/Zachary0612/OCR-WEB.git /opt/ocr
cd /opt/ocr
```

### 方式二：上传代码包

```bash
# 在本地打包
tar -czvf ocr-project.tar.gz --exclude='.git' --exclude='node_modules' --exclude='.venv' --exclude='__pycache__' .

# 上传到服务器
scp ocr-project.tar.gz user@server:/opt/

# 在服务器解压
cd /opt
mkdir ocr && tar -xzvf ocr-project.tar.gz -C ocr
cd ocr
```

---

## 5. 配置环境变量

### 5.1 创建 .env 文件

```bash
cd /opt/ocr
cp .env.example .env
```

### 5.2 编辑配置

```bash
vim .env
```

内容：

```bash
# ============================================
# OCR Docker 环境变量配置
# ============================================

# PostgreSQL 数据库密码（必须修改！）
POSTGRES_PASSWORD=YourStrongPassword123!

# OCR 配置
OCR_USE_GPU=true
OCR_DEVICE=gpu:0
OCR_LANG=ch
```

### 5.3 配置说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `POSTGRES_PASSWORD` | 数据库密码 | `YourStrongPassword123!` |
| `OCR_USE_GPU` | 是否使用 GPU | `true` / `false` |
| `OCR_DEVICE` | OCR 设备 | `gpu:0` / `cpu` |
| `OCR_LANG` | 识别语言 | `ch`（中英混合）/ `en` |

---

## 6. 启动服务

### 6.1 构建并启动（GPU 模式）

```bash
cd /opt/ocr

# 构建镜像并启动（首次需要较长时间）
docker compose up -d --build

# 查看启动状态
docker compose ps
```

### 6.2 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 只看后端日志
docker compose logs -f backend

# 只看最近 100 行
docker compose logs --tail 100 backend
```

### 6.3 等待服务就绪

首次启动时，后端需要下载 OCR 模型（约 2-3 GB），请耐心等待：

```bash
# 查看后端状态
docker compose logs -f backend

# 看到以下日志表示启动成功：
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 7. 验证部署

### 7.1 检查服务状态

```bash
docker compose ps
```

预期输出：

```
NAME            STATUS              PORTS
ocr-backend     Up (healthy)        0.0.0.0:8000->8000/tcp
ocr-frontend    Up (healthy)        0.0.0.0:80->80/tcp
ocr-postgres    Up (healthy)        0.0.0.0:5432->5432/tcp
ocr-redis       Up (healthy)        0.0.0.0:6379->6379/tcp
```

### 7.2 测试 API

```bash
# 健康检查
curl http://localhost:8000/api/health

# 预期返回
# {"status": "ok", "database": "connected", "redis": "connected"}
```

### 7.3 访问前端

浏览器打开：`http://服务器IP/`

### 7.4 测试 GPU（可选）

```bash
# 进入后端容器
docker compose exec backend bash

# 测试 PaddlePaddle GPU
python -c "import paddle; paddle.utils.run_check()"

# 退出容器
exit
```

---

## 8. 初始数据导入

如果有现有的归档数据需要导入：

### 8.1 上传数据文件

```bash
# 在服务器创建数据目录
mkdir -p /opt/ocr/data

# 上传 Excel 文件
scp archive.xls user@server:/opt/ocr/data/
```

### 8.2 执行导入

```bash
cd /opt/ocr

# 复制文件到容器
docker cp /opt/ocr/data/archive.xls ocr-backend:/app/data/

# 执行导入脚本
docker compose exec backend python init_archive_db.py /app/data/archive.xls

# 或使用环境变量方式
docker compose exec -e INIT_ARCHIVE_EXCEL_PATH=/app/data/archive.xls backend python init_archive_db.py
```

### 8.3 验证导入

```bash
# 连接数据库查看
docker compose exec postgres psql -U ocruser -d ocr_db -c "SELECT COUNT(*) FROM archive_records;"
```

---

## 9. 日常运维

### 9.1 服务管理

```bash
cd /opt/ocr

# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart backend

# 查看服务状态
docker compose ps

# 查看资源使用
docker stats
```

### 9.2 日志管理

```bash
# 实时查看日志
docker compose logs -f

# 查看指定服务日志
docker compose logs -f backend
docker compose logs -f postgres

# 查看最近 N 行
docker compose logs --tail 200 backend

# 查看指定时间段
docker compose logs --since "2026-03-30T10:00:00" backend
```

### 9.3 进入容器调试

```bash
# 进入后端容器
docker compose exec backend bash

# 进入数据库容器
docker compose exec postgres psql -U ocruser -d ocr_db

# 进入 Redis 容器
docker compose exec redis redis-cli
```

### 9.4 GPU 监控

```bash
# 宿主机查看 GPU
nvidia-smi

# 持续监控
watch -n 2 nvidia-smi
```

---

## 10. 数据备份与恢复

### 10.1 备份数据库

```bash
# 创建备份目录
mkdir -p /opt/ocr/backups

# 备份数据库
docker compose exec postgres pg_dump -U ocruser -d ocr_db -F c -f /tmp/backup.dump
docker cp ocr-postgres:/tmp/backup.dump /opt/ocr/backups/ocr_db_$(date +%Y%m%d_%H%M%S).dump
```

### 10.2 恢复数据库

```bash
# 复制备份文件到容器
docker cp /opt/ocr/backups/ocr_db_20260330.dump ocr-postgres:/tmp/backup.dump

# 恢复
docker compose exec postgres pg_restore -U ocruser -d ocr_db -c /tmp/backup.dump
```

### 10.3 备份上传文件

```bash
# 备份 uploads 卷
docker run --rm -v ocr_uploads:/data -v /opt/ocr/backups:/backup alpine \
    tar -czvf /backup/uploads_$(date +%Y%m%d).tar.gz -C /data .
```

### 10.4 自动备份脚本

创建 `/opt/ocr/backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR=/opt/ocr/backups
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker compose exec -T postgres pg_dump -U ocruser -d ocr_db -F c > $BACKUP_DIR/db_$DATE.dump

# 备份上传文件
docker run --rm -v ocr_uploads:/data -v $BACKUP_DIR:/backup alpine \
    tar -czvf /backup/uploads_$DATE.tar.gz -C /data .

# 清理 7 天前的备份
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

设置定时任务：

```bash
chmod +x /opt/ocr/backup.sh
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /opt/ocr/backup.sh >> /opt/ocr/backups/backup.log 2>&1
```

---

## 11. 更新部署

### 11.1 拉取最新代码

```bash
cd /opt/ocr
git pull origin main
```

### 11.2 重新构建并启动

```bash
# 停止服务
docker compose down

# 重新构建镜像
docker compose build --no-cache

# 启动服务
docker compose up -d

# 查看日志确认启动成功
docker compose logs -f
```

### 11.3 仅更新后端

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

### 11.4 仅更新前端

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

---

## 12. CPU 模式部署

如果服务器没有 GPU，可以使用 CPU 模式。

### 12.1 修改环境变量

编辑 `.env`：

```bash
OCR_USE_GPU=false
OCR_DEVICE=cpu
```

### 12.2 修改 docker-compose.yml

移除 GPU 相关配置：

```bash
vim docker-compose.yml
```

删除或注释掉 `backend` 服务中的 `deploy` 部分：

```yaml
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
```

### 12.3 使用 CPU 版 Dockerfile

创建 `Dockerfile.cpu`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 安装 CPU 版 PaddlePaddle
RUN pip install paddlepaddle==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/ && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY config.py main.py init_archive_db.py ./
COPY app/ ./app/

RUN mkdir -p /app/uploads /app/.cache /app/logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

修改 `docker-compose.yml` 中的 backend 构建配置：

```yaml
  backend:
    build:
      context: .
      dockerfile: Dockerfile.cpu  # 使用 CPU 版
```

### 12.4 启动 CPU 模式

```bash
docker compose up -d --build
```

---

## 13. 常见问题

### Q1：docker compose 命令找不到

**原因**：Docker Compose V2 是 Docker 的插件。

**解决**：
```bash
# 确认 Docker 版本
docker --version

# 如果是旧版，使用 docker-compose（带连字符）
docker-compose up -d

# 或重新安装 Docker（推荐）
```

### Q2：GPU 不可用 / CUDA 错误

**原因**：NVIDIA Container Toolkit 未正确安装。

**解决**：
```bash
# 检查驱动
nvidia-smi

# 重新安装 toolkit
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 测试
docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi
```

### Q3：后端启动很慢

**原因**：首次启动需要下载 OCR 模型（约 2-3 GB）。

**解决**：
```bash
# 查看下载进度
docker compose logs -f backend

# 模型会缓存到 ocr_cache 卷，后续启动会很快
```

### Q4：数据库连接失败

**原因**：PostgreSQL 容器未完全启动。

**解决**：
```bash
# 检查 postgres 状态
docker compose ps postgres

# 查看日志
docker compose logs postgres

# 等待健康检查通过后重启后端
docker compose restart backend
```

### Q5：端口被占用

**原因**：80 或其他端口已被使用。

**解决**：
```bash
# 查看端口占用
sudo lsof -i :80
sudo ss -tlnp | grep 80

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:80"  # 改用 8080
```

### Q6：磁盘空间不足

**原因**：Docker 镜像和卷占用空间。

**解决**：
```bash
# 查看 Docker 空间使用
docker system df

# 清理未使用的镜像和卷
docker system prune -a --volumes

# 查看各卷大小
docker system df -v
```

### Q7：前端页面 502 错误

**原因**：后端服务未启动或未就绪。

**解决**：
```bash
# 检查后端状态
docker compose ps backend

# 查看后端日志
docker compose logs backend

# 等待 "Application startup complete" 后刷新页面
```

### Q8：Redis 连接失败

**原因**：Redis 容器未启动。

**解决**：
```bash
# 检查 Redis 状态
docker compose ps redis

# 测试连接
docker compose exec redis redis-cli ping
# 应返回 PONG
```

### Q9：如何查看容器内文件

```bash
# 进入容器
docker compose exec backend bash

# 查看文件
ls -la /app/
ls -la /app/uploads/

# 退出
exit
```

### Q10：如何完全重置

```bash
cd /opt/ocr

# 停止并删除所有容器和卷
docker compose down -v

# 删除镜像
docker rmi $(docker images -q 'ocr-*')

# 重新构建
docker compose up -d --build
```

---

## 附录 A：文件结构

```
/opt/ocr/
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
├── .dockerignore           # Docker 构建忽略
├── Dockerfile              # 后端镜像（GPU）
├── Dockerfile.cpu          # 后端镜像（CPU，可选）
├── docker-compose.yml      # 编排配置
├── docker/
│   └── nginx/
│       └── default.conf    # Nginx 配置
├── frontend/
│   ├── Dockerfile          # 前端镜像
│   └── ...
├── app/                    # 后端代码
├── config.py
├── requirements.txt
├── backups/                # 备份目录
└── data/                   # 数据文件
```

---

## 附录 B：Docker 数据卷

| 卷名 | 挂载路径 | 说明 |
|------|----------|------|
| `ocr_postgres_data` | `/var/lib/postgresql/data` | 数据库文件 |
| `ocr_redis_data` | `/data` | Redis 持久化 |
| `ocr_uploads` | `/app/uploads` | 上传文件 |
| `ocr_cache` | `/app/.cache` | 模型缓存 |
| `ocr_logs` | `/app/logs` | 日志文件 |

查看卷位置：

```bash
docker volume inspect ocr_uploads
```

---

## 附录 C：快速命令参考

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 重启
docker compose restart

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 进入后端
docker compose exec backend bash

# 进入数据库
docker compose exec postgres psql -U ocruser -d ocr_db

# 重新构建
docker compose build --no-cache

# 更新部署
git pull && docker compose up -d --build
```

---

**文档结束**
