/*
Bulk load generated CSV files into staging tables.

Run this in SQLCMD mode and set DataRoot to the absolute folder that contains
the generated SQL-load-ready CSV files.

Example:
:setvar DataRoot "C:\Users\denys\OneDrive\Документи\New project 2\data\processed\sql_load"
*/

:setvar DataRoot "C:\Users\denys\OneDrive\Документи\New project 2\data\processed\sql_load"

TRUNCATE TABLE dbo.Stg_Dim_Date;
TRUNCATE TABLE dbo.Stg_Dim_Time;
TRUNCATE TABLE dbo.Stg_Dim_Queue;
TRUNCATE TABLE dbo.Stg_Dim_Agent;
TRUNCATE TABLE dbo.Stg_Fact_Calls;
GO

BULK INSERT dbo.Stg_Dim_Date
FROM '$(DataRoot)\dim_date_sample.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO

BULK INSERT dbo.Stg_Dim_Time
FROM '$(DataRoot)\dim_time_sample.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO

BULK INSERT dbo.Stg_Dim_Queue
FROM '$(DataRoot)\dim_queue_sample_sql.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO

BULK INSERT dbo.Stg_Dim_Agent
FROM '$(DataRoot)\dim_agent_sample_sql.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO

BULK INSERT dbo.Stg_Fact_Calls
FROM '$(DataRoot)\fact_calls_sample_sql.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', TABLOCK);
GO

