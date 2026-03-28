# PaddleOCR 文档识别系统 — 部署文档

## 1. 项目概述

本系统基于 **PaddleOCR 3.x** 深度学习引擎，集成 **三模型识别链路**（PaddleOCR-VL-1.5 / PP-StructureV3 / PP-OCRv5），提供图片与 PDF 的上传识别、本地路径批量导入、结构化解析、全文搜索、归档 Excel 导出与历史归档管理能力。系统采用 **Vue 3 + FastAPI** 前后端分离架构，并通过 **Redis + PostgreSQL** 提供缓存与持久化支持。

### 核心功能

| 功能 | 说明 |
|------|------|
| 文档上传 | 支持 JPG、PNG、BMP、TIFF、PDF 格式，最大 50MB |
| **三模型引擎** | VL 视觉语言模型 / PP-StructureV3 / PP-OCRv5，前端一键切换 |
| **版面分析** | RT-DETR-H 17 类检测：标题/文本/表格/图片/公式/印章等 |
| **表格识别** | SLANet_plus 自动识别表格结构，还原为 HTML 表格 |
| **可编辑结果** | 双击 OCR 区块即可修正文字，保存回数据库 |
| **Bbox 高亮** | 点击识别区块时在源图上高亮对应检测框，支持多边形框 |
| **历史按文件夹分组** | 首页历史按源目录聚合显示，点击后进入同目录结果页 |
| **文件夹级历史删除** | 历史目录支持按文件夹批量删除识别记录 |
| **目录侧边栏切换** | 结果页左侧显示当前文件夹全部文件，可快速切换查看 |
| **本地路径批量识别** | 输入服务器路径递归扫描文件夹，支持批量识别 |
| **结果目录导出** | 批量识别时自动输出 `.json` + `.txt` 到指定目录 |
| **归档 Excel 自动写入** | 自动提取档号/文号/题名等字段，支持目录或文件路径输入 |
| 数据存储 | 识别结果以 JSONB 格式持久化存储于 PostgreSQL |
| REST API | 完整的 RESTful 接口，附带 Swagger 文档 |

### 技术栈

| 组件 | 技术 |
|------|------|
| OCR 引擎 | PaddleOCR 3.x + PaddlePaddle GPU |
| 视觉语言模型 | PaddleOCR-VL-1.5 |
| 版面分析 | PP-StructureV3 (PaddleX layout_parsing) |
| 表格识别 | SLANet_plus |
| 后端框架 | FastAPI (Python 3.12) |
| 数据库 | PostgreSQL + SQLAlchemy ORM (asyncpg) |
| 缓存 | Redis (redis-py) |
| 前端 | Vue 3 + Vite + TailwindCSS + Axios |
| PDF 处理 | PyMuPDF (fitz) |
| GPU 加速 | NVIDIA CUDA 12.x |

---

## 2. 环境要求

### 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8 核及以上 |
| 内存 | 8 GB | 16 GB 及以上 |
| 磁盘 | 10 GB 可用空间 | SSD 20 GB 及以上 |
| GPU | 无（可用 CPU 模式） | NVIDIA GPU，显存 ≥ 4GB |

### 软件要求

| 软件 | 版本要求 |
|------|----------|
| 操作系统 | Windows 10/11、Ubuntu 20.04+、CentOS 7+ |
| Python | 3.10 ~ 3.12（不支持 3.13） |
| PostgreSQL | 14.0 及以上 |
| NVIDIA 驱动 | 525+ (CUDA 12.x) |
| CUDA Toolkit | 12.0 及以上（如使用 GPU） |

---

## 3. 安装部署步骤

### 3.1 安装 Python 环境

确保系统已安装 Python 3.10 ~ 3.12：

```bash
python --version
# 输出应为 Python 3.10.x / 3.11.x / 3.12.x
```

如未安装，Windows 用户可通过以下方式安装：

```bash
winget install Python.Python.3.12
```

### 3.2 创建虚拟环境

