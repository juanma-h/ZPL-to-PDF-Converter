from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SRC = PROJECT_ROOT / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from zpl_converter.image_ops import compose_labels_side_by_side, ensure_pdf_extension


class ImageOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = PROJECT_ROOT / "build" / "tmp" / "tests"
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.tmp_dir = self.tmp_root / f"image-ops-{uuid4().hex[:8]}"
        self.tmp_dir.mkdir(parents=True, exist_ok=False)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def create_image(self, name: str, size: tuple[int, int], color: str) -> str:
        path = self.tmp_dir / name
        image = Image.new("RGB", size, color)
        image.save(path, format="PNG")
        image.close()
        return str(path)

    def test_ensure_pdf_extension_appends_suffix(self) -> None:
        self.assertEqual(ensure_pdf_extension("output"), "output.pdf")
        self.assertEqual(ensure_pdf_extension("output.PDF"), "output.PDF")

    def test_compose_labels_side_by_side_builds_single_row(self) -> None:
        image_paths = [
            self.create_image("one.png", (100, 50), "red"),
            self.create_image("two.png", (80, 40), "blue"),
        ]
        output_files = compose_labels_side_by_side(
            image_paths=image_paths,
            output_dir=str(self.tmp_dir),
            output_prefix="merged",
            channels_per_row=2,
        )

        self.assertEqual(len(output_files), 1)
        merged = Image.open(output_files[0])
        self.assertEqual(merged.size, (200, 50))
        merged.close()


if __name__ == "__main__":
    unittest.main()
