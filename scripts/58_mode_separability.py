#!/usr/bin/env python3
"""
Is the information to tell fault modes apart even present in these features?

Preregistered in research/MODE_SEPARABILITY_NOTE.md, including the prediction
that GEOMETRY_ROTATION vs GAIN_DRIFT separates at AUC > 0.8.

THIS IS AN INFORMATION PROBE AND AN UPPER BOUND, NOT A MONITOR
--------------------------------------------------------------
It uses the injected fault labels, which a deployed monitor never has, and fits a
discriminant per pair of modes. No number here may be quoted as monitor
performance. It answers one question: when attribution named GEOMETRY_ROTATION
wrongly 100% of the time, was that because the four components throw the
information away, or because the information is not there to begin with?

METHOD
------
Feature: per-channel SIGNED log-ratio between the early-warning window and the
episode's own strictly-clean pre-onset baseline. Signed and per-channel on
purpose -- a scalar dispersion measure discards exactly the signs and pairing
that should distinguish a rotation (channels exchange activity, some up and their
partners down) from a gain drift (channels scale independently).

Validation: leave-one-SESSION-out. Episodes from one block are not independent,
so a random episode split would leak. Regularisation is fixed at
lambda = 0.1 * trace(Sigma)/p in advance and is not tuned.

Usage: python3 scripts/58_mode_separability.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250
LAMBDA_FRAC = 0.1          # fixed in advance
MIN_PER_CLASS = 8
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def auc(a, b):
    if len(a) < 5 or len(b) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(a, b, alternative="two-sided")
    return float(u / (len(a) * len(b)))


def lda_direction(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Regularised Fisher direction. lambda is fixed, not selected."""
    mu = A.mean(axis=0) - B.mean(axis=0)
    S = np.cov(np.vstack([A - A.mean(axis=0), B - B.mean(axis=0)]).T)
    lam = LAMBDA_FRAC * np.trace(S) / S.shape[0]
    return np.linalg.solve(S + lam * np.eye(S.shape[0]), mu)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    inj = _load("inj", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    sc = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    sc = sc[(sc.detector == "decoder_guard") & (sc.split == "test") & sc.crossed]
    cw_by_id = dict(zip(sc.episode_id, sc.crossing_w))
    keep = set(sc.episode_id)

    X, y, g = [], [], []
    for e in episodes:
        if e.episode_id not in keep or e.block_id not in ds.neural or e.mode == "NONE":
            continue
        Xb = ds.neural[e.block_id]
        starts = np.arange(0, Xb.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        ow = int(np.searchsorted(starts, e.onset_bin))
        # Strictly clean baseline: the window must END at or before onset.
        ow_strict = int(np.searchsorted(starts + WINDOW_BINS, e.onset_bin, side="right"))
        cw = int(cw_by_id[e.episode_id])
        if ow_strict < 3 or cw <= ow:
            continue
        Y, _ = inj.apply_episode(Xb, e)
        F = det.window_features(Y, starts, WINDOW_BINS)
        base = np.log1p(np.maximum(np.median(F[:ow_strict], axis=0), 0.0))
        during = np.log1p(np.maximum(np.median(F[ow:cw], axis=0), 0.0))
        X.append(during - base)
        y.append(e.mode)
        g.append(day_of(e.block_id))

    X = np.vstack(X); y = np.array(y); g = np.array(g)
    print(f"  {len(X)} episodes, {X.shape[1]} channels, "
          f"{len(set(g))} sessions, modes {sorted(set(y))}\n")

    modes = sorted(set(y))
    rows = []
    for m1, m2 in itertools.combinations(modes, 2):
        s1, s2 = [], []
        for held in sorted(set(g)):
            tr = g != held
            te = g == held
            A = X[tr & (y == m1)]; B = X[tr & (y == m2)]
            if len(A) < MIN_PER_CLASS or len(B) < MIN_PER_CLASS:
                continue
            w = lda_direction(A, B)
            a = X[te & (y == m1)] @ w
            b = X[te & (y == m2)] @ w
            if len(a) and len(b):
                s1.extend(a.tolist()); s2.extend(b.tolist())
        a_ = auc(np.array(s1), np.array(s2))
        rows.append({"mode_a": m1, "mode_b": m2, "n_a": len(s1), "n_b": len(s2),
                     "auc": round(a_, 4) if np.isfinite(a_) else None})
        print(f"  {m1:<20} vs {m2:<20} AUC {a_:.3f}   (n {len(s1)}/{len(s2)})")

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    D.to_csv(OUT / f"mode_separability{sfx}.csv", index=False)

    key = D[(D.mode_a == "GAIN_DRIFT") & (D.mode_b == "GEOMETRY_ROTATION")]
    res = {"participant": P, "n_episodes": int(len(X)),
           "n_sessions": int(len(set(g))),
           "n_channels": int(X.shape[1]),
           "lambda_frac": LAMBDA_FRAC,
           "median_pairwise_auc": round(float(D.auc.median()), 4),
           "min_pairwise_auc": round(float(D.auc.min()), 4),
           "max_pairwise_auc": round(float(D.auc.max()), 4)}
    if len(key):
        v = float(key.auc.iloc[0])
        res["gain_drift_vs_rotation_auc"] = round(v, 4)
        res["prediction_met_auc_above_0.8"] = bool(v > 0.8)
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"mode_separability{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
