/*
Indexes for raw NYC 311 source table. Run after the raw load finishes.
*/

CREATE INDEX IX_Raw_NYC_311_Created_Date
    ON dbo.Raw_NYC_311_Service_Requests(Created_Date);
GO

CREATE INDEX IX_Raw_NYC_311_Complaint_Type
    ON dbo.Raw_NYC_311_Service_Requests(Complaint_Type);
GO
