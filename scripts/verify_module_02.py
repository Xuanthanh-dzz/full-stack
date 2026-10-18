#!/usr/bin/env python3
"""Compile the explicit published source set, never the largest code block."""
from pathlib import Path
import argparse
from datetime import date
import hashlib
import json
import os
import re
import subprocess
import tempfile
from verify_module_01 import FENCE, run, solution

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'fullstack-roadmap/02-c-chuyen-sau'
FILES={12:['inventory_limits.h','main.c'],13:['inventory.h','inventory.c','main.c'],15:['inventory.h','inventory.c','storage.h','storage.c','main.c']}

def verify(compiler,sanitize):
    flags=['-std=c11','-Wall','-Wextra','-Wpedantic','-Werror','-O0','-g']
    if sanitize:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
    records=[]
    paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
    if len(paths)!=15:raise ValueError('Expected 15 lessons')
    for n,p in enumerate(paths,1):
        body=solution(p.read_text())
        blocks=[(m.group(2),m.group(3)) for m in FENCE.finditer(body)]
        sources=[s for lang,s in blocks if lang=='c']
        names=FILES.get(n,['main.c'])
        if len(names)!=len(sources):raise ValueError(f'{p}: source manifest mismatch')
        match=re.search(r'Output(?: thành công| trên standard output)?:\n\n(```|~~~)text\n(.*?)^\1',body,re.M|re.S)
        if not match:raise ValueError(f'{p}: missing expected output')
        expected=match.group(2)
        checks=[]
        with tempfile.TemporaryDirectory(prefix='module02-') as temp:
            work=Path(temp)
            for name,source in zip(names,sources):(work/name).write_text(source)
            units=[name for name in names if name.endswith('.c')]
            run([compiler,*flags,*units,'-o','sample'],cwd=work)
            result=run(['./sample'],cwd=work)
            if result.stdout!=expected or result.stderr:raise ValueError(f'{p}: output mismatch {result.stdout!r} {result.stderr!r}')
            checks.append('published exact stdout, empty stderr, exit 0')
            if n==12:
                run([compiler,*flags,'-DTRACE_ENABLED=1','main.c','-o','traced'],cwd=work)
                result=run(['./traced'],cwd=work)
                if result.stdout!=expected or result.stderr!='TRACE: Bat dau chuan hoa\n':raise ValueError('Trace configuration contract failed')
                checks.append('TRACE_ENABLED=0/1 have identical stdout and documented stderr')
            if n in (13,15) and not sanitize:
                make=next(s for lang,s in blocks if lang=='makefile')
                (work/'Makefile').write_text(make)
                run(['make',f'CC={compiler}'],cwd=work)
                result=run(['./inventory-app'],cwd=work)
                if result.stdout!=expected:raise ValueError('Makefile output differs')
                run(['make','-q'],cwd=work)
                # Touch dependency logically into the future without waiting on timestamp granularity.
                old=(work/'inventory.h').stat().st_mtime
                os.utime(work/'inventory.h',(old+5,old+5))
                dry=run(['make','-n'],cwd=work).stdout
                if 'main.c' not in dry or 'inventory.c' not in dry:raise ValueError('Header dependency missing')
                checks.append('published Makefile builds, second make is up-to-date, header rebuilds callers')
            harness={
                2:'int a=7,b=2; assert(!order_ascending(NULL,&b)); assert(order_ascending(&a,&b)); assert(a==2&&b==7); assert(order_ascending(&a,&a));',
                3:'int a[]={INT_MAX,1}; int out=99; assert(!sum_quantities(a,2,&out)); assert(out==99); assert(sum_quantities(NULL,0,&out)&&out==0); assert(find_character("ABC",\'x\')==NULL);',
                4:'int a[]={1,9,3}; const int *p=NULL; assert(!select_largest(a,0,&p)&&p==NULL); assert(select_largest(a,3,&p)&&p==&a[1]);',
                5:'assert(calculate_line_total(INT_MAX,2,regular_price)==-1); assert(calculate_line_total(1000,0,regular_price)==0); assert(calculate_line_total(1000,1,NULL)==-1);',
                6:'int out=99; assert(!calculate_total(INT_MAX,2,&out)&&out==99); assert(calculate_total(0,INT_MAX,&out)&&out==0);',
                7:'int *p=malloc(sizeof *p); assert(p); p[0]=7; assert(!resize_prices(&p,1,0)&&p[0]==7); assert(resize_prices(&p,1,3)&&p[0]==7&&p[1]==0&&p[2]==0); free(p);',
                8:'char *p=duplicate_text(""); assert(p&&p[0]==0); char out=\'X\'; assert(!try_get_character(p,0,&out)&&out==\'X\'); release_text(&p); release_text(&p); assert(p==NULL);',
                9:'Product p={.id=1,.name="A",.quantity=INT_MAX,.reorder_level=2}; assert(!restock(&p,1)&&p.quantity==INT_MAX); assert(restock(&p,0)); assert(!restock(NULL,0));',
                10:'Adjustment a={.kind=ADJUST_PERCENT,.value.percent=101}; int out=99; assert(!apply_adjustment(100,&a,&out)&&out==99); a.value.percent=100; assert(apply_adjustment(INT_MAX,&a,&out)&&out==0);',
                11:'int out=99; assert(!parse_nonnegative_int("12x",&out)&&out==99); assert(!parse_nonnegative_int("999999999999999999999",&out)); Product p={.code="A|B",.quantity=1,.price_cents=1}; assert(!save_products("invalid.txt",&p,1)); size_t count=99; assert(!load_and_print_products("missing.txt",&count));',
                14:'int out=99; assert(parse_quantity("12x",&out)==APP_INVALID_ARGUMENT&&out==99); assert(parse_quantity("999999999999999999999999",&out)==APP_OUT_OF_RANGE); assert(parse_quantity(" +25",&out)==APP_OK&&out==25); assert(save_quantity("missing-dir/file",1)==APP_IO_ERROR);',
            }.get(n)
            if harness:
                (work/'contracts.c').write_text('#include <assert.h>\n#include <limits.h>\n#define main lesson_main\n#include "main.c"\n#undef main\nint main(void){'+harness+'return 0;}\n')
                run([compiler,*flags,'contracts.c','-o','contracts'],cwd=work)
                run(['./contracts'],cwd=work)
                checks.append('invalid-domain/boundary contracts and unchanged-output assertions')
            if n==2:
                fragments=[m.group(3) for m in FENCE.finditer(p.read_text()) if m.group(2)=='c' and 'static int try_divide(' in m.group(3)]
                if len(fragments)!=1:raise ValueError('Missing supplemental try_divide')
                (work/'divide.c').write_text('#include <assert.h>\n#include <stddef.h>\n#include <limits.h>\n'+fragments[0]+'\nint main(void){int out=99;assert(!try_divide(1,0,&out)&&out==99);assert(!try_divide(INT_MIN,-1,&out)&&out==99);assert(!try_divide(4,2,NULL));assert(try_divide(7,2,&out)&&out==3);return 0;}\n')
                run([compiler,*flags,'divide.c','-o','divide'],cwd=work)
                run(['./divide'],cwd=work)
                checks.append('supplemental try_divide: zero/overflow/NULL preserve output, integer division')
            if n==15:
                extra=(ROOT/'scripts/tests/module02_inventory_contracts.c').read_text()
                (work/'contracts.c').write_text(extra)
                run([compiler,*flags,'contracts.c','storage.c','-o','contracts'],cwd=work)
                run(['./contracts'],cwd=work)
                checks.append('allocator failure injection, growth/removal/dispose, malformed load preserves destination, roundtrip')
        records.append({'lesson':str(p.relative_to(ROOT)),'sources':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in zip(names,sources)},'checks':checks})
        print(f'PASS {p.name}: {len(checks)} checks')
    return records

