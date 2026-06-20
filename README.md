# Call Center Workforce Management Analytics Prototype

Master's engineering capstone that connects demand analysis, machine-learning
forecasting, Erlang C staffing, roster simulation, and an interactive review
dashboard.

- Public demo: [wfm.vartsab.com](https://wfm.vartsab.com)
- Source data: NYC 311 Service Requests, 2023-2025
- Historical records: 10,336,480
- Planning grain: 30 minutes

## What The Project Does

```text
NYC 311 demand
  -> SQL Server raw and dimensional layers
  -> interval feature engineering
  -> chronological model comparison
  -> January 2026 demand forecast
  -> Erlang C staffing requirements
  -> OR-Tools roster simulation
  -> Streamlit dashboard
```

The local engineering workflow uses Microsoft SQL Server for the full
10.34-million-row warehouse. The public deployment uses compact PostgreSQL
tables generated from the validated analytical outputs.

## Data Boundaries

| Layer | Status | Content |
| --- | --- | --- |
| Historical demand | Real | NYC 311 timestamps, complaint types, agencies, boroughs, and volumes |
| Operating metadata | Synthetic | AHT, abandonment, SLA fields, agents, and shift records |
| Future demand | Forecasted | Model output for 30-minute planning intervals |
| Staffing and roster | Simulated | Erlang C requirements, assignments, and coverage outcomes |

These boundaries are shown in the dashboard and documented in
[`docs/data_generation_methodology.md`](docs/data_generation_methodology.md).

## Forecasting Results

The final 90 days of 2025 form a chronological holdout of 4,320 intervals.

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Histogram Gradient Boosting | 34.8872 | 49.7414 | 22.16% |
| Random Forest | 35.7124 | 50.8680 | 22.54% |
| Gradient Boosting | 38.2330 | 54.0725 | 24.20% |
| Ridge | 42.0608 | 59.0505 | 27.20% |
| Poisson | 47.9825 | 71.4876 | 30.55% |

Histogram Gradient Boosting supplies the January 2026 planning forecast.
Model definitions remain replaceable through the registry in
[`src/forecasting/sklearn_model_compare.py`](src/forecasting/sklearn_model_compare.py).

## Staffing And Roster Results

| Metric | Value |
| --- | ---: |
| Future planning intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |
| Peak base staffing | 132 |
| Peak staffing after shrinkage | 189 |
| Simulated roster | 160 agents |
| Assigned shifts | 3,427 |
| Estimated full-coverage roster | 462 agents |
| Daily, weekly, and rest-rule violations | 0 |

The 160-agent case is a constrained scenario. It exposes the difference
between a feasible roster and full coverage of the modeled 24/7 requirement.

## Technology

- Python, pandas, NumPy
- scikit-learn
- Microsoft SQL Server and T-SQL
- PostgreSQL
- OR-Tools CP-SAT
- Streamlit and Plotly
- Docker Compose and Caddy
- pytest

## Repository Layout

```text
app/streamlit/          dashboard application
deploy/                 PostgreSQL, Caddy, and Docker deployment
docs/                   technical methods, results, and screenshots
scripts/                reproducible run and readiness scripts
sql/                    SQL Server schema, ETL, views, and validation
src/data_acquisition/   NYC 311 extraction and raw loading
src/data_generation/    synthetic operational layer
src/forecasting/        feature engineering, training, and forecasting
src/workforce/          Erlang C staffing
src/scheduling/         CP-SAT roster simulation
tests/                  automated tests
```

## Quick Start

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the dashboard with locally generated CSV evidence:

```powershell
$env:CALLCENTER_DASHBOARD_SOURCE = "csv"
.\.venv\Scripts\python.exe -m streamlit run app\streamlit\app.py
```

Use the SQL Server path:

```powershell
.\scripts\run_dashboard.ps1 -DataSource Sql
```

Run the automated checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\check_demo_readiness.ps1
```

## Rebuild The Planning Pipeline

The local workflow expects the full historical feature matrix in
`data/processed/`. Raw and processed extracts remain outside version control.

```powershell
.\scripts\run_planning_pipeline.ps1
```

The script regenerates the future forecast, staffing requirements, roster,
coverage output, and summary files.

## Public Deployment

The portfolio runtime is deliberately compact:

```text
Browser
  -> Caddy on ports 80/443
  -> Streamlit
  -> PostgreSQL seed tables
```

Create the private environment file from `deploy/env.example`, then run:

```bash
docker compose --env-file deploy/env.local up -d --build
```

Deployment details are in [`deploy/README.md`](deploy/README.md).

## Technical Documentation

- [Architecture](docs/architecture.md)
- [Dataset source](docs/dataset_source.md)
- [Data dictionary](docs/data_dictionary.md)
- [Synthetic data methodology](docs/data_generation_methodology.md)
- [Forecasting methodology](docs/forecasting_methodology.md)
- [Model registry](docs/model_registry.md)
- [Staffing methodology](docs/staffing_methodology.md)
- [Scheduling methodology](docs/scheduling_methodology.md)
- [SQL validation](docs/sql_validation_summary.md)
- [Deployment status](docs/deployment_status.md)

The repository excludes raw data, local database files, credentials, academic
document drafts, rehearsal material, and generated office files.
