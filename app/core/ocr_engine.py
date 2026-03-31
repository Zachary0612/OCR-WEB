import logging
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    import cv2
except ImportError:  # pragma: no cover - environment dependent
    cv2 = None

try:
    import numpy as np
except ImportError:  # pragma: no cover - environment dependent
    np = None

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover - environment dependent
    PaddleOCR = Any

try:
    import fitz  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - environment dependent
    fitz = None

# 图片最大像素面积限制（长×宽），超过则等比缩放
MAX_IMAGE_PIXELS = 2500 * 2500
STRUCTURED_MAX_IMAGE_PIXELS = 5000 * 5000

from app.core.result_validation import normalize_table_data, table_data_to_text, table_html_to_data
from config import OCR_DEVICE, OCR_LANG, UPLOAD_DIR


def _cv_imread(path: str):
    """读取图片（支持中文路径）"""
    _require_cv_stack()
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _cv_imwrite(path: str, img):
    """保存图片（支持中文路径）"""
    _require_cv_stack()
    ext = Path(path).suffix or '.jpg'
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)

logger = logging.getLogger(__name__)

# ===== 多模型管理 =====
_ocr_instance = None
_layout_pipeline = None
_vl_pipeline = None
_UNSUPPORTED_PREDICT_ARG_RE = re.compile(r"unexpected keyword argument ['\"](?P<name>\w+)['\"]")
_MISSING_DOC_PREPROCESSOR_RE = re.compile(r"doc_preprocessor_pipeline")


def _pipeline_has_doc_preprocessor(pipeline) -> bool:
    if not hasattr(pipeline, "doc_preprocessor_pipeline"):
        return False
    try:
        return getattr(pipeline, "doc_preprocessor_pipeline") is not None
    except Exception:
        return False


def _require_fitz():
    if fitz is None:
        raise RuntimeError("PyMuPDF is required to process PDF files. Install PyMuPDF>=1.24.0.")
    return fitz


def _require_cv_stack():
    if cv2 is None or np is None:
        raise RuntimeError("OpenCV and NumPy are required to process images.")


def _require_paddleocr():
    if PaddleOCR is Any:
        raise RuntimeError("paddleocr is required to run OCR. Install paddleocr>=3.0.0.")


def get_ocr() -> PaddleOCR:
    """获取 PP-OCRv5 基础 OCR 单例（快速文字识别，无版面分析）"""
    global _ocr_instance
    if _ocr_instance is None:
        _require_paddleocr()
        logger.info("正在初始化 PP-OCRv5 引擎 (lang=%s, device=%s)...", OCR_LANG, OCR_DEVICE)
        # PP-OCRv5 server 模型在 PaddlePaddle 3.3.0 CPU 下有 PIR/oneDNN Bug
        # 当 device=cpu 时改用 mobile 模型，避免 ConvertPirAttribute2RuntimeAttribute 报错
        use_mobile = (OCR_DEVICE == "cpu")
        _ocr_instance = PaddleOCR(
            lang=OCR_LANG,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            device=OCR_DEVICE,
            text_detection_model_name="PP-OCRv5_mobile_det" if use_mobile else None,
            text_recognition_model_name="PP-OCRv5_mobile_rec" if use_mobile else None,
        )
        logger.info("PP-OCRv5 引擎初始化完成")
    return _ocr_instance


def get_layout_pipeline():
    """获取 PP-StructureV3 版面解析管线单例（含 OCR + 表格识别 + 版面分析）"""
    global _layout_pipeline
    if _layout_pipeline is None:
        from paddlex import create_pipeline
        logger.info("正在初始化 PP-StructureV3 版面解析管线 (device=%s)...", OCR_DEVICE)
        _layout_pipeline = create_pipeline(
            pipeline="layout_parsing",
            device=OCR_DEVICE,
        )
        logger.info("PP-StructureV3 版面解析管线初始化完成")
    return _layout_pipeline


def _maybe_resize_image(image_path: str, max_pixels: int | None = MAX_IMAGE_PIXELS) -> str:
    """如果图片过大，等比缩放后保存到临时文件，返回新路径；否则返回原路径"""
    try:
        if not max_pixels or max_pixels <= 0:
            return image_path
        img = _cv_imread(image_path)
        if img is None:
            return image_path
        h, w = img.shape[:2]
        pixels = h * w
        if pixels <= max_pixels:
            del img
            return image_path
        scale = (max_pixels / pixels) ** 0.5
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


