SET NOCOUNT ON;
IF (SELECT is_read_committed_snapshot_on FROM sys.databases WHERE database_id=DB_ID())<>1 THROW 52020,'RCSI disabled',1;
SELECT 'CONTRACT_OK';
