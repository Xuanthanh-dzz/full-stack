SET NOCOUNT ON;
INSERT dbo.Customers(Email,FullName) VALUES('test@example.com',N'Test');INSERT dbo.Products(Sku,Name) VALUES('test',N'Old');INSERT dbo.Categories(Name) VALUES(N'One'),(N'Two');INSERT dbo.ProductCategories VALUES(1,1),(1,2);
INSERT dbo.Orders(CustomerId,ShippingName,ShippingAddress) VALUES(1,N'Test',N'Original');INSERT dbo.OrderItems(OrderId,ProductId,ProductName,UnitPrice,Quantity) VALUES(1,1,N'Old',10,1);
UPDATE dbo.Products SET Name=N'New';
IF (SELECT ProductName FROM dbo.OrderItems WHERE OrderId=1)<>N'Old' OR (SELECT COUNT(*) FROM sys.foreign_keys)<>5 THROW 52014,'relations/history',1;
SELECT 'CONTRACT_OK';
