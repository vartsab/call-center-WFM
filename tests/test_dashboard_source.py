import os
import unittest
from unittest.mock import patch

from app.streamlit.app import dashboard_source_mode, load_data


class DashboardSourceTests(unittest.TestCase):
    def test_dashboard_source_mode_defaults_to_auto(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(dashboard_source_mode(), "auto")

    def test_dashboard_source_mode_rejects_unknown_value(self) -> None:
        with patch.dict(os.environ, {"CALLCENTER_DASHBOARD_SOURCE": "warehouse"}, clear=True):
            self.assertEqual(dashboard_source_mode(), "auto")

    def test_csv_mode_loads_generated_sample(self) -> None:
        with patch.dict(os.environ, {"CALLCENTER_DASHBOARD_SOURCE": "csv"}, clear=True):
            source, data = load_data()

        self.assertEqual(source, "CSV sample")
        self.assertFalse(data["volume_30min"].empty)
        self.assertFalse(data["forecasting_input"].empty)


if __name__ == "__main__":
    unittest.main()
