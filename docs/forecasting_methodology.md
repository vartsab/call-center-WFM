# Forecasting Methodology

## Purpose

The forecasting step predicts inbound demand for each 30-minute interval. The forecast is then used by the Erlang C staffing calculator and the schedule optimizer.

## Full-History Input

The forecasting pipeline now uses the full local SQL Server raw table created from NYC 311 data for 2023-01-01 through 2025-12-31.

| Metric | Value |
| --- | ---: |
| Raw SQL records | 10,336,480 |
| Source period | 2023-01-01 to 2025-12-31 |
| Observed 30-minute rows | 52,603 |
| Complete 30-minute grid rows | 52,608 |
| Holdout period | 2025-10-03 to 2025-12-31 |
| Holdout intervals | 4,320 |

The full interval input is generated from SQL Server by:

```text
src/forecasting/build_full_forecasting_input_from_sql.py
```

## Feature Matrix

The feature matrix is created with:

```text
src/forecasting/build_feature_matrix.py
```

It includes cyclical half-hour and weekday features, calendar features, weekend flags, US federal holiday flags, distance to the nearest federal holiday, and a previous-week same-interval lag.

Federal holidays are generated locally by:

```text
src/forecasting/us_federal_holidays.py
```

## Baseline Comparison

The seasonal naive baseline uses the average historical call volume by weekday and half-hour interval.

| Metric | Value |
| --- | ---: |
| MAE | 41.1254 |
| RMSE | 57.3621 |
| MAPE | 0.2356 |

## Feature-Based Model Comparison

The scikit-learn model comparison is created with:

```text
src/forecasting/sklearn_model_compare.py
```

Models are selected by lowest holdout MAE.

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Histogram gradient boosting | 34.8872 | 49.7414 | 0.2216 |
| Random forest | 35.7124 | 50.8680 | 0.2254 |
| Gradient boosting | 38.2330 | 54.0725 | 0.2420 |
| Ridge regression | 42.0608 | 59.0505 | 0.2720 |
| Poisson regression | 47.9825 | 71.4876 | 0.3055 |

The selected model is histogram gradient boosting. Random forest is close, while Poisson regression performs worst on the full-history holdout. This result replaces the earlier January-sample result, where the very small demand range made Poisson regression look better than it does on the full operational history.

The comparison script can also export interval-level holdout predictions for every registered model:

```text
data/processed/full_model_holdout_predictions.csv
```

This file supports dashboard visualization of the actual holdout curve against multiple model predictions. It makes the model choice visible rather than hiding it inside a single selected output file.

## Model Registry And Extensibility

The forecasting models are registered in:

```text
src/forecasting/sklearn_model_compare.py
```

The current registry is the `model_candidates()` function. Adding a new model means adding another named estimator to that function, rerunning the comparison, and reviewing its holdout metrics in the dashboard.

The planning pipeline accepts a model parameter:

```powershell
.\scripts\run_planning_pipeline.ps1 -Model random_forest
```

Supported current model names:

- `hist_gradient_boosting`
- `random_forest`
- `gradient_boosting`
- `ridge`
- `poisson`

## Future Planning Forecast

The selected histogram gradient boosting model is retrained on the full 2023-2025 feature matrix and used to forecast the January 2026 planning horizon.

| Metric | Value |
| --- | ---: |
| Forecast period | 2026-01-01 to 2026-01-31 |
| Forecast intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |

Future holiday features are generated with the same US federal holiday calendar used in the holdout evaluation. The previous-week lag is seeded from observed 2025 history and then rolled forward recursively inside the January 2026 horizon.

The future planning pipeline also generates a scenario file for all registered models:

```text
data/processed/future_model_scenario_forecasts.csv
docs/future_model_scenario_summary.json
```

Current January 2026 model scenarios:

| Model | Avg predicted calls | Peak predicted calls |
| --- | ---: | ---: |
| Random forest | 208.1176 | 448.0598 |
| Histogram gradient boosting | 204.4150 | 386.1923 |
| Gradient boosting | 199.0700 | 331.4391 |
| Ridge regression | 191.1717 | 324.4033 |
| Poisson regression | 185.3209 | 391.6900 |

These scenarios allow the dashboard to visualize how model selection affects the planning forecast before the forecast is converted into Erlang C staffing and schedules.

## Output

The full-history model writes:

```text
data/processed/full_sklearn_best_forecast.csv
data/processed/full_model_holdout_predictions.csv
docs/full_sklearn_model_comparison_summary.json
```

The future planning model writes:

```text
data/processed/future_sklearn_forecast.csv
data/processed/future_forecast_features.csv
data/processed/future_model_scenario_forecasts.csv
docs/future_forecast_summary.json
docs/future_model_scenario_summary.json
```

Raw and processed CSV outputs remain local generated artifacts and are not committed to version control.
