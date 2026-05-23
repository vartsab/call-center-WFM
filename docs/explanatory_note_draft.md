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

Прогноз попиту на січень 2026 року використано для розрахунку staffing requirements за формулою Erlang C. Далі побудовано оптимізатор графіків на OR-Tools CP-SAT, який формує simulated roster для 160 агентів із правилами щодо тривалості зміни, перерви, максимальної кількості змін на тиждень і мінімального відпочинку між змінами. Результати виведено в інтерактивному Streamlit dashboard з вкладками для overview, demand analysis, demand forecast, capacity planning, roster simulation, service quality metrics і methods & assumptions.

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
- сформувати roster simulation за допомогою OR-Tools;
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

# Розділ 2. Дослідження ринку та технологічного середовища

## 2.1. Аналіз проблеми

У контакт-центрі основними операційними показниками є volume, answer rate, abandonment rate, average handle time, service level, occupancy та staffing coverage. Ці метрики взаємопов'язані. Зростання volume без відповідного збільшення staffing призводить до довших черг, падіння service level і більшої кількості abandoned calls. З іншого боку, надмірний staffing підвищує витрати.

Особливість workforce management полягає в тому, що рішення потрібно приймати на рівні коротких інтервалів. Денний або тижневий total volume недостатній для планування, оскільки пікове навантаження може виникати лише в окремі години. Тому у проєкті використано 30-хвилинну гранулярність, яка є типовою для contact center planning.

Класична література з управління контакт-центрами описує такі системи як соціотехнічні середовища, де поведінка клієнтів, робота агентів, черги, технології маршрутизації та цільові показники якості взаємно впливають одне на одного. Gans, Koole and Mandelbaum підкреслюють, що традиційні операційні моделі є корисними для contact center management, але мають обмеження, якщо їх застосовувати без урахування реальної поведінки клієнтів і працівників [1]. Це важливо для цього проєкту: dashboard не повинен лише показувати красиві KPI, він має пояснювати, як forecasting, staffing і scheduling впливають на service level та cost.

Сучасна практика WFM зазвичай розділяє задачу на кілька етапів: прогнозування contact volume і AHT, розрахунок required staffing, створення графіків, intraday monitoring та schedule adherence. Koole and Li описують call center workforce planning як окрему практичну та наукову область, у якій потрібно оцінювати методи не тільки за математичною якістю, а й за придатністю до реального планування [2]. Саме тому у цьому проєкті forecasting не підміняє staffing: модель машинного навчання прогнозує попит, Erlang C переводить попит у потребу в операторах, а optimizer перетворює staffing curve у schedule.

## 2.2. Огляд літератури щодо прогнозування, staffing і scheduling

У задачах call center forecasting ключовою одиницею є arrival rate або кількість звернень за короткий інтервал. Aldor-Noiman, Feigin and Mandelbaum розглядають workload forecasting як задачу прогнозування arrival process і показують, що в модель можуть включатися зовнішні фактори, наприклад події або billing cycles [3]. Для міського сервісного середовища аналогічну роль можуть мати holidays, day-of-week, seasonality, extreme weather або city events. У поточній реалізації враховано US federal holidays, cyclical time features і previous-week lag; у майбутньому модель можна розширити подіями та погодою.

Інше дослідження Aldor-Noiman et al. щодо inhomogeneous Poisson processes підкреслює, що accurate forecasting of call arrival rates є базовою передумовою efficient staffing [4]. Цей висновок безпосередньо підтримує архітектуру проєкту: спочатку формується interval-level forecasting input, потім виконується model comparison, і лише після цього результат передається в Erlang C.

Емпіричні дослідження call-center arrivals також показують, що просте припущення про незалежний Poisson process не завжди достатнє. Brown et al. аналізують реальний телефонний контакт-центр з позиції queueing science і показують важливість arrival process, waiting time, service time, abandonment і time-varying behavior для операційного моделювання [17]. Ibrahim and L'Ecuyer порівнюють fixed-effects, mixed-effects і bivariate models для call center arrivals, що підсилює ідею: модель має враховувати як intraday pattern, так і залежності між днями або типами звернень [18].

