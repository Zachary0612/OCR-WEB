import logging
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import numpy as np
import fitz  # PyMuPDF
from paddleocr import PaddleOCR

# 图片最大像素面积限制（长×宽），超过则等比缩放
MAX_IMAGE_PIXELS = 2500 * 2500

from config import OCR_LANG, UPLOAD_DIR


def _cv_imread(path: str):
    """读取图片（支持中文路径）"""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv_imwrite(path: str, img):
    """保存图片（支持中文路径）"""
    ext = Path(path).suffix or '.jpg'
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)

logger = logging.getLogger(__name__)

# ===== 多模型管理 =====
_ocr_instance: PaddleOCR | None = None
_layout_pipeline = None
_vl_pipeline = None


def get_ocr() -> PaddleOCR:
    """获取 PP-OCRv5 基础 OCR 单例（快速文字识别，无版面分析）"""
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("正在初始化 PP-OCRv5 引擎 (lang=%s)...", OCR_LANG)
        _ocr_instance = PaddleOCR(
            lang=OCR_LANG,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            device="gpu:0",
        )
        logger.info("PP-OCRv5 引擎初始化完成")
    return _ocr_instance


def get_layout_pipeline():
    """获取 PP-StructureV3 版面解析管线单例（含 OCR + 表格识别 + 版面分析）"""
    global _layout_pipeline
    if _layout_pipeline is None:
        from paddlex import create_pipeline
        logger.info("正在初始化 PP-StructureV3 版面解析管线...")
        _layout_pipeline = create_pipeline(
            pipeline="layout_parsing",
            device="gpu:0",
        )
        logger.info("PP-StructureV3 版面解析管线初始化完成")
    return _layout_pipeline


def _maybe_resize_image(image_path: str) -> str:
    """如果图片过大，等比缩放后保存到临时文件，返回新路径；否则返回原路径"""
    try:
        img = _cv_imread(image_path)
        if img is None:
            return image_path
        h, w = img.shape[:2]
        pixels = h * w
        if pixels <= MAX_IMAGE_PIXELS:
            del img
            return image_path
        scale = (MAX_IMAGE_PIXELS / pixels) ** 0.5
        new_w = int(w * scale)
        new_h = int(h * scale)
        logger.info("缩放大图: %s (%dx%d -> %dx%d, %.0f%%)", Path(image_path).name, w, h, new_w, new_h, scale * 100)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        # 保存到 uploads 目录（纯 ASCII 路径，避免中文路径问题）
        suffix = Path(image_path).suffix or '.jpg'
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, dir=str(UPLOAD_DIR))
        tmp.close()
        _cv_imwrite(tmp.name, resized)
        del img, resized
        return tmp.name
    except Exception as e:
        logger.warning("图片缩放失败 %s: %s", image_path, e)
        return image_path


def _poly_to_list(poly) -> list[list[float]]:
    if hasattr(poly, "tolist"):
        poly = poly.tolist()
    if not poly or not isinstance(poly[0], (list, tuple)) or len(poly[0]) < 2:
        return []
    return [[float(p[0]), float(p[1])] for p in poly]


def _rect_contains_point(rect: list[float], x: float, y: float) -> bool:
    return len(rect) >= 4 and rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def _rect_from_polys(polys: list[list[list[float]]]) -> list[float]:
    xs = [pt[0] for poly in polys for pt in poly]
    ys = [pt[1] for poly in polys for pt in poly]
    if not xs or not ys:
        return []
    return [min(xs), min(ys), max(xs), max(ys)]


def _rect_area(rect: list[float]) -> float:
    if len(rect) < 4:
        return 0.0
    return max(0.0, rect[2] - rect[0]) * max(0.0, rect[3] - rect[1])


def _rect_intersection_area(a: list[float], b: list[float]) -> float:
    if len(a) < 4 or len(b) < 4:
        return 0.0
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.92
    return SequenceMatcher(None, a, b).ratio()


def _precise_region_bbox(label: str, bbox: list[float], content: str, page_lines: list[dict]):
    if len(bbox) < 4 or label in {"table", "figure", "image", "seal"}:
        return bbox, "rect"

    candidates = []
    for line in page_lines:
        poly = line.get("bbox") or []
        if not poly or not isinstance(poly[0], list):
            continue
        line_rect = _rect_from_polys([poly])
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        inter_area = _rect_intersection_area(bbox, line_rect)
        line_area = _rect_area(line_rect) or 1.0
        overlap_ratio = inter_area / line_area
        if _rect_contains_point(bbox, cx, cy) or overlap_ratio >= 0.45:
            candidates.append((line, overlap_ratio))

    if not candidates:
        return bbox, "rect"

    content_norm = "".join(str(content or "").split())
    matched = []
    if content_norm:
        for line, overlap_ratio in candidates:
            line_norm = "".join(str(line.get("text") or "").split())
            sim = _text_similarity(content_norm, line_norm)
            if line_norm and sim >= 0.72:
                matched.append((line, overlap_ratio, sim))

    if matched:
        matched.sort(key=lambda item: (item[2], item[1]), reverse=True)
        if len(content_norm) <= 32:
            chosen_lines = [matched[0][0]]
        else:
            chosen_lines = [item[0] for item in matched]
    else:
        candidates.sort(key=lambda item: item[1], reverse=True)
        if len(content_norm) <= 32:
            chosen_lines = [candidates[0][0]]
        else:
            chosen_lines = [item[0] for item in candidates if item[1] >= 0.45] or [candidates[0][0]]

    polys = [line["bbox"] for line in chosen_lines if line.get("bbox")]
    if not polys:
        return bbox, "rect"
    if len(polys) == 1:
        return polys[0], "poly"
    precise_rect = _rect_from_polys(polys)
    return precise_rect or bbox, "rect"


