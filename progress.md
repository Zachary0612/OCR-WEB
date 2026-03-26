# 开发进度记录

## 2025-03-25

### [初始化] 项目规划与需求确认

**完成内容：**
- 确认项目需求：基于 PaddleOCR 3.0 的文档识别系统
- 确认交互方式：Web 界面 + REST API 双模式
- 创建 `README.md` 项目大纲文档
- 创建 `progress.md` 进度记录文档

**技术决策：**
- 后端框架选用 FastAPI（异步高性能，自带 Swagger 文档）
- 数据库默认 SQLite（轻量无需安装，后续可切换 MySQL）
- ORM 使用 SQLAlchemy
- 前端使用 HTML + TailwindCSS + 原生 JS（轻量，无需 Node 构建）

**下一步：**
- 搭建项目目录结构
- 创建 requirements.txt
- 安装 PaddlePaddle 和 PaddleOCR 3.0

---

### [环境搭建] 安装依赖与配置

**环境检测结果：**
- Python 3.13.9（系统）→ 不兼容 PaddlePaddle
- Python 3.12.10 可用 → 创建 `.venv` 虚拟环境
- NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)
- CUDA Driver 12.6

**完成内容：**
- 用 Python 3.12 创建虚拟环境 `d:\OCR\.venv`
- 安装 PaddlePaddle GPU 3.3.1 (CUDA 12.6)
- 安装 PaddleOCR 3.4.0 及所有依赖
- 安装 FastAPI, uvicorn, SQLAlchemy, aiosqlite, PyMuPDF 等
- 清理 C 盘 pip 缓存（释放 2.5GB）
- 配置 pip 缓存目录到 `D:\pip_cache`
- 配置 PaddleOCR 模型和 HuggingFace 缓存到 `D:\OCR\.cache\`

**创建的项目文件：**
- `config.py` — 配置文件（缓存、数据库、OCR 参数）
- `main.py` — FastAPI 应用入口
- `app/db/database.py` — 异步数据库连接
- `app/db/models.py` — OCRTask + OCRResult 数据模型
- `app/schemas/ocr_schemas.py` — Pydantic 响应模型
- `app/core/ocr_engine.py` — PaddleOCR 引擎封装
- `app/services/ocr_service.py` — 业务服务层
- `app/api/routes.py` — REST API 路由
- `templates/index.html` — Web 前端页面

**下一步：**
- 启动服务测试
- 验证 OCR 识别功能

---

### [服务启动] 修复 PaddleOCR 3.x 兼容性并成功启动

**问题与修复：**
1. PaddleOCR 3.x API 变更：`use_gpu` → `device="gpu:0"`，`ocr()` → `predict()`，返回格式改为 `rec_texts/rec_scores/dt_polys`
2. FastAPI `regex` 参数已废弃 → 改为 `pattern`
3. HuggingFace xet 下载协议在当前网络环境下失败（模型文件 0 字节）→ 切换为百度 BOS 下载源
4. PaddleX 缓存目录环境变量名：`PADDLE_PDX_CACHE_HOME`（非 `PADDLEX_HOME`）
5. C 盘残留损坏模型缓存导致反复失败 → 清理后重新下载

**配置变更（config.py）：**
- `PADDLE_PDX_CACHE_HOME` → `D:\OCR\.cache\paddlex`（模型存 D 盘）
- `PADDLE_PDX_MODEL_SOURCE=bos`（百度 BOS 下载源）
- `FLAGS_json_format_model=0`（传统模型格式）
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True`（跳过连通性检查）

**模型下载完成（存储在 D:\OCR\.cache\paddlex\）：**
- PP-LCNet_x1_0_textline_ori（文本行方向分类）
- PP-OCRv5_server_det（文字检测）
- PP-OCRv5_server_rec（文字识别）

**服务状态：**
- 启动成功，运行在 http://localhost:8000
- Web 界面可访问
- API 文档：http://localhost:8000/docs

**下一步：**
- 用实际图片/PDF 测试 OCR 识别功能
- 验证数据库存储是否正常

---

### [前端重构] 左右分栏布局 + 源文件预览

**变更内容：**
- 重构前端为三栏布局：左侧文件列表/上传、中间源文件预览、右侧 OCR 结果
- 中间预览面板支持图片直接显示、PDF 翻页浏览（基于 PDF.js）、缩放
- 右侧结果面板支持"文档解析"和"逐行详情"两个 Tab 切换
- 新增复制文本按钮、Toast 提示
- 新增全局拖放上传覆盖层
- 新增 API 接口 `GET /api/ocr/tasks/{id}/file` 用于从服务器获取源文件预览
- 历史记录高亮当前选中项，显示文件类型图标
- 修复 Starlette 新版 `TemplateResponse` 参数顺序

**修改的文件：**
- `templates/index.html` — 完全重写前端界面
- `app/api/routes.py` — 新增文件预览接口，添加 FileResponse 导入

