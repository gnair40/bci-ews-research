#!/usr/bin/env python3
"""
note_onset.py — record when a fault you caused by hand actually started.

=============================================================================
WHAT THIS IS FOR, AND WHY IT IS NOT draw_onset.py
=============================================================================
Experiment P-5 imposes faults **nobody designed**: half-unseating the camera
ribbon, a fingerprint on the lens, warming the board with a hair dryer. There is
no equation for what those look like, which is the whole point of doing them.

They cannot be drawn in advance, because the time they start is the time your
hand moves. So the onset is recorded **afterwards**, from a stopwatch.

**That is weaker evidence than a drawn onset, and this script says so
everywhere it can.** A drawn onset was fixed before the recording existed and is
checksummed; a noted onset is your word. The analysis keeps the two apart and
reports P-5 in its own table for exactly that reason. Mixing them silently would
hand the whole phase's main argument back.

What P-5 keeps is the thing that matters most: **you did not design what the
fault would look like.** You only know when it started.

=============================================================================
BEFORE YOU RUN IT
=============================================================================
Record the session with `--undesigned`, which tells `run_session.py` not to
demand a drawn plan:

    python3 physical/code/run_session.py --session 30 --block 1 \
        --undesigned "half-unseated the camera ribbon and re-seated it"

It prints the exact clock time the recording started. **Write down the clock
time you caused the fault**, to the nearest second, while it is happening. Do
not reconstruct it afterwards from memory.

=============================================================================
HOW TO RUN IT
=============================================================================
Either say how far into the recording it happened:

    python3 physical/code/note_onset.py --session 30 --block 1 --at-seconds 143

or give the clock time you wrote down:

    python3 physical/code/note_onset.py --session 30 --block 1 --at-clock 21:47:12

The second form is usually easier, because a clock is what you were looking at.

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/raw/s30_b1/observed_onset.json

The analysis reads it in the same place it would read a drawn plan, but it
carries `onset_provenance: "stopwatch"`, and every report built from it says so.

It **refuses to overwrite** an existing note. If the first one was wrong, that
is worth a line in the research log rather than a silent correction: use
`--replace` and say in the log what was wrong and why.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
RAW = DATA / "raw"
FPS = 50


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--block", type=int, required=True)
    ap.add_argument("--at-seconds", type=float, default=None,
                    help="how many seconds into the recording the fault started")
    ap.add_argument("--at-clock", default=None,
                    help="the clock time you caused it, as HH:MM:SS")
    ap.add_argument("--fault", default="UNDESIGNED",
                    help="a short label, e.g. CONNECTOR, THERMAL, CONTAMINATION")
    ap.add_argument("--what", default="",
                    help="what you actually did, in your own words")
    ap.add_argument("--replace", action="store_true",
                    help="overwrite an existing note; say why in the research log")
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()

    root = Path(a.raw) if a.raw else RAW
    folder = root / f"s{a.session}_b{a.block}"
    if not (folder / "capture.npy").exists():
        print(f"No recording at {folder}.")
        print("Record the session first:")
        print(f"    python3 physical/code/run_session.py --session {a.session} "
              f"--block {a.block} --undesigned \"what you did\"")
        return 1

    out = folder / "observed_onset.json"
    if out.exists() and not a.replace:
        print(f"REFUSING: {out} already exists.")
        print(json.dumps(json.loads(out.read_text()), indent=2))
        print()
        print("An onset has already been noted for this session. If it is wrong,")
        print("pass --replace AND write in the research log what was wrong and")
        print("why — a silently corrected onset is indistinguishable from an")
        print("onset adjusted to improve a result.")
        return 1

    if (a.at_seconds is None) == (a.at_clock is None):
        print("Give exactly one of --at-seconds or --at-clock.")
        return 1

    t = np.load(folder / "capture_t.npy")
    started, ended = float(t[0]), float(t[-1])

    if a.at_seconds is not None:
        onset_s = float(a.at_seconds)
    else:
        # The clock time you wrote down, resolved against the day the recording
        # happened. Recordings do not span midnight, so the date is unambiguous.
        day = time.strftime("%Y-%m-%d", time.localtime(started))
        try:
            when = time.mktime(time.strptime(f"{day} {a.at_clock}",
                                             "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            print(f"Could not read {a.at_clock!r} as a clock time. "
                  f"Use HH:MM:SS, e.g. 21:47:12.")
            return 1
        onset_s = when - started

    duration = ended - started
    if not (0 < onset_s < duration):
        print(f"That onset is {onset_s:.1f} s into a recording that lasted "
              f"{duration:.1f} s, so it falls outside it.")
        print("The recording started at "
              f"{time.strftime('%H:%M:%S', time.localtime(started))} and ended at "
              f"{time.strftime('%H:%M:%S', time.localtime(ended))}.")
        print("Nothing was written. Check the time you noted.")
        return 1

    note = {
        "session": a.session, "block": a.block,
        "healthy": False,
        "fault_type": a.fault,
        "fault_type_plain": a.what or "imposed by hand; not designed in advance",
        "severity": float("nan"),
        "onset_seconds": round(onset_s, 2),
        "onset_frame": int(round(onset_s * FPS)),
        "frames": int(len(t)), "fps": FPS,
        "onset_provenance": "stopwatch",
        "noted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "recording_started": time.strftime("%H:%M:%S", time.localtime(started)),
        "replaced_an_earlier_note": bool(a.replace and out.exists()),
        "caveat": "Noted after the recording, from a stopwatch, not drawn and "
                  "checksummed beforehand. Analysed in a separate table from "
                  "the drawn-onset sessions.",
    }
    out.write_text(json.dumps(note, indent=2))

    print("=" * 70)
    print(f"session {a.session} block {a.block}: onset noted at "
          f"{onset_s:.1f} s ({onset_s / duration:.0%} of the way in)")
    print(f"  what you did : {note['fault_type_plain']}")
    print(f"  label        : {a.fault}")
    print(f"  written to   : {out}")
    print()
    print("  This onset came from a stopwatch, not from a checksummed draw.")
    print("  It is analysed in its own table and reported separately, because")
    print("  the provenance is weaker. What it keeps is the part that matters:")
    print("  you did not design what this fault would look like.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
