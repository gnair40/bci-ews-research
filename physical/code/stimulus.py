#!/usr/bin/env python3
"""
stimulus.py — draw the moving pattern the camera watches.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
It fills the screen with a grid of grey squares. Each square has its own
"preferred direction". When the computer picks a direction, squares whose
preference matches get slightly brighter and the rest get slightly dimmer.

That is the same trick a direction-tuned brain cell uses: it fires fastest for
its favourite direction of movement. The camera watching this screen is
therefore looking at something structured like a small patch of motor cortex.

The program writes down the true direction for every single frame. That file is
the ground truth for the whole experiment.

=============================================================================
THE TWO SETTINGS THAT MATTER MOST, AND WHY
=============================================================================
**--depth (modulation depth).** How much brighter a square gets for its
favourite direction. The obvious choice is "as much as possible", and it is
wrong. A simulation of this apparatus showed that at full brightness swing it
decodes direction PERFECTLY -- 0.0 degrees of error -- where the real neural
decoder sits at 54.6 degrees. An apparatus that good is useless: degrading it
barely changes anything, so there is nothing for a monitor to detect, and
comparing it to a brain would measure difficulty rather than monitoring.

Real neurons fire at a high baseline and modulate it only modestly. The small
default below reproduces that. **Do not raise it to make the screen look nicer.**

**Dithering.** The calibrated depth asks each square to change by about half of
one brightness level, out of the 255 a screen can show. A screen can only
display whole levels, so simply rounding would throw the entire signal away.

The fix is spatial dithering, standard in vision research: to show a level of
127.4, set 40% of the square's pixels to 128 and the rest to 127. The camera's
optics average over the square and measure the fraction. A square is 40x40 =
1600 pixels, so this gives 1/1600 of a level of resolution instead of 1.

This was nearly missed, and without it the apparatus records nothing but noise.

=============================================================================
HOW THE FAULT GETS APPLIED
=============================================================================
If you pass --plan (a file made by draw_onset.py), this program reads the
degradation that was drawn BEFORE the session, and applies it automatically at
the drawn moment -- but only for the two fault types that are imposed in
software. The other two are physical and you apply them by hand.

    GAIN_DRIFT         software, automatic
    GEOMETRY_ROTATION  software, automatic
    RATE_LOSS          BY HAND -- slide the filter in front of the lens
    CHANNEL_DROPOUT    BY HAND -- place tape over part of the field

The program prints a countdown for the by-hand ones so you know when to act.

=============================================================================
HOW TO RUN IT
=============================================================================
Healthy session:
    python3 physical/code/stimulus.py --frames 15000 --out physical/data/stim.csv

With a drawn degradation:
    python3 physical/code/stimulus.py --plan physical/data/onsets/s1_b3.json \
        --out physical/data/stim_s1_b3.csv

Normally you do not run this directly -- run_session.py starts it for you.

=============================================================================
WHAT IT PRODUCES
=============================================================================
A CSV with one row per frame: frame number, wall-clock time, the true direction
in radians, the trial number, and the gain actually applied.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PREF_FILE = HERE.parent / "data" / "preferred_directions.npy"


def benchmark(a) -> int:
    """How fast can THIS machine draw the pattern? Measured, not estimated.

    The frame budget is the one assumption in this design that a slow computer
    can break silently: if the stimulus cannot keep up, frames are late, the
    direction label on each camera frame is wrong by an unknown amount, and
    nothing in the recording says so. `bench.py frames` catches it afterwards.
    This catches it beforehand, in ten seconds, before a campaign is planned
    around a frame rate the machine cannot hold.

    It runs the real inner loop — same arithmetic, same array shapes — with no
    display attached, so it works over SSH.
    """
    import time as _t

    n = a.cols * a.rows
    rng = np.random.default_rng(a.seed)
    pref = rng.uniform(0, 2 * math.pi, n)
    W, H = a.cols * a.patch, a.rows * a.patch
    dither = rng.random((W, H)).astype(np.float32)
    dither_blocks = dither.reshape(a.cols, a.patch, a.rows, a.patch)
    frame_buf = np.empty((W, H, 3), dtype=np.uint8)
    buf_blocks = frame_buf.reshape(a.cols, a.patch, a.rows, a.patch, 3)
    gain = np.ones(n)

    def one(heading):
        b = (a.base + a.depth * np.cos(heading - pref)) * a.brightness * gain
        t = np.clip(b, 0, 1) * 255.0
        lo = np.floor(t)
        blk = lo.reshape(a.rows, a.cols).T[:, None, :, None]
        frc = (t - lo).reshape(a.rows, a.cols).T[:, None, :, None]
        px = blk.astype(np.uint8) + (dither_blocks < frc)
        buf_blocks[..., 0] = px
        buf_blocks[..., 1] = px
        buf_blocks[..., 2] = px

    for _ in range(10):
        one(1.0)
    t0 = _t.perf_counter()
    for i in range(a.benchmark):
        one(float(rng.uniform(0, 2 * math.pi)))
    per = (_t.perf_counter() - t0) / a.benchmark

    budget = 1.0 / a.fps
    used = per / budget
    print(f"screen              {W} x {H} = {W * H:,} pixels "
          f"({a.cols}x{a.rows} patches of {a.patch}x{a.patch})")
    print(f"frames measured     {a.benchmark}")
    print(f"per frame           {per * 1000:.2f} ms")
    print(f"budget at {a.fps} fps    {budget * 1000:.1f} ms")
    print(f"used                {used:.0%} of the budget")
    print(f"sustainable rate    {1 / per:.0f} fps, arithmetic only")
    print()
    print("This is the drawing arithmetic alone. pygame's blit and the display")
    print("flip cost more on top, so treat anything above about 60% as tight.")
    print()
    if used < 0.6:
        print(f"PASS — this machine can hold {a.fps} fps with room to spare.")
        return 0
    print(f"FAIL — {a.fps} fps is not safe on this machine. In order of "
          f"preference:")
    print("  1. Run the stimulus on a faster computer with the screen attached,")
    print("     and the capture on the Pi. Then re-measure the lag (bench.py")
    print("     lag) — two machines means two clocks.")
    print(f"  2. Lower --patch. It is {a.patch} now; 24 costs about a third as")
    print("     much. This SHRINKS THE PATTERN ON SCREEN and changes how many")
    print("     camera pixels see each patch, so it is an apparatus change:")
    print("     re-run bench.py margin afterwards and record it in the log.")
    print("  3. Drop to --fps 25 and record twice as long per session. The")
    print("     analysis window is 30 s either way; you halve the resolution")
    print("     of every lead-time claim, so say so in the write-up.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cols", type=int, default=24)
    ap.add_argument("--rows", type=int, default=16)   # 24 x 16 = 384 channels
    ap.add_argument("--patch", type=int, default=40,  # screen pixels per square
                    help="bigger gives finer dithering but a slower frame rate")
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--hold", type=int, default=100,  # frames per direction
                    help="100 frames at 50 fps = 2 seconds per direction")
    ap.add_argument("--frames", type=int, default=15000)
    ap.add_argument("--base", type=float, default=0.5,
                    help="the resting brightness of every square, 0 to 1")
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="direction modulation; calibrated, do not change lightly")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--plan", default=None,
                    help="a JSON file from draw_onset.py")
    ap.add_argument("--seed", type=int, default=20260920)
    ap.add_argument("--out", default="physical/data/stim_log.csv")
    ap.add_argument("--benchmark", type=int, default=0, metavar="N",
                    help="run N frames of the real arithmetic with NO display "
                         "and report the frame rate this machine can sustain. "
                         "Run it on the Pi before planning a campaign")
    a = ap.parse_args()

    if a.benchmark:
        return benchmark(a)

    plan = json.loads(Path(a.plan).read_text()) if a.plan else None
    if plan:
        a.frames = plan.get("frames", a.frames)
        a.fps = plan.get("fps", a.fps)

    import pygame

    n = a.cols * a.rows
    rng = np.random.default_rng(a.seed)

    # Preferred directions are fixed for the life of the apparatus. Saving them
    # once and reusing the file means channel identities never change between
    # sessions -- if they did, no two sessions would be comparable.
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
    if PREF_FILE.exists():
        pref = np.load(PREF_FILE)
        assert len(pref) == n, f"{PREF_FILE} has {len(pref)} channels, need {n}"
    else:
        pref = rng.uniform(0, 2 * math.pi, n)
        np.save(PREF_FILE, pref)
        print(f"created {PREF_FILE} — keep this file, it defines the channels")

    pygame.init()
    W, H = a.cols * a.patch, a.rows * a.patch
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    # A fixed dither mask, drawn once. Fixed rather than re-drawn each frame so
    # the dither is a stable spatial pattern instead of a new noise source
    # flickering in every frame.
    dither = rng.random((W, H)).astype(np.float32)
    frame_buf = np.empty((W, H, 3), dtype=np.uint8)

    # The screen, seen as blocks rather than pixels. A patch is uniform, so a
    # per-patch value broadcasts into (cols, patch, rows, patch) without ever
    # being expanded to pixels. The first version of this loop called np.repeat
    # twice per frame, allocating two 614,400-element arrays 50 times a second,
    # and measured 6.9 ms per frame on a fast laptop -- which extrapolates to
    # more than the whole 20 ms budget on a Raspberry Pi 4. This produces
    # bit-identical pixels in 1.8 ms. See --benchmark.
    dither_blocks = dither.reshape(a.cols, a.patch, a.rows, a.patch)
    buf_blocks = frame_buf.reshape(a.cols, a.patch, a.rows, a.patch, 3)

    def blocks(vals: np.ndarray) -> np.ndarray:
        """One value per square -> shape that broadcasts over its pixels."""
        return vals.reshape(a.rows, a.cols).T[:, None, :, None]

    # Per-channel gain, which is what GAIN_DRIFT changes once the onset passes.
    gain = np.ones(n)
    if plan and plan.get("fault_type") == "GAIN_DRIFT":
        sev = plan["severity"]
        g = 1.0 + sev * rng.normal(0, 0.5, n)
        gain_after = np.clip(g, 0.05, None)
        gain_after /= gain_after.mean()      # mean-preserving, so it is not
    else:                                    # just overall dimming in disguise
        gain_after = gain

    roll_after = 0
    if plan and plan.get("fault_type") == "GEOMETRY_ROTATION":
        roll_after = int(round(plan["severity"] * a.cols * 0.25))

    onset = plan["onset_frame"] if plan and plan.get("onset_frame") else None
    by_hand = plan and plan.get("fault_type") in ("RATE_LOSS", "CHANNEL_DROPOUT")

    if plan and not plan["healthy"]:
        print(f"Fault: {plan['fault_type']} severity {plan['severity']} "
              f"at {plan['onset_seconds']:.1f} s")
        if by_hand:
            print(">>> THIS ONE IS BY HAND. Watch the countdown. <<<")

    log = open(a.out, "w", newline="")
    w = csv.writer(log)
    w.writerow(["frame", "t_unix", "heading_rad", "trial", "fault_active"])

    heading, trial = float(rng.uniform(0, 2 * math.pi)), 0
    warned = set()
    try:
        for f in range(a.frames):
            if f % a.hold == 0:
                heading = float(rng.uniform(0, 2 * math.pi))
                trial = f // a.hold

            active = bool(onset is not None and f >= onset)

            if by_hand and onset is not None:
                left = (onset - f) / a.fps
                for mark in (60, 30, 10, 5, 0):
                    if mark not in warned and 0 <= left < mark + 0.5 and left >= mark - 0.5:
                        print(f"  apply the fault in {mark} s" if mark
                              else "  *** APPLY THE FAULT NOW ***", flush=True)
                        warned.add(mark)

            g = gain_after if active else gain
            b = (a.base + a.depth * np.cos(heading - pref)) * a.brightness * g
            t = np.clip(b, 0, 1) * 255.0

            if active and roll_after:
                t = np.roll(t.reshape(a.rows, a.cols), roll_after, axis=1).ravel()

            lo = np.floor(t)
            px = blocks(lo).astype(np.uint8) + (dither_blocks < blocks(t - lo))
            # Three explicit channel writes, not one broadcast write. The
            # broadcast version reads nicer and measured 2.6x SLOWER, because
            # adding a trailing axis defeats the memory layout. Measured, not
            # assumed.
            buf_blocks[..., 0] = px
            buf_blocks[..., 1] = px
            buf_blocks[..., 2] = px
            pygame.surfarray.blit_array(screen, frame_buf)
            pygame.display.flip()

            w.writerow([f, time.time(), heading, trial, int(active)])
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    raise KeyboardInterrupt
            clock.tick(a.fps)
    finally:
        log.close()
        pygame.quit()
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
