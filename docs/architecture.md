# Architecture

## System Flow

```text
Public 311 data
    -> full 2023-2025 raw extraction
    -> SQL Server raw landing table
    -> 30-minute forecasting aggregate
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

- Seed data: public city service records from NYC 311.
- Full forecasting history: 10,336,480 raw service requests from 2023-01-01 through 2025-12-31 loaded into SQL Server.
- Generated fields: call start time, answer time, talk time, after-call work, hold time, abandonment flag, agent assignment, queue, SLA status.
- Grain: one row per simulated call/contact.

### Database Layer

Target platform: Microsoft SQL Server Express or Developer edition.

Raw landing table:

- `Raw_NYC_311_Service_Requests`

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

- `vw_Volume_30Min` for interval, queue, and service-category volume and SLA metrics;
- `vw_Agent_Performance` for handled-call volume and handle-time components;
- `vw_Forecasting_Input` for 30-minute modeling input.

Full raw-history views:

- `vw_Raw_NYC_311_Volume_30Min` for 30-minute demand from the 10.3M-row raw table;
- `vw_Raw_NYC_311_Daily_Summary` for daily public-service demand;
- `vw_Raw_NYC_311_Complaint_Type_Summary` for source complaint mix.

Service level is treated as a queue, service-category, and staffing metric rather than an agent-level performance metric because an individual agent does not control the queue wait before the call is routed.

### Forecasting

Forecast target: call count per 30-minute interval.

Candidate models:

- seasonal naive baseline;
- Prophet;
- XGBoost with lag and calendar features;
- optional SARIMA or LSTM only if time allows.

Current baseline:

- seasonal naive mean by weekday and half-hour interval;
- train period: 2023-01-01 to 2025-10-02;
- test period: 2025-10-03 to 2025-12-31;
- latest full-history metrics are stored in `docs/full_baseline_forecast_summary.json`.

Current selected feature model:

- histogram gradient boosting;
- selected by lowest holdout MAE on the full-history 90-day test period;
- latest metrics are stored in `docs/full_sklearn_model_comparison_summary.json`.

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

Current full-history constraints:

- shift templates;
- horizon-wide shift-template counts;
- coverage by 30-minute interval;
- 8-hour shifts with a 30-minute break;
- optional skill group eligibility.

Objective:

- enforce zero undercoverage in the default full-history schedule;
- minimize overcoverage;
- minimize total scheduled shifts.

### Streamlit App

Tabs:

- Executive Summary;
- Historical Trends;
- Forecasting;
- Staffing;
- Scheduling;
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
