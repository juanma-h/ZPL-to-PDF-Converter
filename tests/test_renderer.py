from __future__ import annotations

import unittest

from backend.app.core.errors import RenderError
from backend.app.services.renderer import parse_renderer_output


class RendererOutputTests(unittest.TestCase):
    def test_parse_renderer_output_uses_last_json_line(self) -> None:
        payload = """
        diagnostic line
        {"files": ["one.png", "two.png"]}
        """
        self.assertEqual(parse_renderer_output(payload), ["one.png", "two.png"])

    def test_parse_renderer_output_rejects_empty_payload(self) -> None:
        with self.assertRaises(RenderError):
            parse_renderer_output("")

    def test_parse_renderer_output_requires_files(self) -> None:
        with self.assertRaises(RenderError):
            parse_renderer_output('{"files": []}')


if __name__ == "__main__":
    unittest.main()