def get_vl_pipeline():
    """获取 PaddleOCR-VL-1.5 视觉语言模型管线单例（官网同款，识别质量最佳）"""
    global _vl_pipeline
    if _vl_pipeline is None:
        import os
        from paddlex import create_pipeline
        logger.info("正在初始化 PaddleOCR-VL-1.5 视觉语言模型管线...")
        # VL 管线的 PP-DocLayoutV3 需要 JSON 格式模型，临时切换标志
        old_flag = os.environ.get("FLAGS_json_format_model")
        os.environ.pop("FLAGS_json_format_model", None)
        try:
            _vl_pipeline = create_pipeline(
                pipeline="PaddleOCR-VL-1.5",
                device="gpu:0",
            )
            logger.info("PaddleOCR-VL-1.5 管线初始化完成")
        finally:
            if old_flag is not None:
                os.environ["FLAGS_json_format_model"] = old_flag
    return _vl_pipeline


# ===== PP-OCRv5 基础识别 =====
def ocr_image_basic(image_path: str) -> dict:
    """
    使用 PP-OCRv5 基础识别（快速，无版面分析）
    返回: {"lines": [...]}
    """
    ocr = get_ocr()
    results = ocr.predict(image_path)

    lines = []
    if results:
        for res in results:
            rec_texts = res.get("rec_texts", [])
            rec_scores = res.get("rec_scores", [])
            dt_polys = res.get("dt_polys", [])
            for idx in range(len(rec_texts)):
                text = rec_texts[idx]
                confidence = float(rec_scores[idx]) if idx < len(rec_scores) else 0.0
                bbox = dt_polys[idx].tolist() if idx < len(dt_polys) and hasattr(dt_polys[idx], 'tolist') else []
                lines.append({
                    "line_num": idx + 1,
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                })
    return {"lines": lines}


# ===== PP-StructureV3 版面解析 =====
def ocr_image_with_layout(image_path: str) -> dict:
    """
    使用 PP-StructureV3 版面解析（含表格识别）
    返回: {"regions": [...], "lines": [...]}
    """
    pipeline = get_layout_pipeline()
    results = list(pipeline.predict(
        image_path,
        use_doc_orientation_classify=True,
        use_doc_unwarping=True,
    ))

    regions = []
    lines = []
    line_num = 0

    for res in results:
        page_lines = []
        try:
            ocr_res = res["overall_ocr_res"]
            rec_texts = ocr_res.get("rec_texts", [])
            rec_scores = ocr_res.get("rec_scores", [])
            dt_polys = ocr_res.get("dt_polys", [])

            for idx in range(len(rec_texts)):
                text = rec_texts[idx]
                confidence = float(rec_scores[idx]) if idx < len(rec_scores) else 0.0
                bbox = _poly_to_list(dt_polys[idx]) if idx < len(dt_polys) else []
                line_num += 1
                line = {
                    "line_num": line_num,
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                }
                page_lines.append(line)
                lines.append(line)
        except Exception as e:
            logger.warning("提取 OCR 行数据失败: %s", e)

        parsing_list = res.get("parsing_res_list", [])
        for item in parsing_list:
            bbox_raw = item.get("block_bbox", [])
            label = item.get("block_label", "text")
            content = item.get("block_content", "")

            if hasattr(bbox_raw, 'tolist'):
                bbox_raw = bbox_raw.tolist()
            layout_bbox = [float(x) for x in bbox_raw[:4]] if len(bbox_raw) >= 4 else []
            precise_bbox, bbox_type = _precise_region_bbox(label, layout_bbox, content, page_lines)

            region = {
                "type": label,
                "bbox": precise_bbox,
                "bbox_type": bbox_type,
                "layout_bbox": layout_bbox,
                "content": content,
                "html": content if label == "table" else None,
            }
            regions.append(region)

    return {"regions": regions, "lines": lines}


