# Щотижневий звіт про прогрес. Тиждень 3

## Проєкт

**Call Center Analytics and Workforce Optimization for City Service Operations**

Дата підготовки звіту: 20.05.2026  
Звітний період: 3-й тиждень активного етапу дипломного проєктування

Фокус тижня: повномасштабне отримання даних, SQL raw landing layer та підготовка бази для повного warehouse.

## 1. Виконані завдання, досягнення та зміни у проєкті

На третьому тижні проєкт перейшов від малого sample dataset до повномасштабної історичної бази даних. Основна мета етапу полягала у створенні надійного raw data layer у SQL Server, який можна використовувати для подальшого прогнозування, синтетичного збагачення та побудови аналітичного warehouse.

Виконано такі завдання:

- завантажено повний public extract NYC 311 за період з 2023-01-01 до 2025-12-31;
- створено SQL raw landing table `dbo.Raw_NYC_311_Service_Requests`;
- завантажено 10,336,480 записів у SQL Server;
- після завантаження створено індекси для прискорення запитів;
- створено raw views для 30-хвилинного попиту, daily summary та complaint-type summary;
- перевірено reconciliation між raw table та 30-хвилинним view;
- оновлено документацію щодо dataset, architecture, decision log та validation summary.

## 2. Реалізовані компоненти

Реалізовано full-history data acquisition pipeline та SQL raw layer.

- `src/data_acquisition/download_nyc_311_full.py` — завантаження повного extract через NYC Open Data API;
- `src/data_acquisition/load_raw_nyc_311_pyodbc.py` — batch load у SQL Server через pyodbc;
- `sql/raw/001_create_raw_nyc_311.sql` — створення raw landing table;
- `sql/raw/003_create_raw_nyc_311_indexes.sql` — індексація raw table;
- `sql/raw/004_create_raw_nyc_311_views.sql` — створення raw analytical views.

| Метрика | Значення |
| --- | --- |
| Raw SQL records | 10,336,480 |
| Source period | 2023-01-01 to 2025-12-31 |
| Raw 30-minute view rows | 52,603 |
| Raw 30-minute view total requests | 10,336,480 |

## 3. Методологічні рішення

Було прийнято рішення використовувати SQL Server raw landing table як стабільну основу для повного historical pipeline. Це дозволяє відокремити незмінені публічні дані від подальшого synthetic warehouse layer.

Окремо зафіксовано важливе обмеження: NYC 311 records є public-service demand records, а не guaranteed phone calls. Тому вони використовуються як реалістичний seed для попиту контакт-центру, а не як прямий запис фактичних телефонних дзвінків.

## 4. Demo / проміжна перевірка

На цьому етапі була перевірена не візуальна частина продукту, а надійність data foundation. Основний demo-result — SQL Server містить повний raw dataset, а raw views повертають узгоджені aggregate totals.

Письмовий feedback від наукового керівника до цього звіту не додавався.

## 5. Ризики та шляхи їх вирішення

| Ризик або проблема | Вплив |
| --- | --- |
| Великий обсяг даних | Повний extract містить понад 10 млн записів, що може сповільнювати локальну обробку. |
| Вирішення | Використано SQL Server raw table, batch loading та індексацію після завантаження. |

| Ризик або проблема | Вплив |
| --- | --- |
| 311 records не є прямими call-center calls | Потрібно коректно описувати природу dataset. |
| Вирішення | Формулювати систему як operational simulation seeded by real public-service demand. |

## 6. План роботи на наступний тиждень

- побудувати повний synthetic call-center warehouse на основі raw table;
- заповнити dimensions і fact table;
- створити й перевірити dashboard-ready SQL views;
- оновити Streamlit dashboard під SQL-backed дані;
- документувати synthetic operational metrics та validation outputs.

## 7. Артефакти

- `src/data_acquisition/download_nyc_311_full.py`
- `src/data_acquisition/load_raw_nyc_311_pyodbc.py`
- `sql/raw/001_create_raw_nyc_311.sql`
- `sql/raw/003_create_raw_nyc_311_indexes.sql`
- `sql/raw/004_create_raw_nyc_311_views.sql`
- `docs/full_dataset_summary.json`
- `docs/sql_validation_summary.md`

## 8. Висновок за тиждень

На третьому тижні створено повномасштабну базу історичних даних для подальшого моделювання. Це суттєво підвищило якість проєкту порівняно з початковим sample pipeline, оскільки подальші прогнозні та staffing-модулі тепер можуть спиратися на три роки реального public-service demand.