---

### [数据库迁移] SQLite → PostgreSQL

**变更内容：**
- 安装 `asyncpg` 异步 PostgreSQL 驱动
- 创建 PostgreSQL 数据库 `ocr_db`（用户 postgres，密码 123456）
- 修改 `config.py` 数据库连接字符串为 `postgresql+asyncpg://postgres:123456@localhost:5432/ocr_db`
- 更新 `requirements.txt` 添加 asyncpg 依赖
- ORM 层（SQLAlchemy）自动适配，无需修改模型代码

**迁移原因：**
- PostgreSQL 支持 JSONB、全文搜索、并发访问
- 适合生产环境部署和甲方交付

**修改的文件：**
- `config.py` — 数据库连接字符串
- `requirements.txt` — 添加 asyncpg

---

### [文档] 编写项目部署文档

**变更内容：**
- 创建 `DEPLOYMENT.md` 项目部署文档（甲方交付用）
- 包含：环境要求、安装步骤、数据库配置、启动运行、API 说明、常见问题

---

### [前端重构2] PaddleOCR 官网风格 + 可编辑 OCR 区块 + bbox 高亮 + JSON 标签页

**变更内容：**

**后端：**
- 新增 `PUT /api/ocr/tasks/{id}` 端点：支持编辑后保存（更新 result_json 和 full_text）
- 修复 `model_dump()` → `model_dump(mode='json')` 解决 datetime 序列化 500 错误
- 所有返回任务详情的端点统一使用 `mode='json'` 序列化

**前端（templates/index.html 完全重写）：**
- **右面板双标签页**：「文档解析」显示可编辑 OCR 区块，「JSON」显示深蓝主题语法高亮 JSON
- **可编辑 OCR 区块**：每个识别行渲染为独立区块，显示置信度，支持复制、双击进入编辑模式（contentEditable）
- **bbox 高亮覆盖层**：点击 OCR 区块时，在源图预览上用 SVG polygon 高亮对应检测框
- **bbox 定位修复**：SVG viewBox 设为图片原始尺寸，width/height 设为渲染尺寸，确保坐标精准对齐
- **保存栏**：编辑文本后底部出现保存栏，点击保存调用 PUT 接口更新数据库
- **JSON 查看器**：深蓝背景、行号、语法高亮（键名蓝色、字符串绿色、数字黄色、布尔紫色）
- **预览面板重构**：图片和 PDF canvas 包裹在 `.pw` 容器中，SVG 覆盖层绝对定位

**修复 git revert 损坏的 .venv：**
- 重新安装 click、fastapi、Pillow、pandas、python-bidi、setuptools
- 从 PaddlePaddle 官方 cu126 源重新安装 paddlepaddle-gpu==3.3.1（579MB）

**修改的文件：**
- `templates/index.html` — 完全重写 CSS + HTML 结构 + JavaScript
- `app/api/routes.py` — 新增 PUT 端点，修复 model_dump 序列化

**验证状态：**
- 服务启动成功，所有 API 端点返回 200 OK
- 上传识别、历史列表、任务详情、文件预览均正常工作

---

### [核心升级] PP-StructureV3 版面解析 + 表格识别

**变更内容：**

**OCR 引擎升级（ocr_engine.py 完全重写）：**
- 从基础 `PaddleOCR`（仅文字检测+识别）升级为 `paddlex.create_pipeline(pipeline="layout_parsing")`
- 新管线包含 7 个模型：
  - PP-LCNet_x1_0_doc_ori（文档方向分类）
  - UVDoc（文档校正）
  - RT-DETR-H_layout_17cls（17类版面检测：标题/文本/表格/图片/公式/印章等）
  - PP-OCRv4_server_det（文字检测）
  - PP-OCRv4_server_rec（文字识别）
  - PP-OCRv4_server_seal_det（印章检测）
  - SLANet_plus（表格结构识别→HTML）
- 输出格式扩展：每页包含 `regions`（结构化区域）和 `lines`（逐行 OCR）
  - regions: `{type, bbox, content, html}` — 表格区域的 html 字段为 `<table>` HTML
  - lines: `{line_num, text, confidence, bbox}` — 保持向后兼容

**安装依赖：**
- `pip install "paddleocr[doc-parser]"` — 安装版面解析额外依赖（beautifulsoup4, lxml, openpyxl, scikit-learn 等）

**前端更新（index.html）：**
- `buildBlocks()` 优先渲染 `regions`（版面解析结果），回退到 `lines`（旧格式兼容）
- 表格区域：直接渲染 `<table>` HTML，添加 `parsed-table` 样式
- 标题区域：加粗加大字号，标注「标题」标签
- 文本区域：可编辑文本块，标注「文本」标签
- 图片区域：标注「图片」标签
- 区域类型标签（彩色小标签）：标题黄色、表格蓝色、图片粉色、文本灰色
- bbox 高亮支持矩形 `[x1,y1,x2,y2]`（regions）和多边形 `[[x1,y1],...]`（lines）两种格式
- 新增 `editRegion()`、`cpRegion()`、`rebuildFullText()` 函数

