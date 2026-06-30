from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.app.domain.models import ConversionConfig
from backend.app.services.conversion import convert_zpl
from backend.app.services.runtime import local_renderer_script_path

RENDERER_AVAILABLE = bool(shutil.which("node")) and local_renderer_script_path().is_file()


@unittest.skipUnless(RENDERER_AVAILABLE, "Node.js renderer is not available")
class ConversionIntegrationTests(unittest.TestCase):
    def test_converts_zpl_to_pdf_with_real_renderer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zpl-integration-") as temp_dir:
            root = Path(temp_dir)
            input_path = root / "label.zpl"
            output_path = root / "label.pdf"
            input_path.write_text(
                "^XA^FO20,20^A0N,25,25^FDIntegration test^FS^XZ",
                encoding="utf-8",
            )

            result = convert_zpl(
                ConversionConfig(
                    file_path=str(input_path),
                    width_in=1.0,
                    height_in=1.0,
                    dpmm=6,
                    quality_scale=1,
                    channels_per_row=1,
                    output_format="pdf",
                    output_path=str(output_path),
                    png_prefix="label",
                )
            )

            self.assertEqual(result.total_rendered_labels, 1)
            self.assertTrue(output_path.is_file())
            self.assertTrue(output_path.read_bytes().startswith(b"%PDF"))
