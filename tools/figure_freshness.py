#!/usr/bin/env python3
"""
figure_freshness.py
===================
Does every committed figure still match the script that draws it?

WHY THIS EXISTS
---------------
On 17 September 2026 `reports/figures/13_auc_by_fault_mode.png` was found to
disagree with `scripts/23_benchmark_figures.py`. Every number in it was right.
What was missing was the y-axis label's second line, "(window-level AUC)" --
which is precisely the disclosure that the bars are a window-level quantity, the
thing the claims register warns must not be read as an episode-level result.

The cause was ordinary. Figures were gitignored while the project was being
written, so the copies on disk drifted from the scripts. When figures were later
added to version control, whatever happened to be on disk was frozen in, and the
stale one went with it. It sat wrong for thirteen days.

WHY IT IS NOT ONE OF THE FIVE GATES
-----------------------------------
`scripts/55_reproducibility_audit.py` is deliberately static: it needs no data
and runs in a second, which is why it can run before every commit. This check
has to actually redraw the figures and compare bytes, because the cheap
alternatives do not work:

  - Comparing modification times fails: git sets them to checkout time.
  - Comparing commit dates fails on exactly the case that motivated this. The
    script changed in commit 110 and the figure was committed in 111, so the
    figure's last commit is NEWER than the script's and a date comparison calls
    it fresh. It was not.

So the only honest check is to redraw and compare, and that is too slow to gate
every commit. It is a tool you run deliberately.

A CAVEAT WORTH STATING
----------------------
A mismatch means the figure and its script disagree HERE. A different matplotlib
or freetype version can also change PNG bytes without anything being wrong, so a
mismatch on someone else's machine is a prompt to look, not proof of staleness.
The fast set below was verified byte-reproducible on the machine this was written
on.

Usage:
    python3 tools/figure_freshness.py          # fast scripts only, no raw data
    python3 tools/figure_freshness.py --all    # also the ones needing data/raw
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIGS = REPO / "reports" / "figures"

# Scripts that redraw figures from data/processed alone.
FAST = ["16_phase12_synthesis.py", "23_benchmark_figures.py",
        "27_decision_rules.py", "40_calibration_report.py",
        "42_staleness_report.py"]

# Scripts that additionally need the raw archive under data/raw.
NEEDS_RAW = ["04_explore_dataset.py", "05_check_decoder_stability.py",
             "06_ews_controls.py", "07_ews_power_sweep.py",
             "09_reproduce_mindful.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true",
                    help="also run the scripts that need data/raw (slow)")
    args = ap.parse_args()

    scripts = FAST + (NEEDS_RAW if args.all else [])
    if args.all and not (REPO / "data" / "raw").exists():
        print("--all given but data/raw is missing; run the download first")
        return 2

    before = {p.name: sha(p) for p in sorted(FIGS.glob("*.png"))}
    backup = Path(tempfile.mkdtemp(prefix="figfresh-"))
    for p in FIGS.glob("*.png"):
        shutil.copy2(p, backup / p.name)

    ran, failed = [], []
    try:
        for s in scripts:
            r = subprocess.run([sys.executable, str(REPO / "scripts" / s)],
                               capture_output=True, text=True, cwd=REPO)
            (ran if r.returncode == 0 else failed).append(s)

        after = {p.name: sha(p) for p in sorted(FIGS.glob("*.png"))}
        stale = sorted(n for n, h in after.items()
                       if n in before and before[n] != h)
        added = sorted(set(after) - set(before))
    finally:
        # Always put the committed figures back. This tool reports; it does not
        # decide to overwrite tracked artifacts.
        for p in backup.glob("*.png"):
            shutil.copy2(p, FIGS / p.name)
        shutil.rmtree(backup, ignore_errors=True)

    print(f"redrew {len(ran)} script(s)"
          + (f", {len(failed)} failed to run: {', '.join(failed)}" if failed else ""))
    print(f"checked {len(before)} committed figure(s)"
          + ("" if args.all else "; skipped the raw-data scripts (use --all)"))

    if added:
        print("\nfigures produced that are not committed:")
        for n in added:
            print(f"  {n}")
    if stale:
        print("\nDISAGREE with their script:")
        for n in stale:
            print(f"  {n}")
        print("\nRegenerate and commit, after checking the difference is a real\n"
              "staleness and not a library-version change.")
    if failed:
        print("\nA script that would not run has not been checked. That is a gap,\n"
              "not a pass.")

    ok = not stale and not failed
    print("\n" + ("PASS — every figure checked matches its script"
                  if ok else "PROBLEM — see above"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