Окремий напрям літератури порівнює статистичні та machine learning approaches. Boulin у MIT thesis показує практичну цінність комбінації statistical forecasting і judgmental adjustments у sales call center context [19]. Manno et al. порівнюють deep and shallow neural networks для call center arrivals і роблять важливий для цього проєкту висновок: складніші neural approaches не завжди є автоматично кращими, а простіші моделі з продуманими features можуть бути конкурентними [20]. Тому в поточному проєкті акцент зроблено на explainable feature-based comparison, а не на демонстративно складній LSTM/Deep Learning моделі без operational benefit.

У літературі та практиці contact center planning часто використовуються:

- сезонні naive або moving-average baseline models;
- exponential smoothing та double-seasonal methods;
- regression або generalized linear models;
- Poisson-based arrival models;
- tree-based machine learning models;
- simulation and queueing models for staffing;
- mathematical optimization for scheduling.

Для магістерського інженерного проєкту важливо не просто обрати складну модель, а порівняти її з baseline. У цьому проєкті seasonal naive baseline виконує роль мінімального benchmark. Feature-based models оцінюються на holdout-періоді за MAE, RMSE і MAPE. У full-history test найкращий результат показала histogram gradient boosting model, тоді як Poisson regression, яка могла виглядати прийнятно на малому sample, показала слабший результат на повному 2023-2025 dataset.

Для staffing у contact center domain традиційно використовуються queueing models. Erlang C залишається поширеним стандартом для inbound call center planning, коли потрібно оцінити кількість агентів для заданого arrival volume, AHT, service-level target і occupancy constraint. Водночас у літературі вказується, що Erlang C має припущення та обмеження: він спрощує поведінку abandonments, повторних звернень, multiskill routing і non-stationary demand. Тому в цьому проєкті Erlang C використовується як прозорий і пояснюваний staffing layer, а не як абсолютна модель реальності.

Robbins and Medeiros порівнюють Erlang C з simulation model, де частину класичних припущень Erlang C послаблено, і показують, що у реальних contact centers така модель може не завжди точно відтворювати performance [21]. Це не означає, що Erlang C не можна використовувати; це означає, що в дипломній роботі його потрібно чесно описати як baseline queueing-theory staffing method і винести Erlang A / discrete-event simulation у future work.

Scheduling є окремою задачею operations research. Якщо forecasting відповідає на питання "скільки звернень очікується", а staffing - "скільки операторів потрібно", scheduling відповідає на питання "які конкретні люди в які зміни мають працювати". У практичних WFM-системах scheduling повинен враховувати shift templates, breaks, weekly limits, rest rules, availability, time off, skills і business hours. Koole and Li описують стандартну decomposition logic: спочатку визначають required staffing levels, потім підбирають shifts, після цього shifts assigned to agents, і далі плануються activities during scheduled work time [2]. Це прямо відповідає pipeline цього проєкту.

У більш складних contact centers scheduling переходить у multi-skill / multilingual optimization. Прикладом є ILP-модель scheduling of agents in inbound multilingual call centers, де враховуються segmentation by skills та labor law restrictions [22]. Поточна реалізація ще не має повного multi-skill routing, але обрана OR-Tools CP-SAT архітектура створює основу для такого розширення.

## 2.3. Ринковий контекст і технологічне середовище

Сучасні WFM-рішення зазвичай включають historical reporting, demand forecasting, staffing calculation, schedule generation і adherence monitoring. Комерційні платформи можуть бути дорогими та закритими для внутрішньої методологічної перевірки. У навчальному проєкті важливо створити прозору систему, де кожен крок можна пояснити, відтворити й протестувати.

Обраний підхід використовує відкриті public-service data, локальну SQL Server database, Python-модулі для моделювання та Streamlit dashboard. Такий стек дає достатню наближеність до enterprise-практики, але залишається доступним для демонстрації на локальній машині.

Публічний dataset NYC 311 є доречним для такого проєкту, тому що він містить реальні service requests з complaint type, agency, location і timestamp fields. Офіційний опис dataset зазначає, що кожен рядок містить інформацію про service request, включно з complaint type, responding agency та geographic location, але не розкриває персональні дані заявника [5]. Це дає хорошу основу для моделювання demand, однак не дає фактичних call-center metrics. Тому обрано hybrid data strategy: real public demand plus synthetic operational enrichment.

## 2.4. Аналіз конкурентів і подібних продуктів

Ринок contact center WFM є зрілим: великі платформи вже мають forecasting, scheduling, adherence і agent self-service. Це означає, що новизна навчального продукту не полягає в тому, що він першим автоматизує WFM. Його новизна полягає в прозорому, відтворюваному, explainable workflow, який демонструє весь шлях від public data до staffing decision.

