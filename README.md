# PaddleOCR 3.0 文档识别系统

## 项目简介

基于 **PaddleOCR 3.0** 的本地文档识别系统，集成 **双模型引擎**（PP-OCRv5 + PP-StructureV3），支持图片/PDF 文档的 OCR 识别、**版面分析**、**表格结构识别**。识别结果存入 PostgreSQL 数据库，提供 Web 界面和 REST API 双重交互方式。

## 核心能力

| 能力 | 说明 |
|------|------|
| **PP-OCRv5 文字识别** | 快速提取文档中的文字，支持中英文混合、手写体 |
| **PP-StructureV3 版面解析** | 17 类版面检测（标题/文本/表格/图片/公式/印章等） |
| **表格结构识别** | 自动识别表格并转为 HTML 表格渲染，还原行列结构 |
| **可编辑 OCR 结果** | 双击识别区块即可修正文字，保存回数据库 |
| **Bbox 高亮** | 点击识别区块时在源图上高亮对应检测框 |
| **JSON 查看器** | 深蓝主题语法高亮 JSON 原始数据查看 |
| **双模式切换** | 前端一键切换：版面解析（含表格） / 纯文字（快速） |

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| OCR 引擎 | PaddleOCR 3.4 + PaddlePaddle GPU 3.3.1 |
| 版面分析 | PP-StructureV3 (PaddleX layout_parsing) |
| 表格识别 | SLANet_plus |
| 版面检测 | RT-DETR-H_layout_17cls |
| 后端框架 | FastAPI (Python 3.12) |
| 数据库 | PostgreSQL + SQLAlchemy (asyncpg) |
| 前端 | HTML + TailwindCSS + PDF.js + FontAwesome |
| PDF 处理 | PyMuPDF (fitz) |
| GPU 加速 | NVIDIA CUDA 12.x |

## 集成模型列表

| 模型 | 用途 | 管线 |
|------|------|------|
| PP-OCRv5_server_det | 文字检测 | PP-OCRv5 |
| PP-OCRv5_server_rec | 文字识别 | PP-OCRv5 |
| PP-LCNet_x1_0_textline_ori | 文本行方向分类 | PP-OCRv5 |
| RT-DETR-H_layout_17cls | 17 类版面检测 | PP-StructureV3 |
| SLANet_plus | 表格结构识别 | PP-StructureV3 |
| PP-OCRv4_server_det | 文字检测（版面内） | PP-StructureV3 |
| PP-OCRv4_server_rec | 文字识别（版面内） | PP-StructureV3 |
| PP-OCRv4_server_seal_det | 印章检测 | PP-StructureV3 |
| PP-LCNet_x1_0_doc_ori | 文档方向分类 | PP-StructureV3 |
| UVDoc | 文档校正 | PP-StructureV3 |

## 项目结构

```
d:\OCR\
├── main.py                   # 应用入口（预加载双模型）
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖
├── README.md                 # 项目说明（本文件）
├── DEPLOYMENT.md             # 部署文档
├── progress.md               # 开发进度
├── app/
│   ├── api/
│   │   └── routes.py         # REST API 路由（含 mode 参数）
│   ├── core/
│   │   └── ocr_engine.py     # 双模型 OCR 引擎（PP-OCRv5 + PP-StructureV3）
│   ├── db/
│   │   ├── database.py       # 异步数据库连接
│   │   └── models.py         # 数据模型（OCRTask, JSONB 存储）
│   ├── schemas/
│   │   └── ocr_schemas.py    # Pydantic 响应模型
│   └── services/
│       └── ocr_service.py    # 业务逻辑层
├── templates/
│   └── index.html            # Web 前端（三栏布局 + 表格渲染）
├── uploads/                  # 上传文件存储（自动创建）
└── .cache/                   # 模型缓存目录（自动创建）
```

## REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/upload?mode=layout\|ocr` | 上传文件并识别（layout=版面解析, ocr=纯文字） |
| GET | `/api/ocr/tasks?page=1&page_size=20` | 获取任务列表（分页） |
| GET | `/api/ocr/tasks/{id}` | 获取任务详情及识别结果 |
| PUT | `/api/ocr/tasks/{id}` | 更新已编辑的识别结果 |
| GET | `/api/ocr/tasks/{id}/file` | 获取源文件预览 |
| GET | `/api/ocr/tasks/{id}/export?fmt=txt\|json` | 导出识别结果 |
| DELETE | `/api/ocr/tasks/{id}` | 删除任务及文件 |

## 数据库设计

### ocr_tasks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 主键 |
| filename | VARCHAR | 原始文件名 |
| file_path | VARCHAR | 服务器存储路径 |
| file_type | VARCHAR | 文件类型 |
| status | VARCHAR | pending / processing / done / failed |
| result_json | JSONB | 完整识别结果（含 regions + lines） |
| full_text | TEXT | 识别全文 |
| page_count | INTEGER | 页数 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 快速开始

### 1. 安装依赖
```bash
# 基础 OCR
pip install -r requirements.txt

# 版面解析 + 表格识别（推荐）
pip install "paddleocr[doc-parser]"
```

### 2. 配置数据库
```bash
psql -U postgres -c "CREATE DATABASE ocr_db ENCODING 'UTF8';"
```

### 3. 启动服务
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 访问
- Web 界面：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 环境要求

- Python 3.10 ~ 3.12（不支持 3.13）
- PostgreSQL 14+
- NVIDIA GPU + CUDA 12.x（推荐，也可 CPU 模式）
- Windows / Linux
