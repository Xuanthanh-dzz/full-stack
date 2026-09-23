SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Customers c JOIN dbo.Orders o ON o.CustomerId=c.CustomerId)<>3 THROW 52008,'inner count',1;
IF (SELECT COUNT(*) FROM dbo.Customers c LEFT JOIN dbo.Orders o ON o.CustomerId=c.CustomerId)<>4 THROW 52008,'left count',1;
IF (SELECT COUNT(*) FROM dbo.Customers CROSS JOIN dbo.Products)<>6 THROW 52008,'cross count',1;
IF (SELECT COUNT(*) FROM dbo.Customers c LEFT JOIN dbo.Orders o ON o.CustomerId=c.CustomerId AND o.Status='Paid')<>3 OR (SELECT COUNT(*) FROM dbo.Customers c LEFT JOIN dbo.Orders o ON o.CustomerId=c.CustomerId WHERE o.Status='Paid')<>2 THROW 52008,'ON versus WHERE',1;
DECLARE @A TABLE(Id int);DECLARE @B TABLE(Id int);INSERT @A VALUES(1),(2);INSERT @B VALUES(2),(3);
IF (SELECT COUNT(*) FROM @A a FULL JOIN @B b ON a.Id=b.Id)<>3 OR (SELECT COUNT(*) FROM @A a RIGHT JOIN @B b ON a.Id=b.Id)<>2 THROW 52008,'full/right',1;
SELECT 'CONTRACT_OK';
