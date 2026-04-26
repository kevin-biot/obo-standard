#!/usr/bin/env python3
"""Fail when public artifacts still refer to the previous OBO draft id."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STALE = "draft-obo-agentic-evidence-envelope-00"
SCOPES = ["README.md", "docs", "examples", "profiles", "schemas"]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for scope in SCOPES:
        path = ROOT / scope
        if path.is_file():
            files.append(path)
        else:
            files.extend(p for p in path.rglob("*") if p.is_file())
    return files


def main() -> int:
    offenders: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(errors="ignore")
        except UnicodeDecodeError:
            continue
        if STALE in text:
            offenders.append(str(path.relative_to(ROOT)))

    if offenders:
        print("stale draft references found:", file=sys.stderr)
        for offender in offenders:
            print(f"  {offender}", file=sys.stderr)
        return 1

    print("no stale draft-00 references found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
