#!/usr/bin/env python3
"""
check_all.py
============
Run every gate in this repository, in order, and print one summary.

WHY THIS EXISTS
---------------
The gates were listed in the README as nine commands to run by hand. That list
has already failed once in exactly the way such lists do: `69_command_check.py`
was missing from it for several days, which is how a gate quietly stops being a
gate. A list of commands in prose is documentation; a script is a thing that
either runs or does not.

It also matters for working alone. Nine commands is nine chances to skip the
one that would have caught something, on the evening when you are tired and the
box has been recording all night.

WHAT IT DOES NOT DO
-------------------
It does not fix anything, and it does not decide what a failure means. Each
gate prints its own explanation; this only makes sure each one is reached and
that a failure cannot scroll past unnoticed. A gate that fails here is read in
full, not re-run until it passes.

It deliberately keeps going after a failure rather than stopping at the first.
Stopping early hides how much is wrong, and the second failure is often the one
that explains the first.

Usage:
  python3 tools/check_all.py            # everything
  python3 tools/check_all.py --quick    # skip the slow ones (mutation check)
  python3 tools/check_all.py --list     # show what would run, run nothing
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (label, argv, slow?, what a failure means)
GATES: list[tuple[str, list[str], bool, str]] = [
    ("unit tests",
     ["-m", "unittest", "discover", "-s", "tests"], False,
     "Code behaves differently from what a test derived from a real past "
     "mistake expects. Read which test, not just how many."),
    ("mutation check",
     ["tools/mutation_check.py"], True,
     "The tests pass, but they would also pass with a bug this project "
     "actually had reintroduced. The tests are weaker than they look."),
    ("claims verified",
     ["scripts/31_verify_claims.py"], False,
     "A headline number in a document no longer matches what recomputing it "
     "from the data gives."),
    ("reproducibility audit",
     ["scripts/55_reproducibility_audit.py"], False,
     "Something in the pipeline cannot be reproduced from what is committed."),
    ("claims register",
     ["scripts/56_claims_register.py"], False,
     "A claim is made somewhere without a registered source."),
    ("statistical hygiene",
     ["scripts/61_statistical_hygiene.py"], False,
     "A statistical practice this project committed to avoiding has "
     "reappeared."),
    ("log coverage",
     ["scripts/65_log_coverage.py"], False,
     "Work happened that the research log does not record. The log is the "
     "part that cannot be reconstructed afterwards."),
    ("command check",
     ["scripts/69_command_check.py"], False,
     "A command written in a document would not work if a reader ran it."),
    ("cross-reference",
     ["scripts/77_cross_reference.py"], False,
     "Two documents disagree about the same number, or a corrected figure is "
     "quoted without its correction."),
    ("preregistration freeze",
     ["scripts/79_preregistration_freeze.py"], False,
     "The frozen preregistration has drifted since its timestamp, or an edit "
     "to it was not disclosed. This is the most serious failure in the list: "
     "a preregistration that has drifted still looks like evidence of "
     "foresight."),
    ("physical pipeline selftest",
     ["physical/code/monitor.py", "--selftest"], False,
     "The physical phase's analysis chain does not work end to end on "
     "synthetic data. Nothing recorded would be analysable."),
]


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="skip the slow gates (the mutation check)")
    ap.add_argument("--list", action="store_true",
                    help="print what would run, and run nothing")
    a = ap.parse_args()

    gates = [g for g in GATES if not (a.quick and g[2])]

    if a.list:
        for label, argv, slow, _ in GATES:
            mark = "  (slow)" if slow else ""
            skipped = "  [skipped by --quick]" if a.quick and slow else ""
            print(f"  {label:<30} python3 {' '.join(argv)}{mark}{skipped}")
        return 0

    print("=" * 72)
    print(f"running {len(gates)} gates"
          + (" (--quick: slow gates skipped)" if a.quick else ""))
    print("=" * 72)

    failures: list[tuple[str, int, str]] = []
    started = time.monotonic()

    for label, argv, _, meaning in gates:
        print(f"\n{'-' * 72}\n>>> {label}\n{'-' * 72}")
        t0 = time.monotonic()
        r = subprocess.run([sys.executable, *argv], cwd=REPO)
        dt = time.monotonic() - t0
        if r.returncode == 0:
            print(f"<<< {label}: PASS ({dt:.1f}s)")
        else:
            print(f"<<< {label}: FAIL (exit {r.returncode}, {dt:.1f}s)")
            failures.append((label, r.returncode, meaning))

    total = time.monotonic() - started
    print("\n" + "=" * 72)
    print(f"{len(gates) - len(failures)} of {len(gates)} gates passed "
          f"in {total:.0f}s")
    print("=" * 72)

    if not failures:
        print("\nPASS — every gate is green.")
        if a.quick:
            print("\nNote: --quick skipped the mutation check. Run the full")
            print("set before committing, not just before looking.")
        return 0

    print(f"\n{len(failures)} gate(s) failed:\n")
    for label, code, meaning in failures:
        print(f"  {label}  (exit {code})")
        print(f"      {meaning}\n")
    print("Scroll up and read the failing gate's own output in full. Each one")
    print("explains what it checked and why. Do not re-run until it passes —")
    print("find out what changed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
