#!/usr/bin/env python3
"""Run the published C++20 sources, outputs and ownership contracts."""
from pathlib import Path
import argparse
from datetime import date
import hashlib
import json
import subprocess
import tempfile
import re
from verify_module_01 import FENCE, run, solution
ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'fullstack-roadmap/03-cpp'

def verify(compiler,sanitize):
    flags=['-std=c++20','-Wall','-Wextra','-Wpedantic','-Werror','-O0','-g']
    if sanitize:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
    records=[]
    paths=sorted(MODULE.glob('[0-9][0-9]-*.md'))
    if len(paths)!=14:raise ValueError('Expected 14 lessons')
    for n,path in enumerate(paths,1):
        body=solution(path.read_text())
        sources=[m.group(3) for m in FENCE.finditer(body) if m.group(2)=='cpp']
        if len(sources)!=1:raise ValueError(f'{path}: expected one published source')
        source=sources[0]
        if n==1:
            # Published terminal transcript includes input echo; piped stdin does not.
            expected='Product name: Quantity: Unit price (VND): \nInvoice\nProduct: Mechanical Keyboard\nSubtotal: 750000 VND\nVAT: 60000 VND\nTotal: 810000 VND\n'
        else:
            match=re.search(r'Kết quả(?: console)?:\n\n(```|~~~)text\n(.*?)^\1',body,re.M|re.S)
            if not match:raise ValueError(f'{path}: missing expected output')
            expected=match.group(2)
        checks=[]
        with tempfile.TemporaryDirectory(prefix='module03-') as temp:
            work=Path(temp);(work/'main.cpp').write_text(source)
            run([compiler,*flags,'main.cpp','-o','sample'],cwd=work)
            result=run(['./sample'],cwd=work,input='Mechanical Keyboard\n3\n250000\n' if n==1 else '')
            if result.stdout!=expected or result.stderr:raise ValueError(f'{path}: output mismatch {result.stdout!r} {result.stderr!r}')
            checks.append('published primary program exact stdout, empty stderr, exit 0')
            if n==1:
                for input in ['\n3\n1\n','A\n0\n1\n','A\n2\n-1\n','A\nabc\n1\n','A\n1000001\n1\n','A\n1\n1000000000001\n','A\n']:
                    bad=run(['./sample'],cwd=work,input=input,expected=1)
                    if bad.stderr!='Invalid invoice data\n' or 'Invoice\n' in bad.stdout:raise ValueError('Invoice failure contract changed')
                checks.append('invalid invoice domain, parse and EOF reject with exit 1')
            if n in (11,14):
                filename='order-report.txt' if n==11 else 'library-report.txt'
                expected_file='ORD-001,750000\n' if n==11 else 'BK-001,C++20 Essentials,available,14\nBK-002,RAII in Practice,available,21\n'
                if (work/filename).read_text()!=expected_file:raise ValueError('Report file mismatch')
                checks.append('exact report file content after cleanup/close')
            harness={
                2:'std::string s="   ";trim_trailing_spaces(s);make_first_letter_uppercase(s);assert(s.empty());long long out=99;assert(!try_calculate_subtotal(0,1,out)&&out==99);assert(try_calculate_subtotal(1000000,1000000000000LL,out)&&out==1000000000000000000LL);',
                3:'LoyaltyAccount a,b;assert(!a.set_customer_id(""));assert(a.add_points(1000000));assert(!a.add_points(1)&&a.points()==1000000);assert(!a.redeem(1000001));assert(a.redeem(1000000)&&a.points()==0);assert(b.points()==0);',
                5:'IntBuffer a{2};a.at(0)=7;IntBuffer b=a;b.at(0)=9;assert(a.at(0)==7);auto copy=[](auto& x,const auto& y){x=y;};copy(a,a);assert(a.at(0)==7);auto move=[](auto& x,auto& y){x=std::move(y);};move(a,a);assert(a.size()==2);IntBuffer c{1};c=std::move(b);assert(c.at(0)==9&&b.size()==0);b=a;assert(b.at(0)==7);IntBuffer empty{0};empty=a;assert(empty.size()==2);a=IntBuffer{0};assert(a.size()==0);',
                6:'ExpressDelivery e;const Delivery& view=e;assert(view.fee(600000)==60000);Delivery sliced=e;assert(sliced.fee(600000)==0);Delivery s{"S"};assert(s.fee(499999)==30000&&s.fee(500000)==0);',
                7:'DigitalWallet w{"W"};assert(!w.pay(1));assert(w.top_up(1000000000000LL));assert(!w.top_up(1)&&w.balance()==1000000000000LL);PaymentMethod& p=w;assert(p.pay(1));Refundable& r=w;assert(r.refund(1));assert(!r.refund(1));',
                8:'FixedStack<int,2> s;int out=99;assert(!s.pop(out)&&out==99);assert(s.push(4)&&s.push(7)&&!s.push(9));assert(s.pop(out)&&out==7);assert(s.pop(out)&&out==4);assert(!s.pop(out));assert(clamp_value(-1,0,10)==0);',
                11:'bool caught=false;try{calculate_total(2,std::numeric_limits<long long>::max());}catch(const std::overflow_error&){caught=true;}assert(caught);caught=false;try{ReportWriter w{"missing-dir/report"};}catch(const std::runtime_error&){caught=true;}assert(caught);assert(calculate_total(1,0)==0);',
                12:'Shelf shelf;bool caught=false;try{shelf.add(nullptr);}catch(const std::invalid_argument&){caught=true;}assert(caught);auto a=std::make_unique<Book>("A");auto* view=a.get();auto b=std::move(a);assert(!a&&view==b.get()&&view->title()=="A");std::weak_ptr<const Promotion> weak;{auto p=std::make_shared<const Promotion>("P");weak=p;assert(weak.lock());}assert(!weak.lock());',
                13:'std::string draft="keep";auto a=create_message(draft);assert(draft=="keep"&&a->text()==draft);auto b=create_message(std::string{"temporary"});assert(b->text()=="temporary");',
            }.get(n)
            if n==14:harness=(ROOT/'scripts/tests/module03_library_contracts.inc').read_text()
            if harness:
                (work/'contracts.cpp').write_text('#include <cassert>\n#define main lesson_main\n#include "main.cpp"\n#undef main\nint main(){'+harness+'return 0;}\n')
                run([compiler,*flags,'contracts.cpp','-o','contracts'],cwd=work)
                run(['./contracts'],cwd=work)
                checks.append('boundary, ownership and failure-state contracts')
            if n==8:
                for label,expression in [('zero_capacity','FixedStack<int,0> value;'),('constraint','auto value=clamp_value(std::string{"a"},std::string{"b"},std::string{"c"});')]:
                    (work/'negative.cpp').write_text('#define main lesson_main\n#include "main.cpp"\n#undef main\nint main(){'+expression+'(void)value;}\n')
                    result=subprocess.run([compiler,*flags,'negative.cpp','-o','negative'],cwd=work,text=True,capture_output=True,timeout=30)
                    if result.returncode==0:raise ValueError(f'Template negative case compiled: {label}')
                checks.append('compile rejection: zero capacity and nonnumeric clamp')
        records.append({'lesson':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'checks':checks})
        print(f'PASS {path.name}: {len(checks)} checks')
    return records

