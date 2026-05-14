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