def _item_polygon_points(item, attr_name: str = "polygon_points", dict_key: str = "block_polygon_points") -> list[list[float]]:
    if hasattr(item, attr_name):
        return _poly_to_list(getattr(item, attr_name))
    if isinstance(item, dict):
        return _poly_to_list(item.get(dict_key))
    return []


def _item_value(item, *names: str):
    for name in names:
        if hasattr(item, name):
            value = getattr(item, name)
            if value is not None:
                return value
        if isinstance(item, dict) and name in item:
            value = item.get(name)
            if value is not None:
                return value
    return None


def _coerce_layout_bbox(bbox_raw, poly_pts: list[list[float]] | None = None) -> tuple[list[float], list[list[float]]]:
    if hasattr(bbox_raw, "tolist"):
        bbox_raw = bbox_raw.tolist()
    poly = poly_pts or []
    if isinstance(bbox_raw, list) and bbox_raw and isinstance(bbox_raw[0], (list, tuple)):
        raw_poly = _poly_to_list(bbox_raw)
        if raw_poly and not poly:
            poly = raw_poly
        return (_rect_from_polys([raw_poly]) if raw_poly else []), poly
    if isinstance(bbox_raw, (list, tuple)) and len(bbox_raw) >= 4:
        return [float(x) for x in bbox_raw[:4]], poly
    return [], poly


