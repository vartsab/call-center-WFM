# Пояснювальна записка. Робочий змістовий драфт

## Назва проєкту

**Call Center Analytics and Workforce Optimization for City Service Operations**

Пояснювальна записка до магістерського інженерного проєкту.

Цей файл є змістовим драфтом для перенесення в офіційний Word-шаблон. Форматування титульної сторінки, змісту, списку таблиць, списку рисунків, нумерації сторінок і підписів до ілюстрацій потрібно виконати у фінальному документі.

## Список скорочень

| Скорочення | Значення |
| --- | --- |
| ACW | After Call Work, час післядзвінкової обробки |
| AHT | Average Handle Time, середній час обробки звернення |
| API | Application Programming Interface |
| CP-SAT | Constraint Programming SAT Solver |
| CSV | Comma-Separated Values |
| ETL | Extract, Transform, Load |
| FTE | Full-Time Equivalent |
| KPI | Key Performance Indicator |
| MAE | Mean Absolute Error |
| MAPE | Mean Absolute Percentage Error |
| MILP | Mixed Integer Linear Programming |
| RMSE | Root Mean Squared Error |
| SLA | Service Level Agreement |
| SQL | Structured Query Language |
| WFM | Workforce Management |

## Анотація

Магістерський інженерний проєкт присвячено створенню end-to-end аналітичної системи для контакт-центру міських сервісів. Актуальність роботи пов'язана з тим, що контакт-центри мають обслуговувати змінний попит у розрізі часу доби, дня тижня, сезонності, категорій звернень і святкових періодів. Для прийняття рішень менеджеру недостатньо лише історичних звітів: необхідно прогнозувати навантаження, розраховувати потребу в операторах і формувати графік змін з урахуванням обмежень.

У роботі використано гібридну стратегію даних. Реальні публічні записи NYC 311 за 2023-2025 роки застосовано як основу для попиту, а відсутні операційні поля контакт-центру згенеровано синтетично. Дані завантажено в Microsoft SQL Server, побудовано raw landing layer, dimensional warehouse, fact table, dimension tables і SQL views для аналітики. На основі 30-хвилинної історії попиту створено feature-based forecasting pipeline з календарними, циклічними, lag та holiday features. Для прогнозування було порівняно кілька моделей машинного навчання; найкращий результат на holdout-періоді показала модель histogram gradient boosting.

Прогноз попиту на січень 2026 року використано для розрахунку staffing requirements за формулою Erlang C. Далі побудовано оптимізатор графіків на OR-Tools CP-SAT, який формує legal roster для 160 агентів із правилами щодо тривалості зміни, перерви, максимальної кількості змін на тиждень і мінімального відпочинку між змінами. Результати виведено в інтерактивному Streamlit dashboard з вкладками для executive summary, historical trends, forecasting, staffing, scheduling, agent performance і methodology.

Результатом є відтворювана локальна аналітична система, яка демонструє повний шлях від публічного набору даних до практичного workforce planning рішення.

# Розділ 1. Вступ

## 1.1. Контекст магістерського інженерного проєкту

Контакт-центри міських сервісів працюють у середовищі, де попит на звернення є нерівномірним і залежить від багатьох чинників. Кількість звернень змінюється протягом дня, між робочими та вихідними днями, у різні сезони, під час свят, а також залежно від категорії проблеми. Наприклад, звернення щодо житлових умов, транспорту, санітарії або громадської безпеки можуть мати різні часові патерни та різну тривалість обробки.

У такій операційній системі важливо не лише зберігати історію звернень, а й перетворювати її на управлінське рішення: скільки операторів потрібно в кожному 30-хвилинному інтервалі, чи виконується service level, які категорії створюють найбільше навантаження, як змінюється прогнозований попит і чи достатній поточний staffing pool.

Цей проєкт розглядає контакт-центр як інженерну систему, що поєднує data engineering, базу даних, аналітичний dashboard, прогнозування, queueing theory та operations research.

## 1.2. Постановка проблеми та актуальність теми

Основна проблема полягає в тому, що менеджер контакт-центру має планувати роботу операторів наперед, але попит на звернення є змінним і невизначеним. Якщо персоналу замало, збільшується час очікування, знижується service level, зростає abandonment і погіршується користувацький досвід. Якщо персоналу забагато, організація має зайві витрати на оплату праці.