def verify_failure_labs(compiler):
    records=[]
    paths=sorted((MODULE/'failure-labs').glob('*.md'))
    if len(paths)!=3:raise ValueError('Expected three Module 02 Failure Labs')
    for n,path in enumerate(paths,1):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='c']
        if len(sources)!=1:raise ValueError('Expected one documented reproducer per lab')
        with tempfile.TemporaryDirectory(prefix='module02-lab-') as temp:
            work=Path(temp);(work/'bug.c').write_text(sources[0])
            flags=['-std=c11','-Wall','-Wextra','-Wpedantic','-Werror','-O0','-g']
            if n==2:
                flags.remove('-Werror')  # Deliberately faulty lab: retain warning, then reproduce ASan evidence.
                flags+=['-fsanitize=address','-fno-omit-frame-pointer']
            run([compiler,*flags,'bug.c','-o','bug'],cwd=work)
            result=subprocess.run(['./bug'],cwd=work,capture_output=True,text=True,timeout=10)
            if n==2:
                if result.returncode==0 or 'heap-use-after-free' not in result.stderr:raise ValueError(f'{path}: missing expected ASan failure: {result.stderr}')
            else:
                expected={1:'Trong ham: 9\nCaller: 3\n',3:'ok=0 quantity=0\n'}[n]
                if result.returncode or result.stderr or result.stdout!=expected:raise ValueError(f'{path}: documented bug not reproduced')
        records.append({'lab':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(sources[0].encode()).hexdigest(),'documented_failure_reproduced':True})
        print(f'PASS failure reproduction: {path.name}')
    return records


def main():
    a=argparse.ArgumentParser();a.add_argument('--cc',default='cc');a.add_argument('--sanitize',action='store_true');a.add_argument('--samples-only',action='store_true');a.add_argument('--report',type=Path);args=a.parse_args()
    if not args.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('02')
    report={'date':date.today().isoformat(),'compiler':subprocess.check_output([args.cc,'--version'],text=True).splitlines()[0],'sanitize':args.sanitize,'lessons':verify(args.cc,args.sanitize),'failure_labs':verify_failure_labs(args.cc)}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Module 02 published samples: 15/15 pass. Exercises/snippet fragments are not all independent programs.')
if __name__=='__main__':main()
