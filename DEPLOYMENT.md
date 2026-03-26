# PaddleOCR 文档识别系统 — 部署文档

## 1. 项目概述

本系统基于 **PaddleOCR 3.0** 深度学习引擎，集成 **双模型引擎**（PP-OCRv5 + PP-StructureV3），提供文档图像的文字识别（OCR）、**版面分析**和**表格结构识别**能力。支持图片和 PDF 文件的上传、识别、在线编辑与结果存储。系统提供 **Web 可视化界面**和 **REST API** 两种使用方式。

### 核心功能

| 功能 | 说明 |
|------|------|
| 文档上传 | 支持 JPG、PNG、BMP、TIFF、PDF 格式，最大 50MB |
| **双模型引擎** | PP-OCRv5（快速文字识别）+ PP-StructureV3（版面解析+表格识别），前端一键切换 |
| **版面分析** | RT-DETR-H 17 类检测：标题/文本/表格/图片/公式/印章等 |
| **表格识别** | SLANet_plus 自动识别表格结构，还原为 HTML 表格 |
| **可编辑结果** | 双击 OCR 区块即可修正文字，保存回数据库 |
| **Bbox 高亮** | 点击识别区块时在源图上高亮对应检测框 |
| 源文件预览 | 上传或历史文件在中间面板实时预览（含 PDF 翻页缩放） |
| 结果展示 | 右侧面板「文档解析」（结构化区域）+「JSON」（语法高亮）双标签页 |
| 数据存储 | 识别结果以 JSONB 格式持久化存储于 PostgreSQL |
| REST API | 完整的 RESTful 接口，附带 Swagger 文档 |

### 技术栈

| 组件 | 技术 |
|------|------|
| OCR 引擎 | PaddleOCR 3.4 + PaddlePaddle GPU 3.3.1 |
| 版面分析 | PP-StructureV3 (PaddleX layout_parsing, 含 10 个模型) |
| 表格识别 | SLANet_plus |
| 后端框架 | FastAPI (Python 3.12) |
| 数据库 | PostgreSQL + SQLAlchemy ORM (asyncpg) |
| 前端 | HTML + TailwindCSS + PDF.js + FontAwesome |
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

```bash
# 开发模式（带热重载）
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

首次启动时，系统会自动下载 OCR 模型文件（PP-OCRv5 约 200MB + PP-StructureV3 约 500MB），模型缓存在项目的 `.cache/` 目录下。

> **安装版面解析依赖**（表格识别必需）：
> ```bash
> pip install "paddleocr[doc-parser]"
> ```

### 3.6 访问系统

| 入口 | 地址 |
|------|------|
| Web 界面 | http://localhost:8000 |
| API 文档（Swagger） | http://localhost:8000/docs |
| API 文档（ReDoc） | http://localhost:8000/redoc |

---

## 4. 项目目录结构

```
d:\OCR\
├── main.py                  # 应用入口
├── config.py                # 配置文件（数据库、缓存、OCR 参数）
├── requirements.txt         # Python 依赖
├── DEPLOYMENT.md            # 部署文档（本文件）
├── README.md                # 项目说明
├── progress.md              # 开发进度
├── app/
│   ├── api/
│   │   └── routes.py        # REST API 路由
│   ├── core/
│   │   └── ocr_engine.py    # OCR 引擎封装
│   ├── db/
│   │   ├── database.py      # 数据库连接
│   │   └── models.py        # 数据模型（OCRTask, OCRResult）
│   ├── schemas/
│   │   └── ocr_schemas.py   # Pydantic 响应模型
│   └── services/
│       └── ocr_service.py   # 业务逻辑层
├── templates/
│   └── index.html           # Web 前端页面
├── uploads/                 # 上传文件存储目录（自动创建）
└── .cache/                  # 模型缓存目录（自动创建）
```

---

## 5. API 接口说明

### 5.1 上传并识别文档

```
POST /api/ocr/upload?mode=layout
Content-Type: multipart/form-data
```

**请求参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| file | File | 要识别的文件（JPG/PNG/BMP/TIFF/PDF） |
| mode | Query | `layout`=PP-StructureV3 版面解析（含表格），`ocr`=PP-OCRv5 纯文字（快速） |

**响应示例：**

```json
{
  "id": 1,
  "filename": "test.jpg",
  "file_type": ".jpg",
  "status": "done",
  "full_text": "识别到的文字内容...",
  "page_count": 1,
  "result_json": [
    {
      "page_num": 1,
      "regions": [
        {"type": "title", "bbox": [x1,y1,x2,y2], "content": "标题文字", "html": null},
        {"type": "table", "bbox": [x1,y1,x2,y2], "content": "", "html": "<table>...</table>"},
        {"type": "text", "bbox": [x1,y1,x2,y2], "content": "段落文字", "html": null}
      ],
      "lines": [
        {"line_num": 1, "text": "第一行文字", "confidence": 0.98, "bbox": [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]}
      ]
    }
  ],
  "created_at": "2025-03-25T20:00:00",
  "updated_at": "2025-03-25T20:00:01"
}
```

### 5.2 获取任务列表

```
GET /api/ocr/tasks?page=1&page_size=20
```

### 5.3 获取任务详情

```
GET /api/ocr/tasks/{task_id}
```

### 5.4 获取源文件

```
GET /api/ocr/tasks/{task_id}/file
```

### 5.5 更新识别结果（编辑后保存）

```
PUT /api/ocr/tasks/{task_id}
Content-Type: application/json

{"result_json": [...], "full_text": "..."}
```

### 5.6 导出识别结果

```
GET /api/ocr/tasks/{task_id}/export?fmt=txt
GET /api/ocr/tasks/{task_id}/export?fmt=json
```

### 5.7 删除任务

```
DELETE /api/ocr/tasks/{task_id}
```

> 完整 API 文档请访问 http://localhost:8000/docs（Swagger UI）

---

## 6. 数据库设计

### ocr_tasks 表（识别任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PRIMARY KEY | 任务 ID |
| filename | VARCHAR(255) | 原始文件名 |
| file_path | VARCHAR(500) | 服务器存储路径 |
| file_type | VARCHAR(20) | 文件类型（.jpg/.pdf 等） |
| status | VARCHAR(20) | 状态（pending/processing/done/failed） |
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
