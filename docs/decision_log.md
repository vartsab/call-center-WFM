# Decision Log

This file records important project choices. Keep entries short and dated.

## 2026-05-11 - Treat the capstone as an engineering project

Status: accepted pending supervisor feedback.

Reasoning: the project creates a working analytical product with data pipelines, SQL Server database design, forecasting, staffing, optimization, and a Streamlit UI.

## 2026-05-11 - Use a hybrid data strategy

Status: accepted pending dataset validation.

Decision: use real public 311 data as the demand seed and generate missing call center operational metadata synthetically.

Reasoning: public 311 data gives realistic seasonality and service patterns, while operational fields such as talk time, ACW, hold time, agent assignment, SLA status, and abandonment are usually unavailable in public datasets.

## 2026-05-11 - Model analytics data as a star schema

Status: accepted.

Decision: create a call fact table and conformed dimensions for date, time, agent, queue, and service/request attributes.

Reasoning: star schema design makes SQL Server queries simpler, dashboard-ready, and easier to explain in the thesis methodology.

## 2026-05-11 - Use 30-minute intervals as the operational grain

Status: accepted.

Reasoning: 30-minute intervals are standard in workforce management and align forecasting, Erlang C staffing, and scheduling.

## 2026-05-11 - Separate forecasting from staffing

Status: accepted.

Decision: use ML/time-series models to forecast volume, then use Erlang C for required staffing.

Reasoning: staffing is a queueing-theory calculation, not a direct ML prediction problem.

## 2026-05-11 - Use MILP for scheduling

Status: accepted.

Decision: use OR-Tools for the first scheduling implementation.

Reasoning: shift scheduling is a constrained optimization problem; MILP gives transparent constraints and an explainable objective function.

## 2026-05-11 - Use Streamlit for the MVP application

Status: accepted.

Reasoning: Streamlit is fast for data applications, supports Plotly charts, and is appropriate for a capstone MVP.

## 2026-05-11 - Select NYC 311 Service Requests as the first seed dataset

Status: accepted for MVP.

Decision: use the NYC Open Data 311 Service Requests from 2020 to Present dataset through the public Socrata CSV API endpoint `https://data.cityofnewyork.us/resource/erm2-nwe9.csv`.

Reasoning: the dataset provides real city-service request timestamps, categories, agencies, statuses, boroughs, and optional geospatial fields. It is appropriate as a demand seed for a simulated city service contact center.

Limitations: a 311 service request is not guaranteed to be a phone call, and operational call center fields are not public. The project must state that it is a realistic operational simulation seeded by real public demand data.

## 2026-05-11 - Use standard-library Python for the first data scripts

Status: accepted for MVP.

Decision: implement the first acquisition and generation scripts using Python standard-library modules.

Reasoning: the current machine has Python available but does not yet have pandas or numpy installed. Standard-library scripts keep the first data pipeline runnable before dependency setup.

## 2026-05-11 - Preserve source dates but simulate call start time within day

Status: accepted for MVP.

Decision: keep the original 311 `created_date` as `Source_Created_Datetime`, but generate `Call_Start_Datetime` within the same calendar date using a business-hour-heavy distribution.

Reasoning: the public API sample can be front-loaded when records are ordered by creation timestamp. Workforce management analysis needs a usable 30-minute operational workload curve. This approach keeps the real daily/service mix while creating an interval-level call center simulation.

Limitation: this is a synthetic intraday distribution, so the final report must not claim that it represents actual NYC 311 call arrival times.

## 2026-05-14 - Add SQL-load-ready files before SQL Server execution

Status: accepted for MVP.

Decision: generate SQL-load-ready CSV files for `Dim_Date`, `Dim_Time`, `Dim_Agent`, `Dim_Queue`, and `Fact_Calls` before running SQL Server bulk load scripts.

Reasoning: separating CSV preparation from SQL Server loading makes the pipeline easier to inspect, test, and reproduce. It also allows progress on forecasting and dashboard preparation even before SQL Server is configured locally.

## 2026-05-14 - Use a seasonal naive baseline before advanced forecasting

Status: accepted.

Decision: implement the first forecast as a seasonal naive mean by weekday and 30-minute interval.

Reasoning: a baseline model is necessary for evaluating later Prophet, XGBoost, or other time-series models. It also provides a quick, explainable first forecasting artifact for the capstone.

## 2026-05-14 - Use proportional daily sampling for the MVP dataset

Status: accepted.

Decision: allocate the 6,200-record January 2025 seed sample across days in proportion to real NYC 311 daily request counts.

Reasoning: a fixed daily cap created an artificial flat daily volume pattern in the dashboard. Proportional daily sampling keeps the sample small while preserving a more realistic day-to-day demand curve.

## 2026-05-14 - Fill missing forecast intervals with zero call volume

Status: accepted.

Decision: evaluate and export the baseline forecast on the full 30-minute calendar grid for the holdout period.

Reasoning: staffing and scheduling require every planning interval, including intervals where no calls occurred. Leaving those intervals out would create gaps in the workforce requirement curve.

