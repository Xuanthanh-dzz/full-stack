SET NOCOUNT ON;
IF NOT EXISTS(SELECT 1 FROM dbo.Products p JOIN dbo.OrderItems i ON i.ProductId=p.ProductId WHERE p.Price=1500000 AND p.Name=N'Keyboard Pro 2' AND i.UnitPriceSnapshot=1200000 AND i.ProductNameSnapshot=N'Keyboard Pro') THROW 52016,'historical snapshot',1;
SELECT 'CONTRACT_OK';
