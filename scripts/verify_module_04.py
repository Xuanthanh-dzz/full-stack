#!/usr/bin/env python3
"""Build published net9.0/C#13 sources; check output and failure-state contracts."""
from pathlib import Path
import argparse
from datetime import date
import hashlib
import json
import os
import re
import subprocess
import tempfile
from verify_module_01 import FENCE, solution
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'fullstack-roadmap/04-csharp-co-ban'
SDK='9.0.121'
PROJECT='<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup></Project>'
FILES16=['Domain/TodoStatus.cs','Domain/TodoItem.cs','Application/ITodoRepository.cs','Application/TodoItemView.cs','Application/TodoService.cs','Infrastructure/JsonTodoRepository.cs','Program.cs']

def command(args,cwd,env,expected=0):
    r=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
    if r.returncode!=expected:raise ValueError(f'{args}: expected exit {expected}, got {r.returncode}\n{r.stdout}\n{r.stderr}')
    return r

def extract(path,w,n):
    body=solution(path.read_text());blocks=list(FENCE.finditer(body))
    sources=[m.group(3) for m in blocks if m.group(2)=='csharp']
    xml=[m.group(3) for m in blocks if m.group(2)=='xml']
    names=['Program.cs'] if n<16 else FILES16
    project='Sample.csproj'
    if n==14:
        names=['StoreBilling.Domain/Billing/InvoiceLine.cs','StoreBilling.Domain/Billing/InvoiceCalculator.cs','StoreBilling.Cli/Program.cs']
        project='StoreBilling.Cli/StoreBilling.Cli.csproj'
        if len(xml)!=2:raise ValueError('Expected two published project files')
        projects=dict(zip(['StoreBilling.Domain/StoreBilling.Domain.csproj',project],xml))
    else:projects={project:xml[0] if xml else PROJECT}
    if len(sources)!=len(names):raise ValueError(f'{path}: published file manifest mismatch')
    files=projects|dict(zip(names,sources))
    for name,content in files.items():
        f=w/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
    return project,files

def normalize(n,s):
    if n==12:
        s=re.sub(r'Created order: [a-f0-9]{32}', 'Created order: <id>',s)
        s=re.sub(r'Attempt took \d+ ms\.', 'Attempt took <ms> ms.',s)
    if n==15:s=re.sub(r'elapsed_ms=\d+(?:\.\d+)?','elapsed_ms=<ms>',s)
    return s

