SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Orders)<>20000 OR (SELECT COUNT(*) FROM dbo.Orders WHERE CustomerId=1)<>12000 THROW 52021,'skew fixture',1;
IF NOT EXISTS(SELECT 1 FROM dbo.Orders WHERE CustomerId=42 AND Status='Paid') THROW 52021,'empty target query',1;
IF EXISTS(SELECT 1 FROM sys.stats WHERE object_id=OBJECT_ID('dbo.Orders') AND STATS_DATE(object_id,stats_id) IS NULL) THROW 52021,'statistics missing',1;
SELECT 'CONTRACT_OK';
