import tempfile
import unittest
from pathlib import Path

from app.core.auth import create_session_token, verify_session_token
from app.core.path_security import PathSecurityError, ensure_allowed_path
from app.core.result_validation import normalize_result_pages, serialize_pages_text, table_html_to_data


class AuthTests(unittest.TestCase):
    def test_session_token_round_trip(self):
        token = create_session_token("tester", ttl=60)
        payload = verify_session_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "tester")

    def test_expired_session_token_is_rejected(self):
        token = create_session_token("tester", ttl=-1)
        self.assertIsNone(verify_session_token(token))


class PathSecurityTests(unittest.TestCase):
    def test_allowed_path_must_stay_inside_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            allowed_file = root / "sample.pdf"
            allowed_file.write_text("ok", encoding="utf-8")

            resolved = ensure_allowed_path(str(allowed_file), expect_file=True, roots=[root])
            self.assertEqual(resolved, allowed_file.resolve(strict=False))

            with self.assertRaises(PathSecurityError):
                ensure_allowed_path(str(root.parent / "outside.pdf"), roots=[root])


class ResultValidationTests(unittest.TestCase):
    def test_html_table_is_converted_to_structured_rows(self):
        pages = normalize_result_pages(
            [
                {
                    "page_num": 1,
                    "regions": [
                        {
                            "type": "table",
                            "bbox": [0, 0, 100, 100],
                            "html": "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>",
                        }
                    ],
                }
            ]
        )

        table_region = pages[0]["regions"][0]
        self.assertEqual(table_region["table_data"], [["A", "B"], ["1", "2"]])
        self.assertNotIn("html", table_region)
        self.assertIn("A\tB", serialize_pages_text(pages))

    def test_table_html_parser_handles_line_breaks(self):
        rows = table_html_to_data("<table><tr><td>Line 1<br/>Line 2</td></tr></table>")
        self.assertEqual(rows, [["Line 1\nLine 2"]])


if __name__ == "__main__":
    unittest.main()
