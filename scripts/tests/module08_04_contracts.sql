SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM dbo.Products)<>2 OR EXISTS(SELECT 1 FROM dbo.Products WHERE Sku='MS-01') THROW 52004,'delete state',1;
IF NOT EXISTS(SELECT 1 FROM dbo.Products WHERE Sku='KB-01' AND Price=790000 AND IsActive=1) OR NOT EXISTS(SELECT 1 FROM dbo.Products WHERE Sku='MN-01' AND IsActive=0) THROW 52004,'update state',1;
UPDATE dbo.Products SET Price=1 WHERE Sku='missing';
IF @@ROWCOUNT<>0 THROW 52004,'missing update',1;
SELECT 'CONTRACT_OK';
