# Щотижневий звіт про прогрес. Тиждень 5

## Проєкт

**Call Center Analytics and Workforce Optimization for City Service Operations**

Дата підготовки звіту: 20.05.2026  
Звітний період: 5-й тиждень активного етапу дипломного проєктування

Фокус тижня: forecasting model evaluation та Erlang C staffing.

## 1. Виконані завдання, досягнення та зміни у проєкті

На п’ятому тижні було реалізовано predictive-to-prescriptive pipeline: прогнозування попиту, порівняння моделей і розрахунок потреби в персоналі через Erlang C.

- побудовано 30-хвилинний full-history forecasting input;
- створено feature matrix для 2023-2025 років;
- додано cyclical time features, weekend features, US federal holidays та distance-to-holiday features;
- реалізовано seasonal naive baseline;
- порівняно кілька scikit-learn моделей;
- обрано histogram gradient boosting як найкращу модель за holdout MAE;
- побудовано future forecast на січень 2026 року;
- перетворено прогноз і AHT на staffing requirements через Erlang C.

## 2. Оцінювання моделей

Для оцінювання використано 90-денний holdout period: 2025-10-03 to 2025-12-31. Моделі порівнювалися за MAE, RMSE та MAPE.

| Model | MAE / RMSE / MAPE |
| --- | --- |
| Histogram gradient boosting | 34.8872 / 49.7414 / 0.2216 |
| Random forest | 35.7124 / 50.8680 / 0.2254 |
| Gradient boosting | 38.2330 / 54.0725 / 0.2420 |
| Ridge regression | 42.0608 / 59.0505 / 0.2720 |
| Poisson regression | 47.9825 / 71.4876 / 0.3055 |

Histogram gradient boosting було обрано як selected model, оскільки ця модель мала найнижче MAE на повному historical holdout.

## 3. Staffing calculation

Після прогнозування було застосовано Erlang C, тому що staffing у контакт-центрі є задачею queueing theory, а не напряму задачею machine learning. Модель прогнозує попит, а Erlang C перетворює forecasted calls та AHT у потрібну кількість операторів.

| Metric | Value |
| --- | --- |
| Forecast period | 2026-01-01 to 2026-01-31 |
| Forecast intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |
| Average shrinkage-adjusted agents | 103.0108 |
| Peak shrinkage-adjusted agents | 189 |
| Target service level | 80% answered within 20 sec |
| Max occupancy | 85% |
| Shrinkage | 30% |

## 4. Методологічні рішення

Федеральні свята США були додані до feature set, оскільки public-service demand може змінюватися навколо свят. Для майбутнього forecast на January 2026 previous-week lag seed використовується з історичних даних, а потім rolling forward рекурсивно в межах майбутнього горизонту.

MAPE використовується обережно, тому що у low-volume intervals ця метрика може бути нестабільною.

## 5. Ризики та шляхи їх вирішення

| Ризик або проблема | Вплив |
| --- | --- |
| Forecast error впливає на staffing | Помилка прогнозу може призвести до overstaffing або understaffing. |
| Вирішення | Порівняти моделі з baseline і використовувати holdout metrics для обґрунтування вибору. |

| Ризик або проблема | Вплив |
| --- | --- |
| Надмірна складність моделей | Складні моделі важче пояснювати в дипломній роботі. |
| Вирішення | Використати explainable feature-based model comparison, а не вводити LSTM без потреби. |

## 6. План роботи на наступний тиждень

- побудувати roster simulation optimizer;
- створити future schedule для January 2026;
- додати scheduling tab у dashboard;
- підготувати screenshots і demo script;
- перевірити тестами ключові модулі.

## 7. Артефакти

- `src/forecasting/build_feature_matrix.py`
- `src/forecasting/sklearn_model_compare.py`
- `src/forecasting/future_feature_forecast.py`
- `src/workforce/erlang_c_staffing.py`
- `docs/forecasting_methodology.md`
- `docs/full_sklearn_model_comparison_summary.json`
- `docs/future_forecast_summary.json`
- `docs/future_staffing_requirements_summary.json`

## 8. Висновок за тиждень

На п’ятому тижні реалізовано ключову Data Science частину проєкту. Було побудовано та оцінено моделі прогнозування, обрано найкращу модель для full-history holdout, а також виконано Erlang C staffing calculation для майбутнього planning horizon.
