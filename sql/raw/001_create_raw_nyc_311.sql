/*
Raw NYC 311 staging table for multi-year source data.
*/

DROP TABLE IF EXISTS dbo.Raw_NYC_311_Service_Requests;
GO

CREATE TABLE dbo.Raw_NYC_311_Service_Requests (
    Unique_Key varchar(50) NULL,
    Created_Date varchar(40) NULL,
    Closed_Date varchar(40) NULL,
    Agency varchar(50) NULL,
    Agency_Name varchar(200) NULL,
    Complaint_Type varchar(200) NULL,
    Descriptor varchar(300) NULL,
    Location_Type varchar(200) NULL,
    Incident_Zip varchar(20) NULL,
    Incident_Address varchar(300) NULL,
    City varchar(100) NULL,
    Status varchar(80) NULL,
    Borough varchar(80) NULL,
    Latitude varchar(50) NULL,
    Longitude varchar(50) NULL
);
GO
