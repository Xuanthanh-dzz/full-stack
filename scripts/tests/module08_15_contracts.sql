SET NOCOUNT ON;
IF (SELECT SUM(Quantity*UnitPrice) FROM dbo.OrderItems WHERE OrderId=1000)<>2200000 THROW 52015,'line totals',1;
UPDATE dbo.Categories SET ManagerEmail='next@example.com' WHERE CategoryId=10;
IF (SELECT COUNT(*) FROM dbo.Products p JOIN dbo.Categories c ON c.CategoryId=p.CategoryId WHERE c.ManagerEmail='next@example.com')<>2 THROW 52015,'dependency owner',1;
SELECT 'CONTRACT_OK';