def verify_failure_labs(compiler):
    records=[]
    paths=sorted((MODULE/'failure-labs').glob('*.md'))
    if len(paths)!=3:raise ValueError('Expected three Failure Labs')
    for n,path in enumerate(paths,1):
        sources=[m.group(3) for m in FENCE.finditer(path.read_text()) if m.group(2)=='cpp']
        if len(sources)!=1:raise ValueError('Expected one reproducer')
        with tempfile.TemporaryDirectory(prefix='module03-lab-') as temp:
            work=Path(temp);(work/'bug.cpp').write_text(sources[0])
            run([compiler,'-std=c++20','-Wall','-Wextra','-Wpedantic','-O0','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','bug.cpp','-o','bug'],cwd=work)
            result=subprocess.run(['./bug'],cwd=work,capture_output=True,text=True,timeout=10)
            if n<3:
                marker={1:'attempting double-free',2:'heap-use-after-free'}[n]
                if result.returncode==0 or marker not in result.stderr:raise ValueError(f'{path}: expected {marker}: {result.stderr}')
            elif result.returncode or result.stdout!='size=0\n' or result.stderr:raise ValueError('RAII rollback lab did not reproduce')
        records.append({'lab':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(sources[0].encode()).hexdigest(),'documented_failure_reproduced':True})
        print(f'PASS failure reproduction: {path.name}')
    return records


def main():
    p=argparse.ArgumentParser();p.add_argument('--cxx',default='c++');p.add_argument('--sanitize',action='store_true');p.add_argument('--samples-only',action='store_true');p.add_argument('--report',type=Path);a=p.parse_args()
    if not a.samples_only:
        from verify_retrofit_v4 import check_module
        check_module('03')
    report={'date':date.today().isoformat(),'compiler':subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],'sanitize':a.sanitize,'lessons':verify(a.cxx,a.sanitize),'failure_labs':verify_failure_labs(a.cxx)}
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Module 03: 14 primary programs passed; human review and exercise solutions remain separate.')
if __name__=='__main__':main()
