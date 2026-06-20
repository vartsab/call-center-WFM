# Data Dictionary

This is the initial target schema. Final column names may change after seed data selection and SQL implementation.

## Fact_Calls

Grain: one row per simulated inbound call/contact.

| Column | Type | Description |
| --- | --- | --- |
| Call_ID | bigint | Unique call identifier. |
| Source_Request_ID | varchar | Original public service request identifier, if available. |
| Date_ID | int | Foreign key to `Dim_Date`. |
| Time_ID | int | Foreign key to `Dim_Time`, usually 30-minute interval. |
| Agent_ID | int | Foreign key to `Dim_Agent`; null or special value for abandoned before assignment. |
| Queue_ID | int | Foreign key to `Dim_Queue`. |
| Call_Start_Datetime | datetime2 | Simulated call arrival timestamp. |
| Answer_Datetime | datetime2 | Simulated answer timestamp, if answered. |
| End_Datetime | datetime2 | Simulated call end timestamp. |
| Talk_Time_Sec | int | Simulated talk time. |
| Hold_Time_Sec | int | Simulated wait/hold time before answer. |
| ACW_Time_Sec | int | Simulated after-call work. |
| Handle_Time_Sec | int | Talk time plus ACW time. |
| Abandoned_Flag | bit | Whether caller abandoned before answer. |
| SLA_Met_Flag | bit | Whether the call met service-level target. |

## Dim_Date

| Column | Type | Description |
| --- | --- | --- |
| Date_ID | int | Date key, usually `YYYYMMDD`. |
| Calendar_Date | date | Calendar date. |
| Day_Of_Week | varchar | Day name. |
| Week_Of_Year | int | Week number. |
| Month | int | Month number. |
| Month_Name | varchar | Month name. |
| Quarter | int | Calendar quarter. |
| Year | int | Calendar year. |
| Is_Weekend | bit | Weekend flag. |
| Is_Holiday | bit | Holiday flag, if available. |

## Dim_Time

| Column | Type | Description |
| --- | --- | --- |
| Time_ID | int | Time key, for example `HHMM`. |
| Interval_Start_Time | time | Start of the 30-minute interval. |
| Interval_End_Time | time | End of the 30-minute interval. |
| Hour | int | Hour of day. |
| Half_Hour_Index | int | Index from 0 to 47. |
| Shift_Band | varchar | Morning, midday, evening, overnight, or similar. |

## Dim_Agent

| Column | Type | Description |
| --- | --- | --- |
| Agent_ID | int | Unique synthetic agent identifier. |
| Agent_Name | varchar | Synthetic name or anonymized label. |
| Skill_Group | varchar | Queue/skill group assignment. |
| Hire_Date | date | Synthetic hire date. |
| Tenure_Band | varchar | Synthetic tenure group. |
| Employment_Type | varchar | Full-time, part-time, contractor, etc. |
| Active_Flag | bit | Agent active status. |

## Dim_Queue

| Column | Type | Description |
| --- | --- | --- |
| Queue_ID | int | Unique queue identifier. |
| Queue_Name | varchar | Queue or service category. |
| Service_Category | varchar | Higher-level service grouping. |
| SLA_Target_Sec | int | Target answer time, such as 20 seconds. |
| Target_Service_Level | decimal | Target percentage answered within SLA. |

## Modeling Notes

- Synthetic fields must be reproducible with a random seed.
- Talk time should use a right-skewed distribution such as log-normal or gamma.
- Abandonment probability should increase as wait time increases.
- Agent assignment should respect queue/skill groups when implemented.
- Service level should be analyzed at queue, service-category, interval, and staffing levels because the queue wait occurs before agent assignment.
- All synthetic assumptions must be documented in `docs/decision_log.md` or a dedicated methodology note.

## Seed Dataset Fields

Initial seed dataset: NYC 311 Service Requests from 2020 to Present.

