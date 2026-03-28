# OCR 文档识别归档系统

## 项目简介

基于 **PaddleOCR 3.x** 的本地文档智能识别与归档系统。集成三种 OCR 模型引擎（PP-OCRv5 基础识别、PP-StructureV3 版面解析、PaddleOCR-VL-1.5 视觉语言模型），支持图片/PDF 批量识别、结构化提取、全文搜索，并提供归档 Excel 自动导出功能。

采用 **Vue 3 + FastAPI** 现代全栈架构，使用 **Redis** 缓存加速，识别结果存入 **PostgreSQL** 数据库。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **三模型识别** | VL 视觉语言模型 / 版面解析 / 基础文字识别，前端一键切换 |
| **批量文件夹识别** | 输入服务器路径，递归扫描并批量识别，支持实时进度条 |
| **识别历史按文件夹分组** | 首页历史按源目录聚合显示，点击目录直接进入该批次结果 |
| **文件夹级历史删除** | 历史列表支持按文件夹批量删除识别记录 |
| **结果页文件侧边栏** | 进入目录后左侧显示当前文件夹全部文件，可快速切换查看 |
| **识别结果目录导出** | 批量识别时自动将 JSON + TXT 结果保存到指定目录 |
| **归档 Excel 自动写入** | 识别完成后自动提取关键字段写入 Excel，支持“目录或文件路径”两种输入 |
| **全文搜索** | 在已识别文档中按关键词搜索，支持文本、表格、JSON 全匹配，返回高亮片段 |
| **版面解析 + 表格识别** | 17 类版面检测，表格转 HTML 渲染，还原行列结构 |
| **Bbox 区块高亮** | 点击识别区块在源图上高亮对应检测框，支持编辑保存 |
| **PDF 预览** | iframe 内嵌浏览器原生 PDF 预览，识别结果连续滚动展示 |
| **Redis 缓存** | 任务详情、列表、搜索结果多级缓存，显著提升响应速度 |
| **大图自动缩放** | 超大图片自动缩放后再送入 OCR，防止显存溢出 |
| **中文路径支持** | 使用 numpy+imdecode 读写图片，解决 OpenCV 中文路径问题 |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| OCR 引擎 | PaddleOCR 3.x + PaddlePaddle GPU |
| 视觉语言模型 | PaddleOCR-VL-1.5 |
| 版面分析 | PP-StructureV3 (PaddleX layout_parsing) |
| 后端框架 | FastAPI + Uvicorn (Python 3.12) |
| 数据库 | PostgreSQL + SQLAlchemy (asyncpg 异步) |
| 缓存 | Redis (redis-py) |
| 前端 | Vue 3 + Vite + TailwindCSS + Axios |
| Excel 导出 | openpyxl |
| PDF 处理 | PyMuPDF (fitz) |
| GPU 加速 | NVIDIA CUDA 12.x |

---

## 集成模型

| 模型 | 用途 | 管线 |
|------|------|------|
| PaddleOCR-VL-1.5 | 视觉语言理解，识别质量最佳 | VL |
| RT-DETR-H_layout_17cls | 17 类版面检测 | PP-StructureV3 |
| SLANet_plus | 表格结构识别 | PP-StructureV3 |
| PP-OCRv4_server_det/rec | 版面内文字检测识别 | PP-StructureV3 |
| PP-OCRv4_server_seal_det | 印章检测 | PP-StructureV3 |
| PP-LCNet_x1_0_doc_ori | 文档方向分类 | PP-StructureV3 |
| UVDoc | 文档校正展开 | PP-StructureV3 |
| PP-OCRv5_server_det/rec | 快速文字检测识别 | PP-OCRv5 |

---

## 项目结构

