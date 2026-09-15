#!/usr/bin/env python3
"""Shows a grid of patches whose brightness encodes a heading direction.

Each patch has a fixed preferred direction. Its brightness is highest when the
current heading matches that preference, the same way a direction-tuned neuron
fires fastest for its preferred direction.

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
ap.add_argument("--brightness", type=float, default=1.0)  # 0-1, for the SNR sweep
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

def draw_heading():
    """Uniform over all directions by default. Raising --concentration makes
    headings cluster, which is the task-geometry variable I sweep in Phase 9."""
    if a.concentration <= 0:
        return rng.uniform(0, 2 * math.pi)
    return float(rng.vonmises(0.0, a.concentration))

heading, trial = draw_heading(), 0
try:
    for f in range(a.frames):
        if f % a.hold == 0:
            heading, trial = draw_heading(), f // a.hold
        b = 0.5 * (1 + np.cos(heading - PREF)) * a.brightness
        for i in range(N):
            v = int(np.clip(b[i], 0, 1) * 255)
            pygame.draw.rect(screen, (v, v, v),
                             ((i % a.cols) * a.patch, (i // a.cols) * a.patch,
                              a.patch, a.patch))
        pygame.display.flip()
        w.writerow([f, time.time(), heading, trial])
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise KeyboardInterrupt
        clock.tick(a.fps)
finally:
    log.close()
    pygame.quit()
