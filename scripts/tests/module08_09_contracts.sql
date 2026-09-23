SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Customers c WHERE EXISTS(SELECT 1 FROM dbo.Orders o WHERE o.CustomerId=c.CustomerId AND o.Status='Paid'))<>2 THROW 52009,'exists',1;
IF NOT EXISTS(SELECT 1 FROM dbo.Customers c WHERE c.CustomerId=3 AND NOT EXISTS(SELECT 1 FROM dbo.Orders o WHERE o.CustomerId=c.CustomerId)) THROW 52009,'anti match',1;
IF (SELECT MAX(OrderedAt) FROM dbo.Orders WHERE CustomerId=3) IS NOT NULL THROW 52009,'empty scalar',1;
IF EXISTS(SELECT 1 WHERE 3 NOT IN(1,NULL)) THROW 52009,'NOT IN NULL',1;
SELECT 'CONTRACT_OK';
