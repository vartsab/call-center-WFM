# Project Brief

## Working Title

Call Center Analytics and Workforce Optimization for City Service Operations

## Project Type

Engineering project with a data science component.

## Core Idea

Build an end-to-end analytical system that turns raw or semi-raw call/service demand data into operational decisions for a call center. The system should support historical reporting, forecast future demand, estimate required staffing by 30-minute interval, and generate a feasible team schedule.

## Problem Statement

Call centers face time-varying demand, long-tail handle times, SLA pressure, and staffing constraints. Managers need a reproducible way to understand demand, forecast interval-level volume, calculate required coverage, and schedule agents while minimizing undercoverage and overstaffing.

## Proposed Domain

Primary domain: city 311 service center.

Preferred seed data: public 311 request data from a large city, such as NYC 311 or Austin 311. The real dataset provides realistic demand seasonality, geographic distribution, request types, and event-driven spikes. Missing call center operational fields will be synthetically generated and clearly documented.

Alternative domain: healthcare service/contact center if a suitable public or synthetic dataset is chosen.

## Product Users

- call center operations manager;
- workforce management analyst;
- city service performance analyst;
- academic evaluator reviewing the engineering and data science methodology.

## Main Deliverables

- reproducible dataset acquisition and synthetic enhancement pipeline;
- Microsoft SQL Server database using a dimensional/star schema;
- SQL views for dashboard and model inputs;
- Streamlit dashboard with historical KPIs, trends, forecasting, staffing, and schedule views;
- forecasting pipeline for 30-minute call volume;
- Erlang C staffing calculator;
- MILP schedule optimizer;
- explanatory note and weekly progress reports.

## Scientific And Engineering Contribution

The project combines:

- data engineering: data ingestion, cleaning, schema design, SQL views;
- data science: time-series forecasting and model evaluation;
- operations research: staffing and shift optimization;
- software engineering: interactive dashboard and reproducible project structure.

## Initial Success Criteria

- A user can inspect historical call center KPIs from SQL-backed views.
- The system can generate future 30-minute call forecasts.
- The system can convert forecasted volume and AHT into staffing requirements.
- The system can produce a feasible schedule for a sample agent pool.
- Technical assumptions, limitations, and synthetic data generation choices are documented.

## Current Priority

Create the project backbone, then immediately start Week 1 and Week 2 progress reporting while implementation work begins in parallel.

