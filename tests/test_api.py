from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient, Response

from backend.app.api.routes.zpl import safe_stem
from backend.app.domain.models import ConversionConfig, ConversionResult
from backend.app.main import app


class ApiTests(unittest.TestCase):
    def request(self, method: str, url: str, **kwargs) -> Response:
        async def send() -> Response:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(send())

    def test_health_reports_application_status(self) -> None:
        response = self.request("GET", "/api/v1/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(payload["status"], {"ok", "degraded"})
        self.assertEqual(payload["version"], "3.0.0")

    def test_analyze_accepts_zpl_upload(self) -> None:
        response = self.request(
            "POST",
            "/api/v1/zpl/analyze",
            files={"file": ("labels.zpl", b"^XA^PQ2^XZ\n^XA^XZ", "text/plain")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["label_count"], 2)
        self.assertEqual(response.json()["total_quantity"], 3)

    def test_convert_returns_generated_pdf(self) -> None:
        def fake_convert(config: ConversionConfig) -> ConversionResult:
            output = Path(config.output_path)
            output.write_bytes(b"%PDF-1.4\n%%EOF")
            return ConversionResult(
                message="ok",
                output_path=str(output),
                output_format="pdf",
                generated_count=1,
                source_label_count=1,
                total_rendered_labels=1,
            )

        with patch("backend.app.api.routes.zpl.convert_zpl", side_effect=fake_convert):
            response = self.request(
                "POST",
                "/api/v1/zpl/convert",
                files={"file": ("shipping.zpl", b"^XA^XZ", "text/plain")},
                data={"output_format": "pdf"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("shipping.pdf", response.headers["content-disposition"])
        self.assertEqual(response.headers["x-rendered-labels"], "1")

    def test_safe_stem_removes_path_and_special_characters(self) -> None:
        self.assertEqual(safe_stem("../../my labels!.txt"), "my_labels")


if __name__ == "__main__":
    unittest.main()