| Source Field | Target Use |
| --- | --- |
| `unique_key` | `Fact_Calls.Source_Request_ID` |
| `created_date` | `Source_Created_Datetime` and `Call_Start_Datetime` seed |
| `closed_date` | Optional future service-resolution analysis |
| `agency` | Optional future agency dimension |
| `agency_name` | Optional future agency dimension |
| `complaint_type` | `Dim_Queue.Queue_Name` seed |
| `descriptor` | Queue classification helper |
| `location_type` | Optional service context |
| `incident_zip` | `Fact_Calls.Incident_Zip` |
| `incident_address` | Not planned for fact table; avoid unnecessary address exposure in dashboards |
| `city` | Optional location dimension |
| `status` | `Fact_Calls.Source_Status` |
| `borough` | `Fact_Calls.Borough` |
| `latitude` | Optional future map view |
| `longitude` | Optional future map view |

## Generated Sample Outputs

The project keeps raw and processed CSV outputs local. The code and committed summary files document how to reproduce them.

| Output | Description |
| --- | --- |
| `data/raw/nyc_311_sample.csv` | Downloaded public 311 seed sample. |
| `data/raw/nyc_311_full/*.csv` | Full 2023-2025 NYC 311 raw extract chunks. |
| `data/raw/nyc_311_sample_metadata.json` | Query metadata for reproducibility. |
| `data/processed/synthetic_calls_sample.csv` | Simulated call-level fact source. |
| `data/processed/dim_agents_sample.csv` | Synthetic agent dimension source. |
| `data/processed/dim_queues_sample.csv` | Queue dimension source derived from complaint types. |
| `docs/sample_generation_summary.json` | Committed summary metrics from the latest generated sample. |
| `data/processed/sql_load/*.csv` | SQL-load-ready dimension and fact files. |
| `data/processed/forecasting_input_sample.csv` | 30-minute forecasting input by normalized queue service category. |
| `data/processed/forecast_features_sample.csv` | Holiday-aware feature matrix for interval forecasting. |
| `data/processed/baseline_forecast_sample.csv` | First baseline forecast output for the holdout period. |
| `docs/baseline_forecast_summary.json` | Committed metrics from the latest baseline forecast run. |
| `data/processed/sklearn_best_forecast_sample.csv` | Best forecast from the scikit-learn model comparison. |
| `docs/sklearn_model_comparison_summary.json` | Committed comparison metrics for feature-based forecasting models. |
| `data/processed/staffing_requirements_sample.csv` | Erlang C staffing requirements by 30-minute interval. |
| `docs/staffing_requirements_summary.json` | Committed staffing summary from the latest Erlang C run. |
| `data/processed/optimized_schedule_sample.csv` | Optimized agent shift assignments for the sample staffing horizon. |
| `data/processed/schedule_coverage_sample.csv` | Interval-level scheduled coverage versus required staffing. |
| `docs/scheduling_summary.json` | Committed summary from the latest scheduling optimization run. |
| `data/processed/full_forecasting_input.csv` | Full-history SQL-derived 30-minute demand input. |
| `data/processed/full_forecast_features.csv` | Full-history holiday-aware forecasting feature matrix. |
| `data/processed/full_sklearn_best_forecast.csv` | Selected full-history model forecast for the holdout period. |
| `docs/full_sklearn_model_comparison_summary.json` | Full-history model comparison metrics. |
| `data/processed/full_staffing_requirements.csv` | Full-history Erlang C staffing requirements. |
| `docs/full_staffing_requirements_summary.json` | Full-history staffing summary. |
| `data/processed/full_optimized_schedule.csv` | Full-history optimized shift assignments. |
| `data/processed/full_schedule_coverage.csv` | Full-history scheduled coverage versus required staffing. |
| `docs/full_scheduling_summary.json` | Full-history scheduling summary. |
| `data/processed/full_operational_forecasting_input.csv` | Full synthetic SQL view export with interval volume and average handle time for staffing. |
| `data/processed/future_forecast_features.csv` | January 2026 future feature matrix. |
| `data/processed/future_sklearn_forecast.csv` | January 2026 selected-model call-volume forecast. |
| `docs/future_forecast_summary.json` | January 2026 future forecast summary. |
| `data/processed/future_staffing_requirements.csv` | January 2026 Erlang C staffing requirements. |
| `docs/future_staffing_requirements_summary.json` | January 2026 staffing summary. |
| `data/processed/future_optimized_schedule.csv` | January 2026 simulated roster schedule for the 160-agent planning scenario. |
| `data/processed/future_schedule_coverage.csv` | January 2026 scheduled coverage versus required staffing. |
| `docs/future_scheduling_summary.json` | January 2026 scheduling summary. |