Традиційний dashboard, який показує лише історичні KPI, не вирішує цю проблему повністю. Для workforce management потрібен ланцюг:

1. отримати історичний попит;
2. агрегувати його в операційні 30-хвилинні інтервали;
3. спрогнозувати майбутній volume;
4. перевести прогноз у required agents;
5. побудувати графік змін з урахуванням правил роботи персоналу;
6. показати результат в інтерфейсі, придатному для аналізу.

Актуальність проєкту полягає в тому, що він об'єднує ці кроки в одному відтворюваному продукті.

## 1.3. Цілі проєкту

Метою проєкту є створення аналітичної системи для call center workforce optimization, яка використовує реальні public-service demand data як основу для моделювання та формує практичні рекомендації щодо staffing і scheduling.

Основні завдання:

- отримати реалістичний історичний dataset для міських сервісних звернень;
- створити synthetic call-center metadata для полів, відсутніх у публічних даних;
- побудувати SQL Server database з raw layer, dimensional warehouse і views;
- реалізувати Streamlit dashboard для історичної та операційної аналітики;
- створити 30-хвилинний forecasting pipeline;
- порівняти моделі прогнозування та обрати модель за holdout metrics;
- розрахувати staffing requirements за Erlang C;
- сформувати legal roster за допомогою OR-Tools;
- задокументувати методологію, обмеження, результати й можливості розвитку.

## 1.4. Значущість проєкту

Практична цінність проєкту полягає в тому, що він показує, як історичні записи про звернення можуть бути перетворені на workforce planning рішення. Система не обмежується descriptive analytics, а проходить шлях до predictive та prescriptive analytics.

Для освітнього контексту проєкт демонструє поєднання кількох напрямів Data Science та Software/Data Engineering:

- data acquisition і batch loading;
- synthetic data generation;
- SQL Server modeling;
- dashboard development;
- feature engineering;
- model evaluation;
- queueing theory;
- constrained optimization;
- reproducible project documentation.

## 1.5. Структура документа

Пояснювальна записка складається з п'яти розділів. Перший розділ описує контекст, проблему, цілі та значущість проєкту. Другий розділ розглядає технологічне середовище та підходи до call center analytics і workforce management. Третій розділ описує методологію проєктування, архітектуру, стек технологій і реалізацію основних функцій. Четвертий розділ подає результати реалізації, метрики, тестування та dashboard outputs. П'ятий розділ містить висновки, обмеження та рекомендації щодо подальшого розвитку.

## Висновки до першого розділу

У першому розділі визначено проблему workforce planning для контакт-центру, сформульовано мету й завдання проєкту та обґрунтовано його практичну цінність. Проєкт позиціонується як інженерна система, що поєднує дані, прогнозування та оптимізацію для підтримки управлінських рішень.

# Розділ 2. Дослідження технологічного середовища

## 2.1. Аналіз проблеми

У контакт-центрі основними операційними показниками є volume, answer rate, abandonment rate, average handle time, service level, occupancy та staffing coverage. Ці метрики взаємопов'язані. Зростання volume без відповідного збільшення staffing призводить до довших черг, падіння service level і більшої кількості abandoned calls. З іншого боку, надмірний staffing підвищує витрати.

Особливість workforce management полягає в тому, що рішення потрібно приймати на рівні коротких інтервалів. Денний або тижневий total volume недостатній для планування, оскільки пікове навантаження може виникати лише в окремі години. Тому у проєкті використано 30-хвилинну гранулярність, яка є типовою для contact center planning.

## 2.2. Ринковий контекст і технологічне середовище

Сучасні WFM-рішення зазвичай включають historical reporting, demand forecasting, staffing calculation, schedule generation і adherence monitoring. Комерційні платформи можуть бути дорогими та закритими для внутрішньої методологічної перевірки. У навчальному проєкті важливо створити прозору систему, де кожен крок можна пояснити, відтворити й протестувати.

Обраний підхід використовує відкриті public-service data, локальну SQL Server database, Python-модулі для моделювання та Streamlit dashboard. Такий стек дає достатню наближеність до enterprise-практики, але залишається доступним для демонстрації на локальній машині.

