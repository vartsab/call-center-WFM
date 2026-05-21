# Current Project Status

Last updated: 2026-05-21

## Repository State

The tracked repository contains the main source code, SQL scripts, methodology documents, dashboard screenshots, presentation outline, and submission checklist. Raw data, processed CSV outputs, and Word report files are local generated artifacts and are intentionally excluded from version control.

## Implemented Product Scope

Completed:

- full NYC 311 2023-2025 acquisition workflow;
- SQL Server raw landing table workflow;
- full synthetic call-center warehouse load;
- dimensional tables and analytics views;
- Streamlit dashboard with SQL Server access and generated-artifact support;
- Streamlit dashboard with Postgres deployment mode and password protection;
- compact portfolio seed database for VPS deployment;
- Docker Compose deployment with Postgres, Streamlit, and Caddy;
- public HTTPS deployment on `https://wfm.vartsab.com:8443` while preserving the existing VPN on port `443`;
- deployment runbook and verified deployment status documentation;
- holiday-aware full-history forecasting feature matrix;
- model comparison with selected histogram gradient boosting model;
- interval-level holdout prediction comparison for registered models;
- future planning scenario comparison across registered models;
- Erlang C staffing scenario comparison across registered forecast models;
- forecasting model registry documentation;
- January 2026 future demand forecast;
- Erlang C staffing calculation;
- legal 160-agent roster optimizer;
- dashboard screenshots for report/demo use;
- demo launch and planning pipeline scripts;
- Week 1-6 progress report drafts;
- first full explanatory note draft;
- Word explanatory note draft with embedded dashboard screenshots;
- PowerPoint presentation draft with embedded dashboard screenshots;
- expanded literature, market, and competitor review;
- final presentation outline;
- repository handoff documentation;
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

Future model scenarios:

| Model | Avg predicted calls | Peak predicted calls |
| --- | ---: | ---: |
| Random forest | 208.1176 | 448.0598 |
| Histogram gradient boosting | 204.4150 | 386.1923 |
| Gradient boosting | 199.0700 | 331.4391 |
| Ridge regression | 191.1717 | 324.4033 |
| Poisson regression | 185.3209 | 391.6900 |

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

Model staffing scenarios:

| Model | Peak shrinkage agents | Estimated full-coverage roster |
| --- | ---: | ---: |
| Random forest | 219 | 470 |
| Histogram gradient boosting | 189 | 462 |
| Gradient boosting | 163 | 450 |
| Ridge regression | 158 | 432 |
| Poisson regression | 193 | 419 |

Testing:

```text
13 tests passed
```

Portfolio deployment:

| Check | Result |
| --- | --- |
| Public dashboard URL | `https://wfm.vartsab.com:8443` |
| DNS | `wfm.vartsab.com -> 46.225.121.233` |
| HTTPS certificate | Let's Encrypt certificate issued by Caddy |
| HTTP redirect | `http://wfm.vartsab.com` redirects to `https://wfm.vartsab.com:8443/` |
| Runtime stack | Docker Compose: Postgres, Streamlit, Caddy |
| Dashboard source | Postgres |
| Password gate | Enabled and browser-tested |
| Browser console | No errors or warnings in smoke test |
| Seed row count | `dashboard_volume_30min`: 252,790 rows |

## Local Generated Artifacts

Word reports:

- `docs/reporting/word/Звіт_тиждень_1.docx`
- `docs/reporting/word/Звіт_тиждень_2.docx`
- `docs/reporting/word/Звіт_тиждень_3.docx`
- `docs/reporting/word/Звіт_тиждень_4.docx`
- `docs/reporting/word/Звіт_тиждень_5.docx`
- `docs/reporting/word/Звіт_тиждень_6.docx`

Final report draft:

- `docs/final/Пояснювальна_записка_чернетка.docx`
- `docs/explanatory_note_draft.md`

Presentation draft:

- `docs/final/Презентація_чернетка.pptx`
- `docs/presentation_outline.md`

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
| Technical product | 96% |
| Capstone submission package | 95% |
| Portfolio deployment readiness | 96% |
| Demo readiness | 97% |
| Final report and presentation | 88% |

## Recommended Next Steps

1. Rehearse the public dashboard demo at `https://wfm.vartsab.com:8443` using the deployment password.
2. Rotate `WFM_DEMO_PASSWORD` before sharing the portfolio link broadly.
3. Add a lightweight uptime check or reminder if the public demo must stay available for a fixed review window.
4. Add Postgres backups only if the VPS deployment becomes more than a reproducible portfolio demo.
5. Manually open `docs/final/Пояснювальна_записка_чернетка.docx` and `docs/final/Презентація_чернетка.pptx` only when returning to final submission polish.
