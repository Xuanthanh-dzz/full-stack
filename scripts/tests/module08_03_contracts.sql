SET NOCOUNT ON;
IF (SELECT COUNT(WeightKg) FROM dbo.Products)<>1 OR (SELECT AVG(WeightKg) FROM dbo.Products)<>0.095 THROW 52003,'NULL aggregate',1;
IF NOT EXISTS(SELECT 1 FROM dbo.Products WHERE ProductId=1 AND Description=N'' AND WeightKg IS NULL) THROW 52003,'empty versus NULL',1;
DECLARE @Before binary(8)=(SELECT RowVersion FROM dbo.Products WHERE ProductId=1);
UPDATE dbo.Products SET Stock=Stock WHERE ProductId=1;
IF @Before=(SELECT RowVersion FROM dbo.Products WHERE ProductId=1) THROW 52003,'rowversion must change',1;
IF EXISTS(SELECT 1 WHERE NULL=NULL) THROW 52003,'NULL equality',1;
SELECT 'CONTRACT_OK';
