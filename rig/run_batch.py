#!/usr/bin/env python3
"""
run_batch.py — record many blocks unattended, for the long arms of the study.

The drift sweep needs 5 levels x 53 blocks = 265 blocks, about 22 hours
(reports/DRIFT_SWEEP_DESIGN.md). Nobody is starting those by hand, and a study
run by hand at 2am is a study with a typo in it somewhere.

This reads a plan file -- one line per block, saying what to record -- and works
through it, skipping blocks already present so an interrupted run can simply be
restarted. It never overwrites a finished block.

    python3 rig/run_batch.py --plan rig/plans/sweep.txt
    python3 rig/run_batch.py --plan rig/plans/sweep.txt --dry-run
    python3 rig/run_batch.py --make-sweep-plan rig/plans/sweep.txt

PLAN FILE FORMAT
    One block per line, as arguments to run_block.py. Blank lines and lines
    starting with # are ignored.

        --session 10 --blocknum 1 --drift-tau 4 --drift-depth 0.3
        --session 10 --blocknum 2 --drift-tau 4 --drift-depth 0.3

A PHYSICAL FAULT CANNOT BE AUTOMATED
------------------------------------
Blocks carrying a fault you impose by hand -- the ND filter, tape on the lens, a
fingerprint -- must be run one at a time with run_block.py, because somebody has
to put the filter there. Use this only for the arms where nothing is touched:
healthy blocks, and the imposed-drift sweep, which the stimulus does in software.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RIG = Path(__file__).resolve().parent
REPO = RIG.parent


def sweep_plan(path: Path, session: int, levels, blocks: int, depth: float) -> None:
    """The 5-level drift sweep from reports/DRIFT_SWEEP_DESIGN.md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Drift sweep. Levels and block count computed by",
             "# scripts/71_drift_sweep_design.py -- not guessed.",
             "# Nothing is touched by hand during these, so they can run unattended.",
             ""]
    n = 1
    for tau in levels:
        lines.append(f"# --- tau = {tau:g} s ---")
        for _ in range(blocks):
            lines.append(f"--session {session} --blocknum {n} "
                         f"--drift-tau {tau:g} --drift-depth {depth} "
                         f"--fault IMPOSED_DRIFT --note tau={tau:g}")
            n += 1
        lines.append("")
    path.write_text("\n".join(lines) + "\n")
    total = len(levels) * blocks
    print(f"wrote {path}: {total} blocks, about "
          f"{total * 300 / 3600:.1f} hours of recording")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan")
    ap.add_argument("--make-sweep-plan")
    ap.add_argument("--session", type=int, default=10)
    ap.add_argument("--levels", type=float, nargs="+",
                    default=[4, 13, 42, 140, 811])
    ap.add_argument("--blocks", type=int, default=53)
    ap.add_argument("--drift-depth", type=float, default=0.3)
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.make_sweep_plan:
        sweep_plan(Path(a.make_sweep_plan), a.session, a.levels, a.blocks,
                   a.drift_depth)
        return 0
    if not a.plan:
        ap.error("give --plan, or --make-sweep-plan to create one")

    lines = [l.strip() for l in Path(a.plan).read_text().splitlines()]
    jobs = [l for l in lines if l and not l.startswith("#")]
    print(f"{len(jobs)} blocks in {a.plan}")

    done = failed = skipped = 0
    for i, job in enumerate(jobs, 1):
        parts = job.split()
        try:
            sess = parts[parts.index("--session") + 1]
            blk = parts[parts.index("--blocknum") + 1]
        except ValueError:
            print(f"[{i}] malformed line, no --session/--blocknum: {job}")
            failed += 1
            continue

        out = REPO / a.root / "RIG" / f"day_{sess}" / f"block_{blk}"
        if out.exists():
            skipped += 1
            continue

        cmd = [sys.executable, str(RIG / "run_block.py")] + parts
        if a.dry_run:
            cmd.append("--dry-run")
        print(f"[{i}/{len(jobs)}] session {sess} block {blk}")
        if subprocess.run(cmd).returncode == 0:
            done += 1
        else:
            failed += 1
            print("  FAILED — continuing. Check rig/blocklog.csv before trusting "
                  "this session, and re-run this plan to fill the gap.")

    print(f"\nrecorded {done}, skipped {skipped} already present, {failed} failed")
    if failed:
        print("Re-running the same plan will retry only the missing blocks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
