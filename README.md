# Call Center Workforce Optimization

Master's capstone engineering project focused on call center analytics, demand forecasting, and workforce planning.

## Overview

This project develops an end-to-end analytical workflow for a city service contact center. It uses public 311 service request data as a realistic demand source and enriches it with documented synthetic operational fields needed for workforce management analysis.

The system is designed to support:

- call-level data preparation;
- dimensional modeling in Microsoft SQL Server;
- SQL views for operational analytics;
- 30-minute interval call volume forecasting;
- staffing requirement calculation;
- shift scheduling optimization;
- dashboard reporting.

## Current Scope

The current implementation includes:

- NYC 311 sample acquisition script;
- full 2023-2025 NYC 311 acquisition and raw SQL load scripts;
- synthetic call center data generation script;
- SQL-load-ready dimension and fact file builder;
- initial SQL Server warehouse schema;
- full raw SQL Server landing table for 10.3M public service records;
- full synthetic SQL Server warehouse load for 10.3M call-center records;
- SQL Server staging and load scripts;
- initial SQL analytics views;
- first 30-minute forecasting input builder;
- full-history seasonal naive baseline forecast;
- full-history feature model comparison with holiday and lag features;
- Erlang C staffing requirement calculator;
- OR-Tools shift scheduling optimizers;
- Streamlit dashboard MVP with SQL Server and CSV fallback data access;
- portfolio deployment path with Streamlit, PostgreSQL, Caddy, Docker Compose, and password protection;
- project documentation for dataset selection, data generation methodology, architecture, and data dictionary.

## Repository Structure

```text
app/streamlit/          Streamlit dashboard application
docs/                   project documentation
notebooks/              exploratory analysis notebooks
sql/schema/             SQL Server DDL scripts
sql/views/              SQL analytics views
sql/etl/                ETL/load scripts
src/data_acquisition/   source data extraction scripts
src/data_generation/    synthetic operational data generation
src/forecasting/        forecasting pipeline
src/workforce/          staffing calculation logic
src/scheduling/         schedule optimization logic
tests/                  tests
```

## Data Source

The seed dataset is NYC Open Data's 311 Service Requests from 2020 to Present, accessed through the public Socrata API.

The public dataset provides real service request timestamps, categories, agencies, boroughs, statuses, and location fields. Operational call center fields that are not available publicly, such as handle time, wait time, abandonment, SLA status, and agent assignment, are generated synthetically and documented in `docs/data_generation_methodology.md`.

The current full-history extract covers 2023-01-01 through 2025-12-31 and contains 10,336,480 records loaded into SQL Server. Raw and processed data files are generated locally and excluded from version control.

## Quick Start

Start the dashboard product demo:

```powershell
.\scripts\run_dashboard.ps1
```

Force the SQL-backed dashboard path when rehearsing SQL live:

```powershell
.\scripts\run_dashboard.ps1 -DataSource Sql
```

Check demo readiness without launching the dashboard:

```powershell
.\scripts\check_demo_readiness.ps1
.\scripts\check_demo_readiness.ps1 -RequireSql
```

Download a small January 2025 sample:

```powershell
python src\data_acquisition\download_nyc_311_sample.py --start-date 2025-01-01 --end-date 2025-01-31 --target-total 6200
```

Generate synthetic call center records:

```powershell
python src\data_generation\generate_synthetic_calls.py
```

Prepare SQL-load-ready files:

```powershell
python src\data_generation\prepare_sql_load_files.py
```

Build forecasting input and run the first baseline forecast:

```powershell
python src\forecasting\build_forecasting_input.py
python src\forecasting\build_feature_matrix.py
python src\forecasting\baseline_forecast.py
python src\forecasting\sklearn_model_compare.py
```

Calculate interval staffing requirements:

```powershell
python src\workforce\erlang_c_staffing.py
```

Generate the first optimized shift schedule:

```powershell
python src\scheduling\shift_optimizer.py
```

Load and validate the SQL Server sample:

```text
Run the scripts listed in sql/README.md, then run sql/validation/001_validate_loaded_sample.sql.
```

Run the dashboard:

```powershell
streamlit run app\streamlit\app.py
```

## Portfolio VPS Deployment

The public portfolio deployment uses a compact Postgres seed database instead of the local SQL Server warehouse. The current VPS shape is documented in `deploy/README.md`:

- DNS: `wfm.vartsab.com` points to the VPS public IP.
- Public URL: `https://wfm.vartsab.com:8443`.
- Port `443` remains available for the existing VPN.
- Docker Compose runs Postgres, Streamlit, and Caddy.

Build or refresh the deployment seed:

```powershell
python scripts\build_portfolio_seed.py
```

Deploy from the VPS project directory:

```bash
docker compose --env-file deploy/env.local up -d --build
```

View the generated summary:

```powershell
Get-Content docs\sample_generation_summary.json
Get-Content docs\baseline_forecast_summary.json
```

## Full-History Workflow

Download the full 2023-2025 public extract:

```powershell
python src\data_acquisition\download_nyc_311_full.py --start-date 2023-01-01 --end-date 2025-12-31
```

Create and load the SQL raw table:

```text
Run sql/raw/001_create_raw_nyc_311.sql, then:
```

```powershell
python src\data_acquisition\load_raw_nyc_311_pyodbc.py --truncate --batch-size 10000
```

After loading, create raw-table indexes:

```text
Run sql/raw/003_create_raw_nyc_311_indexes.sql.
```

Load the full synthetic warehouse:

```text
Run sql/etl/004_load_full_synthetic_warehouse_from_raw.sql.
```

Build the full historical model-evaluation artifacts:

```powershell
python src\forecasting\build_full_forecasting_input_from_sql.py
python src\forecasting\build_feature_matrix.py --input data\processed\full_forecasting_input.csv --output data\processed\full_forecast_features.csv
python src\forecasting\baseline_forecast.py --input data\processed\full_forecasting_input.csv --output data\processed\full_baseline_forecast.csv --summary-output docs\full_baseline_forecast_summary.json --test-days 90
python src\forecasting\sklearn_model_compare.py --input data\processed\full_forecast_features.csv --output data\processed\full_sklearn_best_forecast.csv --summary-output docs\full_sklearn_model_comparison_summary.json --test-days 90
```

Build the January 2026 planning artifacts:

```powershell
.\scripts\run_planning_pipeline.ps1
```

Demo and reporting notes:

- `docs/demo_script.md`
- `docs/deployment_status.md`
- `docs/repository_handoff.md`
- `docs/technology_choice.md`
- `docs/reporting_evidence_week3_6.md`
- `docs/productization_plan.md`

## Notes

Raw and processed data files are excluded from version control. The repository stores code, SQL scripts, and documentation needed to reproduce the pipeline.
