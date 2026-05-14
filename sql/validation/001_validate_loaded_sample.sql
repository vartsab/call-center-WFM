/*
Validation checks for the loaded sample warehouse.
*/

SELECT 'Dim_Date' AS Object_Name, COUNT(*) AS Row_Count FROM dbo.Dim_Date
UNION ALL SELECT 'Dim_Time', COUNT(*) FROM dbo.Dim_Time
UNION ALL SELECT 'Dim_Queue', COUNT(*) FROM dbo.Dim_Queue
UNION ALL SELECT 'Dim_Agent', COUNT(*) FROM dbo.Dim_Agent
UNION ALL SELECT 'Fact_Calls', COUNT(*) FROM dbo.Fact_Calls
UNION ALL SELECT 'vw_Volume_30Min', COUNT(*) FROM dbo.vw_Volume_30Min
UNION ALL SELECT 'vw_Forecasting_Input', COUNT(*) FROM dbo.vw_Forecasting_Input
UNION ALL SELECT 'vw_Agent_Performance', COUNT(*) FROM dbo.vw_Agent_Performance;
GO

SELECT
    COUNT(*) AS Offered_Calls,
    SUM(CASE WHEN Abandoned_Flag = 0 THEN 1 ELSE 0 END) AS Answered_Calls,
    SUM(CASE WHEN Abandoned_Flag = 1 THEN 1 ELSE 0 END) AS Abandoned_Calls,
    CAST(AVG(CASE WHEN Abandoned_Flag = 0 THEN CAST(Handle_Time_Sec AS decimal(10, 2)) END) AS decimal(10, 2)) AS Avg_Answered_Handle_Time_Sec,
    CAST(AVG(CAST(SLA_Met_Flag AS decimal(10, 4))) AS decimal(10, 4)) AS SLA_Rate
FROM dbo.Fact_Calls;
GO

SELECT
    SUM(Offered_Calls) AS View_Offered_Calls,
    SUM(Answered_Calls) AS View_Answered_Calls,
    SUM(Abandoned_Calls) AS View_Abandoned_Calls
FROM dbo.vw_Volume_30Min;
GO

SELECT TOP 10
    Service_Category,
    SUM(Offered_Calls) AS Offered_Calls,
    CAST(AVG(Service_Level_Rate) AS decimal(10, 4)) AS Avg_Service_Level,
    CAST(AVG(Avg_Handle_Time_Sec) AS decimal(10, 2)) AS Avg_AHT
FROM dbo.vw_Volume_30Min
GROUP BY Service_Category
ORDER BY Offered_Calls DESC;
GO

