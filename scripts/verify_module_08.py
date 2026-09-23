#!/usr/bin/env python3
"""Execute explicit SQL manifests in a disposable labelled SQL Server 2025 container.

Checks runtime contracts, expected SQL errors, two-session behavior and a real
backup/restore. No longest-block heuristic and no application database target.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from verify_module_01 import FENCE, solution
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'fullstack-roadmap/08-sql-va-csdl'
SQLCMD='/opt/mssql-tools18/bin/sqlcmd'

def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def process(args,**kwargs):
    # Do not print arguments or env: credentials are passed only through env.
    return subprocess.run(args,text=True,capture_output=True,timeout=180,**kwargs)

class Server:
    def __init__(self,container):
        self.container=container
        password=os.environ.get('MODULE08_SA_PASSWORD')
        if not password:raise ValueError('Set MODULE08_SA_PASSWORD for the disposable lab container')
        self.env=os.environ|{'SQLCMDPASSWORD':password}
        inspect=process(['docker','inspect','--format','{{ index .Config.Labels "fullstack.module08.verifier" }}',container])
        if inspect.returncode or inspect.stdout.strip()!='1':raise ValueError('Refusing target: container must carry fullstack.module08.verifier=1')
        self.args=['docker','exec','-i','-e','SQLCMDPASSWORD',container,SQLCMD,'-S','localhost','-U','sa','-C','-b','-r1','-W','-h','-1','-s','|','-w','65535','-f','65001']
    def sql(self,sql,database='master',error=None,wide=False):
        args=[x for x in self.args if not (wide and x=='-W')]+(['-y','0'] if wide else [])
        r=process(args+['-d',database],env=self.env,input='SET NOCOUNT ON;\n'+sql+'\n')
        if error is None:
            if r.returncode:raise ValueError(f'SQL failed in {database}:\n{r.stdout}\n{r.stderr}')
        elif r.returncode==0 or not re.search(r'\bMsg '+str(error)+r'\b',r.stdout+r.stderr):
            raise ValueError(f'Expected SQL error {error}, got exit {r.returncode}:\n{r.stdout}\n{r.stderr}')
        return r

def rows(stdout):
    result=[]
    for line in stdout.splitlines():
        line=line.strip()
        if not line or line.startswith(('Changed database context','SQL Server','Table ','Worktable','Workfile','CPU time','(')):continue
        parts=[p.strip() for p in line.split('|')]
        parts=[format(Decimal(p).normalize(),'f') if re.fullmatch(r'-?\d+(\.\d+)?',p) else p for p in parts]
        result.append('|'.join(parts))
    return result

# These are hand-derived semantic rows, not golden files captured from the run.
EXPECTED={
1:['1|Nguyễn An|an@example.com','2|Trần Bình|binh@example.com'],
3:['1|Bàn phím cơ|1299000|NULL|NULL|','Bàn phím cơ|','Chuột không dây|(chưa có mô tả)'],
4:['750000|790000','2|MS-01','1|KB-01|Bàn phím|790000|1','3|MN-01|Màn hình|5200000|0'],
5:['8|Mechanical Keyboard C|2200000|2026-01-08 00:00:00','2|Mechanical Keyboard B|1800000|2026-01-02 00:00:00','1|Mechanical Keyboard A|1200000|2026-01-01 00:00:00','4|Gaming Mouse|900000','5|4K Monitor|6500000','6|USB Hub|400000'],
7:['1|3|2|7500000|3750000|3000000|4500000','2|2|2|14000000|7000000|2000000|12000000','3|1|1|900000|900000|900000|900000','2|12000000','1|7500000','2026|1|3|19500000','2026|2|3|2900000'],
8:['101|An|Paid','102|An|Pending','103|Bình|Paid','3|Chi|NULL|NULL','Chi|Mouse'],
9:['1|An','2|Bình','3|Chi','103|2|9000000','1|An|2026-02-01','2|Bình|2026-02-10','3|Chi|NULL'],
10:['COMMON-01','A-01','A-02','B-01','B-02'],
11:['1|NULL|Electronics|0|Electronics','3|2|Laptop|2|Electronics > Computer > Laptop','1|3000000','2|5000000'],
12:['101|1|2026-01-01|1000000|3|3|2|1000000|NULL','102|1|2026-01-10|3000000|1|1|1|4000000|1000000','103|1|2026-02-01|3000000|2|1|1|7000000|3000000','102|1|3000000','103|1|3000000','202|2|7000000','201|2|5000000'],
13:['1|Keyboard|1000000','101|1|3000000','102|1|1000000'],
15:['1000|an@example.com|Nguyễn An|Keyboard|Accessory|1|1200000','1000|an@example.com|Nguyễn An|Mouse|Accessory|2|500000'],
16:['Keyboard Pro 2|1500000|Keyboard Pro|1200000'],
19:['1|2','1|Pending'],20:['1|99','2|100'],22:['8760'],
23:['1|Keyboard|1000000','2|Mouse|500000'],24:['1|Nguyễn Văn An|Văn An|Nguyễn','2|Trần Bình|Bình|Trần'],
25:['1|an@example.com|Pending|2400000|Keyboard Pro|1200000|2|Pending']}
NEGATIVE={
2:[("INSERT sales.Customers(FullName,Email) VALUES(N'Duplicate','an@example.com');",2627),("INSERT catalog.Products(Sku,Name,Price) VALUES('bad',N'Bad',-1);",547),("INSERT sales.Orders(CustomerId,Status) VALUES(999,'Pending');",547)],
3:[("UPDATE dbo.Products SET Stock=NULL WHERE ProductId=1;",515)],
9:[("SELECT (SELECT CustomerId FROM dbo.Orders);",512)],
11:[("BEGIN TRAN; UPDATE dbo.Categories SET ParentCategoryId=7 WHERE CategoryId=1; WITH t AS(SELECT CategoryId FROM dbo.Categories WHERE CategoryId=1 UNION ALL SELECT c.CategoryId FROM dbo.Categories c JOIN t ON c.ParentCategoryId=t.CategoryId) SELECT CategoryId FROM t OPTION(MAXRECURSION 3); ROLLBACK;",530)],
14:[("INSERT dbo.ProductCategories VALUES(1,1);",2627),("INSERT dbo.ProductCategories VALUES(1,999);",547)],
23:[("EXECUTE AS USER='demo_reader';DELETE FROM dbo.Products;REVERT;",229)]}

def check_stdout(n,out):
    actual=rows(out)
    for wanted in EXPECTED.get(n,[]):
        if wanted not in actual:raise ValueError(f'Lesson {n:02}: missing expected result row {wanted!r}; actual={actual}')
    if n==2 and not any(x.startswith('1|Nguyễn An|Pending|') for x in actual):raise ValueError('Order/default stdout')
    if n==6:
        for prefix,suffix in [('1|Keyboard Pro|KEY|1200000|Standard|(chưa có mô tả)|','|20'),('2|Office Mouse|OFF|350000|Budget|Basic mouse|','|0'),('3|4K Monitor|4K |7200000|Premium|27-inch monitor|','|0')]:
            # sqlcmd whitespace trimming affects the three-character short code.
            prefix=prefix.replace('4K |','4K|')
            if not any(x.startswith(prefix) and x.endswith(suffix) for x in actual):raise ValueError(f'Scalar output missing {prefix}')
    if n==10 and (len(actual)!=16 or actual.count('COMMON-01')!=4):raise ValueError('Set operator multiplicity')
    if n==14 and len([x for x in actual if x.startswith('FK_')])!=5:raise ValueError('FK metadata output')
    if n in (17,18,21):
        data=[x.split('|') for x in actual if re.match(r'^\d+\|',x)]
        expected=20 if n==17 else 50 if n==18 else 13
        if len(data)!=expected:raise ValueError(f'Index/plan query {n}: expected {expected} rows, got {len(data)}')
    if n==22 and actual.count('8760')!=2:raise ValueError('SARGable counts differ')

def concurrency(server,blocks):
    db='CommerceLab08_20'
    with ThreadPoolExecutor(max_workers=2) as pool:
        # Published sessions use a 5-second overlap. Error 1205 may choose either victim.
        def session(s):return process(server.args+['-d',db],env=server.env,input='SET NOCOUNT ON;\n'+s)
        futures=[pool.submit(session,s) for s in blocks[1:]]
        results=[f.result(timeout=90) for f in futures]
        errors=[r for r in results if r.returncode]
        if len(errors)!=1 or not re.search(r'\bMsg 1205\b',errors[0].stdout+errors[0].stderr):raise ValueError('Expected exactly one deadlock victim: '+str([(r.returncode,r.stdout,r.stderr) for r in results]))
    if rows(server.sql('SELECT ProductId,Stock FROM dbo.Inventory ORDER BY ProductId;',db).stdout)!=['1|98','2|99']:raise ValueError('Deadlock rollback/survivor state')
    # Use a transaction-owned application lock as a readiness signal, not a blind sleep.
    writer="BEGIN TRAN; UPDATE dbo.Inventory SET Stock=Stock-1 WHERE ProductId=1; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'Module08WriterReady',@LockMode='Exclusive',@LockOwner='Transaction'; WAITFOR DELAY '00:00:10'; ROLLBACK;"
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(server.sql,writer,db)
        ready=False
        for _ in range(40):
            if rows(server.sql("SELECT APPLOCK_TEST('public','Module08WriterReady','Shared','Session');",db).stdout)==['0']:
                ready=True;break
            time.sleep(.1)
        if not ready:raise ValueError('RCSI writer readiness timeout')
        if rows(server.sql('SET TRANSACTION ISOLATION LEVEL READ COMMITTED; SELECT Stock FROM dbo.Inventory WHERE ProductId=1;',db).stdout)!=['98']:raise ValueError('RCSI reader saw uncommitted value')
        future.result(timeout=30)
    return ['published two-session deadlock: exactly one 1205; victim rollback and survivor state','RCSI reader sees committed version while writer is active']

def verify(server,output):
    output.mkdir(parents=True,exist_ok=True)
    identity=server.sql("SELECT CAST(SERVERPROPERTY('ProductVersion') AS varchar(50)),CAST(SERVERPROPERTY('Edition') AS varchar(100)),CAST(SERVERPROPERTY('ProductMajorVersion') AS varchar(10));").stdout
    engine=rows(identity)[0].split('|')
    if engine[-1]!='17':raise ValueError('Expected SQL Server 2025 major version 17')
    image=process(['docker','inspect','--format','{{.Image}}',server.container]).stdout.strip()
    mkdir=process(['docker','exec',server.container,'mkdir','-p','/var/opt/mssql/backup'])
    if mkdir.returncode:raise ValueError(mkdir.stderr)
    records=[]
    paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
    if len(paths)!=25:raise ValueError('Expected 25 lesson manifest')
    for n,path in enumerate(paths,1):
        sources=[m.group(3) for m in FENCE.finditer(solution(path.read_text())) if m.group(2)=='sql']
        expected=3 if n in (20,24) else 1
        if len(sources)!=expected:raise ValueError(f'{path}: SQL manifest needs {expected} blocks, got {len(sources)}')
        db=f'CommerceLab08_{n:02}'
        logs=[];errors=[]
        for source in (sources[:1] if n==20 else sources):
            r=server.sql(source);logs.append(r.stdout);errors.append(r.stderr)
        (output/f'{n:02}.stdout.txt').write_text('\n'.join(logs));(output/f'{n:02}.stderr.txt').write_text('\n'.join(errors))
        check_stdout(n,'\n'.join(logs))
        compatibility=rows(server.sql('SELECT compatibility_level FROM sys.databases WHERE database_id=DB_ID();',db).stdout)
        if compatibility!=['170']:raise ValueError(f'{db}: expected compatibility 170, got {compatibility}')
        checks=['explicit published SQL manifest executes; semantic stdout rows','database compatibility 170']
        if n==20:checks+=concurrency(server,sources)
        contract=ROOT/f'scripts/tests/module08_{n:02}_contracts.sql'
        r=server.sql(contract.read_text(),db)
        if 'CONTRACT_OK' not in rows(r.stdout):raise ValueError('Missing contract completion marker')
        checks.append('independent state, query and boundary assertions')
        for sql,code in NEGATIVE.get(n,[]):server.sql(sql,db,error=code)
        if n in NEGATIVE:checks.append(f'{len(NEGATIVE[n])} expected SQL constraint/permission/semantics errors')
        if n==25:
            checkout=sources[0].split('SET XACT_ABORT ON;',1)[1].split('\nGO',1)[0]
            for quantity,code in [('11',51002),('0',51003),('-1',51003),('NULL',51003)]:
                variant='SET XACT_ABORT ON;'+checkout.replace('DECLARE @Quantity int = 2;','DECLARE @Quantity int = '+quantity+';')
                if variant.count('DECLARE @Quantity')!=1:raise ValueError('Checkout variant manifest mismatch')
                server.sql(variant,db,error=code)
                server.sql("IF (SELECT COUNT(*) FROM sales.Orders)<>1 OR (SELECT COUNT(*) FROM sales.OrderItems)<>1 OR (SELECT COUNT(*) FROM billing.Payments)<>1 OR (SELECT Quantity FROM inventory.Stock WHERE ProductId=1)<>8 THROW 52025,'failed checkout changed state',1;",db)
            checks.append('published checkout variants: insufficient, zero, negative and NULL quantity roll back')
        if n==24:checks.append('published COPY_ONLY backup, VERIFYONLY, restore to separate database, CHECKDB and data equality')
        if n==21:
            plan=server.sql("SET STATISTICS XML ON; SELECT OrderId,CustomerId,OrderedAt,TotalAmount FROM dbo.Orders WHERE CustomerId=42 AND Status='Paid'; SET STATISTICS XML OFF;",db,wide=True)
            match=re.search(r'(<ShowPlanXML.*?</ShowPlanXML>)',plan.stdout,re.S)
            if not match:raise ValueError('Missing complete actual plan XML')
            import xml.etree.ElementTree as ET
            ET.fromstring(match.group(1))
            (output/'21-plan.txt').write_text(plan.stdout);checks.append('actual plan XML captured without pinning physical operators')
        records.append({'lesson':str(path.relative_to(ROOT)),'sql_blocks_sha256':[sha(x) for x in sources],'contract_sha256':sha(contract.read_text()),'checks':checks})
        print(f'PASS {path.name}: {len(checks)} checks',flush=True)
    labs=[]
    for path,wanted in zip(sorted((MODULE/'failure-labs').glob('*.md')),['1','1|101','3','1|5','2']):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='sql']
        if len(sources)!=1:raise ValueError('Lab source manifest mismatch')
        actual=rows(server.sql(sources[0],'tempdb').stdout)
        if actual!=[wanted]:raise ValueError(f'{path}: documented fault output mismatch {actual}')
        labs.append({'lab':str(path.relative_to(ROOT)),'source_sha256':sha(sources[0]),'documented_failure_reproduced':True})
        print(f'PASS failure reproduction: {path.name}',flush=True)
    if len(labs)!=5:raise ValueError('Expected five labs')
    return {'verified_on':str(date.today()),'engine_version':engine[0],'edition':engine[1],'image_id':image,'compatibility_level':170,'lessons':records,'failure_labs':labs}

def main():
    p=argparse.ArgumentParser();p.add_argument('--container',default=os.environ.get('MODULE08_SQL_CONTAINER','module08-v4-verifier'));p.add_argument('--samples-only',action='store_true');p.add_argument('--report',type=Path,default=Path('artifacts/module08-verification.json'));a=p.parse_args()
    report=verify(Server(a.container),a.report.parent/'module08-sql')
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not a.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('08')
if __name__=='__main__':main()
