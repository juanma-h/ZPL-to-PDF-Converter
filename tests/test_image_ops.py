from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from backend.app.services.image_ops import compose_labels_side_by_side, ensure_pdf_extension


class ImageOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="zpl-image-ops-")
        self.tmp_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

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

    def test_compose_labels_side_by_side_applies_die_cut_margin(self) -> None:
        image_paths = [
            self.create_image("one-margin.png", (100, 50), "red"),
            self.create_image("two-margin.png", (80, 40), "blue"),
        ]
        output_files = compose_labels_side_by_side(
            image_paths=image_paths,
            output_dir=str(self.tmp_dir),
            output_prefix="merged-margin",
            channels_per_row=2,
            label_margin_px=10,
        )

        self.assertEqual(len(output_files), 1)
        merged = Image.open(output_files[0])
        self.assertEqual(merged.size, (240, 70))
        merged.close()

    def test_compose_single_label_with_die_cut_margin_creates_padded_canvas(self) -> None:
        image_paths = [
            self.create_image("one-single-margin.png", (60, 30), "green"),
        ]
        output_files = compose_labels_side_by_side(
            image_paths=image_paths,
            output_dir=str(self.tmp_dir),
            output_prefix="single-margin",
            channels_per_row=1,
            label_margin_px=8,
        )

        self.assertEqual(len(output_files), 1)
        merged = Image.open(output_files[0])
        self.assertEqual(merged.size, (76, 46))
        merged.close()


if __name__ == "__main__":
    unittest.main()
