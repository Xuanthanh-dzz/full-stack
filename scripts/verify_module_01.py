#!/usr/bin/env python3
"""Verify the *published* C11 programs, their output and failure contracts.

--samples-only deliberately does not assert that the module meets clarity v4.
No code is selected by size and no success is inferred merely from exit code 0.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'fullstack-roadmap/01-nen-tang-lap-trinh'
FENCE = re.compile(r'^(```|~~~)(\w+)\n(.*?)^\1\s*$', re.M | re.S)
INPUTS = {6: '4\n', 7: '2\n', 13: 'Lan Anh\n', 15: '1\nLan\n8\n7\n9\n2\n3\nLan\n4\n'}


def run(command, *, cwd, input='', expected=0):
    result = subprocess.run(command, cwd=cwd, input=input, text=True,
                            capture_output=True, timeout=30,
                            env={**os.environ, 'LC_ALL': 'C'})
    if result.returncode != expected:
        raise ValueError(f'{command}: exit {result.returncode}, expected {expected}\n{result.stdout}\n{result.stderr}')
    return result


def solution(text):
    match = re.search(r'^## 3\. .*?\n(.*?)(?=^## 4\.)', text, re.M | re.S)
    if not match:
        raise ValueError('Missing runnable solution section')
    return match.group(1)


def verify_samples(compiler, sanitize=False):
    results = []
    flags = ['-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O0', '-g']
    if sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all']
    paths = sorted(MODULE.glob('[0-9][0-9]-*.md'))
    if len(paths) != 15:
        raise ValueError('Expected exactly 15 published lessons')
    for number, path in enumerate(paths, 1):
        content = path.read_text()
        body = solution(content)
        blocks = [(m.group(2), m.group(3)) for m in FENCE.finditer(body)]
        sources = [s for lang, s in blocks if lang == 'c']
        if len(sources) != 1 or 'int main(void)' not in sources[0]:
            raise ValueError(f'{path}: expected exactly one full C program in section 3')
        output_match = re.search(r'Output:\n\n(```|~~~)text\n(.*?)^\1', body, re.M | re.S)
        if not output_match:
            raise ValueError(f'{path}: missing exact expected Output block')
        expected_output = output_match.group(2)
        source = sources[0]
        checks = []
        with tempfile.TemporaryDirectory(prefix='module01-') as temp:
            work = Path(temp)
            (work/'main.c').write_text(source)
            run([compiler, *flags, 'main.c', '-o', 'sample'], cwd=work)
            result = run(['./sample'], cwd=work, input=INPUTS.get(number, ''))
            if result.stdout != expected_output or result.stderr:
                raise ValueError(f'{path}: output mismatch\nexpected={expected_output!r}\nactual={result.stdout!r}\nstderr={result.stderr!r}')
            checks.append('published stdout exactly matches; stderr empty; exit 0')
            cases = []
            if number == 7:
                cases = [('1\n', 0, 'Gia: 50000 VND', ''), ('3\n', 0, 'Gia: 20000 VND', ''), ('x\n', 1, 'Chon ve', 'Lua chon khong hop le.'), ('', 1, 'Chon ve', 'Lua chon khong hop le.')]
            if number == 13:
                cases = [('',1,'Nhap ten:','Khong co input.'), ('\n',3,'Nhap ten:','Ten khong duoc rong.'), ('A'*30+'\n',0,'Do dai: 30',''), ('A'*31+'\n',2,'Nhap ten:','Ten qua dai.')]
            if number == 15:
                full = ''.join(f'1\nStudent{i}\n8\n7\n9\n' for i in range(5)) + '1\n4\n'
                cases = [('',0,'Tam biet. So hoc sinh: 0',''), ('1\nAn\n8\n7\n',0,'Het input; chua them.',''), ('2\n4\n',0,'Danh sach rong.',''), (full,0,'Danh sach da day.',''), ('1\nAn\n11\n8\n7\n9\n4\n',0,'Tam biet. So hoc sinh: 1',''), ('1\n'+'A'*32+'\n4\n',0,'Ten khong hop le; chua them.','')]
            for data, code, out, err in cases:
                result = run(['./sample'], cwd=work, input=data, expected=code)
                if out not in result.stdout or (err not in result.stderr if err else bool(result.stderr)):
                    raise ValueError(f'{path}: failure path mismatch for {data!r}')
                if number == 15 and data.startswith('1\nAn\n8\n7\n') and 'So hoc sinh: 0' not in result.stdout:
                    raise ValueError('Incomplete student was committed')
                checks.append(f'input={data!r}: exit={code}, contract assertion passed')
            harness = {
                9: 'assert(calculate_average(-1, 5, 5) == -1.0); assert(calculate_average(10,10,10) == 10.0); assert(grade_from_average(6.5) == \'B\');',
                10: 'assert(calculate_subtotal(INT_MAX, 2) == -1); assert(calculate_subtotal(0, INT_MAX) == 0); assert(calculate_total(3,120,361) == -1);',
                11: 'int a[]={8,7,11}; assert(sum_scores(a,3)==-1); assert(sum_scores(a,0)==0); assert(sum_scores(a,-1)==-1); assert(find_max(a,2)==8);',
                12: 'int a[]={8,11}; assert(row_average(a,0)==-1.0); assert(row_average(a,2)==-1.0); assert(row_average(a,1)==8.0);',
                13: 'char a[1]={\'X\'}; assert(read_line(a,0)==-2); assert(a[0]==\'X\');',
                15: 'assert(parse_number("",10)==-1); assert(parse_number("x",10)==-1); assert(parse_number("10",10)==10); assert(parse_number("11",10)==-1); assert(parse_number("9999999999999999999999999",10)==-1); char a[1]={\'X\'}; assert(read_line(a,0)==-2); assert(a[0]==\'X\');',
            }.get(number)
            if harness:
                (work/'contracts.c').write_text('#include <assert.h>\n#define main lesson_main\n#include "main.c"\n#undef main\nint main(void) { '+harness+' return 0; }\n')
                run([compiler, *flags, 'contracts.c','-o','contracts'], cwd=work)
                run(['./contracts'], cwd=work)
                checks.append('boundary/invalid-domain function contracts passed')
            if number == 14:
                # Prove the published regression tests actually reject the original bug.
                (work/'mutant.c').write_text(source.replace('average >= 8.0', 'average > 8.0', 1))
                run([compiler, *flags, 'mutant.c','-o','mutant'], cwd=work)
                mutant = subprocess.run(['./mutant'], cwd=work, capture_output=True, text=True, timeout=10)
                if mutant.returncode == 0 or 'classify(8.0)' not in mutant.stderr:
                    raise ValueError('Published boundary test failed to kill >= to > mutation')
                checks.append('>= to > mutation rejected by published assert')
        print(f'PASS {path.name}: {len(checks)} checks')
        results.append({'lesson': str(path.relative_to(ROOT)), 'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'checks': checks})
    return results


def verify_failure_labs(compiler):
    """Reproduce the documented bugs; never publish repaired full solutions."""
    results = []
    for number, path in enumerate(sorted((MODULE/'failure-labs').glob('*.md')), 1):
        blocks = [m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2) == 'c']
        if len(blocks) != 1:
            raise ValueError(f'{path}: expected one reproducer')
        with tempfile.TemporaryDirectory(prefix='module01-lab-') as temp:
            work = Path(temp)
            (work/'lab.c').write_text(blocks[0])
            flags = ['-std=c11','-Wall','-Wextra','-Wpedantic','-Werror','-O0','-g']
            if number == 3:
                flags += ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
            run([compiler,*flags,'lab.c','-o','lab'],cwd=work)
            result = subprocess.run(['./lab'],cwd=work,text=True,capture_output=True,timeout=10)
            if number in (1,2):
                expected = {1:'Sold: 0.0%\n',2:'Grade: F\n'}[number]
                if result.returncode or result.stdout != expected or result.stderr:
                    raise ValueError(f'{path}: documented bug no longer reproduces')
            elif result.returncode == 0 or not any(s in result.stderr for s in ('out of bounds','stack-buffer-overflow')):
                raise ValueError(f'{path}: sanitizer did not identify the documented bounds bug\n{result.stderr}')
            results.append({'lab':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(blocks[0].encode()).hexdigest(),'documented_failure_reproduced':True})
            print(f'PASS failure reproduction: {path.name}')
    if len(results) != 3:
        raise ValueError('Expected three reproduced Failure Labs')
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cc', default=os.environ.get('CC','cc'))
    parser.add_argument('--sanitize', action='store_true')
    parser.add_argument('--samples-only', action='store_true')
    parser.add_argument('--report', type=Path)
    args=parser.parse_args()
    if not args.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('01')
    results=verify_samples(args.cc, args.sanitize)
    labs = verify_failure_labs(args.cc)
    report={'date': date.today().isoformat(), 'compiler': subprocess.check_output([args.cc,'--version'],text=True).splitlines()[0], 'sanitize': args.sanitize, 'scope': 'published primary programs and listed contracts; not every exercise solution', 'lessons': results, 'failure_labs':labs}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Module 01 sample verification passed: 15/15. Human clarity review remains separate.')

if __name__=='__main__':
    main()