## 2.3. Аналіз архітектур і технологій

Для data layer використано публічний dataset NYC 311 Service Requests. Він містить реальні timestamps, complaint types, borough, statuses та інші поля, які відображають міський сервісний попит. Водночас dataset не містить call-center operational fields, тому такі поля як talk time, hold time, ACW, abandonment, SLA і agent assignment створюються синтетично.

Для database layer обрано Microsoft SQL Server. Попри те, що для безкоштовного web deployment простіше було б використати PostgreSQL або SQLite, SQL Server є доречним для інженерного проєкту, оскільки він часто використовується в корпоративній аналітиці, підтримує надійне індексування, views, batch loading і зрозумілу star schema модель.

Для forecasting використано scikit-learn model comparison. Моделі оцінювалися на holdout-періоді за MAE, RMSE і MAPE. Для staffing застосовано Erlang C, оскільки це стандартний математичний підхід для inbound queue planning. Для scheduling застосовано OR-Tools CP-SAT, що дозволяє явно задавати обмеження та objective function.

## 2.4. Сучасні проблеми розробки

Під час створення подібної системи виникають кілька типових проблем:

- публічні дані не завжди містять усі операційні поля;
- великі datasets потребують продуманого loading та indexing;
- модель forecasting має бути порівняна з baseline, а не обрана інтуїтивно;
- staffing не можна напряму замінити машинним навчанням, оскільки потрібна queueing theory;
- schedule optimizer повинен враховувати людські правила, а не лише покриття demand curve;
- dashboard має бути зрозумілим для менеджера, а не тільки для розробника.

У проєкті ці проблеми вирішено через гібридну стратегію даних, SQL validation, model comparison, Erlang C calculation, legal roster constraints та окрему Methodology вкладку в dashboard.

## Висновки до другого розділу

У другому розділі розглянуто технологічне середовище contact center workforce management. Обґрунтовано використання public-service data як demand seed, SQL Server як warehouse, Python/scikit-learn для forecasting, Erlang C для staffing і OR-Tools для scheduling. Показано, що задача потребує поєднання кількох методів, а не одного ізольованого алгоритму.

# Розділ 3. Методологія проєктування

## 3.1. Вимоги до розробки

Функціональні вимоги:

- завантаження історичних 311-даних за 2023-2025 роки;
- створення raw SQL table;
- генерація synthetic operational metrics;
- побудова dimensional warehouse;
- створення SQL views для dashboard і forecasting;
- прогнозування 30-хвилинного volume;
- розрахунок staffing requirements;
- генерація future schedule;
- візуалізація результатів у Streamlit.

Нефункціональні вимоги:

- відтворюваність pipeline;
- прозора документація припущень;
- можливість локального запуску;
- достатня продуктивність для 10M+ records;
- зрозумілі validation metrics;
- розділення raw, warehouse, modeling і dashboard layers.

## 3.2. Організація розробки

Розробку було організовано поетапно:

1. формування концепції та архітектури;
2. створення sample pipeline;
3. перехід на full-history dataset;
4. SQL Server raw load та warehouse ETL;
5. dashboard MVP;
6. forecasting and model comparison;
7. Erlang C staffing;
8. OR-Tools scheduling;
9. demo packaging and documentation.

Такий підхід дозволив спочатку перевірити end-to-end path на малому dataset, а потім перейти до full-scale реалізації.

## 3.3. Обґрунтування стеку технологій

Основні технології:

| Компонент | Технологія | Причина вибору |
| --- | --- | --- |
| Data acquisition | Python | Гнучкий доступ до API та локальна обробка |
| Database | Microsoft SQL Server | Enterprise-style warehouse, views, indexing |
| Modeling | Python, scikit-learn | Швидке порівняння моделей та feature engineering |
| Staffing | Erlang C implementation | Стандартний підхід для inbound call center staffing |
| Scheduling | OR-Tools CP-SAT | Прозоре моделювання обмежень |
| Dashboard | Streamlit, Plotly | Швидка побудова інтерактивного data product |
| Testing | pytest | Автоматична перевірка ключової логіки |

## 3.4. Архітектура проєкту

Архітектура має такий логічний потік:

