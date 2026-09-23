#!/usr/bin/env python3
"""Execute Module 07 examples and independent data structure and algorithm contracts."""
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
MODULE=ROOT/'fullstack-roadmap/07-cau-truc-du-lieu-giai-thuat'

def verify(dotnet,configuration):
    records=[]
    with tempfile.TemporaryDirectory(prefix='module07-') as temp:
        base=Path(temp);(base/'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>');(base/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
        env=os.environ|{'DOTNET_NOLOGO':'1','DOTNET_CLI_TELEMETRY_OPTOUT':'1','LANG':'en_US.UTF-8','LC_ALL':'en_US.UTF-8','TMPDIR':str(base)}
        if command([dotnet,'--version'],base,env).stdout.strip()!=SDK:raise ValueError('SDK mismatch')
        paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
        if len(paths)!=19:raise ValueError('Expected 19 lessons')
        for n,path in enumerate(paths,1):
            b=solution(path.read_text());blocks=list(FENCE.finditer(b));sources=[m.group(3) for m in blocks if m.group(2)=='csharp'];xml=[m.group(3) for m in blocks if m.group(2)=='xml'];names=['Program.cs']
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
            if n==1:
                pattern=(r"n=1,000: linear=1,000, pairs=1,000,000\nn=10,000: linear=10,000, pairs=100,000,000\nn=100,000: linear=100,000, pairs=10,000,000,000\n\nList\.Contains : [0-9,.]+ ms\nHashSet\.Contains: [0-9,.]+ ms\nDo not compare these milliseconds across different machines\.\n")
                if not re.fullmatch(pattern,result.stdout):raise ValueError('Big-O output/count mismatch')
            elif n==8:
                lines=result.stdout.splitlines()
                expected={'P3: T-100 - Change avatar','P1: T-101 - Server down','P2: T-102 - Payment delayed','P2: T-103 - Cannot login'}
                if len(lines)!=4 or set(lines)!=expected or [x[:2] for x in lines]!=['P1','P2','P2','P3']:raise ValueError('Priority output mismatch')
            else:
                candidates=[m.group(3) for m in blocks if m.group(2)=='text' and b[max(0,m.start()-50):m.start()].strip().endswith(('Output:','Output chính:','Một output hợp lệ:','Một output:','Output đầy đủ:'))]
                if len(candidates)!=1 or result.stdout!=candidates[0]:raise ValueError(f'{path}: published stdout mismatch: {result.stdout!r}; candidates={len(candidates)}')
            checks.append('published stdout contract, empty stderr and exit zero; timing and heap ties handled explicitly')
            contract=ROOT/f'scripts/tests/module07_{n:02}_contracts.cs'
            if not contract.exists():raise ValueError(f'Missing independent contracts: {contract}')
            if contract.exists():
                (w/'Contracts.cs').write_text(contract.read_text())
                project=xml[0].replace('</PropertyGroup>','<StartupObject>Contracts</StartupObject></PropertyGroup>')
                (w/'Contracts.csproj').write_text(project)
                command([dotnet,'build','Contracts.csproj','-c',configuration,'--nologo','-warnaserror'],w,env)
                command([dotnet,str(w/f'bin/{configuration}/net9.0/Contracts.dll')],w,env)
                checks.append('independent boundary, mutation and algorithm oracle assertions')
            records.append({'lesson':str(path.relative_to(ROOT)),'files':{name:hashlib.sha256(s.encode()).hexdigest() for name,s in files.items()},'checks':checks})
            print(f'PASS {path.name}: {len(checks)} checks',flush=True)
    return records

def verify_labs(dotnet,configuration):
    from verify_module_04 import PROJECT
    records=[]
    paths=sorted((MODULE/'failure-labs').glob('*.md'))
    if len(paths)!=4:raise ValueError('Expected four Failure Labs')
    for path,expected in zip(paths,['shifts=499500\n','found=False\n','index=-1\n','lengths=0,0\n']):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='csharp']
        if len(sources)!=1:raise ValueError('Expected one lab source')
        with tempfile.TemporaryDirectory(prefix='module07-lab-') as temp:
            w=Path(temp);(w/'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>');(w/'global.json').write_text(json.dumps({'sdk':{'version':SDK,'rollForward':'disable'}}))
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
        check_module('07')
    records=verify(a.dotnet,a.configuration)
    report={'verified_on':str(date.today()),'sdk':SDK,'target':'net9.0','language':'C#13','configuration':a.configuration,'lessons':records,'failure_labs':verify_labs(a.dotnet,a.configuration)}
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
