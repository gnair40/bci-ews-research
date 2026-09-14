#!/usr/bin/env python3
"""
68_rig_pipeline_dryrun.py
=========================
Does the whole analysis pipeline actually run on a rig participant?

=============================================================================
  THE DATA THIS BUILDS IS NOT DATA. NO CLAIM MAY CITE ANY NUMBER IT PRODUCES.
=============================================================================

`research/RIG_PROCEDURE.md` promises that the existing analysis runs unchanged
on rig recordings, and calls that the project's strongest defence against the
charge that the result was shaped to fit. Until 14 September 2026 that promise
had never been executed. `67_rig_format_check.py` proved the FILE FORMAT loads;
it did not run a single analysis stage.

Running it found three things the format check could not:

  1. Scripts 17, 18 and 20 called the loader with no root, so they always read
     data/raw and would never have looked at data/raw_rig, where the procedure
     says to put rig recordings. They now take --raw-root.
  2. Script 18 loaded the rig dataset and then looked its blocks up in
     data/processed/blocks.csv, a cache of the ARCHIVED data. Nothing matched,
     `blocks` came out empty, and the fit died with "only 0 days; cannot split
     into train/val/test". Scripts 18 and 20 now use the tables the loader just
     produced.
  3. Script 21 used pd.Timestamp.utcnow(), deprecated in pandas 3 and removed
     later. That warning was firing on every archived run too, unread.

All three would have been discovered on build day, with hardware on the bench.

WHAT THIS IS FOR, AND WHAT IT IS NOT FOR
----------------------------------------
It answers "does the code run", not "what is the answer". The fixture's numbers
are a property of the equations below and nothing else, so reading a result off
them would be the circularity PROJECT_DEFINITION.md 5.5 forbids. Everything it
creates is deleted before it exits, including from data/processed and reports/,
and it refuses to run if that cleanup would collide with a real file.

The participant is called RIG9 rather than RIG so that a stray artefact is
obvious, and so this can never be mistaken for the real rig data that will
eventually live under RIG.

Usage:
    python3 scripts/68_rig_pipeline_dryrun.py
    python3 scripts/68_rig_pipeline_dryrun.py --keep   # leave the fixture
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import savemat

REPO = Path(__file__).resolve().parent.parent
PROCESSED = REPO / "data" / "processed"
REPORTS = REPO / "reports"

PART = "RIG9"                 # never "RIG", which is reserved for real data
N_CH = 64
N_DAYS, N_BLOCKS, N_BINS, HOLD = 6, 2, 6000, 100
SEED = 20260826


def build_fixture(root: Path) -> None:
    rng = np.random.default_rng(SEED)
    pref = rng.uniform(0, 2 * np.pi, N_CH)
    for day in range(1, N_DAYS + 1):
        for blk in range(1, N_BLOCKS + 1):
            bd = root / PART / f"day_{day}" / f"block_{blk}"
            bd.mkdir(parents=True)
            n_tr = N_BINS // HOLD
            head = np.repeat(rng.uniform(0, 2 * np.pi, n_tr), HOLD)[:N_BINS]
            X = np.clip(0.5 * (1 + np.cos(head[:, None] - pref[None, :])) * 40
                        + rng.normal(0, 12, (N_BINS, N_CH)), 0, None)
            st = (np.arange(n_tr) * HOLD + 1).astype(float)
            savemat(bd / "data.mat", {"nctx": X.astype(np.float32),
                                      "FIXTURE_NOT_DATA": "synthetic"})
            savemat(bd / "info.mat", {
                "cursorPos": np.zeros((N_BINS, 2), np.float32),
                "targetPos": np.stack([np.cos(head), np.sin(head)], 1).astype(np.float32),
                "angleErrorPerTrial": rng.uniform(40, 70, n_tr),
                "trialSuccess": np.ones(n_tr, bool),
                "timeToTarget": rng.uniform(2, 5, n_tr),
                "pathEfficiency": rng.uniform(0.5, 0.9, n_tr),
                "orthChanges": rng.integers(0, 4, n_tr).astype(float),
                "percentCorrect": 95.0, "FIXTURE_NOT_DATA": "synthetic"})
            savemat(bd / "task.mat", {
                "startStops": np.stack([st, st + HOLD - 1], 1),
                "name": "rigDryRun",
                "excludeTrials": np.zeros(n_tr, bool),
                "useClick": np.zeros(n_tr, bool),
                "FIXTURE_NOT_DATA": "synthetic"})


def artefacts() -> list[Path]:
    """Everything a dry run can create. Checked before AND after."""
    return (sorted(PROCESSED.glob(f"*{PART}*"))
            + sorted(REPORTS.glob(f"*{PART}*")))


def stage(label: str, cmd: list[str]) -> bool:
    r = subprocess.run([sys.executable] + cmd, cwd=REPO,
                       capture_output=True, text=True, timeout=1800)
    ok = r.returncode == 0
    print(f"  {label:<34} {'ok' if ok else 'FAILED'}")
    if not ok:
        tail = (r.stdout + r.stderr).strip().split("\n")[-4:]
        for line in tail:
            print(f"      {line[:96]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    print("=" * 74)
    print("  RIG PIPELINE DRY RUN -- the fixture is NOT DATA and no claim")
    print("  in this project may cite any number it produces.")
    print("=" * 74)

    pre = artefacts()
    if pre:
        print("\nREFUSING TO RUN: files matching the dry-run participant already "
              "exist, and cleaning up would delete them:")
        for f in pre:
            print(f"  {f.relative_to(REPO)}")
        return 1

    root = Path(tempfile.mkdtemp(prefix="rig_dryrun_"))
    try:
        print(f"\nBuilding fixture: {N_DAYS} days x {N_BLOCKS} blocks x "
              f"{N_BINS} bins x {N_CH} channels")
        build_fixture(root)

        print("\nRunning the pipeline, unmodified, against it:")
        stages = [
            ("17 injector -- lock the plan",
             ["scripts/17_fault_injector.py", "plan",
              "--participant", PART, "--raw-root", str(root)]),
            ("17 injector -- verify invariants",
             ["scripts/17_fault_injector.py", "verify",
              "--participant", PART, "--raw-root", str(root)]),
            ("18 reference decoder -- fit and freeze",
             ["scripts/18_reference_decoder.py", "fit",
              "--participant", PART, "--raw-root", str(root)]),
            ("20 harness -- score episodes",
             ["scripts/20_evaluation_harness.py", "run",
              "--participant", PART, "--raw-root", str(root), "--limit", "40"]),
            ("21 score report -- gates and write-up",
             ["scripts/21_score_report.py", "--participant", PART]),
        ]
        results = [stage(lbl, cmd) for lbl, cmd in stages]
    finally:
        made = artefacts()
        if not a.keep:
            for f in made:
                f.unlink()
            shutil.rmtree(root, ignore_errors=True)
            left = artefacts()
            print(f"\ncleaned up {len(made)} artefact(s); "
                  f"{len(left)} left behind" + (" -- PROBLEM" if left else ""))
        else:
            print(f"\nkept fixture at {root} and {len(made)} artefact(s) "
                  f"-- NOT DATA, delete when done")

    print("=" * 74)
    if all(results):
        print("PASS -- every pipeline stage runs on a rig participant, with no")
        print("        change to any analysis script beyond --raw-root.")
        return 0
    print(f"FAIL -- {results.count(False)} of {len(results)} stages did not run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
