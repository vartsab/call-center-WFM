/*
Initial SQL Server star schema for the capstone call center warehouse.
The schema is intentionally compact for the MVP and can be extended after
the seed dataset and synthetic generation logic stabilize.
*/

IF OBJECT_ID('dbo.Fact_Calls', 'U') IS NOT NULL DROP TABLE dbo.Fact_Calls;
IF OBJECT_ID('dbo.Dim_Agent', 'U') IS NOT NULL DROP TABLE dbo.Dim_Agent;
IF OBJECT_ID('dbo.Dim_Queue', 'U') IS NOT NULL DROP TABLE dbo.Dim_Queue;
IF OBJECT_ID('dbo.Dim_Time', 'U') IS NOT NULL DROP TABLE dbo.Dim_Time;
IF OBJECT_ID('dbo.Dim_Date', 'U') IS NOT NULL DROP TABLE dbo.Dim_Date;
GO

CREATE TABLE dbo.Dim_Date (
    Date_ID int NOT NULL PRIMARY KEY,
    Calendar_Date date NOT NULL,
    Day_Of_Week varchar(20) NOT NULL,
    Week_Of_Year tinyint NOT NULL,
    Month_Number tinyint NOT NULL,
    Month_Name varchar(20) NOT NULL,
    Quarter_Number tinyint NOT NULL,
    Year_Number smallint NOT NULL,
    Is_Weekend bit NOT NULL,
    Is_Holiday bit NOT NULL DEFAULT 0
);
GO

CREATE TABLE dbo.Dim_Time (
    Time_ID int NOT NULL PRIMARY KEY,
    Interval_Start_Time time(0) NOT NULL,
    Interval_End_Time time(0) NOT NULL,
    Hour_Number tinyint NOT NULL,
    Half_Hour_Index tinyint NOT NULL,
    Shift_Band varchar(20) NOT NULL
);
GO

CREATE TABLE dbo.Dim_Queue (
    Queue_ID int NOT NULL PRIMARY KEY,
    Queue_Name varchar(150) NOT NULL,
    Service_Category varchar(60) NOT NULL,
    SLA_Target_Sec int NOT NULL DEFAULT 20,
    Target_Service_Level decimal(5, 4) NOT NULL DEFAULT 0.8000,
    Active_Flag bit NOT NULL DEFAULT 1
);
GO

CREATE TABLE dbo.Dim_Agent (
    Agent_ID int NOT NULL PRIMARY KEY,
    Agent_Name varchar(100) NOT NULL,
    Skill_Group varchar(60) NOT NULL,
    Employment_Type varchar(30) NOT NULL,
    Active_Flag bit NOT NULL DEFAULT 1
);
GO

CREATE TABLE dbo.Fact_Calls (
    Call_ID bigint NOT NULL PRIMARY KEY,
    Source_Request_ID varchar(50) NULL,
    Date_ID int NOT NULL,
    Time_ID int NOT NULL,
    Queue_ID int NOT NULL,
    Agent_ID int NULL,
    Source_Created_Datetime datetime2(0) NOT NULL,
    Call_Start_Datetime datetime2(0) NOT NULL,
    Answer_Datetime datetime2(0) NULL,
    End_Datetime datetime2(0) NOT NULL,
    Talk_Time_Sec int NOT NULL,
    Hold_Time_Sec int NOT NULL,
    ACW_Time_Sec int NOT NULL,
    Handle_Time_Sec int NOT NULL,
    Abandoned_Flag bit NOT NULL,
    SLA_Met_Flag bit NOT NULL,
    Borough varchar(40) NULL,
    Incident_Zip varchar(20) NULL,
    Source_Status varchar(40) NULL,
    CONSTRAINT FK_Fact_Calls_Dim_Date
        FOREIGN KEY (Date_ID) REFERENCES dbo.Dim_Date(Date_ID),
    CONSTRAINT FK_Fact_Calls_Dim_Time
        FOREIGN KEY (Time_ID) REFERENCES dbo.Dim_Time(Time_ID),
    CONSTRAINT FK_Fact_Calls_Dim_Queue
        FOREIGN KEY (Queue_ID) REFERENCES dbo.Dim_Queue(Queue_ID),
    CONSTRAINT FK_Fact_Calls_Dim_Agent
        FOREIGN KEY (Agent_ID) REFERENCES dbo.Dim_Agent(Agent_ID),
    CONSTRAINT CK_Fact_Calls_NonNegative_Durations
        CHECK (
            Talk_Time_Sec >= 0
            AND Hold_Time_Sec >= 0
            AND ACW_Time_Sec >= 0
            AND Handle_Time_Sec >= 0
        )
);
GO

CREATE INDEX IX_Fact_Calls_Date_Time
    ON dbo.Fact_Calls(Date_ID, Time_ID)
    INCLUDE (Queue_ID, Handle_Time_Sec, Hold_Time_Sec, Abandoned_Flag, SLA_Met_Flag);
GO

CREATE INDEX IX_Fact_Calls_Queue_Date
    ON dbo.Fact_Calls(Queue_ID, Date_ID, Time_ID);
GO

CREATE INDEX IX_Fact_Calls_Agent_Date
    ON dbo.Fact_Calls(Agent_ID, Date_ID)
    WHERE Agent_ID IS NOT NULL;
GO

