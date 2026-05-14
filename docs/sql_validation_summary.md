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
| `vw_Volume_30Min` | 4,125 |
| `vw_Forecasting_Input` | 2,718 |
| `vw_Agent_Performance` | 1,310 |

## Fact Table KPIs

| Metric | Value |
| --- | ---: |
| Offered calls | 6,200 |
| Answered calls | 5,785 |
| Abandoned calls | 415 |
| Abandonment rate | 6.69% |
| Average answered handle time | 519.82 sec |
| SLA rate | 20.00% |

## View Reconciliation

The totals from `vw_Volume_30Min` reconcile with `Fact_Calls`:

| Metric | Value |
| --- | ---: |
| View offered calls | 6,200 |
| View answered calls | 5,785 |
| View abandoned calls | 415 |

## Service Category Summary

| Service category | Offered calls | Avg service level | Avg AHT |
| --- | ---: | ---: | ---: |
| housing | 3,913 | 0.2147 | 555.11 |
| transportation | 1,023 | 0.1937 | 448.93 |
| general | 876 | 0.1802 | 481.04 |
| public_safety | 360 | 0.2055 | 437.36 |
| sanitation | 28 | 0.2222 | 390.35 |

## Notes

- The warehouse schema, staging tables, bulk load, transform script, and analytics views executed successfully.
- `vw_Forecasting_Input` uses normalized service categories from `Dim_Queue`, and the Python forecasting input builder was aligned to the same grain.
- The validation script is stored in `sql/validation/001_validate_loaded_sample.sql`.
