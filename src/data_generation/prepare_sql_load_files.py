"""Prepare SQL Server load files from the generated synthetic call sample."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path


MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
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


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def build_dim_date(call_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    dates = sorted({parse_dt(row["call_start_datetime"]).date() for row in call_rows})
    rows: list[dict[str, str]] = []
    for value in dates:
        rows.append(
            {
                "Date_ID": value.strftime("%Y%m%d"),
                "Calendar_Date": value.isoformat(),
                "Day_Of_Week": value.strftime("%A"),
                "Week_Of_Year": str(value.isocalendar().week),
                "Month_Number": str(value.month),
                "Month_Name": MONTH_NAMES[value.month],
                "Quarter_Number": str((value.month - 1) // 3 + 1),
                "Year_Number": str(value.year),
                "Is_Weekend": "1" if value.weekday() >= 5 else "0",
                "Is_Holiday": "0",
            }
        )
    return rows


def build_dim_time() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    base = datetime.combine(date(2000, 1, 1), time(0, 0))
    for index in range(48):
        start = base + timedelta(minutes=30 * index)
        end = start + timedelta(minutes=30)
        hour = start.hour
        if 6 <= hour < 12:
            shift_band = "Morning"
        elif 12 <= hour < 18:
            shift_band = "Afternoon"
        elif 18 <= hour < 22:
            shift_band = "Evening"
        else:
            shift_band = "Overnight"
        rows.append(
            {
                "Time_ID": start.strftime("%H%M"),
                "Interval_Start_Time": start.strftime("%H:%M:%S"),
                "Interval_End_Time": end.strftime("%H:%M:%S"),
                "Hour_Number": str(hour),
                "Half_Hour_Index": str(index),
                "Shift_Band": shift_band,
            }
        )
    return rows


def build_dim_agents(agent_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "Agent_ID": row["agent_id"],
            "Agent_Name": row["agent_name"],
            "Skill_Group": row["skill_group"],
            "Employment_Type": row["employment_type"],
            "Active_Flag": row["active_flag"],
        }
        for row in agent_rows
    ]


def queue_service_category_map(call_rows: list[dict[str, str]]) -> dict[str, str]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in call_rows:
        counts[row["queue_id"]][row["service_category"] or "general"] += 1
    return {
        queue_id: category_counts.most_common(1)[0][0]
        for queue_id, category_counts in counts.items()
    }


def build_dim_queues(
    queue_rows: list[dict[str, str]],
    service_category_by_queue: dict[str, str],
) -> list[dict[str, str]]:
    return [
        {
            "Queue_ID": row["queue_id"],
            "Queue_Name": row["queue_name"],
            "Service_Category": service_category_by_queue.get(
                row["queue_id"],
                row["service_category"] or "general",
            ),
            "SLA_Target_Sec": row["sla_target_sec"],
            "Target_Service_Level": row["target_service_level"],
            "Active_Flag": "1",
        }
        for row in queue_rows
    ]


def build_fact_calls(call_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row in call_rows:
        output_rows.append(
            {
                "Call_ID": row["call_id"],
                "Source_Request_ID": row["source_request_id"],
                "Date_ID": row["date_id"],
                "Time_ID": row["time_id"],
                "Queue_ID": row["queue_id"],
                "Agent_ID": row["agent_id"],
                "Source_Created_Datetime": row["source_created_datetime"],
                "Call_Start_Datetime": row["call_start_datetime"],
                "Answer_Datetime": row["answer_datetime"],
                "End_Datetime": row["end_datetime"],
                "Talk_Time_Sec": row["talk_time_sec"],
                "Hold_Time_Sec": row["hold_time_sec"],
                "ACW_Time_Sec": row["acw_time_sec"],
                "Handle_Time_Sec": row["handle_time_sec"],
                "Abandoned_Flag": row["abandoned_flag"],
                "SLA_Met_Flag": row["sla_met_flag"],
                "Borough": row["borough"],
                "Incident_Zip": row["incident_zip"],
                "Source_Status": row["status"],
            }
        )
    return output_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calls", default="data/processed/synthetic_calls_sample.csv")
    parser.add_argument("--agents", default="data/processed/dim_agents_sample.csv")
    parser.add_argument("--queues", default="data/processed/dim_queues_sample.csv")
    parser.add_argument("--output-dir", default="data/processed/sql_load")
    args = parser.parse_args()

    call_rows = read_csv(Path(args.calls))
    agent_rows = read_csv(Path(args.agents))
    queue_rows = read_csv(Path(args.queues))
    output_dir = Path(args.output_dir)
    service_category_by_queue = queue_service_category_map(call_rows)

    outputs = {
        "dim_date_sample.csv": (
            build_dim_date(call_rows),
            [
                "Date_ID",
                "Calendar_Date",
                "Day_Of_Week",
                "Week_Of_Year",
                "Month_Number",
                "Month_Name",
                "Quarter_Number",
                "Year_Number",
                "Is_Weekend",
                "Is_Holiday",
            ],
        ),
        "dim_time_sample.csv": (
            build_dim_time(),
            [
                "Time_ID",
                "Interval_Start_Time",
                "Interval_End_Time",
                "Hour_Number",
                "Half_Hour_Index",
                "Shift_Band",
            ],
        ),
        "dim_agent_sample_sql.csv": (
            build_dim_agents(agent_rows),
            ["Agent_ID", "Agent_Name", "Skill_Group", "Employment_Type", "Active_Flag"],
        ),
        "dim_queue_sample_sql.csv": (
            build_dim_queues(queue_rows, service_category_by_queue),
            [
                "Queue_ID",
                "Queue_Name",
                "Service_Category",
                "SLA_Target_Sec",
                "Target_Service_Level",
                "Active_Flag",
            ],
        ),
        "fact_calls_sample_sql.csv": (
            build_fact_calls(call_rows),
            [
                "Call_ID",
                "Source_Request_ID",
                "Date_ID",
                "Time_ID",
                "Queue_ID",
                "Agent_ID",
                "Source_Created_Datetime",
                "Call_Start_Datetime",
                "Answer_Datetime",
                "End_Datetime",
                "Talk_Time_Sec",
                "Hold_Time_Sec",
                "ACW_Time_Sec",
                "Handle_Time_Sec",
                "Abandoned_Flag",
                "SLA_Met_Flag",
                "Borough",
                "Incident_Zip",
                "Source_Status",
            ],
        ),
    }

    for filename, (rows, fields) in outputs.items():
        write_csv(output_dir / filename, rows, fields)
        print(f"{filename}: {len(rows)} rows")


if __name__ == "__main__":
    main()
