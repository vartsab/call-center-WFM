/*
Transform staging rows into the typed dimensional warehouse tables.
Execute after:
1. sql/schema/001_create_call_center_warehouse.sql
2. sql/etl/001_create_staging_tables.sql
3. sql/etl/002_bulk_insert_sample_files.sql
*/

DELETE FROM dbo.Fact_Calls;
DELETE FROM dbo.Dim_Agent;
DELETE FROM dbo.Dim_Queue;
DELETE FROM dbo.Dim_Time;
DELETE FROM dbo.Dim_Date;
GO

INSERT INTO dbo.Dim_Date (
    Date_ID,
    Calendar_Date,
    Day_Of_Week,
    Week_Of_Year,
    Month_Number,
    Month_Name,
    Quarter_Number,
    Year_Number,
    Is_Weekend,
    Is_Holiday
)
SELECT
    TRY_CONVERT(int, Date_ID),
    TRY_CONVERT(date, Calendar_Date),
    Day_Of_Week,
    TRY_CONVERT(tinyint, Week_Of_Year),
    TRY_CONVERT(tinyint, Month_Number),
    Month_Name,
    TRY_CONVERT(tinyint, Quarter_Number),
    TRY_CONVERT(smallint, Year_Number),
    TRY_CONVERT(bit, Is_Weekend),
    TRY_CONVERT(bit, Is_Holiday)
FROM dbo.Stg_Dim_Date;
GO

INSERT INTO dbo.Dim_Time (
    Time_ID,
    Interval_Start_Time,
    Interval_End_Time,
    Hour_Number,
    Half_Hour_Index,
    Shift_Band
)
SELECT
    TRY_CONVERT(int, Time_ID),
    TRY_CONVERT(time(0), Interval_Start_Time),
    TRY_CONVERT(time(0), Interval_End_Time),
    TRY_CONVERT(tinyint, Hour_Number),
    TRY_CONVERT(tinyint, Half_Hour_Index),
    Shift_Band
FROM dbo.Stg_Dim_Time;
GO

INSERT INTO dbo.Dim_Queue (
    Queue_ID,
    Queue_Name,
    Service_Category,
    SLA_Target_Sec,
    Target_Service_Level,
    Active_Flag
)
SELECT
    TRY_CONVERT(int, Queue_ID),
    Queue_Name,
    Service_Category,
    TRY_CONVERT(int, SLA_Target_Sec),
    TRY_CONVERT(decimal(5, 4), Target_Service_Level),
    TRY_CONVERT(bit, Active_Flag)
FROM dbo.Stg_Dim_Queue;
GO

INSERT INTO dbo.Dim_Agent (
    Agent_ID,
    Agent_Name,
    Skill_Group,
    Employment_Type,
    Active_Flag
)
SELECT
    TRY_CONVERT(int, Agent_ID),
    Agent_Name,
    Skill_Group,
    Employment_Type,
    TRY_CONVERT(bit, Active_Flag)
FROM dbo.Stg_Dim_Agent;
GO

INSERT INTO dbo.Fact_Calls (
    Call_ID,
    Source_Request_ID,
    Date_ID,
    Time_ID,
    Queue_ID,
    Agent_ID,
    Source_Created_Datetime,
    Call_Start_Datetime,
    Answer_Datetime,
    End_Datetime,
    Talk_Time_Sec,
    Hold_Time_Sec,
    ACW_Time_Sec,
    Handle_Time_Sec,
    Abandoned_Flag,
    SLA_Met_Flag,
    Borough,
    Incident_Zip,
    Source_Status
)
SELECT
    TRY_CONVERT(bigint, Call_ID),
    NULLIF(Source_Request_ID, ''),
    TRY_CONVERT(int, Date_ID),
    TRY_CONVERT(int, Time_ID),
    TRY_CONVERT(int, Queue_ID),
    TRY_CONVERT(int, NULLIF(Agent_ID, '')),
    TRY_CONVERT(datetime2(0), Source_Created_Datetime),
    TRY_CONVERT(datetime2(0), Call_Start_Datetime),
    TRY_CONVERT(datetime2(0), NULLIF(Answer_Datetime, '')),
    TRY_CONVERT(datetime2(0), End_Datetime),
    TRY_CONVERT(int, Talk_Time_Sec),
    TRY_CONVERT(int, Hold_Time_Sec),
    TRY_CONVERT(int, ACW_Time_Sec),
    TRY_CONVERT(int, Handle_Time_Sec),
    TRY_CONVERT(bit, Abandoned_Flag),
    TRY_CONVERT(bit, SLA_Met_Flag),
    NULLIF(Borough, ''),
    NULLIF(Incident_Zip, ''),
    NULLIF(Source_Status, '')
FROM dbo.Stg_Fact_Calls;
GO

SELECT 'Dim_Date' AS Table_Name, COUNT(*) AS Row_Count FROM dbo.Dim_Date
UNION ALL SELECT 'Dim_Time', COUNT(*) FROM dbo.Dim_Time
UNION ALL SELECT 'Dim_Queue', COUNT(*) FROM dbo.Dim_Queue
UNION ALL SELECT 'Dim_Agent', COUNT(*) FROM dbo.Dim_Agent
UNION ALL SELECT 'Fact_Calls', COUNT(*) FROM dbo.Fact_Calls;
GO

