"""Pruebas con datos inventados: los archivos empresariales nunca van al repo."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import Workbook

from gateway_roster import load_roster, normalized_name, reconcile_features


def point(name: str, zone: str) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-74.0, 4.0]},
            "properties": {"kind": "finca", "name": name, "region": zone}}


class GatewayRosterTests(unittest.TestCase):
    def test_excel_order_and_zone_carry_forward(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "inventado.xlsx"
            book = Workbook()
            sheet = book.active
            sheet.title = "Detallado"
            sheet.append(["Zona", "Fincas"])
            sheet.append(["Centro", "Finca A"])
            sheet.append([None, "Finca B"])
            sheet.append(["Total Centro", None])
            sheet.append(["Norte", "Finca C"])
            book.save(path)

            rows = load_roster(path)
            self.assertEqual([row["name"] for row in rows], ["Finca A", "Finca B", "Finca C"])
            self.assertEqual([row["zone_order"] for row in rows], [1, 2, 1])

    def test_normalization_is_conservative(self):
        self.assertEqual(normalized_name("Finca La Prueba"), normalized_name("LA PRUEBA"))
        self.assertEqual(normalized_name("Café Azul"), normalized_name("Cafe Azul"))
        self.assertNotEqual(normalized_name("Parcela 1"), normalized_name("PARCELA"))

    def test_reconciliation_respects_zone_and_keeps_unmatched_point(self):
        roster = [{"zone": "Centro", "name": "Finca La Prueba", "order": 1, "zone_order": 1}]
        features = [point("LA PRUEBA", "Centro"), point("LA PRUEBA", "Norte")]
        mapped, rows = reconcile_features(features, roster)
        self.assertTrue(rows[0]["on_map"])
        self.assertEqual(mapped[0]["properties"]["kind"], "finca")
        self.assertEqual(mapped[1]["properties"]["kind"], "referencia_punto")
        self.assertEqual(features[1]["properties"]["kind"], "finca")


if __name__ == "__main__":
    unittest.main()