```text
NYC 311 public data
    -> full 2023-2025 extraction
    -> SQL Server raw landing table
    -> synthetic call-center warehouse
    -> SQL analytics views
    -> forecasting feature matrix
    -> model comparison and future forecast
    -> Erlang C staffing requirements
    -> OR-Tools schedule optimization
    -> Streamlit dashboard
```

Raw layer зберігає початкові public-service records. Warehouse layer перетворює їх на call-center analytical model. Modeling layer створює forecast і staffing requirements. Optimization layer формує schedule. Presentation layer показує результати в dashboard.

## 3.5. Особливості реалізації основних функцій

### Data acquisition

Повний extract NYC 311 за 2023-2025 роки містить 10,336,480 записів. Дані завантажено частинами, після чого вони були завантажені в SQL Server raw table `dbo.Raw_NYC_311_Service_Requests`.

### Synthetic warehouse

На основі raw table створено один synthetic call/contact для кожного 311 record. `Fact_Calls` містить 10,336,480 записів. `Dim_Date` містить 1,096 дат, `Dim_Time` - 48 30-хвилинних інтервалів, `Dim_Queue` - 217 черг, `Dim_Agent` - 160 агентів.

Synthetic metrics включають hold time, talk time, ACW, handle time, abandonment flag, SLA met flag і agent assignment. Talk time моделюється як right-skewed duration, а ймовірність abandonment зростає зі збільшенням hold time.

### Forecasting

Forecast target - кількість звернень у 30-хвилинному інтервалі. Feature matrix включає:

- cyclical half-hour features;
- cyclical weekday features;
- day of month;
- week of year;
- month;
- weekend flag;
- US federal holiday flag;
- days to nearest federal holiday;
- previous-week same-interval lag.

Було порівняно seasonal naive baseline, ridge regression, Poisson regression, gradient boosting, random forest і histogram gradient boosting. Обрано histogram gradient boosting як модель з найнижчим MAE на full-history holdout.

### Staffing

Forecasted calls переводяться в required agents за Erlang C. Використано 30-хвилинний interval, target service level 80% answered within 20 seconds, maximum occupancy 85% і shrinkage 30%.

### Scheduling

Schedule optimizer використовує OR-Tools CP-SAT. Поточний future planning horizon - січень 2026 року. Оптимізатор формує legal roster для 160 агентів. Обмеження включають:

- 8-hour shifts;
- 30-minute break after 4 hours;
- one shift per agent per day;
- maximum 5 shifts per agent per week;
- 11-hour minimum rest;
- hourly shift start options.

Сценарій із 160 агентами є constrained planning case. Він показує, що юридично коректний графік можна сформувати, але approved pool не покриває весь 24/7 demand curve.

### Dashboard

Streamlit dashboard має вкладки:

- Executive Summary;
- Historical Trends;
- Forecasting;
- Staffing;
- Scheduling;
- Agent Performance;
- Methodology.

Dashboard читає SQL Server views, а для локальної демонстрації може використовувати generated CSV artifacts.

## 3.6. Стратегії тестування

Перевірка виконувалася на кількох рівнях:

- SQL reconciliation між raw table, views і fact table;
- перевірка row counts після ETL;
- model evaluation на holdout-періоді;
- тестування Erlang C calculation;
- тестування holiday feature generation;
- тестування schedule optimizer constraints;
- dashboard screenshot validation для demo package.

Автоматичні тести виконуються через pytest. Поточний результат: 10 tests passed.

## 3.7. Виклики у проєктуванні

Основні виклики:

- перехід від малого sample до full 10.3M-row dataset;
- продуктивне завантаження raw data в SQL Server;
- коректне пояснення synthetic operational fields;
- вибір моделі прогнозування на основі повної історії, а не sample;
- відокремлення forecast evaluation від future schedule planning;
- побудова schedule, який є legal, але чесно показує coverage gap.

## Висновки до третього розділу

У третьому розділі описано методологію реалізації проєкту. Система побудована як модульний pipeline, де кожен етап має окремі входи, виходи, validation artifacts і документацію. Такий підхід робить проєкт відтворюваним і придатним для демонстрації.

# Розділ 4. Результати проєктування

## 4.1. Реалізовані функції та архітектура проєкту

У результаті реалізовано повний data product для call center workforce management. Система включає raw data load, SQL warehouse, dashboard, forecasting, staffing і schedule optimization.

