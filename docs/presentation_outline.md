# Final Presentation Outline

## Slide 1 - Title

Call Center Analytics and Workforce Optimization for City Service Operations

Include:

- student name;
- program;
- supervisor;
- date.

## Slide 2 - Problem And Motivation

Key message: contact centers need interval-level planning because demand changes by time, day, season, and service category.

Mention:

- variable workload;
- service-level targets;
- staffing cost;
- risk of understaffing and overstaffing.

## Slide 3 - Project Goal

Goal: build an end-to-end analytical product that converts public service demand data into operational workforce planning decisions.

Main functions:

- SQL warehouse;
- dashboard analytics;
- 30-minute demand forecasting;
- Erlang C staffing;
- legal shift scheduling.

## Slide 4 - Data Source And Synthetic Enrichment

Explain:

- NYC 311 public-service records for 2023-2025;
- 10,336,480 source records;
- public data provides real demand pattern;
- operational call-center fields are simulated and documented.

Suggested figure:

- screenshot or table from `docs/sql_validation_summary.md`.

## Slide 5 - Architecture

Show pipeline:

Public 311 data -> SQL raw table -> synthetic warehouse -> SQL views -> Streamlit dashboard -> forecasting -> Erlang C -> schedule optimizer.

Suggested source:

- `docs/architecture.md`.

## Slide 6 - SQL Server Warehouse

Mention:

- `Fact_Calls`;
- `Dim_Date`;
- `Dim_Time`;
- `Dim_Queue`;
- `Dim_Agent`;
- analytics views.

Key validation:

- `Fact_Calls`: 10,336,480;
- `Dim_Queue`: 217;
- `Dim_Agent`: 160.

## Slide 7 - Dashboard Overview

Use screenshot:

- `docs/screenshots/01_executive_summary.png`

Explain:

- SQL-backed KPIs;
- service category filtering;
- date filtering;
- operational summary.

## Slide 8 - Forecasting

Use screenshot:

- `docs/screenshots/03_forecasting.png`

Mention:

- full-history 90-day holdout;
- holiday-aware features;
- model comparison;
- selected model: histogram gradient boosting.

Key result:

- MAE 34.8872;
- RMSE 49.7414;
- MAPE 0.2216.

## Slide 9 - Model-Aware Planning

Mention:

- forecasting models are registered rather than hardcoded;
- supported current models: histogram gradient boosting, random forest, gradient boosting, ridge, Poisson;
- dashboard can compare holdout predictions and future scenarios;
- planning pipeline supports `-Model`.

## Slide 10 - Staffing With Erlang C

Use screenshot:

- `docs/screenshots/04_staffing_requirements.png`

Explain:

- forecast predicts calls;
- Erlang C converts forecast and AHT into required agents;
- target: 80% answered within 20 seconds;
- shrinkage: 30%;
- max occupancy: 85%.

## Slide 11 - Schedule Optimization

Use screenshot:

- `docs/screenshots/05_scheduling_coverage.png`

Explain:

- OR-Tools CP-SAT optimizer;
- 160-agent legal roster;
- one shift per day;
- max five shifts per week;
- 11-hour minimum rest;
- future planning horizon: January 2026.

Key planning insight:

- 160-agent pool is legal but insufficient for full 24/7 coverage;
- estimated full-coverage roster: 462 agents.

## Slide 12 - Validation And Tests

Mention:

- SQL reconciliation;
- model metrics;
- schedule constraint validation;
- public deployment smoke test;
- test suite result: 13 passed.

Suggested screenshot:

- `docs/screenshots/07_methodology_validation.png`

## Slide 13 - Engineering Positioning

Mention:

- similar WFM systems exist commercially;
- the project is still engineering work because it creates a working, inspectable product;
- novelty is in transparency, reproducibility, open-data foundation, and model-aware planning.

## Slide 14 - Limitations

Mention:

- 311 records are public-service demand records, not guaranteed phone calls;
- operational metrics are synthetic;
- skill-based routing is not yet enforced in scheduling;
- public deployment uses compact Postgres seed tables, not the full SQL Server warehouse.

## Slide 15 - Future Work

Possible improvements:

- add skill-based scheduling;
- add scenario controls in Streamlit;
- add MLflow model tracking;
- add monitoring, backups, and managed database deployment if the demo becomes long-running;
- improve schedule optimizer for multi-skill coverage.

## Slide 16 - Conclusion

Closing message:

The project demonstrates a complete data science and engineering workflow from public demand data to actionable workforce planning: warehouse, dashboard, forecasting, staffing, and schedule optimization.