def verify(dotnet,configuration):
    env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1','LANG':'en_US.UTF-8','LC_ALL':'en_US.UTF-8'}
    records=[]
    paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
    if len(paths)!=16:raise ValueError('Expected 16 lessons')
    with tempfile.TemporaryDirectory(prefix='module04-') as temp:
        base=Path(temp);(base/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
        if command([dotnet,'--version'],base,env).stdout.strip()!=SDK:raise ValueError('SDK baseline mismatch')
        for n,path in enumerate(paths,1):
            w=base/f'{n:02}';w.mkdir();project,files=extract(path,w,n)
            if n==14:
                command([dotnet,'new','sln','-n','StoreBilling'],w,env)
                command([dotnet,'sln','StoreBilling.sln','add','StoreBilling.Domain/StoreBilling.Domain.csproj',project],w,env)
                target='StoreBilling.sln'
            else:target=project
            command([dotnet,'build',target,'-c',configuration,'--nologo','-warnaserror'],w,env)
            dll=w/(f'StoreBilling.Cli/bin/{configuration}/net9.0/StoreBilling.Cli.dll' if n==14 else f'bin/{configuration}/net9.0/Sample.dll')
            checks=['published source/project manifest builds with warnings as errors']
            def invoke(args=(),expected=0,extra=None):return command([dotnet,str(dll),*args],w,env|(extra or {}),expected)
            if n<16:
                r=invoke();wanted=(ROOT/f'samples/module-04/expected/{n:02}.txt').read_text()
                if n==15 and configuration=='Debug':wanted=wanted.replace('customer=l***@example.com\n','customer=l***@example.com\nDEBUG item_count=2\n')
                stderr='Reservation failed for product BOOK-CSHARP.\n' if n==12 else ''
                if normalize(n,r.stdout)!=wanted or r.stderr!=stderr:raise ValueError(f'{path}: output mismatch {r.stdout!r}, stderr {r.stderr!r}')
                checks.append('reviewed stdout oracle, expected stderr and exit; only GUID/timing normalized')
                if n==12:
                    data=(w/'orders.log').read_text()
                    if not re.fullmatch(r'[a-f0-9]{32},CUS-001,2\n',data):raise ValueError(f'Order log mismatch: {data!r}')
                    checks.append('persisted order ID/customer/quantity after compensation paths')
            else:
                verify_cli(invoke,w);checks.append('CLI add/list/done/remove across processes; invalid input, JSON, ID range and file failure preserve bytes')
            if n==2:
                for args in [('0',),('13',),('abc',),('1','-1'),('1','100000001')]:
                    r=invoke(args)
                    expected_error='Quantity must be an integer from 1 to 12.\n' if len(args)==1 else 'Unit price must be from 0 to 100000000.\n'
                    if r.stdout!=expected_error or r.stderr:raise ValueError('Invalid order input was accepted')
                checks.append('quantity/price parse and domain rejection')
            if n==8:
                expressions=[('new InventoryItem("A",1m);','CS9035'),('var x=new InventoryItem("A",1m){Sku="A"};x.Sku="B";','CS8852'),('var x=new InventoryItem("A",1m){Sku="A"};x.Stock=1;','CS0272')]
                for expression,diagnostic in expressions:
                    (w/'Negative.cs').write_text('internal static class Negative { public static void Main(){'+expression+'} }')
                    result=command([dotnet,'build',project,'-c',configuration,'--nologo','-p:StartupObject=Negative'],w,env,1)
                    if diagnostic not in result.stdout:raise ValueError(f'Missing expected compile diagnostic {diagnostic}')
                (w/'Negative.cs').unlink()
                checks.append('compiler rejects missing required, init reassignment and private setter')
            if n==14:
                source=w/'StoreBilling.Domain/Billing/InvoiceCalculator.cs';old=source.read_text()
                source.write_text(old.replace('public static class InvoiceCalculator','internal static class InvoiceCalculator'))
                result=command([dotnet,'build',target,'-c',configuration,'--nologo'],w,env,1)
                if 'CS0122' not in result.stdout:raise ValueError('Expected cross-assembly internal rejection')
                source.write_text(old)
                checks.append('internal calculator is inaccessible across real assembly boundary')
            contract=ROOT/f'scripts/tests/module04_{n:02}_contracts.cs'
            if contract.exists():
                (w/'Contracts.cs').write_text(contract.read_text())
                contract_project=PROJECT.replace('</PropertyGroup>','<StartupObject>Contracts</StartupObject><EnableDefaultCompileItems>false</EnableDefaultCompileItems></PropertyGroup>')
                excluded='Program.cs;bin/**;obj/**' if n==16 else 'bin/**;obj/**'
                contract_project=contract_project.replace('</Project>',f'<ItemGroup><Compile Include="**/*.cs" Exclude="{excluded}" /></ItemGroup></Project>')
                (w/'Contracts.csproj').write_text(contract_project)
                command([dotnet,'build','Contracts.csproj','-c',configuration,'--nologo','-warnaserror'],w,env)
                command([dotnet,str(w/f'bin/{configuration}/net9.0/Contracts.dll')],w,env)
                checks.append('boundary and unchanged-state assertions from independent contract harness')
            records.append({'lesson':str(path.relative_to(ROOT)),'files':{name:hashlib.sha256(s.encode()).hexdigest() for name,s in files.items()},'checks':checks})
            print(f'PASS {path.name}: {len(checks)} checks',flush=True)
    return records

def verify_cli(invoke,w):
    file=w/'data/tasks.json';extra={'TASK_DATA_FILE':str(file)}
    def call(args,expected=0):return invoke(args,expected,extra)
    if call(['list']).stdout!='Chưa có công việc.\n':raise ValueError('Empty list mismatch')
    for i,title in enumerate(['Hoc C# co ban','Viet bai tap'],1):
        if call(['add',title]).stdout!=f'Đã thêm #{i}: {title}\n':raise ValueError('Add output')
    before=json.loads(file.read_text());r=call(['list'])
    if not re.fullmatch(r'\[ \] #1 Hoc C# co ban \(\d{4}-\d\d-\d\d \d\d:\d\d UTC\)\n\[ \] #2 Viet bai tap \(\d{4}-\d\d-\d\d \d\d:\d\d UTC\)\n',r.stdout):raise ValueError('List output')
    if call(['done','1']).stdout!='Đã hoàn thành #1.\n':raise ValueError('Done output')
    if call(['remove','2']).stdout!='Đã xóa #2.\n':raise ValueError('Remove output')
    if not call(['list']).stdout.startswith('[x] #1 Hoc C# co ban ('):raise ValueError('Persisted completion')
    saved=file.read_bytes();data=json.loads(saved)
    if len(data)!=1 or data[0]['Status']!=1 or data[0]['CreatedAt']!=before[0]['CreatedAt']:raise ValueError('Roundtrip persistence')
    for args,code in [(['add',' '],2),(['add','x'*201],2),(['done','0'],2),(['done','x'],2),(['remove','999'],1),(['wat'],2)]:
        call(args,code)
        if file.read_bytes()!=saved:raise ValueError('Rejected command changed file')
    for bad in ['{','null','[null]','[{"Id":0,"Title":"x"}]','[{"Id":1,"Title":"x","Status":99}]',json.dumps([data[0],data[0]])]:
        file.write_text(bad);call(['list'],3)
        if file.read_text()!=bad:raise ValueError('Invalid JSON changed')
    exhausted=data[0]|{'Id':2147483647};file.write_text(json.dumps([exhausted]));old=file.read_bytes();call(['add','x'],2)
    if file.read_bytes()!=old:raise ValueError('ID exhaustion changed file')
    file.write_bytes(saved);tmp=Path(str(file)+'.tmp');tmp.mkdir();call(['add','write must fail'],4)
    if file.read_bytes()!=saved:raise ValueError('Failed temporary write changed main file')
    tmp.rmdir()


def verify_labs(dotnet,configuration):
    env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1'}
    records=[]
    paths=sorted((MODULE/'failure-labs').glob('*.md'))
    if len(paths)!=3:raise ValueError('Expected three failure labs')
    for path,expected in zip(paths,['stock=8\n','base=25, direct=55\n','old_done=True\n']):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='csharp']
        if len(sources)!=1:raise ValueError('Expected one published lab source')
        with tempfile.TemporaryDirectory(prefix='module04-lab-') as temp:
            w=Path(temp);(w/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
            (w/'Lab.csproj').write_text(PROJECT);(w/'Program.cs').write_text(sources[0])
            command([dotnet,'build','-c',configuration,'--nologo','-warnaserror'],w,env)
            r=command([dotnet,str(w/f'bin/{configuration}/net9.0/Lab.dll')],w,env)
            if r.stdout!=expected or r.stderr:raise ValueError(f'Failure lab did not reproduce: {path}: {r.stdout!r}')
        records.append({'lab':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(sources[0].encode()).hexdigest(),'documented_failure_reproduced':True})
        print(f'PASS failure reproduction: {path.name}',flush=True)
    return records


def main():
    p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');p.add_argument('--configuration',choices=['Debug','Release'],default='Release');p.add_argument('--samples-only',action='store_true');p.add_argument('--report',type=Path);a=p.parse_args()
    if not a.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('04')
    records=verify(a.dotnet,a.configuration)
    report={'verified_on':str(date.today()),'sdk':SDK,'target':'net9.0','language':'C#13','configuration':a.configuration,'lessons':records,'failure_labs':verify_labs(a.dotnet,a.configuration)}
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
