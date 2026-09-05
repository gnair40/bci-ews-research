#!/usr/bin/env python3
"""
Does the research log account for every date that has commits?

The log is the project's primary record. It is worth nothing if a day's work can
vanish from it silently -- and on 5 September an audit found exactly that risk:
commits exist on 30 and 31 August with no heading carrying those dates. The work
was recorded, but under headings dated 28 August and 1 September, because those
sessions ran across midnight.

That is not a falsified record; it is an unreconciled one. This makes the
reconciliation explicit and checkable, so the next gap is caught by a gate rather
than by someone happening to grep.

WHAT IS CHECKED
---------------
Every date with at least one commit must either
  (a) appear as a heading in research/research_log.md, in either format used --
      ISO (2026-08-16) or written (16 August 2026), including ranges, or
  (b) appear in the RECONCILED table below, which names where that day's work is
      described instead.

Anything else is an unaccounted date and fails the gate.

Usage: python3 scripts/65_log_coverage.py
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "research" / "research_log.md"

MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}

# Dates whose work is logged under a different heading, with where to find it.
# Sessions here routinely ran past midnight, so a heading carries the date the
# work began rather than the date its commits landed.
RECONCILED = {
    "2026-08-30": "Logged under '28 August 2026 — One measurement per session'. "
                  "That session began on the 28th and its commits landed on the 30th.",
    "2026-08-31": "Logged under '28 August 2026 — The live demonstration' and "
                  "'— Checking that the documents still match the data', plus "
                  "'1 September 2026 — The feature study'. Same midnight-spanning "
                  "sessions.",
}


def commit_dates() -> set[str]:
    out = subprocess.run(["git", "log", "--date=short", "--pretty=format:%ad"],
                         cwd=REPO, capture_output=True, text=True).stdout
    return {d for d in out.split() if d}


def logged_dates(text: str) -> set[str]:
    found: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("## "):
            continue
        # ISO form, e.g. "## 2026-08-16 — Day 1"
        for m in re.finditer(r"(20\d\d)-(\d\d)-(\d\d)", line):
            found.add(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")
        # Written form, e.g. "## 26 August 2026" or "## 2-3 September 2026",
        # where a range means every day it spans is accounted for.
        for m in re.finditer(r"(\d{1,2})(?:\s*[–-]\s*(\d{1,2}))?\s+"
                             r"([A-Z][a-z]+)\s+(20\d\d)", line):
            d1, d2, mon, yr = m.groups()
            if mon not in MONTHS:
                continue
            lo, hi = int(d1), int(d2 or d1)
            for day in range(lo, hi + 1):
                try:
                    found.add(date(int(yr), MONTHS[mon], day).isoformat())
                except ValueError:
                    pass
    return found


def main() -> int:
    if not LOG.exists():
        print("research_log.md missing")
        return 1
    commits = commit_dates()
    logged = logged_dates(LOG.read_text())
    reconciled = set(RECONCILED)

    accounted = logged | reconciled
    missing = sorted(commits - accounted)

    print(f"log coverage: {len(commits)} dates with commits\n")
    for d in sorted(commits):
        if d in logged:
            mark, note = "logged", ""
        elif d in reconciled:
            mark, note = "reconciled", f"  {RECONCILED[d]}"
        else:
            mark, note = "UNACCOUNTED", ""
        print(f"  {d}  {mark}{note}")

    out = {"n_commit_dates": len(commits), "n_logged": len(commits & logged),
           "n_reconciled": len(commits & reconciled),
           "unaccounted": missing}
    (REPO / "data" / "processed" / "log_coverage.json").write_text(
        json.dumps(out, indent=2))

    if missing:
        print(f"\n{len(missing)} UNACCOUNTED date(s): {', '.join(missing)}")
        print("Either add a log entry for that date, or add it to RECONCILED "
              "with the heading that describes its work. Do NOT re-date an "
              "existing entry to make this pass -- that falsifies the record.")
        return 1
    print("\nPASS — every commit date is logged or reconciled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
