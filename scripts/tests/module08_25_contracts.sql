SET NOCOUNT ON;
IF (SELECT Quantity FROM inventory.Stock WHERE ProductId=1)<>8 OR (SELECT Quantity FROM inventory.Stock WHERE ProductId=2)<>10 THROW 52025,'stock',1;
IF (SELECT COUNT(*) FROM sales.Orders)<>1 OR NOT EXISTS(SELECT 1 FROM sales.Orders WHERE Status='Pending' AND TotalAmount=2400000) THROW 52025,'order',1;
IF NOT EXISTS(SELECT 1 FROM sales.OrderItems WHERE ProductNameSnapshot=N'Keyboard Pro' AND Quantity=2 AND UnitPriceSnapshot=1200000) OR NOT EXISTS(SELECT 1 FROM billing.Payments WHERE Status='Pending' AND Amount=2400000) THROW 52025,'item/payment intent',1;
UPDATE catalog.Products SET Price=1500000,Name=N'Changed' WHERE ProductId=1;
IF (SELECT UnitPriceSnapshot FROM sales.OrderItems WHERE ProductId=1)<>1200000 THROW 52025,'snapshot survives catalog change',1;
SELECT 'CONTRACT_OK';
