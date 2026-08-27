import unittest
from pathlib import Path

from src.workbook_reader import extract_headers, find_template


ROOT = Path(__file__).resolve().parents[1]


class WorkbookReaderTests(unittest.TestCase):
    def test_template_discovery_and_headers(self):
        template = find_template("Tafeln", ROOT / "input" / "Templates")
        headers = extract_headers(template, "Lochbleche")
        self.assertEqual(headers[0], "Handle")
        self.assertTrue(headers[-1].startswith("Variant Metafield:"))
        self.assertEqual(headers[headers.index("Image Src") + 1], "Image Command")
        self.assertNotIn("Inventory Quantity", headers)
        self.assertEqual(len(headers), 27)


if __name__ == "__main__":
    unittest.main()
