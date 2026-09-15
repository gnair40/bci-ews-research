#!/usr/bin/env python3
"""
Was "the features' fault" actually the model's fault?

Preregistered in research/PERMUTATION_INVARIANT_NOTE.md, prediction included:
the worst confusable pair should rise from 0.574 to above 0.75 on T11.

THE ARGUMENT
------------
58_mode_separability.py fitted a LINEAR discriminant on the per-channel vector,
searching for one fixed direction in 384-dimensional channel space. But which
channels a fault touches is drawn at random per episode -- CHANNEL_DROPOUT
silences a random subset, GAIN_DRIFT scales each channel by an independent random
factor -- so no fixed direction identifies either. The model is structurally
incapable of seeing them, and its failure said nothing about the information.

The three confusable modes differ in the SHAPE of the per-channel change
distribution, which does not depend on channel identity at all:

    CHANNEL_DROPOUT   sparse and extreme  -- most channels untouched, a few at zero
    RATE_LOSS         uniform shift       -- everything down together
    GAIN_DRIFT        spread, mean intact -- scattered both ways

Everything else is held identical to 58: same episodes, same
leave-one-session-out, same fixed lambda, same pairwise AUC. Only the
representation changes.

Usage: python3 scripts/62_permutation_invariant.py --participant T11|T5
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
LAMBDA_FRAC = 0.1
MIN_PER_CLASS = 8
SEED = 20260902

FEATURE_NAMES = ["mean", "sd", "skew", "kurtosis", "p05", "p25", "p50", "p75",
                 "p95", "frac_unchanged", "frac_severely_down",
                 "participation_ratio"]


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


def invariant_features(v: np.ndarray) -> np.ndarray:
    """Twelve summaries of the per-channel change vector, none of which depends
    on WHICH channel is which. Fixed in advance; nothing added after seeing a
    result."""
    a = np.abs(v)
    l1, l2 = a.sum(), np.sqrt((a ** 2).sum())
    return np.array([
        float(np.mean(v)),
        float(np.std(v)),
        float(stats.skew(v)),
        float(stats.kurtosis(v)),
        *[float(np.percentile(v, q)) for q in (5, 25, 50, 75, 95)],
        float(np.mean(a < 0.05)),            # untouched channels
        float(np.mean(v < -1.0)),            # severely reduced -- dropout's mark
        float(l1 / l2) if l2 > 1e-12 else 0.0,   # participation ratio: sparsity
    ])


def lda_direction(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    mu = A.mean(axis=0) - B.mean(axis=0)
    S = np.cov(np.vstack([A - A.mean(axis=0), B - B.mean(axis=0)]).T)
    S = np.atleast_2d(S)
    lam = LAMBDA_FRAC * np.trace(S) / S.shape[0]
    return np.linalg.solve(S + lam * np.eye(S.shape[0]), mu)


def random_channel_control(Xfull, y, g, n_dims, n_repeats=20, seed=SEED):
    """Same pipeline on n_dims RANDOMLY CHOSEN RAW CHANNELS.

    Twelve invariant features beat 384 raw channels, so part of the gain could
    be dimensionality rather than invariance -- a 384-feature discriminant on
    ~400 episodes is heavily regularised and may simply underfit. This control
    holds the dimension count fixed and destroys only the invariance. If 12
    random channels do poorly, the gain is the representation; if they do well,
    it was the dimension count and my explanation is wrong.
    """
    rng = np.random.default_rng(seed)
    modes = sorted(set(y))
    out = {}
    for m1, m2 in itertools.combinations(modes, 2):
        aucs = []
        for _ in range(n_repeats):
            cols = rng.choice(Xfull.shape[1], n_dims, replace=False)
            Xr = Xfull[:, cols]
            Xr = (Xr - Xr.mean(axis=0)) / (Xr.std(axis=0) + 1e-9)
            s1, s2 = [], []
            for held in sorted(set(g)):
                tr, te = g != held, g == held
                A, B = Xr[tr & (y == m1)], Xr[tr & (y == m2)]
                if len(A) < MIN_PER_CLASS or len(B) < MIN_PER_CLASS:
                    continue
                w = lda_direction(A, B)
                a, b = Xr[te & (y == m1)] @ w, Xr[te & (y == m2)] @ w
                if len(a) and len(b):
                    s1.extend(a.tolist()); s2.extend(b.tolist())
            v = auc(np.array(s1), np.array(s2))
            if np.isfinite(v):
                aucs.append(v)
        out[f"{m1}|{m2}"] = round(float(np.mean(aucs)), 4) if aucs else None
    return out


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

    X, Xraw, y, g = [], [], [], []
    for e in episodes:
        if e.episode_id not in keep or e.block_id not in ds.neural or e.mode == "NONE":
            continue
        Xb = ds.neural[e.block_id]
        starts = np.arange(0, Xb.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        ow = int(np.searchsorted(starts, e.onset_bin))
        ow_strict = int(np.searchsorted(starts + WINDOW_BINS, e.onset_bin, side="right"))
        cw = int(cw_by_id[e.episode_id])
        if ow_strict < 3 or cw <= ow:
            continue
        Y, _ = inj.apply_episode(Xb, e)
        F = det.window_features(Y, starts, WINDOW_BINS)
        base = np.log1p(np.maximum(np.median(F[:ow_strict], axis=0), 0.0))
        during = np.log1p(np.maximum(np.median(F[ow:cw], axis=0), 0.0))
        d = during - base
        X.append(invariant_features(d))
        Xraw.append(d)
        y.append(e.mode)
        g.append(day_of(e.block_id))

    X = np.vstack(X); Xraw = np.vstack(Xraw); y = np.array(y); g = np.array(g)
    # Standardise so the fixed lambda means the same thing across features whose
    # units differ by orders of magnitude (a percentile against a fraction).
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)
    print(f"  {len(X)} episodes, {X.shape[1]} invariant features, "
          f"{len(set(g))} sessions\n")

    sfx = "" if P == "T11" else f"_{P}"
    prev_path = OUT / f"mode_separability{sfx}.csv"
    prev = pd.read_csv(prev_path) if prev_path.exists() else None

    rows = []
    for m1, m2 in itertools.combinations(sorted(set(y)), 2):
        s1, s2 = [], []
        for held in sorted(set(g)):
            tr, te = g != held, g == held
            A, B = X[tr & (y == m1)], X[tr & (y == m2)]
            if len(A) < MIN_PER_CLASS or len(B) < MIN_PER_CLASS:
                continue
            w = lda_direction(A, B)
            a, b = X[te & (y == m1)] @ w, X[te & (y == m2)] @ w
            if len(a) and len(b):
                s1.extend(a.tolist()); s2.extend(b.tolist())
        a_ = auc(np.array(s1), np.array(s2))
        was = None
        if prev is not None:
            m = prev[(prev.mode_a == m1) & (prev.mode_b == m2)]
            if len(m):
                was = float(m.auc.iloc[0])
        rows.append({"mode_a": m1, "mode_b": m2,
                     "auc_invariant": round(a_, 4) if np.isfinite(a_) else None,
                     "auc_per_channel": was,
                     "change": round(a_ - was, 4) if (was and np.isfinite(a_)) else None})
        arrow = "" if was is None else f"   was {was:.3f}   change {a_ - was:+.3f}"
        print(f"  {m1:<20} vs {m2:<20} AUC {a_:.3f}{arrow}")

    D = pd.DataFrame(rows)
    D.to_csv(OUT / f"permutation_invariant{sfx}.csv", index=False)

    confusable = D[~(D.mode_a.eq("GEOMETRY_ROTATION") | D.mode_b.eq("GEOMETRY_ROTATION"))]
    rot = D[D.mode_a.eq("GEOMETRY_ROTATION") | D.mode_b.eq("GEOMETRY_ROTATION")]
    res = {
        "participant": P, "n_episodes": int(len(X)),
        "n_features": int(X.shape[1]), "feature_names": FEATURE_NAMES,
        "worst_pair_invariant": round(float(D.auc_invariant.min()), 4),
        "worst_pair_per_channel": round(float(D.auc_per_channel.min()), 4)
        if D.auc_per_channel.notna().any() else None,
        "confusable_trio_mean_invariant": round(float(confusable.auc_invariant.mean()), 4),
        "confusable_trio_mean_per_channel": round(float(confusable.auc_per_channel.mean()), 4)
        if confusable.auc_per_channel.notna().any() else None,
        "rotation_pairs_mean_invariant": round(float(rot.auc_invariant.mean()), 4),
        "rotation_pairs_mean_per_channel": round(float(rot.auc_per_channel.mean()), 4)
        if rot.auc_per_channel.notna().any() else None,
    }
    res["prediction_worst_pair_above_0.75"] = bool(res["worst_pair_invariant"] > 0.75)

    ctrl = random_channel_control(Xraw, y, g, n_dims=X.shape[1])
    res["control_random_channels_same_dim"] = ctrl
    vals = [v for v in ctrl.values() if v is not None]
    res["control_mean_auc"] = round(float(np.mean(vals)), 4) if vals else None
    res["gain_is_representation_not_dimension"] = bool(
        res["control_mean_auc"] is not None
        and res["confusable_trio_mean_invariant"] - res["control_mean_auc"] > 0.15)
    print(f"\n  control: {X.shape[1]} RANDOM raw channels, 20 draws")
    for k, v in ctrl.items():
        print(f"    {k:<45} {v}")
    print(f"  control mean {res['control_mean_auc']}   "
          f"invariant trio mean {res['confusable_trio_mean_invariant']}")
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"permutation_invariant{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
