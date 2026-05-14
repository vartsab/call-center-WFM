"""Generate a first shift schedule from staffing requirements using OR-Tools."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


SCHEDULE_FIELDS = [
    "agent_id",
    "agent_name",
    "shift_date",
    "shift_start_datetime",
    "shift_end_datetime",
    "break_start_datetime",
    "break_end_datetime",
    "covered_intervals",
]

COVERAGE_FIELDS = [
    "interval_start_datetime",
    "required_agents",
    "scheduled_agents",
    "understaffed_agents",
    "overstaffed_agents",
]


@dataclass(frozen=True)
class ShiftOption:
    shift_id: int
    start_index: int
    end_index: int
    break_index: int
    covered_indexes: tuple[int, ...]
    window_indexes: tuple[int, ...]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_agents(path: Path, fallback_count: int) -> list[dict[str, str]]:
    if path.exists():
        rows = read_csv(path)
        return [
            {
                "agent_id": row.get("agent_id") or row.get("Agent_ID") or str(index),
                "agent_name": row.get("agent_name") or row.get("Agent_Name") or f"Agent {index:03d}",
            }
            for index, row in enumerate(rows, start=1)
        ]
    return [
        {"agent_id": str(index), "agent_name": f"Agent {index:03d}"}
        for index in range(1, fallback_count + 1)
    ]


def load_requirements(path: Path) -> tuple[list[datetime], list[int]]:
    rows = read_csv(path)
    intervals = [datetime.fromisoformat(row["interval_start_datetime"]) for row in rows]
    required = [int(row["shrinkage_adjusted_agents"]) for row in rows]
    return intervals, required


def build_shift_options(
    interval_count: int,
    shift_intervals: int,
    break_after_intervals: int,
    start_step_intervals: int,
) -> list[ShiftOption]:
    options: list[ShiftOption] = []
    shift_id = 0
    latest_start = interval_count - shift_intervals
    for start in range(0, latest_start + 1, start_step_intervals):
        end = start + shift_intervals
        break_index = start + break_after_intervals
        window = tuple(range(start, end))
        covered = tuple(index for index in window if index != break_index)
        options.append(
            ShiftOption(
                shift_id=shift_id,
                start_index=start,
                end_index=end,
                break_index=break_index,
                covered_indexes=covered,
                window_indexes=window,
            )
        )
        shift_id += 1
    return options


def solve_schedule(
    required_agents: list[int],
    agent_count: int,
    shift_options: list[ShiftOption],
    max_shifts_per_agent: int,
    time_limit_sec: int,
) -> tuple[cp_model.CpSolver, dict[tuple[int, int], cp_model.IntVar], list[cp_model.IntVar], list[cp_model.IntVar]]:
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    assignments: dict[tuple[int, int], cp_model.IntVar] = {}
    for agent_index in range(agent_count):
        for option in shift_options:
            assignments[(agent_index, option.shift_id)] = model.NewBoolVar(
                f"agent_{agent_index}_shift_{option.shift_id}"
            )

    for agent_index in range(agent_count):
        model.Add(
            sum(assignments[(agent_index, option.shift_id)] for option in shift_options)
            <= max_shifts_per_agent
        )

    for agent_index in range(agent_count):
        days = sorted({option.start_index // 48 for option in shift_options})
        for day in days:
            day_options = [
                option for option in shift_options if option.start_index // 48 == day
            ]
            model.Add(
                sum(assignments[(agent_index, option.shift_id)] for option in day_options)
                <= 1
            )

    for agent_index in range(agent_count):
        for interval_index in range(len(required_agents)):
            overlapping = [
                assignments[(agent_index, option.shift_id)]
                for option in shift_options
                if interval_index in option.window_indexes
            ]
            if overlapping:
                model.Add(sum(overlapping) <= 1)

    understaffed: list[cp_model.IntVar] = []
    overstaffed: list[cp_model.IntVar] = []
    max_required = max(required_agents) if required_agents else 0
    max_overstaffing = agent_count

    for interval_index, required in enumerate(required_agents):
        coverage_terms = [
            assignments[(agent_index, option.shift_id)]
            for agent_index in range(agent_count)
            for option in shift_options
            if interval_index in option.covered_indexes
        ]
        under = model.NewIntVar(0, max_required, f"under_{interval_index}")
        over = model.NewIntVar(0, max_overstaffing, f"over_{interval_index}")
        model.Add(sum(coverage_terms) + under - over == required)
        understaffed.append(under)
        overstaffed.append(over)

    total_assignments = sum(assignments.values())
    model.Minimize(
        1000 * sum(understaffed)
        + 10 * sum(overstaffed)
        + total_assignments
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 20260514
    solver.Solve(model)
    return solver, assignments, understaffed, overstaffed


def build_outputs(
    intervals: list[datetime],
    required_agents: list[int],
    agents: list[dict[str, str]],
    shift_options: list[ShiftOption],
    solver: cp_model.CpSolver,
    assignments: dict[tuple[int, int], cp_model.IntVar],
    understaffed: list[cp_model.IntVar],
    overstaffed: list[cp_model.IntVar],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    schedule_rows: list[dict[str, str]] = []
    scheduled_by_interval = [0 for _ in intervals]

    for agent_index, agent in enumerate(agents):
        for option in shift_options:
            if solver.Value(assignments[(agent_index, option.shift_id)]) != 1:
                continue
            shift_start = intervals[option.start_index]
            shift_end = intervals[option.end_index - 1] + timedelta(minutes=30)
            break_start = intervals[option.break_index]
            break_end = break_start + timedelta(minutes=30)
            for covered_index in option.covered_indexes:
                scheduled_by_interval[covered_index] += 1
            schedule_rows.append(
                {
                    "agent_id": agent["agent_id"],
                    "agent_name": agent["agent_name"],
                    "shift_date": shift_start.date().isoformat(),
                    "shift_start_datetime": shift_start.isoformat(timespec="seconds"),
                    "shift_end_datetime": shift_end.isoformat(timespec="seconds"),
                    "break_start_datetime": break_start.isoformat(timespec="seconds"),
                    "break_end_datetime": break_end.isoformat(timespec="seconds"),
                    "covered_intervals": str(len(option.covered_indexes)),
                }
            )

    coverage_rows = [
        {
            "interval_start_datetime": interval.isoformat(timespec="seconds"),
            "required_agents": str(required),
            "scheduled_agents": str(scheduled_by_interval[index]),
            "understaffed_agents": str(int(solver.Value(understaffed[index]))),
            "overstaffed_agents": str(int(solver.Value(overstaffed[index]))),
        }
        for index, (interval, required) in enumerate(zip(intervals, required_agents))
    ]
    return schedule_rows, coverage_rows


def build_summary(
    schedule_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    solver_status: str,
    objective_value: float,
    max_shifts_per_agent: int,
    shift_hours: int,
    break_after_hours: int,
    start_step_minutes: int,
    time_limit_sec: int,
) -> dict[str, float | int | str]:
    total_understaffed = sum(int(row["understaffed_agents"]) for row in coverage_rows)
    total_overstaffed = sum(int(row["overstaffed_agents"]) for row in coverage_rows)
    agents_scheduled = len({row["agent_id"] for row in schedule_rows})
    return {
        "method": "OR-Tools CP-SAT",
        "solver_status": solver_status,
        "objective_value": round(objective_value, 2),
        "scheduled_shifts": len(schedule_rows),
        "agents_scheduled": agents_scheduled,
        "coverage_intervals": len(coverage_rows),
        "shift_hours": shift_hours,
        "break_after_hours": break_after_hours,
        "start_step_minutes": start_step_minutes,
        "max_shifts_per_agent": max_shifts_per_agent,
        "time_limit_sec": time_limit_sec,
        "total_understaffed_agent_intervals": total_understaffed,
        "total_overstaffed_agent_intervals": total_overstaffed,
        "intervals_with_understaffing": sum(
            int(row["understaffed_agents"]) > 0 for row in coverage_rows
        ),
        "intervals_with_overstaffing": sum(
            int(row["overstaffed_agents"]) > 0 for row in coverage_rows
        ),
        "peak_required_agents": max(int(row["required_agents"]) for row in coverage_rows),
        "peak_scheduled_agents": max(int(row["scheduled_agents"]) for row in coverage_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", default="data/processed/staffing_requirements_sample.csv")
    parser.add_argument("--agents", default="data/processed/dim_agents_sample.csv")
    parser.add_argument("--schedule-output", default="data/processed/optimized_schedule_sample.csv")
    parser.add_argument("--coverage-output", default="data/processed/schedule_coverage_sample.csv")
    parser.add_argument("--summary-output", default="docs/scheduling_summary.json")
    parser.add_argument("--fallback-agent-count", type=int, default=60)
    parser.add_argument("--shift-hours", type=int, default=8)
    parser.add_argument("--break-after-hours", type=int, default=4)
    parser.add_argument("--start-step-minutes", type=int, default=60)
    parser.add_argument("--max-shifts-per-agent", type=int, default=5)
    parser.add_argument("--time-limit-sec", type=int, default=60)
    args = parser.parse_args()

    intervals, required_agents = load_requirements(Path(args.requirements))
    agents = load_agents(Path(args.agents), args.fallback_agent_count)
    shift_options = build_shift_options(
        interval_count=len(intervals),
        shift_intervals=args.shift_hours * 2,
        break_after_intervals=args.break_after_hours * 2,
        start_step_intervals=max(1, args.start_step_minutes // 30),
    )
    solver, assignments, understaffed, overstaffed = solve_schedule(
        required_agents=required_agents,
        agent_count=len(agents),
        shift_options=shift_options,
        max_shifts_per_agent=args.max_shifts_per_agent,
        time_limit_sec=args.time_limit_sec,
    )
    status = solver.StatusName()
    if status not in {"OPTIMAL", "FEASIBLE"}:
        raise SystemExit(f"No feasible schedule found. Solver status: {status}")

    schedule_rows, coverage_rows = build_outputs(
        intervals=intervals,
        required_agents=required_agents,
        agents=agents,
        shift_options=shift_options,
        solver=solver,
        assignments=assignments,
        understaffed=understaffed,
        overstaffed=overstaffed,
    )
    write_csv(Path(args.schedule_output), schedule_rows, SCHEDULE_FIELDS)
    write_csv(Path(args.coverage_output), coverage_rows, COVERAGE_FIELDS)

    summary = build_summary(
        schedule_rows=schedule_rows,
        coverage_rows=coverage_rows,
        solver_status=status,
        objective_value=solver.ObjectiveValue(),
        max_shifts_per_agent=args.max_shifts_per_agent,
        shift_hours=args.shift_hours,
        break_after_hours=args.break_after_hours,
        start_step_minutes=args.start_step_minutes,
        time_limit_sec=args.time_limit_sec,
    )
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
