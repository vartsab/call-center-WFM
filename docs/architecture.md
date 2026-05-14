# Architecture

## System Flow

```text
Public 311 data
    -> acquisition and cleaning
    -> synthetic call center metadata generation
    -> SQL Server staging tables
    -> dimensional warehouse tables
    -> dashboard/model SQL views
    -> Streamlit dashboard
    -> forecasting pipeline
    -> Erlang C staffing calculator
    -> MILP schedule optimizer
    -> schedule visualization
```

## Main Components

### Data Layer

- Seed data: public city service records.
- Generated fields: call start time, answer time, talk time, after-call work, hold time, abandonment flag, agent assignment, queue, SLA status.
- Grain: one row per simulated call/contact.

### Database Layer

Target platform: Microsoft SQL Server Express or Developer edition.

Initial star schema:

- `Fact_Calls`
- `Dim_Date`
- `Dim_Time`
- `Dim_Agent`
- `Dim_Queue`
- optional `Dim_Location`
- optional `Dim_Service_Request_Type`

### Analytics Views

Initial views:

- `vw_Volume_30Min`
- `vw_Agent_Performance`
- `vw_Service_Level`
- `vw_Queue_Performance`
- `vw_Forecasting_Input`

### Forecasting

Forecast target: call count per 30-minute interval.

Candidate models:

- seasonal naive baseline;
- Prophet;
- XGBoost with lag and calendar features;
- optional SARIMA or LSTM only if time allows.

Current baseline:

- seasonal naive mean by weekday and half-hour interval;
- train period: 2025-01-01 to 2025-01-24;
- test period: 2025-01-25 to 2025-01-31;
- latest metrics are stored in `docs/baseline_forecast_summary.json`.

Evaluation metrics:

- MAE;
- RMSE;
- MAPE or sMAPE, with caution for low-volume intervals.

### Staffing

Use Erlang C to convert forecasted call volume and AHT into required agents per 30-minute interval.

Inputs:

- forecasted calls;
- AHT;
- target SLA, such as 80 percent answered within 20 seconds;
- interval length;
- occupancy cap;
- shrinkage factor.

### Scheduling

Use a mixed integer linear programming model with OR-Tools.

Initial constraints:

- shift templates;
- max one shift per agent per day;
- coverage by 30-minute interval;
- optional lunch and break rules;
- optional skill group eligibility.

Objective:

- minimize undercoverage with a high penalty;
- minimize overcoverage with a lower penalty;
- optionally minimize total scheduled hours.

### Streamlit App

Tabs:

- Executive Summary;
- Historical Trends;
- Forecasting;
- Agent Performance;
- Methodology.

The current dashboard reads from SQL Server views when available and uses generated CSV files as a fallback for local demos.

## Repository Layout

```text
app/streamlit/          Streamlit application
data/raw/               raw downloaded data, not committed
data/processed/         generated and cleaned data, not committed
data/external/          external reference files, not committed
docs/                   project documentation
notebooks/              exploratory notebooks
sql/schema/             DDL scripts
sql/views/              SQL view definitions
sql/etl/                staging and load scripts
src/data_acquisition/   download and seed-data extraction
src/data_generation/    synthetic call event generation
src/forecasting/        model training and inference
src/workforce/          staffing calculation logic
src/scheduling/         optimization models
tests/                  unit and integration tests
```
