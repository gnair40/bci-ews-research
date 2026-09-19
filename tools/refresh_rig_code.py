#!/usr/bin/env python3
"""
refresh_rig_code.py — keep research/RIG_CODE.md's inlined source current.

WHY THIS EXISTS
---------------
RIG_CODE.md carries the full source of every rig program inline, so that a file
lost from an SD card can be retyped from the documentation. That redundancy is
worth having on a project whose hardware lives on a memory card.

It also creates exactly the failure this project has already hit twice: a
document that is part hand-written and part generated. ACHIEVABILITY.md lost a
correction block that way in August, and DATASET_EXPLORATION.md lost three
sections of Phase 1-2 findings in September, both because someone regenerated a
file without knowing it had been edited by hand.

So the prose above the marker is hand-written and never touched, and everything
below it is regenerated from the real files. Neither half can quietly rot.

    python3 tools/refresh_rig_code.py            # rewrite the source sections
    python3 tools/refresh_rig_code.py --check    # fail if they are stale
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "research" / "RIG_CODE.md"
MARKER = "# Full source"

FILES = ["rig/run_block.py", "rig/bench.py", "rig/run_batch.py",
         "rig/daily_session.py", "rig/motor.py", "rig/logtemp.py",
         "rig/stimulus.py", "rig/capture.py", "rig/to_mat.py"]


def build_source_section() -> str:
    out = [MARKER, "",
           "Everything below is regenerated from the files themselves by",
           "`tools/refresh_rig_code.py`. **Do not edit it here** — edit the file and",
           "re-run that tool. Everything ABOVE this line is hand-written and is never",
           "touched by it.", ""]
    for rel in FILES:
        p = REPO / rel
        if not p.exists():
            out += [f"## `{rel}`", "", f"*Missing from the repository.*", ""]
            continue
        out += [f"## `{rel}`", "", "```python", p.read_text().rstrip(), "```", ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report staleness instead of fixing it")
    a = ap.parse_args()

    text = DOC.read_text()
    if MARKER not in text:
        print(f"{DOC} has no '{MARKER}' marker; cannot tell prose from source")
        return 1
    prose = text[:text.index(MARKER)].rstrip() + "\n\n"
    fresh = prose + build_source_section()

    if a.check:
        if fresh == text:
            print(f"PASS — the source inlined in {DOC.name} matches the "
                  f"{len(FILES)} files it documents")
            return 0
        print(f"STALE — {DOC.name} no longer matches the real files.\n"
              f"Run: python3 tools/refresh_rig_code.py")
        return 1

    if fresh == text:
        print("already current; nothing written")
        return 0
    DOC.write_text(fresh)
    print(f"refreshed {len(FILES)} source sections in {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
