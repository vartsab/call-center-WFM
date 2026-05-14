import unittest
from datetime import date

from src.forecasting.us_federal_holidays import (
    nearest_holiday_distance,
    us_federal_holidays,
)


class USFederalHolidayTests(unittest.TestCase):
    def test_2025_january_holidays(self) -> None:
        holidays = us_federal_holidays(2025, 2025)

        self.assertEqual(holidays[date(2025, 1, 1)], "New Year's Day")
        self.assertEqual(holidays[date(2025, 1, 20)], "Martin Luther King Jr. Day")

    def test_observed_fixed_holiday(self) -> None:
        holidays = us_federal_holidays(2026, 2026)

        self.assertEqual(holidays[date(2026, 7, 3)], "Independence Day")

    def test_nearest_holiday_distance(self) -> None:
        holidays = us_federal_holidays(2025, 2025)

        self.assertEqual(nearest_holiday_distance(date(2025, 1, 19), holidays), 1)


if __name__ == "__main__":
    unittest.main()
