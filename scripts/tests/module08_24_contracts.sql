SET NOCOUNT ON;
IF NOT EXISTS(SELECT 1 FROM dbo.Customers WHERE CustomerId=1 AND FullName=N'Nguyễn Văn An' AND FirstName=N'Văn An' AND LastName=N'Nguyễn') THROW 52024,'backfill mapping',1;
IF (SELECT COUNT(*) FROM CommerceLab08_24_Restore.dbo.Customers)<>2 OR EXISTS(SELECT CustomerId,FullName,FirstName,LastName FROM dbo.Customers EXCEPT SELECT CustomerId,FullName,FirstName,LastName FROM CommerceLab08_24_Restore.dbo.Customers) OR EXISTS(SELECT CustomerId,FullName,FirstName,LastName FROM CommerceLab08_24_Restore.dbo.Customers EXCEPT SELECT CustomerId,FullName,FirstName,LastName FROM dbo.Customers) THROW 52024,'restored data mismatch',1;
SELECT 'CONTRACT_OK';
