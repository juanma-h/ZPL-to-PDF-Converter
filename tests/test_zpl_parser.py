from __future__ import annotations

import unittest

from backend.app.services.zpl_parser import (
    analyze_zpl_text,
    extract_quantity_from_label,
    split_zpl_labels,
)


class ZplParserTests(unittest.TestCase):
    def test_split_detects_multiple_labels(self) -> None:
        content = "^XA\n^FO10,10^FDUno^FS\n^XZ\n^XA\n^FO10,10^FDDos^FS\n^XZ"
        labels = split_zpl_labels(content)
        self.assertEqual(len(labels), 2)

    def test_split_wraps_content_without_markers(self) -> None:
        labels = split_zpl_labels("^FO10,10^FDHola^FS")
        self.assertEqual(labels, ["^XA\n^FO10,10^FDHola^FS\n^XZ"])

    def test_extract_quantity_defaults_to_one(self) -> None:
        self.assertEqual(extract_quantity_from_label("^XA^FO10,10^FDHola^FS^XZ"), 1)

    def test_extract_quantity_reads_pq(self) -> None:
        self.assertEqual(extract_quantity_from_label("^XA^PQ5^XZ"), 5)

    def test_analyze_counts_labels_and_quantities(self) -> None:
        stats = analyze_zpl_text("^XA^PQ2^XZ\n^XA^XZ")
        self.assertEqual(stats.label_count, 2)
        self.assertEqual(stats.total_quantity, 3)
        self.assertTrue(stats.has_quantity_commands)


if __name__ == "__main__":
    unittest.main()
