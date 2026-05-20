# Synthetic Data Generation Methodology

## Purpose

The project uses public NYC 311 service request records as a realistic demand seed, then generates operational call center metadata that is not available in the public dataset.

This creates a dataset suitable for:

- SQL Server star schema modeling;
- call center KPI dashboards;
- 30-minute call volume forecasting;
- Erlang C staffing calculation;
- shift schedule optimization.

## Source Fields Preserved

The generated call-level dataset keeps the original source context:

- source request ID;
- source created datetime;
- complaint type;
- descriptor-derived service category;
- borough;
- incident ZIP;
- source status.

## Generated Fields

The generator creates:

- simulated call start datetime;
- answer datetime;
- end datetime;
- date and 30-minute interval keys;
- queue ID and queue name;
- service category;
- synthetic agent assignment;
- talk time;
- hold time;
- after-call work;
- handle time;
- abandonment flag;
- SLA met flag.

## Time Distribution

The source `created_date` is preserved as `source_created_datetime`. The simulated `call_start_datetime` keeps the same calendar date, but distributes calls across the day using a business-hour-heavy pattern.

Reasoning:

- Socrata API samples ordered by timestamp can overrepresent the earliest records in each day.
- Call center staffing requires a usable interval-level operational curve.
- Keeping the real source date preserves daily and weekday patterns, while the simulated intraday distribution creates a practical 30-minute call center workload for the MVP.

This limitation must be disclosed in the final methodology.

## Handle Time

Talk time is generated with a log-normal distribution because call durations are non-negative and right-skewed. Queue/service categories use different base durations:

| Service Category | Base Talk Time |
| --- | --- |
| housing | 420 sec |
| sanitation | 260 sec |
| transportation | 330 sec |
| public_safety | 300 sec |
| general | 360 sec |

After-call work is generated with a gamma distribution and added to talk time to calculate handle time.

## Hold Time And Abandonment

Hold time is generated with a log-normal distribution. Peak weekday business hours receive a higher base wait time than off-peak periods.

Abandonment probability increases as hold time increases. Abandoned calls have:

- no agent assignment;
- no talk time;
- no ACW;
- no handle time;
- `SLA_Met_Flag = 0`.

## SLA

The initial service-level target is 80 percent of calls answered within 20 seconds.

For each answered call:

- `SLA_Met_Flag = 1` when hold time is 20 seconds or less;
- `SLA_Met_Flag = 0` otherwise.

## Agent And Queue Simulation

The full SQL warehouse uses 160 synthetic agents distributed across five skill groups:

| Skill Group | Agent ID Range | Agent Count |
| --- | ---: | ---: |
| housing | 1-32 | 32 |
| sanitation | 33-59 | 27 |
| transportation | 60-86 | 27 |
| public_safety | 87-107 | 21 |
| general | 108-160 | 53 |

Queues are derived from every observed NYC 311 complaint type in the 2023-2025 extract. The current full warehouse contains 217 queues. Each queue is mapped to a normalized service category with keyword rules. The category is then used for service mix reporting, agent skill assignment, and dashboard filtering.

The January 2025 CSV sample remains as a small development fixture, but it is no longer the main analytical dataset.

## Reproducibility

The first CSV generator uses a fixed default random seed:

```text
20260511
```

Running the generator with the same input file and seed should produce the same synthetic output.

The full SQL warehouse uses deterministic pseudo-random values derived from each source request key. This means the full 10.3M-row synthetic warehouse can be rebuilt from the raw NYC 311 table without relying on a session-level random state.

## Latest Full Warehouse Summary

The current production-scale dataset is generated directly in SQL Server from the 2023-2025 raw table:

```text
sql/etl/004_load_full_synthetic_warehouse_from_raw.sql
```

Current full warehouse characteristics:

| Metric | Value |
| --- | ---: |
| Source period | 2023-01-01 to 2025-12-31 |
| Raw source rows | 10,336,480 |
| Fact calls | 10,336,480 |
| Dates | 1,096 |
| Time intervals | 48 |
| Queues | 217 |
| Agents | 160 |
| Answered calls | 9,527,782 |
| Abandoned calls | 808,698 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |
| SLA rate | 22.57% |

The latest SQL validation summary is stored in:

```text
docs/sql_validation_summary.md
```

## Development Fixture Summary

The latest generated summary is stored in:

```text
docs/sample_generation_summary.json
```

Current sample characteristics:

- source rows: 6,200;
- synthetic agents: 60;
- queues: 101;
- abandonment rate: 6.69 percent;
- average handle time for answered calls: 519.82 seconds;
- distinct 30-minute intervals: 1,325;
- maximum calls in one interval: 19.
