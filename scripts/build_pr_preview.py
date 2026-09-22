#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


if __name__ == "__main__":
    main()