## 2026-05-14 - Use OR-Tools CP-SAT for the first schedule optimizer

Status: accepted.

Decision: build the first schedule optimizer with OR-Tools CP-SAT using binary agent-shift assignment variables.

Reasoning: shift scheduling is a constrained optimization problem. CP-SAT gives a transparent model for coverage, breaks, per-agent shift limits, understaffing, and overstaffing.

## 2026-05-14 - Keep service level out of agent performance

Status: accepted.

Decision: treat service level as a queue, service-category, interval, and staffing metric rather than an agent-level performance metric.

Reasoning: service level measures whether calls are answered within a target wait time. That outcome is driven by demand, routing, queue backlog, staffing, scheduling, and forecast accuracy before the call reaches an individual agent. Agent performance should focus on handled-call volume and handle-time components.

## 2026-05-14 - Use federal holidays in forecasting features

Status: accepted.

Decision: add US federal holiday flags, holiday names, and distance-to-holiday features to the forecasting feature matrix.

Reasoning: public-service contact volume can change around holidays. Holiday features make the forecast more explainable and prepare the project for a longer historical training window.

## 2026-05-14 - Select feature-based Poisson regression for the first proper forecast

Status: superseded by full-history model comparison on 2026-05-15.

Decision: compare multiple scikit-learn models and use the lowest-MAE model output for downstream staffing.

Reasoning: the feature-based Poisson model outperformed the seasonal naive baseline on MAE, RMSE, and MAPE in the small January sample. This result was treated as an early benchmark only.

## 2026-05-15 - Move forecasting to the full 2023-2025 NYC 311 history

Status: accepted.

Decision: download the 2023-01-01 to 2025-12-31 NYC 311 records, load all 10,336,480 rows into SQL Server, and build the 30-minute forecasting input from the SQL raw table.

Reasoning: the January 2025 sample was useful for the first end-to-end MVP but too small for a credible forecasting and workforce planning model. The full three-year history gives realistic seasonality, holiday effects, trend shifts, and high-volume operational patterns.

## 2026-05-15 - Use a SQL raw landing table for the full public extract

Status: accepted.

Decision: create `dbo.Raw_NYC_311_Service_Requests` as a varchar landing table and load it with a Python pyodbc batch loader.

Reasoning: SQL Server bulk insert was unreliable in the local environment for the generated chunk files. A controlled pyodbc loader successfully loaded and validated all 10,336,480 records, after which indexing was applied.

## 2026-05-15 - Select histogram gradient boosting for full-history forecasting

Status: accepted.

Decision: select histogram gradient boosting for the full-history 90-day holdout forecast.

Reasoning: on the full 2023-2025 interval history, histogram gradient boosting produced the lowest holdout MAE. Random forest was close, while Poisson regression performed worst among the compared models.

## 2026-05-15 - Enforce zero understaffing in the full schedule

Status: superseded by legal-roster planning scenario on 2026-05-15.

Decision: make zero understaffing a hard constraint in the full-horizon schedule optimizer.

Reasoning: the schedule is intended for service-level planning, so covering required staffing in every interval is more important than marginally reducing overstaffing.

## 2026-05-15 - Use a simulated 160-agent future planning roster

Status: accepted.

Decision: separate historical model evaluation from future workforce planning. Use the 2025-10-03 to 2025-12-31 holdout for forecast evaluation only, then retrain the selected model on full 2023-2025 history and generate a January 2026 planning forecast, Erlang C staffing curve, and simulated 160-agent roster.

Reasoning: historical schedules are not useful as an operational deliverable. The schedule should represent a future planning period that can be demonstrated as a workforce management analytical demonstration. A simulated roster also needs human constraints: one shift per agent per day, maximum weekly shifts, minimum rest, and explicit break placement.

Outcome: the January 2026 planning forecast contains 1,488 30-minute intervals. Erlang C estimates an average shrinkage-adjusted requirement of 103.0108 agents and a peak of 189 agents. The simulated 160-agent roster schedules 3,427 shifts and validates with zero daily-shift, weekly-limit, or rest violations. The model also estimates that full coverage of the January 2026 24/7 demand curve would require approximately 462 total rostered agents.

## 2026-05-15 - Use synthetic display names for the agent roster

Status: accepted.

Decision: assign stable synthetic display names to the 160-agent roster while preserving numeric `Agent_ID` keys.

Reasoning: named agents make the dashboard and schedule easier to inspect during a demonstration. Numeric IDs remain the database and integration keys, so reports and SQL validation stay reproducible.

## 2026-05-20 - Treat MLflow as an optional productization layer

Status: proposed.

Decision: evaluate MLflow for experiment tracking and model artifact management, but do not add it as a hard dependency until the project team confirms the demonstration workflow.

Reasoning: MLflow is useful for tracking model experiments, parameters, metrics, datasets, and artifacts. The current project already has reproducible JSON summaries and CSV outputs, so the immediate product should remain easy to run. A local MLflow tracking store can be added as a capstone-quality MLOps layer without making SQL Server, Streamlit, or the schedule optimizer depend on MLflow at runtime.
