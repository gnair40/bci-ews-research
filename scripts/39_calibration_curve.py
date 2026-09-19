#!/usr/bin/env python3
"""
How much healthy recording does a monitor need to be commissioned?

Scope fixed in `research/CALIBRATION_STUDY_NOTE.md` before this ran.

WHY THIS IS THE QUESTION THE TRANSFER ANALYSIS LEAVES
-----------------------------------------------------
0 of 7 candidates improved both participants, so what helps appears to be
participant-specific. If a monitor must be fitted per person anyway, the useful
number is not "which feature wins" but "how much healthy data does commissioning
one take". That is within-participant, so the disagreement blocking everything
else does not apply.

WHAT VARIES AND WHAT DOES NOT
-----------------------------
Only the number of healthy windows used for the GLOBAL fit. Local re-baselining
on each episode's own pre-onset windows is unchanged, so this isolates what the
global fit contributes -- which, after re-baselining, is essentially the subspace
the profile component is measured in.

EFFICIENCY
----------
Features are computed once per episode and cached, then scored under every fit.
Injection and feature extraction dominate the cost and do not depend on the fit,
so recomputing them per grid point would multiply the run by 35 for no reason.

Usage: python3 scripts/39_calibration_curve.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250
GRID = [5, 10, 20, 40, 80, 160, None]     # None = all available
REPEATS = 5
N_EPISODES = 300
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def auc(E, H):
    if len(E) < 5 or len(H) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def draw_contiguous(H_blocks, n, rng):
    """n consecutive windows from ONE block -- what a real commissioning session
    would collect. Adjacent windows overlap (30 s window, 5 s step) and lag-1
    r = 0.995, so this is far less information than n windows scattered across
    the record, even though the count is identical."""
    ok = [B for B in H_blocks if len(B) >= n]
    if not ok:
        return None
    B = ok[rng.integers(len(ok))]
    s0 = int(rng.integers(len(B) - n + 1))
    return B[s0:s0 + n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    ap.add_argument("--draw", choices=["scattered", "contiguous"], default="scattered",
                    help="scattered = the frozen protocol (windows drawn at random from the "
                         "whole healthy record). contiguous = added after seeing the frozen "
                         "curve, to test whether the window count translates into a claim "
                         "about minutes of recording. See CALIBRATION_STUDY_NOTE.md.")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    _, meta_path = rd.decoder_paths(P)
    meta = json.loads(meta_path.read_text())
    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)
    fit_blocks = [b for b in meta["train_blocks"] if b in ds.neural]

    H_blocks = []
    for b in fit_blocks:
        X = ds.neural[b]
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        H_blocks.append(det.window_features(X, st, WINDOW_BINS))
    H_all = np.vstack(H_blocks)

    base = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    base = base[base.detector == "decoder_guard"]
    crossed = dict(zip(base.episode_id, base.crossed))
    crossing = dict(zip(base.episode_id, base.crossing_w))

    rng = np.random.default_rng(SEED)
    usable = [e for e in episodes if e.block_id in ds.neural]
    pick = rng.choice(len(usable), size=min(N_EPISODES, len(usable)), replace=False)
    chosen = [usable[i] for i in pick]

    print(f"Calibration curve — {P}  (draw: {args.draw})")
    print(f"  {len(H_all)} healthy windows available for the global fit")
    print(f"  {len(chosen)} episodes (fixed random sample, seed {SEED})\n")

    # Cache features once. This is the whole reason the run is minutes not hours.
    cache = []
    for i, e in enumerate(chosen):
        X = ds.neural[e.block_id]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        Y, _ = inj.apply_episode(X, e)
        ow = int(np.searchsorted(starts, e.onset_bin))
        if ow < 6:
            continue
        cache.append((e.episode_id, det.window_features(Y, starts, WINDOW_BINS).astype(np.float32), ow))
        if (i + 1) % 100 == 0:
            print(f"  cached {i+1}")
    print(f"  cached {len(cache)} episodes\n")

    rows = []
    print(f"  {'windows':>9}{'minutes':>9}   AUC (mean over repeats, +/- spread)")
    for n in GRID:
        vals = []
        for rep in range(1 if n is None else REPEATS):
            r2 = np.random.default_rng(SEED + rep)
            if n is None:
                H = H_all
            elif args.draw == "scattered":
                H = H_all[r2.choice(len(H_all), min(n, len(H_all)), replace=False)]
            else:
                H = draw_contiguous(H_blocks, n, r2)
                if H is None:
                    continue
            if len(H) < 8:
                continue
            g = guard.DecoderGuard().fit(H)
            E, Hp = [], []
            for eid, F, ow in cache:
                g.recenter(F[:ow])
                sc = g.score(F)
                if not crossed.get(eid, False):
                    Hp.append(float(np.median(sc)))
                else:
                    cw = crossing.get(eid, -1)
                    if cw > ow and len(sc) >= cw:
                        E.append(float(np.median(sc[ow:cw])))
            a = auc(E, Hp)
            if np.isfinite(a):
                vals.append(a)
        if not vals:
            continue
        label = len(H_all) if n is None else n
        # Span of recording the windows occupy IF collected contiguously:
        # (n-1) steps plus one full window. For the scattered draw the windows
        # come from all over the record, so this is not a duration -- it is only
        # reported so the two draws are on one axis.
        mins = ((label - 1) * STEP_BINS + WINDOW_BINS) * 0.02 / 60
        m, sd = float(np.mean(vals)), float(np.std(vals))
        rows.append({"participant": P,
                     "draw": "all-pooled" if n is None else args.draw,
                     "n_windows": label, "minutes": round(mins, 1),
                     "auc_mean": round(m, 4), "auc_sd": round(sd, 4), "repeats": len(vals)})
        print(f"  {label:>9}{mins:>9.1f}   {m:.3f} +/- {sd:.3f}")

    sfx = ("" if P == "T11" else f"_{P}") + ("" if args.draw == "scattered" else "_contiguous")
    pd.DataFrame(rows).to_csv(OUT / f"calibration_curve{sfx}.csv", index=False)
    print(f"\nwrote {OUT/f'calibration_curve{sfx}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
