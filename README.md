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
- synthetic call center data generation script;
- initial SQL Server warehouse schema;
- initial SQL analytics views;
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

The first seed dataset is NYC Open Data's 311 Service Requests from 2020 to Present, accessed through the public Socrata API.

The public dataset provides real service request timestamps, categories, agencies, boroughs, statuses, and location fields. Operational call center fields that are not available publicly, such as handle time, wait time, abandonment, SLA status, and agent assignment, are generated synthetically and documented in `docs/data_generation_methodology.md`.

## Quick Start

Download a small January 2025 sample:

```powershell
python src\data_acquisition\download_nyc_311_sample.py --start-date 2025-01-01 --end-date 2025-01-31 --daily-limit 200 --limit 6200
```

Generate synthetic call center records:

```powershell
python src\data_generation\generate_synthetic_calls.py
```

View the generated summary:

```powershell
Get-Content docs\sample_generation_summary.json
```

## Notes

Raw and processed data files are excluded from version control. The repository stores code, SQL scripts, and documentation needed to reproduce the sample pipeline.
