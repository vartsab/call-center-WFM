# Щотижневий звіт про прогрес. Тиждень 4

## Проєкт

**Call Center Analytics and Workforce Optimization for City Service Operations**

Дата підготовки звіту: 20.05.2026  
Звітний період: 4-й тиждень активного етапу дипломного проєктування

Фокус тижня: повний synthetic warehouse, SQL views та SQL-backed Streamlit dashboard.

## 1. Виконані завдання, досягнення та зміни у проєкті

На четвертому тижні було створено повний synthetic call-center warehouse на основі SQL raw table. Проєкт перейшов від raw public-service records до повноцінної аналітичної моделі контакт-центру з fact table, dimension tables, операційними метриками та dashboard-ready SQL views.

- реалізовано повний SQL ETL з raw NYC 311 table до synthetic warehouse;
- створено один simulated call/contact для кожного raw 311 record;
- заповнено `Dim_Date`, `Dim_Time`, `Dim_Queue`, `Dim_Agent` та `Fact_Calls`; 
- створено 217 queues на основі observed complaint types;
- створено 160 synthetic agents;
- згенеровано hold time, talk time, after-call work, abandonment flag, SLA flag та agent assignment;
- перевірено view totals і KPI reconciliation;
- оновлено Streamlit dashboard для читання даних з SQL Server views.

## 2. Реалізовані компоненти

Головним технічним результатом тижня став SQL script `sql/etl/004_load_full_synthetic_warehouse_from_raw.sql`, який rebuilds the dimensional warehouse з повного raw dataset.

| Object / Metric | Value |
| --- | --- |
| `Dim_Date` | 1,096 |
| `Dim_Time` | 48 |
| `Dim_Queue` | 217 |
| `Dim_Agent` | 160 |
| `Fact_Calls` | 10,336,480 |
| `vw_Volume_30Min` rows | 2,230,984 |
| `vw_Forecasting_Input` rows | 252,790 |
| Offered calls | 10,336,480 |
| Answered calls | 9,527,782 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |

## 3. Методологічні рішення

Синтетичні call-center поля були згенеровані deterministic способом, щоб warehouse можна було відтворити. Такий підхід дозволяє уникнути випадкових розбіжностей між запусками та робить результати придатними для валідації.

Service level було визначено як queue/service-category/staffing metric, а не agent-level metric, тому що індивідуальний агент не контролює очікування в черзі до моменту маршрутизації звернення.

## 4. Demo / проміжна перевірка

На цьому етапі dashboard вже міг демонструвати executive summary, historical trends, service category mix та agent performance на основі SQL Server. Це стало першим повним end-user view поверх warehouse.

Письмовий feedback від наукового керівника до цього звіту не додавався.

## 5. Ризики та шляхи їх вирішення

| Ризик або проблема | Вплив |
| --- | --- |
| Синтетичні операційні поля | Потрібно пояснити, що це simulation, а не actual NYC call center data. |
| Вирішення | Документувати distributions, deterministic logic, assumptions і limitations. |

| Ризик або проблема | Вплив |
| --- | --- |
| Велика кількість view rows | Dashboard може повільно завантажувати granular SQL views. |
| Вирішення | Використовувати агреговані SQL запити для demo dashboard і залишити деталізовані views для validation/modeling. |

## 6. План роботи на наступний тиждень

- побудувати full-history forecasting input;
- створити holiday-aware feature matrix;
- порівняти baseline та feature-based models;
- обрати модель за метриками holdout period;
- перейти до Erlang C staffing calculation.

## 7. Артефакти

- `sql/etl/004_load_full_synthetic_warehouse_from_raw.sql`
- `sql/views/001_analytics_views.sql`
- `app/streamlit/app.py`
- `docs/sql_validation_summary.md`
- `docs/data_dictionary.md`

## 8. Висновок за тиждень

На четвертому тижні проєкт отримав повноцінний SQL-backed warehouse і dashboard foundation. Це закрило ключовий data engineering layer та створило основу для наукової частини проєкту: forecasting, Erlang C staffing і schedule optimization.
