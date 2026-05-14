# SQL Server Load Order

Run the SQL scripts in this order after generating the sample CSV files:

1. `sql/schema/001_create_call_center_warehouse.sql`
2. `sql/etl/001_create_staging_tables.sql`
3. `sql/etl/002_bulk_insert_sample_files.sql`
4. `sql/etl/003_load_star_schema_from_staging.sql`
5. `sql/views/001_analytics_views.sql`

Before running the bulk insert script, generate the SQL-load-ready files:

```powershell
python src\data_generation\prepare_sql_load_files.py
```

The script writes files to:

```text
data/processed/sql_load/
```

The bulk insert script uses SQLCMD mode and includes a `DataRoot` variable. Update that variable if the project folder is in a different local path.