```bash
# 进入项目目录
cd d:\OCR

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3.3 安装依赖

```bash
pip install -r requirements.txt
```

> **GPU 用户**：确保已安装 NVIDIA 驱动和 CUDA 12.x，PaddlePaddle 会自动检测 GPU。
>
> **CPU 用户**：将 `requirements.txt` 中 `paddlepaddle-gpu` 替换为 `paddlepaddle`，并修改 `app/core/ocr_engine.py` 中 `device="gpu:0"` 为 `device="cpu"`。

### 3.4 配置 PostgreSQL 数据库

1. 确保 PostgreSQL 服务已启动
2. 创建数据库：

```bash
psql -U postgres -c "CREATE DATABASE ocr_db ENCODING 'UTF8';"
```

3. 确认 `config.py` 中数据库连接配置：

```python
DATABASE_URL = "postgresql+asyncpg://postgres:123456@localhost:5432/ocr_db"
```

> 如需修改用户名、密码或数据库名，请直接编辑 `config.py` 中的 `DATABASE_URL`，或通过环境变量 `DATABASE_URL` 覆盖。

### 3.5 启动服务

#### 开发模式

```powershell
# 1) 启动 Redis
Start-Process "D:\Redis\redis-server.exe"

# 2) 启动后端（8000，热重载）
D:\OCR\.venv\Scripts\python.exe D:\OCR\main.py

# 3) 启动前端（3000）
cd D:\OCR\frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

#### 生产模式（后端直接托管构建后的 Vue 前端）

```powershell
cd D:\OCR\frontend
npm run build

D:\OCR\.venv\Scripts\python.exe D:\OCR\main.py
```

首次启动时，系统会自动下载 OCR 模型文件，模型缓存在项目的 `.cache/` 目录下。VL 模型体积更大，首次使用时加载时间会明显长于后续请求。

> **安装版面解析依赖**（表格识别必需）：
> ```bash
> pip install "paddleocr[doc-parser]"
> ```

### 3.6 访问系统

| 场景 | 地址 |
|------|------|
| 前端开发环境 | http://localhost:3000 |
| 后端 API 文档（Swagger） | http://localhost:8000/docs |
| 后端 API 文档（ReDoc） | http://localhost:8000/redoc |
| 生产环境前端入口（构建后） | http://localhost:8000 |

---

## 4. 项目目录结构

```
d:\OCR\
├── main.py                        # 应用入口，支持 Vue SPA 回退与 /old 旧版入口
├── config.py                      # 配置文件（数据库、上传目录等）
├── requirements.txt               # Python 依赖
├── DEPLOYMENT.md                  # 部署文档（本文件）
├── README.md                      # 项目说明
├── extract_fields.py              # 独立脚本：从数据库批量提取字段写入 Excel
├── check_tasks.py                 # 独立脚本：查询任务状态统计
├── app/
│   ├── api/
│   │   └── routes.py              # REST API 路由（上传/扫描/识别/搜索/导出）
│   ├── core/
│   │   ├── ocr_engine.py          # OCR 引擎封装
│   │   └── redis_cache.py         # Redis 缓存封装
│   ├── db/
│   │   ├── database.py            # 数据库连接
│   │   └── models.py              # 数据模型（ocr_tasks 表）
│   ├── schemas/
│   │   └── ocr_schemas.py         # Pydantic 响应模型
│   └── services/
│       ├── ocr_service.py         # 业务逻辑层
│       └── excel_export.py        # 归档字段提取与 Excel 写入服务
├── frontend/                      # Vue 3 前端源码
│   ├── src/
│   │   ├── views/
│   │   │   ├── Home.vue           # 首页（模型区 + 历史区）
│   │   │   ├── Result.vue         # 结果页（预览/侧边栏/编辑）
│   │   │   └── Search.vue         # 搜索页
│   │   └── components/
│   │       ├── BufferZone.vue     # 批量上传区
│   │       └── HistoryList.vue    # 历史目录列表
│   ├── package.json
│   └── vite.config.js             # 前端代理与构建配置
├── templates/
│   └── index.html                 # 旧版单页面（备用入口 /old）
├── static/vue/                    # Vue 构建产物（生产环境由后端直接提供）
├── uploads/                       # 上传文件存储目录（自动创建）
└── .cache/                        # 模型缓存目录（自动创建）
```

---