**修改的文件：**
- `app/core/ocr_engine.py` — 完全重写，使用 layout_parsing 管线
- `main.py` — 预加载 layout_parsing 管线
- `templates/index.html` — 表格渲染 + 区域类型标签 + 双格式 bbox

**验证状态：**
- 服务启动成功，7 个模型全部下载并加载
- API 端点正常响应

---

### [多模型集成] PP-OCRv5 + PP-StructureV3 双引擎 + 文档全面更新

**变更内容：**

**双模型引擎（ocr_engine.py 重写）：**
- **PP-OCRv5**（`get_ocr()`）：快速文字识别，无版面分析，适合纯文本文档
- **PP-StructureV3**（`get_layout_pipeline()`）：版面解析 + 表格识别 + OCR，适合复杂文档
- `ocr_document(file_path, mode)` 统一入口，`mode="layout"` 或 `mode="ocr"` 选择引擎
- 启动时预加载两个引擎（main.py: `get_ocr()` + `get_layout_pipeline()`）

**API 更新（routes.py）：**
- `POST /api/ocr/upload?mode=layout|ocr` 新增 `mode` 查询参数
- 默认 `mode=layout`（版面解析+表格），可选 `mode=ocr`（纯文字快速）

**前端更新（index.html）：**
- 顶栏新增模式切换按钮：「版面解析」/「纯文字」
- 上传时 `fetch('/api/ocr/upload?mode=${ocrMode}')` 传递当前模式

**Bug 修复：**
- PyMuPDF (fitz) 被 git revert 损坏导致 `module 'fitz' has no attribute 'open'`
- PDF 上传后显示「无内容」→ `pip install --force-reinstall PyMuPDF` 修复
- 修复后 PDF 表格识别正常，4 页 PDF 成功识别

**文档全面更新：**
- `README.md` — 完全重写：双模型引擎、10 个集成模型列表、JSONB 数据库设计、完整 API 列表
- `DEPLOYMENT.md` — 更新：双模型核心功能、表格识别、版面分析、PUT 端点、安装 doc-parser 依赖
- `progress.md` — 补全所有变更记录

**修改的文件：**
- `app/core/ocr_engine.py` — 双模型引擎（PP-OCRv5 + PP-StructureV3）
- `app/api/routes.py` — mode 查询参数
- `app/services/ocr_service.py` — mode 参数传递
- `main.py` — 预加载双模型
- `templates/index.html` — 模式切换 UI
- `README.md` — 完全重写
- `DEPLOYMENT.md` — 全面更新

**验证状态：**
- 双模型启动成功，PP-OCRv5 + PP-StructureV3 均正常加载
- PDF 上传识别成功（4 页，mode=layout），表格识别正常
- 图片上传识别成功（mode=layout），版面区域分类正确

---

### 2026-03-26 — 前端预览修复 + 官网风格对齐 + 数据库清理

**修复的问题：**

1. **源文件预览不显示（根因：CSS specificity）**
   - `.pw { display:block }` 和 `.pw img { display:block }` 覆盖了 Tailwind 的 `.hidden { display:none }`
   - 导致图片/PDF 预览始终隐藏或始终显示，无法正确切换
   - 修复：移除 `.pw` 和 `.pw img/canvas` 的 `display` 属性，全部改用 `style.display` 内联样式控制可见性

2. **SVG bbox 覆盖层不对齐**
   - 新增 `syncSvgToElement()` 函数，统一处理图片和 PDF canvas 的 SVG 定位
   - SVG 使用 `offsetLeft/offsetTop` 精确覆盖在居中元素上
   - PDF 的 viewBox 使用 2x 缩放坐标系（与 `pdf_to_images` 的 `Matrix(2,2)` 一致）

3. **区域类型映射不完整**
   - PaddleX 返回 `"image"` 类型，但前端只处理 `"figure"`
   - 新增完整的 17 类标签映射：image/paragraph/caption/abstract/toc/note/footnote/sidebar 等

4. **弃用的 ocr_results 数据库表**
   - 删除了 `OCRResult` 模型和 `ocr_results` 表（数据已迁移到 `ocr_tasks.result_json` JSONB 列）
   - 确认 `result_json` 正确存储（已验证 task 44/50/51/54 均有数据）

5. **PDF.js 本地化**
   - 从 CDN 切换到本地 `/static/js/pdf.min.js` 和 `/static/js/pdf.worker.min.js`
   - 避免国内网络访问 CDN 失败导致 PDF 预览空白

**修改文件：**
- `templates/index.html` — CSS/JS 全面修复
- `app/db/models.py` — 移除 OCRResult 模型
- `static/js/pdf.min.js` + `static/js/pdf.worker.min.js` — 本地 PDF.js
