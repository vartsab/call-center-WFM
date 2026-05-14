"""Seasonal naive baseline forecast for 30-minute call volume."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


FORECAST_FIELDS = [
    "interval_start_datetime",
    "actual_call_volume",
    "predicted_call_volume",
    "absolute_error",
    "squared_error",
    "absolute_percentage_error",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FORECAST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def aggregate_total_volume(rows: list[dict[str, str]]) -> dict[datetime, int]:
    totals: dict[datetime, int] = defaultdict(int)
    for row in rows:
        interval = datetime.fromisoformat(row["interval_start_datetime"])
        totals[interval] += int(row["call_volume"])
    return dict(sorted(totals.items()))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_lookup(train: dict[datetime, int]) -> tuple[dict[tuple[int, int], float], dict[int, float], float]:
    by_day_and_interval: dict[tuple[int, int], list[float]] = defaultdict(list)
    by_interval: dict[int, list[float]] = defaultdict(list)
    all_values: list[float] = []
    for interval, volume in train.items():
        half_hour_index = interval.hour * 2 + (1 if interval.minute >= 30 else 0)
        key = (interval.weekday(), half_hour_index)
        by_day_and_interval[key].append(float(volume))
        by_interval[half_hour_index].append(float(volume))
        all_values.append(float(volume))
    return (
        {key: mean(values) for key, values in by_day_and_interval.items()},
        {key: mean(values) for key, values in by_interval.items()},
        mean(all_values),
    )


def predict(
    interval: datetime,
    day_interval_avg: dict[tuple[int, int], float],
    interval_avg: dict[int, float],
    global_avg: float,
) -> float:
    half_hour_index = interval.hour * 2 + (1 if interval.minute >= 30 else 0)
    return day_interval_avg.get(
        (interval.weekday(), half_hour_index),
        interval_avg.get(half_hour_index, global_avg),
    )


def metrics(rows: list[dict[str, str]]) -> dict[str, float | int | str]:
    count = len(rows)
    mae = mean([float(row["absolute_error"]) for row in rows])
    rmse = math.sqrt(mean([float(row["squared_error"]) for row in rows]))
    ape_values = [
        float(row["absolute_percentage_error"])
        for row in rows
        if row["absolute_percentage_error"]
    ]
    mape = mean(ape_values) if ape_values else 0.0
    return {
        "test_intervals": count,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/forecasting_input_sample.csv")
    parser.add_argument("--output", default="data/processed/baseline_forecast_sample.csv")
    parser.add_argument("--summary-output", default="docs/baseline_forecast_summary.json")
    parser.add_argument("--test-days", type=int, default=7)
    args = parser.parse_args()

    totals = aggregate_total_volume(read_csv(Path(args.input)))
    if not totals:
        raise SystemExit("No forecasting input rows found.")

    max_date = max(interval.date() for interval in totals)
    test_start = max_date - timedelta(days=args.test_days - 1)
    train = {interval: volume for interval, volume in totals.items() if interval.date() < test_start}
    test = {interval: volume for interval, volume in totals.items() if interval.date() >= test_start}

    if not train or not test:
        raise SystemExit("Need both train and test intervals for baseline evaluation.")

    day_interval_avg, interval_avg, global_avg = build_lookup(train)
    forecast_rows: list[dict[str, str]] = []
    for interval, actual in test.items():
        predicted = predict(interval, day_interval_avg, interval_avg, global_avg)
        absolute_error = abs(actual - predicted)
        squared_error = absolute_error**2
        ape = absolute_error / actual if actual else 0.0
        forecast_rows.append(
            {
                "interval_start_datetime": interval.isoformat(timespec="seconds"),
                "actual_call_volume": str(actual),
                "predicted_call_volume": f"{predicted:.4f}",
                "absolute_error": f"{absolute_error:.4f}",
                "squared_error": f"{squared_error:.4f}",
                "absolute_percentage_error": f"{ape:.4f}" if actual else "",
            }
        )

    write_csv(Path(args.output), forecast_rows)
    summary = {
        "model": "seasonal naive mean by weekday and half-hour interval",
        "train_start": min(train).date().isoformat(),
        "train_end": max(train).date().isoformat(),
        "test_start": min(test).date().isoformat(),
        "test_end": max(test).date().isoformat(),
        **metrics(forecast_rows),
        "output": args.output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

