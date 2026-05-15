# SQL Server Load Order

## Full Raw NYC 311 Load

The full public extract is loaded into a raw landing table before the forecasting aggregate is built.

1. Run `sql/raw/001_create_raw_nyc_311.sql`.
2. Load the generated raw chunks with:

```powershell
python src\data_acquisition\load_raw_nyc_311_pyodbc.py --truncate --batch-size 10000
```

3. Run `sql/raw/003_create_raw_nyc_311_indexes.sql`.
4. Run `sql/raw/004_create_raw_nyc_311_views.sql`.

The loaded raw table is:

```text
dbo.Raw_NYC_311_Service_Requests
```

The validated full load contains 10,336,480 rows from 2023-01-01 through 2025-12-31.

The raw analytics views expose:

- `vw_Raw_NYC_311_Volume_30Min`
- `vw_Raw_NYC_311_Daily_Summary`
- `vw_Raw_NYC_311_Complaint_Type_Summary`

## Synthetic Warehouse Sample Load

Run the SQL scripts in this order after generating the sample CSV files:

1. `sql/schema/001_create_call_center_warehouse.sql`
2. `sql/etl/001_create_staging_tables.sql`
3. `sql/etl/002_bulk_insert_sample_files.sql`
4. `sql/etl/003_load_star_schema_from_staging.sql`
5. `sql/views/001_analytics_views.sql`
6. `sql/validation/001_validate_loaded_sample.sql`

Before running the bulk insert script, generate the SQL-load-ready files:

```powershell
python src\data_generation\prepare_sql_load_files.py
```

The script writes files to:

```text
data/processed/sql_load/
```

The bulk insert script uses SQLCMD mode and includes a `DataRoot` variable. Update that variable if the project folder is in a different local path.
