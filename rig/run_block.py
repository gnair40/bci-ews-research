#!/usr/bin/env python3
"""
run_block.py — record ONE block, end to end, with one command.

WHY THIS EXISTS
---------------
The build manual said "run the stimulus in one window and the capture in
another". That works once, by hand. It does not work 265 times, which is what
the drift sweep needs, and every hand-run block is a chance to mistype a setting
or forget which fault was in place.

This starts the stimulus, starts the capture, waits for both, converts the
result into the .mat files the analysis already reads, and writes a record of
every setting used. One command, one block, nothing to remember.

WHAT IT PRODUCES
----------------
    data/raw_rig/RIG/day_<session>/block_<n>/   the three .mat files
    rig/blocklog.csv                            one row per block ever recorded

The block log is the thing that saves you later. It records the fault, the
severity, the drift setting, the modulation depth, the temperature and the
timestamp for every block, so a result can always be traced back to the
conditions that produced it. Recovering that from memory three weeks later is
not possible.

Usage:
    python3 rig/run_block.py --session 1 --blocknum 1
    python3 rig/run_block.py --session 2 --blocknum 7 --fault RATE_LOSS --severity 0.5
    python3 rig/run_block.py --session 3 --blocknum 1 --drift-tau 60 --frames 15000
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

RIG = Path(__file__).resolve().parent
REPO = RIG.parent
LOG = RIG / "blocklog.csv"

FIELDS = ["timestamp", "session", "blocknum", "fault", "severity", "frames",
          "fps", "depth", "brightness", "drift_tau", "drift_depth", "exposure",
          "gain", "lag_s", "temp_c", "humidity", "note", "outdir"]


def read_temp() -> tuple[str, str]:
    """Temperature and humidity, if the sensor is wired. Never fatal."""
    try:
        out = subprocess.run([sys.executable, str(RIG / "logtemp.py"), "--once"],
                             capture_output=True, text=True, timeout=15)
        t, h = out.stdout.strip().split(",")
        return t, h
    except Exception:
        return "", ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--blocknum", type=int, required=True)
    ap.add_argument("--frames", type=int, default=15000)
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="modulation depth; leave alone unless B-7 says otherwise")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--drift-tau", type=float, default=0.0,
                    help="seconds; 0 means no imposed drift")
    ap.add_argument("--drift-depth", type=float, default=0.0)
    ap.add_argument("--concentration", type=float, default=0.0)
    ap.add_argument("--exposure", type=int, default=8000)
    ap.add_argument("--gain", type=float, default=2.0)
    ap.add_argument("--lag", type=float, default=0.0,
                    help="seconds, from the B-5 timing measurement")
    ap.add_argument("--fault", default="NONE",
                    help="label only; the fault itself is imposed physically")
    ap.add_argument("--severity", type=float, default=0.0)
    ap.add_argument("--note", default="")
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would run and stop; no hardware needed")
    a = ap.parse_args()

    stim_csv = RIG / f"stim_s{a.session}_b{a.blocknum}.csv"
    cap_npy = RIG / f"cap_s{a.session}_b{a.blocknum}.npy"

    stim_cmd = [sys.executable, str(RIG / "stimulus.py"),
                "--frames", str(a.frames), "--fps", str(a.fps),
                "--depth", str(a.depth), "--brightness", str(a.brightness),
                "--concentration", str(a.concentration),
                "--drift-tau", str(a.drift_tau),
                "--drift-depth", str(a.drift_depth),
                "--out", str(stim_csv)]
    cap_cmd = [sys.executable, str(RIG / "capture.py"),
               "--frames", str(a.frames), "--fps", str(a.fps),
               "--exposure", str(a.exposure), "--gain", str(a.gain),
               "--out", str(cap_npy)]
    conv_cmd = [sys.executable, str(RIG / "to_mat.py"),
                "--block", str(cap_npy), "--stimlog", str(stim_csv),
                "--session", str(a.session), "--blocknum", str(a.blocknum),
                "--lag", str(a.lag), "--root", a.root]

    if a.dry_run:
        for label, c in (("stimulus", stim_cmd), ("capture", cap_cmd),
                         ("convert", conv_cmd)):
            print(f"{label:9} {' '.join(c)}")
        return 0

    # The stimulus is started first and given a moment to put the first frame on
    # the screen. Starting the camera first would record the desktop.
    print(f"--- session {a.session} block {a.blocknum} "
          f"({a.fault} sev {a.severity}) ---")
    stim = subprocess.Popen(stim_cmd)
    time.sleep(3.0)
    cap = subprocess.Popen(cap_cmd)

    cap_rc = cap.wait()
    stim.wait()
    if cap_rc != 0:
        print("capture failed; NOT converting and NOT logging this block")
        return 1

    if subprocess.run(conv_cmd).returncode != 0:
        print("conversion failed")
        return 1

    temp, hum = read_temp()
    outdir = f"{a.root}/RIG/day_{a.session}/block_{a.blocknum}"
    row = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "session": a.session,
           "blocknum": a.blocknum, "fault": a.fault, "severity": a.severity,
           "frames": a.frames, "fps": a.fps, "depth": a.depth,
           "brightness": a.brightness, "drift_tau": a.drift_tau,
           "drift_depth": a.drift_depth, "exposure": a.exposure, "gain": a.gain,
           "lag_s": a.lag, "temp_c": temp, "humidity": hum, "note": a.note,
           "outdir": outdir}
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"logged to {LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