Фактично проєкт можна описати як відкриту експериментальну micro-version сучасного WFM suite: він не конкурує з enterprise platforms за повнотою функцій, але відтворює їхню ключову логіку у контрольованому академічному середовищі. Саме це робить його придатним для магістерського інженерного проєкту: є working artifact, архітектура, codebase, database, model pipeline, optimization module, UI, screenshots, validation і reproducibility.

Тому цей проєкт не слід позиціонувати як фундаментальне академічне дослідження нового математичного методу. Його коректніше позиціонувати як магістерський інженерний проєкт: створення працюючого software/data product, який реалізує відомий клас задач у конкретному domain, з конкретною архітектурою, data pipeline, model comparison, staffing engine, schedule optimizer, dashboard, validation artifacts і документацією. Для інженерного проєкту новизна може полягати не у винайденні нового алгоритму, а в інтеграції, адаптації, прозорості, відтворюваності та корисності продукту для певного сценарію.

Нижче наведено порівняння з основними класами конкурентів.

| Продукт / клас | Типові можливості | Сильні сторони | Обмеження для навчального / дослідницького проєкту |
| --- | --- | --- | --- |
| NICE CXone WFM | Forecasting, schedule generation, time-off, adherence, shift bidding | Commercial WFM ecosystem, інтеграція з CXone | Закрита методологія, vendor lock-in, складність відтворення моделей |
| Genesys Cloud WFM | Forecasts, forecast-based schedules, schedule adherence, time-off management | Глибока інтеграція з contact-center platform і routing | Залежність від Genesys environment та внутрішньої data model |
| Talkdesk WFM | CVO/AHT forecasting, staffing calculation, scheduling, intraday insights | Документація чітко описує workflow forecast -> staffing -> schedule | Методологія моделювання частково закрита, продукт потребує платформи Talkdesk |
| Amazon Connect forecasting/capacity/scheduling | ML forecasting, capacity planning, scheduling, adherence | Cloud-native, інтеграція з AWS ecosystem, capacity planning workflows | Потребує Amazon Connect setup та хмарної інфраструктури |
| Verint WFM | Forecasting, scheduling, multichannel resource planning, employee self-service | Сильний commercial WFM та engagement layer | Комерційна платформа, складно показати внутрішню логіку студентського рішення |
| Calabrio WFM | Forecasting, optimized scheduling, intraday management, agent engagement | Сильна орієнтація на scheduling quality, agility та agent experience | Закритий commercial stack, менша прозорість алгоритмів |
| Five9 Essentials WFM | Forecasting, scheduling, real-time adherence, agent tools | Contact-center suite with WFM module and WFO context | Залежність від Five9 ecosystem |
| Spreadsheets / manual planning | Ручні forecasts, Erlang calculators, manual schedules | Дешево, зрозуміло для малого центру | Високий manual effort, слабка відтворюваність, обмежена інтеграція |

Офіційна документація конкурентів підтверджує, що ринкові продукти вирішують ту саму загальну задачу. Genesys описує WFM як інструмент для forecasting, schedule generation, adherence monitoring і time-off management [6]. NICE CXone WFM дозволяє forecast a schedule, edit it and generate it for agents [7]. Talkdesk документація прямо розділяє CVO forecasting, AHT forecasting, required staffing і scheduling inputs [8]. Amazon Connect описує forecasting, capacity planning і scheduling як workflow для того, щоб мати правильну кількість агентів у правильний час [9]. Verint і Calabrio також позиціонують WFM навколо accurate forecasting, optimized scheduling, service goals і employee experience [10], [11]. Five9 Essentials WFM підкреслює scheduling та real-time adherence як частину WFM-модуля [12].

Отже, ринкова релевантність проєкту підтверджується тим, що такі функції є стандартними для провідних contact center platforms. Водночас студентський продукт має іншу цінність:

- він є прозорим: кожен крок описано в SQL, Python або документації;
- він використовує реальний public dataset, доступний для перевірки;
- він демонструє data warehouse, forecasting, staffing і scheduling в одному pipeline;
- він не приховує modeling assumptions;
- він дає можливість порівнювати різні forecasting models і використовувати обрану модель у planning pipeline;
- він підходить для навчальної, дослідницької та prototype demonstration мети;
- він може бути адаптований для інших public-service або healthcare scenarios.

