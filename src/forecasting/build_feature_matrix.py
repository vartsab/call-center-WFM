"""Build a holiday-aware feature matrix for interval call-volume forecasting."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path

try:
    from .us_federal_holidays import nearest_holiday_distance, us_federal_holidays
except ImportError:
    from us_federal_holidays import nearest_holiday_distance, us_federal_holidays


FIELDS = [
    "interval_start_datetime",
    "calendar_date",
    "actual_call_volume",
    "half_hour_index",
    "half_hour_sin",
    "half_hour_cos",
    "hour",
    "day_of_week_index",
    "day_of_week_sin",
    "day_of_week_cos",
    "day_of_month",
    "week_of_year",
    "month",
    "is_weekend",
    "is_federal_holiday",
    "federal_holiday_name",
    "days_to_nearest_federal_holiday",
    "lag_1_interval",
    "lag_2_intervals",
    "lag_48_intervals",
    "lag_96_intervals",
    "lag_336_intervals",
    "rolling_mean_48_intervals",
    "rolling_mean_336_intervals",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def aggregate_total_volume(rows: list[dict[str, str]]) -> dict[datetime, int]:
    totals: dict[datetime, int] = defaultdict(int)
    for row in rows:
        interval = datetime.fromisoformat(row["interval_start_datetime"])
        totals[interval] += int(row["call_volume"])
    return dict(sorted(totals.items()))


def complete_interval_series(totals: dict[datetime, int], interval_minutes: int = 30) -> dict[datetime, int]:
    if not totals:
        return {}

    start_date = min(interval.date() for interval in totals)
    end_date = max(interval.date() for interval in totals)
    current = datetime.combine(start_date, time(0, 0))
    end = datetime.combine(end_date, time(23, 30))
    complete: dict[datetime, int] = {}
    while current <= end:
        complete[current] = totals.get(current, 0)
        current += timedelta(minutes=interval_minutes)
    return complete


def rolling_mean(values: list[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def value_at(intervals: list[datetime], volumes: dict[datetime, int], index: int, lag: int) -> int:
    lag_index = index - lag
    if lag_index < 0:
        return 0
    return volumes[intervals[lag_index]]


def build_features(totals: dict[datetime, int]) -> list[dict[str, str]]:
    complete = complete_interval_series(totals)
    intervals = list(complete)
    if not intervals:
        return []

    years = [interval.year for interval in intervals]
    holidays = us_federal_holidays(min(years), max(years))
    rows: list[dict[str, str]] = []

    for index, interval in enumerate(intervals):
        interval_date = interval.date()
        holiday_name = holidays.get(interval_date, "")
        prior_48 = [complete[intervals[position]] for position in range(max(0, index - 48), index)]
        prior_336 = [complete[intervals[position]] for position in range(max(0, index - 336), index)]
        half_hour_index = interval.hour * 2 + (1 if interval.minute >= 30 else 0)
        half_hour_radians = 2 * math.pi * half_hour_index / 48
        day_of_week_radians = 2 * math.pi * interval.weekday() / 7
        rows.append(
            {
                "interval_start_datetime": interval.isoformat(timespec="seconds"),
                "calendar_date": interval_date.isoformat(),
                "actual_call_volume": str(complete[interval]),
                "half_hour_index": str(half_hour_index),
                "half_hour_sin": f"{math.sin(half_hour_radians):.6f}",
                "half_hour_cos": f"{math.cos(half_hour_radians):.6f}",
                "hour": str(interval.hour),
                "day_of_week_index": str(interval.weekday()),
                "day_of_week_sin": f"{math.sin(day_of_week_radians):.6f}",
                "day_of_week_cos": f"{math.cos(day_of_week_radians):.6f}",
                "day_of_month": str(interval.day),
                "week_of_year": str(interval_date.isocalendar().week),
                "month": str(interval.month),
                "is_weekend": "1" if interval.weekday() >= 5 else "0",
                "is_federal_holiday": "1" if holiday_name else "0",
                "federal_holiday_name": holiday_name,
                "days_to_nearest_federal_holiday": str(
                    nearest_holiday_distance(interval_date, holidays)
                ),
                "lag_1_interval": str(value_at(intervals, complete, index, 1)),
                "lag_2_intervals": str(value_at(intervals, complete, index, 2)),
                "lag_48_intervals": str(value_at(intervals, complete, index, 48)),
                "lag_96_intervals": str(value_at(intervals, complete, index, 96)),
                "lag_336_intervals": str(value_at(intervals, complete, index, 336)),
                "rolling_mean_48_intervals": f"{rolling_mean(prior_48):.4f}",
                "rolling_mean_336_intervals": f"{rolling_mean(prior_336):.4f}",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/forecasting_input_sample.csv")
    parser.add_argument("--output", default="data/processed/forecast_features_sample.csv")
    args = parser.parse_args()

    rows = build_features(aggregate_total_volume(read_csv(Path(args.input))))
    write_csv(Path(args.output), rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
