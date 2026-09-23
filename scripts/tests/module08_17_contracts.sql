SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Orders)<>10000 OR (SELECT COUNT(*) FROM dbo.Orders WHERE CustomerId=42)<>100 THROW 52017,'seed shape',1;
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Orders') AND name='IX_Orders_CustomerId_OrderedAt' AND type=2) THROW 52017,'nonclustered index',1;
IF INDEX_COL('dbo.Orders',INDEXPROPERTY(OBJECT_ID('dbo.Orders'),'IX_Orders_CustomerId_OrderedAt','IndexId'),1)<>'CustomerId' THROW 52017,'leading key',1;
SELECT 'CONTRACT_OK';
