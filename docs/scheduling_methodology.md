# Shift Scheduling Methodology

## Purpose

The scheduling step converts interval staffing requirements into an agent shift plan. This is an operations research problem because the schedule must balance coverage, overstaffing, and labor constraints.

## Input

The first optimizer uses:

- `data/processed/staffing_requirements_sample.csv` for shrinkage-adjusted required agents;
- `data/processed/dim_agents_sample.csv` for the available synthetic agent pool;
- 30-minute planning intervals.

## Optimization Model

The first version uses Google OR-Tools CP-SAT. Decision variables indicate whether an agent is assigned to a candidate shift.

Current shift assumptions:

| Constraint | Value |
| --- | ---: |
| Shift window | 8 hours |
| Break | 30 minutes after 4 hours |
| Shift start options | hourly |
| Maximum shifts per agent | 5 per horizon |
| Maximum shifts per agent per day | 1 |

The objective minimizes:

1. understaffing;
2. overstaffing;
3. total assigned shifts.

Understaffing receives the strongest penalty because missing required coverage is worse than moderate overstaffing in a service-level planning context.

## Latest Result

The latest sample run produced:

| Metric | Value |
| --- | ---: |
| Solver status | FEASIBLE |
| Scheduled shifts | 123 |
| Agents scheduled | 55 |
| Coverage intervals | 336 |
| Understaffed agent-intervals | 0 |
| Overstaffed agent-intervals | 343 |
| Intervals with understaffing | 0 |
| Peak required agents | 8 |
| Peak scheduled agents | 10 |

## Output

The generated local files are:

```text
data/processed/optimized_schedule_sample.csv
data/processed/schedule_coverage_sample.csv
```

The committed summary file is:

```text
docs/scheduling_summary.json
```

## Limitations

- The first optimizer uses generic shift patterns and does not yet model agent-specific availability.
- Skill-based routing is not yet enforced in the schedule.
- Labor-law rules are simplified to maximum shifts, daily shift count, and a break window.
