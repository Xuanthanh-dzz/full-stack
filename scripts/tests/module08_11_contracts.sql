SET NOCOUNT ON;
;WITH t AS(SELECT CategoryId,0 AS Depth FROM dbo.Categories WHERE CategoryId=1 UNION ALL SELECT c.CategoryId,t.Depth+1 FROM dbo.Categories c JOIN t ON c.ParentCategoryId=t.CategoryId)
SELECT CategoryId,Depth INTO #Tree FROM t OPTION(MAXRECURSION 100);
IF (SELECT COUNT(*) FROM #Tree)<>7 OR (SELECT MAX(Depth) FROM #Tree)<>2 OR (SELECT Depth FROM #Tree WHERE CategoryId=3)<>2 THROW 52011,'tree depth',1;
SELECT 'CONTRACT_OK';
