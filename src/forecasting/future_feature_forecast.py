"""Train the selected feature model on full history and forecast a future horizon."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

try:
    from .build_feature_matrix import FIELDS as FEATURE_MATRIX_FIELDS
    from .sklearn_model_compare import FEATURE_COLUMNS, FORECAST_FIELDS, feature_vector, model_candidates
    from .us_federal_holidays import nearest_holiday_distance, us_federal_holidays
except ImportError:
    from build_feature_matrix import FIELDS as FEATURE_MATRIX_FIELDS
    from sklearn_model_compare import FEATURE_COLUMNS, FORECAST_FIELDS, feature_vector, model_candidates
    from us_federal_holidays import nearest_holiday_distance, us_federal_holidays


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_half_hours(start_date: date, end_date: date) -> list[datetime]:
    current = datetime.combine(start_date, time(0, 0))
    end = datetime.combine(end_date, time(23, 30))
    intervals: list[datetime] = []
    while current <= end:
        intervals.append(current)
        current += timedelta(minutes=30)
    return intervals


def rolling_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def lookup_prior_values(
    interval: datetime,
    volume_lookup: dict[datetime, float],
    interval_count: int,
) -> list[float]:
    return [
        volume_lookup.get(interval - timedelta(minutes=30 * offset), 0.0)
        for offset in range(interval_count, 0, -1)
    ]


def build_future_feature_row(
    interval: datetime,
    volume_lookup: dict[datetime, float],
    holidays: dict[date, str],
) -> dict[str, str]:
    interval_date = interval.date()
    holiday_name = holidays.get(interval_date, "")
    half_hour_index = interval.hour * 2 + (1 if interval.minute >= 30 else 0)
    half_hour_radians = 2 * math.pi * half_hour_index / 48
    day_of_week_radians = 2 * math.pi * interval.weekday() / 7
    prior_48 = lookup_prior_values(interval, volume_lookup, 48)
    prior_336 = lookup_prior_values(interval, volume_lookup, 336)

    return {
        "interval_start_datetime": interval.isoformat(timespec="seconds"),
        "calendar_date": interval_date.isoformat(),
        "actual_call_volume": "",
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
        "days_to_nearest_federal_holiday": str(nearest_holiday_distance(interval_date, holidays)),
        "lag_1_interval": f"{volume_lookup.get(interval - timedelta(minutes=30), 0.0):.4f}",
        "lag_2_intervals": f"{volume_lookup.get(interval - timedelta(minutes=60), 0.0):.4f}",
        "lag_48_intervals": f"{volume_lookup.get(interval - timedelta(days=1), 0.0):.4f}",
        "lag_96_intervals": f"{volume_lookup.get(interval - timedelta(days=2), 0.0):.4f}",
        "lag_336_intervals": f"{volume_lookup.get(interval - timedelta(days=7), 0.0):.4f}",
        "rolling_mean_48_intervals": f"{rolling_mean(prior_48):.4f}",
        "rolling_mean_336_intervals": f"{rolling_mean(prior_336):.4f}",
    }


def train_model(rows: list[dict[str, str]], model_name: str) -> Any:
    candidates = model_candidates()
    if model_name not in candidates:
        raise SystemExit(f"Unknown model '{model_name}'. Options: {', '.join(sorted(candidates))}")
    model = candidates[model_name]
    x_train = [feature_vector(row) for row in rows]
    y_train = [float(row["actual_call_volume"]) for row in rows]
    model.fit(x_train, y_train)
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/full_forecast_features.csv")
    parser.add_argument("--forecast-output", default="data/processed/future_sklearn_forecast.csv")
    parser.add_argument("--feature-output", default="data/processed/future_forecast_features.csv")
    parser.add_argument("--summary-output", default="docs/future_forecast_summary.json")
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument("--end-date", default="2026-01-31")
    parser.add_argument("--model", default="hist_gradient_boosting")
    args = parser.parse_args()

    historical_rows = read_csv(Path(args.input))
    if not historical_rows:
        raise SystemExit(f"No historical feature rows found at {args.input}.")

    model = train_model(historical_rows, args.model)
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    intervals = iter_half_hours(start_date, end_date)
    years = [datetime.fromisoformat(row["interval_start_datetime"]).year for row in historical_rows]
    holidays = us_federal_holidays(min(years + [start_date.year]), max(years + [end_date.year]))

    volume_lookup = {
        datetime.fromisoformat(row["interval_start_datetime"]): float(row["actual_call_volume"])
        for row in historical_rows
    }

    feature_rows: list[dict[str, str]] = []
    forecast_rows: list[dict[str, str]] = []
    predictions: list[float] = []
    for interval in intervals:
        feature_row = build_future_feature_row(interval, volume_lookup, holidays)
        prediction = max(0.0, float(model.predict([feature_vector(feature_row)])[0]))
        volume_lookup[interval] = prediction
        feature_rows.append(feature_row)
        predictions.append(prediction)
        forecast_rows.append(
            {
                "interval_start_datetime": interval.isoformat(timespec="seconds"),
                "actual_call_volume": "",
                "predicted_call_volume": f"{prediction:.4f}",
                "absolute_error": "",
                "squared_error": "",
                "absolute_percentage_error": "",
            }
        )

    write_csv(Path(args.feature_output), feature_rows, FEATURE_MATRIX_FIELDS)
    write_csv(Path(args.forecast_output), forecast_rows, FORECAST_FIELDS)
    summary = {
        "model_family": "scikit-learn feature model",
        "selected_model": args.model,
        "training_rows": len(historical_rows),
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "train_start": historical_rows[0]["calendar_date"],
        "train_end": historical_rows[-1]["calendar_date"],
        "forecast_start": start_date.isoformat(),
        "forecast_end": end_date.isoformat(),
        "forecast_intervals": len(forecast_rows),
        "avg_predicted_calls": round(rolling_mean(predictions), 4),
        "peak_predicted_calls": round(max(predictions), 4) if predictions else 0,
        "forecast_output": args.forecast_output,
        "feature_output": args.feature_output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
