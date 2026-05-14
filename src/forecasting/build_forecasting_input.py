"""Build a 30-minute forecasting input table from synthetic calls."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


FIELDS = [
    "interval_start_datetime",
    "calendar_date",
    "time_id",
    "half_hour_index",
    "day_of_week",
    "is_weekend",
    "service_category",
    "call_volume",
    "answered_calls",
    "abandoned_calls",
    "avg_handle_time_sec",
]


def interval_start(value: datetime) -> datetime:
    minute = 30 if value.minute >= 30 else 0
    return value.replace(minute=minute, second=0, microsecond=0)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/synthetic_calls_sample.csv")
    parser.add_argument("--output", default="data/processed/forecasting_input_sample.csv")
    args = parser.parse_args()

    groups: dict[tuple[str, str], dict[str, float | int | str]] = defaultdict(
        lambda: {
            "call_volume": 0,
            "answered_calls": 0,
            "abandoned_calls": 0,
            "handle_time_sum": 0.0,
        }
    )

    for row in read_csv(Path(args.input)):
        start = interval_start(datetime.fromisoformat(row["call_start_datetime"]))
        service_category = row["service_category"] or "general"
        key = (start.isoformat(timespec="seconds"), service_category)
        group = groups[key]
        group["call_volume"] = int(group["call_volume"]) + 1
        if row["abandoned_flag"] == "1":
            group["abandoned_calls"] = int(group["abandoned_calls"]) + 1
        else:
            group["answered_calls"] = int(group["answered_calls"]) + 1
            group["handle_time_sum"] = float(group["handle_time_sum"]) + float(row["handle_time_sec"])

    output_rows: list[dict[str, str]] = []
    for (start_text, service_category), group in sorted(groups.items()):
        start = datetime.fromisoformat(start_text)
        answered = int(group["answered_calls"])
        avg_handle_time = float(group["handle_time_sum"]) / answered if answered else 0.0
        output_rows.append(
            {
                "interval_start_datetime": start_text,
                "calendar_date": start.date().isoformat(),
                "time_id": start.strftime("%H%M"),
                "half_hour_index": str(start.hour * 2 + (1 if start.minute >= 30 else 0)),
                "day_of_week": start.strftime("%A"),
                "is_weekend": "1" if start.weekday() >= 5 else "0",
                "service_category": service_category,
                "call_volume": str(int(group["call_volume"])),
                "answered_calls": str(answered),
                "abandoned_calls": str(int(group["abandoned_calls"])),
                "avg_handle_time_sec": f"{avg_handle_time:.2f}",
            }
        )

    write_csv(Path(args.output), output_rows)
    print(f"Wrote {len(output_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()

