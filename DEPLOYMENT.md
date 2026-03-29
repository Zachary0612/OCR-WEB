# PaddleOCR 文档识别系统 — 超详细部署手册

> **版本**：v2.0 · 适用操作系统：**Ubuntu 22.04 LTS**（主路径）/ **Windows Server 2019/2022**（备选路径）  
> **预计耗时**：2 ~ 4 小时（取决于网速和 GPU 驱动安装）

---

## 目录

1. [部署总览](#1-部署总览)
2. [环境要求](#2-环境要求)
3. [准备服务器基础环境Linux](#3-准备服务器基础环境linux)
4. [安装 NVIDIA 驱动与 CUDA](#4-安装-nvidia-驱动与-cuda)
5. [安装 PostgreSQL](#5-安装-postgresql)
6. [安装 Redis](#6-安装-redis)
7. [安装 Python 3.12](#7-安装-python-312)
8. [安装 Node.js](#8-安装-nodejs)
9. [上传或克隆项目代码](#9-上传或克隆项目代码)
10. [创建虚拟环境并安装依赖](#10-创建虚拟环境并安装依赖)
11. [修改生产环境配置](#11-修改生产环境配置)
12. [初始化数据库](#12-初始化数据库)
13. [构建前端](#13-构建前端)
14. [写入初始归档数据](#14-写入初始归档数据)
15. [首次手动启动验证](#15-首次手动启动验证)
16. [配置 systemd 开机自启](#16-配置-systemd-开机自启)
17. [配置 Nginx 反向代理（可选）](#17-配置-nginx-反向代理可选)
18. [防火墙放行端口](#18-防火墙放行端口)
19. [Windows Server 部署路径](#19-windows-server-部署路径)
20. [验证清单](#20-验证清单)
21. [常见问题排查](#21-常见问题排查)

---

## 1. 部署总览

### 架构图

```
浏览器 / 内网客户端
        │ HTTP/HTTPS
        ▼
  [Nginx :80/:443]  ← 可选，提供 HTTPS 与静态加速
        │ 反向代理 → :8000
        ▼
  [FastAPI :8000]   ← 后端 + 内嵌 Vue 前端静态文件
        │
        ├── [PostgreSQL :5432]  ← 识别任务 & 归档记录持久化
        ├── [Redis :6379]       ← 接口缓存
        └── [PaddleOCR 引擎]    ← GPU / CPU 识别
```

### 部署步骤一览

| 步骤 | 内容 | 耗时估计 |
|------|------|----------|
| 1-2 | 服务器基础环境 & CUDA | 30 min |
| 3-4 | PostgreSQL & Redis | 10 min |
| 5-6 | Python & Node.js | 10 min |
| 7 | 上传代码 | 5 min |
| 8 | 安装 Python 依赖 | 30~60 min（PaddleOCR 包较大） |
| 9 | 修改配置 | 5 min |
| 10-11 | 数据库初始化 & 前端构建 | 10 min |
| 12 | 首次启动 + 模型下载 | 30~60 min（首次自动下载模型） |
| 13-15 | 自启动 & Nginx | 15 min |

---

## 2. 环境要求

### 硬件

| 项目 | 最低 | 推荐 |
|------|------|------|
| CPU | 4 核 | 8 核 |
| 内存 | 16 GB | 32 GB |
| 磁盘 | 40 GB（SSD） | 100 GB SSD |
| GPU | 无（CPU 模式） | NVIDIA 显存 ≥ 8 GB（RTX 3060/A2000 以上） |

> ⚠️ PaddleOCR VL 模型需约 6 GB 显存，PP-StructureV3 约需 3 GB，三模型同时加载建议 **≥ 8 GB 显存**。

### 软件

| 软件 | 版本 |
|------|------|
| OS | Ubuntu 22.04 LTS 或 Windows Server 2019/2022 |
| Python | **3.12**（不支持 3.13） |
| PostgreSQL | 14 以上 |
| Redis | 6 以上 |
| Node.js | 18 以上（仅构建前端时需要） |
| NVIDIA 驱动 | 525+ |
| CUDA | 12.0+ |

---

## 3. 准备服务器基础环境（Linux）

### 3.1 更新系统包

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget unzip build-essential
```

### 3.2 确认系统信息

```bash
# 查看 OS 版本
cat /etc/os-release

# 查看 CPU 核数
nproc

# 查看内存
free -h

# 查看磁盘空间
df -h

# 查看 GPU（如有）
lspci | grep -i nvidia
```

---

## 4. 安装 NVIDIA 驱动与 CUDA

> 如果服务器没有 GPU，**跳过本节**，直接进入第 5 步，后续步骤中使用 CPU 模式。

### 4.1 安装 NVIDIA 驱动

```bash
# 查询推荐驱动版本
sudo apt install -y ubuntu-drivers-common
ubuntu-drivers devices

# 自动安装推荐驱动（通常为 525 或更高）
sudo ubuntu-drivers autoinstall

# 重启服务器
sudo reboot
```

重启后验证：

```bash
nvidia-smi
```

输出示例（关注 Driver Version 和 CUDA Version）：

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.129.03   Driver Version: 535.129.03   CUDA Version: 12.2    |
+-----------------------------------------------------------------------------+
```

### 4.2 安装 CUDA Toolkit 12.x

```bash
# 下载 CUDA 12.2 安装包（根据实际驱动版本选择对应 CUDA 版本）
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-2

# 配置环境变量
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证
nvcc --version
```

---

## 5. 安装 PostgreSQL

### 5.1 安装

```bash
sudo apt install -y postgresql postgresql-contrib

# 启动并设为开机自启
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 验证状态
sudo systemctl status postgresql
```

### 5.2 创建数据库和用户

```bash
# 切换到 postgres 用户
sudo -i -u postgres

# 进入 PostgreSQL 命令行
psql
```

在 `psql` 交互界面中依次执行：

```sql
-- 创建专用数据库用户（把 'your_password' 换成你自己的强密码）
CREATE USER ocruser WITH PASSWORD 'your_password';

-- 创建数据库
CREATE DATABASE ocr_db ENCODING 'UTF8' OWNER ocruser;

-- 授予全部权限
GRANT ALL PRIVILEGES ON DATABASE ocr_db TO ocruser;

-- 退出
\q
```

退出 postgres 用户：

```bash
exit
```

### 5.3 验证连接

```bash
psql -U ocruser -d ocr_db -h localhost -c "SELECT version();"
# 输入上面设置的密码，看到 PostgreSQL 版本信息即成功
```

---

## 6. 安装 Redis

```bash
sudo apt install -y redis-server

# 修改配置
sudo nano /etc/redis/redis.conf
```

在配置文件中找到并修改以下行：

```conf
# 绑定地址（只允许本地访问，不暴露外网）
bind 127.0.0.1 ::1

# 设置密码（推荐，取消注释并改为你的密码）
requirepass your_redis_password

# 设置最大内存（根据服务器内存调整）
maxmemory 2gb
maxmemory-policy allkeys-lru
```

保存并重启 Redis：

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 验证
redis-cli -a your_redis_password ping
# 输出 PONG 即成功
```

> 如果不需要 Redis 密码，保持默认即可，Redis 默认无密码也可正常使用。

---

## 7. 安装 Python 3.12

Ubuntu 22.04 默认是 Python 3.10，需要单独安装 3.12：

```bash
# 添加 deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装 Python 3.12 和必要工具
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 验证
python3.12 --version
# 输出: Python 3.12.x
```

---

## 8. 安装 Node.js

Node.js 仅在**构建前端时需要**，构建完成后服务器上不再需要。

```bash
# 安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node --version   # v20.x.x
npm --version    # 10.x.x
```

---

## 9. 上传或克隆项目代码

### 方式 A：通过 Git 克隆（推荐）

```bash
# 创建部署目录
sudo mkdir -p /opt/ocr
sudo chown $USER:$USER /opt/ocr

# 克隆项目
git clone https://github.com/Zachary0612/OCR-WEB.git /opt/ocr

cd /opt/ocr
```

### 方式 B：通过 SCP 从本地 Windows 上传压缩包

在**本地 Windows** 的 PowerShell 中执行：

```powershell
# 打包项目（排除不必要的目录）
cd D:\
Compress-Archive -Path D:\OCR -DestinationPath D:\OCR_deploy.zip -CompressionLevel Optimal

# 上传到服务器（替换 user 和 server_ip）
scp D:\OCR_deploy.zip user@server_ip:/opt/
```

在**服务器**上解压：

```bash
cd /opt
unzip OCR_deploy.zip
mv OCR ocr
cd /opt/ocr
```

### 方式 C：通过 WinSCP / FileZilla 图形化上传

1. 打开 WinSCP 或 FileZilla，连接到服务器（协议选 SFTP）
2. 将本地 `D:\OCR` 整个目录上传到服务器 `/opt/ocr/`
3. **排除以下目录**（不需要上传，服务器上会重新生成）：
   - `.venv/` — 虚拟环境
   - `static/vue/` — 前端构建产物
   - `uploads/` — 上传文件
   - `.cache/` — 模型缓存
   - `frontend/node_modules/` — 前端依赖

---

## 10. 创建虚拟环境并安装依赖

```bash
cd /opt/ocr

# 创建虚拟环境
python3.12 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 10.1 安装 PaddlePaddle（关键步骤，必须根据 CUDA 版本选择）

```bash
# 先查看你的 CUDA 版本
nvcc --version
# 或者
nvidia-smi  # 右上角显示 CUDA Version

# ---- 根据 CUDA 版本选择对应命令 ----

# CUDA 12.3:
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# CUDA 12.6:
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 11.8:
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# 无 GPU，使用 CPU 模式:
# pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

验证 PaddlePaddle 安装：

```bash
python -c "import paddle; paddle.utils.run_check()"
# 有 GPU 时输出: PaddlePaddle works well on 1 GPU.
# CPU 模式输出: PaddlePaddle works well on CPU.
```

### 10.2 安装其余 Python 依赖

```bash
# requirements.txt 第一行是 paddlepaddle-gpu，已安装好了，跳过它
sed -i 's/^paddlepaddle-gpu/# paddlepaddle-gpu/' requirements.txt
pip install -r requirements.txt
```

### 10.3 安装版面解析额外依赖（表格识别必需）

```bash
pip install "paddleocr[doc-parser]"
```

> 这一步会安装 PP-StructureV3 所需的 PaddleX 版面解析组件，安装时间较长（5~15 分钟），请耐心等待。

### 10.4 验证全部依赖

```bash
python -c "import fastapi; import sqlalchemy; import paddleocr; import openpyxl; print('全部依赖安装成功!')"
```

---

## 11. 修改生产环境配置

```bash
cd /opt/ocr
nano config.py
```

**必须修改的内容：**

```python
# 修改数据库连接（替换用户名、密码）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ocruser:your_password@localhost:5432/ocr_db"
    #                        ↑用户名     ↑你的密码
)
```

> 保存方法：Ctrl+O → 回车 → Ctrl+X

### 11.1 如果 Redis 设了密码，修改 Redis 连接

```bash
nano app/core/redis_cache.py
```

找到 Redis 连接配置，改为带密码的 URL：

```python
# 把 redis://localhost:6379/0 改为：
# redis://:your_redis_password@localhost:6379/0
```

### 11.2 CPU 模式调整（服务器没有 GPU 时）

```bash
# 快速替换所有 gpu 设备设置为 cpu
sed -i 's/device="gpu:0"/device="cpu"/g' app/core/ocr_engine.py
sed -i 's/device="gpu"/device="cpu"/g' app/core/ocr_engine.py

# 同时修改 config.py
sed -i 's/OCR_USE_GPU = True/OCR_USE_GPU = False/' config.py
```

---

## 12. 初始化数据库

数据库表由 SQLAlchemy 在后端启动时自动创建。也可以提前手动初始化：

```bash
cd /opt/ocr
source .venv/bin/activate

python -c "
import asyncio, sys
sys.path.insert(0, '.')
async def init():
    from app.db.database import init_db
    await init_db()
    print('数据库表创建成功!')
asyncio.run(init())
"
```

---

## 13. 构建前端

```bash
cd /opt/ocr/frontend

# 安装前端依赖
npm install

# 构建生产版本（产物输出到 /opt/ocr/static/vue/）
npm run build
```

构建成功输出示例：

```
vite v5.x.x building for production...
✓ 58 modules transformed.
../static/vue/index.html           0.45 kB
../static/vue/assets/index-xxx.js  280 kB
Build complete.
```

验证构建产物：

```bash
ls /opt/ocr/static/vue/
# 应看到 index.html 和 assets/ 目录
```

---

## 14. 写入初始归档数据（必须执行）

> **为什么必须做？**  
> 系统在每次批量识别结束后会自动下载两个 Excel：  
> ① `归档目录.xlsx` — 来自数据库中 `batch_id = init_import` 的 23 条预置归档目录数据  
> ② `本批识别.xlsx` — 本次 OCR 提取的字段  
> 若不执行本步骤，① 号文件下载时会报 404 错误。

### 步骤 1：上传 Excel 源文件到服务器

**Linux：**
```bash
# 在本地 Windows 上执行（将文件传到服务器）
scp "D:\GOOLGE\软件著录\归档文件目录（所需字段）.xls" root@<服务器IP>:/opt/data/
```

**Windows Server（直接部署）：**
```
直接复制文件到服务器本地路径，例如：
C:\ocr-data\归档文件目录（所需字段）.xls
```

### 步骤 2：修改导入脚本中的路径

打开项目根目录的 `init_archive_db.py`，找到第一行配置：

```python
# Linux 服务器改为：
EXCEL_PATH = "/opt/data/归档文件目录（所需字段）.xls"

# Windows Server 改为：
EXCEL_PATH = r"C:\ocr-data\归档文件目录（所需字段）.xls"
```

### 步骤 3：运行导入脚本

**Linux：**
```bash
cd /opt/ocr
source .venv/bin/activate
python init_archive_db.py
```

**Windows Server：**
```powershell
cd C:\ocr
.venv\Scripts\python.exe init_archive_db.py
```

### 步骤 4：验证导入结果

```
预期输出：成功导入 23 条归档记录
```

在数据库中确认：
```sql
-- PostgreSQL
SELECT COUNT(*) FROM archive_records WHERE batch_id = 'init_import';
-- 结果应为 23
```

> 若重复执行会重复插入数据，再次运行前请先清除旧记录：  
> `DELETE FROM archive_records WHERE batch_id = 'init_import';`

---

## 15. 首次手动启动验证

在配置为系统服务之前，先手动启动确认一切正常：

```bash
cd /opt/ocr
source .venv/bin/activate

# 确认 Redis 在线
redis-cli -a your_redis_password ping

# 前台启动后端（方便查看日志和错误）
python main.py
```

正常启动日志：

```
INFO:     正在初始化数据库...
INFO:     数据库初始化完成
INFO:     服务就绪！模型将在首次使用时自动加载。
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

> ⚠️ **首次使用某个模型时会自动下载模型文件**，大小如下：
> - PP-OCRv5：约 200 MB
> - PP-StructureV3：约 500 MB
> - PaddleOCR-VL-1.5：约 4 GB（较大）
>
> 模型下载到 `/opt/ocr/.cache/` 目录，**下载完成后后续启动无需重复下载**。
>
> 如果服务器网络慢，建议提前在本地把 `.cache/` 目录打包上传到服务器。

在另一个终端验证服务正常：

```bash
# 检查 Swagger API 文档
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs
# 输出 200 即成功

# 检查任务列表接口
curl http://localhost:8000/api/ocr/tasks?page=1&page_size=1
# 应返回 JSON 格式数据
```

确认正常后按 **Ctrl+C** 停止，进入下一步。

---

## 16. 配置 systemd 开机自启

### 16.1 创建 systemd 服务文件

```bash
sudo nano /etc/systemd/system/ocr.service
```

粘贴以下内容（**注意修改 `your_username` 和密码**）：

```ini
[Unit]
Description=PaddleOCR Document Recognition System
Documentation=https://github.com/Zachary0612/OCR-WEB
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/opt/ocr
ExecStart=/opt/ocr/.venv/bin/python /opt/ocr/main.py
Restart=always
RestartSec=5

# 环境变量（替换为你的实际密码）
Environment=DATABASE_URL=postgresql+asyncpg://ocruser:your_password@localhost:5432/ocr_db
Environment=REDIS_URL=redis://:your_redis_password@localhost:6379/0

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ocr-service

[Install]
WantedBy=multi-user.target
```

保存（Ctrl+O → 回车 → Ctrl+X）。

### 16.2 启用并启动服务

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 设置开机自启
sudo systemctl enable ocr.service

# 立即启动
sudo systemctl start ocr.service

# 查看启动状态（应为 active (running)）
sudo systemctl status ocr.service
```

正常状态输出：

```
● ocr.service - PaddleOCR Document Recognition System
     Loaded: loaded (/etc/systemd/system/ocr.service; enabled)
     Active: active (running) since ...
   Main PID: 12345 (python)
```

### 16.3 常用运维命令

```bash
# 查看最近 100 行日志
sudo journalctl -u ocr.service -n 100

# 实时跟踪日志
sudo journalctl -u ocr.service -f

# 重启服务（更新代码后执行）
sudo systemctl restart ocr.service

# 停止服务
sudo systemctl stop ocr.service
```

---

## 17. 配置 Nginx 反向代理（可选）

如果需要通过 80/443 端口访问或配置 HTTPS，使用 Nginx 做反向代理。

### 17.1 安装 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 17.2 创建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/ocr
```

粘贴以下内容（**替换 `your_domain_or_ip`**）：

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # 最大上传文件大小
    client_max_body_size 100m;

    # 超时设置（OCR 识别耗时较长，必须设置）
    proxy_read_timeout 300s;
    proxy_connect_timeout 10s;
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件由 Nginx 直接提供（可选，提升性能）
    location /static/ {
        alias /opt/ocr/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 17.3 启用配置

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/ocr /etc/nginx/sites-enabled/

# 移除默认站点（避免冲突）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置语法
sudo nginx -t
# 输出: nginx: configuration file test is successful

# 重新加载 Nginx
sudo systemctl reload nginx
```

### 17.4 配置 HTTPS（有域名时推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书并自动配置（替换为你的域名和邮箱）
sudo certbot --nginx -d your_domain.com -m your_email@example.com --agree-tos

# 验证自动续期
sudo certbot renew --dry-run
```

---

## 18. 防火墙放行端口

### UFW（Ubuntu 默认防火墙）

```bash
# SSH 端口必须保留！
sudo ufw allow 22/tcp

# 如果使用 Nginx（推荐）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 如果不用 Nginx，直接放行后端端口
sudo ufw allow 8000/tcp

# 启用防火墙
sudo ufw enable

# 查看规则
sudo ufw status
```

### 云服务器安全组（阿里云 / 腾讯云 / AWS）

在控制台安全组中添加入站规则：

| 协议 | 端口 | 来源 | 说明 |
|------|------|------|------|
| TCP | 22 | 你的 IP | SSH |
| TCP | 80 | 0.0.0.0/0 | HTTP |
| TCP | 443 | 0.0.0.0/0 | HTTPS |
| TCP | 8000 | 内网 IP | 后端（不用 Nginx 时） |

---

## 19. Windows Server 部署路径

> 如果服务器是 Windows Server 2019/2022，按以下步骤。

### 19.1 安装基础软件

依次下载并安装以下软件：

| 软件 | 下载地址 |
|------|---------|
| Python 3.12 | https://www.python.org/downloads/windows/ |
| PostgreSQL 16 | https://www.enterprisedb.com/downloads/postgres-postgresql-downloads |
| Redis for Windows | https://github.com/microsoftarchive/redis/releases |
| Node.js 20 LTS | https://nodejs.org/en/download |
| Git | https://git-scm.com/download/win |

> 安装 Python 时勾选 **"Add Python to PATH"**！

### 19.2 创建项目目录并克隆代码

以**管理员身份**打开 PowerShell：

```powershell
mkdir C:\OCR
cd C:\OCR
git clone https://github.com/Zachary0612/OCR-WEB.git .
```

### 19.3 创建虚拟环境并安装依赖

```powershell
python -m venv .venv
.venv\Scripts\activate

# 升级 pip
python -m pip install --upgrade pip

# 安装 PaddlePaddle GPU（根据你的 CUDA 版本）
pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# 安装其余依赖
pip install -r requirements.txt --ignore-installed paddlepaddle-gpu

# 安装版面解析依赖
pip install "paddleocr[doc-parser]"
```

### 19.4 修改 config.py

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://ocruser:your_password@localhost:5432/ocr_db"
)
```

### 19.5 构建前端

```powershell
cd C:\OCR\frontend
npm install
npm run build
```

### 19.6 手动启动测试

```powershell
cd C:\OCR
.venv\Scripts\activate
python main.py
```

访问 http://localhost:8000 验证。

### 19.7 使用 NSSM 注册为 Windows 服务（开机自启）

```powershell
# 下载 NSSM: https://nssm.cc/download
# 解压到 C:\nssm\ 后以管理员身份运行

# 注册服务
nssm install OCR-Service "C:\OCR\.venv\Scripts\python.exe" "C:\OCR\main.py"
nssm set OCR-Service AppDirectory "C:\OCR"
nssm set OCR-Service AppEnvironmentExtra "DATABASE_URL=postgresql+asyncpg://ocruser:your_password@localhost:5432/ocr_db"
nssm set OCR-Service Start SERVICE_AUTO_START

# 启动服务
nssm start OCR-Service

# 查看状态
nssm status OCR-Service
```

---

## 20. 验证清单

部署完成后，逐一核对以下检查项：

```bash
# 1. PostgreSQL 正在运行
sudo systemctl status postgresql | grep "Active:"

# 2. Redis 正在运行
redis-cli -a your_redis_password ping
# 期望输出: PONG

# 3. OCR 服务正在运行
sudo systemctl status ocr.service | grep "Active:"

# 4. 端口监听正常
ss -tlnp | grep -E "8000|5432|6379"

# 5. API 正常响应
curl -s http://localhost:8000/api/ocr/tasks?page=1&page_size=1
# 期望输出: {"total":...,"items":[...]}

# 6. 前端页面可访问
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000
# 期望输出: 200

# 7. 数据库表已创建（应包含 ocr_tasks 和 archive_records）
psql -U ocruser -d ocr_db -h localhost -c "\dt"
```

**全部通过即部署成功 ✓**

---

## 21. 常见问题排查

### Q1：启动时报 `cannot connect to database`

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 测试数据库连接
psql -U ocruser -d ocr_db -h localhost

# 检查 config.py 配置是否正确
grep DATABASE_URL /opt/ocr/config.py
```

---

### Q2：`ModuleNotFoundError: No module named 'paddleocr'`

```bash
# 确认虚拟环境已激活
source /opt/ocr/.venv/bin/activate
which python  # 应显示 /opt/ocr/.venv/bin/python

# 重新安装
pip install paddleocr>=3.0.0
```

---

### Q3：首次识别时模型下载失败（网络超时）

项目已配置使用百度 BOS 镜像，无需访问 HuggingFace。如果 BOS 也慢，可以在本地把模型打包上传：

```powershell
# 在本地 Windows 执行
scp -r D:\OCR\.cache user@server_ip:/opt/ocr/
```

---

### Q4：前端显示空白或 404

```bash
# 检查构建产物是否存在
ls /opt/ocr/static/vue/
# 应该有 index.html 和 assets/ 目录

# 没有的话重新构建
cd /opt/ocr/frontend && npm run build
```

---

### Q5：GPU 不被 PaddlePaddle 识别

```bash
# 检查驱动
nvidia-smi

# 检查 CUDA 版本匹配
nvcc --version

# 检查 PaddlePaddle 是否能看到 GPU
python -c "import paddle; print(paddle.device.cuda.device_count())"
# 应输出 1 或更多

# 如果还是无法识别，改用 CPU 模式（见 11.2 节）
```

---

### Q6：服务器重启后服务未自动启动

```bash
# 检查是否设为开机自启
sudo systemctl is-enabled ocr.service
# 应输出 enabled

# 重新设置
sudo systemctl enable ocr.service
sudo systemctl start ocr.service
```

---

### Q7：上传大文件超时（通过 Nginx）

在 `/etc/nginx/sites-available/ocr` 中增大限制：

```nginx
client_max_body_size 200m;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
```

然后 `sudo systemctl reload nginx`。

---

### Q8：数据库密码包含特殊字符

如果密码中有 `@`、`#`、`/` 等字符，需要 URL 编码：

```
@ → %40
# → %23
/ → %2F
```

例如密码 `p@ss#word` 应写为：

```python
DATABASE_URL = "postgresql+asyncpg://ocruser:p%40ss%23word@localhost:5432/ocr_db"
```

---

### Q9：更新代码后如何重新部署

```bash
cd /opt/ocr

# 拉取最新代码
git pull

# 重新构建前端（如果有前端改动）
cd frontend && npm run build && cd ..

# 重启后端服务
sudo systemctl restart ocr.service

# 查看日志确认启动正常
sudo journalctl -u ocr.service -n 50
```

---

*如有部署问题请联系项目开发团队。*
