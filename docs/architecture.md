# Architecture

## System Flow

```text
Public 311 data
    -> full 2023-2025 raw extraction
    -> SQL Server raw landing table
    -> full synthetic call-center metadata generation
    -> dimensional warehouse tables
    -> dashboard/model SQL views
    -> Streamlit dashboard
    -> historical forecasting evaluation
    -> future planning forecast
    -> Erlang C staffing calculator
    -> roster simulation
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

Service level is treated as a queue, service-category, and staffing metric because queue wait is determined before a call reaches an individual agent.

### Forecasting

Forecast target: call count per 30-minute interval.

Candidate models:

- seasonal naive baseline;
- Ridge regression;
- Poisson regression;
- Random Forest;
- Gradient Boosting;
- Histogram Gradient Boosting.

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

Current planning constraints:

- January 2026 future planning horizon;
- 160-agent named roster;
- weekly shift-count optimization;
- agent-level roster assignment;
- coverage by 30-minute interval;
- 8-hour shifts with a 30-minute break;
- one shift per agent per day;
- maximum 5 shifts per agent per week;
- 11-hour minimum rest;
- optional skill group eligibility for future expansion.

Objective:

- minimize understaffing first;
- minimize overcoverage;
- minimize total scheduled shifts.

The approved 160-agent scenario is intentionally shown as a constrained planning case. The January 2026 staffing curve implies a much larger full-coverage roster estimate, so the dashboard reports both the simulated 160-agent roster and the remaining coverage gap.

### Productization Layer

The current product is a local analytical application:

- SQL Server stores the raw table, dimensional warehouse, and analytics views;
- Python scripts rebuild forecasting, staffing, and scheduling artifacts;
- Streamlit provides the demonstration interface.

An optional MLOps layer can be added with MLflow for experiment tracking and model artifacts. MLflow should support model evaluation and reproducibility, while Streamlit remains the user-facing product.

### Streamlit App

Tabs:

- Overview;
- Demand Analysis;
- Demand Forecast;
- Capacity Planning;
- Roster Simulation;
- Service Quality Metrics;
- Methods & Assumptions;
- Deployment Proposal.

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
