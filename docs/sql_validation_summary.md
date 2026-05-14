# SQL Validation Summary

Validation date: 2026-05-14

Database:

```text
CallCenterWFM
```

SQL Server instance:

```text
localhost / TheLaptop
```

## Load Results

| Object | Row count |
| --- | ---: |
| `Dim_Date` | 31 |
| `Dim_Time` | 48 |
| `Dim_Queue` | 101 |
| `Dim_Agent` | 60 |
| `Fact_Calls` | 6,200 |
| `vw_Volume_30Min` | 4,230 |
| `vw_Forecasting_Input` | 2,764 |
| `vw_Agent_Performance` | 1,322 |

## Fact Table KPIs

| Metric | Value |
| --- | ---: |
| Offered calls | 6,200 |
| Answered calls | 5,790 |
| Abandoned calls | 410 |
| Abandonment rate | 6.61% |
| Average answered handle time | 517.57 sec |
| SLA rate | 20.55% |

## View Reconciliation

The totals from `vw_Volume_30Min` reconcile with `Fact_Calls`:

| Metric | Value |
| --- | ---: |
| View offered calls | 6,200 |
| View answered calls | 5,790 |
| View abandoned calls | 410 |

## Service Category Summary

| Service category | Offered calls | Avg service level | Avg AHT |
| --- | ---: | ---: | ---: |
| housing | 3,825 | 0.2124 | 554.98 |
| transportation | 1,070 | 0.2328 | 451.62 |
| general | 892 | 0.1992 | 476.24 |
| public_safety | 383 | 0.1983 | 422.33 |
| sanitation | 30 | 0.2759 | 388.76 |

## Notes

- The warehouse schema, staging tables, bulk load, transform script, and analytics views executed successfully.
- `vw_Forecasting_Input` uses normalized service categories from `Dim_Queue`, and the Python forecasting input builder was aligned to the same grain.
- The validation script is stored in `sql/validation/001_validate_loaded_sample.sql`.
