SET NOCOUNT ON;
EXECUTE AS USER='demo_reader';
IF HAS_PERMS_BY_NAME('dbo.Products','OBJECT','SELECT')<>1 OR HAS_PERMS_BY_NAME('dbo.Products','OBJECT','DELETE')<>0 THROW 52023,'least privilege',1;
REVERT;
DECLARE @Search nvarchar(100)=N'none'' OR 1=1 --';
DECLARE @Matches TABLE(Id int);
INSERT @Matches EXEC sys.sp_executesql N'SELECT ProductId FROM dbo.Products WHERE Name=@Name',N'@Name nvarchar(100)',@Name=@Search;
IF EXISTS(SELECT 1 FROM @Matches) THROW 52023,'parameter treated as syntax',1;
SELECT 'CONTRACT_OK';