Таким чином, наявність конкурентів не зменшує цінність проєкту. Вона показує, що задача реальна, а запропонований продукт є open, explainable і reproducible аналогом enterprise-inspired workflow для навчання, демонстрації та подальших експериментів.

## 2.5. Аналіз архітектур і технологій

Для data layer використано публічний dataset NYC 311 Service Requests. Він містить реальні timestamps, complaint types, borough, statuses та інші поля, які відображають міський сервісний попит. Водночас dataset не містить call-center operational fields, тому такі поля як talk time, hold time, ACW, abandonment, SLA і agent assignment створюються синтетично.

Для database layer обрано Microsoft SQL Server. Попри те, що для безкоштовного web deployment простіше було б використати PostgreSQL або SQLite, SQL Server є доречним для інженерного проєкту, оскільки він часто використовується в корпоративній аналітиці, підтримує надійне індексування, views, batch loading і зрозумілу star schema модель. Для публічної portfolio-демонстрації додано compact PostgreSQL runtime: dashboard читає підготовлені analytical seed tables, а повний SQL Server warehouse залишається canonical data engineering layer.

Для forecasting використано scikit-learn model comparison. Моделі оцінювалися на holdout-періоді за MAE, RMSE і MAPE. Для staffing застосовано Erlang C, оскільки це стандартний математичний підхід для inbound queue planning. Для scheduling застосовано OR-Tools CP-SAT, що дозволяє явно задавати обмеження та objective function.

На відміну від багатьох commercial WFM systems, архітектура проєкту не є black-box. SQL views показують, які метрики потрапляють у dashboard. Forecasting scripts показують feature engineering та model selection. Staffing module окремо реалізує Erlang C. Scheduling module явно задає constraints. Це робить продукт придатним для академічної демонстрації, де важлива не тільки функціональність, а й пояснюваність.

## 2.6. Релевантність, новизна та подальший розвиток продукту

Релевантність продукту визначається трьома факторами.

По-перше, contact center workforce planning є реальною бізнес-проблемою: організації повинні підтримувати service level без надмірного staffing cost. По-друге, public-service organizations мають великі datasets, але не завжди мають готову WFM-аналітику. По-третє, навіть коли commercial tools існують, їх внутрішня логіка часто недоступна для навчального аналізу.

Новизна цього проєкту для навчального та демонстраційного середовища полягає в такому:

- використання повного 2023-2025 NYC 311 extract як реального demand foundation;
- synthetic enrichment, який перетворює public service requests на call-center analytical dataset;
- поєднання SQL Server warehouse, Streamlit dashboard, ML forecasting, Erlang C і OR-Tools в одному pipeline;
- порівняння моделей на full-history holdout;
- окреме розділення historical evaluation і future workforce planning;
- explicit reporting of coverage gap для constrained 160-agent scenario;
- model registry, який дозволяє додавати нові forecasting models і порівнювати їх у dashboard.
- публічний portfolio deployment через Docker Compose, PostgreSQL, Streamlit і Caddy HTTPS.

Потенційний розвиток продукту:

- додати реальні або benchmark AHT assumptions для різних queue types;
- порівняти Erlang C з Erlang A та discrete-event simulation для сценаріїв з abandonment;
- додати weather, city events і emergency indicators як exogenous forecast features;
- додати intraday re-forecasting, коли модель оновлює прогноз протягом дня;
- реалізувати skill-based multiqueue scheduling;
- додати agent-centric constraints: preferences, fairness, consecutive working days, shift bidding;
- додати scenario planning для SLA, shrinkage, roster size і hours of operation;
- додати MLflow для experiment tracking та model registry;
- розширити deployment до managed database, monitoring і scheduled backups, якщо продукт виходитиме за межі portfolio demo;
- додати automated report export для WFM manager.

## 2.7. Сучасні проблеми розробки

Під час створення подібної системи виникають кілька типових проблем:

- публічні дані не завжди містять усі операційні поля;
- великі datasets потребують продуманого loading та indexing;
- модель forecasting має бути порівняна з baseline, а не обрана інтуїтивно;
- staffing не можна напряму замінити машинним навчанням, оскільки потрібна queueing theory;
- schedule optimizer повинен враховувати людські правила, а не лише покриття demand curve;
- dashboard має бути зрозумілим для менеджера, а не тільки для розробника.

У проєкті ці проблеми вирішено через гібридну стратегію даних, SQL validation, model comparison, Erlang C calculation, simplified roster constraints та окрему Methods & Assumptions вкладку в dashboard.

