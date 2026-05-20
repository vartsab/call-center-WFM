# Week 3-6 Reporting Evidence

This document preserves report-ready evidence for the next weekly progress reports. It is written as project documentation, not as final report text. It can be used to draft formal Word sections in the explanatory-note format.

## Week 3 - Full Data Acquisition And SQL Landing Layer

Recommended report theme: the project moved from the small January sample to a full-scale public-data foundation.

Completed work:

- downloaded the full NYC 311 public-service extract for 2023-01-01 through 2025-12-31;
- loaded 10,336,480 raw records into SQL Server;
- created the raw landing table `dbo.Raw_NYC_311_Service_Requests`;
- added raw-table indexes after the load;
- created raw analytical views for 30-minute volume, daily summary, and complaint-type summary;
- validated yearly row counts and 30-minute volume reconciliation.

Evidence:

- `src/data_acquisition/download_nyc_311_full.py`
- `src/data_acquisition/load_raw_nyc_311_pyodbc.py`
- `sql/raw/001_create_raw_nyc_311.sql`
- `sql/raw/003_create_raw_nyc_311_indexes.sql`
- `sql/raw/004_create_raw_nyc_311_views.sql`
- `docs/full_dataset_summary.json`
- `docs/sql_validation_summary.md`

Key metrics:

| Metric | Value |
| --- | ---: |
| Raw SQL records | 10,336,480 |
| Source period | 2023-01-01 to 2025-12-31 |
| Raw 30-minute view rows | 52,603 |
| Raw 30-minute view total requests | 10,336,480 |

Risks and limitations:

- NYC 311 service requests are public-service demand records, not guaranteed phone calls.
- Operational call-center attributes must therefore be simulated and documented as synthetic.

Next-step bridge:

- Use the full raw table as the seed for a full synthetic call-center warehouse.

## Week 4 - Full Synthetic Warehouse And Dashboard Foundation

Recommended report theme: the project became a SQL-backed analytical warehouse with dashboard-ready views.

Completed work:

- created the full synthetic warehouse load from the raw 311 table;
- populated `Fact_Calls` with one simulated call/contact per raw request;
- populated `Dim_Date`, `Dim_Time`, `Dim_Queue`, and `Dim_Agent`;
- mapped all observed complaint types to queues;
- generated deterministic operational metrics: hold time, talk time, after-call work, abandonment, SLA flag, and agent assignment;
- validated dashboard views against fact totals;
- updated Streamlit to read SQL Server views and present a 360-degree call-center view.

Evidence:

- `sql/etl/004_load_full_synthetic_warehouse_from_raw.sql`
- `sql/views/001_analytics_views.sql`
- `app/streamlit/app.py`
- `docs/sql_validation_summary.md`
- `docs/data_dictionary.md`

Key metrics:

| Object / Metric | Value |
| --- | ---: |
| `Dim_Date` | 1,096 |
| `Dim_Time` | 48 |
| `Dim_Queue` | 217 |
| `Dim_Agent` | 160 |
| `Fact_Calls` | 10,336,480 |
| `vw_Volume_30Min` rows | 2,230,984 |
| `vw_Forecasting_Input` rows | 252,790 |
| Offered calls | 10,336,480 |
| Answered calls | 9,527,782 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |

Risks and limitations:

- Synthetic operational distributions must be clearly described in the methodology.
- Queue and agent assignments are simulated for analytical realism and are not actual NYC staffing data.

Next-step bridge:

- Build full-history forecasting features from the SQL-derived 30-minute demand series.

## Week 5 - Forecasting And Staffing Science Pipeline

Recommended report theme: the project added predictive and queueing-theory components.

Completed work:

- built a complete 30-minute feature matrix for 2023-2025;
- added cyclical time features, weekend indicators, US federal holiday flags, holiday names, and distance-to-holiday features;
- evaluated a seasonal naive baseline on a 90-day holdout;
- compared scikit-learn forecasting models;
- selected histogram gradient boosting by lowest holdout MAE;
- retrained the selected model on the full 2023-2025 history;
- generated a January 2026 future planning forecast;
- converted forecasted calls and synthetic AHT into staffing requirements with Erlang C.

Evidence:

- `src/forecasting/build_feature_matrix.py`
- `src/forecasting/us_federal_holidays.py`
- `src/forecasting/baseline_forecast.py`
- `src/forecasting/sklearn_model_compare.py`
- `src/forecasting/future_feature_forecast.py`
- `src/workforce/erlang_c_staffing.py`
- `docs/forecasting_methodology.md`
- `docs/full_sklearn_model_comparison_summary.json`
- `docs/future_forecast_summary.json`
- `docs/future_staffing_requirements_summary.json`

Model evaluation:

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Histogram gradient boosting | 34.8872 | 49.7414 | 0.2216 |
| Random forest | 35.7124 | 50.8680 | 0.2254 |
| Gradient boosting | 38.2330 | 54.0725 | 0.2420 |
| Ridge regression | 42.0608 | 59.0505 | 0.2720 |
| Poisson regression | 47.9825 | 71.4876 | 0.3055 |

January 2026 staffing output:

| Metric | Value |
| --- | ---: |
| Forecast intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |
| Average shrinkage-adjusted agents | 103.0108 |
| Peak shrinkage-adjusted agents | 189 |
| Target service level | 80% answered within 20 sec |
| Max occupancy | 85% |
| Shrinkage | 30% |

Risks and limitations:

- MAPE can be unstable in very low-volume intervals.
- The future forecast uses recursive previous-week lag features after the first forecast week.

Next-step bridge:

- Use the staffing curve as input for a legal roster optimizer and demonstrate schedule feasibility.

## Week 6 - Scheduling, Productization, And Validation

Recommended report theme: the project became a demonstrable workforce management product.

Completed work:

- built a legal 160-agent roster optimizer with OR-Tools CP-SAT;
- enforced one shift per agent per day, a maximum of five shifts per week, and 11 hours minimum rest;
- generated a January 2026 future schedule only, not historical schedules;
- added named synthetic agents while keeping numeric agent IDs;
- redesigned the Scheduling tab around planning KPIs, coverage gap, daily shift mix, roster table, and timeline;
- added pytest configuration and validated the current test suite.

Evidence:

- `src/scheduling/agent_roster_optimizer.py`
- `src/scheduling/christie_names.py`
- `app/streamlit/app.py`
- `docs/scheduling_methodology.md`
- `docs/future_scheduling_summary.json`
- `tests/conftest.py`

Scheduling output:

| Metric | Value |
| --- | ---: |
| Planning horizon | 2026-01-01 to 2026-01-31 |
| Scheduled shifts | 3,427 |
| Agent pool size | 160 |
| Full-coverage roster estimate | 462 |
| Peak required agents | 189 |
| Peak scheduled agents | 160 |
| Coverage achieved | 33.54% |
| Daily shift violations | 0 |
| Weekly shift-limit violations | 0 |
| Rest violations | 0 |

Testing evidence:

| Test suite result | Value |
| --- | ---: |
| Tests collected | 10 |
| Tests passed | 10 |

Risks and limitations:

- The approved 160-person pool cannot fully cover the full 24/7 Erlang demand curve.
- Skill-based routing is not yet enforced in the optimizer.
- Product packaging still needs a final decision: simple local demo bundle, MLflow-backed model tracking, or Docker-style orchestration.

Next-step bridge:

- Choose the demonstration packaging approach and prepare final report figures/screenshots.
