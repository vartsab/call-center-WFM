# Щотижневий звіт про прогрес. Тиждень 2

## Проєкт

**Call Center Analytics and Workforce Optimization for City Service Operations**

Дата підготовки звіту: 11.05.2026  
Звітний період: 2-й тиждень активного етапу дипломного проєктування

## 1. Виконані завдання, досягнення та зміни у проєкті

На другому тижні було здійснено перехід від концептуального планування до перших технічних артефактів MVP. Основний фокус був на виборі реального seed dataset, створенні відтворюваного data pipeline для першого sample dataset, документуванні synthetic data methodology та підготовці початкової SQL Server архітектури.

Основні виконані завдання:

- обрано перший seed dataset: NYC Open Data 311 Service Requests from 2020 to Present;
- задокументовано причини вибору dataset, його поля, переваги та обмеження;
- створено скрипт завантаження sample data через публічний Socrata CSV API;
- завантажено локальний sample за січень 2025 року з обмеженням до 200 записів на день;
- створено скрипт синтетичної генерації операційних call-center полів;
- згенеровано перший synthetic call-level dataset;
- створено synthetic dimension data для агентів і черг;
- підготовлено початковий SQL Server star schema script;
- підготовлено початкові SQL views для Streamlit dashboard та майбутнього forecasting pipeline;
- оновлено decision log, data dictionary і документацію щодо dataset;
- перевірено, що Python-скрипти компілюються без синтаксичних помилок.

## 2. Реалізовані або вдосконалені компоненти

### Data acquisition

Створено скрипт:

- `src/data_acquisition/download_nyc_311_sample.py`

Скрипт завантажує дані з публічного NYC Open Data API:

- endpoint: `https://data.cityofnewyork.us/resource/erm2-nwe9.csv`;
- поточний період sample: січень 2025 року;
- поточна стратегія: до 200 записів на день;
- output: `data/raw/nyc_311_sample.csv`;
- metadata output: `data/raw/nyc_311_sample_metadata.json`.

### Synthetic generation

Створено скрипт:

- `src/data_generation/generate_synthetic_calls.py`

Скрипт створює:

- call-level fact source;
- synthetic agent dimension;
- queue dimension;
- summary metrics.

Згенеровані локальні файли:

- `data/processed/synthetic_calls_sample.csv`;
- `data/processed/dim_agents_sample.csv`;
- `data/processed/dim_queues_sample.csv`;
- `docs/sample_generation_summary.json`.

Поточні характеристики sample:

| Метрика | Значення |
| --- | ---: |
| Source rows | 6,200 |
| Synthetic agents | 60 |
| Queues | 101 |
| Abandonment rate | 0.0661 |
| Average handle time for answered calls | 517.57 sec |
| Distinct 30-minute intervals | 1,321 |
| Maximum calls in one interval | 17 |

### SQL Server schema

Підготовлено початковий SQL Server DDL:

- `sql/schema/001_create_call_center_warehouse.sql`

Скрипт створює:

- `Dim_Date`;
- `Dim_Time`;
- `Dim_Queue`;
- `Dim_Agent`;
- `Fact_Calls`;
- foreign keys;
- check constraint для не-негативних duration fields;
- індекси для interval-level analytics, queue analytics та agent analytics.

### SQL analytics layer

Підготовлено початкові SQL views:

- `sql/views/001_analytics_views.sql`

Views включають:

- `vw_Volume_30Min`;
- `vw_Forecasting_Input`;
- `vw_Agent_Performance`.

Ці views мають стати основою для Streamlit dashboard та forecasting pipeline.

## 3. Методологічні рішення

Ключове рішення тижня — використання hybrid data strategy:

- реальні NYC 311 дані використовуються для збереження міського контексту, service categories, дат, borough та status;
- операційні call-center поля генеруються синтетично, оскільки вони не є доступними у public dataset.

Синтетично згенеровані поля:

- simulated call start datetime;
- answer datetime;
- end datetime;
- hold time;
- talk time;
- after-call work;
- handle time;
- abandonment flag;
- SLA met flag;
- queue ID;
- agent ID.

