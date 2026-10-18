#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "fullstack-roadmap" / "08-sql-va-csdl"

SQL_BLOCK = re.compile(r"```sql\n(.*?)```", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(command: list[str], *, input_text: str | None = None, timeout: int = 120) -> str:
    completed = subprocess.run(
        command,
        text=True,
        input=input_text,
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
    return completed.stdout


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


def run_sql_sample(path: Path, text: str) -> None:
    blocks = SQL_BLOCK.findall(text)
    if not blocks:
        fail(f"{path}: no SQL code block found")

    # Mỗi bài có nhiều snippet nhỏ. Block lớn nhất là lab chính,
    # được thiết kế để chạy độc lập trên database sạch.
    sample = max(blocks, key=len)

    container = os.environ.get("MODULE08_SQL_CONTAINER", "module08-sql")
    password = os.environ.get("MODULE08_SA_PASSWORD", "SqlLab!2026Strong")

    with tempfile.TemporaryDirectory(prefix="module08-") as directory:
        local_file = Path(directory) / "sample.sql"
        local_file.write_text(sample, encoding="utf-8")

        remote_file = f"/tmp/{path.stem}.sql"

        run(
            [
                "docker",
                "cp",
                str(local_file),
                f"{container}:{remote_file}",
            ]
        )

        print(f"\n=== {path.name}: SQL Server 2025 ===")

        run(
            [
                "docker",
                "exec",
                container,
                "/opt/mssql-tools18/bin/sqlcmd",
                "-S",
                "localhost",
                "-U",
                "sa",
                "-P",
                password,
                "-C",
                "-b",
                "-r1",
                "-i",
                remote_file,
            ],
            timeout=180,
        )


def main() -> None:
    files = sorted(MODULE.glob("[0-9][0-9]-*.md"))

    if len(files) != 25:
        fail(f"expected 25 lessons, found {len(files)}")

    expected = [f"{number:02d}" for number in range(1, 26)]
    actual = [path.name[:2] for path in files]

    if actual != expected:
        fail(
            "lesson numbering is incomplete or duplicated: "
            f"expected {expected}, got {actual}"
        )

    for path in files:
        text = path.read_text(encoding="utf-8")
        check_structure(path, text)
        check_links(path, text)
        run_sql_sample(path, text)

    print("\nModule 08 verification passed: 25/25 lessons.")


if __name__ == "__main__":
    main()
