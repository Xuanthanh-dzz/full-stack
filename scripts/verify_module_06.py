#!/usr/bin/env python3
"""Execute Module 06 examples and independent mutation, lifetime and compatibility contracts."""
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
MODULE=ROOT/'fullstack-roadmap/06-oop-va-thiet-ke'
FILES14=['Legacy/LegacyOrderProcessor.cs','Domain/Money.cs','Domain/Order.cs','Domain/Pricing/DiscountRules.cs','Domain/Pricing/PricingService.cs','Application/OrderParser.cs','Application/ProcessOrdersUseCase.cs','Presentation/ReportBuilder.cs','Infrastructure/Adapters.cs','Testing/CharacterizationHarness.cs','Program.cs']

def verify(dotnet,configuration):
    records=[]
    with tempfile.TemporaryDirectory(prefix='module06-') as temp:
        base=Path(temp);(base/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
        env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1','LANG':'en_US.UTF-8','LC_ALL':'en_US.UTF-8','TMPDIR':str(base)}
        if command([dotnet,'--version'],base,env).stdout.strip()!=SDK:raise ValueError('SDK mismatch')
        paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
        if len(paths)!=14:raise ValueError('Expected 14 lessons')
        for n,path in enumerate(paths,1):
            b=solution(path.read_text());blocks=list(FENCE.finditer(b));sources=[m.group(3) for m in blocks if m.group(2)=='csharp'];xml=[m.group(3) for m in blocks if m.group(2)=='xml'];names=FILES14 if n==14 else ['Program.cs']
            if len(sources)!=len(names) or len(xml)!=1:raise ValueError(f'{path}: source manifest mismatch')
            w=base/f'{n:02}';w.mkdir();files=dict(zip(names,sources))|{'Sample.csproj':xml[0]}
            for name,content in files.items():
                f=w/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
            command([dotnet,'build','Sample.csproj','-c',configuration,'--nologo','-warnaserror'],w,env)
            dll=w/f'bin/{configuration}/net9.0/Sample.dll'
            args=[]
            result=command([dotnet,str(dll),*args],w,env)
            if result.stderr:raise ValueError(f'Unexpected stderr {path}: {result.stderr}')
            checks=['published project/source manifest builds with warnings as errors']
            candidates=[m.group(3) for m in blocks if m.group(2)=='text' and b[max(0,m.start()-30):m.start()].strip().endswith('Output:')]
            if len(candidates)!=1 or result.stdout!=candidates[0]:raise ValueError(f'{path}: published stdout mismatch: {result.stdout!r}')
            checks.append('exact published stdout, empty stderr and exit zero')
            negative={
                1:[('var c=new Customer("A","B");var o=new Order("O",c,"VND");o.Status=OrderStatus.Placed;','CS0272')],
                2:[('new StoreCredit("A").Balance=1m;','CS0200')],
                6:[('IWithdrawable a=new TermDepositAccount("A",1m,new DateOnly(2027,1,1));','CS0029')],
                7:[('IOrderReader r=new InMemoryOrderStore();r.Save(new OrderSummary("A","B",1m,new DateOnly(2026,1,1)));','CS1061')],
                13:[('new StockItem("A",1).Reserved=2;','CS0200')],
            }.get(n,[])
            for expression,diagnostic in negative:
                namespace=re.search(r'^namespace ([\w.]+);',sources[0],re.M).group(1)
                entry='public static void Main()'
                (w/'Negative.cs').write_text('using '+namespace+'; internal static class Negative {'+entry+'{'+expression+'}}')
                failed=command([dotnet,'build','Sample.csproj','-c',configuration,'--nologo','-p:StartupObject=Negative'],w,env,1)
                if diagnostic not in failed.stdout:raise ValueError(f'Expected diagnostic {diagnostic}: {failed.stdout}')
            if negative:
                (w/'Negative.cs').unlink();checks.append('expected compiler rejection of invalid type, access or lifetime contract')
            contract=ROOT/f'scripts/tests/module06_{n:02}_contracts.cs'
            if not contract.exists():raise ValueError(f'Missing independent contracts: {contract}')
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
    if len(paths)!=3:raise ValueError('Expected three Failure Labs')
    for path,expected in zip(paths,['lines=0\n','[req-1] second\n','same=False\n']):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='csharp']
        if len(sources)!=1:raise ValueError('Expected one lab source')
        with tempfile.TemporaryDirectory(prefix='module06-lab-') as temp:
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
        check_module('06')
    records=verify(a.dotnet,a.configuration)
    report={'verified_on':str(date.today()),'sdk':SDK,'target':'net9.0','language':'C#13','configuration':a.configuration,'lessons':records,'failure_labs':verify_labs(a.dotnet,a.configuration)}
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