## Latest Full Warehouse Summary

The main analytical dataset is the SQL Server warehouse generated from the full 2023-2025 NYC 311 raw table.

| Metric | Value |
| --- | ---: |
| Source period | 2023-01-01 to 2025-12-31 |
| Raw source rows | 10,336,480 |
| Fact calls | 10,336,480 |
| Dates | 1,096 |
| Time intervals | 48 |
| Queues | 217 |
| Agents | 160 |
| Answered calls | 9,527,782 |
| Abandoned calls | 808,698 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |
| SLA rate | 22.57% |

## Development Fixture Summary

The January 2025 generated sample remains as a small local development fixture for fast testing and CSV fallback mode. It is not the main forecasting or staffing dataset.

| Metric | Value |
| --- | ---: |
| Source rows | 6,200 |
| Synthetic agents | 60 |
| Queues | 101 |
| Abandonment rate | 0.0669 |
| Average handle time, answered calls | 519.82 sec |
| Distinct 30-minute intervals | 1,325 |
| Maximum calls in one interval | 19 |

## Latest Baseline Forecast Summary

The full-history seasonal naive baseline uses the mean call volume by weekday and 30-minute interval from the training period.

| Metric | Value |
| --- | ---: |
| Training period | 2023-01-01 to 2025-10-02 |
| Test period | 2025-10-03 to 2025-12-31 |
| Test intervals | 4,320 |
| MAE | 41.1254 |
| RMSE | 57.3621 |
| MAPE | 0.2356 |

## Latest Feature Forecast Summary

The full-history feature-based comparison uses calendar, previous-week lag, and US federal holiday features. The selected model is the model with the lowest holdout MAE.

| Metric | Value |
| --- | ---: |
| Selected model | hist_gradient_boosting |
| Feature count | 11 |
| Test intervals | 4,320 |
| MAE | 34.8872 |
| RMSE | 49.7414 |
| MAPE | 0.2216 |

## Latest Staffing Summary

The latest staffing calculation uses the January 2026 future forecast, Erlang C, an 80/20 service target, a maximum occupancy of 85 percent, and a 30 percent shrinkage assumption.

| Metric | Value |
| --- | ---: |
| Staffing intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |
| Average base required agents | 71.7836 |
| Peak base required agents | 132 |
| Average shrinkage-adjusted agents | 103.0108 |
| Peak shrinkage-adjusted agents | 189 |

## Latest Scheduling Summary

The latest schedule uses OR-Tools CP-SAT with 8-hour shifts, a 30-minute break after 4 hours, hourly shift starts, a 160-agent pool, one shift per agent per day, a maximum of 5 shifts per agent per week, and an 11-hour minimum rest rule.

| Metric | Value |
| --- | ---: |
| Solver status | FEASIBLE |
| Scheduled shifts | 3,427 |
| Agent pool size | 160 |
| Full-coverage roster estimate | 462 |
| Coverage intervals | 1,488 |
| Understaffed agent-intervals | 101,875 |
| Overstaffed agent-intervals | 0 |
| Intervals with understaffing | 1,395 |
| Peak required agents | 189 |
| Peak scheduled agents | 160 |
| Coverage achieved | 33.54% |