Ключові результати SQL warehouse:

| Метрика | Значення |
| --- | ---: |
| Raw records | 10,336,480 |
| Fact calls | 10,336,480 |
| Dates | 1,096 |
| Time intervals | 48 |
| Queues | 217 |
| Agents | 160 |
| Answered calls | 9,527,782 |
| Abandoned calls | 808,698 |
| Abandonment rate | 7.82% |
| Average answered handle time | 532.50 sec |

Для фінальної версії документа сюди потрібно вставити screenshot `docs/screenshots/01_executive_summary.png`.

## 4.2. Етапи проєктування

Реалізація проходила через такі етапи:

| Етап | Результат |
| --- | --- |
| Concept and architecture | Сформовано problem statement, architecture і data strategy |
| Sample MVP | Побудовано перший small-data pipeline |
| Full data load | Завантажено 10,336,480 NYC 311 records |
| SQL warehouse | Створено full synthetic call-center warehouse |
| Dashboard | Реалізовано Streamlit interface |
| Forecasting | Порівняно models і обрано найкращу |
| Staffing | Розраховано Erlang C required agents |
| Scheduling | Побудовано legal January 2026 roster |
| Demo package | Підготовлено screenshots, scripts і documentation |

## 4.3. Тестування та аналіз результатів

### Forecasting results

Порівняння моделей на full-history holdout:

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Histogram gradient boosting | 34.8872 | 49.7414 | 0.2216 |
| Random forest | 35.7124 | 50.8680 | 0.2254 |
| Gradient boosting | 38.2330 | 54.0725 | 0.2420 |
| Ridge regression | 42.0608 | 59.0505 | 0.2720 |
| Poisson regression | 47.9825 | 71.4876 | 0.3055 |
| Seasonal naive baseline | 41.1254 | 57.3621 | 0.2356 |

Histogram gradient boosting було обрано через найнижчий MAE. Random forest показав близький результат, але був трохи гіршим за основною метрикою. Poisson regression, який на ранньому sample виглядав прийнятно, на повній історії показав найгірший результат серед feature-based моделей.

### Future forecast

Future planning forecast сформовано для 2026-01-01 - 2026-01-31.

| Метрика | Значення |
| --- | ---: |
| Forecast intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |

Для фінальної версії документа сюди потрібно вставити screenshot `docs/screenshots/03_forecasting.png`.

### Staffing results

Erlang C staffing calculation для січня 2026 року:

| Метрика | Значення |
| --- | ---: |
| Staffing intervals | 1,488 |
| Average base required agents | 71.7836 |
| Peak base required agents | 132 |
| Average shrinkage-adjusted agents | 103.0108 |
| Peak shrinkage-adjusted agents | 189 |
| Average expected occupancy | 0.8359 |
| Average service-level probability | 0.9167 |

Для фінальної версії документа сюди потрібно вставити screenshot `docs/screenshots/04_staffing_requirements.png`.

### Scheduling results

Legal roster scenario:

| Метрика | Значення |
| --- | ---: |
| Solver status | FEASIBLE |
| Scheduled shifts | 3,427 |
| Agent pool size | 160 |
| Full-coverage roster estimate | 462 |
| Coverage intervals | 1,488 |
| Understaffed agent-intervals | 101,875 |
| Overstaffed agent-intervals | 0 |
| Peak required agents | 189 |
| Peak scheduled agents | 160 |
| Coverage achieved | 33.54% |
| Daily shift violations | 0 |
| Weekly shift-limit violations | 0 |
| Rest violations | 0 |

Результат показує, що 160-agent roster може бути побудований без порушень правил, але він недостатній для повного покриття 24/7 попиту. Це важливий planning insight, а не помилка optimizer: система демонструє gap між approved staffing pool і required staffing curve.

Для фінальної версії документа сюди потрібно вставити screenshot `docs/screenshots/05_scheduling_coverage.png`.

### Dashboard results

Dashboard дає 360-degree view of call center performance:

- executive KPIs: offered calls, answered calls, abandoned calls, abandonment rate, AHT;
- historical volume trend;
- service category mix;
- forecasting output;
- staffing requirements;
- schedule coverage;
- agent performance;
- methodology and validation evidence.

