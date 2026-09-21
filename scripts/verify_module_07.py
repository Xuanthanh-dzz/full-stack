#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "fullstack-roadmap" / "07-cau-truc-du-lieu-giai-thuat"

CSHARP_BLOCK = re.compile(r"```csharp\n(.*?)```", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
"""


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_structure(path: Path, text: str) -> None:
    for section in range(1, 9):
        if f"## {section}." not in text:
            fail(f"{path}: missing section ## {section}.")


def check_links(path: Path, text: str) -> None:
    for raw in MARKDOWN_LINK.findall(text):
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
            fail(f"{path}: broken Markdown link: {raw}")


def run(command: list[str], cwd: Path, timeout: int = 60) -> None:
    print("$", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )

    print(completed.stdout)

    if completed.returncode != 0:
        fail(
            f"command failed with exit code {completed.returncode}: "
            + " ".join(command)
        )


def verify_csharp_sample(path: Path, text: str) -> None:
    blocks = CSHARP_BLOCK.findall(text)

    if not blocks:
        fail(f"{path}: no C# code block found")

    # Bài học có nhiều snippet nhỏ. Block lớn nhất là sample hoàn chỉnh
    # dùng để build/run trong module này.
    program = max(blocks, key=len)

    with tempfile.TemporaryDirectory(prefix="module07-") as directory:
        work = Path(directory)
        (work / "Sample.csproj").write_text(CSPROJ, encoding="utf-8")
        (work / "Program.cs").write_text(program, encoding="utf-8")

        print(f"\n=== {path.name}: build ===")
        run(
            ["dotnet", "build", "--nologo", "-warnaserror"],
            cwd=work,
            timeout=90,
        )

        print(f"=== {path.name}: run ===")
        run(
            ["dotnet", "run", "--no-build", "--nologo"],
            cwd=work,
            timeout=30,
        )


def main() -> None:
    if shutil.which("dotnet") is None:
        fail("dotnet SDK is not installed")

    files = sorted(MODULE.glob("[0-9][0-9]-*.md"))

    if len(files) != 19:
        fail(f"expected 19 lessons, found {len(files)}")

    prefixes = [path.name[:2] for path in files]
    expected = [f"{number:02d}" for number in range(1, 20)]

    if prefixes != expected:
        fail(
            "lesson numbering is incomplete or duplicated: "
            f"expected {expected}, got {prefixes}"
        )

    for path in files:
        text = path.read_text(encoding="utf-8")
        check_structure(path, text)
        check_links(path, text)
        verify_csharp_sample(path, text)

    print("\nModule 07 verification passed: 19/19 lessons.")


if __name__ == "__main__":
    main()
