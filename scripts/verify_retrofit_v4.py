#!/usr/bin/env python3
"""Structural clarity gate for explicitly activated retrofit modules.

This is evidence of structure, not an automated judgement of teaching quality.
Adding a module requires its sample verifier and assessment manifest first.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
ROADMAP=ROOT/'fullstack-roadmap'
ACTIVE={'01': ('01-nen-tang-lap-trinh',15,[(1,5),(6,10),(11,15)]),
        '02': ('02-c-chuyen-sau',15,[(1,5),(6,10),(11,15)]),
        '03': ('03-cpp',14,[(1,5),(6,10),(11,14)]),
        '04': ('04-csharp-co-ban',16,[(1,5),(6,10),(11,16)]),
        '05': ('05-csharp-nang-cao',19,[(1,5),(6,10),(11,15),(16,19)]),
        '06': ('06-oop-va-thiet-ke',14,[(1,5),(6,10),(11,14)]),
        '07': ('07-cau-truc-du-lieu-giai-thuat',19,[(1,5),(6,10),(11,15),(16,19)])}
FENCE=re.compile(r'^(```|~~~)[^\n]*\n.*?^\1\s*$',re.M|re.S)
SECTIONS=['Mục tiêu','Bài toán mở đầu','Lời giải chạy được','Cơ chế hoạt động','Kiến thức nền và prerequisites','Lỗi thường gặp','Khi nào KHÔNG dùng','Production notes & scale check','Bài tập kỹ thuật','Bài tập tích hợp liên module — Judgment','Retrieval practice','Checklist tự đánh giá & điều hướng']


def require(condition,message):
    if not condition:
        raise ValueError(message)


def heading_body(text, heading):
    # Exact headings outside code fences only, so sample strings cannot pass gates.
    clean=FENCE.sub('',text)
    match=re.search(r'^'+re.escape(heading)+r'\s*\n(.*?)(?=^#{1,3} |\Z)',clean,re.M|re.S)
    require(match is not None,f'Missing heading: {heading}')
    body=match.group(1).strip()
    # Parent headings can legitimately begin with substantive subsections.
    return body


def slug(value):
    value=re.sub(r'<[^>]+>','',value).replace('`','').replace('*','')
    value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()
    value=re.sub(r'[^\w\s-]','',value)
    return re.sub(r'[-\s]+','-',value).strip('-')


def check_links(path,text):
    clean=FENCE.sub('',text)
    # Inline code can contain lambda syntax [capture](parameters), not a link.
    clean=re.sub(r'(`+)(?!`).*?(?<!`)\1(?!`)', '', clean)
    for raw in re.findall(r'\[[^\]]+\]\(([^)]+)\)',clean):
        if re.match(r'^(https?:|mailto:)',raw):
            continue
        raw=unquote(raw.strip('<>'))
        target,_,anchor=raw.partition('#')
        resolved=(path.parent/target).resolve() if target else path.resolve()
        require(resolved.is_relative_to(ROOT.resolve()),f'{path}: link escapes repository: {raw}')
        require(resolved.exists(),f'{path}: broken local link: {raw}')
        if anchor and resolved.suffix=='.md':
            linked=FENCE.sub('',resolved.read_text())
            ids=set(re.findall(r'<a\s+id="([^"]+)"',linked))
            counts={}
            for h in re.findall(r'^#{1,6}\s+(.+)$',linked,re.M):
                base=slug(h); n=counts.get(base,0); counts[base]=n+1
                ids.add(base if not n else f'{base}_{n}')
            require(anchor in ids,f'{path}: unknown fragment: {raw}')


def check_lesson(path,today=None):
    text=path.read_text()
    clean=FENCE.sub('',text)
    today=today or date.today()
    for field in ['Last verified','Baseline','Review cycle','Re-verify triggers']:
        require(re.search(r'^> \*\*'+field+r':\*\*\s*\S.+$',text,re.M),f'{path}: missing metadata {field}')
    verified=re.search(r'\*\*Last verified:\*\* (\d{4}-\d{2}-\d{2})',text)
    cycle=re.search(r'\*\*Review cycle:\*\* (\d+) days',text)
    require(verified and cycle,f'{path}: unverified or invalid freshness metadata')
    age=(today-date.fromisoformat(verified.group(1))).days
    require(0<=age<=int(cycle.group(1)) and int(cycle.group(1))>0,f'{path}: stale/future verification date')
    headings=re.findall(r'^## (\d+)\. (.+)$',clean,re.M)
    require(headings==[(str(i),s) for i,s in enumerate(SECTIONS,1)],f'{path}: expected ordered 12 v4 sections')
    tldr=heading_body(text,'## TL;DR')
    require(len(re.findall(r'^- \S.+$',tldr,re.M))==3,f'{path}: TL;DR needs exactly three bullets')
    require(text.index('## TL;DR')<text.index('## 1.'),f'{path}: TL;DR must precede goals')
    for h in ['### Trực giác 60 giây','### Từ vựng','### Ví dụ nhỏ — tính tay trước','### Walkthrough — execution / state / cost','### Mini-check','### So sánh để chọn đúng','### Misconception check','### Ba tầng học']:
        require(bool(heading_body(text,h)),f'{path}: empty clarity section {h}')
    require(text.index('### Trực giác')<text.index('### Từ vựng')<text.index('### Ví dụ nhỏ')<text.index('## 3.')<text.index('### Walkthrough')<text.index('## 4.'),f'{path}: beginner-first sequence violated')
    vocabulary=heading_body(text,'### Từ vựng')
    require('| Thuật ngữ | Nghĩa đơn giản | Trong bài này |' in vocabulary,f'{path}: vocabulary table contract missing')
    for table in [vocabulary,heading_body(text,'### So sánh để chọn đúng')]:
        rows=[x for x in table.splitlines() if x.startswith('|') and not x.startswith('|---')]
        require(len(rows)>=3 and all(all(c.strip() for c in r.strip('|').split('|')) for r in rows),f'{path}: table needs header and two nonempty data rows')
    misconception=heading_body(text,'### Misconception check')
    require(2<=misconception.count('**Đúng hay sai?**')<=4,f'{path}: expected 2–4 misconceptions')
    require(misconception.count('<details')==misconception.count('**Đúng hay sai?**'),f'{path}: answers need visual separation')
    levels=heading_body(text,'### Ba tầng học')
    require(all(x in levels for x in ('Beginner core','Working Developer','Deep Dive')),f'{path}: missing learning level')
    require(3<=len(re.findall(r'^\d+\. ',heading_body(text,'## 11. Retrieval practice'),re.M))<=5,f'{path}: expected 3–5 retrieval questions')
    for number in (7,8,10,11):
        require(bool(heading_body(text,f'## {number}. {SECTIONS[number-1]}')),f'{path}: empty required section {number}')
    check_links(path,text)


def check_module(module):
    require(module in ACTIVE,f'Module {module} has no activated v4 retrofit gate yet')
    directory,count,clusters=ACTIVE[module]
    folder=ROADMAP/directory
    lessons=sorted(folder.glob('[0-9][0-9]-*.md'))
    manifest=re.findall(r'^- \[[ xX]\] `('+re.escape(directory)+r'/[^`]+)`$',(ROADMAP/'PROGRESS.md').read_text(),re.M)
    require(len(lessons)==count and {p.relative_to(ROADMAP).as_posix() for p in lessons}==set(manifest),f'Module {module}: manifest mismatch')
    for lesson in lessons:
        check_lesson(lesson)
    artifacts={
        'failure-labs':('*.md',['Bối cảnh','Code lỗi','Triệu chứng','Cách tái hiện','Acceptance criteria','Hints','Checklist điều tra']),
        'reviews':('review-*.md',['Retrieval','Dự đoán output','Debug','Judgment liên module','Self-score']),
        'pr-review-labs':('*.md',['Diff','Nhiệm vụ review','Rubric','Submission format'])}
    for kind,(pattern,headers) in artifacts.items():
        paths=sorted((folder/kind).glob(pattern))
        minimum=1 if kind=='pr-review-labs' else len(clusters)
        require(len(paths)>=minimum,f'{folder}: insufficient {kind}')
        for path in paths:
            text=path.read_text()
            for h in headers:
                require(bool(heading_body(text,'## '+h)),f'{path}: empty {h}')
            if kind=='failure-labs':
                require(not re.search(r'^## (Lời giải|Full solution)',text,re.M),f'{path}: solution exposed')
                require(2<=len(re.findall(r'^\d+\. ',heading_body(text,'## Hints'),re.M))<=4,f'{path}: expected 2–4 hints')
            if kind=='reviews':
                require(len(re.findall(r'^\d+\. ',heading_body(text,'## Retrieval'),re.M))==5,f'{path}: expected 5 retrieval tasks')
                require(len(re.findall(r'^\d+\. ',heading_body(text,'## Dự đoán output'),re.M))==2,f'{path}: expected 2 prediction tasks')
            check_links(path,text)
    # Enforce the learning path, not just artifact counts in a disconnected folder.
    for start,end in clusters:
        require(4<=end-start+1<=6,f'Module {module}: bad review cadence')
        endpoint=lessons[end-1].read_text()
        require('./reviews/' in endpoint and './failure-labs/' in endpoint,f'{lessons[end-1]}: missing cluster links')
    diffs=list((folder/'pr-review-labs/diffs').glob('*.diff'))
    require(diffs and all('@@ ' in p.read_text() for p in diffs),f'{folder}: missing real PR patch')
    require('./pr-review-labs/' in lessons[-1].read_text(),f'{folder}: capstone lacks PR review link')
    if module=='05':
        require((folder/'career-checkpoint/index.md').exists(),'Missing C# Foundation checkpoint')
    for path in folder.rglob('*.md'):
        check_links(path,path.read_text())
    print(f'Module {module}: structural clarity v4 + links + assessment cadence passed; human review required.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('module', choices=ACTIVE)
    check_module(parser.parse_args().module)
