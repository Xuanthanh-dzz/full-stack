SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Customers)<>2 OR NOT EXISTS(SELECT 1 FROM dbo.Customers WHERE CustomerId=1 AND FullName=N'Nguyễn An' AND Email='an@example.com') THROW 52001,'customer fixture',1;
SELECT 'CONTRACT_OK';