def _looks_like_html_table(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return "<table" in lowered or ("<tr" in lowered and ("<td" in lowered or "<th" in lowered))


def _looks_like_markdown_table(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    pipe_lines = [line for line in lines if line.count("|") >= 2]
    if len(pipe_lines) < 2:
        return False
    divider = pipe_lines[1].replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
    return divider == ""


def _has_table_content(table_data: list[list[str]] | None) -> bool:
    return bool(table_data) and any(str(cell).strip() for row in table_data for cell in row)


def _normalize_table_payload(raw_table) -> list[list[str]] | None:
    if raw_table is None:
        return None
    try:
        table_data = normalize_table_data(raw_table)
    except Exception:
        return None
    return table_data if _has_table_content(table_data) else None


def _markdown_table_to_data(value: Any) -> list[list[str]] | None:
    if not _looks_like_markdown_table(value):
        return None
    lines = [line.strip() for line in str(value).splitlines() if line.strip() and line.count("|") >= 1]
    rows = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        divider = stripped.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
        if index == 1 and divider == "":
            continue
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        rows.append([cell.strip() for cell in stripped.split("|")])
    return _normalize_table_payload(rows)


def _plain_text_table_to_data(value: Any) -> list[list[str]] | None:
    if not isinstance(value, str):
        return None
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    rows = []
    max_cols = 0
    for line in lines:
        if "\t" in line:
            cells = [cell.strip() for cell in line.split("\t")]
        else:
            cells = [cell.strip() for cell in re.split(r"\s{2,}", line) if cell.strip()]
        if len(cells) < 2:
            return None
        rows.append(cells)
        max_cols = max(max_cols, len(cells))
    padded_rows = [row + [""] * (max_cols - len(row)) for row in rows]
    return _normalize_table_payload(padded_rows)


def _extract_table_payload(item, label: str, content: str) -> tuple[list[list[str]] | None, str | None, str]:
    raw_label = str(label or "").strip().lower()
    table_data = _normalize_table_payload(_item_value(item, "table_data", "block_table_data", "cells"))
    html = _item_value(item, "html", "block_html", "table_html")
    markdown = _item_value(item, "markdown", "block_markdown", "table_markdown")

    nested = _item_value(item, "res", "result", "block_result", "table_result")
    if isinstance(nested, dict):
        if table_data is None:
            table_data = _normalize_table_payload(nested.get("table_data") or nested.get("cells"))
        if html is None:
            html = nested.get("html") or nested.get("table_html")
        if markdown is None:
            markdown = nested.get("markdown") or nested.get("table_markdown")

    if table_data is None and isinstance(content, str):
        if _looks_like_html_table(content):
            html = content
        elif _looks_like_markdown_table(content):
            markdown = content
        elif raw_label in {"table", "table_body"}:
            table_data = _plain_text_table_to_data(content)

    if table_data is None and isinstance(html, str) and _looks_like_html_table(html):
        try:
            table_data = _normalize_table_payload(table_html_to_data(html))
        except Exception:
            table_data = None

    if table_data is None and isinstance(markdown, str) and markdown.strip():
        table_data = _markdown_table_to_data(markdown)

    table_content = str(content or "")
    if table_data is not None:
        table_content = table_data_to_text(table_data)
    elif isinstance(markdown, str) and markdown.strip():
        table_content = markdown.strip()

    html_value = html.strip() if isinstance(html, str) and _looks_like_html_table(html) else None
    return table_data, html_value, table_content


def _canonical_region_type(label: Any, has_table_payload: bool = False) -> str:
    lowered = str(label or "text").strip().lower()
    if has_table_payload or lowered in {"table", "table_body"}:
        return "table"
    if "seal" in lowered or "stamp" in lowered:
        return "seal"
    return lowered or "text"


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _line_rect(line: dict) -> list[float]:
    bbox = line.get("bbox") or []
    if bbox and isinstance(bbox[0], list):
        return _rect_from_polys([bbox])
    if len(bbox) >= 4:
        return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
    return []


def _line_center(poly: list[list[float]]) -> tuple[float, float]:
    if not poly:
        return 0.0, 0.0
    return (
        sum(point[0] for point in poly) / len(poly),
        sum(point[1] for point in poly) / len(poly),
    )


def _normalize_seal_content(value: Any) -> str:
    lines = [line.strip() for line in str(value or "").splitlines() if line.strip()]
    if not lines:
        return ""
    joined = "\n".join(lines)
    if len(lines) > 4:
        return ""
    if len(joined) > 48 and re.search(r"[，。；、]", joined):
        return ""
    return joined


def _seal_content_from_lines(layout_bbox: list[float], page_lines: list[dict], raw_content: str = "") -> str:
    if len(layout_bbox) < 4 or not page_lines:
        return _normalize_seal_content(raw_content)

    candidates = []
    for line in page_lines:
        text = str(line.get("text") or "").strip()
        poly = line.get("bbox") or []
        if not text or not poly or not isinstance(poly[0], list):
            continue
        line_rect = _line_rect(line)
        if len(line_rect) < 4:
            continue
        cx, cy = _line_center(poly)
        overlap_ratio = _rect_intersection_area(layout_bbox, line_rect) / (_rect_area(line_rect) or 1.0)
        if _rect_contains_point(layout_bbox, cx, cy) or overlap_ratio >= 0.55:
            candidates.append((text, overlap_ratio))

    if not candidates:
        return _normalize_seal_content(raw_content)

    candidates.sort(key=lambda item: item[1], reverse=True)
    seen = set()
    selected = []
    for text, _ in candidates:
        normalized = _compact_text(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if len(normalized) > 24 and re.search(r"[，。；、]", text):
            continue
        selected.append(text)
        if len(selected) >= 4:
            break

    return "\n".join(selected) if selected else _normalize_seal_content(raw_content)


def _region_rect(region: dict) -> list[float]:
    layout_bbox = region.get("layout_bbox") or []
    if len(layout_bbox) >= 4:
        return [float(layout_bbox[0]), float(layout_bbox[1]), float(layout_bbox[2]), float(layout_bbox[3])]
    bbox = region.get("bbox") or []
    if bbox and isinstance(bbox[0], list):
        return _rect_from_polys([bbox])
    if len(bbox) >= 4:
        return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
    return []


def _overlap_on_smaller(a: list[float], b: list[float]) -> float:
    denominator = min(_rect_area(a), _rect_area(b))
    if denominator <= 0:
        return 0.0
    return _rect_intersection_area(a, b) / denominator


def _filter_output_regions(regions: list[dict]) -> list[dict]:
    if not regions:
        return regions

    kept = []
    kept_tables: list[dict[str, Any]] = []
    for region in regions:
        region_type = str(region.get("type") or "text")
        region_rect = _region_rect(region)
        region_text = _compact_text(region.get("content"))

        if region_type == "table":
            duplicated = any(
                _overlap_on_smaller(region_rect, table["rect"]) >= 0.82
                and (
                    not region_text
                    or not table["text"]
                    or region_text in table["text"]
                    or table["text"] in region_text
                )
                for table in kept_tables
            )
            if duplicated:
                continue
            kept.append(region)
            kept_tables.append({"rect": region_rect, "text": region_text})
            continue

        if region_type in {"text", "paragraph", "number"} and region_text:
            covered_by_table = any(
                _overlap_on_smaller(region_rect, table["rect"]) >= 0.88
                and (not table["text"] or region_text in table["text"])
                for table in kept_tables
            )
            if covered_by_table:
                continue

        kept.append(region)

    return kept


def _extract_page_lines(res, line_num_start: int = 0) -> tuple[list[dict], int]:
    page_lines = []
    line_num = line_num_start
    try:
        ocr_res = _item_value(res, "overall_ocr_res") or {}
        rec_texts = _item_value(ocr_res, "rec_texts") or []
        rec_scores = _item_value(ocr_res, "rec_scores") or []
        dt_polys = _item_value(ocr_res, "dt_polys") or []

        for idx in range(len(rec_texts)):
            text = rec_texts[idx]
            confidence = float(rec_scores[idx]) if idx < len(rec_scores) else 0.0
            bbox = _poly_to_list(dt_polys[idx]) if idx < len(dt_polys) else []
            line_num += 1
            page_lines.append(
                {
                    "line_num": line_num,
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                }
            )
    except Exception as exc:
        logger.warning("提取 OCR 行数据失败: %s", exc)
    return page_lines, line_num


def _predict_structured(pipeline, image_path: str):
    kwargs = {
        "use_doc_orientation_classify": True,
        "use_doc_unwarping": True,
        "use_table_recognition": True,
        "use_seal_recognition": True,
        "layout_shape_mode": "poly",
        "layout_merge_bboxes_mode": "union",
        "format_block_content": True,
    }

    if not _pipeline_has_doc_preprocessor(pipeline):
        disabled = []
        for arg_name in ("use_doc_orientation_classify", "use_doc_unwarping"):
            if arg_name in kwargs:
                kwargs.pop(arg_name)
                disabled.append(arg_name)
        if disabled:
            logger.info(
                "当前管线未初始化 doc_preprocessor_pipeline，预测前跳过 %s。",
                ", ".join(disabled),
            )

    while True:
        try:
            return list(pipeline.predict(image_path, **kwargs))
        except TypeError as exc:
            match = _UNSUPPORTED_PREDICT_ARG_RE.search(str(exc))
            if not match:
                raise
            arg_name = match.group("name")
            if arg_name not in kwargs:
                raise
            logger.warning("predict 参数 %s 当前不可用，自动回退。", arg_name)
            kwargs.pop(arg_name)
        except Exception as exc:
            message = str(exc)
            if not _MISSING_DOC_PREPROCESSOR_RE.search(message):
                raise

            disabled = []
            for arg_name in ("use_doc_orientation_classify", "use_doc_unwarping"):
                if arg_name in kwargs:
                    kwargs.pop(arg_name)
                    disabled.append(arg_name)

            if not disabled:
                raise

            logger.warning(
                "当前管线缺少 doc_preprocessor_pipeline，已自动关闭 %s 后重试。",
                ", ".join(disabled),
            )


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
        logger.info("正在初始化 PaddleOCR-VL-1.5 视觉语言模型管线 (device=%s)...", OCR_DEVICE)
        # VL 管线的 PP-DocLayoutV3 需要 JSON 格式模型，临时切换标志
        old_flag = os.environ.get("FLAGS_json_format_model")
        os.environ.pop("FLAGS_json_format_model", None)
        try:
            _vl_pipeline = create_pipeline(
                pipeline="PaddleOCR-VL-1.5",
                device=OCR_DEVICE,
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
    results = _predict_structured(pipeline, image_path)

    regions = []
    lines = []
    line_num = 0

    for res in results:
        page_lines, line_num = _extract_page_lines(res, line_num)
        lines.extend(page_lines)

        parsing_list = _item_value(res, "parsing_res_list") or []
        for item in parsing_list:
            bbox_raw = _item_value(item, "block_bbox", "bbox") or []
            poly_pts = _item_polygon_points(item, dict_key="block_polygon_points")
            layout_bbox, poly_pts = _coerce_layout_bbox(bbox_raw, poly_pts)
            raw_label = _item_value(item, "block_label", "label") or "text"
            content = str(_item_value(item, "block_content", "content") or "")
            table_data, table_html, content = _extract_table_payload(item, str(raw_label), content)
            label = _canonical_region_type(raw_label, has_table_payload=table_data is not None or bool(table_html))
            if label == "seal":
                content = _seal_content_from_lines(layout_bbox, page_lines, raw_content=content)

            if poly_pts:
                precise_bbox, bbox_type = poly_pts, "poly"
            else:
                precise_bbox, bbox_type = _precise_region_bbox(label, layout_bbox, content, page_lines)

            region = {
                "type": label,
                "bbox": precise_bbox,
                "bbox_type": bbox_type,
                "layout_bbox": layout_bbox,
                "content": content,
            }
            if table_html:
                region["html"] = table_html
            if table_data is not None:
                region["table_data"] = table_data
            regions.append(region)

    return {"regions": _filter_output_regions(regions), "lines": lines}


# ===== PaddleOCR-VL-1.5 视觉语言模型识别 =====
def ocr_image_with_vl(image_path: str) -> dict:
    """
    使用 PaddleOCR-VL-1.5 视觉语言模型识别（官网同款，识别质量最佳）
    返回: {"regions": [...], "lines": []}
    """
    pipeline = get_vl_pipeline()
    results = _predict_structured(pipeline, image_path)

    regions = []
    line_num = 0
    for res in results:
        page_lines, line_num = _extract_page_lines(res, line_num)
        parsing_list = _item_value(res, "parsing_res_list") or []
        for item in parsing_list:
            raw_label = _item_value(item, "label", "block_label") or "text"
            content = str(_item_value(item, "content", "block_content") or "")
            bbox_raw = _item_value(item, "bbox", "block_bbox") or []
            poly_pts = _item_polygon_points(item, dict_key="block_polygon_points")
            bbox, poly_pts = _coerce_layout_bbox(bbox_raw, poly_pts)
            table_data, table_html, content = _extract_table_payload(item, str(raw_label), content)
            label = _canonical_region_type(raw_label, has_table_payload=table_data is not None or bool(table_html))
            if label == "seal":
                content = _seal_content_from_lines(bbox, page_lines, raw_content=content)

            bbox_type = "rect"
            final_bbox = bbox
            if poly_pts:
                final_bbox = poly_pts
                bbox_type = "poly"

            region = {
                "type": label,
                "bbox": final_bbox,
                "bbox_type": bbox_type,
                "layout_bbox": bbox,
                "content": content,
            }
            if table_html:
                region["html"] = table_html
            if table_data is not None:
                region["table_data"] = table_data
            regions.append(region)

    return {"regions": _filter_output_regions(regions), "lines": []}


# ===== PDF 转图片 =====
def pdf_to_images(pdf_path: str) -> list[str]:
    """将 PDF 转换为图片列表（保存到 uploads 目录避免中文路径问题）"""
    fitz_module = _require_fitz()
    doc = fitz_module.open(pdf_path)
    image_paths = []
    prefix = Path(pdf_path).stem[:8]  # 取文件名前8字符作为前缀

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz_module.Matrix(2, 2)  # 2x 分辨率
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

    max_pixels = MAX_IMAGE_PIXELS if mode == "ocr" else STRUCTURED_MAX_IMAGE_PIXELS

    try:
        if file_ext == ".pdf":
            image_paths = pdf_to_images(file_path)
            temp_images = image_paths
            for page_idx, img_path in enumerate(image_paths):
                resized_path = _maybe_resize_image(img_path, max_pixels=max_pixels)
                if resized_path != img_path:
                    temp_images.append(resized_path)
                page_result = recognize_fn(resized_path)
                page_result["page_num"] = page_idx + 1
                pages.append(page_result)
        else:
            resized_path = _maybe_resize_image(file_path, max_pixels=max_pixels)
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
