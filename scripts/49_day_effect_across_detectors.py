#!/usr/bin/env python3
"""
Is the day effect decoder-guard's fault, or the data's?

Prediction committed in advance, in the addendum to
research/DAY_PREDICTOR_PREREGISTRATION.md: SHARED, at rho > 0.7 between
decoder-guard and each baseline, because the mechanism proposed for P5 -- an
atypical recording -- is not a property of any one detector.

Method is identical to 44_day_variance.py in every respect (same days, same
episodes, same 40-window same-day fits, same early-warning window). Only the
detector changes. If anything else varied, a difference between detectors would
be confounded with that.

Usage: python3 scripts/49_day_effect_across_detectors.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
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
FIT_WINDOWS = 40
EPISODES_PER_DAY = 40
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


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    inj = _load("inj", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")

    makers = {
        "mean_activity": det.MeanActivity,
        "robust_dispersion": det.RobustDispersion,
        "distribution_shift": det.DistributionShift,
        "decoder_guard": guard.DecoderGuard,
    }

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    healthy: dict[int, np.ndarray] = {}
    for b, X in ds.neural.items():
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(st) == 0:
            continue
        F = det.window_features(X, st, WINDOW_BINS)
        d = day_of(b)
        healthy[d] = F if d not in healthy else np.vstack([healthy[d], F])
    days = sorted(d for d, F in healthy.items() if len(F) >= FIT_WINDOWS)

    base = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    base = base[base.detector == "decoder_guard"]
    crossed = dict(zip(base.episode_id, base.crossed))
    crossing = dict(zip(base.episode_id, base.crossing_w))

    rng = np.random.default_rng(SEED)
    by_day: dict[int, list] = {}
    for e in episodes:
        if e.block_id in ds.neural:
            by_day.setdefault(day_of(e.block_id), []).append(e)

    rows = []
    for d in days:
        eps = by_day.get(d, [])
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        r = np.random.default_rng(SEED + d)
        H_fit = healthy[d][r.choice(len(healthy[d]), FIT_WINDOWS, replace=False)]

        # Cache the episode features once; every detector sees exactly the same
        # windows of exactly the same injected data.
        cached = []
        for e in eps:
            X = ds.neural[e.block_id]
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12:
                continue
            Y, _ = inj.apply_episode(X, e)
            ow = int(np.searchsorted(starts, e.onset_bin))
            if ow < 6:
                continue
            cached.append((e.episode_id, det.window_features(Y, starts, WINDOW_BINS), ow))

        row = {"day": d, "n_episodes": len(cached)}
        for dn, maker in makers.items():
            g = maker().fit(H_fit)
            E, Hp = [], []
            for eid, F, ow in cached:
                g.recenter(F[:ow])
                sc = g.score(F)
                if not crossed.get(eid, False):
                    Hp.append(float(np.median(sc)))
                else:
                    cw = crossing.get(eid, -1)
                    if cw > ow and len(sc) >= cw:
                        E.append(float(np.median(sc[ow:cw])))
            row[dn] = auc(E, Hp)
        rows.append(row)
        print("  day %d: " % d + "  ".join(
            f"{k}={row[k]:.3f}" for k in makers if np.isfinite(row[k])))

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    D.to_csv(OUT / f"day_effect_detectors{sfx}.csv", index=False)

    pred = pd.read_csv(OUT / f"day_predictors{sfx}.csv")[["day", "P5_decoder_error"]]
    M = D.merge(pred, on="day", how="left")

    res = {"participant": P, "n_days": int(len(M))}
    for dn in makers:
        if dn == "decoder_guard":
            continue
        ok = M[dn].notna() & M.decoder_guard.notna()
        if ok.sum() >= 4:
            r, p = stats.spearmanr(M.loc[ok, dn], M.loc[ok, "decoder_guard"])
            res[f"guard_vs_{dn}"] = {"rho": round(float(r), 3), "p": round(float(p), 4),
                                     "n": int(ok.sum()),
                                     "meets_predicted_0.7": bool(r > 0.7)}
    for dn in makers:
        ok = M[dn].notna() & M.P5_decoder_error.notna()
        if ok.sum() >= 4:
            r, p = stats.spearmanr(M.loc[ok, dn], M.loc[ok, "P5_decoder_error"])
            res[f"{dn}_vs_decoder_error"] = {"rho": round(float(r), 3),
                                             "p": round(float(p), 4), "n": int(ok.sum())}
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"day_effect_detectors{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
