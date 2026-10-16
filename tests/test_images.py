import tempfile
import unittest
from pathlib import Path

from src.images import (add_records_to_baseline, confirm_pending_upload,
                        image_columns, image_filename, load_baseline,
                        load_pending_upload, save_baseline, save_pending_upload)


class ImageTests(unittest.TestCase):
    def test_filename_ignores_domain_and_query(self):
        first = "https://old.example/files/Product_Image.jpg?v=1"
        second = "https://new.example/other/Product_Image.jpg?v=999"
        self.assertEqual(image_filename(first), image_filename(second))

    def test_gallery_column_order(self):
        record = {"Bild 3": "c", "Bild": "a", "Bild 2": "b", "Other": "x"}
        self.assertEqual(image_columns(record), ["Bild", "Bild 2", "Bild 3"])

    def test_baseline_update(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "baseline.json"
            added = add_records_to_baseline(path, [{"Bild": "https://x.test/A.jpg?v=1"}])
            self.assertEqual(added, 1)
            self.assertEqual(load_baseline(path), {"a.jpg"})

    def test_pending_upload_survives_and_can_be_confirmed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            baseline = root / "baseline.json"
            pending = root / "pending.json"
            save_baseline(baseline, {"old.jpg"})
            count = save_pending_upload(
                pending,
                group="Tafeln",
                category="Lochbleche",
                output_file=root / "output.xlsx",
                image_urls=["https://example.test/new.jpg?v=2"],
            )
            self.assertEqual(count, 1)
            pending_data = load_pending_upload(pending)
            self.assertEqual(pending_data["filenames"], ["new.jpg"])
            self.assertEqual(pending_data["groups"], ["Tafeln"])
            self.assertEqual(pending_data["categories"], ["Lochbleche"])
            self.assertEqual(confirm_pending_upload(baseline, pending), 1)
            self.assertEqual(load_baseline(baseline), {"old.jpg", "new.jpg"})
            self.assertFalse(pending.exists())


if __name__ == "__main__":
    unittest.main()
