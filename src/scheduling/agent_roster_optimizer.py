"""Build a legal agent roster from interval staffing requirements."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from .christie_names import christie_agent_name
except ImportError:
    from christie_names import christie_agent_name


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
class ShiftCandidate:
    shift_id: int
    week_start: date
    shift_date: date
    start_datetime: datetime
    end_datetime: datetime
    break_start_datetime: datetime
    active_indexes: tuple[int, ...]
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


def week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def build_agents(agent_count: int) -> list[dict[str, str]]:
    return [
        {"agent_id": str(agent_id), "agent_name": christie_agent_name(agent_id)}
        for agent_id in range(1, agent_count + 1)
    ]


def interval_index(horizon_start: datetime, value: datetime) -> int:
    return int((value - horizon_start).total_seconds() // 1800)


def build_week_candidates(
    intervals: list[datetime],
    current_week_start: date,
    shift_hours: int,
    break_after_hours: int,
    start_step_minutes: int,
) -> list[ShiftCandidate]:
    horizon_start = intervals[0]
    horizon_end = intervals[-1] + timedelta(minutes=30)
    interval_count = len(intervals)
    candidates: list[ShiftCandidate] = []
    shift_id = 0

    for day_offset in range(7):
        shift_day = current_week_start + timedelta(days=day_offset)
        day_start = datetime.combine(shift_day, datetime.min.time())
        for start_minute in range(0, 24 * 60, start_step_minutes):
            shift_start = day_start + timedelta(minutes=start_minute)
            shift_end = shift_start + timedelta(hours=shift_hours)
            break_start = shift_start + timedelta(hours=break_after_hours)

            if shift_start < horizon_start or shift_start >= horizon_end:
                continue

            active: list[int] = []
            covered: list[int] = []
            first_index = interval_index(horizon_start, shift_start)
            last_index = interval_index(horizon_start, shift_end - timedelta(minutes=30))
            for index in range(first_index, last_index + 1):
                if not 0 <= index < interval_count:
                    continue
                interval_start = intervals[index]
                active.append(index)
                if interval_start != break_start:
                    covered.append(index)

            if not active or not covered:
                continue

            candidates.append(
                ShiftCandidate(
                    shift_id=shift_id,
                    week_start=current_week_start,
                    shift_date=shift_day,
                    start_datetime=shift_start,
                    end_datetime=shift_end,
                    break_start_datetime=break_start,
                    active_indexes=tuple(active),
                    covered_indexes=tuple(covered),
                )
            )
            shift_id += 1

    return candidates


def solve_week_shift_counts(
    required: list[int],
    existing_active: list[int],
    existing_coverage: list[int],
    candidates: list[ShiftCandidate],
    week_interval_indexes: list[int],
    agent_count: int,
    max_shifts_per_agent_per_week: int,
    time_limit_sec: int,
) -> tuple[list[int], str, float]:
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()
    max_weekly_shifts = agent_count * max_shifts_per_agent_per_week
    counts = [
        model.NewIntVar(0, agent_count, f"shift_{candidate.shift_id}_count")
        for candidate in candidates
    ]

    candidates_by_day: dict[date, list[int]] = defaultdict(list)
    candidates_covering_interval: dict[int, list[int]] = defaultdict(list)
    candidates_active_interval: dict[int, list[int]] = defaultdict(list)

    for candidate_index, candidate in enumerate(candidates):
        candidates_by_day[candidate.shift_date].append(candidate_index)
        for interval in candidate.covered_indexes:
            candidates_covering_interval[interval].append(candidate_index)
        for interval in candidate.active_indexes:
            candidates_active_interval[interval].append(candidate_index)

    for candidate_indexes in candidates_by_day.values():
        model.Add(sum(counts[index] for index in candidate_indexes) <= agent_count)

    model.Add(sum(counts) <= max_weekly_shifts)

    under_vars = []
    over_vars = []
    peak_required = max(required) if required else 0

    for interval_index in week_interval_indexes:
        coverage_terms = [
            counts[index] for index in candidates_covering_interval.get(interval_index, [])
        ]
        active_terms = [
            counts[index] for index in candidates_active_interval.get(interval_index, [])
        ]
        under = model.NewIntVar(0, peak_required, f"under_{interval_index}")
        over = model.NewIntVar(0, agent_count, f"over_{interval_index}")
        model.Add(
            existing_coverage[interval_index]
            + sum(coverage_terms)
            + under
            - over
            == required[interval_index]
        )
        model.Add(existing_active[interval_index] + sum(active_terms) <= agent_count)
        under_vars.append(under)
        over_vars.append(over)

    model.Minimize(1000 * sum(under_vars) + 10 * sum(over_vars) + sum(counts))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 20260515
    status = solver.Solve(model)
    if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        raise SystemExit(f"No feasible weekly shift count plan found: {solver.StatusName()}")

    return [int(solver.Value(value)) for value in counts], solver.StatusName(), solver.ObjectiveValue()


def assign_shift_instances(
    agents: list[dict[str, str]],
    shift_instances: list[ShiftCandidate],
    max_shifts_per_agent_per_week: int,
    min_rest_hours: int,
    last_end_by_agent: dict[str, datetime],
    weekly_counts: dict[tuple[str, date], int],
    worked_dates: dict[tuple[str, date], set[date]],
) -> tuple[list[dict[str, str]], list[ShiftCandidate], list[ShiftCandidate]]:
    assigned_rows: list[dict[str, str]] = []
    assigned_shifts: list[ShiftCandidate] = []
    unassigned: list[ShiftCandidate] = []

    for shift in sorted(shift_instances, key=lambda value: (value.start_datetime, value.shift_id)):
        eligible: list[tuple[int, datetime, int, dict[str, str]]] = []
        for agent in agents:
            agent_id = agent["agent_id"]
            weekly_key = (agent_id, shift.week_start)
            worked_key = (agent_id, shift.week_start)
            if weekly_counts[weekly_key] >= max_shifts_per_agent_per_week:
                continue
            if shift.shift_date in worked_dates[worked_key]:
                continue
            earliest_start = last_end_by_agent.get(agent_id, datetime.min) + timedelta(hours=min_rest_hours)
            if shift.start_datetime < earliest_start:
                continue
            eligible.append(
                (
                    weekly_counts[weekly_key],
                    last_end_by_agent.get(agent_id, datetime.min),
                    int(agent_id),
                    agent,
                )
            )

        if not eligible:
            unassigned.append(shift)
            continue

        _, _, _, selected_agent = min(eligible)
        agent_id = selected_agent["agent_id"]
        weekly_key = (agent_id, shift.week_start)
        worked_key = (agent_id, shift.week_start)
        weekly_counts[weekly_key] += 1
        worked_dates[worked_key].add(shift.shift_date)
        last_end_by_agent[agent_id] = shift.end_datetime
        assigned_shifts.append(shift)
        assigned_rows.append(
            {
                "agent_id": agent_id,
                "agent_name": selected_agent["agent_name"],
                "shift_date": shift.shift_date.isoformat(),
                "shift_start_datetime": shift.start_datetime.isoformat(timespec="seconds"),
                "shift_end_datetime": shift.end_datetime.isoformat(timespec="seconds"),
                "break_start_datetime": shift.break_start_datetime.isoformat(timespec="seconds"),
                "break_end_datetime": (
                    shift.break_start_datetime + timedelta(minutes=30)
                ).isoformat(timespec="seconds"),
                "covered_intervals": str(len(shift.covered_indexes)),
            }
        )

    return assigned_rows, assigned_shifts, unassigned


def schedule_coverage(
    intervals: list[datetime],
    required: list[int],
    assigned_shifts: list[ShiftCandidate],
) -> list[dict[str, str]]:
    scheduled = [0 for _ in intervals]
    for shift in assigned_shifts:
        for interval_index in shift.covered_indexes:
            scheduled[interval_index] += 1

    rows: list[dict[str, str]] = []
    for interval, required_agents, scheduled_agents in zip(intervals, required, scheduled):
        rows.append(
            {
                "interval_start_datetime": interval.isoformat(timespec="seconds"),
                "required_agents": str(required_agents),
                "scheduled_agents": str(scheduled_agents),
                "understaffed_agents": str(max(required_agents - scheduled_agents, 0)),
                "overstaffed_agents": str(max(scheduled_agents - required_agents, 0)),
            }
        )
    return rows


def build_summary(
    schedule_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    agent_count: int,
    max_shifts_per_agent_per_week: int,
    min_rest_hours: int,
    shift_hours: int,
    break_after_hours: int,
    start_step_minutes: int,
    unassigned_shift_count: int,
    weekly_statuses: list[str],
    weekly_objective_value: float,
) -> dict[str, object]:
    required_total = sum(int(row["required_agents"]) for row in coverage_rows)
    total_understaffed = sum(int(row["understaffed_agents"]) for row in coverage_rows)
    total_overstaffed = sum(int(row["overstaffed_agents"]) for row in coverage_rows)
    first_interval = datetime.fromisoformat(coverage_rows[0]["interval_start_datetime"])
    last_interval = datetime.fromisoformat(coverage_rows[-1]["interval_start_datetime"])
    horizon_days = max((last_interval.date() - first_interval.date()).days + 1, 1)
    required_agent_hours = required_total * 0.5
    productive_shift_hours = max(shift_hours - 0.5, 0.5)
    productive_hours_per_agent = (
        productive_shift_hours * max_shifts_per_agent_per_week * horizon_days / 7
    )
    estimated_full_coverage_agents = (
        math.ceil(required_agent_hours / productive_hours_per_agent)
        if productive_hours_per_agent
        else 0
    )
    daily_shift_counts = defaultdict(int)
    for row in schedule_rows:
        daily_shift_counts[row["shift_date"]] += 1

    return {
        "method": "OR-Tools CP-SAT weekly shift-count optimization with legal agent roster assignment",
        "solver_status": "FEASIBLE" if schedule_rows else "NO_SCHEDULE",
        "weekly_solver_statuses": sorted(set(weekly_statuses)),
        "objective_value": round(weekly_objective_value, 2),
        "scheduled_shifts": len(schedule_rows),
        "agent_pool_size": agent_count,
        "agents_scheduled": len({row["agent_id"] for row in schedule_rows}),
        "coverage_intervals": len(coverage_rows),
        "horizon_start": coverage_rows[0]["interval_start_datetime"],
        "horizon_end": coverage_rows[-1]["interval_start_datetime"],
        "shift_hours": shift_hours,
        "break_after_hours": break_after_hours,
        "start_step_minutes": start_step_minutes,
        "max_one_shift_per_agent_per_day": True,
        "max_shifts_per_agent_per_week": max_shifts_per_agent_per_week,
        "min_rest_hours": min_rest_hours,
        "required_agent_hours": round(required_agent_hours, 2),
        "productive_hours_per_agent_in_horizon": round(productive_hours_per_agent, 2),
        "estimated_full_coverage_agents": estimated_full_coverage_agents,
        "approved_agent_pool_gap": max(estimated_full_coverage_agents - agent_count, 0),
        "unassigned_optimized_shifts": unassigned_shift_count,
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
        "peak_understaffed_agents": max(int(row["understaffed_agents"]) for row in coverage_rows),
        "coverage_achieved_rate": round(
            (required_total - total_understaffed) / required_total,
            4,
        ) if required_total else 0,
        "max_daily_shifts": max(daily_shift_counts.values()) if daily_shift_counts else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", default="data/processed/full_staffing_requirements.csv")
    parser.add_argument("--schedule-output", default="data/processed/full_optimized_schedule.csv")
    parser.add_argument("--coverage-output", default="data/processed/full_schedule_coverage.csv")
    parser.add_argument("--summary-output", default="docs/full_scheduling_summary.json")
    parser.add_argument("--agent-count", type=int, default=160)
    parser.add_argument("--shift-hours", type=int, default=8)
    parser.add_argument("--break-after-hours", type=int, default=4)
    parser.add_argument("--start-step-minutes", type=int, default=60)
    parser.add_argument("--max-shifts-per-agent-per-week", type=int, default=5)
    parser.add_argument("--min-rest-hours", type=int, default=11)
    parser.add_argument("--weekly-time-limit-sec", type=int, default=30)
    args = parser.parse_args()

    intervals, required = load_requirements(Path(args.requirements))
    agents = build_agents(args.agent_count)
    first_week = week_start(intervals[0].date())
    last_week = week_start(intervals[-1].date())
    week = first_week

    existing_active = [0 for _ in intervals]
    existing_coverage = [0 for _ in intervals]
    assigned_schedule_rows: list[dict[str, str]] = []
    assigned_shifts: list[ShiftCandidate] = []
    unassigned_shift_count = 0
    weekly_statuses: list[str] = []
    weekly_objective_value = 0.0
    last_end_by_agent: dict[str, datetime] = {}
    weekly_counts: dict[tuple[str, date], int] = defaultdict(int)
    worked_dates: dict[tuple[str, date], set[date]] = defaultdict(set)

    while week <= last_week:
        week_end = week + timedelta(days=7)
        week_interval_indexes = [
            index
            for index, interval in enumerate(intervals)
            if week <= interval.date() < week_end
        ]
        candidates = build_week_candidates(
            intervals=intervals,
            current_week_start=week,
            shift_hours=args.shift_hours,
            break_after_hours=args.break_after_hours,
            start_step_minutes=args.start_step_minutes,
        )
        counts, status, objective = solve_week_shift_counts(
            required=required,
            existing_active=existing_active,
            existing_coverage=existing_coverage,
            candidates=candidates,
            week_interval_indexes=week_interval_indexes,
            agent_count=args.agent_count,
            max_shifts_per_agent_per_week=args.max_shifts_per_agent_per_week,
            time_limit_sec=args.weekly_time_limit_sec,
        )
        weekly_statuses.append(status)
        weekly_objective_value += objective

        shift_instances: list[ShiftCandidate] = []
        for candidate, count in zip(candidates, counts):
            shift_instances.extend([candidate] * count)

        schedule_rows, assigned_this_week, unassigned = assign_shift_instances(
            agents=agents,
            shift_instances=shift_instances,
            max_shifts_per_agent_per_week=args.max_shifts_per_agent_per_week,
            min_rest_hours=args.min_rest_hours,
            last_end_by_agent=last_end_by_agent,
            weekly_counts=weekly_counts,
            worked_dates=worked_dates,
        )
        assigned_schedule_rows.extend(schedule_rows)
        unassigned_shift_count += len(unassigned)
        assigned_shifts.extend(assigned_this_week)
        for shift in assigned_this_week:
            for interval_index in shift.active_indexes:
                existing_active[interval_index] += 1
            for interval_index in shift.covered_indexes:
                existing_coverage[interval_index] += 1

        print(
            json.dumps(
                {
                    "week_start": week.isoformat(),
                    "status": status,
                    "optimized_shifts": sum(counts),
                    "assigned_shifts": len(schedule_rows),
                    "unassigned_shifts": len(unassigned),
                }
            )
        )
        week = week_end

    coverage_rows = schedule_coverage(intervals, required, assigned_shifts)
    write_csv(Path(args.schedule_output), assigned_schedule_rows, SCHEDULE_FIELDS)
    write_csv(Path(args.coverage_output), coverage_rows, COVERAGE_FIELDS)
    summary = build_summary(
        schedule_rows=assigned_schedule_rows,
        coverage_rows=coverage_rows,
        agent_count=args.agent_count,
        max_shifts_per_agent_per_week=args.max_shifts_per_agent_per_week,
        min_rest_hours=args.min_rest_hours,
        shift_hours=args.shift_hours,
        break_after_hours=args.break_after_hours,
        start_step_minutes=args.start_step_minutes,
        unassigned_shift_count=unassigned_shift_count,
        weekly_statuses=weekly_statuses,
        weekly_objective_value=weekly_objective_value,
    )
    Path(args.summary_output).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
