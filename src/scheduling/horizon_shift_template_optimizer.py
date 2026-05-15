"""Horizon-wide shift-template optimizer for large staffing curves."""

from __future__ import annotations

import argparse
import csv
import heapq
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
class Template:
    template_id: int
    start_index: int
    end_index: int
    break_index: int
    covered_indexes: tuple[int, ...]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        return list(csv.DictReader(input_file))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_requirements(path: Path) -> tuple[list[datetime], list[int]]:
    rows = read_csv(path)
    pairs = sorted(
        (
            datetime.fromisoformat(row["interval_start_datetime"]),
            int(row["shrinkage_adjusted_agents"]),
        )
        for row in rows
    )
    return [pair[0] for pair in pairs], [pair[1] for pair in pairs]


def build_templates(
    interval_count: int,
    shift_intervals: int,
    break_after_intervals: int,
    start_step_intervals: int,
) -> list[Template]:
    templates: list[Template] = []
    template_id = 0
    latest_start = interval_count - shift_intervals
    for start in range(0, latest_start + 1, start_step_intervals):
        end = start + shift_intervals
        break_index = start + break_after_intervals
        covered = tuple(index for index in range(start, end) if index != break_index)
        templates.append(
            Template(
                template_id=template_id,
                start_index=start,
                end_index=end,
                break_index=break_index,
                covered_indexes=covered,
            )
        )
        template_id += 1
    return templates


def solve_horizon(
    required: list[int],
    templates: list[Template],
    time_limit_sec: int,
    allow_understaffing: bool,
) -> tuple[list[int], list[int], list[int], list[int], str, float]:
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    peak_required = max(required) if required else 0
    max_template_count = max(peak_required * 2, 1)
    counts = [
        model.NewIntVar(0, max_template_count, f"template_{template.template_id}_count")
        for template in templates
    ]
    under_vars = []
    over_vars = []
    templates_by_interval: list[list[int]] = [[] for _ in required]
    for template_index, template in enumerate(templates):
        for interval_index in template.covered_indexes:
            templates_by_interval[interval_index].append(template_index)

    for interval_index, required_agents in enumerate(required):
        coverage_terms = [counts[index] for index in templates_by_interval[interval_index]]
        under_limit = peak_required if allow_understaffing else 0
        under = model.NewIntVar(0, under_limit, f"under_{interval_index}")
        over = model.NewIntVar(0, max_template_count * len(templates), f"over_{interval_index}")
        model.Add(sum(coverage_terms) + under - over == required_agents)
        under_vars.append(under)
        over_vars.append(over)

    model.Minimize(1000 * sum(under_vars) + 10 * sum(over_vars) + sum(counts))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 20260515
    status = solver.Solve(model)
    if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        raise SystemExit(f"No feasible schedule found. Solver status: {solver.StatusName()}")

    scheduled_counts = [int(solver.Value(value)) for value in counts]
    under = [int(solver.Value(value)) for value in under_vars]
    over = [int(solver.Value(value)) for value in over_vars]
    scheduled = []
    for interval_index in range(len(required)):
        scheduled.append(sum(scheduled_counts[index] for index in templates_by_interval[interval_index]))
    return scheduled_counts, scheduled, under, over, solver.StatusName(), solver.ObjectiveValue()


def assign_agents(
    intervals: list[datetime],
    templates: list[Template],
    counts: list[int],
    agent_count: int,
) -> list[dict[str, str]]:
    available_agents = [(0, agent_id) for agent_id in range(1, agent_count + 1)]
    heapq.heapify(available_agents)
    rows: list[dict[str, str]] = []

    for template, count in zip(templates, counts):
        for _ in range(count):
            if not available_agents or available_agents[0][0] > template.start_index:
                raise SystemExit(f"Agent pool too small. Increase above {agent_count}.")
            _, agent_id = heapq.heappop(available_agents)
            shift_start = intervals[template.start_index]
            shift_end = intervals[template.end_index - 1] + timedelta(minutes=30)
            break_start = intervals[template.break_index]
            break_end = break_start + timedelta(minutes=30)
            rows.append(
                {
                    "agent_id": str(agent_id),
                    "agent_name": f"Agent {agent_id:04d}",
                    "shift_date": shift_start.date().isoformat(),
                    "shift_start_datetime": shift_start.isoformat(timespec="seconds"),
                    "shift_end_datetime": shift_end.isoformat(timespec="seconds"),
                    "break_start_datetime": break_start.isoformat(timespec="seconds"),
                    "break_end_datetime": break_end.isoformat(timespec="seconds"),
                    "covered_intervals": str(len(template.covered_indexes)),
                }
            )
            heapq.heappush(available_agents, (template.end_index, agent_id))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", default="data/processed/full_staffing_requirements.csv")
    parser.add_argument("--schedule-output", default="data/processed/full_optimized_schedule.csv")
    parser.add_argument("--coverage-output", default="data/processed/full_schedule_coverage.csv")
    parser.add_argument("--summary-output", default="docs/full_scheduling_summary.json")
    parser.add_argument("--agent-count", type=int, default=500)
    parser.add_argument("--shift-hours", type=int, default=8)
    parser.add_argument("--break-after-hours", type=int, default=4)
    parser.add_argument("--start-step-minutes", type=int, default=60)
    parser.add_argument("--time-limit-sec", type=int, default=120)
    parser.add_argument(
        "--allow-understaffing",
        action="store_true",
        help="Allow understaffed intervals with a heavy objective penalty.",
    )
    args = parser.parse_args()

    intervals, required = load_requirements(Path(args.requirements))
    templates = build_templates(
        interval_count=len(intervals),
        shift_intervals=args.shift_hours * 2,
        break_after_intervals=args.break_after_hours * 2,
        start_step_intervals=max(1, args.start_step_minutes // 30),
    )
    counts, scheduled, under, over, status, objective = solve_horizon(
        required=required,
        templates=templates,
        time_limit_sec=args.time_limit_sec,
        allow_understaffing=args.allow_understaffing,
    )
    schedule_rows = assign_agents(intervals, templates, counts, args.agent_count)
    coverage_rows = [
        {
            "interval_start_datetime": interval.isoformat(timespec="seconds"),
            "required_agents": str(required_agents),
            "scheduled_agents": str(scheduled_agents),
            "understaffed_agents": str(under_agents),
            "overstaffed_agents": str(over_agents),
        }
        for interval, required_agents, scheduled_agents, under_agents, over_agents in zip(
            intervals,
            required,
            scheduled,
            under,
            over,
        )
    ]
    write_csv(Path(args.schedule_output), schedule_rows, SCHEDULE_FIELDS)
    write_csv(Path(args.coverage_output), coverage_rows, COVERAGE_FIELDS)

    summary = {
        "method": "OR-Tools CP-SAT horizon-wide shift-template optimization",
        "solver_status": status,
        "objective_value": round(objective, 2),
        "scheduled_shifts": sum(counts),
        "agent_pool_size": args.agent_count,
        "coverage_intervals": len(coverage_rows),
        "shift_hours": args.shift_hours,
        "break_after_hours": args.break_after_hours,
        "start_step_minutes": args.start_step_minutes,
        "allow_understaffing": args.allow_understaffing,
        "total_understaffed_agent_intervals": sum(under),
        "total_overstaffed_agent_intervals": sum(over),
        "intervals_with_understaffing": sum(value > 0 for value in under),
        "intervals_with_overstaffing": sum(value > 0 for value in over),
        "peak_required_agents": max(required),
        "peak_scheduled_agents": max(scheduled),
        "schedule_output": args.schedule_output,
        "coverage_output": args.coverage_output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