## Висновки до другого розділу

У другому розділі розглянуто літературу, ринок і технологічне середовище contact center workforce management. Аналіз показує, що подібні задачі зазвичай вирішуються через послідовність forecasting, staffing, scheduling і adherence monitoring. Провідні commercial platforms підтверджують ринкову релевантність такого workflow, але їхні методології часто залишаються закритими. Запропонований продукт є релевантним як прозорий, відтворюваний і навчально-дослідницький аналог enterprise-inspired WFM workflow.

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
| Database | Microsoft SQL Server | Enterprise-inspired warehouse, views, indexing |
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

Моделі організовані як registry у функції `model_candidates()`. Це означає, що нову модель можна додати як окремий named estimator, після чого її можна включити в holdout comparison і future planning scenario. Planning pipeline має параметр `-Model`, тому прогноз, staffing та schedule можуть бути перераховані для іншої моделі без зміни архітектури.

### Staffing

Forecasted calls переводяться в required agents за Erlang C. Використано 30-хвилинний interval, target service level 80% answered within 20 seconds, maximum occupancy 85% і shrinkage 30%.

### Scheduling

Schedule optimizer використовує OR-Tools CP-SAT. Поточний future planning horizon - січень 2026 року. Оптимізатор формує simulated roster для 160 агентів. Обмеження включають:

- 8-hour shifts;
- 30-minute break after 4 hours;
- one shift per agent per day;
- maximum 5 shifts per agent per week;
- 11-hour minimum rest;
- hourly shift start options.

Сценарій із 160 агентами є constrained planning case. Він показує, що юридично коректний графік можна сформувати, але approved pool не покриває весь 24/7 demand curve.

### Dashboard

Streamlit dashboard має вкладки:

- Overview;
- Demand Analysis;
- Demand Forecast;
- Capacity Planning;
- Roster Simulation;
- Service Quality Metrics;
- Methods & Assumptions.

Dashboard читає SQL Server views, для локальної демонстрації може використовувати generated CSV artifacts, а для VPS portfolio deployment читає compact PostgreSQL seed tables. Публічна версія доступна через Caddy HTTPS із простим password gate.

## 3.6. Стратегії тестування

Перевірка виконувалася на кількох рівнях:

- SQL reconciliation між raw table, views і fact table;
- перевірка row counts після ETL;
- model evaluation на holdout-періоді;
- тестування Erlang C calculation;
- тестування holiday feature generation;
- тестування schedule optimizer constraints;
- dashboard screenshot validation для demo package;
- public deployment smoke test.

Автоматичні тести виконуються через pytest. Поточний результат: 13 tests passed.

## 3.7. Виклики у проєктуванні

Основні виклики:

- перехід від малого sample до full 10.3M-row dataset;
- продуктивне завантаження raw data в SQL Server;
- коректне пояснення synthetic operational fields;
- вибір моделі прогнозування на основі повної історії, а не sample;
- відокремлення forecast evaluation від future schedule planning;
- побудова schedule, який є simulated, але чесно показує coverage gap;
- публічне розгортання продукту без перенесення повного SQL Server warehouse.

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

![Рисунок 4.1. Overview dashboard](screenshots/01_overview.png)

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
| Scheduling | Побудовано simulated January 2026 roster |
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

Dashboard також візуалізує interval-level holdout predictions для кількох моделей. Це важливо для planning workflow, тому що різні моделі можуть мати схожу середню помилку, але по-різному поводитися у peak intervals.

### Future forecast

Future planning forecast сформовано для 2026-01-01 - 2026-01-31.

| Метрика | Значення |
| --- | ---: |
| Forecast intervals | 1,488 |
| Average predicted calls | 204.4150 |
| Peak predicted calls | 386.1923 |

![Рисунок 4.2. Demand forecast dashboard](screenshots/03_demand_forecast.png)

Додатково сформовано future model scenario comparison для всіх зареєстрованих моделей:

| Model | Average predicted calls | Peak predicted calls |
| --- | ---: | ---: |
| Random forest | 208.1176 | 448.0598 |
| Histogram gradient boosting | 204.4150 | 386.1923 |
| Gradient boosting | 199.0700 | 331.4391 |
| Ridge regression | 191.1717 | 324.4033 |
| Poisson regression | 185.3209 | 391.6900 |

