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

The first synthetic sample uses 60 agents distributed across five skill groups:

- housing;
- sanitation;
- transportation;
- public_safety;
- general.

Queues are derived from 311 complaint types. A simple keyword classifier maps complaint type and descriptor text to the service category/skill group.

## Reproducibility

The generator uses a fixed default random seed:

```text
20260511
```

Running the generator with the same input file and seed should produce the same synthetic output.

## Latest Sample Summary

The latest generated summary is stored in:

```text
docs/sample_generation_summary.json
```

Current sample characteristics:

- source rows: 6,200;
- synthetic agents: 60;
- queues: 101;
- abandonment rate: 6.61 percent;
- average handle time for answered calls: 517.57 seconds;
- distinct 30-minute intervals: 1,321;
- maximum calls in one interval: 17.

