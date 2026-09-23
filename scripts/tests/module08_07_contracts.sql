SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Orders WHERE CustomerId=1)<>3 OR (SELECT COUNT(TotalAmount) FROM dbo.Orders WHERE CustomerId=1)<>2 OR (SELECT AVG(TotalAmount) FROM dbo.Orders WHERE CustomerId=1)<>3750000 THROW 52007,'grain and NULL',1;
IF (SELECT SUM(TotalAmount) FROM dbo.Orders WHERE Status='Paid')<>20400000 THROW 52007,'paid revenue',1;
IF (SELECT COUNT(*) FROM (SELECT CustomerId FROM dbo.Orders WHERE Status='Paid' GROUP BY CustomerId HAVING SUM(TotalAmount)>=5000000) x)<>2 THROW 52007,'having',1;
SELECT 'CONTRACT_OK';