Це розширює продукт від single-model forecast до model-aware planning tool: користувач може оцінити, як зміна моделі впливає на майбутній demand curve, перш ніж перераховувати staffing і schedule.

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

![Рисунок 4.3. Capacity planning dashboard](screenshots/04_capacity_planning.png)

### Scheduling results

Roster simulation scenario:

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

![Рисунок 4.4. Roster simulation dashboard](screenshots/05_roster_simulation.png)

### Dashboard results

Dashboard дає 360-degree view of call center performance:

- executive KPIs: offered calls, answered calls, abandoned calls, abandonment rate, AHT;
- historical volume trend;
- service category mix;
- forecasting output;
- staffing requirements;
- schedule coverage;
- service quality metrics;
- methodology and validation evidence.

Dashboard також має public portfolio mode: компактна Postgres database на VPS містить seed tables для основних analytical views, а Caddy публікує Streamlit через HTTPS endpoint `https://wfm.vartsab.com:8443`. Це дозволяє демонструвати продукт поза локальним комп'ютером без хостингу повного SQL Server warehouse.

Для фінальної версії документа потрібно вставити screenshots з папки `docs/screenshots`.

![Рисунок 4.5. Service quality metrics dashboard](screenshots/06_service_quality_metrics.png)

![Рисунок 4.6. Methods and assumptions dashboard](screenshots/07_methods_assumptions.png)

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
| Full SQL Server warehouse складно дешево розгорнути у cloud | Для portfolio demo створено compact PostgreSQL seed runtime |

Можливі напрями розвитку:

- додати skill-based routing constraints у schedule optimizer;
- реалізувати MLflow tracking для експериментів;
- додати monitoring, scheduled backups і managed database для довгострокового deployment;
- покращити synthetic assumptions на основі реальних call-center benchmarks;
- додати scenario planning для різних SLA, shrinkage і roster sizes;
- створити automated report export для WFM manager.

## Висновки до четвертого розділу

У четвертому розділі представлено результати реалізації. Проєкт досягнув стану working product: дані завантажені, warehouse побудований, dashboard працює, forecasting model обрана на основі метрик, staffing розраховано, schedule сформовано, а portfolio deployment доступний зовні через VPS. Основним незакритим етапом залишається фінальне ручне оформлення пояснювальної записки та презентації.

# Розділ 5. Висновки та рекомендації

У межах магістерського інженерного проєкту створено end-to-end систему для call center analytics and workforce optimization. Проєкт пройшов шлях від вибору dataset до data product, який підтримує historical reporting, forecasting, staffing calculation, schedule generation і public portfolio demonstration.

Основні результати:

- використано повний NYC 311 dataset за 2023-2025 роки;
- завантажено 10,336,480 raw records у SQL Server;
- створено full synthetic call-center warehouse з 10,336,480 fact calls;
- побудовано SQL views для dashboard і modeling;
- реалізовано Streamlit dashboard;
- проведено model comparison на holdout-періоді;
- обрано histogram gradient boosting як найкращу модель;
- додано model scenario comparison для planning forecast;
- створено January 2026 future forecast;
- розраховано Erlang C staffing requirements;
- сформовано simulated 160-agent schedule;
- створено compact PostgreSQL deployment mode;
- розгорнуто public dashboard через Docker Compose і Caddy HTTPS;
- підготовлено screenshots, demo script, methodology documents і submission checklist.

Цілі проєкту досягнуто на рівні working MVP / portfolio analytical product. Система демонструє повний predictive-to-prescriptive workflow: від історичного попиту до майбутнього плану покриття. Окремо важливо, що результат не приховує operational gap: approved 160-agent pool є юридично планованим, але не достатнім для повного покриття 24/7 required staffing curve. Це робить dashboard корисним не лише як демонстраційний інструмент, а і як planning decision support system.

Обмеження проєкту:

- 311 records є public-service demand records, а не guaranteed phone calls;
- operational metrics є synthetic;
- handle time and shrinkage assumptions не походять із реального contact center;
- schedule constraints спрощують трудове законодавство;
- public deployment використовує compact seed tables, а не повний SQL Server warehouse;
- dashboard має portfolio-grade hardening, але не є hosted SaaS із SLA, monitoring і backup policy.

Рекомендації:

