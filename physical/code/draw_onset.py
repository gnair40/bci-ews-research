#!/usr/bin/env python3
"""
draw_onset.py — decide when the degradation starts, BEFORE the session runs.

=============================================================================
WHAT THIS SCRIPT IS FOR
=============================================================================
This is the most important script in the physical phase, and the reason the
whole phase can make a claim nobody else can.

In a real brain-implant recording, nobody wrote down when the electrodes started
going bad. So when somebody later asks "how early did the monitor warn?", the
answer depends on which moment the analyst decides to call the start. A
different analyst picks a different moment and gets a different answer. The
false-alarm rate is worse: you cannot count wrong alarms without knowing which
alarms were wrong.

This script removes that problem by deciding the answer first:

  1. It picks the onset time, the fault type and the severity at random.
  2. It writes them to a file.
  3. It computes a checksum of that file and records it.

Because the checksum is written before the recording exists, nobody -- including
the person running the experiment -- can quietly adjust the onset afterwards to
make a result look better. Somebody who does not trust the experimenter can
check the file still matches its checksum.

=============================================================================
WHAT YOU NEED TO KNOW BEFORE RUNNING IT
=============================================================================
Nothing about Python. You type one line into a terminal and it writes a file.

A "terminal" is a window where you type commands instead of clicking. On a
Raspberry Pi you open it from the menu, or connect from another computer.

=============================================================================
HOW TO RUN IT
=============================================================================
Before EVERY degraded session, run:

    python3 physical/code/draw_onset.py --session 3 --block 7

That is it. It prints what it drew and tells you what to do.

To draw a healthy session instead (no degradation at all), add --healthy:

    python3 physical/code/draw_onset.py --session 3 --block 7 --healthy

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/onsets/s<session>_b<block>.json    the drawn plan
    physical/data/onsets/MANIFEST.csv                one line per draw, with
                                                     the checksum

The JSON file is read later by the analysis scripts. The manifest is the audit
trail: it is append-only, and every line records when the draw happened.

=============================================================================
WHERE IT FITS IN THE WORKFLOW
=============================================================================
    draw_onset.py   -> run_session.py  -> analyze_leadtime.py
    (decide first)     (record)           (measure against what was decided)

If you record a session without drawing an onset first, that session CANNOT be
used for lead-time analysis. It can still be used as a healthy session only if
it was genuinely untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
ONSETS = DATA / "onsets"
MANIFEST = ONSETS / "MANIFEST.csv"

# The four kinds of degradation, matching the computational half exactly so
# results can be compared. Plain-language names are given because the reader is
# not assumed to know the project's jargon.
FAULT_TYPES = {
    "RATE_LOSS": "overall signal loss — everything dims together, "
                 "like a filter over the lens",
    "CHANNEL_DROPOUT": "some channels stop responding, "
                       "like tape over part of the field of view",
    "GAIN_DRIFT": "channels drift by different amounts, "
                  "like uneven brightness across the screen",
    "GEOMETRY_ROTATION": "the whole field rotates, "
                         "like the camera being turned",
}
SEVERITIES = [0.25, 0.5, 1.0]

# The onset is drawn from the middle of the session, never the first or last
# fifth. Too early and there is no healthy baseline to compare against; too late
# and the fault has no time to develop before the recording ends.
ONSET_LOW_FRACTION = 0.20
ONSET_HIGH_FRACTION = 0.80


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", type=int, required=True,
                    help="which recording day this belongs to")
    ap.add_argument("--block", type=int, required=True,
                    help="which block within that day")
    ap.add_argument("--healthy", action="store_true",
                    help="draw a HEALTHY session: no degradation at all")
    ap.add_argument("--frames", type=int, default=15000,
                    help="session length in frames (15000 = 5 minutes at 50 fps)")
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=None,
                    help="only for testing; leave unset for a real draw")
    a = ap.parse_args()

    ONSETS.mkdir(parents=True, exist_ok=True)
    out = ONSETS / f"s{a.session}_b{a.block}.json"

    # Refusing to overwrite is the point. If a plan already exists for this
    # session and block, re-drawing it would be exactly the tampering the
    # checksum exists to prevent.
    if out.exists():
        print(f"REFUSING: {out} already exists.")
        print("A plan has already been drawn for this session and block.")
        print("Re-drawing it would defeat the purpose of locking it. If this is")
        print("genuinely a new session, use a different --block number.")
        return 1

    import random
    rng = random.Random(a.seed)

    if a.healthy:
        plan = {"session": a.session, "block": a.block, "healthy": True,
                "fault_type": None, "fault_type_plain": None, "severity": 0.0,
                "onset_frame": None, "onset_seconds": None,
                "frames": a.frames, "fps": a.fps}
    else:
        ftype = rng.choice(sorted(FAULT_TYPES))
        sev = rng.choice(SEVERITIES)
        lo = int(a.frames * ONSET_LOW_FRACTION)
        hi = int(a.frames * ONSET_HIGH_FRACTION)
        onset = rng.randint(lo, hi)
        plan = {"session": a.session, "block": a.block, "healthy": False,
                "fault_type": ftype, "fault_type_plain": FAULT_TYPES[ftype],
                "severity": sev,
                "onset_frame": onset, "onset_seconds": round(onset / a.fps, 2),
                "frames": a.frames, "fps": a.fps}

    plan["drawn_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out.write_text(json.dumps(plan, indent=2))
    digest = sha256_of(out)

    new = not MANIFEST.exists()
    with MANIFEST.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["drawn_at", "session", "block", "healthy", "fault_type",
                        "severity", "onset_seconds", "file", "sha256"])
        w.writerow([plan["drawn_at"], a.session, a.block, plan["healthy"],
                    plan["fault_type"] or "", plan["severity"],
                    plan["onset_seconds"] if plan["onset_seconds"] is not None else "",
                    out.name, digest])

    # ------------------------------------------------------------ what to do
    print("=" * 70)
    if plan["healthy"]:
        print(f"HEALTHY session {a.session}, block {a.block}")
        print()
        print("Record this session and CHANGE NOTHING. Do not touch the box, the")
        print("camera, the screen or the lens. This session is what false alarms")
        print("are counted against, so any interference makes it unusable.")
    else:
        print(f"DEGRADED session {a.session}, block {a.block}")
        print()
        print(f"  Fault type : {plan['fault_type']}")
        print(f"               {plan['fault_type_plain']}")
        print(f"  Severity   : {plan['severity']}")
        print(f"  Starts at  : {plan['onset_seconds']:.1f} seconds "
              f"({plan['onset_frame']} frames) into the session")
        print()
        if plan["fault_type"] in ("RATE_LOSS", "CHANNEL_DROPOUT"):
            print("  This one is imposed BY HAND. Start a timer when the recording")
            print(f"  begins and apply the fault at {plan['onset_seconds']:.0f} seconds:")
            if plan["fault_type"] == "RATE_LOSS":
                print("    -> slide the neutral-density filter in front of the lens")
            else:
                print("    -> place tape over the fraction of the field given by")
                print(f"       the severity ({plan['severity']:.0%} of it)")
        else:
            print("  This one is imposed automatically by the software. You do")
            print("  not need to do anything during the recording.")
    print()
    print(f"  Plan written to : {out}")
    print(f"  Checksum        : {digest[:16]}...")
    print()
    print("  This plan is now LOCKED. It was written before the recording")
    print("  exists, so the onset cannot be adjusted afterwards to flatter a")
    print("  result. That is what makes the lead-time measurement trustworthy.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
