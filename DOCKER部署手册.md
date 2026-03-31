# OCR 项目 Docker 服务器部署手册（超详细版）

> 适用项目：`https://github.com/Zachary0612/OCR-WEB.git`
>
> 适用目标：将本项目从 **GitHub 仓库拉取代码** 后，部署到 **Linux 服务器**，并通过 **Docker / Docker Compose** 运行。
>
> 推荐操作系统：**Ubuntu 22.04 LTS**
>
> 推荐部署方式：**Docker Compose + PostgreSQL + Redis + App 容器**
>
> 推荐运行环境：**NVIDIA GPU 服务器**
>
> 本手册重点：**从 0 到 1 可落地、尽量少踩坑、把隐藏限制讲清楚**

---

## 目录

1. [先说结论：这个项目能不能 Docker 部署](#1-先说结论这个项目能不能-docker-部署)
2. [当前项目 Docker 化评估](#2-当前项目-docker-化评估)
3. [推荐部署架构](#3-推荐部署架构)
4. [部署前必须知道的 4 个关键限制](#4-部署前必须知道的-4-个关键限制)
5. [推荐服务器规格](#5-推荐服务器规格)
6. [服务器基础准备](#6-服务器基础准备)
7. [安装 Docker 与 Docker Compose](#7-安装-docker-与-docker-compose)
8. [GPU 服务器额外准备：NVIDIA Container Toolkit](#8-gpu-服务器额外准备nvidia-container-toolkit)
9. [规划部署目录](#9-规划部署目录)
10. [从 GitHub 拉取项目代码](#10-从-github-拉取项目代码)
11. [Docker 化前的源码兼容性调整建议](#11-docker-化前的源码兼容性调整建议)
12. [准备 Docker 部署文件](#12-准备-docker-部署文件)
13. [准备初始归档数据文件](#13-准备初始归档数据文件)
14. [构建镜像与启动容器](#14-构建镜像与启动容器)
15. [初始化数据库与导入初始数据](#15-初始化数据库与导入初始数据)
16. [首次访问与验证](#16-首次访问与验证)
17. [日常运维命令](#17-日常运维命令)
18. [更新代码后的发布流程](#18-更新代码后的发布流程)
19. [可选：增加 Nginx 反向代理](#19-可选增加-nginx-反向代理)
20. [常见问题排查](#20-常见问题排查)
21. [最终建议](#21-最终建议)

---

## 1. 先说结论：这个项目能不能 Docker 部署

**可以。**

但要先把话说完整：

- **这个项目的结构本身是适合 Docker 部署的**
  - 后端是 FastAPI
  - 前端是 Vue 3 + Vite
  - 数据库是 PostgreSQL
  - 缓存是 Redis
  - 前端构建后可以直接由后端静态托管

- **当前仓库里没有现成的 Dockerfile / docker-compose.yml**
  - 也就是说，仓库现在还不是“开箱即用”的 Docker 项目
  - 需要你按本文档新增 Docker 相关文件

- **当前仓库的关键 Docker 兼容层已经补齐**
  - `config.py` 已支持 `REDIS_URL`、`OCR_DEVICE`、`OCR_LANG`、`UPLOAD_DIR`、`CACHE_DIR`
  - `app/core/redis_cache.py` 已改为通过 `REDIS_URL` 连接 Redis
  - `app/core/ocr_engine.py` 已改为通过 `OCR_DEVICE` 切换 GPU / CPU
  - `init_archive_db.py` 已支持命令行参数或环境变量传入 Excel 路径

所以更准确的结论是：

**这个项目现在已经具备标准 Docker Compose 部署所需的核心源码兼容性；你下一步主要是补齐 Docker 文件并按本文档落地部署。**

---

## 2. 当前项目 Docker 化评估

根据当前仓库代码，结论如下。

### 2.1 已具备 Docker 化基础的部分

- **后端入口明确**
  - `main.py` 使用 `uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)`
  - 这意味着它天然适合容器内监听 `0.0.0.0:8000`

- **前端产物可由后端托管**
  - `frontend/vite.config.js` 中 `build.outDir = '../static/vue'`
  - `main.py` 中会读取 `static/vue/index.html`
  - 所以适合做成“前端先 build，后端统一对外提供服务”的单应用容器

- **数据库和缓存是标准外部依赖**
  - PostgreSQL
  - Redis
  - 这两者都非常适合用 Docker 官方镜像运行

- **模型与缓存可挂载持久化目录**
  - `config.py` 里会把模型缓存写到项目根目录下 `.cache`
  - 上传文件写到 `uploads`
  - 这些都可以映射成 Docker 卷或宿主机目录

### 2.2 需要特别注意的部分

- **Redis 已支持标准容器网络**
  - 当前代码已通过 `REDIS_URL` 读取 Redis 地址
  - 在 Docker Compose 里，直接设置为 `redis://redis:6379/0` 即可

- **OCR 设备已支持环境切换**
  - 当前代码已通过 `OCR_DEVICE` 控制 OCR 设备
  - GPU 服务器可用 `OCR_DEVICE=gpu:0`
  - CPU 测试环境可用 `OCR_DEVICE=cpu`

- **首次模型下载很慢**
  - PaddleOCR / PaddleX 首次运行时会下载模型
  - 这一步可能需要几分钟到几十分钟
  - 如果不挂载 `.cache`，容器重建后还会重新下载

- **初始归档数据脚本已支持容器路径**
  - `init_archive_db.py` 已支持命令行参数或 `INIT_ARCHIVE_EXCEL_PATH`
  - Docker 部署时仍需要把 Excel 文件挂载到容器内再执行导入

---

## 3. 推荐部署架构

推荐你采用下面这个结构。

```text
浏览器 / 内网客户端
        │
        │ HTTP / HTTPS
        ▼
   [可选 Nginx 容器]
        │
        ▼
   [App 容器]
   - FastAPI
   - 已构建好的 Vue 前端静态文件
   - OCR 服务
        │
        ├── [PostgreSQL 容器]
        ├── [Redis 容器]
        ├── [uploads 持久化目录]
        └── [.cache 模型缓存目录]
```

### 3.1 为什么推荐这种结构

- **前后端一起对外提供**，结构简单
- **数据库和缓存独立容器**，运维清晰
- **模型缓存与上传文件持久化**，避免数据丢失
- **后续加 Nginx、HTTPS、内网域名都方便**

### 3.2 本手册的推荐主路径

本手册默认你采用：

- **Ubuntu 22.04 LTS**
- **Docker Compose**
- **1 个 App 容器 + 1 个 PostgreSQL 容器 + 1 个 Redis 容器**
- **可选 1 个 Nginx 容器**
- **从 GitHub 拉取源码后，在服务器本地构建镜像**

---

## 4. 部署前必须知道的 4 个关键限制

这一节非常重要，请不要跳过。

### 4.1 限制一：Redis 已支持通过环境变量连接

当前文件：`config.py`、`app/core/redis_cache.py`

当前代码已经支持：

```python
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
```

以及：

```python
_redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
)
```

#### 这意味着什么

- 本机直装 Redis 时，默认仍可用
- Docker Compose 时，直接设 `REDIS_URL=redis://redis:6379/0`
- 以后换远程 Redis 也无需改源码

### 4.2 限制二：OCR 设备已支持 GPU / CPU 切换

当前文件：`config.py`、`app/core/ocr_engine.py`

当前代码已经支持：

```python
OCR_USE_GPU = os.getenv("OCR_USE_GPU", "true").lower() in {"1", "true", "yes", "on"}
OCR_DEVICE = os.getenv("OCR_DEVICE", "gpu:0" if OCR_USE_GPU else "cpu")
```

并在 OCR 初始化时统一使用：

```python
device=OCR_DEVICE
```

#### 这意味着什么

- GPU 服务器：`.env` 里设 `OCR_USE_GPU=true`、`OCR_DEVICE=gpu:0`
- CPU 服务器：`.env` 里设 `OCR_USE_GPU=false`、`OCR_DEVICE=cpu`
- 同一套代码可以在不同环境切换

### 4.3 限制三：初始数据导入脚本已支持参数化路径

当前文件：`init_archive_db.py`

当前脚本已经支持：

- 命令行参数传入 Excel 路径
- 环境变量 `INIT_ARCHIVE_EXCEL_PATH`
- 环境变量 `INIT_ARCHIVE_BATCH_ID`

#### 推荐用法

```bash
python init_archive_db.py /app/docker-init/归档文件目录（所需字段）.xls
```

#### 这意味着什么

- 不需要再手工改 Windows 写死路径
- Docker 容器里可以直接传容器内路径
- 更适合服务器批量部署

### 4.4 限制四：当前仓库里仍没有现成 Docker 文件

目前仓库里没有：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `docker/nginx/default.conf`

所以你必须自己新增这些文件，或者让我下一步直接帮你把这些文件补进仓库。

---

## 5. 推荐服务器规格

### 5.1 GPU 生产环境推荐

| 项目 | 最低 | 推荐 |
|------|------|------|
| CPU | 4 核 | 8 核以上 |
| 内存 | 16 GB | 32 GB |
| 磁盘 | 80 GB SSD | 200 GB SSD |
| GPU | 8 GB 显存 | 12 GB 及以上 |
| 操作系统 | Ubuntu 22.04 | Ubuntu 22.04 |

### 5.2 为什么推荐 GPU

当前项目使用：

- PP-OCRv5
- PP-StructureV3
- PaddleOCR-VL-1.5

这些模型在 CPU 上不是不能跑，但：

- 速度会明显下降
- 首次加载慢
- 实际体验差
- 容易误判为“项目有问题”

所以：

- **生产环境建议 GPU**
- **CPU 仅适合临时测试或演示**

---

## 6. 服务器基础准备

### 6.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget unzip ca-certificates gnupg lsb-release software-properties-common
```

### 6.2 检查服务器信息

```bash
cat /etc/os-release
nproc
free -h
df -h
```

### 6.3 如果是 GPU 服务器，检查显卡

```bash
nvidia-smi
```

如果这条命令都不能正常输出，请先不要继续 Docker 部署，先把显卡驱动装好。

---

## 7. 安装 Docker 与 Docker Compose

### 7.1 卸载旧版本（如果有）

```bash
sudo apt remove -y docker docker-engine docker.io containerd runc
```

### 7.2 添加 Docker 官方仓库

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 7.3 安装 Docker Engine 和 Compose

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 7.4 启动并设置开机自启

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker
```

### 7.5 把当前用户加入 docker 用户组

```bash
sudo usermod -aG docker $USER
```

执行后请重新登录一次服务器，或者执行：

```bash
newgrp docker
```

### 7.6 验证 Docker 是否正常

```bash
docker version
docker compose version
docker run --rm hello-world
```

---

## 8. GPU 服务器额外准备：NVIDIA Container Toolkit

> 如果你的服务器没有 GPU，可以跳过本节；后续只需要在 `.env` 中把 `OCR_USE_GPU=false`、`OCR_DEVICE=cpu`。

### 8.1 安装 NVIDIA Container Toolkit

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
&& curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
&& curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
```

### 8.2 配置 Docker 使用 NVIDIA Runtime

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 8.3 验证容器能不能拿到 GPU

```bash
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

如果这条命令能在容器里看到 GPU 信息，说明 Docker GPU 环境正常。

---

## 9. 规划部署目录

推荐统一放在 `/opt/ocr-docker`。

### 9.1 创建目录

```bash
sudo mkdir -p /opt/ocr-docker
sudo chown -R $USER:$USER /opt/ocr-docker
```

### 9.2 推荐目录结构

后续建议形成下面的结构：

```text
/opt/ocr-docker/
├── OCR-WEB/                    # GitHub 拉下来的项目代码
├── data/
│   ├── postgres/               # PostgreSQL 数据持久化
│   ├── redis/                  # Redis 数据持久化
│   ├── uploads/                # 上传文件持久化
│   ├── cache/                  # Paddle 模型缓存
│   └── init/                   # 初始归档 Excel 文件
└── docker/
    └── nginx/                  # 可选：Nginx 配置
```

### 9.3 创建这些目录

```bash
mkdir -p /opt/ocr-docker/data/postgres
mkdir -p /opt/ocr-docker/data/redis
mkdir -p /opt/ocr-docker/data/uploads
mkdir -p /opt/ocr-docker/data/cache
mkdir -p /opt/ocr-docker/data/init
mkdir -p /opt/ocr-docker/docker/nginx
```

---

## 10. 从 GitHub 拉取项目代码

### 10.1 克隆仓库

```bash
git clone https://github.com/Zachary0612/OCR-WEB.git /opt/ocr-docker/OCR-WEB
```

如果是私有仓库，请使用：

- SSH Key
- 或 Personal Access Token

### 10.2 进入项目目录

```bash
cd /opt/ocr-docker/OCR-WEB
```

### 10.3 查看远程分支

```bash
git branch -r
```

### 10.4 切换到你要部署的分支

下面示例假设你用 `main` 分支，若实际不是，请自己替换。

```bash
git checkout main
git pull origin main
```

### 10.5 建议记录当前提交号

```bash
git rev-parse --short HEAD
```

部署时把这个提交号记下来，后续出问题方便回溯。

---

## 11. Docker 化前的源码兼容性调整建议

这一节是本手册最关键的一节之一。

下面这些兼容性调整已经在当前仓库中完成，你部署时可以直接按本章的环境变量和命令使用。

---

### 11.1 `config.py` 已完成环境变量化

当前文件：`config.py`

建议把核心运行参数做成环境变量可控。

#### 推荐写法

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CACHE_DIR = Path(os.getenv("CACHE_DIR", str(BASE_DIR / ".cache")))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR / "huggingface")
os.environ["PADDLE_PDX_CACHE_HOME"] = str(CACHE_DIR / "paddlex")
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"
os.environ["FLAGS_json_format_model"] = "0"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:123456@localhost:5432/ocr_db"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024

OCR_USE_GPU = os.getenv("OCR_USE_GPU", "true").lower() in {"1", "true", "yes", "on"}
OCR_DEVICE = os.getenv("OCR_DEVICE", "gpu:0" if OCR_USE_GPU else "cpu")
OCR_LANG = os.getenv("OCR_LANG", "ch")
```

#### 这样做的意义

- `DATABASE_URL` 能连 PostgreSQL 容器
- `REDIS_URL` 能连 Redis 容器
- `CACHE_DIR` / `UPLOAD_DIR` 可直接挂载持久化目录
- `OCR_DEVICE` 可按 GPU / CPU 环境切换

---

### 11.2 `app/core/redis_cache.py` 已完成 Redis URL 化

当前文件：`app/core/redis_cache.py`

#### 推荐改法

```python
import json
import logging
from typing import Any

import redis
from config import REDIS_URL

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None

PREFIX = "ocr:"
TASK_TTL = 3600
LIST_TTL = 30
SEARCH_TTL = 120


def get_redis() -> redis.Redis | None:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
            logger.info("Redis 连接成功: %s", REDIS_URL)
        except Exception as e:
            logger.warning("Redis 连接失败，将不使用缓存: %s", e)
            _redis_client = None
    return _redis_client
```

#### 这样做的意义

- 本机部署时仍可用
- Docker Compose 时直接填 `REDIS_URL=redis://redis:6379/0`
- 以后换成远程 Redis 也方便

---

### 11.3 `app/core/ocr_engine.py` 已完成 OCR 设备环境变量化

当前文件：`app/core/ocr_engine.py`

#### 第一步：修改导入

把：

```python
from config import OCR_LANG, UPLOAD_DIR
```

改为：

```python
from config import OCR_LANG, OCR_DEVICE, UPLOAD_DIR
```

#### 第二步：把所有 `device="gpu:0"` 改成 `device=OCR_DEVICE`

需要修改的位置有 3 处：

- `PaddleOCR(...)`
- `create_pipeline(pipeline="layout_parsing", ...)`
- `create_pipeline(pipeline="PaddleOCR-VL-1.5", ...)`

#### 修改后的效果

- GPU 环境：`OCR_DEVICE=gpu:0`
- CPU 环境：`OCR_DEVICE=cpu`

---

### 11.4 `init_archive_db.py` 已支持命令行 / 环境变量传入 Excel 路径

当前脚本已经支持：

- `python init_archive_db.py /app/docker-init/归档文件目录（所需字段）.xls`
- `INIT_ARCHIVE_EXCEL_PATH=/app/docker-init/归档文件目录（所需字段）.xls python init_archive_db.py`
- `INIT_ARCHIVE_BATCH_ID=init_import`

这样更适合服务器部署，也不会污染本地路径配置。

---

### 11.5 关于 Python 依赖的提醒

当前 `requirements.txt` 里已包含：

- `paddlepaddle-gpu`
- `paddleocr`
- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `asyncpg`
- `openpyxl`
- `PyMuPDF`
- `redis`

但根据源码实际导入，你在 Docker 构建阶段仍应显式保证这些包可用：

- `numpy`
- `opencv-python-headless`
- `paddleocr[doc-parser]`

所以我在下面的 Dockerfile 示例里，会把这些额外依赖显式安装进去。

---

## 12. 准备 Docker 部署文件

本章默认你已经进入：

```bash
cd /opt/ocr-docker/OCR-WEB
```

### 12.1 创建 `.env`

在项目根目录新建 `.env` 文件：

```bash
nano .env
```

填入下面内容：

```env
TZ=Asia/Shanghai

POSTGRES_DB=ocr_db
POSTGRES_USER=ocruser
POSTGRES_PASSWORD=PleaseChangeThisStrongPassword

DATABASE_URL=postgresql+asyncpg://ocruser:PleaseChangeThisStrongPassword@postgres:5432/ocr_db
REDIS_URL=redis://redis:6379/0

OCR_USE_GPU=true
OCR_DEVICE=gpu:0
OCR_LANG=ch

UPLOAD_DIR=/app/uploads
CACHE_DIR=/app/.cache
```

#### 说明

- `POSTGRES_PASSWORD` 请替换成你自己的强密码
- `OCR_DEVICE=gpu:0` 适用于 GPU 服务器
- 如果你后续改成 CPU 测试，设成：`OCR_DEVICE=cpu`

---

### 12.2 创建 `.dockerignore`

新建：`.dockerignore`

```bash
nano .dockerignore
```

写入：

```text
.git
.gitignore
.venv
__pycache__
*.pyc
*.pyo
*.pyd
node_modules
frontend/node_modules
uploads
.cache
static/vue
```

#### 为什么要有这个文件

否则 Docker 构建时可能把你本地虚拟环境、缓存、前端依赖全带进去，导致：

- 构建慢
- 镜像大
- 局部环境污染

---

### 12.3 创建 `Dockerfile`

新建：`Dockerfile`

```bash
nano Dockerfile
```

写入下面内容：

```dockerfile
# syntax=docker/dockerfile:1.7

FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS app

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    ca-certificates \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && ln -sf /usr/bin/python3.12 /usr/local/bin/python \
    && ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN grep -v '^paddlepaddle-gpu' requirements.txt > requirements.docker.txt \
    && pip install --upgrade pip setuptools wheel \
    && pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/ \
    && pip install -r requirements.docker.txt \
    && pip install redis numpy opencv-python-headless "paddleocr[doc-parser]"

COPY . .
COPY --from=frontend-builder /static/vue ./static/vue

EXPOSE 8000

CMD ["python", "main.py"]
```

#### 这份 Dockerfile 做了什么

- 第一阶段：用 Node 20 构建前端
- 第二阶段：用 NVIDIA CUDA Runtime 作为运行底座
- 安装 Python 3.12
- 安装 PaddlePaddle GPU + 其余依赖
- 构建完成后，把前端静态文件复制到后端的 `static/vue`
- 启动时直接运行 `python main.py`

#### 为什么前端复制路径是 `/static/vue`

因为你的 `vite.config.js` 里：

```js
build: {
  outDir: '../static/vue',
}
```

也就是说在前端构建阶段，产物会被输出到构建容器中的 `/static/vue`。

---

### 12.4 创建 `docker-compose.yml`

新建：`docker-compose.yml`

```bash
nano docker-compose.yml
```

写入下面内容：

```yaml
services:
  postgres:
    image: postgres:16
    container_name: ocr-postgres
    restart: unless-stopped
    environment:
      TZ: ${TZ}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - /opt/ocr-docker/data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: ocr-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - /opt/ocr-docker/data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ocr-app
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      TZ: ${TZ}
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      OCR_USE_GPU: ${OCR_USE_GPU}
      OCR_DEVICE: ${OCR_DEVICE}
      OCR_LANG: ${OCR_LANG}
      UPLOAD_DIR: ${UPLOAD_DIR}
      CACHE_DIR: ${CACHE_DIR}
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility
    ports:
      - "8000:8000"
    volumes:
      - /opt/ocr-docker/data/uploads:/app/uploads
      - /opt/ocr-docker/data/cache:/app/.cache
      - /opt/ocr-docker/data/init:/app/docker-init
    gpus: all
```

#### 说明

- `postgres` 和 `redis` 不对外暴露端口，更安全
- `app` 对外暴露 `8000`
- `uploads`、`.cache`、`init` 都映射到了宿主机目录
- `gpus: all` 表示把宿主机 GPU 暴露给应用容器

#### 如果你是 CPU 服务器

把 `app` 里的这两块去掉：

```yaml
gpus: all
```

和：

```yaml
NVIDIA_VISIBLE_DEVICES: all
NVIDIA_DRIVER_CAPABILITIES: compute,utility
```

同时把 `.env` 中：

```env
OCR_USE_GPU=false
OCR_DEVICE=cpu
```

并且要把 `Dockerfile` 里的 Paddle 安装部分改成 CPU 版本，见第 20 章问题排查。

---

## 13. 准备初始归档数据文件

这个步骤非常重要。

如果你不导入初始归档数据，后续系统里涉及 `init_import` 的归档目录导出功能就不完整。

### 13.1 把 Excel 文件放到宿主机目录

把你的 Excel 文件：

```text
归档文件目录（所需字段）.xls
```

放到：

```text
/opt/ocr-docker/data/init/
```

放好后应为：

```text
/opt/ocr-docker/data/init/归档文件目录（所需字段）.xls
```

### 13.2 检查文件是否真的在位

```bash
ls -lh /opt/ocr-docker/data/init
```

你应该能看到这个文件名。

---

## 14. 构建镜像与启动容器

### 14.1 先检查 Compose 文件有没有语法错误

```bash
cd /opt/ocr-docker/OCR-WEB
docker compose config
```

如果这条命令输出的是合并后的配置，而不是报错，说明 Compose 语法基本没问题。

### 14.2 开始构建镜像

```bash
docker compose build app
```

#### 第一次构建会比较慢

因为它会：

- 安装 Python 3.12
- 安装 PaddlePaddle GPU
- 安装 PaddleOCR 相关依赖
- 构建 Vue 前端

如果网络一般，第一次可能要几十分钟。

### 14.3 启动全部服务

```bash
docker compose up -d
```

### 14.4 查看容器状态

```bash
docker compose ps
```

正常情况下你应该看到：

- `ocr-postgres` 为 `running`
- `ocr-redis` 为 `running`
- `ocr-app` 为 `running`

### 14.5 查看应用日志

```bash
docker compose logs -f app
```

你应该至少能看到类似意思的日志：

```text
正在初始化数据库...
数据库初始化完成
服务就绪！模型将在首次使用时自动加载。
```

#### 注意

项目本身是“模型懒加载”的。

也就是说：

- 容器启动成功
- 不代表模型已经下载好了
- 模型通常在**第一次真正发起 OCR 请求时**才开始加载 / 下载

这是正常现象。

---

## 15. 初始化数据库与导入初始数据

### 15.1 数据库表会在应用启动时自动初始化

`main.py` 的生命周期里会调用：

```python
await init_db()
```

所以数据库表一般不需要你额外手工建。

### 15.2 用脚本直接导入初始归档数据

这一招的好处是：

- 当前仓库已经支持命令行传入 Excel 路径
- 直接在容器里导入
- 更适合 Docker 环境

在项目目录执行：

```bash
docker compose exec app python init_archive_db.py "/app/docker-init/归档文件目录（所需字段）.xls"
```

默认批次号就是 `init_import`。

如果你想显式指定批次号，可以执行：

```bash
docker compose exec -e INIT_ARCHIVE_BATCH_ID=init_import app python init_archive_db.py "/app/docker-init/归档文件目录（所需字段）.xls"
```

### 15.3 验证导入结果

执行：

```bash
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT COUNT(*) FROM archive_records WHERE batch_id='init_import';"
```

#### 期望结果

如果一切正常，结果应该是：

```text
23
```

如果不是 23，请检查：

- Excel 文件路径是否正确
- 文件名是否一致
- 表结构是否初始化成功
- 导入命令是否执行成功

### 15.4 如果重复导入了怎么办

可以先清除旧的初始批次数据：

```bash
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "DELETE FROM archive_records WHERE batch_id='init_import';"
```

然后重新执行导入命令。

---

## 16. 首次访问与验证

### 16.1 直接访问应用

如果你没有加 Nginx，直接浏览器打开：

```text
http://服务器IP:8000
```

### 16.2 验证接口

你也可以先测接口：

```bash
curl http://127.0.0.1:8000/docs
```

如果返回 FastAPI 文档页面对应的 HTML，说明服务正常。

### 16.3 第一次 OCR 请求为什么会慢

因为第一次真正发起识别时，系统可能会：

- 下载模型
- 初始化 PaddleOCR
- 初始化版面解析管线
- 初始化 VL 管线

#### 这一步可能持续多久

- 几分钟
- 十几分钟
- 网络差时更久

#### 为什么一定要挂载 `.cache`

因为模型下载后会放到：

```text
/app/.cache
```

如果这个目录不做持久化映射：

- 容器重建后模型缓存丢失
- 下次又要重新下载

### 16.4 你应该重点验证什么

建议按下面顺序验证：

- **页面能打开**
- **上传单个文件能识别**
- **上传 PDF 能识别**
- **历史列表能看到记录**
- **全文搜索正常**
- **批量识别完成后 Excel 导出正常**
- **`init_import` 的归档目录数据已存在**

---

## 17. 日常运维命令

### 17.1 查看容器状态

```bash
docker compose ps
```

### 17.2 查看应用日志

```bash
docker compose logs -f app
```

### 17.3 查看数据库日志

```bash
docker compose logs -f postgres
```

### 17.4 查看 Redis 日志

```bash
docker compose logs -f redis
```

### 17.5 重启应用容器

```bash
docker compose restart app
```

### 17.6 停止全部服务

```bash
docker compose down
```

### 17.7 停止并删除容器、网络、匿名卷

```bash
docker compose down -v
```

> **注意：** `-v` 可能删除卷数据。若你用的是宿主机目录映射，数据一般还在；但仍不建议乱用。

### 17.8 进入应用容器

```bash
docker compose exec app bash
```

如果镜像里没有 `bash`，就改用：

```bash
docker compose exec app sh
```

### 17.9 进入 PostgreSQL 命令行

```bash
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

---

## 18. 更新代码后的发布流程

以后你改了代码，重新部署建议按下面流程做。

### 18.1 拉取最新代码

```bash
cd /opt/ocr-docker/OCR-WEB
git pull origin main
```

如果你不是 `main` 分支，请改成你的实际分支名。

### 18.2 重新构建应用镜像

```bash
docker compose build app
```

### 18.3 重启应用服务

```bash
docker compose up -d app
```

### 18.4 查看日志确认启动成功

```bash
docker compose logs -f app
```

### 18.5 如果前端也改了，会不会自动更新

会。

因为当前 Dockerfile 在构建阶段会重新执行：

- `npm install`
- `npm run build`

构建后的前端静态文件会被重新复制到镜像里的 `static/vue`。

---

## 19. 可选：增加 Nginx 反向代理

如果你只是内网临时使用，直接暴露 `8000` 端口也可以。

但如果你希望：

- 用标准 `80/443` 端口访问
- 配 HTTPS
- 做统一入口
- 以后挂内网域名

建议加一个 Nginx 容器。

### 19.1 新建 Nginx 配置文件

新建：`/opt/ocr-docker/docker/nginx/default.conf`

```bash
nano /opt/ocr-docker/docker/nginx/default.conf
```

写入：

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 100m;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 19.2 在 `docker-compose.yml` 中增加 `nginx` 服务

```yaml
  nginx:
    image: nginx:1.27-alpine
    container_name: ocr-nginx
    restart: unless-stopped
    depends_on:
      - app
    volumes:
      - /opt/ocr-docker/docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - "80:80"
```

### 19.3 启动 Nginx

```bash
docker compose up -d nginx
```

之后你就可以用：

```text
http://服务器IP
```

直接访问。

---

## 20. 常见问题排查

这一节建议你部署时开着看。

---

### 20.1 问题：`docker compose build app` 非常慢

#### 原因

- Paddle 依赖体积大
- 前端依赖多
- 网络到某些源不稳定

#### 处理方法

- 服务器尽量能访问官方源
- 第一次构建耐心等待
- 镜像成功构建后，后续会快很多

---

### 20.2 问题：应用容器启动后，日志里提示 Redis 连接失败

#### 高概率原因

- `.env` 中 `REDIS_URL` 仍指向本机地址
- Compose 服务名不是 `redis`
- 你运行的镜像不是最新构建版本

#### 处理方法

- 检查 `.env` 中是否为 `REDIS_URL=redis://redis:6379/0`
- 重新执行 `docker compose build app`
- 再执行 `docker compose up -d app`

---

### 20.3 问题：应用容器启动后，OCR 请求时报 GPU 相关错误

#### 高概率原因

- 服务器没 GPU
- Docker 没装 NVIDIA Container Toolkit
- 容器没拿到 GPU
- `.env` 中 `OCR_DEVICE` 配置不正确
- 你运行的镜像不是最新构建版本

#### 排查顺序

1. 宿主机执行：

```bash
nvidia-smi
```

2. 容器测试执行：

```bash
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

3. 检查 `.env`：

```env
OCR_USE_GPU=true
OCR_DEVICE=gpu:0
```

4. 重新构建并重启应用容器：

```bash
docker compose build app
docker compose up -d app
```

---

### 20.4 问题：服务器没 GPU，能不能先 CPU 跑

#### 可以，而且当前源码已经支持

- `.env` 中设置：
  - `OCR_USE_GPU=false`
  - `OCR_DEVICE=cpu`

- 重新构建并启动应用：

```bash
docker compose build app
docker compose up -d app
```

#### 同时还要改 Dockerfile 的 Paddle 安装

把：

```dockerfile
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/
```

改为：

```dockerfile
pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

#### 还建议把运行底座换成 Python 基础镜像

GPU 版本 Dockerfile 用的是：

```dockerfile
nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04
```

如果你只跑 CPU，建议换成：

```dockerfile
python:3.12-slim-bookworm
```

这样镜像会更轻。

---

### 20.5 问题：页面能打开，但第一次识别特别慢

#### 这是正常的

因为第一次真正 OCR 时才会：

- 下载模型
- 初始化识别引擎
- 初始化版面解析管线
- 初始化 VL 模型

#### 处理方法

- 看 `docker compose logs -f app`
- 观察是否在下载模型 / 初始化模型
- 只要不是报错，先等

---

### 20.6 问题：容器重建后又重新下载模型

#### 原因

`.cache` 没持久化。

#### 正确做法

确保 Compose 里有：

```yaml
volumes:
  - /opt/ocr-docker/data/cache:/app/.cache
```

---

### 20.7 问题：上传过的文件重启后没了

#### 原因

`uploads` 没持久化。

#### 正确做法

确保 Compose 里有：

```yaml
volumes:
  - /opt/ocr-docker/data/uploads:/app/uploads
```

---

### 20.8 问题：批量导出 `归档目录.xlsx` 时 404

#### 高概率原因

你没有导入 `init_import` 这批初始数据。

#### 处理方法

按第 15 章执行初始导入。

---

### 20.9 问题：前端页面空白或样式丢失

#### 高概率原因

前端构建产物没有正确复制到：

```text
/app/static/vue
```

#### 检查方法

进入容器：

```bash
docker compose exec app bash
ls -lah /app/static/vue
```

如果里面没有 `index.html`，说明 Dockerfile 前端构建或复制路径有问题。

---

### 20.10 问题：`pip install -r requirements.txt` 相关步骤在镜像构建时失败

#### 原因分析

当前项目的依赖包含：

- PaddlePaddle
- PaddleOCR
- doc-parser 扩展
- OpenCV
- numpy

这类依赖对网络、Python 版本、系统库比较敏感。

#### 处理建议

- 确保 Python 使用 3.12
- 优先使用本文档里的 Dockerfile，不要随便改底座镜像
- 若某个包单独失败，可以进入构建日志中找具体报错

---

### 20.11 问题：为什么我不推荐 Windows Server 做 Docker 主路径

不是说绝对不行，而是：

- GPU 容器链路更复杂
- Paddle 相关依赖在 Linux 下更成熟
- Docker + NVIDIA + Python + OCR 在 Ubuntu 上更稳
- 你的现有部署文档主路径本来也偏 Linux

所以：

**如果你追求稳定上线，优先用 Ubuntu 服务器。**

---

## 21. 最终建议

如果你问我：

**这个项目能不能用 Docker 在服务器上部署，并且代码从 GitHub 拉取？**

我的答案是：

**能，而且非常值得这么做。**

但我更建议你按下面思路推进：

### 21.1 推荐落地顺序

- **第一步**：先在 Ubuntu GPU 服务器上按本文档完成部署
- **第二步**：按本文档补齐 `Dockerfile`、`docker-compose.yml`、`.dockerignore` 等文件
- **第三步**：配置 `.env`，重点确认 `DATABASE_URL`、`REDIS_URL`、`OCR_DEVICE`
- **第四步**：执行 `docker compose build app && docker compose up -d`
- **第五步**：验证单文件识别、批量识别、历史搜索、Excel 导出
- **第六步**：导入初始归档数据，再考虑 Nginx / HTTPS / 域名 / 备份策略

### 21.2 我对当前项目 Docker 化的判断

- **技术上可行**：是
- **适合生产化部署**：是
- **当前仓库是否已具备 Docker 兼容源码基础**：是
- **当前仓库是否已开箱即用**：否（仍缺 Docker 文件）
- **当前还需补齐什么**：`Dockerfile`、`docker-compose.yml`、`.dockerignore`、`docker/nginx/default.conf`

### 21.3 下一步如果你愿意，我建议我继续帮你做的事

我可以继续直接帮你把下面这些文件**真正补进仓库**，这样你就不是只有文档，而是直接有可提交到 GitHub 的 Docker 部署支持：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `docker/nginx/default.conf`

如果你下一步让我继续，我建议直接做成：

**“提交一套可直接 `docker compose up -d` 的完整 Docker 化配置”**。