## 5. API 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/upload?mode=vl\|layout\|ocr` | 上传文件并识别 |
| GET | `/api/ocr/scan-folder?path=...` | 扫描服务器本地文件夹，返回支持的图片/PDF 文件 |
| POST | `/api/ocr/upload-from-path?mode=vl&excel_path=...&excel_init=1&output_dir=...` | 按服务器路径识别，可自动写 Excel 和保存结果目录 |
| GET | `/api/ocr/tasks/folders` | 获取历史文件夹分组列表 |
| GET | `/api/ocr/tasks?page=1&page_size=20&folder=...` | 获取任务列表，支持按文件夹过滤，`page_size` 最大 1000 |
| GET | `/api/ocr/tasks/{task_id}` | 获取任务详情 |
| PUT | `/api/ocr/tasks/{task_id}` | 更新识别结果（编辑后保存） |
| DELETE | `/api/ocr/tasks/{task_id}` | 删除单个任务 |
| DELETE | `/api/ocr/tasks/by-folder?folder=...` | 删除某个历史文件夹下的全部任务 |
| GET | `/api/ocr/tasks/{task_id}/file` | 获取源文件（图片/PDF 预览） |
| GET | `/api/ocr/tasks/{task_id}/export?fmt=txt\|json` | 导出识别结果 |
| GET | `/api/ocr/tasks/search?q=关键词` | 搜索已识别文档全文 |

> 完整 API 文档请访问 http://localhost:8000/docs（Swagger UI）

---

## 6. 数据库设计

### ocr_tasks 表（识别任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 任务 ID |
| filename | VARCHAR(255) | 原始文件名 |
| file_path | VARCHAR(500) | 服务器存储路径（本地路径导入时保留原始路径） |
| file_type | VARCHAR(20) | 文件类型（.jpg/.pdf 等） |
| mode | VARCHAR(20) | 识别模型（vl/layout/ocr） |
| status | VARCHAR(20) | 状态（pending/processing/done/failed） |
| result_json | JSONB | 完整识别结果（regions/lines/table html/bbox） |
| full_text | TEXT | 完整识别文本 |
| page_count | INTEGER | 总页数 |
| error_message | TEXT | 错误信息（失败时） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

> 注：识别结果以 JSONB 格式存储在 `result_json` 字段中，包含 `regions`（版面区域）和 `lines`（逐行 OCR）。不再使用独立的 `ocr_results` 表。

---

## 7. 配置说明

所有配置集中在 `config.py` 文件中：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | postgresql+asyncpg://postgres:123456@localhost:5432/ocr_db | 数据库连接 |
| UPLOAD_DIR | ./uploads | 上传文件目录 |
| ALLOWED_EXTENSIONS | .jpg,.jpeg,.png,.bmp,.tiff,.tif,.pdf | 允许的文件类型 |
| MAX_FILE_SIZE | 50MB | 单文件最大尺寸 |
| OCR_LANG | ch | OCR 语言（ch=中英混合） |
| PADDLE_PDX_MODEL_SOURCE | bos | 模型下载源（百度对象存储） |

---

## 8. 常见问题

### Q1: 首次启动很慢？
首次启动需要下载模型文件（PP-OCRv5 约 200MB + PP-StructureV3 约 500MB），请确保网络畅通。模型下载后缓存在 `.cache/` 目录，后续启动无需重复下载。

### Q2: 如何切换为 CPU 模式？
修改 `app/core/ocr_engine.py` 中的 `device="gpu:0"` 为 `device="cpu"`。同时将 `requirements.txt` 中的 `paddlepaddle-gpu` 改为 `paddlepaddle`。

### Q3: 如何修改数据库连接？
编辑 `config.py` 中的 `DATABASE_URL`，或设置环境变量 `DATABASE_URL`。支持 PostgreSQL 和 SQLite：
- PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/dbname`
- SQLite: `sqlite+aiosqlite:///path/to/db.sqlite3`

### Q4: 如何修改服务端口？
启动时指定 `--port` 参数：
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 9000
```

### Q5: 上传的文件存储在哪里？
默认存储在项目目录下的 `uploads/` 文件夹中。可在 `config.py` 中修改 `UPLOAD_DIR`。

### Q6: 如何在生产环境部署？
推荐使用 systemd (Linux) 或 NSSM (Windows) 将服务注册为系统服务：

**Linux (systemd)：**
```ini
[Unit]
Description=PaddleOCR Document Recognition Service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ocr
ExecStart=/opt/ocr/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

**Windows (NSSM)：**
```bash
nssm install PaddleOCR "D:\OCR\.venv\Scripts\python.exe" "-m uvicorn main:app --host 0.0.0.0 --port 8000"
nssm set PaddleOCR AppDirectory "D:\OCR"
nssm start PaddleOCR
```

---

## 9. 联系方式

如有部署问题，请联系项目开发团队。
