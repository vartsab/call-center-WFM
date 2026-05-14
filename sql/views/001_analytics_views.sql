/*
Initial analytics views for Streamlit and modeling.
*/

CREATE OR ALTER VIEW dbo.vw_Volume_30Min AS
SELECT
    d.Calendar_Date,
    t.Time_ID,
    t.Interval_Start_Time,
    t.Half_Hour_Index,
    q.Queue_ID,
    q.Queue_Name,
    q.Service_Category,
    COUNT_BIG(*) AS Offered_Calls,
    SUM(CASE WHEN f.Abandoned_Flag = 0 THEN 1 ELSE 0 END) AS Answered_Calls,
    SUM(CASE WHEN f.Abandoned_Flag = 1 THEN 1 ELSE 0 END) AS Abandoned_Calls,
    AVG(CASE WHEN f.Abandoned_Flag = 0 THEN CAST(f.Handle_Time_Sec AS decimal(10, 2)) END) AS Avg_Handle_Time_Sec,
    AVG(CAST(f.Hold_Time_Sec AS decimal(10, 2))) AS Avg_Hold_Time_Sec,
    AVG(CAST(f.SLA_Met_Flag AS decimal(10, 4))) AS Service_Level_Rate
FROM dbo.Fact_Calls AS f
INNER JOIN dbo.Dim_Date AS d
    ON f.Date_ID = d.Date_ID
INNER JOIN dbo.Dim_Time AS t
    ON f.Time_ID = t.Time_ID
INNER JOIN dbo.Dim_Queue AS q
    ON f.Queue_ID = q.Queue_ID
GROUP BY
    d.Calendar_Date,
    t.Time_ID,
    t.Interval_Start_Time,
    t.Half_Hour_Index,
    q.Queue_ID,
    q.Queue_Name,
    q.Service_Category;
GO

CREATE OR ALTER VIEW dbo.vw_Forecasting_Input AS
SELECT
    CAST(
        DATEADD(
            minute,
            t.Half_Hour_Index * 30,
            CAST(d.Calendar_Date AS datetime2(0))
        ) AS datetime2(0)
    ) AS Interval_Start_Datetime,
    t.Half_Hour_Index,
    d.Day_Of_Week,
    d.Is_Weekend,
    d.Is_Holiday,
    q.Service_Category,
    COUNT_BIG(*) AS Call_Volume,
    AVG(CASE WHEN f.Abandoned_Flag = 0 THEN CAST(f.Handle_Time_Sec AS decimal(10, 2)) END) AS Avg_Handle_Time_Sec
FROM dbo.Fact_Calls AS f
INNER JOIN dbo.Dim_Date AS d
    ON f.Date_ID = d.Date_ID
INNER JOIN dbo.Dim_Time AS t
    ON f.Time_ID = t.Time_ID
INNER JOIN dbo.Dim_Queue AS q
    ON f.Queue_ID = q.Queue_ID
GROUP BY
    d.Calendar_Date,
    t.Half_Hour_Index,
    d.Day_Of_Week,
    d.Is_Weekend,
    d.Is_Holiday,
    q.Service_Category;
GO

CREATE OR ALTER VIEW dbo.vw_Agent_Performance AS
SELECT
    a.Agent_ID,
    a.Agent_Name,
    a.Skill_Group,
    d.Calendar_Date,
    COUNT_BIG(*) AS Handled_Calls,
    AVG(CAST(f.Handle_Time_Sec AS decimal(10, 2))) AS Avg_Handle_Time_Sec,
    AVG(CAST(f.Talk_Time_Sec AS decimal(10, 2))) AS Avg_Talk_Time_Sec,
    AVG(CAST(f.ACW_Time_Sec AS decimal(10, 2))) AS Avg_ACW_Time_Sec
FROM dbo.Fact_Calls AS f
INNER JOIN dbo.Dim_Agent AS a
    ON f.Agent_ID = a.Agent_ID
INNER JOIN dbo.Dim_Date AS d
    ON f.Date_ID = d.Date_ID
WHERE f.Abandoned_Flag = 0
GROUP BY
    a.Agent_ID,
    a.Agent_Name,
    a.Skill_Group,
    d.Calendar_Date;
GO