Talk time генерується через log-normal distribution, оскільки тривалість дзвінків є невід’ємною і зазвичай має right-skewed distribution. After-call work генерується через gamma distribution. Ймовірність abandonment збільшується зі зростанням hold time.

Окремо задокументовано важливе обмеження: `Call_Start_Datetime` є синтетичним полем. Реальна дата звернення зберігається як `Source_Created_Datetime`, але час початку дзвінка симулюється в межах тієї самої календарної дати, щоб отримати придатну 30-хвилинну operational curve для MVP.

## 4. Перше demo та feedback

Станом на дату підготовки звіту письмовий feedback від наукового керівника ще не додано до артефактів проєкту. Тому в цьому розділі зафіксовано готовність матеріалів до першого demo / architecture walkthrough.

На цей момент підготовлено матеріали для першого architecture / data pipeline walkthrough:

- problem statement and project objectives;
- end-to-end system architecture;
- selected dataset and limitations;
- first acquisition script;
- first synthetic generation script;
- generated sample summary;
- initial SQL Server schema;
- initial SQL analytics views.

Питання для обговорення з керівником:

- Чи прийнятне позиціонування роботи як інженерного проєкту?
- Чи прийнятний city 311 domain для теми контакт-центру?
- Чи достатньо прозоро обґрунтовано використання synthetic operational metadata?
- Чи потрібно звужувати scope MVP перед наступним етапом?

## 5. Ризики та шляхи їх вирішення

| Ризик або проблема | Вплив | Вирішення |
| --- | --- | --- |
| 311 record не завжди є телефонним дзвінком. | Не можна стверджувати, що dataset напряму описує реальний call center. | Формулювати dataset як simulation seeded by real public city-service demand. |
| Операційні поля є synthetic. | Потрібно довести академічну коректність припущень. | Документувати розподіли, random seed, логіку SLA, abandonment та agent assignment. |
| Перший sample ще не завантажений у SQL Server. | SQL views поки не перевірені на реальній базі. | Наступний крок — налаштувати SQL Server database і виконати DDL/load scripts. |
| Dashboard ще не реалізовано. | Немає повного end-user demo. | Після SQL або CSV-ready layer створити перший Streamlit MVP. |
| Scope залишається великим. | Є ризик не встигнути глибоко реалізувати всі компоненти. | Пріоритет: data pipeline, SQL views, один baseline forecast, Erlang C, простий optimizer, dashboard. |

## 6. План роботи на тиждень 3

На третій тиждень заплановано:

- створити SQL ETL/load script для завантаження generated CSV у MS SQL Server;
- заповнити `Dim_Date`, `Dim_Time`, `Dim_Queue`, `Dim_Agent`, `Fact_Calls`;
- виконати та перевірити SQL views;
- підготувати перші KPI outputs для dashboard;
- створити baseline forecasting dataset на 30-хвилинному рівні;
- реалізувати перший простий forecasting baseline;
- почати перший Streamlit MVP або notebook demo;
- підготувати короткі demo screenshots або query outputs для документації.

## 7. Артефакти

Підготовлені артефакти другого тижня:

- `docs/dataset_source.md`
- `docs/data_generation_methodology.md`
- `docs/sample_generation_summary.json`
- `src/data_acquisition/download_nyc_311_sample.py`
- `src/data_generation/generate_synthetic_calls.py`
- `sql/schema/001_create_call_center_warehouse.sql`
- `sql/views/001_analytics_views.sql`
- `docs/data_dictionary.md`
- `docs/decision_log.md`

Локальні generated data outputs:

- `data/raw/nyc_311_sample.csv`
- `data/raw/nyc_311_sample_metadata.json`
- `data/processed/synthetic_calls_sample.csv`
- `data/processed/dim_agents_sample.csv`
- `data/processed/dim_queues_sample.csv`

## 8. Висновок за тиждень

На другому тижні проєкт перейшов від архітектурного планування до першого робочого data pipeline. Було обрано seed dataset, створено acquisition script, згенеровано synthetic call-center sample, підготовлено SQL Server schema draft і SQL views. Наступний етап — завантажити sample у SQL Server, перевірити views та почати dashboard/forecasting MVP.
