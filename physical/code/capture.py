#!/usr/bin/env python3
"""
capture.py — record what the camera sees, as channels rather than pictures.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
It runs the camera for a fixed number of frames. For each frame it throws the
picture away and keeps a small table of numbers instead: the average brightness
of each little square region of the image.

Each of those regions is one **channel**. A channel here plays the same role a
single electrode plays in a brain implant: it reports one number, many times a
second, and that number goes up and down with what the subject is doing.

So a five-minute recording is not 15,000 photographs. It is a table with 15,000
rows (one per frame) and 384 columns (one per channel). That is exactly the
shape the neural recordings come in, which is why the same analysis code can
read both.

=============================================================================
THE THREE SETTINGS THAT ARE NOT NEGOTIABLE, AND WHY
=============================================================================

**1. Automatic exposure and automatic white balance must be OFF.**

A modern camera constantly adjusts itself to keep the picture looking good. If
the scene gets dimmer, it opens up and brightens it back. That is exactly the
wrong behaviour here: the experiment deliberately dims the scene to simulate a
failing implant, and an automatic camera would quietly cancel that out. The
recording would then show a healthy system when the system was in fact being
degraded — and nothing in the data would reveal that it had happened.

The script therefore fixes exposure time, analogue gain, and white balance, and
records the values it used.

**2. Pixels-per-channel is a calibration setting, not a convenience.**

Averaging N pixels into one channel divides that channel's random noise by the
square root of N. Average 400 pixels and the channel is twenty times quieter
than a single pixel — which sounds good and is in fact a problem. A system that
clean decodes direction perfectly, and a system that decodes perfectly has
nothing left to detect when you degrade it.

An earlier version of this apparatus captured 480x320 and averaged 20x20 = 400
pixels per channel. A simulation (`scripts/72_rig_digital_twin.py`) showed that
this was half the reason it decoded with **0.0 degrees of error** where the real
neural decoder sits at 54.6 degrees. The defaults below capture 48x32, so each
channel is a 2x2 = 4-pixel block.

**Raising the capture size back up will silently make the apparatus too good
again.** If you change it, re-run the difficulty check (`bench.py margin`).

**3. The green channel only.**

Colour camera sensors have twice as many green pixels as red or blue, so green
is the least interpolated and the least noisy. The screen shows grey, so no
colour information is being discarded.

=============================================================================
WHAT YOU NEED BEFORE RUNNING IT
=============================================================================
- A Raspberry Pi with a camera attached and `picamera2` installed.
- The box closed. Run `bench.py darkframe` first to confirm it is light-tight.

This script only runs on the Pi, because only the Pi has the camera. Everything
downstream — the bench checks, the analysis — runs anywhere.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/capture.py --frames 15000 --out physical/data/raw/cap.npy

Normally you do not run this by hand. `run_session.py` starts the stimulus and
this script together and puts the outputs in the right place.

=============================================================================
WHAT IT PRODUCES
=============================================================================
    <out>            a table of numbers, frames x channels  (.npy)
    <out>_t.npy      the clock time of each frame
    <out>_meta.json  every setting used, plus timing statistics

The timing statistics matter. If the camera could not keep up and dropped
frames, that shows here, and a recording with heavy frame loss should be
discarded rather than analysed — a dropped frame is a moment where the camera
and the screen disagree about what was being shown.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cols", type=int, default=24,
                    help="channel grid across; 24 x 16 = 384 channels")
    ap.add_argument("--rows", type=int, default=16)
    ap.add_argument("--width", type=int, default=48,
                    help="captured pixels across; 48/24 = 2 px per channel side")
    ap.add_argument("--height", type=int, default=32)
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--frames", type=int, default=15000,
                    help="15000 frames at 50 fps = 5 minutes")
    ap.add_argument("--exposure", type=int, default=8000,
                    help="microseconds, FIXED; automatic exposure is disabled")
    ap.add_argument("--gain", type=float, default=2.0,
                    help="analogue gain, FIXED")
    ap.add_argument("--settle", type=float, default=2.0,
                    help="seconds to let the sensor stabilise before recording")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.width % a.cols or a.height % a.rows:
        print(f"The captured frame ({a.width}x{a.height}) does not divide evenly "
              f"into the channel grid ({a.cols}x{a.rows}).")
        print("Each channel must be a whole block of pixels, so width must be a")
        print("multiple of cols and height a multiple of rows.")
        return 1

    try:
        from picamera2 import Picamera2
    except ImportError:
        print("picamera2 is not installed, so there is no camera to record from.")
        print()
        print("This script only runs on the Raspberry Pi. On the Pi, install it with:")
        print("    sudo apt install -y python3-picamera2")
        print()
        print("If you are on a laptop, you are on the wrong machine — the bench")
        print("checks and every analysis script run here, but capture does not.")
        return 1

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    cam = Picamera2()
    cam.configure(cam.create_video_configuration(
        main={"size": (a.width, a.height), "format": "RGB888"},
        controls={"FrameRate": a.fps}))
    # Every automatic compensator off. See the docstring: leaving these on lets
    # the camera undo the degradation this experiment exists to measure.
    cam.set_controls({"AeEnable": False, "AwbEnable": False,
                      "ExposureTime": a.exposure, "AnalogueGain": a.gain})
    cam.start()
    time.sleep(a.settle)

    py, px = a.height // a.rows, a.width // a.cols
    frames = np.empty((a.frames, a.rows * a.cols), dtype=np.float32)
    stamps = np.empty(a.frames, dtype=np.float64)
    n = 0
    t0 = time.time()
    try:
        for i in range(a.frames):
            img = cam.capture_array("main")[:, :, 1].astype(np.float32)  # green
            frames[i] = img.reshape(a.rows, py, a.cols, px).mean(axis=(1, 3)).ravel()
            stamps[i] = time.time()
            n = i + 1
    except KeyboardInterrupt:
        print(f"\nstopped early at frame {n}")
    finally:
        cam.stop()

    frames, stamps = frames[:n], stamps[:n]
    np.save(out, frames)
    np.save(str(out).replace(".npy", "_t.npy"), stamps)

    # --- did the camera actually keep up? ---------------------------------
    gaps = np.diff(stamps) if n > 1 else np.array([np.nan])
    nominal = 1.0 / a.fps
    late = int((gaps > 1.5 * nominal).sum())
    meta = {
        "frames_requested": a.frames, "frames_recorded": n,
        "channels": a.rows * a.cols, "grid": [a.cols, a.rows],
        "capture_size": [a.width, a.height], "pixels_per_channel": px * py,
        "fps_requested": a.fps,
        "fps_measured": float(n / (stamps[-1] - stamps[0])) if n > 1 else None,
        "exposure_us": a.exposure, "analogue_gain": a.gain,
        "auto_exposure": False, "auto_white_balance": False,
        "median_frame_gap_s": float(np.median(gaps)),
        "long_gaps": late,
        "long_gap_fraction": float(late / len(gaps)),
        "started_unix": float(stamps[0]) if n else None,
        "wall_seconds": round(time.time() - t0, 2),
    }
    Path(str(out).replace(".npy", "_meta.json")).write_text(json.dumps(meta, indent=2))

    print(f"wrote {out}  {frames.shape[0]} frames x {frames.shape[1]} channels")
    print(f"measured {meta['fps_measured']:.2f} fps (asked for {a.fps})")
    if meta["long_gap_fraction"] > 0.01:
        print()
        print(f"WARNING: {meta['long_gap_fraction']:.1%} of frames arrived late.")
        print("The camera could not keep up. A late frame is a moment where the")
        print("camera and the screen disagree about what was being shown, which")
        print("adds noise that looks like degradation. Lower --fps or --frames,")
        print("close other programs, and record this session again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
