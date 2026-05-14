import unittest
from datetime import datetime

from src.forecasting.build_feature_matrix import aggregate_total_volume, build_features


class FeatureMatrixTests(unittest.TestCase):
    def test_empty_feature_matrix(self) -> None:
        self.assertEqual(build_features({}), [])

    def test_feature_matrix_marks_federal_holiday(self) -> None:
        rows = build_features(
            {
                datetime(2025, 1, 1, 0, 0): 2,
                datetime(2025, 1, 20, 0, 0): 3,
            }
        )
        holiday_rows = [row for row in rows if row["is_federal_holiday"] == "1"]
        holiday_names = {row["federal_holiday_name"] for row in holiday_rows}

        self.assertIn("New Year's Day", holiday_names)
        self.assertIn("Martin Luther King Jr. Day", holiday_names)

    def test_aggregate_total_volume(self) -> None:
        totals = aggregate_total_volume(
            [
                {"interval_start_datetime": "2025-01-01T00:00:00", "call_volume": "2"},
                {"interval_start_datetime": "2025-01-01T00:00:00", "call_volume": "3"},
            ]
        )

        self.assertEqual(totals[datetime(2025, 1, 1, 0, 0)], 5)


if __name__ == "__main__":
    unittest.main()
