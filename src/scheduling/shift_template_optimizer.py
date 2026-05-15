"""Scalable daily shift-template optimizer for full-history staffing curves."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
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


def load_requirements(path: Path) -> dict[str, list[tuple[datetime, int]]]:
    days: dict[str, list[tuple[datetime, int]]] = defaultdict(list)
    for row in read_csv(path):
        interval = datetime.fromisoformat(row["interval_start_datetime"])
        days[interval.date().isoformat()].append(
            (interval, int(row["shrinkage_adjusted_agents"]))
        )
    return {
        day: sorted(values, key=lambda item: item[0])
        for day, values in sorted(days.items())
    }


def build_templates(shift_intervals: int, break_after_intervals: int, start_step_intervals: int) -> list[Template]:
    templates: list[Template] = []
    template_id = 0
    latest_start = 48 - shift_intervals
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


def solve_day(required: list[int], templates: list[Template], time_limit_sec: int) -> tuple[list[int], list[int], list[int], list[int], str, float]:
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

    for interval_index, required_agents in enumerate(required):
        coverage_terms = [
            counts[index]
            for index, template in enumerate(templates)
            if interval_index in template.covered_indexes
        ]
        under = model.NewIntVar(0, peak_required, f"under_{interval_index}")
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
        raise SystemExit(f"No feasible daily schedule found. Solver status: {solver.StatusName()}")

    scheduled_counts = [int(solver.Value(value)) for value in counts]
    under = [int(solver.Value(value)) for value in under_vars]
    over = [int(solver.Value(value)) for value in over_vars]
    scheduled = []
    for interval_index in range(len(required)):
        scheduled.append(
            sum(
                scheduled_counts[index]
                for index, template in enumerate(templates)
                if interval_index in template.covered_indexes
            )
        )
    return scheduled_counts, scheduled, under, over, solver.StatusName(), solver.ObjectiveValue()


def agent_pool(size: int) -> list[dict[str, str]]:
    return [
        {"agent_id": str(index), "agent_name": f"Agent {index:04d}"}
        for index in range(1, size + 1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", default="data/processed/full_staffing_requirements.csv")
    parser.add_argument("--schedule-output", default="data/processed/full_optimized_schedule.csv")
    parser.add_argument("--coverage-output", default="data/processed/full_schedule_coverage.csv")
    parser.add_argument("--summary-output", default="docs/full_scheduling_summary.json")
    parser.add_argument("--agent-count", type=int, default=700)
    parser.add_argument("--shift-hours", type=int, default=8)
    parser.add_argument("--break-after-hours", type=int, default=4)
    parser.add_argument("--start-step-minutes", type=int, default=60)
    parser.add_argument("--time-limit-sec", type=int, default=10)
    args = parser.parse_args()

    days = load_requirements(Path(args.requirements))
    templates = build_templates(
        shift_intervals=args.shift_hours * 2,
        break_after_intervals=args.break_after_hours * 2,
        start_step_intervals=max(1, args.start_step_minutes // 30),
    )
    agents = agent_pool(args.agent_count)
    schedule_rows: list[dict[str, str]] = []
    coverage_rows: list[dict[str, str]] = []
    statuses: set[str] = set()
    objective_value = 0.0
    total_shifts = 0

    for day_index, (day, day_values) in enumerate(days.items()):
        intervals = [value[0] for value in day_values]
        required = [value[1] for value in day_values]
        counts, scheduled, under, over, status, objective = solve_day(
            required=required,
            templates=templates,
            time_limit_sec=args.time_limit_sec,
        )
        statuses.add(status)
        objective_value += objective

        agent_cursor = 0
        for template, template_count in zip(templates, counts):
            for _ in range(template_count):
                if agent_cursor >= len(agents):
                    raise SystemExit(
                        f"Agent pool too small for {day}. Need more than {args.agent_count} agents."
                    )
                agent = agents[agent_cursor]
                agent_cursor += 1
                shift_start = intervals[template.start_index]
                shift_end = intervals[template.end_index - 1] + timedelta(minutes=30)
                break_start = intervals[template.break_index]
                break_end = break_start + timedelta(minutes=30)
                schedule_rows.append(
                    {
                        "agent_id": agent["agent_id"],
                        "agent_name": agent["agent_name"],
                        "shift_date": day,
                        "shift_start_datetime": shift_start.isoformat(timespec="seconds"),
                        "shift_end_datetime": shift_end.isoformat(timespec="seconds"),
                        "break_start_datetime": break_start.isoformat(timespec="seconds"),
                        "break_end_datetime": break_end.isoformat(timespec="seconds"),
                        "covered_intervals": str(len(template.covered_indexes)),
                    }
                )
        total_shifts += sum(counts)

        for interval, required_agents, scheduled_agents, under_agents, over_agents in zip(
            intervals,
            required,
            scheduled,
            under,
            over,
        ):
            coverage_rows.append(
                {
                    "interval_start_datetime": interval.isoformat(timespec="seconds"),
                    "required_agents": str(required_agents),
                    "scheduled_agents": str(scheduled_agents),
                    "understaffed_agents": str(under_agents),
                    "overstaffed_agents": str(over_agents),
                }
            )
        print(f"{day_index + 1}/{len(days)} {day}: {sum(counts):,} shifts")

    write_csv(Path(args.schedule_output), schedule_rows, SCHEDULE_FIELDS)
    write_csv(Path(args.coverage_output), coverage_rows, COVERAGE_FIELDS)

    summary = {
        "method": "OR-Tools CP-SAT daily shift-template optimization",
        "solver_statuses": sorted(statuses),
        "objective_value": round(objective_value, 2),
        "scheduled_shifts": total_shifts,
        "agent_pool_size": args.agent_count,
        "coverage_intervals": len(coverage_rows),
        "shift_hours": args.shift_hours,
        "break_after_hours": args.break_after_hours,
        "start_step_minutes": args.start_step_minutes,
        "total_understaffed_agent_intervals": sum(int(row["understaffed_agents"]) for row in coverage_rows),
        "total_overstaffed_agent_intervals": sum(int(row["overstaffed_agents"]) for row in coverage_rows),
        "intervals_with_understaffing": sum(int(row["understaffed_agents"]) > 0 for row in coverage_rows),
        "intervals_with_overstaffing": sum(int(row["overstaffed_agents"]) > 0 for row in coverage_rows),
        "peak_required_agents": max(int(row["required_agents"]) for row in coverage_rows),
        "peak_scheduled_agents": max(int(row["scheduled_agents"]) for row in coverage_rows),
        "schedule_output": args.schedule_output,
        "coverage_output": args.coverage_output,
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
