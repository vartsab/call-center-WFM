/*
Load the full synthetic call-center warehouse from the raw NYC 311 table.

Approved full-load design:
- source: dbo.Raw_NYC_311_Service_Requests, 2023-2025
- grain: one synthetic call per raw 311 request
- agent pool: 160 agents
- queues: every observed NYC 311 complaint type
- call start: raw Created_Date timestamp
- operational metrics: deterministic synthetic hold, talk, ACW, abandonment, SLA, and agent assignment
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @BatchStart date;
DECLARE @BatchEnd date;
DECLARE @RowsInserted bigint;
DECLARE @TotalInserted bigint = 0;
DECLARE @ProgressMessage nvarchar(4000);

IF OBJECT_ID('dbo.Raw_NYC_311_Service_Requests', 'U') IS NULL
BEGIN
    THROW 50001, 'dbo.Raw_NYC_311_Service_Requests does not exist. Load the raw NYC 311 table first.', 1;
END;

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fact_Calls_Date_Time' AND object_id = OBJECT_ID('dbo.Fact_Calls'))
    DROP INDEX IX_Fact_Calls_Date_Time ON dbo.Fact_Calls;

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fact_Calls_Queue_Date' AND object_id = OBJECT_ID('dbo.Fact_Calls'))
    DROP INDEX IX_Fact_Calls_Queue_Date ON dbo.Fact_Calls;

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Fact_Calls_Agent_Date' AND object_id = OBJECT_ID('dbo.Fact_Calls'))
    DROP INDEX IX_Fact_Calls_Agent_Date ON dbo.Fact_Calls;

DELETE FROM dbo.Fact_Calls;
DELETE FROM dbo.Dim_Agent;
DELETE FROM dbo.Dim_Queue;
DELETE FROM dbo.Dim_Time;
DELETE FROM dbo.Dim_Date;

DECLARE @MinDate date = (
    SELECT MIN(CAST(TRY_CONVERT(datetime2(0), Created_Date) AS date))
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE TRY_CONVERT(datetime2(0), Created_Date) IS NOT NULL
);

DECLARE @MaxDate date = (
    SELECT MAX(CAST(TRY_CONVERT(datetime2(0), Created_Date) AS date))
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE TRY_CONVERT(datetime2(0), Created_Date) IS NOT NULL
);

;WITH DateRange AS (
    SELECT @MinDate AS Calendar_Date
    UNION ALL
    SELECT DATEADD(day, 1, Calendar_Date)
    FROM DateRange
    WHERE Calendar_Date < @MaxDate
),
FederalHolidays AS (
    SELECT Holiday_Date
    FROM (VALUES
        (CONVERT(date, '2023-01-02')),
        (CONVERT(date, '2023-01-16')),
        (CONVERT(date, '2023-02-20')),
        (CONVERT(date, '2023-05-29')),
        (CONVERT(date, '2023-06-19')),
        (CONVERT(date, '2023-07-04')),
        (CONVERT(date, '2023-09-04')),
        (CONVERT(date, '2023-10-09')),
        (CONVERT(date, '2023-11-10')),
        (CONVERT(date, '2023-11-23')),
        (CONVERT(date, '2023-12-25')),
        (CONVERT(date, '2024-01-01')),
        (CONVERT(date, '2024-01-15')),
        (CONVERT(date, '2024-02-19')),
        (CONVERT(date, '2024-05-27')),
        (CONVERT(date, '2024-06-19')),
        (CONVERT(date, '2024-07-04')),
        (CONVERT(date, '2024-09-02')),
        (CONVERT(date, '2024-10-14')),
        (CONVERT(date, '2024-11-11')),
        (CONVERT(date, '2024-11-28')),
        (CONVERT(date, '2024-12-25')),
        (CONVERT(date, '2025-01-01')),
        (CONVERT(date, '2025-01-20')),
        (CONVERT(date, '2025-02-17')),
        (CONVERT(date, '2025-05-26')),
        (CONVERT(date, '2025-06-19')),
        (CONVERT(date, '2025-07-04')),
        (CONVERT(date, '2025-09-01')),
        (CONVERT(date, '2025-10-13')),
        (CONVERT(date, '2025-11-11')),
        (CONVERT(date, '2025-11-27')),
        (CONVERT(date, '2025-12-25'))
    ) AS Holidays(Holiday_Date)
)
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
    CONVERT(int, CONVERT(char(8), d.Calendar_Date, 112)) AS Date_ID,
    d.Calendar_Date,
    DATENAME(weekday, d.Calendar_Date) AS Day_Of_Week,
    DATEPART(isowk, d.Calendar_Date) AS Week_Of_Year,
    DATEPART(month, d.Calendar_Date) AS Month_Number,
    DATENAME(month, d.Calendar_Date) AS Month_Name,
    DATEPART(quarter, d.Calendar_Date) AS Quarter_Number,
    DATEPART(year, d.Calendar_Date) AS Year_Number,
    CASE WHEN DATENAME(weekday, d.Calendar_Date) IN ('Saturday', 'Sunday') THEN 1 ELSE 0 END AS Is_Weekend,
    CASE WHEN h.Holiday_Date IS NULL THEN 0 ELSE 1 END AS Is_Holiday
FROM DateRange AS d
LEFT JOIN FederalHolidays AS h
    ON d.Calendar_Date = h.Holiday_Date
OPTION (MAXRECURSION 0);

;WITH Numbers AS (
    SELECT 0 AS Half_Hour_Index
    UNION ALL
    SELECT Half_Hour_Index + 1
    FROM Numbers
    WHERE Half_Hour_Index < 47
),
Times AS (
    SELECT
        Half_Hour_Index,
        DATEADD(minute, Half_Hour_Index * 30, CAST('20000101' AS datetime2(0))) AS Start_Datetime
    FROM Numbers
)
INSERT INTO dbo.Dim_Time (
    Time_ID,
    Interval_Start_Time,
    Interval_End_Time,
    Hour_Number,
    Half_Hour_Index,
    Shift_Band
)
SELECT
    DATEPART(hour, Start_Datetime) * 100 + DATEPART(minute, Start_Datetime) AS Time_ID,
    CAST(Start_Datetime AS time(0)) AS Interval_Start_Time,
    CAST(DATEADD(minute, 30, Start_Datetime) AS time(0)) AS Interval_End_Time,
    DATEPART(hour, Start_Datetime) AS Hour_Number,
    Half_Hour_Index,
    CASE
        WHEN DATEPART(hour, Start_Datetime) >= 6 AND DATEPART(hour, Start_Datetime) < 12 THEN 'Morning'
        WHEN DATEPART(hour, Start_Datetime) >= 12 AND DATEPART(hour, Start_Datetime) < 18 THEN 'Afternoon'
        WHEN DATEPART(hour, Start_Datetime) >= 18 AND DATEPART(hour, Start_Datetime) < 22 THEN 'Evening'
        ELSE 'Overnight'
    END AS Shift_Band
FROM Times
OPTION (MAXRECURSION 0);

;WITH QueueNames AS (
    SELECT DISTINCT
        COALESCE(NULLIF(Complaint_Type, ''), 'Unknown') AS Queue_Name
    FROM dbo.Raw_NYC_311_Service_Requests
),
Classified AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY Queue_Name) AS Queue_ID,
        Queue_Name,
        CASE
            WHEN LOWER(Queue_Name) LIKE '%heat%'
                OR LOWER(Queue_Name) LIKE '%hot water%'
                OR LOWER(Queue_Name) LIKE '%noise%'
                OR LOWER(Queue_Name) LIKE '%building%'
                OR LOWER(Queue_Name) LIKE '%plumbing%'
                OR LOWER(Queue_Name) LIKE '%tenant%'
                THEN 'housing'
            WHEN LOWER(Queue_Name) LIKE '%sanitation%'
                OR LOWER(Queue_Name) LIKE '%trash%'
                OR LOWER(Queue_Name) LIKE '%dirty%'
                OR LOWER(Queue_Name) LIKE '%missed collection%'
                OR LOWER(Queue_Name) LIKE '%recycling%'
                THEN 'sanitation'
            WHEN LOWER(Queue_Name) LIKE '%street%'
                OR LOWER(Queue_Name) LIKE '%parking%'
                OR LOWER(Queue_Name) LIKE '%traffic%'
                OR LOWER(Queue_Name) LIKE '%vehicle%'
                OR LOWER(Queue_Name) LIKE '%highway%'
                OR LOWER(Queue_Name) LIKE '%sidewalk%'
                THEN 'transportation'
            WHEN LOWER(Queue_Name) LIKE '%police%'
                OR LOWER(Queue_Name) LIKE '%fire%'
                OR LOWER(Queue_Name) LIKE '%hazard%'
                OR LOWER(Queue_Name) LIKE '%illegal%'
                OR LOWER(Queue_Name) LIKE '%blocked%'
                THEN 'public_safety'
            ELSE 'general'
        END AS Service_Category
    FROM QueueNames
)
INSERT INTO dbo.Dim_Queue (
    Queue_ID,
    Queue_Name,
    Service_Category,
    SLA_Target_Sec,
    Target_Service_Level,
    Active_Flag
)
SELECT
    Queue_ID,
    Queue_Name,
    Service_Category,
    20 AS SLA_Target_Sec,
    CONVERT(decimal(5, 4), 0.8000) AS Target_Service_Level,
    1 AS Active_Flag
FROM Classified;

;WITH AgentNumbers AS (
    SELECT TOP (160)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS Agent_ID
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Dim_Agent (
    Agent_ID,
    Agent_Name,
    Skill_Group,
    Employment_Type,
    Active_Flag
)
SELECT
    Agent_ID,
    CONCAT('Agent ', FORMAT(Agent_ID, '000')) AS Agent_Name,
    CASE
        WHEN Agent_ID BETWEEN 1 AND 32 THEN 'housing'
        WHEN Agent_ID BETWEEN 33 AND 59 THEN 'sanitation'
        WHEN Agent_ID BETWEEN 60 AND 86 THEN 'transportation'
        WHEN Agent_ID BETWEEN 87 AND 107 THEN 'public_safety'
        ELSE 'general'
    END AS Skill_Group,
    CASE WHEN Agent_ID % 5 = 0 THEN 'Part-Time' ELSE 'Full-Time' END AS Employment_Type,
    1 AS Active_Flag
FROM AgentNumbers
ORDER BY Agent_ID;

SET @BatchStart = DATEFROMPARTS(YEAR(@MinDate), MONTH(@MinDate), 1);

WHILE @BatchStart <= @MaxDate
BEGIN
    SET @BatchEnd = DATEADD(month, 1, @BatchStart);

    ;WITH SourceRows AS (
        SELECT
            TRY_CONVERT(bigint, r.Unique_Key) AS Call_ID,
            r.Unique_Key,
            TRY_CONVERT(datetime2(0), r.Created_Date) AS Created_Datetime,
            COALESCE(NULLIF(r.Complaint_Type, ''), 'Unknown') AS Queue_Name,
            LEFT(NULLIF(r.Borough, ''), 40) AS Borough,
            LEFT(NULLIF(r.Incident_Zip, ''), 20) AS Incident_Zip,
            LEFT(NULLIF(r.Status, ''), 40) AS Source_Status
        FROM dbo.Raw_NYC_311_Service_Requests AS r
        WHERE r.Created_Date >= CONCAT(CONVERT(char(10), @BatchStart, 126), 'T00:00:00')
            AND r.Created_Date < CONCAT(CONVERT(char(10), @BatchEnd, 126), 'T00:00:00')
            AND TRY_CONVERT(datetime2(0), r.Created_Date) IS NOT NULL
            AND TRY_CONVERT(bigint, r.Unique_Key) IS NOT NULL
    ),
    JoinedRows AS (
        SELECT
            s.Call_ID,
            s.Unique_Key,
            s.Created_Datetime,
            q.Queue_ID,
            q.Service_Category,
            s.Borough,
            s.Incident_Zip,
            s.Source_Status,
            ROW_NUMBER() OVER (PARTITION BY q.Service_Category ORDER BY s.Call_ID) AS Skill_Row_Number
        FROM SourceRows AS s
        INNER JOIN dbo.Dim_Queue AS q
            ON s.Queue_Name = q.Queue_Name
    )
    INSERT INTO dbo.Fact_Calls WITH (TABLOCK) (
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
        jr.Call_ID,
        CONVERT(varchar(50), jr.Unique_Key) AS Source_Request_ID,
        CONVERT(int, CONVERT(char(8), jr.Created_Datetime, 112)) AS Date_ID,
        DATEPART(hour, jr.Created_Datetime) * 100
            + CASE WHEN DATEPART(minute, jr.Created_Datetime) >= 30 THEN 30 ELSE 0 END AS Time_ID,
        jr.Queue_ID,
        CASE
            WHEN synthetic.Abandoned_Flag = 1 THEN NULL
            WHEN jr.Service_Category = 'housing' THEN 1 + (jr.Skill_Row_Number - 1) % 32
            WHEN jr.Service_Category = 'sanitation' THEN 33 + (jr.Skill_Row_Number - 1) % 27
            WHEN jr.Service_Category = 'transportation' THEN 60 + (jr.Skill_Row_Number - 1) % 27
            WHEN jr.Service_Category = 'public_safety' THEN 87 + (jr.Skill_Row_Number - 1) % 21
            ELSE 108 + (jr.Skill_Row_Number - 1) % 53
        END AS Agent_ID,
        jr.Created_Datetime AS Source_Created_Datetime,
        jr.Created_Datetime AS Call_Start_Datetime,
        CASE
            WHEN synthetic.Abandoned_Flag = 1 THEN NULL
            ELSE DATEADD(second, synthetic.Hold_Time_Sec, jr.Created_Datetime)
        END AS Answer_Datetime,
        CASE
            WHEN synthetic.Abandoned_Flag = 1
                THEN DATEADD(second, synthetic.Hold_Time_Sec, jr.Created_Datetime)
            ELSE DATEADD(second, synthetic.Hold_Time_Sec + synthetic.Talk_Time_Sec, jr.Created_Datetime)
        END AS End_Datetime,
        synthetic.Talk_Time_Sec,
        synthetic.Hold_Time_Sec,
        synthetic.ACW_Time_Sec,
        synthetic.Talk_Time_Sec + synthetic.ACW_Time_Sec AS Handle_Time_Sec,
        synthetic.Abandoned_Flag,
        CASE WHEN synthetic.Abandoned_Flag = 0 AND synthetic.Hold_Time_Sec <= 20 THEN 1 ELSE 0 END AS SLA_Met_Flag,
        jr.Borough,
        jr.Incident_Zip,
        jr.Source_Status
    FROM JoinedRows AS jr
    CROSS APPLY (
        SELECT
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|hold1')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_Hold_1,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|hold2')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_Hold_2,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|talk1')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_Talk_1,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|talk2')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_Talk_2,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|acw1')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_ACW_1,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|acw2')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_ACW_2,
            (ABS(CAST(CHECKSUM(CONCAT(jr.Unique_Key, '|abandon')) AS bigint)) % 1000000 + 1) / 1000001.0 AS U_Abandon
    ) AS randoms
    CROSS APPLY (
        SELECT
            SQRT(-2.0 * LOG(randoms.U_Hold_1)) * COS(2.0 * PI() * randoms.U_Hold_2) AS Hold_Normal,
            SQRT(-2.0 * LOG(randoms.U_Talk_1)) * COS(2.0 * PI() * randoms.U_Talk_2) AS Talk_Normal
    ) AS normals
    CROSS APPLY (
        SELECT
            CASE
                WHEN DATENAME(weekday, jr.Created_Datetime) NOT IN ('Saturday', 'Sunday')
                    AND DATEPART(hour, jr.Created_Datetime) BETWEEN 9 AND 16
                    THEN 55.0
                ELSE 35.0
            END AS Hold_Base,
            CASE jr.Service_Category
                WHEN 'housing' THEN 420.0
                WHEN 'sanitation' THEN 260.0
                WHEN 'transportation' THEN 330.0
                WHEN 'public_safety' THEN 300.0
                ELSE 360.0
            END AS Talk_Base
    ) AS bases
    CROSS APPLY (
        SELECT
            CAST(
                CASE
                    WHEN ROUND(EXP(LOG(bases.Hold_Base) + 0.85 * normals.Hold_Normal), 0) < 0 THEN 0
                    WHEN ROUND(EXP(LOG(bases.Hold_Base) + 0.85 * normals.Hold_Normal), 0) > 900 THEN 900
                    ELSE ROUND(EXP(LOG(bases.Hold_Base) + 0.85 * normals.Hold_Normal), 0)
                END
                AS int
            ) AS Hold_Time_Sec,
            CAST(
                CASE
                    WHEN ROUND(EXP(LOG(bases.Talk_Base) + 0.55 * normals.Talk_Normal), 0) < 45 THEN 45
                    WHEN ROUND(EXP(LOG(bases.Talk_Base) + 0.55 * normals.Talk_Normal), 0) > 2400 THEN 2400
                    ELSE ROUND(EXP(LOG(bases.Talk_Base) + 0.55 * normals.Talk_Normal), 0)
                END
                AS int
            ) AS Talk_Time_Raw,
            CAST(
                CASE
                    WHEN ROUND(-35.0 * (LOG(randoms.U_ACW_1) + LOG(randoms.U_ACW_2)), 0) < 10 THEN 10
                    WHEN ROUND(-35.0 * (LOG(randoms.U_ACW_1) + LOG(randoms.U_ACW_2)), 0) > 480 THEN 480
                    ELSE ROUND(-35.0 * (LOG(randoms.U_ACW_1) + LOG(randoms.U_ACW_2)), 0)
                END
                AS int
            ) AS ACW_Time_Raw,
            randoms.U_Abandon,
            0 AS Agent_Random
    ) AS metrics
    CROSS APPLY (
        SELECT
            CASE
                WHEN metrics.U_Abandon < CASE
                    WHEN 0.025 + metrics.Hold_Time_Sec / 1400.0 > 0.65 THEN 0.65
                    ELSE 0.025 + metrics.Hold_Time_Sec / 1400.0
                END THEN 1
                ELSE 0
            END AS Abandoned_Flag,
            metrics.Hold_Time_Sec,
            metrics.Agent_Random,
            metrics.Talk_Time_Raw,
            metrics.ACW_Time_Raw
    ) AS abandonment
    CROSS APPLY (
        SELECT
            abandonment.Abandoned_Flag,
            abandonment.Hold_Time_Sec,
            abandonment.Agent_Random,
            CASE WHEN abandonment.Abandoned_Flag = 1 THEN 0 ELSE abandonment.Talk_Time_Raw END AS Talk_Time_Sec,
            CASE WHEN abandonment.Abandoned_Flag = 1 THEN 0 ELSE abandonment.ACW_Time_Raw END AS ACW_Time_Sec
    ) AS synthetic;

    SET @RowsInserted = @@ROWCOUNT;
    SET @TotalInserted += @RowsInserted;
    SET @ProgressMessage = CONCAT(
        'Loaded synthetic calls for ',
        CONVERT(varchar(10), @BatchStart, 126),
        ': ',
        FORMAT(@RowsInserted, 'N0'),
        ' rows; cumulative ',
        FORMAT(@TotalInserted, 'N0'),
        ' rows.'
    );
    RAISERROR('%s', 10, 1, @ProgressMessage) WITH NOWAIT;

    SET @BatchStart = @BatchEnd;
END;

CREATE INDEX IX_Fact_Calls_Date_Time
    ON dbo.Fact_Calls(Date_ID, Time_ID)
    INCLUDE (Queue_ID, Handle_Time_Sec, Hold_Time_Sec, Abandoned_Flag, SLA_Met_Flag);

CREATE INDEX IX_Fact_Calls_Queue_Date
    ON dbo.Fact_Calls(Queue_ID, Date_ID, Time_ID);

CREATE INDEX IX_Fact_Calls_Agent_Date
    ON dbo.Fact_Calls(Agent_ID, Date_ID)
    WHERE Agent_ID IS NOT NULL;

SELECT 'Dim_Date' AS Table_Name, COUNT_BIG(*) AS Row_Count FROM dbo.Dim_Date
UNION ALL SELECT 'Dim_Time', COUNT_BIG(*) FROM dbo.Dim_Time
UNION ALL SELECT 'Dim_Queue', COUNT_BIG(*) FROM dbo.Dim_Queue
UNION ALL SELECT 'Dim_Agent', COUNT_BIG(*) FROM dbo.Dim_Agent
UNION ALL SELECT 'Fact_Calls', COUNT_BIG(*) FROM dbo.Fact_Calls;
