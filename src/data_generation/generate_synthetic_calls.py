"""Generate synthetic call center operations metadata from 311 demand records."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


AGENT_SKILLS = [
    ("housing", 12),
    ("sanitation", 10),
    ("transportation", 10),
    ("public_safety", 8),
    ("general", 20),
]

KEYWORD_SKILLS = [
    ("housing", ("heat", "hot water", "noise", "building", "plumbing", "tenant")),
    ("sanitation", ("sanitation", "trash", "dirty", "missed collection", "recycling")),
    ("transportation", ("street", "parking", "traffic", "vehicle", "highway", "sidewalk")),
    ("public_safety", ("police", "fire", "hazard", "illegal", "blocked")),
]

OUTPUT_FIELDS = [
    "call_id",
    "source_request_id",
    "source_created_datetime",
    "call_start_datetime",
    "answer_datetime",
    "end_datetime",
    "date_id",
    "time_id",
    "half_hour_index",
    "queue_id",
    "queue_name",
    "service_category",
    "agent_id",
    "talk_time_sec",
    "hold_time_sec",
    "acw_time_sec",
    "handle_time_sec",
    "abandoned_flag",
    "sla_met_flag",
    "borough",
    "incident_zip",
    "status",
]


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def classify_skill(complaint_type: str, descriptor: str) -> str:
    text = f"{complaint_type} {descriptor}".lower()
    for skill, keywords in KEYWORD_SKILLS:
        if any(keyword in text for keyword in keywords):
            return skill
    return "general"


def build_agents() -> list[dict[str, str]]:
    agents: list[dict[str, str]] = []
    agent_id = 1
    for skill, count in AGENT_SKILLS:
        for index in range(1, count + 1):
            agents.append(
                {
                    "agent_id": str(agent_id),
                    "agent_name": f"Agent {agent_id:03d}",
                    "skill_group": skill,
                    "employment_type": "Full-Time" if index % 5 else "Part-Time",
                    "active_flag": "1",
                }
            )
            agent_id += 1
    return agents


def interval_keys(value: datetime) -> tuple[str, str, int]:
    date_id = value.strftime("%Y%m%d")
    half_hour_index = value.hour * 2 + (1 if value.minute >= 30 else 0)
    interval_minute = 30 if value.minute >= 30 else 0
    time_id = f"{value.hour:02d}{interval_minute:02d}"
    return date_id, time_id, half_hour_index


def simulated_call_start(source_created_at: datetime, rng: random.Random) -> datetime:
    """Keep the real source date, then simulate an operational call time.

    The public service request timestamp remains available as source context.
    For the call-center simulation, this avoids an artifact where API samples
    ordered by creation time overrepresent the first intervals of each day.
    """
    weekday = source_created_at.weekday()
    if weekday < 5:
        hour_weights = {
            0: 0.01,
            1: 0.01,
            2: 0.01,
            3: 0.01,
            4: 0.01,
            5: 0.02,
            6: 0.03,
            7: 0.05,
            8: 0.07,
            9: 0.09,
            10: 0.09,
            11: 0.08,
            12: 0.07,
            13: 0.08,
            14: 0.08,
            15: 0.08,
            16: 0.07,
            17: 0.06,
            18: 0.04,
            19: 0.03,
            20: 0.02,
            21: 0.02,
            22: 0.02,
            23: 0.02,
        }
    else:
        hour_weights = {
            0: 0.01,
            1: 0.01,
            2: 0.01,
            3: 0.01,
            4: 0.01,
            5: 0.01,
            6: 0.02,
            7: 0.03,
            8: 0.04,
            9: 0.06,
            10: 0.08,
            11: 0.09,
            12: 0.09,
            13: 0.09,
            14: 0.08,
            15: 0.07,
            16: 0.06,
            17: 0.05,
            18: 0.04,
            19: 0.04,
            20: 0.03,
            21: 0.03,
            22: 0.02,
            23: 0.02,
        }
    hours = list(hour_weights.keys())
    weights = list(hour_weights.values())
    hour = rng.choices(hours, weights=weights, k=1)[0]
    minute = rng.randrange(60)
    second = rng.randrange(60)
    return source_created_at.replace(hour=hour, minute=minute, second=second, microsecond=0)


def bounded_int(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def simulate_call(
    row: dict[str, str],
    call_id: int,
    queue_id: int,
    agents_by_skill: dict[str, list[str]],
    rng: random.Random,
) -> dict[str, str]:
    source_created_at = parse_datetime(row.get("created_date", ""))
    if source_created_at is None:
        source_created_at = datetime(2025, 1, 1) + timedelta(minutes=call_id)
    call_start_at = simulated_call_start(source_created_at, rng)

    complaint_type = row.get("complaint_type", "").strip() or "Unknown"
    descriptor = row.get("descriptor", "").strip()
    skill = classify_skill(complaint_type, descriptor)
    is_peak = call_start_at.weekday() < 5 and 9 <= call_start_at.hour <= 16

    hold_mu = math.log(55 if is_peak else 35)
    hold_time = bounded_int(rng.lognormvariate(hold_mu, 0.85), 0, 900)
    abandon_probability = min(0.65, 0.025 + hold_time / 1400)
    abandoned = rng.random() < abandon_probability

    base_talk = {
        "housing": 420,
        "sanitation": 260,
        "transportation": 330,
        "public_safety": 300,
        "general": 360,
    }[skill]
    talk_time = bounded_int(rng.lognormvariate(math.log(base_talk), 0.55), 45, 2400)
    acw_time = bounded_int(rng.gammavariate(2.0, 35.0), 10, 480)

    if abandoned:
        answer_at = ""
        end_at = call_start_at + timedelta(seconds=hold_time)
        talk_time = 0
        acw_time = 0
        handle_time = 0
        agent_id = ""
        sla_met = 0
    else:
        answer_datetime = call_start_at + timedelta(seconds=hold_time)
        end_at = answer_datetime + timedelta(seconds=talk_time)
        answer_at = answer_datetime.isoformat(timespec="seconds")
        handle_time = talk_time + acw_time
        agent_id = rng.choice(agents_by_skill.get(skill) or agents_by_skill["general"])
        sla_met = 1 if hold_time <= 20 else 0

    date_id, time_id, half_hour_index = interval_keys(call_start_at)
    return {
        "call_id": str(call_id),
        "source_request_id": row.get("unique_key", ""),
        "source_created_datetime": source_created_at.isoformat(timespec="seconds"),
        "call_start_datetime": call_start_at.isoformat(timespec="seconds"),
        "answer_datetime": answer_at,
        "end_datetime": end_at.isoformat(timespec="seconds"),
        "date_id": date_id,
        "time_id": time_id,
        "half_hour_index": str(half_hour_index),
        "queue_id": str(queue_id),
        "queue_name": complaint_type,
        "service_category": skill,
        "agent_id": agent_id,
        "talk_time_sec": str(talk_time),
        "hold_time_sec": str(hold_time),
        "acw_time_sec": str(acw_time),
        "handle_time_sec": str(handle_time),
        "abandoned_flag": "1" if abandoned else "0",
        "sla_met_flag": str(sla_met),
        "borough": row.get("borough", ""),
        "incident_zip": row.get("incident_zip", ""),
        "status": row.get("status", ""),
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/nyc_311_sample.csv")
    parser.add_argument("--output", default="data/processed/synthetic_calls_sample.csv")
    parser.add_argument("--agents-output", default="data/processed/dim_agents_sample.csv")
    parser.add_argument("--queues-output", default="data/processed/dim_queues_sample.csv")
    parser.add_argument("--summary-output", default="docs/sample_generation_summary.json")
    parser.add_argument("--seed", type=int, default=20260511)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    input_path = Path(args.input)
    with input_path.open("r", newline="", encoding="utf-8-sig") as input_file:
        source_rows = list(csv.DictReader(input_file))

    agents = build_agents()
    agents_by_skill: dict[str, list[str]] = {}
    for agent in agents:
        agents_by_skill.setdefault(agent["skill_group"], []).append(agent["agent_id"])

    complaint_types = sorted({row.get("complaint_type", "").strip() or "Unknown" for row in source_rows})
    queue_map = {queue_name: index + 1 for index, queue_name in enumerate(complaint_types)}
    queue_rows = [
        {
            "queue_id": str(queue_id),
            "queue_name": queue_name,
            "service_category": classify_skill(queue_name, ""),
            "sla_target_sec": "20",
            "target_service_level": "0.80",
        }
        for queue_name, queue_id in queue_map.items()
    ]

    synthetic_rows = [
        simulate_call(
            row=row,
            call_id=index,
            queue_id=queue_map[row.get("complaint_type", "").strip() or "Unknown"],
            agents_by_skill=agents_by_skill,
            rng=rng,
        )
        for index, row in enumerate(source_rows, start=1)
    ]

    write_csv(Path(args.output), synthetic_rows, OUTPUT_FIELDS)
    write_csv(
        Path(args.agents_output),
        agents,
        ["agent_id", "agent_name", "skill_group", "employment_type", "active_flag"],
    )
    write_csv(
        Path(args.queues_output),
        queue_rows,
        ["queue_id", "queue_name", "service_category", "sla_target_sec", "target_service_level"],
    )

    total = len(synthetic_rows)
    abandoned = sum(row["abandoned_flag"] == "1" for row in synthetic_rows)
    answered_rows = [row for row in synthetic_rows if row["abandoned_flag"] == "0"]
    avg_handle_time = (
        sum(int(row["handle_time_sec"]) for row in answered_rows) / len(answered_rows)
        if answered_rows
        else 0
    )
    interval_counts = Counter((row["date_id"], row["time_id"]) for row in synthetic_rows)
    summary = {
        "seed": args.seed,
        "source_rows": total,
        "synthetic_calls_path": args.output,
        "agents_path": args.agents_output,
        "queues_path": args.queues_output,
        "agent_count": len(agents),
        "queue_count": len(queue_rows),
        "abandonment_rate": round(abandoned / total, 4) if total else 0,
        "average_handle_time_sec_answered": round(avg_handle_time, 2),
        "interval_count": len(interval_counts),
        "max_calls_in_interval": max(interval_counts.values()) if interval_counts else 0,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