- використовувати систему як demonstrator для workforce planning logic;
- у фінальній презентації чітко розділяти real public demand і synthetic operational enrichment;
- показувати forecasting, staffing і scheduling як послідовний decision pipeline;
- підкреслити, що service level є queue/staffing metric, а не agent-level metric;
- розглядати MLflow або інший experiment tracking layer як optional future improvement після завершення основного submission package;
- перед широким поширенням portfolio link змінити demo password і визначити, чи потрібен uptime monitoring.

## Бібліографія

1. Gans, N., Koole, G., Mandelbaum, A. Telephone Call Centers: Tutorial, Review, and Research Prospects. Manufacturing & Service Operations Management, 2003. https://doi.org/10.1287/msom.5.2.79.16071
2. Koole, G. M., Li, S. A Practice-Oriented Overview of Call Center Workforce Planning. Stochastic Systems, 2023. https://doi.org/10.1287/stsy.2021.0008
3. Aldor-Noiman, S., Feigin, P. D., Mandelbaum, A. Workload forecasting for a call center: Methodology and a case study. https://arxiv.org/abs/1009.5741
4. Aldor-Noiman, S., Brown, L. D., Feigin, P. D., Mandelbaum, A., Shen, H. Forecasting time series of inhomogeneous Poisson processes with application to call center workforce management. https://arxiv.org/abs/0807.4071
5. City of New York. 311 Service Requests from 2020 to Present. https://catalog.data.gov/dataset/311-service-requests-from-2010-to-present
6. Genesys Cloud Resource Center. Workforce management overview. https://help.genesys.cloud/articles/workforce-management-
7. NICE CXone Help. Workforce Management. https://help.nicecxone.com/content/workforcemanagement/welcometoworkforcemanagement.htm
8. Talkdesk Knowledge Base. Workforce Management: Overview. https://support.talkdesk.com/hc/en-us/articles/360043948512-Workforce-Management-Overview
9. Amazon Web Services. Forecasting, capacity planning, and scheduling in Amazon Connect. https://docs.aws.amazon.com/connect/latest/adminguide/forecasting-capacity-planning-scheduling.html
10. Verint. Workforce Forecasting & Scheduling. https://www.verint.com/workforce-management-software-wfm-solutions/forecasting-and-scheduling/
11. Calabrio. Call Center Forecasting & Scheduling Software. https://www.calabrio.com/products/workforce-management/forecasting-scheduling-software/
12. Five9. Essentials Workforce Management Data Sheet. https://www.five9.com/sites/default/files/2023-09/Data_Sheet_Five9_Essentials_Workforce_Management.PDF
13. Microsoft. SQL Server documentation. https://learn.microsoft.com/sql/sql-server/
14. Streamlit documentation. https://docs.streamlit.io/
15. scikit-learn documentation. https://scikit-learn.org/stable/documentation.html
16. Google OR-Tools documentation. https://developers.google.com/optimization
17. Brown, L., Gans, N., Mandelbaum, A., Sakov, A., Shen, H., Zeltyn, S., Zhao, L. Statistical Analysis of a Telephone Call Center: A Queueing-Science Perspective. Journal of the American Statistical Association, 2005. https://doi.org/10.1198/016214504000001808
18. Ibrahim, R., L'Ecuyer, P. Forecasting Call Center Arrivals: Fixed-Effects, Mixed-Effects, and Bivariate Models. Manufacturing & Service Operations Management, 2013. https://doi.org/10.1287/msom.1120.0405
19. Boulin, J. M. Call Center Demand Forecasting: Improving Sales Calls Prediction Accuracy Through the Combination of Statistical Methods and Judgmental Forecast. MIT, 2010. http://hdl.handle.net/1721.1/59159
20. Manno, A., Rossi, F., Smriglio, S., Cerone, L. Comparing deep and shallow neural networks in forecasting call center arrivals. Soft Computing, 2022. https://doi.org/10.1007/s00500-022-07055-2
21. Robbins, T. R., Medeiros, D. J. Does the Erlang C model fit in real call centers? Winter Simulation Conference, 2010. https://pure.psu.edu/en/publications/does-the-erlang-c-model-fit-in-real-call-centers/
22. Buriol, L. S., et al. Scheduling of agents in inbound multilingual call centers. Brazilian Journal of Operations & Production Management, 2017. https://bjopm.org.br/bjopm/article/download/V14N2A11/html?inline=1

## Додатки

Рекомендовані додатки:

- SQL schema scripts;
- SQL views;
- ключові Python modules;
- model comparison table;
- Erlang C staffing summary;
- schedule optimization summary;
- dashboard screenshots.