```
d:\OCR\
├── main.py                        # 应用入口，启动 FastAPI + 服务 Vue 静态文件
├── config.py                      # 配置（数据库、Redis、上传目录等）
├── requirements.txt               # Python 依赖
├── extract_fields.py              # 独立脚本：从数据库批量提取字段写入 Excel
├── check_tasks.py                 # 独立脚本：查询任务状态统计
├── app/
│   ├── api/
│   │   └── routes.py              # REST API（上传/扫描/识别/搜索/导出）
│   ├── core/
│   │   ├── ocr_engine.py          # 三模型 OCR 引擎（含大图缩放/中文路径修复）
│   │   └── redis_cache.py         # Redis 缓存封装（get/set/invalidate）
│   ├── db/
│   │   ├── database.py            # 异步数据库连接
│   │   └── models.py              # ORM 模型（ocr_tasks 表）
│   ├── schemas/
│   │   └── ocr_schemas.py         # Pydantic 响应模型
│   └── services/
│       ├── ocr_service.py         # OCR 业务逻辑（创建任务/运行/搜索）
│       └── excel_export.py        # 归档字段提取与 Excel 写入服务
├── frontend/                      # Vue 3 前端源码
│   ├── src/
│   │   ├── views/
│   │   │   ├── Result.vue         # 识别结果页（源文件预览/目录侧边栏/编辑）
│   │   │   └── Search.vue         # 全文搜索页
│   │   └── components/
│   │       ├── BufferZone.vue     # 批量上传区（文件/路径/Excel导出/结果目录）
│   │       └── HistoryList.vue    # 历史目录列表（分组查看/批量删除）
│   └── package.json
├── uploads/                       # 上传文件存储（自动创建）
├── static/vue/                    # Vue 构建产物（生产环境由后端直接提供）
├── templates/index.html           # 旧版单页面（备用入口 /old）
└── .cache/                        # 模型缓存目录（首次使用时自动下载）
```

---

## REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ocr/upload?mode=vl\|layout\|ocr` | 上传文件并识别 |
| GET | `/api/ocr/scan-folder?path=...` | 扫描本地文件夹，返回文件列表 |
| POST | `/api/ocr/upload-from-path?mode=vl&excel_path=...&excel_init=1&output_dir=...` | 按服务器路径识别，可自动写 Excel 和保存结果文件 |
| GET | `/api/ocr/tasks/folders` | 获取历史源文件夹分组列表 |
| GET | `/api/ocr/tasks?page=1&page_size=20&folder=...` | 任务列表（支持文件夹过滤，`page_size` 最大 1000） |
| GET | `/api/ocr/tasks/{id}` | 任务详情（Redis 缓存） |
| GET | `/api/ocr/tasks/search?q=关键词` | 全文搜索（Redis 缓存） |
| PUT | `/api/ocr/tasks/{id}` | 更新识别结果（编辑后保存） |
| GET | `/api/ocr/tasks/{id}/file` | 获取源文件（图片/PDF 预览） |
| GET | `/api/ocr/tasks/{id}/export?fmt=txt\|json` | 导出识别结果 |
| DELETE | `/api/ocr/tasks/{id}` | 删除任务 |
| DELETE | `/api/ocr/tasks/by-folder?folder=...` | 删除某个历史文件夹下的全部任务 |

---

## 数据库设计

### `ocr_tasks` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | 主键 |
| filename | VARCHAR | 原始文件名 |
| file_path | VARCHAR | 服务器存储路径（本地路径保留原路径） |
| file_type | VARCHAR | 文件类型（.jpg/.pdf 等） |
| mode | VARCHAR | 使用的识别模型（vl/layout/ocr） |
| status | VARCHAR | pending / processing / done / failed |
| result_json | JSONB | 完整识别结果（含 regions/lines/bbox） |
| full_text | TEXT | 识别全文（用于搜索） |
| page_count | INTEGER | 页数 |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

---

## 快速启动

### 环境要求
- Python 3.10 ~ 3.12（不支持 3.13）
- PostgreSQL 14+
- Redis（本地 `D:\Redis\redis-server.exe`）
- Node.js 18+（前端开发）
- NVIDIA GPU + CUDA 12.x（推荐）