Для фінальної версії документа потрібно вставити screenshots з папки `docs/screenshots`.

## 4.4. Шляхи вирішення труднощів і перспективи розвитку

Ключові труднощі та рішення:

| Труднощі | Рішення |
| --- | --- |
| Public 311 data не містить call-center metrics | Застосовано synthetic operational enrichment |
| Малий sample спотворював прогнозування | Перехід на full 2023-2025 dataset |
| SQL bulk loading був ненадійним у локальному середовищі | Використано pyodbc batch loader |
| Service level помилково можна сприйняти як agent metric | Метрика винесена на queue/service/staffing level |
| Historical schedule не має практичного сенсу | Побудовано future January 2026 schedule |
| 160-agent pool не покриває full demand | Dashboard явно показує coverage gap і full-coverage roster estimate |

Можливі напрями розвитку:

- додати skill-based routing constraints у schedule optimizer;
- реалізувати MLflow tracking для експериментів;
- додати PostgreSQL або cloud-friendly deployment mode;
- покращити synthetic assumptions на основі реальних call-center benchmarks;
- додати scenario planning для різних SLA, shrinkage і roster sizes;
- створити фінальну presentation-ready deployment package.

## Висновки до четвертого розділу

У четвертому розділі представлено результати реалізації. Проєкт досягнув стану working product: дані завантажені, warehouse побудований, dashboard працює, forecasting model обрана на основі метрик, staffing розраховано, schedule сформовано. Основним незакритим етапом залишається фінальне оформлення пояснювальної записки та презентації.

# Розділ 5. Висновки та рекомендації

У межах магістерського інженерного проєкту створено end-to-end систему для call center analytics and workforce optimization. Проєкт пройшов шлях від вибору dataset до локального data product, який підтримує historical reporting, forecasting, staffing calculation і schedule generation.

Основні результати:

- використано повний NYC 311 dataset за 2023-2025 роки;
- завантажено 10,336,480 raw records у SQL Server;
- створено full synthetic call-center warehouse з 10,336,480 fact calls;
- побудовано SQL views для dashboard і modeling;
- реалізовано Streamlit dashboard;
- проведено model comparison на holdout-періоді;
- обрано histogram gradient boosting як найкращу модель;
- створено January 2026 future forecast;
- розраховано Erlang C staffing requirements;
- сформовано legal 160-agent schedule;
- підготовлено screenshots, demo script, methodology documents і submission checklist.

Цілі проєкту досягнуто на рівні working MVP / local analytical product. Система демонструє повний predictive-to-prescriptive workflow: від історичного попиту до майбутнього плану покриття. Окремо важливо, що результат не приховує operational gap: approved 160-agent pool є юридично планованим, але не достатнім для повного покриття 24/7 required staffing curve. Це робить dashboard корисним не лише як демонстраційний інструмент, а і як planning decision support system.

Обмеження проєкту:

- 311 records є public-service demand records, а не guaranteed phone calls;
- operational metrics є synthetic;
- handle time and shrinkage assumptions не походять із реального contact center;
- schedule constraints спрощують трудове законодавство;
- dashboard працює як local product, а не production cloud deployment.

Рекомендації:

- використовувати систему як demonstrator для workforce planning logic;
- у фінальній презентації чітко розділяти real public demand і synthetic operational enrichment;
- показувати forecasting, staffing і scheduling як послідовний decision pipeline;
- підкреслити, що service level є queue/staffing metric, а не agent-level metric;
- розглядати MLflow або інший experiment tracking layer як optional future improvement після завершення основного submission package.

## Робоча бібліографія для фінального оформлення

Фінальна версія має містити оформлену бібліографію за вимогами програми. Мінімальний набір джерел для перевірки перед PDF-export:

- NYC Open Data. 311 Service Requests from 2020 to Present.
- Microsoft. SQL Server documentation.
- Streamlit documentation.
- scikit-learn documentation.
- Google OR-Tools documentation.
- Класичні матеріали щодо Erlang C та contact center workforce management.

## Додатки

Рекомендовані додатки:

- SQL schema scripts;
- SQL views;
- ключові Python modules;
- model comparison table;
- Erlang C staffing summary;
- schedule optimization summary;
- dashboard screenshots.
