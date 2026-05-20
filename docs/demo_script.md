# Demonstration Script

## Purpose

This script turns the project into a clear capstone product demonstration. The goal is to show one coherent system: SQL Server warehouse, Streamlit dashboard, forecasting, Erlang C staffing, and legal roster optimization.

## Prerequisites

- SQL Server database `CallCenterWFM` exists locally.
- Full synthetic warehouse load has already been executed.
- Generated planning artifacts exist under `data/processed/`.
- Python dependencies from `requirements.txt` are installed.
- Streamlit can be launched with `python -m streamlit`.

## Launch

Start the dashboard:

```powershell
.\scripts\run_dashboard.ps1
```

Open:

```text
http://localhost:8501/
```

If the January 2026 planning artifacts need to be rebuilt:

```powershell
.\scripts\run_planning_pipeline.ps1
```

## Demo Flow

### 1. Executive Summary

Show that the dashboard reads the full SQL-backed synthetic warehouse.

Points to mention:

- source period is 2023-2025;
- fact table contains 10,336,480 simulated calls;
- KPIs include offered calls, answered calls, abandonment, and AHT.

### 2. Historical Trends

Show the historical workload patterns and service category mix.

Points to mention:

- demand is seeded from real NYC 311 public-service records;
- operational call-center fields are synthetic and documented;
- the dashboard supports filtering by date and service category.

### 3. Forecasting

Show the model evaluation and future forecast.

Points to mention:

- the holdout period is used for model evaluation;
- histogram gradient boosting was selected by lowest MAE;
- the January 2026 planning forecast is generated after training on the full 2023-2025 history;
- US federal holiday features are included.

### 4. Staffing

Show the Erlang C staffing curve.

Points to mention:

- machine learning predicts demand, but Erlang C converts demand and AHT into staffing;
- the target is 80% of calls answered within 20 seconds;
- shrinkage and occupancy constraints are included.

### 5. Scheduling

Show the future January 2026 roster.

Points to mention:

- the schedule is future-facing, not historical;
- the roster has 160 named synthetic agents;
- legal constraints include one shift per day, max five shifts per week, and 11 hours minimum rest;
- the dashboard shows the difference between the approved 160-agent scenario and the estimated full-coverage roster.

### 6. Agent Performance

Show the agent-level operational view.

Points to mention:

- agent metrics include handled calls and handle-time components;
- service level is intentionally not treated as an agent-level metric because queue wait occurs before an agent receives the call.

### 7. Methodology

Show the validation and methodology tab.

Points to mention:

- SQL row counts reconcile;
- model outputs and staffing outputs are documented;
- assumptions and limitations are explicit.

## Screenshot List

Capture these figures for the report:

1. Executive Summary KPI view.
2. Historical Trends volume chart.
3. Forecasting model comparison table.
4. January 2026 future forecast chart.
5. Staffing requirement curve.
6. Scheduling coverage and shift mix view.
7. Daily roster table.
8. Agent Performance view.
9. Methodology / validation view.

Suggested destination:

```text
docs/screenshots/
```

## Current Product Coverage

| Area | Current coverage |
| --- | ---: |
| Data acquisition | 95% |
| SQL warehouse and views | 90% |
| Synthetic operational enrichment | 90% |
| Forecasting and evaluation | 85% |
| Erlang C staffing | 90% |
| Schedule optimization | 75% |
| Streamlit product dashboard | 84% |
| Documentation evidence | 80% |
| Demo packaging | 85% |
| Final report and presentation | 55% |

Overall technical product coverage: approximately 86%.

Overall capstone submission package coverage: approximately 80%.
