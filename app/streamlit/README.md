# Streamlit Dashboard

Run from the project root:

```powershell
streamlit run app\streamlit\app.py
```

The dashboard first attempts to read from SQL Server using the `CallCenterWFM` database. If `pyodbc` or SQL Server is unavailable, it falls back to the generated local CSV sample under `data/processed/`.

Optional SQL Server connection override:

```powershell
$env:CALLCENTER_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=CallCenterWFM;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
streamlit run app\streamlit\app.py
```

