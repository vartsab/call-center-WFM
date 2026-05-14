"""Compare scikit-learn forecasting models on the holiday-aware feature matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


FEATURE_COLUMNS = [
    "half_hour_sin",
    "half_hour_cos",
    "day_of_week_sin",
    "day_of_week_cos",
    "day_of_month",
    "week_of_year",
    "month",
    "is_weekend",
    "is_federal_holiday",
    "days_to_nearest_federal_holiday",
    "lag_336_intervals",
]

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


def split_rows(rows: list[dict[str, str]], test_days: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if not rows:
        return [], []
    intervals = [datetime.fromisoformat(row["interval_start_datetime"]) for row in rows]
    test_start = max(interval.date() for interval in intervals) - timedelta(days=test_days - 1)
    train: list[dict[str, str]] = []
    test: list[dict[str, str]] = []
    for row, interval in zip(rows, intervals):
        if interval.date() < test_start:
            train.append(row)
        else:
            test.append(row)
    return train, test


def feature_vector(row: dict[str, str]) -> list[float]:
    return [float(row[column]) for column in FEATURE_COLUMNS]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_forecast_rows(test_rows: list[dict[str, str]], predictions: list[float]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row, prediction in zip(test_rows, predictions):
        actual = float(row["actual_call_volume"])
        clipped_prediction = max(0.0, prediction)
        absolute_error = abs(actual - clipped_prediction)
        squared_error = absolute_error**2
        ape = absolute_error / actual if actual else 0.0
        output_rows.append(
            {
                "interval_start_datetime": row["interval_start_datetime"],
                "actual_call_volume": f"{actual:.0f}",
                "predicted_call_volume": f"{clipped_prediction:.4f}",
                "absolute_error": f"{absolute_error:.4f}",
                "squared_error": f"{squared_error:.4f}",
                "absolute_percentage_error": f"{ape:.4f}" if actual else "",
            }
        )
    return output_rows


def metrics(rows: list[dict[str, str]]) -> dict[str, float | int]:
    mae = mean([float(row["absolute_error"]) for row in rows])
    rmse = math.sqrt(mean([float(row["squared_error"]) for row in rows]))
    ape_values = [
        float(row["absolute_percentage_error"])
        for row in rows
        if row["absolute_percentage_error"]
    ]
    return {
        "test_intervals": len(rows),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mean(ape_values), 4) if ape_values else 0.0,
    }


def model_candidates() -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import PoissonRegressor, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return {
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=25.0)),
        "poisson": make_pipeline(StandardScaler(), PoissonRegressor(alpha=0.5, max_iter=1000)),
        "random_forest": RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            random_state=20260514,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            random_state=20260514,
            n_estimators=150,
            learning_rate=0.04,
            max_depth=2,
            min_samples_leaf=5,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            random_state=20260514,
            max_iter=150,
            learning_rate=0.04,
            max_leaf_nodes=15,
            l2_regularization=0.1,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/forecast_features_sample.csv")
    parser.add_argument("--output", default="data/processed/sklearn_best_forecast_sample.csv")
    parser.add_argument("--summary-output", default="docs/sklearn_model_comparison_summary.json")
    parser.add_argument("--test-days", type=int, default=7)
    args = parser.parse_args()

    rows = read_csv(Path(args.input))
    train_rows, test_rows = split_rows(rows, args.test_days)
    if not train_rows or not test_rows:
        raise SystemExit("Need both train and test rows for feature-based forecasting.")

    x_train = [feature_vector(row) for row in train_rows]
    y_train = [float(row["actual_call_volume"]) for row in train_rows]
    x_test = [feature_vector(row) for row in test_rows]

    results: list[dict[str, Any]] = []
    best_forecast_rows: list[dict[str, str]] = []
    best_metric = float("inf")
    best_model_name = ""

    for model_name, model in model_candidates().items():
        model.fit(x_train, y_train)
        predictions = list(model.predict(x_test))
        forecast_rows = build_forecast_rows(test_rows, predictions)
        model_metrics = metrics(forecast_rows)
        results.append(
            {
                "model": model_name,
                **model_metrics,
            }
        )
        if float(model_metrics["mae"]) < best_metric:
            best_metric = float(model_metrics["mae"])
            best_model_name = model_name
            best_forecast_rows = forecast_rows

    write_csv(Path(args.output), best_forecast_rows)
    summary = {
        "model_family": "scikit-learn feature model comparison",
        "selected_model": best_model_name,
        "selection_metric": "mae",
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "train_start": train_rows[0]["calendar_date"],
        "train_end": train_rows[-1]["calendar_date"],
        "test_start": test_rows[0]["calendar_date"],
        "test_end": test_rows[-1]["calendar_date"],
        "models": sorted(results, key=lambda row: float(row["mae"])),
        "output": args.output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
