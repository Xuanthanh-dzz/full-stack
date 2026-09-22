#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "fullstack-roadmap"

LAST_VERIFIED = re.compile(r"> \*\*Last verified:\*\*\s*(\d{4}-\d{2}-\d{2})")
REVIEW_CYCLE = re.compile(r"> \*\*Review cycle:\*\*\s*(\d+)\s*days", re.IGNORECASE)


def iter_lessons(start_module: int) -> list[Path]:
    lessons: list[Path] = []
    for directory in sorted(ROADMAP.iterdir()):
        if not directory.is_dir():
            continue

        match = re.match(r"^(\d{2})-", directory.name)
        if not match:
            continue

        module_number = int(match.group(1))
        if module_number < start_module:
            continue

        lessons.extend(sorted(directory.glob("[0-9][0-9]-*.md")))

    return lessons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-module", type=int, default=9)
    parser.add_argument("--today", type=str, default=None)
    args = parser.parse_args()

    today = (
        datetime.strptime(args.today, "%Y-%m-%d").date()
        if args.today
        else date.today()
    )

    missing: list[str] = []
    stale: list[str] = []

    for path in iter_lessons(args.start_module):
        text = path.read_text(encoding="utf-8")
        verified = LAST_VERIFIED.search(text)
        cycle = REVIEW_CYCLE.search(text)

        relative = path.relative_to(ROOT)

        if not verified or not cycle:
            missing.append(str(relative))
            continue

        verified_date = datetime.strptime(verified.group(1), "%Y-%m-%d").date()
        cycle_days = int(cycle.group(1))
        age_days = (today - verified_date).days

        if age_days > cycle_days:
            stale.append(
                f"{relative}: verified {verified_date}, "
                f"age={age_days}d, cycle={cycle_days}d"
            )

    if missing:
        print("Lessons missing freshness metadata:")
        for item in missing:
            print(f"  - {item}")

    if stale:
        print("Stale lessons requiring re-verification:")
        for item in stale:
            print(f"  - {item}")

    if missing or stale:
        return 1

    print(
        f"Freshness check passed for Module {args.start_module:02d}+ "
        f"on {today.isoformat()}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