### 1. 安装依赖

```bash
# Python 后端
pip install -r requirements.txt

# 前端
cd frontend && npm install
```

### 2. 配置数据库

```bash
psql -U postgres -c "CREATE DATABASE ocr_db ENCODING 'UTF8';"
```

编辑 `config.py` 确认数据库密码与 Redis 地址。

### 3. 启动 Redis

```powershell
Start-Process "D:\Redis\redis-server.exe"
```

### 4. 启动后端（端口 8000）

```powershell
D:\OCR\.venv\Scripts\python.exe main.py
```

### 5. 启动前端（端口 3000）

```powershell
cd D:\OCR\frontend
npx vite --port 3000 --host
```

### 6. 访问

- 前端开发环境：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs
- 前端生产环境（执行 `npm run build` 后）：http://localhost:8000

---

## 批量识别与归档导出

### 前端操作流程

1. 打开 http://localhost:3000，选择识别模型（VL/版面解析/基础OCR）
2. 在「文件夹路径」框输入 `D:\GOOLGE\软件著录\模版文件`，点击「导入」
3. （可选）在「归档Excel路径」框输入目录或完整文件路径，例如 `D:\GOOLGE\软件著录` 或 `D:\GOOLGE\软件著录\归档文件目录.xlsx`
4. （可选）在「识别结果输出目录」框输入目录路径，识别后自动保存 `.json` + `.txt`
5. 点击「立即批量识别」，批次第一个文件会先清空 Excel 旧数据行，再写入当前批次结果
6. 首页「识别历史」按源文件夹分组显示，点击目录进入结果页，左侧侧边栏可切换当前目录下文件
7. 鼠标悬停历史目录可按文件夹批量删除记录

### 命令行提取字段写入 Excel

批量识别完成后，直接运行：

```powershell
D:\OCR\.venv\Scripts\python.exe D:\OCR\extract_fields.py
```

脚本会：
- 查询数据库中 `D:\GOOLGE\软件著录\模版文件` 路径下的所有已完成任务
- 提取档号、文号、责任者、题名、日期、页数、密级、备注
- 写入 `D:\GOOLGE\软件著录\归档文件目录（所需字段）.xls`

---

## Redis 缓存策略

| 缓存键 | TTL | 说明 |
|--------|-----|------|
| `task:{id}` | 1 小时 | 单任务详情缓存 |
| `list:{page}:{size}:{folder}` | 30 秒 | 任务列表缓存（含文件夹过滤） |
| `search:{q}:{page}:{size}` | 2 分钟 | 搜索结果缓存 |
| `folders` | 30 秒 | 历史文件夹分组缓存 |

上传/更新/删除操作会自动失效相关缓存。Redis 不可用时自动降级为直接查数据库。

---

## 常见问题

**Q: `RequestsDependencyWarning: urllib3...` 警告**  
A: 不影响运行，是 urllib3 版本兼容性提示，忽略即可。

**Q: CUDNN 版本不匹配警告**  
A: Paddle 编译版本与本机 CUDNN 版本差异导致，不影响识别功能，建议后续对齐版本。

**Q: 批量识别时内存溢出**  
A: 系统已内置大图自动缩放（超过 2500×2500 自动缩放），并在每个任务后执行 GC + GPU 缓存清理。

**Q: 中文文件夹路径无法读取**  
A: 系统已使用 `numpy.fromfile + cv2.imdecode` 替代 `cv2.imread`，支持中文路径。

**Q: 归档 Excel 路径填目录还是文件？**  
A: 两种都支持。若填写目录如 `D:\GOOLGE\软件著录`，系统会自动写入 `D:\GOOLGE\软件著录\归档文件目录.xlsx`；若填写 `.xls`，会自动转换为 `.xlsx`。
