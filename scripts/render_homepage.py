#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from build_pr_preview import render_homepage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render homepage progress markers from PROGRESS.md."
    )
    parser.add_argument("--docs", type=Path, default=Path("fullstack-roadmap"))
    args = parser.parse_args()

    docs = args.docs.resolve()
    render_homepage(docs / "index.md", docs / "PROGRESS.md")


if __name__ == "__main__":
    main()
