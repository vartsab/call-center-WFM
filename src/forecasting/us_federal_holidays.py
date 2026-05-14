"""US federal holiday calendar helpers for forecasting features."""

from __future__ import annotations

from datetime import date, timedelta


def observed_fixed_holiday(value: date) -> date:
    if value.weekday() == 5:
        return value - timedelta(days=1)
    if value.weekday() == 6:
        return value + timedelta(days=1)
    return value


def nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != weekday:
        current += timedelta(days=1)
    return current + timedelta(days=7 * (occurrence - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        current = date(year, 12, 31)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def us_federal_holidays_for_year(year: int) -> dict[date, str]:
    holidays: dict[date, str] = {
        nth_weekday(year, 1, 0, 3): "Martin Luther King Jr. Day",
        nth_weekday(year, 2, 0, 3): "Washington's Birthday",
        last_weekday(year, 5, 0): "Memorial Day",
        nth_weekday(year, 9, 0, 1): "Labor Day",
        nth_weekday(year, 10, 0, 2): "Columbus Day",
        nth_weekday(year, 11, 3, 4): "Thanksgiving Day",
    }

    fixed_holidays = {
        date(year, 1, 1): "New Year's Day",
        date(year, 6, 19): "Juneteenth National Independence Day",
        date(year, 7, 4): "Independence Day",
        date(year, 11, 11): "Veterans Day",
        date(year, 12, 25): "Christmas Day",
    }
    for actual_date, name in fixed_holidays.items():
        holidays[observed_fixed_holiday(actual_date)] = name

    return holidays


def us_federal_holidays(start_year: int, end_year: int) -> dict[date, str]:
    holidays: dict[date, str] = {}
    for year in range(start_year - 1, end_year + 2):
        holidays.update(us_federal_holidays_for_year(year))
    return {
        holiday_date: name
        for holiday_date, name in holidays.items()
        if start_year <= holiday_date.year <= end_year
    }


def nearest_holiday_distance(value: date, holidays: dict[date, str]) -> int:
    if not holidays:
        return 999
    return min(abs((holiday_date - value).days) for holiday_date in holidays)
