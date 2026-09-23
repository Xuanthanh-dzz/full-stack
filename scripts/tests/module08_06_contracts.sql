SET NOCOUNT ON;
IF (SELECT TRIM(Name) FROM dbo.Products WHERE ProductId=1)<>N'Keyboard Pro' THROW 52006,'trim',1;
IF (SELECT CAST((ListPrice-Price)/NULLIF(ListPrice,0)*100 AS decimal(6,2)) FROM dbo.Products WHERE ProductId=1)<>20 THROW 52006,'discount',1;
IF 1/NULLIF(0,0) IS NOT NULL THROW 52006,'zero denominator',1;
IF DATEDIFF(day,'2026-01-01T23:59:00','2026-01-02T00:01:00')<>1 THROW 52006,'date boundary',1;
DECLARE @Short varchar(1)=NULL;
IF DATALENGTH(ISNULL(@Short,'abc'))<>1 OR DATALENGTH(COALESCE(@Short,'abc'))<>3 THROW 52006,'type inference',1;
SELECT 'CONTRACT_OK';
