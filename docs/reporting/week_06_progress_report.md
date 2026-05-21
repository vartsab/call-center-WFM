# Щотижневий звіт про прогрес. Тиждень 6

## Проєкт

**Call Center Analytics and Workforce Optimization for City Service Operations**

Дата підготовки звіту: 20.05.2026  
Звітний період: 6-й тиждень активного етапу дипломного проєктування

Фокус тижня: legal scheduling, dashboard productization, deployment readiness, screenshots та validation.

## 1. Виконані завдання, досягнення та зміни у проєкті

На шостому тижні проєкт було доведено до рівня демонстраційного workforce management продукту. Основна увага була на майбутньому schedule planning, legal roster constraints, dashboard polish, screenshots та demo packaging.

- створено legal 160-agent roster optimizer на OR-Tools CP-SAT;
- додано обмеження: один shift per agent per day, максимум 5 shifts per week, 11 hours minimum rest;
- побудовано January 2026 future schedule замість historical schedule;
- додано stable synthetic agent display names при збереженні numeric `Agent_ID`; 
- перероблено Scheduling tab у Streamlit dashboard;
- додано demo launch scripts і planning pipeline script;
- додано Postgres deployment mode для dashboard і простий password gate;
- підготовлено Docker Compose stack для portfolio deployment: Streamlit, PostgreSQL, Caddy;
- розгорнуто публічний demo endpoint `https://wfm.vartsab.com:8443` із збереженням наявного VPN на port `443`;
- підготовлено screenshot set для пояснювальної записки;
- запущено pytest і підтверджено проходження тестів.

## 2. Scheduling results

Schedule optimizer працює як constrained planning scenario. Він показує, що 160-agent pool є legal roster, але не може повністю покрити 24/7 Erlang demand curve.

| Metric | Value |
| --- | --- |
| Planning horizon | 2026-01-01 to 2026-01-31 |
| Scheduled shifts | 3,427 |
| Agent pool size | 160 |
| Full-coverage roster estimate | 462 |
| Peak required agents | 189 |
| Peak scheduled agents | 160 |
| Coverage achieved | 33.54% |
| Daily shift violations | 0 |
| Weekly shift-limit violations | 0 |
| Rest violations | 0 |

## 3. Productization та demo packaging

Було додано product wrapper для локальної та публічної демонстрації:

- `scripts/run_dashboard.ps1` — запуск Streamlit dashboard;
- `scripts/run_planning_pipeline.ps1` — rebuild January 2026 forecast, staffing and schedule artifacts;
- `scripts/check_demo_readiness.ps1` — перевірка локальної demo readiness;
- `Dockerfile`, `docker-compose.yml` та `deploy/` — deployment package для VPS;
- `docs/demo_script.md` — сценарій демонстрації продукту;
- `docs/technology_choice.md` — обґрунтування використання MS SQL Server;
- `docs/deployment_status.md` — зафіксований live deployment status;
- `docs/screenshots/` — набір скріншотів dashboard для звітності.

MS SQL Server залишено як основний warehouse, оскільки він добре відповідає data engineering та BI характеру проєкту. Для portfolio deployment використано compact PostgreSQL seed database, що дозволяє зробити dashboard доступним зовні без перенесення повного 10.3M-row SQL Server warehouse.

## 4. Demo / screenshots

Підготовлено screenshots для основних сторінок продукту:

- Executive Summary;
- Historical Trends;
- Forecasting;
- Staffing;
- Scheduling;
- Agent Performance;
- Methodology / validation.

Dashboard було оптимізовано: замість завантаження granular SQL view rows у Streamlit, застосовано SQL-side aggregation для demo-friendly performance.

## 5. Тестування

Поточний test suite успішно пройдено.

| Test result | Value |
| --- | --- |
| Tests collected | 13 |
| Tests passed | 13 |

Також виконано public endpoint smoke test:

| Check | Result |
| --- | --- |
| DNS | `wfm.vartsab.com -> 46.225.121.233` |
| HTTPS URL | `https://wfm.vartsab.com:8443` |
| HTTP redirect | `http://wfm.vartsab.com` redirects to HTTPS on `8443` |
| Dashboard source | Postgres |
| Browser login | Passed |

## 6. Ризики та шляхи їх вирішення

| Ризик або проблема | Вплив |
| --- | --- |
| 160-agent pool не покриває весь demand | У dashboard є understaffing intervals. |
| Вирішення | Показувати це як planning insight: full-coverage roster estimate становить 462 agents. |

| Ризик або проблема | Вплив |
| --- | --- |
| SQL Server важко безкоштовно розгорнути у cloud | Обмежує public demo повного warehouse. |
| Вирішення | Залишити SQL Server як canonical enterprise warehouse, а для VPS використати compact PostgreSQL seed tables. |

## 7. План подальшої роботи

- оформити Week 3-6 reports у Word;
- оновити пояснювальну записку з урахуванням deployment status;
- оновити final presentation outline і deck;
- підготувати GitHub repo handoff;
- провести фінальний review dashboard, документації та repository state перед submission.

## 8. Артефакти

- `src/scheduling/agent_roster_optimizer.py`
- `app/streamlit/app.py`
- `scripts/run_dashboard.ps1`
- `scripts/run_planning_pipeline.ps1`
- `docs/demo_script.md`
- `docs/technology_choice.md`
- `docs/deployment_status.md`
- `docs/screenshots/`
- `docs/future_scheduling_summary.json`
- `Dockerfile`
- `docker-compose.yml`
- `deploy/README.md`

## 9. Висновок за тиждень

На шостому тижні проєкт було доведено до portfolio-demo рівня: dashboard працює як продуктова оболонка, scheduling module створює future legal roster, screenshots підготовлені для звітності, тестовий набір успішно проходить, а публічний VPS deployment робить продукт доступним зовні. Наступний фокус — фінальне оформлення звітів, пояснювальної записки, презентації та GitHub repository package.
