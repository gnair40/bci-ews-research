#!/usr/bin/env python3
"""Shows a grid of patches whose brightness encodes a heading direction.

Each patch has a fixed preferred direction. Its brightness is highest when the
current heading matches that preference, the same way a direction-tuned neuron
fires fastest for its preferred direction.

MODULATION DEPTH IS THE MOST IMPORTANT SETTING IN THIS FILE
-----------------------------------------------------------
A patch sits at --base brightness and swings by --depth with direction:

    patch = base + depth * cos(heading - preferred_direction)

The first version of this file used 0.5 * (1 + cos(...)), a full 100% swing.
Simulated in scripts/72_rig_digital_twin.py, that rig decoded direction to 0.0
degrees of error against an 89 degree chance level, where the neural data sits
at 54.6 against 90.7. Two things followed, both fatal: a comparison between a
perfect decoder and a barely-above-chance one measures difficulty rather than
neurons, and no injected fault could move an error that was already zero, so
there was no severity ladder at all.

Real direction-tuned neurons fire at a substantial baseline and modulate it
modestly, so each channel carries little information and the decoder is limited
by channel quality -- which is what makes degrading a channel matter. The small
default depth below reproduces that, and puts the rig within about a degree of
the neural operating point. Do not raise it to make the picture look nicer on
the screen; the whole comparison depends on it.

THE SCREEN CANNOT SHOW A FRACTION OF A BRIGHTNESS LEVEL, SO IT IS DITHERED
--------------------------------------------------------------------------
The calibrated depth asks each patch to swing by about half of one brightness
level: 126.96 to 128.03 out of 0-255. A display emits whole levels only, so
rounding each patch to an integer would throw the entire signal away and the rig
would record nothing but noise. This is a real hardware limit, not a modelling
detail, and it nearly went unnoticed.

The fix is spatial dithering, which is standard practice in visual
psychophysics. A patch is 40x40 = 1600 screen pixels. To show a mean level of
127.4, set 40% of its pixels to 128 and the rest to 127. The camera's optics and
its 2x2-pixel sampling average over the whole patch, so what it measures is the
fractional mean. Resolution becomes 1/1600 of a level instead of 1, which is
ample.

The dither mask is drawn once and reused every frame rather than redrawn each
time. That is faster, and more importantly it makes the dither a FIXED spatial
pattern instead of a new noise source flickering in every frame.

Writes rig/stim_log.csv, one row per frame, holding the true heading. That file
is the ground truth for the whole experiment, so it is recorded rather than
reconstructed afterwards.
"""
import argparse, csv, math, time
import numpy as np
import pygame

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=24)
ap.add_argument("--rows", type=int, default=16)     # 24 x 16 = 384 channels
ap.add_argument("--patch", type=int, default=40)    # screen pixels per patch
ap.add_argument("--fps", type=int, default=50)      # must match the camera
ap.add_argument("--hold", type=int, default=100)    # frames per heading
ap.add_argument("--frames", type=int, default=15000)  # 5 min at 50 fps
ap.add_argument("--brightness", type=float, default=1.0)  # 0-1, overall dimming
ap.add_argument("--base", type=float, default=0.5)       # DC level of every patch
ap.add_argument("--depth", type=float, default=0.00211)   # direction modulation
# ^ calibrated in reports/RIG_DIGITAL_TWIN.md to match T11's margin over chance.
ap.add_argument("--seed", type=int, default=20260826)
ap.add_argument("--concentration", type=float, default=0.0)  # 0 = all directions
ap.add_argument("--out", default="rig/stim_log.csv")
a = ap.parse_args()

N = a.cols * a.rows
rng = np.random.default_rng(a.seed)

# Preferred directions are fixed for the life of the rig. Save them once and
# reuse the saved file, so the channel identities never change between sessions.
try:
    PREF = np.load("rig/preferred_directions.npy")
    assert len(PREF) == N
except Exception:
    PREF = rng.uniform(0, 2 * math.pi, N)
    np.save("rig/preferred_directions.npy", PREF)

pygame.init()
screen = pygame.display.set_mode((a.cols * a.patch, a.rows * a.patch))
clock = pygame.time.Clock()

log = open(a.out, "w", newline="")
w = csv.writer(log)
w.writerow(["frame", "t_unix", "heading_rad", "trial"])
# The true heading is logged every frame. It is the ground truth for the whole
# experiment, so it is recorded as it is drawn rather than reconstructed later.

def draw_heading():
    """Uniform over all directions by default. Raising --concentration makes
    headings cluster, which is the task-geometry variable I sweep in Phase 9."""
    if a.concentration <= 0:
        return rng.uniform(0, 2 * math.pi)
    return float(rng.vonmises(0.0, a.concentration))

# Fixed dither mask, drawn once. Comparing each pixel's threshold against a
# patch's fractional part decides whether that pixel shows the lower or the
# higher level, which makes the patch mean land between them.
H, W = a.rows * a.patch, a.cols * a.patch
DITHER = rng.random((W, H)).astype(np.float32)      # pygame is (x, y)
frame = np.empty((W, H, 3), dtype=np.uint8)

def expand(vals):
    """One value per patch -> one value per screen pixel, in pygame (x, y) order."""
    g = vals.reshape(a.rows, a.cols).T              # -> (cols, rows)
    return np.repeat(np.repeat(g, a.patch, 0), a.patch, 1)

heading, trial = draw_heading(), 0
try:
    for f in range(a.frames):
        if f % a.hold == 0:
            heading, trial = draw_heading(), f // a.hold
        b = (a.base + a.depth * np.cos(heading - PREF)) * a.brightness
        t = np.clip(b, 0, 1) * 255.0
        lo = np.floor(t)
        px = expand(lo) + (DITHER < expand(t - lo))
        v = px.astype(np.uint8)
        frame[:, :, 0] = v; frame[:, :, 1] = v; frame[:, :, 2] = v
        pygame.surfarray.blit_array(screen, frame)
        pygame.display.flip()
        w.writerow([f, time.time(), heading, trial])
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise KeyboardInterrupt
        clock.tick(a.fps)
finally:
    log.close()
    pygame.quit()
