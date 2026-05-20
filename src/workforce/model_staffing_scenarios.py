"""Compare Erlang C staffing impact across forecast model scenarios."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from .erlang_c_staffing import (
        STAFFING_FIELDS,
        build_staffing_rows,
        build_summary,
        read_csv,
        write_csv,
    )
except ImportError:
    from erlang_c_staffing import (
        STAFFING_FIELDS,
        build_staffing_rows,
        build_summary,
        read_csv,
        write_csv,
    )


SCENARIO_STAFFING_FIELDS = [
    "model",
    *STAFFING_FIELDS,
]


def group_forecasts_by_model(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["model"]].append(
            {
                "interval_start_datetime": row["interval_start_datetime"],
                "actual_call_volume": row.get("actual_call_volume", ""),
                "predicted_call_volume": row["predicted_call_volume"],
            }
        )
    return {
        model: sorted(model_rows, key=lambda value: value["interval_start_datetime"])
        for model, model_rows in grouped.items()
    }


def estimate_full_coverage_agents(
    staffing_rows: list[dict[str, str]],
    interval_minutes: int,
    shift_hours: int,
    break_minutes: int,
    max_shifts_per_agent_per_week: int,
) -> dict[str, float | int]:
    if not staffing_rows:
        return {
            "required_agent_hours": 0.0,
            "productive_hours_per_agent_in_horizon": 0.0,
            "estimated_full_coverage_agents": 0,
        }

    first_interval = datetime.fromisoformat(staffing_rows[0]["interval_start_datetime"])
    last_interval = datetime.fromisoformat(staffing_rows[-1]["interval_start_datetime"])
    horizon_days = max((last_interval.date() - first_interval.date()).days + 1, 1)
    required_total = sum(int(row["shrinkage_adjusted_agents"]) for row in staffing_rows)
    required_agent_hours = required_total * interval_minutes / 60
    productive_shift_hours = max(shift_hours - break_minutes / 60, 0.5)
    productive_hours_per_agent = (
        productive_shift_hours * max_shifts_per_agent_per_week * horizon_days / 7
    )
    estimated_agents = (
        math.ceil(required_agent_hours / productive_hours_per_agent)
        if productive_hours_per_agent
        else 0
    )
    return {
        "required_agent_hours": round(required_agent_hours, 2),
        "productive_hours_per_agent_in_horizon": round(productive_hours_per_agent, 2),
        "estimated_full_coverage_agents": estimated_agents,
    }


def build_model_scenarios(
    scenario_forecasts: list[dict[str, str]],
    forecasting_input_rows: list[dict[str, str]],
    interval_minutes: int,
    target_answer_time_sec: int,
    target_service_level: float,
    max_occupancy: float,
    shrinkage_rate: float,
    agent_count: int,
    shift_hours: int,
    break_minutes: int,
    max_shifts_per_agent_per_week: int,
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    all_rows: list[dict[str, str]] = []
    summaries: list[dict[str, object]] = []
    for model, forecast_rows in group_forecasts_by_model(scenario_forecasts).items():
        staffing_rows = build_staffing_rows(
            forecast_rows=forecast_rows,
            forecasting_input_rows=forecasting_input_rows,
            interval_minutes=interval_minutes,
            target_answer_time_sec=target_answer_time_sec,
            target_service_level=target_service_level,
            max_occupancy=max_occupancy,
            shrinkage_rate=shrinkage_rate,
        )
        all_rows.extend({"model": model, **row} for row in staffing_rows)
        summary = build_summary(
            rows=staffing_rows,
            forecast_input="model_scenario_forecast",
            output="model_scenario_staffing",
            interval_minutes=interval_minutes,
            target_answer_time_sec=target_answer_time_sec,
            target_service_level=target_service_level,
            max_occupancy=max_occupancy,
            shrinkage_rate=shrinkage_rate,
        )
        roster_estimate = estimate_full_coverage_agents(
            staffing_rows=staffing_rows,
            interval_minutes=interval_minutes,
            shift_hours=shift_hours,
            break_minutes=break_minutes,
            max_shifts_per_agent_per_week=max_shifts_per_agent_per_week,
        )
        peak_gap = max(int(summary.get("peak_shrinkage_adjusted_agents", 0)) - agent_count, 0)
        summaries.append(
            {
                "model": model,
                **summary,
                **roster_estimate,
                "approved_agent_pool": agent_count,
                "approved_agent_pool_gap": max(
                    int(roster_estimate["estimated_full_coverage_agents"]) - agent_count,
                    0,
                ),
                "peak_agent_gap": peak_gap,
            }
        )
    summaries.sort(key=lambda row: int(row["estimated_full_coverage_agents"]), reverse=True)
    return all_rows, summaries


def write_scenario_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=SCENARIO_STAFFING_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-forecasts", default="data/processed/future_model_scenario_forecasts.csv")
    parser.add_argument("--forecasting-input", default="data/processed/full_operational_forecasting_input.csv")
    parser.add_argument("--output", default="data/processed/future_model_staffing_scenarios.csv")
    parser.add_argument("--summary-output", default="docs/future_model_staffing_scenario_summary.json")
    parser.add_argument("--interval-minutes", type=int, default=30)
    parser.add_argument("--sla-target-sec", type=int, default=20)
    parser.add_argument("--target-service-level", type=float, default=0.80)
    parser.add_argument("--max-occupancy", type=float, default=0.85)
    parser.add_argument("--shrinkage-rate", type=float, default=0.30)
    parser.add_argument("--agent-count", type=int, default=160)
    parser.add_argument("--shift-hours", type=int, default=8)
    parser.add_argument("--break-minutes", type=int, default=30)
    parser.add_argument("--max-shifts-per-agent-per-week", type=int, default=5)
    args = parser.parse_args()

    rows, summaries = build_model_scenarios(
        scenario_forecasts=read_csv(Path(args.scenario_forecasts)),
        forecasting_input_rows=read_csv(Path(args.forecasting_input)),
        interval_minutes=args.interval_minutes,
        target_answer_time_sec=args.sla_target_sec,
        target_service_level=args.target_service_level,
        max_occupancy=args.max_occupancy,
        shrinkage_rate=args.shrinkage_rate,
        agent_count=args.agent_count,
        shift_hours=args.shift_hours,
        break_minutes=args.break_minutes,
        max_shifts_per_agent_per_week=args.max_shifts_per_agent_per_week,
    )
    write_scenario_csv(Path(args.output), rows)
    summary = {
        "method": "Erlang C staffing scenarios by forecast model",
        "scenario_forecasts": args.scenario_forecasts,
        "output": args.output,
        "agent_count": args.agent_count,
        "models": summaries,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
