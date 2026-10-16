import unittest

from config.categories import get_category
from src.converter import _build_rows, _validate_variant_combinations


class ConverterRuleTests(unittest.TestCase):
    def test_duplicate_option_combination_is_rejected(self):
        config = get_category("Tafeln", "Lochbleche")
        common = {
            "Def-Lochung": "Rundlochung (versetzt)",
            "Lochgröße und -abstand": "Rv 10-15",
            "Material": "Stahl",
            "Stärke": "1,00 mm",
            "Format": "Großformat (1500 x 3000 mm)",
        }
        records = [
            {**common, "Artikel-Nr": 2843},
            {**common, "Artikel-Nr": 557},
        ]
        with self.assertRaisesRegex(ValueError, "2843, 557"):
            _validate_variant_combinations(records, config)

    def test_gallery_rows_follow_product_header_and_are_image_only(self):
        config = get_category("Tafeln", "Lochbleche")
        headers = [
            "Handle", "Command", "Title", "Image Src", "Image Position",
            "Image Command", "Variant Command", "Option1 Name", "Option1 Value",
            "Option1 Linked To", "Option2 Name", "Option2 Value", "Option2 Linked To",
            "Option3 Name", "Option3 Value", "Option3 Linked To", "Variant SKU",
            "Variant Price",
        ]
        records = [{
            "Def-Lochung": "Test",
            "Lochgröße und -abstand": "T 1",
            "Material": "Stahl",
            "Stärke": "1,00 mm",
            "Format": "Kleinformat",
            "Artikel-Nr": 1,
            "Preis 1": 10,
            "Bild": "https://example.test/primary.jpg",
            "Bild 2": "https://example.test/gallery.jpg",
        }]
        rows = _build_rows(records, headers, config, [], set())
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Image Position"], 1)
        self.assertEqual(rows[1]["Image Position"], 2)
        populated = {key for key, value in rows[1].items() if value not in (None, "")}
        self.assertEqual(populated, {"Handle", "Image Src", "Image Position", "Image Command"})


if __name__ == "__main__":
    unittest.main()
