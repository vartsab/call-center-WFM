/*
Create staging tables for loading generated CSV files into SQL Server.
All staging columns are text so CSV import is tolerant; typed conversion
happens in the transform script.
*/

IF OBJECT_ID('dbo.Stg_Fact_Calls', 'U') IS NOT NULL DROP TABLE dbo.Stg_Fact_Calls;
IF OBJECT_ID('dbo.Stg_Dim_Agent', 'U') IS NOT NULL DROP TABLE dbo.Stg_Dim_Agent;
IF OBJECT_ID('dbo.Stg_Dim_Queue', 'U') IS NOT NULL DROP TABLE dbo.Stg_Dim_Queue;
IF OBJECT_ID('dbo.Stg_Dim_Time', 'U') IS NOT NULL DROP TABLE dbo.Stg_Dim_Time;
IF OBJECT_ID('dbo.Stg_Dim_Date', 'U') IS NOT NULL DROP TABLE dbo.Stg_Dim_Date;
GO

CREATE TABLE dbo.Stg_Dim_Date (
    Date_ID varchar(20) NULL,
    Calendar_Date varchar(30) NULL,
    Day_Of_Week varchar(20) NULL,
    Week_Of_Year varchar(10) NULL,
    Month_Number varchar(10) NULL,
    Month_Name varchar(20) NULL,
    Quarter_Number varchar(10) NULL,
    Year_Number varchar(10) NULL,
    Is_Weekend varchar(10) NULL,
    Is_Holiday varchar(10) NULL
);
GO

CREATE TABLE dbo.Stg_Dim_Time (
    Time_ID varchar(20) NULL,
    Interval_Start_Time varchar(30) NULL,
    Interval_End_Time varchar(30) NULL,
    Hour_Number varchar(10) NULL,
    Half_Hour_Index varchar(10) NULL,
    Shift_Band varchar(20) NULL
);
GO

CREATE TABLE dbo.Stg_Dim_Queue (
    Queue_ID varchar(20) NULL,
    Queue_Name varchar(150) NULL,
    Service_Category varchar(60) NULL,
    SLA_Target_Sec varchar(20) NULL,
    Target_Service_Level varchar(20) NULL,
    Active_Flag varchar(10) NULL
);
GO

CREATE TABLE dbo.Stg_Dim_Agent (
    Agent_ID varchar(20) NULL,
    Agent_Name varchar(100) NULL,
    Skill_Group varchar(60) NULL,
    Employment_Type varchar(30) NULL,
    Active_Flag varchar(10) NULL
);
GO

CREATE TABLE dbo.Stg_Fact_Calls (
    Call_ID varchar(30) NULL,
    Source_Request_ID varchar(50) NULL,
    Date_ID varchar(20) NULL,
    Time_ID varchar(20) NULL,
    Queue_ID varchar(20) NULL,
    Agent_ID varchar(20) NULL,
    Source_Created_Datetime varchar(30) NULL,
    Call_Start_Datetime varchar(30) NULL,
    Answer_Datetime varchar(30) NULL,
    End_Datetime varchar(30) NULL,
    Talk_Time_Sec varchar(20) NULL,
    Hold_Time_Sec varchar(20) NULL,
    ACW_Time_Sec varchar(20) NULL,
    Handle_Time_Sec varchar(20) NULL,
    Abandoned_Flag varchar(10) NULL,
    SLA_Met_Flag varchar(10) NULL,
    Borough varchar(40) NULL,
    Incident_Zip varchar(20) NULL,
    Source_Status varchar(40) NULL
);
GO

