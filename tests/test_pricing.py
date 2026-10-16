import unittest

from src.pricing import (build_consolidated_price_data,
                         build_tafeln_price_data,
                         build_zuschnitte_price_data,
                         consolidated_filename)


class PricingTests(unittest.TestCase):
    def test_only_selected_tiers_are_exported(self):
        data, warnings = build_tafeln_price_data([{
            "Artikel-Nr": 557.0,
            "Preis 1": 351,
            "Preis 2": 211,
            "Preis 3": 180,
            "Preis 4": 163,
            "Preis 7": 111,
            "Preis 10": 86,
        }])
        self.assertEqual(data, {"557": {"2": 211.0, "4": 163.0, "7": 111.0, "10": 86.0}})
        self.assertEqual(warnings, [])

    def test_zuschnitte_prices_use_commercial_whole_number_rounding(self):
        data, warnings = build_zuschnitte_price_data([
            {"Artikel-Nr": 1, "Preis": 62.5},
            {"Artikel-Nr": 2, "Preis": 92.8},
        ])
        self.assertEqual(data, {"1": 63, "2": 93})
        self.assertEqual(warnings, [])

    def test_consolidated_data_contains_multiple_categories(self):
        records = {
            "Lochblech": [{"Artikel-Nr": 2, "Preis": 92.8}],
            "Wellengitter": [{"Artikel-Nr": 12519, "Preis": 115}],
        }
        data, warnings = build_consolidated_price_data("Zuschnitte", records)
        self.assertEqual(data, {"2": 93, "12519": 115})
        self.assertEqual(warnings, [])

    def test_group_filenames(self):
        self.assertEqual(consolidated_filename("Tafeln"), "tafelware_mr_json_values.json")
        self.assertEqual(consolidated_filename("Zuschnitte"), "quadratmeterpreise_zuschnitte_values.json")


if __name__ == "__main__":
    unittest.main()
