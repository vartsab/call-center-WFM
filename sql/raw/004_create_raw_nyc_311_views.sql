/*
Analytics views over the full raw NYC 311 landing table.
*/

CREATE OR ALTER VIEW dbo.vw_Raw_NYC_311_Volume_30Min AS
WITH typed AS (
    SELECT TRY_CONVERT(datetime2(0), Created_Date) AS Created_Datetime
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE TRY_CONVERT(datetime2(0), Created_Date) IS NOT NULL
),
intervals AS (
    SELECT
        DATEADD(
            minute,
            (DATEDIFF(minute, CAST('19000101' AS datetime2(0)), Created_Datetime) / 30) * 30,
            CAST('19000101' AS datetime2(0))
        ) AS Interval_Start_Datetime
    FROM typed
)
SELECT
    Interval_Start_Datetime,
    CAST(Interval_Start_Datetime AS date) AS Calendar_Date,
    CONVERT(char(5), CAST(Interval_Start_Datetime AS time), 108) AS Interval_Start_Time,
    FORMAT(Interval_Start_Datetime, 'HHmm') AS Time_ID,
    DATEPART(hour, Interval_Start_Datetime) * 2
        + CASE WHEN DATEPART(minute, Interval_Start_Datetime) >= 30 THEN 1 ELSE 0 END AS Half_Hour_Index,
    DATENAME(weekday, Interval_Start_Datetime) AS Day_Of_Week,
    CASE WHEN DATENAME(weekday, Interval_Start_Datetime) IN ('Saturday', 'Sunday') THEN 1 ELSE 0 END AS Is_Weekend,
    COUNT_BIG(*) AS Call_Volume
FROM intervals
GROUP BY Interval_Start_Datetime;
GO

CREATE OR ALTER VIEW dbo.vw_Raw_NYC_311_Daily_Summary AS
WITH typed AS (
    SELECT
        CAST(TRY_CONVERT(datetime2(0), Created_Date) AS date) AS Calendar_Date,
        NULLIF(Complaint_Type, '') AS Complaint_Type,
        NULLIF(Borough, '') AS Borough
    FROM dbo.Raw_NYC_311_Service_Requests
    WHERE TRY_CONVERT(datetime2(0), Created_Date) IS NOT NULL
)
SELECT
    Calendar_Date,
    COUNT_BIG(*) AS Request_Count,
    COUNT_BIG(DISTINCT Complaint_Type) AS Complaint_Type_Count,
    COUNT_BIG(DISTINCT Borough) AS Borough_Count
FROM typed
GROUP BY Calendar_Date;
GO

CREATE OR ALTER VIEW dbo.vw_Raw_NYC_311_Complaint_Type_Summary AS
SELECT
    COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified') AS Complaint_Type,
    COUNT_BIG(*) AS Request_Count
FROM dbo.Raw_NYC_311_Service_Requests
GROUP BY COALESCE(NULLIF(Complaint_Type, ''), 'Unspecified');
GO
