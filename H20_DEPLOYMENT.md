# NVIDIA H20 GPU 服务器部署手册

> **适用场景**：在搭载 NVIDIA H20 GPU 的 Linux 服务器上从零部署 OCR 档案识别系统  
> **预计耗时**：2-3 小时（含模型首次下载）  
> **最后更新**：2026-03-30

---

## 目录

1. [系统要求](#1-系统要求)
2. [服务器环境准备](#2-服务器环境准备)
3. [NVIDIA 驱动与 CUDA 安装](#3-nvidia-驱动与-cuda-安装)
4. [cuDNN 安装](#4-cudnn-安装)
5. [PostgreSQL 数据库安装](#5-postgresql-数据库安装)
6. [Redis 缓存安装](#6-redis-缓存安装)
7. [Python 环境配置](#7-python-环境配置)
8. [项目代码部署](#8-项目代码部署)
9. [后端服务配置](#9-后端服务配置)
10. [前端构建与部署](#10-前端构建与部署)
11. [Nginx 反向代理配置](#11-nginx-反向代理配置)
12. [SSL 证书配置（可选）](#12-ssl-证书配置可选)
13. [初始数据导入](#13-初始数据导入)
14. [服务验证](#14-服务验证)
15. [systemd 服务管理](#15-systemd-服务管理)
16. [日志管理](#16-日志管理)
17. [备份与恢复](#17-备份与恢复)
18. [性能优化](#18-性能优化)
19. [常见问题排查](#19-常见问题排查)
20. [运维命令速查](#20-运维命令速查)

---

## 1. 系统要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **GPU** | NVIDIA H20 × 1 | NVIDIA H20 × 1 |
| **CPU** | 8 核 | 16 核及以上 |
| **内存** | 32 GB | 64 GB 及以上 |
| **系统盘** | 100 GB SSD | 200 GB NVMe SSD |
| **数据盘** | 500 GB | 1 TB 及以上 |
| **网络** | 100 Mbps | 1 Gbps |

### 1.2 软件要求

| 软件 | 版本要求 |
|------|----------|
| **操作系统** | Ubuntu 22.04 LTS (推荐) / Ubuntu 20.04 LTS |
| **NVIDIA 驱动** | ≥ 535.x |
| **CUDA** | 12.x (推荐 12.2 或 12.4) |
| **cuDNN** | 8.9.x |
| **Python** | 3.10.x |
| **PostgreSQL** | 14.x / 15.x |
| **Redis** | 7.x |
| **Node.js** | 18.x LTS / 20.x LTS |
| **Nginx** | 1.18+ |

### 1.3 NVIDIA H20 GPU 特性

NVIDIA H20 是专为中国市场设计的数据中心 GPU：

- **显存**：96 GB HBM3
- **算力**：适合大规模 AI 推理
- **CUDA 核心**：充足的并行计算能力
- **功耗**：约 400W TDP

> **重要**：H20 完全兼容标准 CUDA 工具链，本项目的 PaddlePaddle GPU 版本可直接运行。

### 1.4 端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx (HTTP) | 80 | 前端入口 |
| Nginx (HTTPS) | 443 | HTTPS 入口（可选） |
| 后端 API | 8000 | FastAPI 服务 |
| 前端开发 | 3000 | 仅开发时使用 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

---

## 2. 服务器环境准备

### 2.1 系统更新

```bash
# 更新软件包列表
sudo apt update

# 升级已安装的软件包
sudo apt upgrade -y

# 安装基础工具
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    tmux \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

### 2.2 创建项目用户（推荐）

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash ocruser

# 设置密码
sudo passwd ocruser

# 添加到 sudo 组（可选，用于调试）
sudo usermod -aG sudo ocruser

# 创建项目目录
sudo mkdir -p /opt/ocr
sudo chown ocruser:ocruser /opt/ocr
```

### 2.3 配置时区

```bash
# 设置时区为中国时区
sudo timedatectl set-timezone Asia/Shanghai

# 验证
timedatectl
```

### 2.4 配置系统限制

编辑 `/etc/security/limits.conf`，添加：

```bash
sudo tee -a /etc/security/limits.conf << 'EOF'
# OCR 服务优化
ocruser soft nofile 65535
ocruser hard nofile 65535
ocruser soft nproc 65535
ocruser hard nproc 65535
EOF
```

### 2.5 配置 swap（如果内存不足）

```bash
# 检查当前 swap
free -h

# 如果没有 swap，创建 16GB swap 文件
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. NVIDIA 驱动与 CUDA 安装

### 3.1 检查 GPU 状态

```bash
# 查看 GPU 硬件
lspci | grep -i nvidia

# 预期输出类似：
# 3b:00.0 3D controller: NVIDIA Corporation Device 2331 (rev a1)
```

### 3.2 禁用 Nouveau 驱动

```bash
# 检查 nouveau 是否加载
lsmod | grep nouveau

# 如果有输出，需要禁用
sudo tee /etc/modprobe.d/blacklist-nouveau.conf << 'EOF'
blacklist nouveau
options nouveau modeset=0
EOF

# 更新 initramfs
sudo update-initramfs -u

# 重启服务器
sudo reboot
```

### 3.3 安装 NVIDIA 驱动

**方法一：使用 Ubuntu 官方驱动（推荐）**

```bash
# 查看推荐驱动
ubuntu-drivers devices

# 自动安装推荐驱动
sudo ubuntu-drivers autoinstall

# 或手动指定版本（H20 推荐 535 或更高）
sudo apt install -y nvidia-driver-535
```

**方法二：使用 NVIDIA 官方 .run 文件**

```bash
# 下载驱动（从 NVIDIA 官网获取最新版本）
wget https://cn.download.nvidia.com/tesla/535.154.05/NVIDIA-Linux-x86_64-535.154.05.run

# 安装依赖
sudo apt install -y linux-headers-$(uname -r)

# 运行安装
sudo chmod +x NVIDIA-Linux-x86_64-535.154.05.run
sudo ./NVIDIA-Linux-x86_64-535.154.05.run
```

### 3.4 验证驱动安装

```bash
# 重启后验证
sudo reboot

# 查看 GPU 信息
nvidia-smi
```

**预期输出**：

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.154.05   Driver Version: 535.154.05   CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA H20          On   | 00000000:3B:00.0 Off |                    0 |
| N/A   32C    P0    72W / 400W |      0MiB / 98304MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### 3.5 安装 CUDA Toolkit

```bash
# 添加 NVIDIA CUDA 仓库
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update

# 安装 CUDA 12.2（与 H20 驱动兼容）
sudo apt install -y cuda-toolkit-12-2

# 或安装完整 CUDA（包含驱动，如果上面没装驱动）
# sudo apt install -y cuda-12-2
```

### 3.6 配置 CUDA 环境变量

```bash
# 添加到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# CUDA 环境变量
export CUDA_HOME=/usr/local/cuda-12.2
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
EOF

# 立即生效
source ~/.bashrc

# 验证
nvcc --version
```

**预期输出**：

```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Tue_Aug_15_22:02:13_PDT_2023
Cuda compilation tools, release 12.2, V12.2.140
```

---

## 4. cuDNN 安装

### 4.1 下载 cuDNN

从 [NVIDIA cuDNN 下载页面](https://developer.nvidia.com/cudnn) 下载对应版本（需要 NVIDIA 账号）。

选择：**cuDNN v8.9.x for CUDA 12.x** → **Local Installer for Linux x86_64 (Tar)**

### 4.2 安装 cuDNN

```bash
# 解压（假设下载到 ~/Downloads）
cd ~/Downloads
tar -xvf cudnn-linux-x86_64-8.9.7.29_cuda12-archive.tar.xz

# 复制文件到 CUDA 目录
sudo cp cudnn-linux-x86_64-8.9.7.29_cuda12-archive/include/cudnn*.h /usr/local/cuda-12.2/include/
sudo cp cudnn-linux-x86_64-8.9.7.29_cuda12-archive/lib/libcudnn* /usr/local/cuda-12.2/lib64/

# 设置权限
sudo chmod a+r /usr/local/cuda-12.2/include/cudnn*.h
sudo chmod a+r /usr/local/cuda-12.2/lib64/libcudnn*

# 更新链接器缓存
sudo ldconfig
```

### 4.3 验证 cuDNN

```bash
# 检查 cuDNN 版本
cat /usr/local/cuda-12.2/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
```

---

## 5. PostgreSQL 数据库安装

### 5.1 安装 PostgreSQL 15

```bash
# 添加官方仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# 导入仓库签名
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 更新并安装
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15
```

### 5.2 启动并设置开机自启

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

### 5.3 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 psql 中执行以下命令
```

```sql
-- 创建数据库用户（修改密码！）
CREATE USER ocruser WITH PASSWORD 'YourStrongPassword123!';

-- 创建数据库
CREATE DATABASE ocr_db OWNER ocruser;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE ocr_db TO ocruser;

-- 允许创建扩展（如果需要）
ALTER USER ocruser CREATEDB;

-- 退出
\q
```

### 5.4 配置远程访问（如需）

编辑 `/etc/postgresql/15/main/postgresql.conf`：

```bash
sudo vim /etc/postgresql/15/main/postgresql.conf

# 修改监听地址（默认只监听 localhost）
listen_addresses = 'localhost'  # 如需远程访问改为 '*'
```

编辑 `/etc/postgresql/15/main/pg_hba.conf`：

```bash
sudo vim /etc/postgresql/15/main/pg_hba.conf

# 如需远程访问，添加：
# host    ocr_db    ocruser    0.0.0.0/0    scram-sha-256
```

```bash
# 重启 PostgreSQL
sudo systemctl restart postgresql
```

### 5.5 验证数据库连接

```bash
# 测试连接
psql -h localhost -U ocruser -d ocr_db -c "SELECT version();"

# 输入密码后应显示 PostgreSQL 版本信息
```

---

## 6. Redis 缓存安装

### 6.1 安装 Redis 7

```bash
# 添加官方仓库
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# 安装
sudo apt update
sudo apt install -y redis
```

### 6.2 配置 Redis

编辑 `/etc/redis/redis.conf`：

```bash
sudo vim /etc/redis/redis.conf
```

修改以下配置：

```conf
# 绑定地址（本机访问）
bind 127.0.0.1 -::1

# 端口
port 6379

# 后台运行
daemonize yes

# 最大内存（根据服务器配置调整）
maxmemory 2gb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 持久化配置
appendonly yes
appendfilename "appendonly.aof"

# 日志级别
loglevel notice
logfile /var/log/redis/redis-server.log
```

### 6.3 启动 Redis

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

### 6.4 验证 Redis

```bash
redis-cli ping
# 应返回: PONG

redis-cli info server | head -5
```

---

## 7. Python 环境配置

### 7.1 安装 Python 3.10

```bash
# Ubuntu 22.04 自带 Python 3.10
python3 --version

# 如果版本不对或没有，安装
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# 安装 pip
sudo apt install -y python3-pip
```

### 7.2 创建虚拟环境

```bash
# 切换到项目目录
cd /opt/ocr

# 创建虚拟环境
python3.10 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

### 7.3 配置 pip 镜像（加速下载）

```bash
# 创建 pip 配置
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
EOF
```

---

## 8. 项目代码部署

### 8.1 克隆代码

```bash
# 确保在项目目录
cd /opt/ocr

# 从 GitHub 克隆（替换为你的仓库地址）
git clone https://github.com/YOUR_USERNAME/OCR.git .

# 或者如果目录非空，先清理
# rm -rf /opt/ocr/*
# git clone https://github.com/YOUR_USERNAME/OCR.git .
```

### 8.2 创建必要目录

```bash
cd /opt/ocr

# 创建上传目录
mkdir -p uploads

# 创建缓存目录
mkdir -p .cache

# 创建日志目录
mkdir -p logs

# 设置权限
chmod 755 uploads .cache logs
```

### 8.3 安装 Python 依赖

```bash
# 确保虚拟环境已激活
source /opt/ocr/.venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> **注意**：`paddlepaddle-gpu` 会自动下载约 2-3 GB，首次安装需要较长时间。

### 8.4 验证 PaddlePaddle GPU

```bash
# 测试 PaddlePaddle GPU
python -c "import paddle; paddle.utils.run_check()"
```

**预期输出**：

```
Running verify PaddlePaddle program ...
W0330 14:00:00.000000 12345 gpu_resources.cc:119] Please NOTE: device: 0, GPU Compute Capability: 9.0, Driver API Version: 12.2, Runtime API Version: 12.2
W0330 14:00:00.000000 12345 gpu_resources.cc:164] device: 0, cuDNN Version: 8.9.
PaddlePaddle works well on 1 GPU.
PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
```

### 8.5 配置环境变量

创建 `/opt/ocr/.env` 文件：

```bash
cat > /opt/ocr/.env << 'EOF'
# 数据库配置（修改密码！）
DATABASE_URL=postgresql+asyncpg://ocruser:YourStrongPassword123!@localhost:5432/ocr_db

# Redis 配置
REDIS_URL=redis://127.0.0.1:6379/0

# 目录配置
UPLOAD_DIR=/opt/ocr/uploads
CACHE_DIR=/opt/ocr/.cache

# OCR 配置（H20 GPU）
OCR_USE_GPU=true
OCR_DEVICE=gpu:0
OCR_LANG=ch

# 初始数据导入配置（可选）
INIT_ARCHIVE_EXCEL_PATH=/opt/ocr/data/archive.xls
INIT_ARCHIVE_BATCH_ID=init_import
EOF
```

### 8.6 加载环境变量

在 `.bashrc` 中添加自动加载：

```bash
echo 'set -a; source /opt/ocr/.env; set +a' >> ~/.bashrc
source ~/.bashrc
```

---

## 9. 后端服务配置

### 9.1 初始化数据库

```bash
cd /opt/ocr
source .venv/bin/activate

# 加载环境变量
set -a; source .env; set +a

# 运行数据库迁移（如果有 Alembic）
# alembic upgrade head

# 或者通过 FastAPI 启动时自动创建表
python -c "
from app.database import engine, Base
import asyncio

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('数据库表创建完成')

asyncio.run(init())
"
```

### 9.2 测试后端启动

```bash
cd /opt/ocr
source .venv/bin/activate
set -a; source .env; set +a

# 手动启动测试
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 看到以下输出表示成功：
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

按 `Ctrl+C` 停止测试。

### 9.3 创建 systemd 服务

```bash
sudo tee /etc/systemd/system/ocr.service << 'EOF'
[Unit]
Description=OCR Archive Recognition Service
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=ocruser
Group=ocruser
WorkingDirectory=/opt/ocr
Environment="PATH=/opt/ocr/.venv/bin:/usr/local/cuda-12.2/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/ocr/.env

# 启动命令
ExecStart=/opt/ocr/.venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log

# 重启策略
Restart=always
RestartSec=5

# 资源限制
LimitNOFILE=65535
LimitNPROC=65535

# 日志
StandardOutput=append:/opt/ocr/logs/uvicorn.log
StandardError=append:/opt/ocr/logs/uvicorn.error.log

[Install]
WantedBy=multi-user.target
EOF
```

### 9.4 启动后端服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ocr

# 设置开机自启
sudo systemctl enable ocr

# 查看状态
sudo systemctl status ocr
```

---

## 10. 前端构建与部署

### 10.1 安装 Node.js 20

```bash
# 使用 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node --version  # v20.x.x
npm --version   # 10.x.x
```

### 10.2 安装 pnpm（推荐）

```bash
npm install -g pnpm
pnpm --version
```

### 10.3 构建前端

```bash
cd /opt/ocr/frontend

# 安装依赖
pnpm install
# 或 npm install

# 配置 API 地址（生产环境）
cat > .env.production << 'EOF'
VITE_API_BASE_URL=/api
EOF

# 构建
pnpm build
# 或 npm run build

# 构建产物在 dist 目录
ls -la dist/
```

### 10.4 部署前端静态文件

```bash
# 创建 Nginx 静态文件目录
sudo mkdir -p /var/www/ocr

# 复制构建产物
sudo cp -r /opt/ocr/frontend/dist/* /var/www/ocr/

# 设置权限
sudo chown -R www-data:www-data /var/www/ocr
```

---

## 11. Nginx 反向代理配置

### 11.1 安装 Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 11.2 配置 Nginx

```bash
sudo tee /etc/nginx/sites-available/ocr << 'EOF'
server {
    listen 80;
    server_name _;  # 替换为你的域名或 IP

    # 前端静态文件
    root /var/www/ocr;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;

    # 前端路由（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置（OCR 可能耗时较长）
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        
        # 文件上传大小限制
        client_max_body_size 100M;
    }

    # 上传文件访问
    location /uploads/ {
        alias /opt/ocr/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/api/health;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
```

### 11.3 启用配置

```bash
# 创建符号链接
sudo ln -sf /etc/nginx/sites-available/ocr /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重新加载
sudo systemctl reload nginx
```

---

## 12. SSL 证书配置（可选）

### 12.1 使用 Let's Encrypt（需要域名）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（替换域名）
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 12.2 使用自签名证书（测试环境）

```bash
# 生成自签名证书
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/ocr-selfsigned.key \
    -out /etc/ssl/certs/ocr-selfsigned.crt \
    -subj "/CN=localhost"

# 在 Nginx 配置中添加 SSL
# listen 443 ssl;
# ssl_certificate /etc/ssl/certs/ocr-selfsigned.crt;
# ssl_certificate_key /etc/ssl/private/ocr-selfsigned.key;
```

---

## 13. 初始数据导入

### 13.1 准备归档数据文件

```bash
# 创建数据目录
mkdir -p /opt/ocr/data

# 上传归档 Excel 文件到 /opt/ocr/data/archive.xls
# 可以使用 scp 或 sftp：
# scp archive.xls user@server:/opt/ocr/data/
```

### 13.2 执行初始导入

```bash
cd /opt/ocr
source .venv/bin/activate
set -a; source .env; set +a

# 方式一：使用环境变量
export INIT_ARCHIVE_EXCEL_PATH=/opt/ocr/data/archive.xls
export INIT_ARCHIVE_BATCH_ID=init_import
python init_archive_db.py

# 方式二：使用命令行参数
python init_archive_db.py /opt/ocr/data/archive.xls

# 方式三：交互式（如果脚本支持）
python init_archive_db.py
```

### 13.3 验证导入结果

```bash
# 连接数据库
psql -h localhost -U ocruser -d ocr_db

# 查询导入记录数
SELECT COUNT(*) FROM archive_records;

# 查看前几条记录
SELECT id, filename, archive_no FROM archive_records LIMIT 5;

# 退出
\q
```

---

## 14. 服务验证

### 14.1 检查所有服务状态

```bash
# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# OCR 后端
sudo systemctl status ocr

# Nginx
sudo systemctl status nginx
```

### 14.2 测试 API

```bash
# 健康检查
curl http://localhost:8000/api/health

# 应返回类似：
# {"status": "ok", "database": "connected", "redis": "connected"}

# 通过 Nginx 访问
curl http://localhost/api/health
```

### 14.3 测试 OCR 功能

```bash
# 准备测试图片
# 上传测试文件
curl -X POST http://localhost/api/ocr/upload \
    -F "file=@/path/to/test-image.jpg"

# 或在浏览器中访问前端界面
# http://YOUR_SERVER_IP/
```

### 14.4 GPU 状态监控

```bash
# 查看 GPU 使用情况
nvidia-smi

# 持续监控（每 2 秒刷新）
watch -n 2 nvidia-smi

# 查看 GPU 进程
nvidia-smi pmon -i 0
```

---

## 15. systemd 服务管理

### 15.1 常用命令

```bash
# 启动服务
sudo systemctl start ocr

# 停止服务
sudo systemctl stop ocr

# 重启服务
sudo systemctl restart ocr

# 重新加载配置（不中断服务）
sudo systemctl reload ocr

# 查看状态
sudo systemctl status ocr

# 查看日志
sudo journalctl -u ocr -f

# 开机自启
sudo systemctl enable ocr

# 禁用开机自启
sudo systemctl disable ocr
```

### 15.2 服务依赖管理

```bash
# 查看服务依赖
systemctl list-dependencies ocr

# 按顺序启动所有相关服务
sudo systemctl start postgresql redis-server ocr nginx
```

---

## 16. 日志管理

### 16.1 日志位置

| 服务 | 日志位置 |
|------|----------|
| OCR 后端 | `/opt/ocr/logs/uvicorn.log` |
| OCR 错误 | `/opt/ocr/logs/uvicorn.error.log` |
| Nginx 访问 | `/var/log/nginx/access.log` |
| Nginx 错误 | `/var/log/nginx/error.log` |
| PostgreSQL | `/var/log/postgresql/postgresql-15-main.log` |
| Redis | `/var/log/redis/redis-server.log` |

### 16.2 查看日志

```bash
# 实时查看 OCR 后端日志
tail -f /opt/ocr/logs/uvicorn.log

# 查看最近 100 行错误日志
tail -100 /opt/ocr/logs/uvicorn.error.log

# 使用 journalctl
sudo journalctl -u ocr --since "1 hour ago"

# 查看 Nginx 错误
sudo tail -f /var/log/nginx/error.log
```

### 16.3 日志轮转配置

```bash
sudo tee /etc/logrotate.d/ocr << 'EOF'
/opt/ocr/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ocruser ocruser
    sharedscripts
    postrotate
        systemctl reload ocr > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## 17. 备份与恢复

### 17.1 数据库备份

```bash
# 创建备份目录
mkdir -p /opt/ocr/backups

# 备份数据库
pg_dump -h localhost -U ocruser -d ocr_db -F c -f /opt/ocr/backups/ocr_db_$(date +%Y%m%d_%H%M%S).dump

# 定时备份（添加到 crontab）
crontab -e

# 每天凌晨 2 点备份
0 2 * * * pg_dump -h localhost -U ocruser -d ocr_db -F c -f /opt/ocr/backups/ocr_db_$(date +\%Y\%m\%d).dump
```

### 17.2 恢复数据库

```bash
# 恢复备份
pg_restore -h localhost -U ocruser -d ocr_db -c /opt/ocr/backups/ocr_db_20260330.dump
```

### 17.3 备份上传文件

```bash
# 备份上传目录
tar -czvf /opt/ocr/backups/uploads_$(date +%Y%m%d).tar.gz /opt/ocr/uploads/

# 恢复
tar -xzvf /opt/ocr/backups/uploads_20260330.tar.gz -C /
```

---

## 18. 性能优化

### 18.1 H20 GPU 优化

```bash
# 设置 GPU 持久化模式（减少启动延迟）
sudo nvidia-smi -pm 1

# 设置 GPU 计算模式为独占
sudo nvidia-smi -c 3

# 设置功耗限制（可选，默认 400W）
# sudo nvidia-smi -pl 350
```

### 18.2 PostgreSQL 优化

编辑 `/etc/postgresql/15/main/postgresql.conf`：

```conf
# 内存配置（根据服务器内存调整）
shared_buffers = 8GB
effective_cache_size = 24GB
work_mem = 256MB
maintenance_work_mem = 2GB

# 连接数
max_connections = 200

# WAL 配置
wal_buffers = 64MB
checkpoint_completion_target = 0.9
```

```bash
sudo systemctl restart postgresql
```

### 18.3 Redis 优化

编辑 `/etc/redis/redis.conf`：

```conf
# 最大内存
maxmemory 4gb

# 淘汰策略
maxmemory-policy allkeys-lru

# 禁用 THP
# 需要在系统级别设置
```

```bash
# 禁用透明大页
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
sudo systemctl restart redis-server
```

### 18.4 系统级优化

```bash
# 网络优化
sudo tee -a /etc/sysctl.conf << 'EOF'
# TCP 优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
EOF

# 应用
sudo sysctl -p
```

---

## 19. 常见问题排查

### Q1：nvidia-smi 显示 "No devices were found"

**原因**：驱动未正确安装或 GPU 未被识别。

**解决方案**：

```bash
# 检查 GPU 硬件
lspci | grep -i nvidia

# 重新安装驱动
sudo apt purge nvidia-*
sudo apt autoremove
sudo ubuntu-drivers autoinstall
sudo reboot
```

### Q2：CUDA 版本不匹配

**原因**：驱动支持的 CUDA 版本与安装的 Toolkit 不一致。

**解决方案**：

```bash
# 查看驱动支持的 CUDA 版本
nvidia-smi | grep "CUDA Version"

# 安装匹配的 CUDA Toolkit
# 例如驱动显示 CUDA 12.2，则安装 cuda-toolkit-12-2
```

### Q3：PaddlePaddle 无法使用 GPU

**原因**：CUDA/cuDNN 环境配置问题。

**解决方案**：

```bash
# 检查环境变量
echo $CUDA_HOME
echo $LD_LIBRARY_PATH

# 验证 CUDA
nvcc --version

# 重新安装 paddlepaddle-gpu
pip uninstall paddlepaddle-gpu
pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# 测试
python -c "import paddle; print(paddle.device.get_device())"
```

### Q4：Redis 连接失败

**原因**：Redis 未启动或配置错误。

**解决方案**：

```bash
# 检查 Redis 状态
sudo systemctl status redis-server

# 检查端口
ss -tlnp | grep 6379

# 测试连接
redis-cli ping

# 查看日志
sudo tail -50 /var/log/redis/redis-server.log
```

### Q5：PostgreSQL 连接被拒绝

**原因**：认证配置或网络问题。

**解决方案**：

```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 检查监听
ss -tlnp | grep 5432

# 检查 pg_hba.conf 配置
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep -v "^#"

# 测试连接
psql -h localhost -U ocruser -d ocr_db
```

### Q6：Nginx 502 Bad Gateway

**原因**：后端服务未运行或端口错误。

**解决方案**：

```bash
# 检查后端服务
sudo systemctl status ocr

# 检查端口
ss -tlnp | grep 8000

# 直接测试后端
curl http://localhost:8000/api/health

# 查看 Nginx 错误日志
sudo tail -50 /var/log/nginx/error.log
```

### Q7：OCR 处理超时

**原因**：大文件或 GPU 内存不足。

**解决方案**：

```bash
# 查看 GPU 内存使用
nvidia-smi

# 减少并发 workers
# 编辑 /etc/systemd/system/ocr.service
# 将 --workers 4 改为 --workers 2

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart ocr
```

### Q8：模型下载失败

**原因**：网络问题或 HuggingFace 访问受限。

**解决方案**：

```bash
# 使用百度 BOS 源（已在 config.py 中配置）
export PADDLE_PDX_MODEL_SOURCE=bos

# 或手动下载模型到缓存目录
# 参考 PaddleOCR 官方文档
```

### Q9：磁盘空间不足

**原因**：模型缓存或上传文件过多。

**解决方案**：

```bash
# 检查磁盘使用
df -h

# 查看大文件
du -sh /opt/ocr/*
du -sh /opt/ocr/.cache/*

# 清理旧日志
sudo journalctl --vacuum-time=7d

# 清理旧备份
rm /opt/ocr/backups/ocr_db_*.dump
```

### Q10：前端页面空白

**原因**：构建失败或路由配置错误。

**解决方案**：

```bash
# 检查前端文件
ls -la /var/www/ocr/

# 检查 index.html 是否存在
cat /var/www/ocr/index.html

# 重新构建
cd /opt/ocr/frontend
pnpm build
sudo cp -r dist/* /var/www/ocr/

# 检查 Nginx 配置
sudo nginx -t
```

---

## 20. 运维命令速查

### 20.1 服务管理

```bash
# 启动所有服务
sudo systemctl start postgresql redis-server ocr nginx

# 停止所有服务
sudo systemctl stop nginx ocr redis-server postgresql

# 重启 OCR 服务
sudo systemctl restart ocr

# 查看所有服务状态
sudo systemctl status postgresql redis-server ocr nginx
```

### 20.2 日志查看

```bash
# OCR 后端实时日志
tail -f /opt/ocr/logs/uvicorn.log

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# 系统日志
sudo journalctl -f
```

### 20.3 GPU 监控

```bash
# GPU 状态
nvidia-smi

# 持续监控
watch -n 1 nvidia-smi

# GPU 进程
nvidia-smi pmon
```

### 20.4 数据库操作

```bash
# 连接数据库
psql -h localhost -U ocruser -d ocr_db

# 备份
pg_dump -h localhost -U ocruser -d ocr_db -F c -f backup.dump

# 恢复
pg_restore -h localhost -U ocruser -d ocr_db -c backup.dump
```

### 20.5 代码更新

```bash
cd /opt/ocr

# 拉取最新代码
git pull

# 更新依赖
source .venv/bin/activate
pip install -r requirements.txt

# 重新构建前端
cd frontend && pnpm build && sudo cp -r dist/* /var/www/ocr/ && cd ..

# 重启服务
sudo systemctl restart ocr
sudo systemctl reload nginx
```

### 20.6 快速诊断

```bash
# 一键检查所有服务
echo "=== PostgreSQL ===" && sudo systemctl is-active postgresql
echo "=== Redis ===" && sudo systemctl is-active redis-server
echo "=== OCR ===" && sudo systemctl is-active ocr
echo "=== Nginx ===" && sudo systemctl is-active nginx
echo "=== GPU ===" && nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv
echo "=== Disk ===" && df -h /opt/ocr
echo "=== API ===" && curl -s http://localhost:8000/api/health
```

---

## 附录 A：完整环境变量列表

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://ocruser:password@localhost:5432/ocr_db` |
| `REDIS_URL` | Redis 连接字符串 | `redis://127.0.0.1:6379/0` |
| `UPLOAD_DIR` | 上传文件目录 | `/opt/ocr/uploads` |
| `CACHE_DIR` | 模型缓存目录 | `/opt/ocr/.cache` |
| `OCR_USE_GPU` | 是否使用 GPU | `true` |
| `OCR_DEVICE` | OCR 设备 | `gpu:0` |
| `OCR_LANG` | OCR 语言 | `ch` |
| `INIT_ARCHIVE_EXCEL_PATH` | 初始导入 Excel 路径 | `/opt/ocr/data/archive.xls` |
| `INIT_ARCHIVE_BATCH_ID` | 初始导入批次 ID | `init_import` |

---

## 附录 B：端口使用汇总

| 端口 | 服务 | 协议 | 说明 |
|------|------|------|------|
| 80 | Nginx | TCP | HTTP 入口 |
| 443 | Nginx | TCP | HTTPS 入口 |
| 8000 | Uvicorn | TCP | 后端 API |
| 5432 | PostgreSQL | TCP | 数据库 |
| 6379 | Redis | TCP | 缓存 |

---

## 附录 C：文件结构

```
/opt/ocr/
├── .venv/                 # Python 虚拟环境
├── .cache/                # 模型缓存
├── .env                   # 环境变量配置
├── uploads/               # 上传文件目录
├── logs/                  # 日志目录
│   ├── uvicorn.log
│   └── uvicorn.error.log
├── backups/               # 备份目录
├── data/                  # 数据文件（如初始导入 Excel）
├── app/                   # 后端代码
├── frontend/              # 前端代码
│   └── dist/              # 前端构建产物
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖
└── init_archive_db.py     # 初始数据导入脚本
```

---

## 附录 D：参考资料

- [NVIDIA H20 产品页面](https://www.nvidia.com/en-us/data-center/h20/)
- [CUDA Toolkit 下载](https://developer.nvidia.com/cuda-downloads)
- [cuDNN 下载](https://developer.nvidia.com/cudnn)
- [PaddlePaddle 官方文档](https://www.paddlepaddle.org.cn/)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Redis 官方文档](https://redis.io/docs/)
- [Nginx 官方文档](https://nginx.org/en/docs/)

---

**文档结束**

> 如有问题，请检查日志或参考 [常见问题排查](#19-常见问题排查) 章节。
