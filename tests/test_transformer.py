import unittest

from src.transformer import build_handle, build_title, color_handle, format_handle, material_handle, sku_text, thickness_handle


class TransformerTests(unittest.TestCase):
    def test_sku_preservation(self):
        self.assertEqual(sku_text(12519.0), "12519")
        self.assertEqual(sku_text("001-A"), "001-A")

    def test_option_handles(self):
        self.assertEqual(thickness_handle("1,50 mm"), "1-5")
        self.assertEqual(material_handle("Aluminium (ohne Folie)"), "aluminium-ohne-folie")
        self.assertEqual(color_handle("weiß"), "weiss")

    def test_title_and_handle(self):
        title = build_title("Lochblech Tafelware", "Quadratlochung (gerade)", "Qg 5-16", True)
        self.assertEqual(title, "Lochblech Tafelware Quadratlochung (gerade) Qg 5-16")
        self.assertEqual(build_handle(title), "lochblech-tafelware-quadratlochung-gerade-qg-5-16")

    def test_hexagonal_reference_exception(self):
        title = build_title(
            "Lochblech Tafelware", "Sonderlochung", "Hexagonal - Hv 6-6,7", True
        )
        self.assertEqual(title, "Lochblech Tafelware Hexagonallochung Hexagonal 6-6,7")
        self.assertEqual(
            build_handle(title),
            "lochblech-tafelware-hexagonallochung-hexagonal-6-6-7",
        )

    def test_tafeln_format_handles(self):
        self.assertEqual(format_handle("Kleinformat (1000 x 2000 mm)"), "kleinformat")
        self.assertEqual(format_handle("Mittelformat (1250 x 2500 mm)"), "mittelformat")
        self.assertEqual(format_handle("Großformat (1500 x 3000 mm)"), "grossformat")
        self.assertEqual(format_handle("Sonderformat (2000 x 3000 mm)"), "sonderformat")

    def test_trailing_dash_is_removed_from_title(self):
        title = build_title(
            "Lochblech Tafelware",
            "Sonderlochung",
            "Seifenblase 5/10/15/20 –",
            True,
        )
        self.assertEqual(
            title,
            "Lochblech Tafelware Sonderlochung Seifenblase 5/10/15/20",
        )


if __name__ == "__main__":
    unittest.main()
