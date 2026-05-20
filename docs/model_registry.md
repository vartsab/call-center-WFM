# Forecasting Model Registry

The forecasting pipeline is intentionally model-aware. The current selected model is not hardcoded into the project architecture; it is selected from a small registry of scikit-learn estimators.

## Current Models

Models are registered in:

```text
src/forecasting/sklearn_model_compare.py
```

Current model names:

| Model name | Family |
| --- | --- |
| `hist_gradient_boosting` | tree boosting |
| `random_forest` | bagged trees |
| `gradient_boosting` | tree boosting |
| `ridge` | regularized linear regression |
| `poisson` | generalized linear model for counts |

## Rerun Planning With Another Model

The planning pipeline accepts the selected model as a parameter:

```powershell
.\scripts\run_planning_pipeline.ps1 -Model random_forest
```

This regenerates:

- future forecast;
- Erlang C staffing requirements;
- optimized January 2026 schedule;
- dashboard inputs.

## Compare Future Scenarios

The future forecasting script can also generate scenario forecasts for every registered model:

```powershell
python src\forecasting\future_feature_forecast.py `
  --input data\processed\full_forecast_features.csv `
  --forecast-output data\processed\future_sklearn_forecast.csv `
  --feature-output data\processed\future_forecast_features.csv `
  --summary-output docs\future_forecast_summary.json `
  --all-models-output data\processed\future_model_scenario_forecasts.csv `
  --all-models-summary-output docs\future_model_scenario_summary.json `
  --model hist_gradient_boosting
```

The Streamlit Forecasting tab reads the scenario file and visualizes differences between model forecast curves.

## Add A New Model

1. Add the estimator to `model_candidates()` in `src/forecasting/sklearn_model_compare.py`.
2. Give it a stable snake_case name.
3. Make sure it supports `.fit(X, y)` and `.predict(X)`.
4. Rerun `sklearn_model_compare.py` with `--all-predictions-output`.
5. Rerun `scripts/run_planning_pipeline.ps1`.
6. Review the dashboard comparison before using the model for staffing.

This keeps model extensibility explicit and reproducible without turning the dashboard into an unsafe arbitrary-code execution surface.
