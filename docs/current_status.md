# Current Project Status

Last updated: 2026-05-20

## Repository State

Latest pushed commit:

```text
264bb71 Add presentation and submission checklist
```

The tracked repository contains the main source code, SQL scripts, methodology documents, dashboard screenshots, presentation outline, and submission checklist. Raw data, processed CSV outputs, and Word report files are local generated artifacts and are intentionally excluded from version control.

## Implemented Product Scope

Completed:

- full NYC 311 2023-2025 acquisition workflow;
- SQL Server raw landing table workflow;
- full synthetic call-center warehouse load;
- dimensional tables and analytics views;
- Streamlit dashboard with SQL Server access and generated-artifact support;
- holiday-aware full-history forecasting feature matrix;
- model comparison with selected histogram gradient boosting model;
- January 2026 future demand forecast;
- Erlang C staffing calculation;
- legal 160-agent roster optimizer;
- dashboard screenshots for report/demo use;
- demo launch and planning pipeline scripts;
- Week 1-6 progress report drafts;
- final presentation outline;
- submission checklist.

## Key Validation Results

SQL warehouse:

| Metric | Value |
| --- | ---: |
| Raw records | 10,336,480 |
| Fact calls | 10,336,480 |
| Dates | 1,096 |
| Time intervals | 48 |
| Queues | 217 |
| Agents | 160 |

Forecasting:

| Metric | Value |
| --- | ---: |
| Selected model | Histogram gradient boosting |
| Holdout MAE | 34.8872 |
| Holdout RMSE | 49.7414 |
| Holdout MAPE | 0.2216 |
| Future forecast horizon | 2026-01-01 to 2026-01-31 |

Staffing and scheduling:

| Metric | Value |
| --- | ---: |
| Future intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |
| Peak shrinkage-adjusted agents | 189 |
| Scheduled shifts | 3,427 |
| Legal roster size | 160 |
| Estimated full-coverage roster | 462 |
| Daily shift violations | 0 |
| Weekly shift-limit violations | 0 |
| Rest violations | 0 |

Testing:

```text
10 tests passed
```

## Local Generated Artifacts

Word reports:

- `docs/reporting/word/Звіт_тиждень_1.docx`
- `docs/reporting/word/Звіт_тиждень_2.docx`
- `docs/reporting/word/Звіт_тиждень_3.docx`
- `docs/reporting/word/Звіт_тиждень_4.docx`
- `docs/reporting/word/Звіт_тиждень_5.docx`
- `docs/reporting/word/Звіт_тиждень_6.docx`

Dashboard screenshots:

- `docs/screenshots/01_executive_summary.png`
- `docs/screenshots/02_historical_trends.png`
- `docs/screenshots/03_forecasting.png`
- `docs/screenshots/04_staffing_requirements.png`
- `docs/screenshots/05_scheduling_coverage.png`
- `docs/screenshots/06_agent_performance.png`
- `docs/screenshots/07_methodology_validation.png`

## Current Coverage Estimate

| Area | Coverage |
| --- | ---: |
| Technical product | 86% |
| Capstone submission package | 85% |
| Demo readiness | 89% |
| Final report and presentation | 62% |

## Recommended Next Steps

1. Manually open and inspect Week 3-6 Word reports in Microsoft Word.
2. Insert selected screenshots into the explanatory note.
3. Draft the final explanatory note chapters.
4. Prepare presentation slides from `docs/presentation_outline.md`.
5. Rehearse the dashboard demo using `scripts/run_dashboard.ps1`.
6. Optionally add MLflow tracking only if time remains after report/presentation polish.
