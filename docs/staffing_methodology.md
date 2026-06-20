# Staffing Requirement Methodology

## Purpose

The staffing step converts the 30-minute demand forecast into the required number of agents through a queueing-theory calculation.

## Input

The current full-history staffing artifact uses:

- `data/processed/full_sklearn_best_forecast.csv` for predicted 30-minute call volume;
- synthetic average handle time assumptions from the operational sample, because public 311 records do not include talk time or after-call work;
- a 30-minute planning interval.

## Erlang C Calculation

For each interval, offered load is calculated as:

```text
traffic intensity = predicted calls * average handle time / interval seconds
```

The Erlang C formula estimates the probability that an arriving caller must wait. Service level is then estimated as the probability that a call is answered within the target answer time.

| Parameter | Value |
| --- | ---: |
| Planning interval | 30 minutes |
| Target service level | 80% |
| Target answer time | 20 seconds |
| Maximum occupancy | 85% |
| Shrinkage assumption | 30% |

The base required agent count is the smallest integer that satisfies both the service-level target and occupancy cap. The shrinkage-adjusted agent count increases the base count to account for non-phone time such as breaks, meetings, training, and absence.

## Latest Full-History Result

| Metric | Value |
| --- | ---: |
| Forecast intervals | 4,320 |
| Forecast period | 2025-10-03 to 2025-12-31 |
| Average predicted calls | 208.3222 |
| Peak predicted calls | 382.2330 |
| Average base required agents | 71.6819 |
| Peak base required agents | 135 |
| Average shrinkage-adjusted agents | 102.8662 |
| Peak shrinkage-adjusted agents | 193 |
| Average expected occupancy | 0.8352 |
| Average service-level probability | 0.9174 |

## Output

The generated staffing files are:

```text
data/processed/full_staffing_requirements.csv
docs/full_staffing_requirements_summary.json
```

## Limitations

- Forecast volume now comes from the full 2023-2025 history, but handle time remains a documented synthetic operational assumption.
- The shrinkage rate is a planning assumption, not an observed workforce metric.
- Erlang C assumes a simplified inbound queue and does not capture every real contact center behavior.
