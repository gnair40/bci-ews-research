#!/usr/bin/env python3
"""
run_session.py — record one complete session with a single command.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
A session needs two programs running at the same time: one drawing the moving
pattern on the screen (`stimulus.py`), and one recording what the camera sees
(`capture.py`). Started by hand, that means two terminal windows, two sets of
settings typed correctly, and a folder created with the right name.

Done once, that is fine. This phase records **over two hundred sessions**, and
every hand-run session is a chance to mistype a setting, forget which
degradation was in place, or overwrite yesterday's recording. This script does
all of it from one line and writes down everything it did.

=============================================================================
WHY IT INSISTS ON A DRAWN PLAN
=============================================================================
Unless you pass `--calibration`, this script refuses to record until a plan
exists for this session and block — that is, until `draw_onset.py` has decided,
in advance and under a checksum, whether this session is healthy and, if not,
when the degradation starts.

That refusal is deliberate. The entire claim of this phase is that the onset was
fixed before the recording existed. A session recorded without a plan cannot
support that claim afterwards, no matter how carefully it was run, and a
recording you cannot use is worse than one you never made because it looks
usable.

`--calibration` exists for the P-1 difficulty check, which is about tuning the
apparatus and is not part of any lead-time or false-alarm number. Sessions
recorded that way are marked `calibration` in the log and the analysis scripts
skip them.

`--undesigned` exists for experiment P-5, where the fault is something you cause
by hand and nobody wrote an equation for — a half-unseated ribbon cable, a
fingerprint on the lens, a warm afternoon imposed with a hair dryer. Those
cannot be drawn in advance because the onset is the moment your hand moves. You
record the session, then write the onset down with `note_onset.py`, and the
analysis keeps those sessions in a separate table because a stopwatch is weaker
evidence than a checksum.

=============================================================================
HOW TO RUN IT
=============================================================================
Step 1, decide the session in advance:

    python3 physical/code/draw_onset.py --session 3 --block 7

Step 2, record it:

    python3 physical/code/run_session.py --session 3 --block 7

That is all. If the drawn fault is one you impose by hand, the stimulus program
prints a countdown telling you when to act.

For the P-1 calibration sessions, which have no plan:

    python3 physical/code/run_session.py --session 0 --block 1 --calibration

For a P-5 undesigned fault:

    python3 physical/code/run_session.py --session 30 --block 1 --undesigned "fingerprint on the lens edge"
    python3 physical/code/note_onset.py   --session 30 --block 1 --at-clock 21:47:12

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/raw/s<session>_b<block>/
        capture.npy         the channel recording
        capture_t.npy       one clock time per camera frame
        capture_meta.json   camera settings and timing statistics
        stim.csv            the true direction on every screen frame
        session.json        everything about how this session was recorded

    physical/data/raw/SESSION_LOG.csv   one row per session ever recorded

**The raw folder is never edited.** Analysis reads it and writes elsewhere.
The session log is the record that lets a result three weeks from now be traced
back to the exact conditions that produced it, which is not something anybody
reconstructs from memory.

=============================================================================
WHERE IT FITS
=============================================================================
    draw_onset.py -> run_session.py -> make_session_table.py -> analyze_*.py
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = HERE.parent / "data"
RAW = DATA / "raw"
ONSETS = DATA / "onsets"
LOG = RAW / "SESSION_LOG.csv"

FIELDS = ["recorded_at", "session", "block", "config", "kind",
          "undesigned_what", "healthy", "fault_type",
          "severity", "onset_seconds", "frames", "fps", "depth", "base",
          "exposure", "gain", "width", "height", "cols", "rows",
          "frames_recorded", "fps_measured", "long_gap_fraction",
          "temp_c", "note", "folder"]


def read_temp() -> str:
    """Room temperature, if a sensor is wired up. Never fatal if it is not.

    Temperature is logged because the camera's dark current rises with it, which
    drifts every channel upward over an evening. That is a real effect on the
    apparatus and, if it is not recorded, it is indistinguishable afterwards
    from the drift the experiment is trying to measure.
    """
    script = REPO / "rig" / "logtemp.py"
    if not script.exists():
        return ""
    try:
        out = subprocess.run([sys.executable, str(script), "--once"],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip().split(",")[0]
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--block", type=int, required=True)
    ap.add_argument("--calibration", action="store_true",
                    help="P-1 only: record without a drawn plan, and mark the "
                         "session as unusable for lead time or false alarms")
    ap.add_argument("--undesigned", default=None, metavar="WHAT",
                    help="P-5 only: record without a drawn plan because the "
                         "fault is one you cause by hand and nobody designed. "
                         "Say what you are about to do, in your own words. "
                         "Note the onset afterwards with note_onset.py")
    ap.add_argument("--frames", type=int, default=15000)
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="modulation depth; set by P-1 and then left alone")
    ap.add_argument("--base", type=float, default=0.5)
    ap.add_argument("--cols", type=int, default=24)
    ap.add_argument("--rows", type=int, default=16)
    ap.add_argument("--patch", type=int, default=40)
    ap.add_argument("--width", type=int, default=48)
    ap.add_argument("--height", type=int, default=32)
    ap.add_argument("--exposure", type=int, default=8000)
    ap.add_argument("--gain", type=float, default=2.0)
    ap.add_argument("--config", default="A",
                    help="which apparatus configuration this session used "
                         "(experiment P-7). 'A' is the calibrated baseline; "
                         "B, C, D vary exposure, patch size and channel count. "
                         "Recorded so the analysis can group by it")
    ap.add_argument("--note", default="", help="anything unusual about this run")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the two commands and stop, without recording")
    a = ap.parse_args()

    plan_file = ONSETS / f"s{a.session}_b{a.block}.json"
    plan = None
    if plan_file.exists():
        plan = json.loads(plan_file.read_text())
        if a.undesigned:
            print(f"REFUSING: a plan already exists at {plan_file}.")
            print("A session cannot be both a drawn-onset session and an")
            print("undesigned-fault session. Use a different --block number.")
            return 1
    elif not (a.calibration or a.undesigned):
        print(f"REFUSING: there is no plan at {plan_file}.")
        print()
        print("Draw the session first, so its onset is fixed before the")
        print("recording exists:")
        print(f"    python3 physical/code/draw_onset.py --session {a.session} "
              f"--block {a.block}")
        print(f"    python3 physical/code/draw_onset.py --session {a.session} "
              f"--block {a.block} --healthy")
        print()
        print("A session recorded without a plan cannot be used for lead time or")
        print("false alarms, because nothing fixed the onset in advance. If this")
        print("is a P-1 calibration session, pass --calibration.")
        return 1

    folder = RAW / f"s{a.session}_b{a.block}"
    if folder.exists() and any(folder.iterdir()):
        print(f"REFUSING: {folder} already has a recording in it.")
        print("Recording again would overwrite it. Raw data is never overwritten.")
        print("Use a different --block number.")
        return 1
    folder.mkdir(parents=True, exist_ok=True)

    if plan:
        a.frames = plan.get("frames", a.frames)
        a.fps = plan.get("fps", a.fps)

    stim_cmd = [sys.executable, str(HERE / "stimulus.py"),
                "--cols", str(a.cols), "--rows", str(a.rows),
                "--patch", str(a.patch), "--fps", str(a.fps),
                "--frames", str(a.frames), "--depth", str(a.depth),
                "--base", str(a.base), "--out", str(folder / "stim.csv")]
    if plan:
        stim_cmd += ["--plan", str(plan_file)]

    cap_cmd = [sys.executable, str(HERE / "capture.py"),
               "--cols", str(a.cols), "--rows", str(a.rows),
               "--width", str(a.width), "--height", str(a.height),
               "--fps", str(a.fps), "--frames", str(a.frames),
               "--exposure", str(a.exposure), "--gain", str(a.gain),
               "--out", str(folder / "capture.npy")]

    if a.dry_run:
        print("stimulus:\n  " + " ".join(stim_cmd))
        print("capture:\n  " + " ".join(cap_cmd))
        print("\nnothing was recorded (--dry-run)")
        return 0

    print("=" * 70)
    print(f"session {a.session} block {a.block}  ->  {folder}")
    if plan and not plan["healthy"]:
        print(f"  {plan['fault_type']} severity {plan['severity']} "
              f"at {plan['onset_seconds']:.0f} s")
    elif plan:
        print("  HEALTHY — touch nothing during this recording")
    elif a.undesigned:
        print(f"  UNDESIGNED FAULT — {a.undesigned}")
        print("  Watch the clock. Write down the time you act, to the second.")
    else:
        print("  CALIBRATION — not usable for lead time or false alarms")
    print(f"  {a.frames} frames at {a.fps} fps = {a.frames / a.fps / 60:.1f} minutes")
    print("=" * 70)

    temp_before = read_temp()
    t0 = time.time()

    # The stimulus starts first and is given a moment to open its window. If the
    # camera started first it would record a blank screen for the first second,
    # and those frames would enter the analysis as if they were data.
    stim = subprocess.Popen(stim_cmd)
    time.sleep(2.0)
    cap = subprocess.Popen(cap_cmd)

    cap_rc = cap.wait()
    stim_rc = stim.wait()

    meta_file = folder / "capture_meta.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}

    record = {
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session": a.session, "block": a.block,
        "config": a.config,
        "kind": ("undesigned" if a.undesigned else
                 "calibration" if a.calibration and not plan else "experiment"),
        "undesigned_what": a.undesigned or "",
        "healthy": plan["healthy"] if plan else None,
        "fault_type": (plan or {}).get("fault_type") or "",
        "severity": (plan or {}).get("severity", ""),
        "onset_seconds": (plan or {}).get("onset_seconds", ""),
        "frames": a.frames, "fps": a.fps, "depth": a.depth, "base": a.base,
        "exposure": a.exposure, "gain": a.gain,
        "width": a.width, "height": a.height, "cols": a.cols, "rows": a.rows,
        "frames_recorded": meta.get("frames_recorded", ""),
        "fps_measured": round(meta["fps_measured"], 2) if meta.get("fps_measured") else "",
        "long_gap_fraction": meta.get("long_gap_fraction", ""),
        "temp_c": temp_before, "note": a.note, "folder": str(folder.relative_to(REPO)),
        "plan_file": plan_file.name if plan else None,
        "stimulus_exit": stim_rc, "capture_exit": cap_rc,
        "wall_seconds": round(time.time() - t0, 1),
        "stimulus_command": stim_cmd, "capture_command": cap_cmd,
    }
    (folder / "session.json").write_text(json.dumps(record, indent=2))

    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(record)

    if stim_rc or cap_rc:
        print()
        print(f"One of the two programs exited with an error "
              f"(stimulus {stim_rc}, capture {cap_rc}).")
        print("The folder has been kept so you can see what it managed to write,")
        print("but treat this session as failed and record it again under a new")
        print("block number rather than analysing a partial recording.")
        return 1

    print(f"\ndone in {record['wall_seconds']:.0f} s — wrote {folder}")
    print(f"logged to {LOG}")
    if a.undesigned:
        print()
        print("This was an undesigned fault, so nothing knows when it started")
        print("except you. Record that now, while you still remember:")
        print(f"    python3 physical/code/note_onset.py --session {a.session} "
              f"--block {a.block} --at-clock HH:MM:SS")
        print("Until you do, this session cannot be analysed at all.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
