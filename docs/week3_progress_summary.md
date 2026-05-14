# Week 3 Technical Progress Summary

This summary documents the current technical state after the first SQL-load and forecasting work.

## SQL Load Preparation

Generated SQL-load-ready files from the synthetic call sample:

| File | Rows |
| --- | ---: |
| `dim_date_sample.csv` | 31 |
| `dim_time_sample.csv` | 48 |
| `dim_agent_sample_sql.csv` | 60 |
| `dim_queue_sample_sql.csv` | 101 |
| `fact_calls_sample_sql.csv` | 6,200 |

The generated files are stored locally under:

```text
data/processed/sql_load/
```

These files are intentionally excluded from version control.

## SQL Scripts Added

SQL Server execution order:

1. `sql/schema/001_create_call_center_warehouse.sql`
2. `sql/etl/001_create_staging_tables.sql`
3. `sql/etl/002_bulk_insert_sample_files.sql`
4. `sql/etl/003_load_star_schema_from_staging.sql`
5. `sql/views/001_analytics_views.sql`

## Forecasting Baseline

Generated forecasting input:

```text
data/processed/forecasting_input_sample.csv
```

Rows:

```text
2,718
```

First baseline model:

```text
seasonal naive mean by weekday and half-hour interval
```

Latest metrics:

| Metric | Value |
| --- | ---: |
| Test intervals | 336 |
| MAE | 1.8299 |
| RMSE | 2.3866 |
| MAPE | 0.7344 |

Metrics are stored in:

```text
docs/baseline_forecast_summary.json
```

## Next Technical Step

Use the Erlang C staffing requirements as the demand curve for the first shift-scheduling optimization step.
