"""Build compact seed files for the public portfolio deployment."""

from __future__ import annotations

import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "data" / "processed"
SEED_DIR = ROOT / "deploy" / "seed"

from src.scheduling.christie_names import christie_agent_name


CATEGORY_SERVICE_LEVEL = {
    "housing": 0.2435,
    "general": 0.2194,
    "transportation": 0.2239,
    "public_safety": 0.2349,
    "sanitation": 0.2257,
}

CATEGORY_ABANDONMENT_RATE = {
    "housing": 0.0782,
    "general": 0.0782,
    "transportation": 0.0782,
    "public_safety": 0.0782,
    "sanitation": 0.0782,
}


COPY_FILES = {
    "full_baseline_forecast.csv": "forecast_baseline.csv",
    "full_sklearn_best_forecast.csv": "forecast_best_holdout.csv",
    "full_model_holdout_predictions.csv": "forecast_model_holdout_predictions.csv",
    "future_sklearn_forecast.csv": "future_forecast.csv",
    "future_model_scenario_forecasts.csv": "future_model_scenario_forecasts.csv",
    "future_staffing_requirements.csv": "staffing_requirements.csv",
    "future_model_staffing_scenarios.csv": "model_staffing_scenarios.csv",
    "future_optimized_schedule.csv": "optimized_schedule.csv",
    "future_schedule_coverage.csv": "schedule_coverage.csv",
    "dim_agents_sample.csv": "dashboard_agent_dimension.csv",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_rows(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def time_id_from_half_hour(half_hour_index: int) -> str:
    hour = half_hour_index // 2
    minute = 30 if half_hour_index % 2 else 0
    return f"{hour:02d}{minute:02d}"


def time_label_from_half_hour(half_hour_index: int) -> str:
    hour = half_hour_index // 2
    minute = 30 if half_hour_index % 2 else 0
    return f"{hour:02d}:{minute:02d}:00"


def build_dashboard_volume() -> None:
    rows = read_rows(DATA_DIR / "full_operational_forecasting_input.csv")
    grouped: dict[tuple[str, int, str], dict[str, float]] = defaultdict(
        lambda: {"calls": 0.0, "weighted_aht": 0.0}
    )

    for row in rows:
        category = row["service_category"]
        half_hour_index = int(row["half_hour_index"])
        call_volume = float(row["call_volume"])
        key = (row["calendar_date"], half_hour_index, category)
        grouped[key]["calls"] += call_volume
        grouped[key]["weighted_aht"] += float(row["avg_handle_time_sec"] or 0) * call_volume

    output_rows: list[dict[str, object]] = []
    forecasting_rows: list[dict[str, object]] = []
    for (calendar_date, half_hour_index, category), values in sorted(grouped.items()):
        offered = int(round(values["calls"]))
        abandonment_rate = CATEGORY_ABANDONMENT_RATE.get(category, 0.0782)
        abandoned = int(round(offered * abandonment_rate))
        answered = max(offered - abandoned, 0)
        avg_aht = values["weighted_aht"] / values["calls"] if values["calls"] else 0.0
        service_level = CATEGORY_SERVICE_LEVEL.get(category, 0.2257)
        time_id = time_id_from_half_hour(half_hour_index)

        output_rows.append(
            {
                "calendar_date": calendar_date,
                "time_id": time_id,
                "interval_start_time": time_label_from_half_hour(half_hour_index),
                "half_hour_index": half_hour_index,
                "queue_id": "",
                "queue_name": "All Queues",
                "service_category": category,
                "offered_calls": offered,
                "answered_calls": answered,
                "abandoned_calls": abandoned,
                "avg_handle_time_sec": f"{avg_aht:.2f}",
                "avg_hold_time_sec": f"{20 + (1 - service_level) * 60:.2f}",
                "service_level_rate": f"{service_level:.4f}",
            }
        )
        forecasting_rows.append(
            {
                "interval_start_datetime": f"{calendar_date}T{time_label_from_half_hour(half_hour_index)}",
                "half_hour_index": half_hour_index,
                "day_of_week": "",
                "is_weekend": "",
                "is_holiday": "",
                "service_category": category,
                "call_volume": offered,
                "avg_handle_time_sec": f"{avg_aht:.2f}",
            }
        )

    write_rows(
        SEED_DIR / "dashboard_volume_30min.csv",
        output_rows,
        [
            "calendar_date",
            "time_id",
            "interval_start_time",
            "half_hour_index",
            "queue_id",
            "queue_name",
            "service_category",
            "offered_calls",
            "answered_calls",
            "abandoned_calls",
            "avg_handle_time_sec",
            "avg_hold_time_sec",
            "service_level_rate",
        ],
    )
    write_rows(
        SEED_DIR / "dashboard_forecasting_input.csv",
        forecasting_rows,
        [
            "interval_start_datetime",
            "half_hour_index",
            "day_of_week",
            "is_weekend",
            "is_holiday",
            "service_category",
            "call_volume",
            "avg_handle_time_sec",
        ],
    )


def build_agent_dimension() -> None:
    rows = read_rows(DATA_DIR / "dim_agents_sample.csv")
    output_rows: list[dict[str, object]] = []
    for row in rows:
        agent_id = int(row["agent_id"])
        output_rows.append(
            {
                "agent_id": agent_id,
                "agent_name": christie_agent_name(agent_id),
                "skill_group": row["skill_group"],
                "employment_type": row["employment_type"],
                "active_flag": row["active_flag"],
            }
        )
    write_rows(
        SEED_DIR / "dashboard_agent_dimension.csv",
        output_rows,
        ["agent_id", "agent_name", "skill_group", "employment_type", "active_flag"],
    )


def build_agent_performance() -> None:
    calls = read_rows(DATA_DIR / "synthetic_calls_sample.csv")
    agents = {
        row["agent_id"]: row
        for row in read_rows(DATA_DIR / "dim_agents_sample.csv")
    }
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {
            "handled_calls": 0.0,
            "handle_time": 0.0,
            "talk_time": 0.0,
            "acw_time": 0.0,
        }
    )

    for row in calls:
        if row["abandoned_flag"] != "0" or not row["agent_id"]:
            continue
        date = row["call_start_datetime"][:10]
        key = (row["agent_id"], date)
        grouped[key]["handled_calls"] += 1
        grouped[key]["handle_time"] += float(row["handle_time_sec"])
        grouped[key]["talk_time"] += float(row["talk_time_sec"])
        grouped[key]["acw_time"] += float(row["acw_time_sec"])

    output_rows: list[dict[str, object]] = []
    for (agent_id, calendar_date), values in sorted(grouped.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        handled = values["handled_calls"]
        agent = agents.get(agent_id, {})
        output_rows.append(
            {
                "agent_id": agent_id,
                "agent_name": christie_agent_name(int(agent_id)),
                "skill_group": agent.get("skill_group", ""),
                "calendar_date": calendar_date,
                "handled_calls": int(handled),
                "avg_handle_time_sec": f"{values['handle_time'] / handled:.2f}",
                "avg_talk_time_sec": f"{values['talk_time'] / handled:.2f}",
                "avg_acw_time_sec": f"{values['acw_time'] / handled:.2f}",
            }
        )

    write_rows(
        SEED_DIR / "dashboard_agent_performance.csv",
        output_rows,
        [
            "agent_id",
            "agent_name",
            "skill_group",
            "calendar_date",
            "handled_calls",
            "avg_handle_time_sec",
            "avg_talk_time_sec",
            "avg_acw_time_sec",
        ],
    )


def copy_artifacts() -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, target_name in COPY_FILES.items():
        shutil.copyfile(DATA_DIR / source_name, SEED_DIR / target_name)


def main() -> None:
    copy_artifacts()
    build_dashboard_volume()
    build_agent_dimension()
    build_agent_performance()
    print(f"Portfolio seed files written to {SEED_DIR}")


if __name__ == "__main__":
    main()
