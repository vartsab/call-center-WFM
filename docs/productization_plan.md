# Productization Plan

## Goal

The final demonstration should feel like one coherent product rather than a collection of scripts. The product should show:

- SQL Server as the warehouse and analytics layer;
- PostgreSQL as the compact public-demo runtime;
- Streamlit as the user-facing dashboard;
- forecast evaluation and future planning forecast;
- Erlang C staffing requirements;
- legal roster optimization;
- documented model, schedule, and deployment outputs.

## Current Product Shape

Current workflow:

1. SQL Server stores the raw NYC 311 table and synthetic call-center warehouse.
2. SQL views expose dashboard and modeling inputs.
3. Python scripts generate forecast, staffing, and schedule artifacts.
4. Streamlit reads SQL views, generated CSV artifacts, or compact PostgreSQL seed tables depending on deployment mode.
5. Docker Compose runs the public portfolio stack: PostgreSQL, Streamlit, and Caddy.
6. Documentation records methodology, validation outputs, and deployment status.

This is a valid capstone product because it demonstrates end-to-end data engineering, analytics, forecasting, queueing theory, optimization, dashboard delivery, and public product packaging.

## Option A - Simple Local Demo Bundle

Description: keep the current architecture and add a single command or script that rebuilds the generated artifacts in the correct order.

Implemented additions:

- `scripts/run_planning_pipeline.ps1`
- `scripts/run_dashboard.ps1`
- `scripts/check_demo_readiness.ps1`
- one documentation page with exact demo steps;
- generated artifacts read by the dashboard without rerunning heavy jobs live.

Benefits:

- lowest risk;
- easiest to demonstrate on the laptop;
- no extra platform dependency;
- easiest to explain in the report.

Tradeoffs:

- less formal MLOps story;
- model comparison is documented through JSON/CSV rather than a dedicated experiment tracker.

## Option B - Add Local MLflow Tracking

Description: add MLflow as an experiment-tracking and model-artifact layer for the forecasting part of the project. SQL Server and Streamlit remain the main product surfaces.

MLflow would track:

- model name;
- feature set;
- train/test date ranges;
- parameters;
- MAE, RMSE, and MAPE;
- selected model artifact;
- forecast CSV and summary JSON as artifacts.

Benefits:

- stronger MLOps demonstration;
- model comparison becomes visual in the MLflow UI;
- the selected model can be stored as an artifact and later loaded reproducibly;
- aligns well with the thesis story about model evaluation and traceability.

Tradeoffs:

- adds another dependency and another local service/UI;
- requires careful demo sequencing;
- should not replace the existing JSON summaries because those are simpler for reports and Git history.

Recommended MLflow scope:

- Use MLflow for forecasting experiment tracking only.
- Do not put Erlang C or scheduling inside MLflow as models.
- Log staffing and schedule summaries as artifacts attached to the selected forecast run.
- Keep Streamlit as the main business application.

## Option C - SQL Server Docker Orchestration

Description: package SQL Server, Streamlit, and optional MLflow with Docker Compose.

Benefits:

- looks product-like and portable;
- clean separation of services.

Tradeoffs:

- highest setup risk on a Windows laptop;
- SQL Server container volume and ODBC driver setup can consume time;
- unnecessary for this school demonstration because the public portfolio runtime now uses compact Postgres seed tables.

## Option D - Compact Public VPS Deployment

Description: keep SQL Server as the canonical local warehouse, but publish a compact portfolio runtime with PostgreSQL seed tables, Streamlit, Caddy, and Docker Compose.

Implemented scope:

- `deploy/seed/` contains compact analytical tables;
- `deploy/postgres/001_schema.sql` loads the seed tables into PostgreSQL;
- `CALLCENTER_DASHBOARD_SOURCE=postgres` makes Streamlit read the VPS database;
- `WFM_DEMO_PASSWORD` enables a simple password gate;
- Caddy serves HTTPS on `8443` because the VPS keeps its existing VPN on `443`.

Benefits:

- externally accessible portfolio demo;
- low monthly cost on a small Hetzner VPS;
- avoids hosting the full SQL Server warehouse;
- preserves the enterprise SQL Server story for the analytical build;
- keeps deployment reproducible from a fresh repository clone.

Tradeoffs:

- public URL uses nonstandard HTTPS port `8443`;
- compact seed tables are analytical extracts, not the complete raw warehouse;
- production hardening such as backups and monitoring remains optional.

## Recommended Path

Implemented sequence:

1. Implemented Option A: scripted local demo workflow and readiness checklist.
2. Implemented Option D: public VPS deployment with Postgres, Streamlit, Caddy, and password protection.
3. Deferred Option B: MLflow remains optional because the JSON summaries and dashboard already support explainable model comparison.
4. Avoid Option C unless the final defense explicitly requires a SQL Server container deployment.

## Proposed Final Demo Flow

1. Open Streamlit dashboard.
2. Show SQL-backed historical executive summary.
3. Show full-history forecast model comparison.
4. Show January 2026 forecast.
5. Show Erlang C staffing requirement curve.
6. Show Scheduling tab with:
   - 160-agent legal roster;
   - full-coverage roster estimate;
   - daily shift mix;
   - selected-day coverage gap;
   - roster table with named agents.
7. Show Methodology tab and validation metrics.
8. Mention public deployment: `https://wfm.vartsab.com:8443`.
9. If MLflow is added later, open MLflow UI and show model comparison runs.

## MLflow Notes

MLflow is most useful here as a model experiment and artifact tracker. If added later, use it for forecasting experiment tracking only:

- model name;
- feature set;
- train/test date ranges;
- parameters;
- MAE, RMSE, and MAPE;
- selected model artifact;
- forecast CSV and summary JSON as artifacts.

Do not make MLflow mandatory for the defense demo. The current product already has documented model comparison summaries, model scenario outputs, and a working public dashboard.
