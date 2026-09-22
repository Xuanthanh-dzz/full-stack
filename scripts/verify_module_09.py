#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "fullstack-roadmap" / "09-linq-va-ef-core"
PROGRESS = ROOT / "fullstack-roadmap" / "PROGRESS.md"

HEADING = re.compile(r"^##\s+(\d{2})-([^\n]+)$", re.MULTILINE)
CHECKBOX = re.compile(r"^- \[([ xX])\] `([^`]+)`$", re.MULTILINE)
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CSHARP_BLOCK = re.compile(r"~~~csharp\n(.*?)~~~", re.DOTALL)
LAST_VERIFIED = re.compile(r"> \*\*Last verified:\*\*\s*(\d{4}-\d{2}-\d{2})")
REVIEW_CYCLE = re.compile(r"> \*\*Review cycle:\*\*\s*(\d+)\s*days", re.IGNORECASE)

REQUIRED_SECTIONS = [f"## {number}." for number in range(1, 13)]

FORBIDDEN_TERMS = {
    "chu kỳ sống": "vòng đời",
    "tải háo hức": "eager loading",
    "tải lười": "lazy loading",
    "khóa chết": "deadlock",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def module_manifest() -> list[str]:
    text = PROGRESS.read_text(encoding="utf-8")
    start = text.find("## 09-linq-va-ef-core")
    end = text.find("## 10-web-nen-tang")
    if start == -1 or end == -1 or end <= start:
        fail("Module 09 manifest block not found in PROGRESS.md")

    section = text[start:end]
    paths = [
        match.group(2)
        for match in CHECKBOX.finditer(section)
        if match.group(2).startswith("09-linq-va-ef-core/")
    ]
    if len(paths) != 24:
        fail(f"Expected 24 Module 09 manifest lessons, found {len(paths)}")
    return paths


def check_links(path: Path, text: str) -> None:
    for raw in LINK.findall(text):
        if raw.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = raw.split("#", 1)[0]
        if not target or not target.endswith(".md"):
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            fail(f"{path}: link escapes repository: {raw}")
        if not resolved.exists():
            fail(f"{path}: broken local link: {raw}")


def check_tldr(path: Path, text: str) -> None:
    start = text.find("## TL;DR")
    end = text.find("## 1. Mục tiêu")
    if start == -1 or end == -1 or end <= start:
        fail(f"{path}: missing TL;DR before section 1")
    body = text[start:end]
    bullets = [line for line in body.splitlines() if line.startswith("- ")]
    if len(bullets) != 3:
        fail(f"{path}: TL;DR must contain exactly 3 bullet lines, found {len(bullets)}")


def check_freshness(path: Path, text: str, today: date) -> None:
    verified = LAST_VERIFIED.search(text)
    cycle = REVIEW_CYCLE.search(text)
    if not verified or not cycle:
        fail(f"{path}: missing Last verified / Review cycle metadata")
    verified_date = datetime.strptime(verified.group(1), "%Y-%m-%d").date()
    cycle_days = int(cycle.group(1))
    age = (today - verified_date).days
    if age < 0:
        fail(f"{path}: Last verified date is in the future: {verified_date}")
    if age > cycle_days:
        fail(f"{path}: stale verification metadata: age={age}d cycle={cycle_days}d")


def check_lesson(path: Path, today: date) -> None:
    text = path.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            fail(f"{path}: missing required section {section}")
    if "## 7. Khi nào KHÔNG dùng" not in text:
        fail(f"{path}: section 7 must be Khi nào KHÔNG dùng")
    if "## 10. Bài tập tích hợp liên module — Judgment" not in text:
        fail(f"{path}: missing cross-module judgment section")
    if "## 11. Retrieval practice" not in text:
        fail(f"{path}: missing retrieval practice")
    check_tldr(path, text)
    check_freshness(path, text, today)
    check_links(path, text)
    lowered = text.lower()
    for forbidden, preferred in FORBIDDEN_TERMS.items():
        if forbidden in lowered:
            fail(f"{path}: forbidden terminology '{forbidden}'; prefer '{preferred}'")



def check_supplemental_artifacts() -> None:
    failure_dir = MODULE / "failure-labs"
    review_dir = MODULE / "reviews"
    pr_review_dir = MODULE / "pr-review-labs"
    checkpoint = MODULE / "career-checkpoint" / "index.md"

    failure_labs = sorted(failure_dir.glob("[0-9][0-9]-*.md"))
    reviews = sorted(review_dir.glob("review-*.md"))
    pr_reviews = sorted(pr_review_dir.glob("[0-9][0-9]-*.md"))
    published_diffs = sorted((pr_review_dir / "diffs").glob("*.diff"))

    if len(failure_labs) != 4:
        fail(f"Expected 4 Failure Labs, found {len(failure_labs)}")
    if len(reviews) != 5:
        fail(f"Expected 5 Spaced Reviews, found {len(reviews)}")
    if len(pr_reviews) != 2:
        fail(f"Expected 2 PR Review Labs, found {len(pr_reviews)}")
    if len(published_diffs) != 2:
        fail(f"Expected 2 published PR diff artifacts, found {len(published_diffs)}")
    if not checkpoint.exists():
        fail("Missing Module 09 career checkpoint")

    required_failure_sections = [
        "## Bối cảnh",
        "## Triệu chứng",
        "## Cách tái hiện",
        "## Acceptance criteria",
        "## Hints",
        "## Checklist điều tra",
    ]
    for path in failure_labs:
        text = path.read_text(encoding="utf-8")
        for section in required_failure_sections:
            if section not in text:
                fail(f"{path}: missing Failure Lab section {section}")
        if "## Lời giải" in text or "## Full solution" in text:
            fail(f"{path}: Failure Lab must not contain a full solution section")
        check_links(path, text)

    for path in reviews:
        text = path.read_text(encoding="utf-8")
        for section in ("## Retrieval", "## Debug", "## Judgment liên module", "## Self-score"):
            if section not in text:
                fail(f"{path}: missing Spaced Review section {section}")
        check_links(path, text)

    for path in pr_reviews:
        text = path.read_text(encoding="utf-8")
        for section in ("## Diff", "## Nhiệm vụ review", "## Rubric", "## Submission format"):
            if section not in text:
                fail(f"{path}: missing PR Review section {section}")
        check_links(path, text)

    checkpoint_text = checkpoint.read_text(encoding="utf-8")
    for section in (
        "## 1. Knowledge test",
        "## 2. Build task",
        "## 3. Debugging task",
        "## 4. PR review task",
        "## 5. Judgment tasks",
        "## 6. Interview-style explanation",
        "## 7. Competency matrix",
        "## 8. Remediation map",
    ):
        if section not in checkpoint_text:
            fail(f"{checkpoint}: missing career checkpoint section {section}")
    check_links(checkpoint, checkpoint_text)

    print("Supplemental assessment gate passed: 4 Failure Labs, 5 Spaced Reviews, 2 PR Reviews, 1 Career Checkpoint.")

def compile_linq_samples(paths: list[Path]) -> None:
    for path in paths[:10]:
        text = path.read_text(encoding="utf-8")
        blocks = CSHARP_BLOCK.findall(text)
        if not blocks:
            fail(f"{path}: no csharp block found for LINQ compile gate")
        source = blocks[0]
        with tempfile.TemporaryDirectory(prefix="module09-linq-") as temp:
            temp_path = Path(temp)
            (temp_path / "Program.cs").write_text(source, encoding="utf-8")
            (temp_path / "Sample.csproj").write_text(
                """<Project Sdk=\"Microsoft.NET.Sdk\">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
""",
                encoding="utf-8",
            )
            print(f"Compiling standalone sample: {path.name}")
            completed = subprocess.run(
                ["dotnet", "build", "Sample.csproj", "--nologo", "-v", "minimal"],
                cwd=temp_path,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            print(completed.stdout)
            if completed.returncode != 0:
                fail(f"{path}: standalone C# sample failed to compile")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-linq", action="store_true")
    parser.add_argument("--today", default=None)
    args = parser.parse_args()

    today = (
        datetime.strptime(args.today, "%Y-%m-%d").date()
        if args.today
        else date.today()
    )

    manifest = module_manifest()
    paths = [ROOT / "fullstack-roadmap" / relative for relative in manifest]
    for path in paths:
        if not path.exists():
            fail(f"Manifest lesson does not exist: {path}")

    actual = sorted(MODULE.glob("[0-9][0-9]-*.md"))
    if len(actual) != 24:
        fail(f"Expected 24 lesson files, found {len(actual)}")

    if {path.resolve() for path in paths} != {path.resolve() for path in actual}:
        fail("Manifest lesson set does not match actual Module 09 files")

    for path in paths:
        check_lesson(path, today)

    check_supplemental_artifacts()

    if args.compile_linq:
        compile_linq_samples(paths)

    print("Module 09 quality gate passed: 24/24 lessons + supplemental assessment artifacts.")


if __name__ == "__main__":
    main()
