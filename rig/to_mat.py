#!/usr/bin/env python3
"""Turns one recorded block into the three .mat files the loader expects."""
import argparse
from pathlib import Path
import numpy as np
from scipy.io import savemat

ap = argparse.ArgumentParser()
ap.add_argument("--block", required=True)     # rig/xxx.npy from capture.py
ap.add_argument("--stimlog", required=True)   # rig/stim_log.csv
ap.add_argument("--session", type=int, required=True)
ap.add_argument("--blocknum", type=int, required=True)
ap.add_argument("--lag", type=float, default=0.0)   # seconds, from Procedure 63
ap.add_argument("--root", default="data/raw_rig")
a = ap.parse_args()

X = np.load(a.block)
t_cam = np.load(a.block.replace(".npy", "_t.npy")) - a.lag
stim = np.genfromtxt(a.stimlog, delimiter=",", names=True)

# For each captured frame take the heading logged closest in time.
idx = np.searchsorted(stim["t_unix"], t_cam).clip(0, len(stim) - 1)
head = stim["heading_rad"][idx]
trial = stim["trial"][idx].astype(int)

n = len(X)
cursor = np.zeros((n, 2), np.float32)
target = np.stack([np.cos(head), np.sin(head)], 1).astype(np.float32)

# One trial per run of constant heading.
edges = np.flatnonzero(np.diff(trial)) + 1
starts = np.concatenate([[0], edges])
stops = np.concatenate([edges, [n]])
keep = (stops - starts) >= 10
starts, stops = starts[keep], stops[keep]
ntr = len(starts)

bd = Path(a.root) / "RIG" / f"day_{a.session}" / f"block_{a.blocknum}"
bd.mkdir(parents=True, exist_ok=True)
savemat(bd / "data.mat", {"nctx": X.astype(np.float32)})
savemat(bd / "info.mat", {
    "cursorPos": cursor, "targetPos": target,
    "angleErrorPerTrial": np.full(ntr, np.nan),
    "trialSuccess": np.ones(ntr, bool),
    "timeToTarget": np.full(ntr, np.nan),
    "pathEfficiency": np.full(ntr, np.nan),
    "orthChanges": np.zeros(ntr),
    "percentCorrect": np.nan})
savemat(bd / "task.mat", {
    "startStops": np.stack([starts + 1, stops], 1).astype(float),  # MATLAB is 1-based
    "name": "rigCosineField",
    "excludeTrials": np.zeros(ntr, bool),
    "useClick": np.zeros(ntr, bool)})
print(f"wrote {bd}  {n} bins, {ntr} trials")
