"""La versión pública no debe aparentar mediciones o fincas reales."""

import os
import unittest
from unittest.mock import patch

from gateways import _source_data


class PublicMapTests(unittest.TestCase):
    def test_without_private_files_there_are_no_map_points(self):
        with patch.dict(os.environ, {"GATEWAYS_KMZ_PATH": "", "GATEWAYS_XLSX_PATH": ""}):
            features, roster, is_private, warning = _source_data()
        self.assertEqual(features, [])
        self.assertEqual(roster, [])
        self.assertFalse(is_private)
        self.assertIsNone(warning)

    def test_invalid_kmz_does_not_fall_back_to_fake_points(self):
        with patch.dict(os.environ, {"GATEWAYS_KMZ_PATH": "does-not-exist.kmz",
                                     "GATEWAYS_XLSX_PATH": ""}):
            features, roster, is_private, warning = _source_data()
        self.assertEqual(features, [])
        self.assertEqual(roster, [])
        self.assertFalse(is_private)
        self.assertIn("KMZ", warning)


if __name__ == "__main__":
    unittest.main()
