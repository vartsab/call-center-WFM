# Shift Scheduling Methodology

## Purpose

The scheduling step converts interval staffing requirements into an agent shift plan. This is an operations research problem because the schedule must balance coverage, overstaffing, and labor constraints.

## Input

The current planning roster optimizer uses:

- `data/processed/future_staffing_requirements.csv` for shrinkage-adjusted required agents;
- a 160-agent planning pool;
- 30-minute planning intervals for the 2026-01-01 to 2026-01-31 future forecast horizon.

## Optimization Model

The full-history roster uses Google OR-Tools CP-SAT to choose weekly shift counts by start time, then assigns those shifts to named agents while enforcing human roster rules. A shift represents an 8-hour work window with a 30-minute break after 4 hours.

Current shift assumptions:

| Constraint | Value |
| --- | ---: |
| Shift window | 8 hours |
| Break | 30 minutes after 4 hours |
| Shift start options | hourly |
| Agent pool | 160 total agents |
| Maximum shifts | 5 per agent per week |
| Daily limit | 1 shift per agent per day |
| Minimum rest | 11 hours between shifts |
| Understaffing | allowed with a high penalty |
| Solver time limit | 20 seconds per week |

The objective minimizes understaffing first, then overstaffing, then total scheduled shifts. Understaffing is allowed because the approved 160-person workforce pool is materially below the full-coverage roster estimate produced by the January 2026 demand curve.

## Latest January 2026 Planning Result

| Metric | Value |
| --- | ---: |
| Solver status | FEASIBLE |
| Scheduled shifts | 3,427 |
| Agent pool size | 160 |
| Full-coverage roster estimate | 462 |
| Coverage intervals | 1,488 |
| Understaffed agent-intervals | 101,875 |
| Overstaffed agent-intervals | 0 |
| Intervals with understaffing | 1,395 |
| Intervals with overstaffing | 0 |
| Peak required agents | 189 |
| Peak scheduled agents | 160 |
| Coverage achieved | 33.54% |
| One-shift-per-agent-per-day violations | 0 |
| Weekly shift-limit violations | 0 |
| Rest violations | 0 |

This schedule is a legal human roster for the future planning month. It also shows an important planning finding: a 160-person total employee pool is not sufficient to cover the 24/7 staffing curve produced by the forecast and Erlang C calculation.

## Output

The generated local files are:

```text
data/processed/future_optimized_schedule.csv
data/processed/future_schedule_coverage.csv
docs/future_scheduling_summary.json
```

## Limitations

- Skill-based routing is not yet enforced in the schedule.
- Labor-law rules are simplified to shift length, break placement, and shift start options.
