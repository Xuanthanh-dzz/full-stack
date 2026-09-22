#!/usr/bin/env python3
"""Execute published C#13 examples and lifecycle/async/serialization contracts."""
from pathlib import Path
import argparse
from datetime import date
import hashlib
import json
import os
import re
import tempfile
from verify_module_01 import FENCE,solution
from verify_module_04 import SDK,command
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'fullstack-roadmap/05-csharp-nang-cao'
FILES19=['Domain/Models.cs','Application/ValidationResult.cs','Application/StringExtensions.cs','Application/OrderRules.cs','Application/FileProcessedEventArgs.cs','Application/OrderBatchProcessor.cs','Serialization/BatchJsonContext.cs','Infrastructure/DemoData.cs','Infrastructure/ReportWriter.cs','Program.cs']

def verify(dotnet,configuration):
    records=[]
    with tempfile.TemporaryDirectory(prefix='module05-') as temp:
        base=Path(temp);(base/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
        env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1','LANG':'en_US.UTF-8','LC_ALL':'en_US.UTF-8','TMPDIR':str(base)}
        if command([dotnet,'--version'],base,env).stdout.strip()!=SDK:raise ValueError('SDK mismatch')
        paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
        if len(paths)!=19:raise ValueError('Expected 19 lessons')
        for n,path in enumerate(paths,1):
            b=solution(path.read_text());blocks=list(FENCE.finditer(b));sources=[m.group(3) for m in blocks if m.group(2)=='csharp'];xml=[m.group(3) for m in blocks if m.group(2)=='xml'];names=FILES19 if n==19 else ['Program.cs']
            if len(sources)!=len(names) or len(xml)!=1:raise ValueError(f'{path}: source manifest mismatch')
            w=base/f'{n:02}';w.mkdir();files=dict(zip(names,sources))|{'Sample.csproj':xml[0]}
            for name,content in files.items():
                f=w/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
            command([dotnet,'build','Sample.csproj','-c',configuration,'--nologo','-warnaserror'],w,env)
            dll=w/f'bin/{configuration}/net9.0/Sample.dll'
            args=['demo'] if n==19 else []
            result=command([dotnet,str(dll),*args],w,env,1 if n==19 else 0)
            if result.stderr:raise ValueError(f'Unexpected stderr {path}: {result.stderr}')
            checks=['published project/source manifest builds with warnings as errors']
            if n==18:
                pattern=r'Runtime: \.NET 9\.0\.\d+\nStopwatch frequency: [\d,]+ ticks/second\nOperations/sample: 100\nItems/operation: 300\nChecksums equal: True\nConcatenation median: [\d,]+ ns/op, [\d,]+ B/op\nStringBuilder median: [\d,]+ ns/op, [\d,]+ B/op\n'
                if not re.fullmatch(pattern,result.stdout):raise ValueError('Benchmark contract/output mismatch')
                checks.append('measurement schema and checksum correctness; no timing/speedup assertion')
            else:
                marker={7:'Output chính:',8:'Output chính:',11:'Output deterministic:',13:'Lần chạy đầu in:',16:'Các dòng chính trong output:',19:'Output chuẩn:'}.get(n)
                if marker:
                    tail=b.split(marker,1)[1];expected=next(m.group(3) for m in FENCE.finditer(tail) if m.group(2)=='text')
                else:
                    candidates=[m.group(3) for m in blocks if m.group(2)=='text' and re.search(r'(Kết quả(?: chính xác)?|Output):',b[max(0,m.start()-90):m.start()])]
                    if len(candidates)!=1:raise ValueError(f'{path}: output oracle ambiguous')
                    expected=candidates[0]
                if result.stdout!=expected:raise ValueError(f'{path}: stdout mismatch: {result.stdout!r}')
                checks.append('exact published stdout, empty stderr and specified process exit')
            if n==19:
                report=json.loads((w/'demo-data/report.json').read_text())
                if (report['totalFiles'],report['succeeded'],report['failed'],report['grandTotal'])!=(3,2,1,3650000):raise ValueError('Report totals')
                if [x['fileName'] for x in report['files']]!=['01-order.json','02-order.json','03-order.json']:raise ValueError('Report order')
                if report['files'][0]['order']['customerEmail']!='lan@example.com':raise ValueError('Email normalization')
                usage=command([dotnet,str(dll)],w,env,2)
                if usage.stdout or usage.stderr!='Usage: dotnet run -- demo\n':raise ValueError('CLI usage contract')
                checks.append('persisted report totals/order/normalized email and usage exit 2')
            negative={
                1: [('GenericAlgorithms.GreaterOf(new object(),new object());','CS0311')],
                3: [('var x=new InventoryItem("A",1,0);x.StockLow=null;','CS0070')],
                4: [('int x=1;Func<int> f=static ()=>x;','CS8820')],
                6: [('string? x=null;Console.WriteLine(x.Length);','CS8602')],
                7: [('var x=new OrderDraft {Id="A"};','CS9035')],
                14: [('Span<int> x=stackalloc int[1];await Task.Yield();Console.WriteLine(x[0]);','CS4007')],
                15: [('List<Cat> cats=[];List<Animal> animals=cats;','CS0029'),('ISource<int> a=new SingleValueSource<int>(1);ISource<object> b=a;','CS0266')],
                16: [('System.Linq.Expressions.Expression<Func<int>> e=()=>{return 1;};','CS0834')],
            }.get(n,[])
            for expression,diagnostic in negative:
                namespace=re.search(r'^namespace ([\w.]+);',sources[0],re.M).group(1)
                entry='public static async Task Main()' if n==14 else 'public static void Main()'
                (w/'Negative.cs').write_text('using '+namespace+'; internal static class Negative {'+entry+'{'+expression+'}}')
                failed=command([dotnet,'build','Sample.csproj','-c',configuration,'--nologo','-p:StartupObject=Negative'],w,env,1)
                if diagnostic not in failed.stdout:raise ValueError(f'Expected diagnostic {diagnostic}: {failed.stdout}')
            if negative:
                (w/'Negative.cs').unlink();checks.append('expected compiler rejection of invalid type, access or lifetime contract')
            contract=ROOT/f'scripts/tests/module05_{n:02}_contracts.cs'
            if contract.exists():
                (w/'Contracts.cs').write_text(contract.read_text())
                project=xml[0].replace('</PropertyGroup>','<StartupObject>Contracts</StartupObject></PropertyGroup>')
                (w/'Contracts.csproj').write_text(project)
                command([dotnet,'build','Contracts.csproj','-c',configuration,'--nologo','-warnaserror'],w,env)
                command([dotnet,str(w/f'bin/{configuration}/net9.0/Contracts.dll')],w,env)
                checks.append('independent boundary/lifetime/failure contract assertions')
            records.append({'lesson':str(path.relative_to(ROOT)),'files':{name:hashlib.sha256(s.encode()).hexdigest() for name,s in files.items()},'checks':checks})
            print(f'PASS {path.name}: {len(checks)} checks',flush=True)
    return records

def verify_labs(dotnet,configuration):
    from verify_module_04 import PROJECT
    records=[]
    paths=sorted((MODULE/'failure-labs').glob('*.md'))
    if len(paths)!=4:raise ValueError('Expected four Failure Labs')
    for path,expected in zip(paths,['3,3,3\n','saved=1\n','owner cannot write\n','completed with file error\n']):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='csharp']
        if len(sources)!=1:raise ValueError('Expected one lab source')
        with tempfile.TemporaryDirectory(prefix='module05-lab-') as temp:
            w=Path(temp);(w/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
            (w/'Lab.csproj').write_text(PROJECT);(w/'Program.cs').write_text(sources[0])
            env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1'}
            command([dotnet,'build','-c',configuration,'--nologo','-warnaserror'],w,env)
            result=command([dotnet,str(w/f'bin/{configuration}/net9.0/Lab.dll')],w,env)
            if result.stdout!=expected or result.stderr:raise ValueError('Lab failure did not reproduce')
        records.append({'lab':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(sources[0].encode()).hexdigest(),'documented_failure_reproduced':True})
        print(f'PASS failure reproduction: {path.name}',flush=True)
    return records

def main():
    p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');p.add_argument('--configuration',choices=['Debug','Release'],default='Release');p.add_argument('--samples-only',action='store_true');p.add_argument('--report',type=Path);a=p.parse_args()
    if not a.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('05')
    records=verify(a.dotnet,a.configuration)
    report={'verified_on':str(date.today()),'sdk':SDK,'target':'net9.0','language':'C#13','configuration':a.configuration,'lessons':records,'failure_labs':verify_labs(a.dotnet,a.configuration)}
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
