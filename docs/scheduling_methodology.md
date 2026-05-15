# Shift Scheduling Methodology

## Purpose

The scheduling step converts interval staffing requirements into an agent shift plan. This is an operations research problem because the schedule must balance coverage, overstaffing, and labor constraints.

## Input

The current full-history optimizer uses:

- `data/processed/full_staffing_requirements.csv` for shrinkage-adjusted required agents;
- a 500-agent planning pool;
- 30-minute planning intervals for the 2025-10-03 to 2025-12-31 forecast horizon.

## Optimization Model

The full-history optimizer uses Google OR-Tools CP-SAT with horizon-wide shift-template counts. A template represents an 8-hour shift with a 30-minute break after 4 hours. The model chooses the number of agents assigned to each shift template across the full forecast horizon.

Current shift assumptions:

| Constraint | Value |
| --- | ---: |
| Shift window | 8 hours |
| Break | 30 minutes after 4 hours |
| Shift start options | hourly |
| Understaffing | hard constraint, zero allowed |
| Solver time limit | 180 seconds |

The objective minimizes overstaffing and total scheduled shifts while preserving required coverage in every interval.

## Latest Full-History Result

| Metric | Value |
| --- | ---: |
| Solver status | FEASIBLE |
| Scheduled shifts | 33,544 |
| Agent pool size | 500 |
| Coverage intervals | 4,320 |
| Understaffed agent-intervals | 0 |
| Overstaffed agent-intervals | 58,778 |
| Intervals with understaffing | 0 |
| Intervals with overstaffing | 2,861 |
| Peak required agents | 193 |
| Peak scheduled agents | 267 |

This replaces the earlier daily decomposition run. The horizon-wide optimizer reduced total overstaffing and removed all understaffed intervals across the 90-day holdout schedule.

## Output

The generated local files are:

```text
data/processed/full_optimized_schedule.csv
data/processed/full_schedule_coverage.csv
docs/full_scheduling_summary.json
```

## Limitations

- The current full-history optimizer uses anonymous shift-template counts before assigning generated agent IDs.
- Skill-based routing is not yet enforced in the schedule.
- Labor-law rules are simplified to shift length, break placement, and shift start options.
