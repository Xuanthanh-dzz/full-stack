#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

# UI/build shell is always owned by main. A PR may contain stale copies of
# these files, but preview assembly intentionally ignores them.
UI_OWNED_DOC_PATHS = {
    Path("index.md"),
    Path(".pages"),
}

UI_OWNED_DOC_DIRS = {
    Path("stylesheets"),
    Path("javascripts"),
    Path("overrides"),
}

MAIN_OWNED_ROOT_FILES = {
    "mkdocs.yml",
    "requirements-docs.txt",
}


def should_overlay(relative_path: Path) -> bool:
    if relative_path in UI_OWNED_DOC_PATHS:
        return False

    if relative_path.parts and Path(relative_path.parts[0]) in UI_OWNED_DOC_DIRS:
        return False

    return True


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


MODULE_META = {
    7: (
        "Cấu Trúc Dữ Liệu & Giải Thuật",
        "material-source-branch",
        "Big-O, array, linked list, hash table, tree, heap, graph, BFS/DFS, Dijkstra, sorting, greedy, backtracking, dynamic programming và Route Engine.",
    ),
    8: (
        "SQL & Cơ Sở Dữ Liệu",
        "material-database",
        "Mô hình quan hệ, CRUD, JOIN, CTE, window function, chuẩn hóa, index, transaction, isolation, execution plan, security, backup/migration và capstone CSDL thương mại điện tử.",
    ),
    9: (
        "LINQ & Entity Framework Core",
        "material-database-cog",
        "LINQ, IQueryable, expression tree, EF Core, migration, tracking, relationship, transaction, performance, testing và data-access architecture.",
    ),
}

PLANNING_GROUPS = [
    ([7], "07", "Cấu trúc dữ liệu & Giải thuật"),
    ([8], "08", "SQL & Database Design"),
    ([9], "09", "LINQ & Entity Framework Core"),
    ([10, 11, 12, 13], "10-13", "Web Foundation, ASP.NET Core & React/Angular"),
    ([14, 15], "14-15", "Testing, CI/CD, Docker & DevOps"),
    ([16, 17, 18, 19, 20], "16-20", "Design Patterns, Microservices & System Design"),
    ([21], "21", "Dự án tổng hợp"),
]


def parse_progress(progress_path: Path) -> dict[int, dict[str, object]]:
    text = progress_path.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^##\s+(\d{2})-([^\n]+)$", text, re.MULTILINE))
    result: dict[int, dict[str, object]] = {}

    for index, heading in enumerate(headings):
        number = int(heading.group(1))
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[start:end]
        pattern = rf"^- \[([ xX])\] `({number:02d}-[^/]+/[^`]+\.md)`$"
        lessons = list(re.finditer(pattern, section, re.MULTILINE))
        if not lessons:
            continue

        completed = sum(1 for lesson in lessons if lesson.group(1).lower() == "x")
        result[number] = {
            "total": len(lessons),
            "completed": completed,
            "done": completed == len(lessons),
            "first": lessons[0].group(2),
            "slug": heading.group(2).strip(),
        }

    return result


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end < start:
        raise RuntimeError(f"Missing homepage auto-progress markers: {start_marker} / {end_marker}")

    content_start = start + len(start_marker)
    return text[:content_start] + "\n" + replacement.rstrip() + "\n" + text[end:]


def render_homepage(index_path: Path, progress_path: Path) -> None:
    modules = parse_progress(progress_path)
    text = index_path.read_text(encoding="utf-8")

    lesson_count = sum(
        int(module["completed"])
        for number, module in modules.items()
        if number >= 1
    )

    cards: list[str] = []
    for number in sorted(modules):
        module = modules[number]
        if number <= 6 or not bool(module["done"]):
            continue

        title, icon, description = MODULE_META.get(
            number,
            (str(module["slug"]).replace("-", " ").title(), "material-book-check", "Module đã hoàn thành toàn bộ bài học và vượt Definition of Done của roadmap."),
        )
        first = str(module["first"])
        total = int(module["total"])
        cards.append(
            f"-   :{icon}:{{ .card-icon }}\n"
            f"    \n"
            f"    ### Module {number:02d}: {title}\n"
            f"    <span class=\"badge badge-success\">{total} Bài • Hoàn thành</span>\n"
            f"    \n"
            f"    {description}\n"
            f"    \n"
            f"    [:octicons-arrow-right-24: Học Module {number:02d}]({first})\n"
        )

    planning_rows: list[str] = [
        "| Module | Chủ đề chính | Trạng thái |",
        "|---|---|---|",
    ]
    for numbers, label, topic in PLANNING_GROUPS:
        known = [modules[number] for number in numbers if number in modules]
        if known and len(known) == len(numbers) and all(bool(module["done"]) for module in known):
            continue
        planning_rows.append(
            f'| **{label}** | {topic} | <span class="badge badge-warning">Đang biên soạn</span> |'
        )

    text = replace_between(
        text,
        "<!-- AUTO_LESSON_COUNT_START -->",
        "<!-- AUTO_LESSON_COUNT_END -->",
        f"{lesson_count}+",
    )
    text = replace_between(
        text,
        "<!-- AUTO_COMPLETED_MODULES_START -->",
        "<!-- AUTO_COMPLETED_MODULES_END -->",
        "\n".join(cards),
    )
    text = replace_between(
        text,
        "<!-- AUTO_PLANNING_ROWS_START -->",
        "<!-- AUTO_PLANNING_ROWS_END -->",
        "\n".join(planning_rows),
    )

    index_path.write_text(text, encoding="utf-8")
    done = [f"{number:02d}" for number, module in sorted(modules.items()) if number >= 1 and bool(module["done"])]
    print(
        "Homepage progress rendered from PROGRESS.md: "
        f"{lesson_count} completed lessons; completed modules={','.join(done)}"
    )


def assemble(main_root: Path, pr_root: Path, out_root: Path) -> None:
    if out_root.exists():
        shutil.rmtree(out_root)

    out_root.mkdir(parents=True)

    # Build configuration and dependency lock are always from main.
    for name in MAIN_OWNED_ROOT_FILES:
        copy_file(main_root / name, out_root / name)

    main_docs = main_root / "fullstack-roadmap"
    pr_docs = pr_root / "fullstack-roadmap"
    out_docs = out_root / "fullstack-roadmap"

    # Start from the latest UI/content shell on main.
    shutil.copytree(main_docs, out_docs)

    # Overlay PR-owned content only. This includes lesson markdown, module
    # .pages files, PROGRESS.md, README.md and roadmap content.
    # Top-level homepage/navigation and UI assets remain from main.
    for source in pr_docs.rglob("*"):
        if not source.is_file():
            continue

        relative = source.relative_to(pr_docs)
        if not should_overlay(relative):
            continue

        copy_file(source, out_docs / relative)

    # Homepage layout comes from main, but status/counts come from this ref's PROGRESS.md.
    render_homepage(out_docs / "index.md", out_docs / "PROGRESS.md")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble a PR docs preview using UI from main and content from the PR."
    )
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--pr", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    assemble(
        args.main.resolve(),
        args.pr.resolve(),
        args.out.resolve(),
    )

    print(f"Assembled preview source: {args.out}")
    print("UI source: main")
    print("Content source: PR")
    print("Homepage status source: assembled PROGRESS.md")


if __name__ == "__main__":
    main()
