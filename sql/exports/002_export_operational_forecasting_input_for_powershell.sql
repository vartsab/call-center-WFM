SET NOCOUNT ON;

SELECT
    CONVERT(varchar(19), Interval_Start_Datetime, 126) AS interval_start_datetime,
    CONVERT(varchar(10), CAST(Interval_Start_Datetime AS date), 126) AS calendar_date,
    Half_Hour_Index AS half_hour_index,
    Day_Of_Week AS day_of_week,
    Is_Weekend AS is_weekend,
    Is_Holiday AS is_holiday,
    Service_Category AS service_category,
    Call_Volume AS call_volume,
    CAST(Avg_Handle_Time_Sec AS decimal(10, 2)) AS avg_handle_time_sec
FROM dbo.vw_Forecasting_Input
ORDER BY Interval_Start_Datetime, Service_Category;
