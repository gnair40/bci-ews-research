#!/usr/bin/env python3
"""
run_campaign.py — record a hundred sessions without sitting next to it.

=============================================================================
WHY THIS SCRIPT EXISTS
=============================================================================
Experiment P-2 needs **at least 101 healthy sessions**, about eight and a half
hours of recording. Nobody starts two hundred recordings by hand, and anyone
who tries will get one of them wrong without noticing.

This script does three separate jobs, and keeps them separate on purpose:

    plan      draw and lock the plans for a run of sessions, in advance
    record    record every session that has been drawn but not yet recorded
    status    show what has been drawn, what has been recorded, and what is left

Drawing and recording are separate commands because they happen at different
times and for different reasons. The draw fixes the answer before the data
exists; the recording happens afterwards, possibly overnight, possibly across
several days. Combining them would blur that line, and that line is the whole
argument for the phase.

=============================================================================
IT CAN BE STOPPED AND RESTARTED
=============================================================================
`record` skips any block that already has a recording. If the power goes out at
block 60, run the same command again in the morning and it carries on at 60. It
never re-records a block, because that would mean overwriting raw data.

=============================================================================
HOW TO RUN IT
=============================================================================
The healthy campaign (P-2), 101 sessions, unattended:

    python3 physical/code/run_campaign.py plan   --session 10 --healthy 101
    python3 physical/code/run_campaign.py record --session 10

The degraded campaign (P-3), 101 sessions, **partly attended**:

    python3 physical/code/run_campaign.py plan   --session 20 --degraded 101
    python3 physical/code/run_campaign.py status --session 20
    python3 physical/code/run_campaign.py record --session 20

Two of the four fault types are imposed by hand — a filter slid in front of the
lens, tape over part of the field. Those blocks need somebody in the room.
`status` lists which ones they are so you can plan the evening around them, and
`record --software-only` will record just the automatic ones if you want to
leave the by-hand ones for a session where you are present.

**`--software-only` changes which faults you end up with**, so if you use it,
finish the by-hand blocks later rather than dropping them. Reporting results
from only the automatic faults, without saying so, would be reporting a
benchmark that quietly excludes the harder half of itself.

=============================================================================
WHAT IT PRODUCES
=============================================================================
Nothing of its own. It calls `draw_onset.py` and `run_session.py`, which write
the plans and the recordings. This script only decides the order and keeps
going.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
RAW = DATA / "raw"
ONSETS = DATA / "onsets"

BY_HAND = ("RATE_LOSS", "CHANNEL_DROPOUT")


def plans_for(session: int) -> list[tuple[int, dict]]:
    """Every drawn plan for this session, in block order."""
    out = []
    for p in sorted(ONSETS.glob(f"s{session}_b*.json")):
        block = int(p.stem.split("_b")[1])
        out.append((block, json.loads(p.read_text())))
    return sorted(out)


def recorded(session: int, block: int) -> bool:
    f = RAW / f"s{session}_b{block}" / "capture.npy"
    return f.exists()


# --------------------------------------------------------------------- plan
def cmd_plan(a) -> int:
    n = a.healthy or a.degraded
    if not n:
        print("Say how many: --healthy N or --degraded N")
        return 1
    existing = [b for b, _ in plans_for(a.session)]
    start = (max(existing) + 1) if existing else 1
    if existing:
        print(f"session {a.session} already has blocks {min(existing)}–{max(existing)}; "
              f"continuing at {start}")

    made = 0
    for i in range(n):
        block = start + i
        cmd = [sys.executable, str(HERE / "draw_onset.py"),
               "--session", str(a.session), "--block", str(block),
               "--frames", str(a.frames), "--fps", str(a.fps)]
        if a.healthy:
            cmd.append("--healthy")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print(f"block {block}: draw refused —")
            print(r.stdout.strip())
            return 1
        made += 1

    kind = "healthy" if a.healthy else "degraded"
    print(f"drew {made} {kind} plans, blocks {start}–{start + made - 1}, "
          f"session {a.session}")
    print(f"each one is checksummed in {ONSETS / 'MANIFEST.csv'}")
    print()
    print(f"Now record them:  python3 physical/code/run_campaign.py record "
          f"--session {a.session}")
    return 0


# ------------------------------------------------------------------- status
def cmd_status(a) -> int:
    rows = plans_for(a.session)
    if not rows:
        print(f"No plans drawn for session {a.session}.")
        return 1
    done = sum(1 for b, _ in rows if recorded(a.session, b))
    hand = [b for b, p in rows
            if not p["healthy"] and p["fault_type"] in BY_HAND
            and not recorded(a.session, b)]

    print(f"session {a.session}: {len(rows)} planned, {done} recorded, "
          f"{len(rows) - done} left")
    print()
    print(f"{'block':>6}  {'state':<9}  {'what':<20}  {'severity':>8}  {'onset':>7}")
    for b, p in rows:
        state = "recorded" if recorded(a.session, b) else "waiting"
        what = "healthy" if p["healthy"] else p["fault_type"]
        sev = "" if p["healthy"] else f"{p['severity']:.2f}"
        ons = "" if p["healthy"] else f"{p['onset_seconds']:.0f}s"
        mark = "  <- by hand" if what in BY_HAND and state == "waiting" else ""
        print(f"{b:>6}  {state:<9}  {what:<20}  {sev:>8}  {ons:>7}{mark}")
    if hand:
        print()
        print(f"{len(hand)} of the remaining blocks "
              f"{'needs' if len(hand) == 1 else 'need'} somebody in the room: "
              f"{', '.join(map(str, hand))}")
        print("The stimulus program prints a countdown for those.")
    left = len(rows) - done
    if left:
        secs = left * a.frames / a.fps
        print()
        print(f"about {secs / 3600:.1f} hours of recording left" if secs >= 3600
              else f"about {secs / 60:.0f} minutes of recording left")
    return 0


# ------------------------------------------------------------------- record
def cmd_record(a) -> int:
    rows = plans_for(a.session)
    if not rows:
        print(f"No plans drawn for session {a.session}. Run `plan` first.")
        return 1

    todo = [(b, p) for b, p in rows if not recorded(a.session, b)]
    if a.software_only:
        skipped = [b for b, p in todo
                   if not p["healthy"] and p["fault_type"] in BY_HAND]
        todo = [(b, p) for b, p in todo
                if p["healthy"] or p["fault_type"] not in BY_HAND]
        if skipped:
            print(f"--software-only: leaving {len(skipped)} by-hand blocks for "
                  f"later ({', '.join(map(str, skipped))})")
            print("Record them before reporting anything, or the benchmark is")
            print("missing its physical faults.")
    if a.limit:
        todo = todo[:a.limit]
    if not todo:
        print("Nothing left to record.")
        return 0

    print(f"recording {len(todo)} blocks, about "
          f"{len(todo) * a.frames / a.fps / 3600:.1f} hours")
    failures = 0
    for i, (block, p) in enumerate(todo, 1):
        print(f"\n--- {i}/{len(todo)}: session {a.session} block {block} ---")
        cmd = [sys.executable, str(HERE / "run_session.py"),
               "--session", str(a.session), "--block", str(block)]
        rc = subprocess.run(cmd).returncode
        if rc:
            failures += 1
            print(f"block {block} failed (exit {rc}).")
            # Two failures in a row almost always means something about the
            # apparatus is wrong -- the camera gone, the screen asleep, the disk
            # full. Grinding through ninety-nine more failures would waste the
            # night and fill the log with unusable rows.
            if failures >= 2:
                print("\nTwo failures in a row. Stopping.")
                print("Check the camera, the screen and the free disk space, then")
                print("run the same command again — it carries on where it left off.")
                return 1
        else:
            failures = 0
        if a.pause and i < len(todo):
            time.sleep(a.pause)

    print(f"\ncampaign finished: {len(todo)} blocks recorded")
    print(f"next:  python3 physical/code/make_session_table.py")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = dict(frames=15000, fps=50)
    p = sub.add_parser("plan", help="draw and lock plans in advance")
    p.add_argument("--session", type=int, required=True)
    p.add_argument("--healthy", type=int, default=0)
    p.add_argument("--degraded", type=int, default=0)
    p.add_argument("--frames", type=int, default=common["frames"])
    p.add_argument("--fps", type=int, default=common["fps"])
    p.set_defaults(fn=cmd_plan)

    s = sub.add_parser("status", help="what is drawn, recorded and left")
    s.add_argument("--session", type=int, required=True)
    s.add_argument("--frames", type=int, default=common["frames"])
    s.add_argument("--fps", type=int, default=common["fps"])
    s.set_defaults(fn=cmd_status)

    r = sub.add_parser("record", help="record everything not yet recorded")
    r.add_argument("--session", type=int, required=True)
    r.add_argument("--limit", type=int, default=0, help="stop after this many")
    r.add_argument("--pause", type=float, default=5.0,
                   help="seconds between blocks, to let the camera cool")
    r.add_argument("--software-only", action="store_true",
                   help="skip faults that must be imposed by hand")
    r.add_argument("--frames", type=int, default=common["frames"])
    r.add_argument("--fps", type=int, default=common["fps"])
    r.set_defaults(fn=cmd_record)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
