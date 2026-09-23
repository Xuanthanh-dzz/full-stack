SET NOCOUNT ON;
IF NOT EXISTS(SELECT 1 FROM sales.Orders WHERE CustomerId=1 AND Status='Pending' AND OrderedAt IS NOT NULL) THROW 52002,'order/default',1;
IF NOT EXISTS(SELECT 1 FROM catalog.Products WHERE IsActive=1 AND Price=750000) THROW 52002,'product/default',1;
SELECT 'CONTRACT_OK';
