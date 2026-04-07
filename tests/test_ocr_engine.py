import unittest
from unittest.mock import patch

from app.core import ocr_engine


class _FakePipeline:
    def __init__(self, side_effects, *, has_doc_preprocessor=True):
        self.side_effects = list(side_effects)
        self.calls = []
        self.doc_preprocessor_pipeline = object() if has_doc_preprocessor else None

    def predict(self, **kwargs):
        self.calls.append(kwargs)
        effect = self.side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


class _FakeOCR:
    def predict(self, image_path):
        return [
            {
                "rec_texts": ["第一行", "第二行"],
                "rec_scores": [0.98, 0.87],
                "dt_polys": [
                    [[0, 0], [10, 0], [10, 10], [0, 10]],
                    [[0, 12], [20, 12], [20, 22], [0, 22]],
                ],
            }
        ]


class OCREngineTests(unittest.TestCase):
    def test_predict_structured_retries_without_unsupported_argument(self):
        pipeline = _FakePipeline(
            [
                TypeError("predict() got an unexpected keyword argument 'format_block_content'"),
                [{"page": 1}],
            ]
        )

        result = ocr_engine._predict_structured(pipeline, "demo.png", profile="layout")

        self.assertEqual(result, [{"page": 1}])
        self.assertEqual(len(pipeline.calls), 2)
        self.assertIn("format_block_content", pipeline.calls[0])
        self.assertNotIn("format_block_content", pipeline.calls[1])

    def test_predict_structured_retries_when_doc_preprocessor_is_missing(self):
        pipeline = _FakePipeline(
            [
                RuntimeError("doc_preprocessor_pipeline is not initialized"),
                [{"page": 1}],
            ]
        )

        result = ocr_engine._predict_structured(pipeline, "demo.png", profile="layout")

        self.assertEqual(result, [{"page": 1}])
        self.assertEqual(len(pipeline.calls), 2)
        self.assertIn("use_doc_orientation_classify", pipeline.calls[0])
        self.assertIn("use_doc_unwarping", pipeline.calls[0])
        self.assertNotIn("use_doc_orientation_classify", pipeline.calls[1])
        self.assertNotIn("use_doc_unwarping", pipeline.calls[1])

    def test_geometry_helpers_return_expected_values(self):
        rect = ocr_engine._rect_from_polys(
            [
                [[0, 0], [10, 0], [10, 10], [0, 10]],
                [[5, 5], [15, 5], [15, 20], [5, 20]],
            ]
        )

        self.assertEqual(rect, [0, 0, 15, 20])
        self.assertEqual(ocr_engine._rect_area(rect), 300)
        self.assertEqual(ocr_engine._rect_intersection_area([0, 0, 10, 10], [5, 5, 15, 20]), 25)
        self.assertTrue(ocr_engine._rect_contains_point([0, 0, 10, 10], 6, 6))
        self.assertFalse(ocr_engine._rect_contains_point([0, 0, 10, 10], 12, 6))

    def test_ocr_image_basic_returns_lines(self):
        with patch.object(ocr_engine, "get_ocr", return_value=_FakeOCR()):
            result = ocr_engine.ocr_image_basic("demo.png")

        self.assertEqual(len(result["lines"]), 2)
        self.assertEqual(result["lines"][0]["text"], "第一行")
        self.assertEqual(result["lines"][0]["bbox"], [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]])
        self.assertEqual(result["lines"][1]["line_num"], 2)

    def test_predict_structured_vl_sets_device(self):
        pipeline = _FakePipeline([[{"page": 1}]])

        fake_device = type("FakeDevice", (), {"set_device": lambda self, value: None})()
        fake_paddle = type("FakePaddle", (), {"device": fake_device})()

        with patch.dict("sys.modules", {"paddle": fake_paddle}):
            result = ocr_engine._predict_structured(pipeline, "demo.png", profile="vl")

        self.assertEqual(result, [{"page": 1}])
        self.assertEqual(pipeline.calls[0]["input"], "demo.png")


if __name__ == "__main__":
    unittest.main()
