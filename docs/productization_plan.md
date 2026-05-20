# Productization Plan

## Goal

The final demonstration should feel like one coherent product rather than a collection of scripts. The product should show:

- SQL Server as the warehouse and analytics layer;
- Streamlit as the user-facing dashboard;
- forecast evaluation and future planning forecast;
- Erlang C staffing requirements;
- legal roster optimization;
- documented model and schedule outputs.

## Current Product Shape

Current local workflow:

1. SQL Server stores the raw NYC 311 table and synthetic call-center warehouse.
2. SQL views expose dashboard and modeling inputs.
3. Python scripts generate forecast, staffing, and schedule artifacts.
4. Streamlit reads SQL views plus generated local planning files.
5. Documentation records methodology and validation outputs.

This is already a valid capstone product because it demonstrates end-to-end data engineering, analytics, forecasting, queueing theory, optimization, and dashboard delivery.

## Option A - Simple Demo Bundle

Description: keep the current architecture and add a single command or script that rebuilds the generated artifacts in the correct order.

Possible additions:

- `scripts/run_planning_pipeline.ps1`
- `scripts/run_dashboard.ps1`
- one documentation page with exact demo steps;
- optional dashboard button that reads existing planning outputs rather than rerunning heavy jobs live.

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

## Option C - Docker Orchestration

Description: package SQL Server, Streamlit, and optional MLflow with Docker Compose.

Benefits:

- looks product-like and portable;
- clean separation of services.

Tradeoffs:

- highest setup risk on a Windows laptop;
- SQL Server container volume and ODBC driver setup can consume time;
- unnecessary for a school demonstration unless portability becomes a formal requirement.

## Recommended Path

Recommended sequence:

1. Implement Option A first: a single scripted demo workflow and a clear demo checklist.
2. Add Option B after that if time allows: local MLflow tracking for model comparison and selected-model artifact storage.
3. Avoid Option C unless the final defense explicitly requires containerized deployment.

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
8. If MLflow is added, open MLflow UI and show model comparison runs.

## MLflow Notes

MLflow is most useful here as a model experiment and artifact tracker. The official MLflow documentation describes tracking runs, models, datasets, and artifacts, with local `mlruns` storage as the simplest setup and an optional tracking server for larger workflows: https://mlflow.org/docs/latest/ml/tracking/

The MLflow CLI can start the UI and serve or predict with saved models: https://mlflow.org/docs/latest/api_reference/cli.html

The open-source Model Registry can manage registered models, versions, aliases, tags, and descriptions: https://mlflow.github.io/mlflow-website/docs/latest/ml/model-registry/

As of the current public GitHub release page, MLflow 3.12.0 is listed as the latest release on 2026-05-05: https://github.com/mlflow/mlflow
