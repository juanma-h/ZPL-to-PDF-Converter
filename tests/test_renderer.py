from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from zpl_converter.renderer import parse_renderer_output


class RendererOutputTests(unittest.TestCase):
    def test_parse_renderer_output_uses_last_json_line(self) -> None:
        payload = """
        diagnostic line
        {"files": ["one.png", "two.png"]}
        """
        self.assertEqual(parse_renderer_output(payload), ["one.png", "two.png"])

    def test_parse_renderer_output_rejects_empty_payload(self) -> None:
        with self.assertRaises(RuntimeError):
            parse_renderer_output("")

    def test_parse_renderer_output_requires_files(self) -> None:
        with self.assertRaises(RuntimeError):
            parse_renderer_output('{"files": []}')


if __name__ == "__main__":
    unittest.main()
