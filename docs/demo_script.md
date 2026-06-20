# Demonstration Script

## Purpose

This script turns the project into a clear capstone product demonstration. The goal is to show one coherent system: SQL Server warehouse, Streamlit dashboard, forecasting, Erlang C staffing, roster simulation, and compact public deployment.

## Prerequisites

- SQL Server database `CallCenterWFM` exists locally.
- Full synthetic warehouse load has already been executed.
- Generated planning artifacts exist under `data/processed/`.
- Python dependencies from `requirements.txt` are installed.
- Streamlit can be launched with `python -m streamlit`.

For the public portfolio demo:

- `wfm.vartsab.com` points to the VPS IP.
- Docker Compose is running Postgres, Streamlit, and Caddy on the VPS.
- The dashboard is available at `https://wfm.vartsab.com`.
- The demo opens without a password unless `WFM_DEMO_PASSWORD` is set in the private `deploy/env.local` file.

## Launch

Start the dashboard:

```powershell
.\scripts\run_dashboard.ps1
```

Open:

```text
http://localhost:8501/
```

Public demo URL:

```text
https://wfm.vartsab.com
```

If the January 2026 planning artifacts need to be rebuilt:

```powershell
.\scripts\run_planning_pipeline.ps1
```

## Demo Flow

### 1. Overview

Show that the dashboard reads the full SQL-backed synthetic warehouse.

Points to mention:

- source period is 2023-2025;
- fact table contains 10,336,480 simulated calls;
- KPIs include offered calls, answered calls, abandonment, and AHT.

### 2. Demand Analysis

Show the historical workload patterns and service category mix.

Points to mention:

- demand is seeded from real NYC 311 public-service records;
- operational call-center fields are synthetic and documented;
- the dashboard supports filtering by date and service category.

### 3. Demand Forecast

Show the model evaluation and future forecast.

Points to mention:

- the holdout period is used for model evaluation;
- histogram gradient boosting was selected by lowest MAE;
- the January 2026 planning forecast is generated after training on the full 2023-2025 history;
- US federal holiday features are included.

### 4. Capacity Planning

Show the Erlang C staffing curve.

Points to mention:

- machine learning predicts demand, but Erlang C converts demand and AHT into staffing;
- the target is 80% of calls answered within 20 seconds;
- shrinkage and occupancy constraints are included.

### 5. Roster Simulation

Show the future January 2026 roster.

Points to mention:

- the schedule is future-facing, not historical;
- the roster has 160 named synthetic agents;
- simplified roster constraints include one shift per day, max five shifts per week, and 11 hours minimum rest;
- the dashboard shows the difference between the approved 160-agent scenario and the estimated full-coverage roster.

### 6. Service Quality Metrics

Show the agent-level operational view.

Points to mention:

- agent metrics include handled calls and handle-time components;
- service level is intentionally not treated as an agent-level metric because queue wait occurs before an agent receives the call.

### 7. Methods & Assumptions

Show the validation and Methods & Assumptions tab.

Points to mention:

- SQL row counts reconcile;
- model outputs and staffing outputs are documented;
- assumptions and limitations are explicit.

### 8. Public Deployment

If showing the portfolio version, open `https://wfm.vartsab.com`.

Points to mention:

- the public deployment uses compact PostgreSQL seed tables generated from the validated SQL Server outputs;
- Caddy provides HTTPS on standard port `443`; the existing Xray/V2Ray service uses port `4443`;
- the deployment is documented in `deploy/README.md` and `docs/deployment_status.md`.

## Screenshot List

Capture these figures for the report:

1. Overview KPI view.
2. Demand Analysis volume chart.
3. Demand Forecast model comparison table.
4. January 2026 future forecast chart.
5. Capacity Planning requirement curve.
6. Roster Simulation coverage and shift mix view.
7. Daily roster table.
8. Service Quality Metrics view.
9. Methods & Assumptions / validation view.

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
| Streamlit product dashboard | 96% |
| Documentation evidence | 94% |
| Demo packaging | 96% |
| Portfolio deployment | 96% |
| Final report and presentation | 88% |

Overall technical product coverage: approximately 96%.

Overall capstone submission package coverage: approximately 95%.
