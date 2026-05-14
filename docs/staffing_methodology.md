# Staffing Requirement Methodology

## Purpose

The staffing step converts the 30-minute call volume forecast into a required number of agents for each interval. This is a prescriptive calculation that uses queueing theory rather than machine learning.

## Input

The latest staffing artifact uses:

- `data/processed/sklearn_best_forecast_sample.csv` for interval-level predicted call volume;
- `data/processed/forecasting_input_sample.csv` for interval-level average handle time;
- a 30-minute planning interval.

## Erlang C Calculation

For each interval, offered load is calculated as:

```text
traffic intensity = predicted calls * average handle time / interval seconds
```

The Erlang C formula estimates the probability that an arriving caller must wait. Service level is then estimated as the probability that a call is answered within the target answer time.

The first configuration uses:

| Parameter | Value |
| --- | ---: |
| Planning interval | 30 minutes |
| Target service level | 80% |
| Target answer time | 20 seconds |
| Maximum occupancy | 85% |
| Shrinkage assumption | 30% |

The base required agent count is the smallest integer that satisfies both the service-level target and occupancy cap. The shrinkage-adjusted agent count increases the base count to account for non-phone time such as breaks, meetings, training, and absence.

## Output

The generated staffing file is:

```text
data/processed/staffing_requirements_sample.csv
```

The committed summary file is:

```text
docs/staffing_requirements_summary.json
```

## Limitations

- The first staffing run uses a baseline forecast rather than an advanced forecast model.
- The shrinkage rate is a planning assumption, not an observed workforce metric.
- Erlang C assumes a simplified inbound queue and does not capture every real contact center behavior.
