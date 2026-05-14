"""Calculate interval staffing requirements with the Erlang C formula."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path


STAFFING_FIELDS = [
    "interval_start_datetime",
    "actual_call_volume",
    "predicted_call_volume",
    "avg_handle_time_sec",
    "traffic_intensity_erlangs",
    "base_required_agents",
    "shrinkage_adjusted_agents",
    "expected_occupancy",
    "service_level_probability",
    "target_service_level",
    "sla_target_sec",
    "max_occupancy",
    "shrinkage_rate",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def half_hour_index(value: datetime) -> int:
    return value.hour * 2 + (1 if value.minute >= 30 else 0)


def erlang_c_probability_wait(traffic_intensity: float, agents: int) -> float:
    if traffic_intensity <= 0:
        return 0.0
    if agents <= traffic_intensity:
        return 1.0

    term = 1.0
    denominator_sum = 1.0
    for n in range(1, agents):
        term *= traffic_intensity / n
        denominator_sum += term

    agents_term = term * traffic_intensity / agents
    queue_term = agents_term * agents / (agents - traffic_intensity)
    return queue_term / (denominator_sum + queue_term)


def service_level_probability(
    traffic_intensity: float,
    agents: int,
    target_answer_time_sec: int,
    avg_handle_time_sec: float,
) -> float:
    if traffic_intensity <= 0:
        return 1.0
    if agents <= traffic_intensity or avg_handle_time_sec <= 0:
        return 0.0

    probability_wait = erlang_c_probability_wait(traffic_intensity, agents)
    delay_decay = math.exp(
        -(agents - traffic_intensity) * target_answer_time_sec / avg_handle_time_sec
    )
    return max(0.0, min(1.0, 1 - probability_wait * delay_decay))


def required_agents(
    traffic_intensity: float,
    avg_handle_time_sec: float,
    target_answer_time_sec: int,
    target_service_level: float,
    max_occupancy: float,
) -> tuple[int, float, float]:
    if traffic_intensity <= 0:
        return 0, 0.0, 1.0

    agents = max(1, math.floor(traffic_intensity) + 1)
    while True:
        occupancy = traffic_intensity / agents
        service_level = service_level_probability(
            traffic_intensity,
            agents,
            target_answer_time_sec,
            avg_handle_time_sec,
        )
        if occupancy <= max_occupancy and service_level >= target_service_level:
            return agents, occupancy, service_level
        agents += 1


def weighted_average(values: list[tuple[float, float]]) -> float:
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in values) / total_weight


def build_aht_lookups(rows: list[dict[str, str]]) -> tuple[dict[str, float], dict[int, float], float]:
    exact_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    interval_values: dict[int, list[tuple[float, float]]] = defaultdict(list)
    all_values: list[tuple[float, float]] = []

    for row in rows:
        interval = datetime.fromisoformat(row["interval_start_datetime"])
        avg_handle_time = float(row.get("avg_handle_time_sec") or 0)
        answered = float(row.get("answered_calls") or 0)
        volume = float(row.get("call_volume") or 0)
        weight = answered if answered > 0 else volume
        if avg_handle_time <= 0 or weight <= 0:
            continue
        key = interval.isoformat(timespec="seconds")
        value = (avg_handle_time, weight)
        exact_values[key].append(value)
        interval_values[half_hour_index(interval)].append(value)
        all_values.append(value)

    exact = {key: weighted_average(values) for key, values in exact_values.items()}
    by_half_hour = {key: weighted_average(values) for key, values in interval_values.items()}
    return exact, by_half_hour, weighted_average(all_values)


def resolve_aht(
    interval: datetime,
    exact_lookup: dict[str, float],
    half_hour_lookup: dict[int, float],
    global_aht: float,
) -> float:
    key = interval.isoformat(timespec="seconds")
    return exact_lookup.get(key, half_hour_lookup.get(half_hour_index(interval), global_aht))


def build_staffing_rows(
    forecast_rows: list[dict[str, str]],
    forecasting_input_rows: list[dict[str, str]],
    interval_minutes: int,
    target_answer_time_sec: int,
    target_service_level: float,
    max_occupancy: float,
    shrinkage_rate: float,
) -> list[dict[str, str]]:
    exact_aht, half_hour_aht, global_aht = build_aht_lookups(forecasting_input_rows)
    interval_seconds = interval_minutes * 60
    output_rows: list[dict[str, str]] = []

    for row in forecast_rows:
        interval = datetime.fromisoformat(row["interval_start_datetime"])
        predicted_volume = float(row["predicted_call_volume"])
        avg_handle_time = resolve_aht(interval, exact_aht, half_hour_aht, global_aht)
        traffic_intensity = predicted_volume * avg_handle_time / interval_seconds
        base_agents, occupancy, service_level = required_agents(
            traffic_intensity=traffic_intensity,
            avg_handle_time_sec=avg_handle_time,
            target_answer_time_sec=target_answer_time_sec,
            target_service_level=target_service_level,
            max_occupancy=max_occupancy,
        )
        shrinkage_adjusted = (
            math.ceil(base_agents / (1 - shrinkage_rate))
            if base_agents and shrinkage_rate < 1
            else base_agents
        )

        output_rows.append(
            {
                "interval_start_datetime": interval.isoformat(timespec="seconds"),
                "actual_call_volume": row.get("actual_call_volume", ""),
                "predicted_call_volume": f"{predicted_volume:.4f}",
                "avg_handle_time_sec": f"{avg_handle_time:.2f}",
                "traffic_intensity_erlangs": f"{traffic_intensity:.4f}",
                "base_required_agents": str(base_agents),
                "shrinkage_adjusted_agents": str(shrinkage_adjusted),
                "expected_occupancy": f"{occupancy:.4f}",
                "service_level_probability": f"{service_level:.4f}",
                "target_service_level": f"{target_service_level:.4f}",
                "sla_target_sec": str(target_answer_time_sec),
                "max_occupancy": f"{max_occupancy:.4f}",
                "shrinkage_rate": f"{shrinkage_rate:.4f}",
            }
        )

    return output_rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_summary(
    rows: list[dict[str, str]],
    forecast_input: str,
    output: str,
    interval_minutes: int,
    target_answer_time_sec: int,
    target_service_level: float,
    max_occupancy: float,
    shrinkage_rate: float,
) -> dict[str, float | int | str]:
    if not rows:
        return {
            "method": "Erlang C",
            "forecast_input": forecast_input,
            "output": output,
            "interval_count": 0,
        }

    predicted = [float(row["predicted_call_volume"]) for row in rows]
    base_agents = [int(row["base_required_agents"]) for row in rows]
    adjusted_agents = [int(row["shrinkage_adjusted_agents"]) for row in rows]
    occupancy = [float(row["expected_occupancy"]) for row in rows if float(row["expected_occupancy"]) > 0]
    service_level = [
        float(row["service_level_probability"])
        for row in rows
        if float(row["predicted_call_volume"]) > 0
    ]

    return {
        "method": "Erlang C",
        "forecast_input": forecast_input,
        "output": output,
        "interval_count": len(rows),
        "start": rows[0]["interval_start_datetime"],
        "end": rows[-1]["interval_start_datetime"],
        "interval_minutes": interval_minutes,
        "sla_target_sec": target_answer_time_sec,
        "target_service_level": target_service_level,
        "max_occupancy": max_occupancy,
        "shrinkage_rate": shrinkage_rate,
        "avg_predicted_calls": round(mean(predicted), 4),
        "peak_predicted_calls": round(max(predicted), 4),
        "avg_base_required_agents": round(mean([float(value) for value in base_agents]), 4),
        "peak_base_required_agents": max(base_agents),
        "avg_shrinkage_adjusted_agents": round(mean([float(value) for value in adjusted_agents]), 4),
        "peak_shrinkage_adjusted_agents": max(adjusted_agents),
        "avg_expected_occupancy": round(mean(occupancy), 4),
        "avg_service_level_probability": round(mean(service_level), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forecast", default="data/processed/baseline_forecast_sample.csv")
    parser.add_argument("--forecasting-input", default="data/processed/forecasting_input_sample.csv")
    parser.add_argument("--output", default="data/processed/staffing_requirements_sample.csv")
    parser.add_argument("--summary-output", default="docs/staffing_requirements_summary.json")
    parser.add_argument("--interval-minutes", type=int, default=30)
    parser.add_argument("--sla-target-sec", type=int, default=20)
    parser.add_argument("--target-service-level", type=float, default=0.80)
    parser.add_argument("--max-occupancy", type=float, default=0.85)
    parser.add_argument("--shrinkage-rate", type=float, default=0.30)
    args = parser.parse_args()

    rows = build_staffing_rows(
        forecast_rows=read_csv(Path(args.forecast)),
        forecasting_input_rows=read_csv(Path(args.forecasting_input)),
        interval_minutes=args.interval_minutes,
        target_answer_time_sec=args.sla_target_sec,
        target_service_level=args.target_service_level,
        max_occupancy=args.max_occupancy,
        shrinkage_rate=args.shrinkage_rate,
    )
    write_csv(Path(args.output), rows, STAFFING_FIELDS)

    summary = build_summary(
        rows=rows,
        forecast_input=args.forecast,
        output=args.output,
        interval_minutes=args.interval_minutes,
        target_answer_time_sec=args.sla_target_sec,
        target_service_level=args.target_service_level,
        max_occupancy=args.max_occupancy,
        shrinkage_rate=args.shrinkage_rate,
    )
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
