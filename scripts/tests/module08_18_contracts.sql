SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Orders WHERE CustomerId=42 AND Status='Paid')<>50 THROW 52018,'paid fixture',1;
IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Orders') AND name='IX_Orders_Paid_OrderedAt' AND has_filter=1) THROW 52018,'filtered metadata',1;
IF NOT EXISTS(SELECT 1 FROM sys.index_columns ic JOIN sys.indexes i ON i.object_id=ic.object_id AND i.index_id=ic.index_id JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id WHERE i.name='IX_Orders_Customer_Status_OrderedAt' AND c.name='TotalAmount' AND ic.is_included_column=1) THROW 52018,'included column',1;
SELECT 'CONTRACT_OK';
