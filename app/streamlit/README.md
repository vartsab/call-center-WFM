# Streamlit Dashboard

Run from the project root:

```powershell
.\scripts\run_dashboard.ps1
```

With `-DataSource Auto`, the dashboard first attempts to read from SQL Server using the `CallCenterWFM` database. If `pyodbc` or SQL Server is unavailable, it falls back to the generated local CSV sample under `data/processed/`.

The launcher defaults to the fast generated-artifact path:

```powershell
.\scripts\run_dashboard.ps1 -DataSource Csv
```

To force SQL Server mode when rehearsing live SQL:

```powershell
.\scripts\run_dashboard.ps1 -DataSource Sql
```

For the VPS portfolio deployment, the dashboard reads compact seed tables from Postgres:

```bash
CALLCENTER_DASHBOARD_SOURCE=postgres streamlit run app/streamlit/app.py
```

The deployed Docker Compose stack sets `CALLCENTER_DASHBOARD_SOURCE=postgres`, `DATABASE_URL`, and `WFM_DEMO_PASSWORD` automatically from `deploy/env.local`. See `deploy/README.md` for the full runbook and public URL.

Before a demo, run the readiness check:

```powershell
.\scripts\check_demo_readiness.ps1 -RequireSql
```

Optional SQL Server connection override:

```powershell
$env:CALLCENTER_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=CallCenterWFM;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
.\scripts\run_dashboard.ps1
```
