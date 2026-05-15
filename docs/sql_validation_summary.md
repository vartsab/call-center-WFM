# SQL Validation Summary

Validation date: 2026-05-15

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
| `Raw_NYC_311_Service_Requests` | 10,336,480 |
| `vw_Raw_NYC_311_Volume_30Min` | 52,603 |
| `Dim_Date` | 1,096 |
| `Dim_Time` | 48 |
| `Dim_Queue` | 217 |
| `Dim_Agent` | 160 |
| `Fact_Calls` | 10,336,480 |
| `vw_Volume_30Min` | 2,230,984 |
| `vw_Forecasting_Input` | 252,790 |
| `vw_Agent_Performance` | 175,359 |

## Raw NYC 311 Validation

The full raw table was loaded from the 2023-01-01 to 2025-12-31 NYC 311 extract.

| Metric | Value |
| --- | ---: |
| Raw rows | 10,336,480 |
| 30-minute view rows | 52,603 |
| 30-minute view total requests | 10,336,480 |
| Minimum created date | 2023-01-01T00:00:00.000 |
| Maximum created date | 2025-12-31T23:59:28.000 |

Yearly row counts:

| Year | Rows |
| --- | ---: |
| 2023 | 3,224,722 |
| 2024 | 3,456,770 |
| 2025 | 3,654,988 |

## Fact Table KPIs

| Metric | Value |
| --- | ---: |
| Offered calls | 10,336,480 |
| Answered calls | 9,527,782 |
| Abandoned calls | 808,698 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |
| SLA rate | 22.57% |

## View Reconciliation

The totals from `vw_Volume_30Min` reconcile with `Fact_Calls`:

| Metric | Value |
| --- | ---: |
| View offered calls | 10,336,480 |
| View answered calls | 9,527,782 |
| View abandoned calls | 808,698 |

## Service Category Summary

| Service category | Offered calls | Avg service level | Avg AHT |
| --- | ---: | ---: | ---: |
| housing | 3,469,112 | 0.2435 | 600.85 |
| general | 3,175,514 | 0.2194 | 525.88 |
| transportation | 2,617,130 | 0.2239 | 487.87 |
| public_safety | 763,458 | 0.2349 | 450.20 |
| sanitation | 311,266 | 0.2257 | 400.11 |

## Notes

- The full synthetic warehouse load from the raw 311 table executed successfully.
- The full raw 311 table loaded successfully through the Python pyodbc loader and was indexed after loading.
- The full raw analytics views reconcile back to the raw table total.
- `vw_Forecasting_Input` uses normalized service categories from `Dim_Queue`, and the Python forecasting input builder was aligned to the same grain.
- The validation script is stored in `sql/validation/001_validate_loaded_sample.sql`.
