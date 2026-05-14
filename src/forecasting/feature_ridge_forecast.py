"""Feature-based interval forecast using standard-library ridge regression."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path


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


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 1.0
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return math.sqrt(variance) or 1.0


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


def feature_vector(row: dict[str, str], means: dict[str, float], scales: dict[str, float]) -> list[float]:
    return [
        (float(row[column]) - means[column]) / scales[column]
        for column in FEATURE_COLUMNS
    ]


def fit_scaler(rows: list[dict[str, str]]) -> tuple[dict[str, float], dict[str, float]]:
    means: dict[str, float] = {}
    scales: dict[str, float] = {}
    for column in FEATURE_COLUMNS:
        values = [float(row[column]) for row in rows]
        means[column] = mean(values)
        scales[column] = stddev(values)
    return means, scales


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]

    for pivot_index in range(size):
        pivot_row = max(
            range(pivot_index, size),
            key=lambda row_index: abs(augmented[row_index][pivot_index]),
        )
        augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]
        pivot = augmented[pivot_index][pivot_index]
        if abs(pivot) < 1e-12:
            continue

        for column_index in range(pivot_index, size + 1):
            augmented[pivot_index][column_index] /= pivot

        for row_index in range(size):
            if row_index == pivot_index:
                continue
            factor = augmented[row_index][pivot_index]
            if factor == 0:
                continue
            for column_index in range(pivot_index, size + 1):
                augmented[row_index][column_index] -= factor * augmented[pivot_index][column_index]

    return [augmented[row_index][size] for row_index in range(size)]


def fit_ridge_regression(features: list[list[float]], target: list[float], alpha: float) -> list[float]:
    column_count = len(features[0]) + 1
    xtx = [[0.0 for _ in range(column_count)] for _ in range(column_count)]
    xty = [0.0 for _ in range(column_count)]

    for row, value in zip(features, target):
        design_row = [1.0, *row]
        for i in range(column_count):
            xty[i] += design_row[i] * value
            for j in range(column_count):
                xtx[i][j] += design_row[i] * design_row[j]

    for index in range(1, column_count):
        xtx[index][index] += alpha

    return solve_linear_system(xtx, xty)


def predict(coefficients: list[float], row: list[float]) -> float:
    raw_prediction = coefficients[0] + sum(
        coefficient * value
        for coefficient, value in zip(coefficients[1:], row)
    )
    return max(0.0, raw_prediction)


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


def build_forecast_rows(
    test_rows: list[dict[str, str]],
    coefficients: list[float],
    means: dict[str, float],
    scales: dict[str, float],
) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row in test_rows:
        actual = float(row["actual_call_volume"])
        prediction = predict(coefficients, feature_vector(row, means, scales))
        absolute_error = abs(actual - prediction)
        squared_error = absolute_error**2
        ape = absolute_error / actual if actual else 0.0
        output_rows.append(
            {
                "interval_start_datetime": row["interval_start_datetime"],
                "actual_call_volume": f"{actual:.0f}",
                "predicted_call_volume": f"{prediction:.4f}",
                "absolute_error": f"{absolute_error:.4f}",
                "squared_error": f"{squared_error:.4f}",
                "absolute_percentage_error": f"{ape:.4f}" if actual else "",
            }
        )
    return output_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/forecast_features_sample.csv")
    parser.add_argument("--output", default="data/processed/feature_ridge_forecast_sample.csv")
    parser.add_argument("--summary-output", default="docs/feature_ridge_forecast_summary.json")
    parser.add_argument("--test-days", type=int, default=7)
    parser.add_argument("--alpha", type=float, default=25.0)
    args = parser.parse_args()

    rows = read_csv(Path(args.input))
    train_rows, test_rows = split_rows(rows, args.test_days)
    if not train_rows or not test_rows:
        raise SystemExit("Need both train and test rows for feature-based forecasting.")

    means, scales = fit_scaler(train_rows)
    train_features = [feature_vector(row, means, scales) for row in train_rows]
    target = [float(row["actual_call_volume"]) for row in train_rows]
    coefficients = fit_ridge_regression(train_features, target, args.alpha)
    forecast_rows = build_forecast_rows(test_rows, coefficients, means, scales)
    write_csv(Path(args.output), forecast_rows)

    summary = {
        "model": "standard-library ridge regression with calendar, previous-week lag, and federal holiday features",
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "alpha": args.alpha,
        "train_start": train_rows[0]["calendar_date"],
        "train_end": train_rows[-1]["calendar_date"],
        "test_start": test_rows[0]["calendar_date"],
        "test_end": test_rows[-1]["calendar_date"],
        **metrics(forecast_rows),
        "output": args.output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