# ===== PaddleOCR-VL-1.5 视觉语言模型识别 =====
def ocr_image_with_vl(image_path: str) -> dict:
    """
    使用 PaddleOCR-VL-1.5 视觉语言模型识别（官网同款，识别质量最佳）
    返回: {"regions": [...], "lines": []}
    """
    pipeline = get_vl_pipeline()
    results = list(pipeline.predict(
        image_path,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
    ))

    regions = []
    for res in results:
        parsing_list = res.get("parsing_res_list", [])
        for item in parsing_list:
            label = item.label if hasattr(item, 'label') else item.get("block_label", "text")
            content = item.content if hasattr(item, 'content') else item.get("block_content", "")
            bbox_raw = item.bbox if hasattr(item, 'bbox') else item.get("block_bbox", [])
            poly_pts = None
            if hasattr(item, 'polygon_points') and item.polygon_points is not None:
                poly_pts = item.polygon_points
            elif isinstance(item, dict) and item.get("block_polygon_points"):
                poly_pts = item["block_polygon_points"]

            if hasattr(bbox_raw, 'tolist'):
                bbox_raw = bbox_raw.tolist()
            bbox = [float(x) for x in bbox_raw[:4]] if len(bbox_raw) >= 4 else []

            bbox_type = "rect"
            final_bbox = bbox
            if poly_pts is not None:
                try:
                    pts = [[float(p[0]), float(p[1])] for p in poly_pts]
                    if len(pts) >= 3:
                        final_bbox = pts
                        bbox_type = "poly"
                except Exception:
                    pass

            region = {
                "type": label,
                "bbox": final_bbox,
                "bbox_type": bbox_type,
                "layout_bbox": bbox,
                "content": content,
                "html": content if label == "table" else None,
            }
            regions.append(region)

    return {"regions": regions, "lines": []}


# ===== PDF 转图片 =====
def pdf_to_images(pdf_path: str) -> list[str]:
    """将 PDF 转换为图片列表（保存到 uploads 目录避免中文路径问题）"""
    doc = fitz.open(pdf_path)
    image_paths = []
    prefix = Path(pdf_path).stem[:8]  # 取文件名前8字符作为前缀

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)  # 2x 分辨率
        pix = page.get_pixmap(matrix=mat)
        # 保存到 uploads 目录（纯 ASCII 路径）
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir=str(UPLOAD_DIR),
                                          prefix=f'page{page_num+1}_')
        tmp.close()
        pix.save(tmp.name)
        image_paths.append(tmp.name)

    doc.close()
    return image_paths


# ===== 统一文档识别入口 =====
def ocr_document(file_path: str, mode: str = "layout") -> dict:
    """
    对文档执行 OCR 识别（支持图片和 PDF）

    mode:
      - "vl":     PaddleOCR-VL-1.5 视觉语言模型（官网同款，识别质量最佳，推荐）
      - "layout": PP-StructureV3 版面解析（含表格识别）
      - "ocr":    PP-OCRv5 基础文字识别（快速，无版面分析）

    返回: {"page_count", "pages": [{page_num, regions?, lines}], "full_text", "mode"}
    """
    file_ext = Path(file_path).suffix.lower()
    pages = []
    temp_images = []

    # 选择识别函数
    if mode == "vl":
        recognize_fn = ocr_image_with_vl
    elif mode == "layout":
        recognize_fn = ocr_image_with_layout
    else:
        recognize_fn = ocr_image_basic

    try:
        if file_ext == ".pdf":
            image_paths = pdf_to_images(file_path)
            temp_images = image_paths
            for page_idx, img_path in enumerate(image_paths):
                resized_path = _maybe_resize_image(img_path)
                if resized_path != img_path:
                    temp_images.append(resized_path)
                page_result = recognize_fn(resized_path)
                page_result["page_num"] = page_idx + 1
                pages.append(page_result)
        else:
            resized_path = _maybe_resize_image(file_path)
            if resized_path != file_path:
                temp_images.append(resized_path)
            page_result = recognize_fn(resized_path)
            page_result["page_num"] = 1
            pages.append(page_result)

        # 拼接全文
        all_texts = []
        for page in pages:
            page_texts = []
            for region in page.get("regions", []):
                if region["type"] == "table":
                    page_texts.append("[表格]")
                elif region["content"]:
                    page_texts.append(region["content"])
            if not page_texts and page.get("lines"):
                page_texts = [line["text"] for line in page["lines"]]
            all_texts.append("\n".join(page_texts))

        if len(pages) > 1:
            full_text = "\n\n".join(
                f"--- 第 {i + 1} 页 ---\n{t}" for i, t in enumerate(all_texts)
            )
        else:
            full_text = all_texts[0] if all_texts else ""

        return {
            "page_count": len(pages),
            "pages": pages,
            "full_text": full_text,
            "mode": mode,
        }
    finally:
        for tmp in temp_images:
            try:
                Path(tmp).unlink(missing_ok=True)
            except Exception:
                pass
