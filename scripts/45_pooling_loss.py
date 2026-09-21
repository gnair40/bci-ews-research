#!/usr/bin/env python3
"""
Where does the monitor's performance go when episodes are pooled across days?

The day-variance analysis produced an inverse-variance pooled AUC of 0.836 (T11)
and 0.889 (T5), while every pooled analysis in this project has reported
0.65-0.74. That is a large discrepancy and it needs an explanation, not a
footnote.

Three candidate causes, and they are separable:
  (a) the fit source   -- per-day fits here vs a global fit there
  (b) the episode set  -- 40 per day here vs all episodes there
  (c) POOLING ITSELF   -- comparing faulted and healthy episodes ACROSS days
                          rather than within one

This script holds (a) and (b) fixed and varies only (c). Every episode is scored
with its OWN day's fit, exactly once, and then the same scores are turned into
an AUC three ways:

  1. WITHIN-DAY   -- one AUC per day, averaged. What the day-variance run reports.
  2. POOLED       -- one AUC over everything at once.
  3. POOLED after per-day standardisation -- each score re-expressed as a robust
     z against that day's own healthy episodes, then pooled.

If 3 recovers 1, the loss is a per-session offset in the score scale and is
fixable by normalising per session. If 3 stays near 2, the loss is real and the
episodes are genuinely less separable once days are mixed.

Usage: python3 scripts/45_pooling_loss.py --participant T11|T5
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

    recs = []
    for d in days:
        eps = by_day.get(d, [])
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        r = np.random.default_rng(SEED + d)
        g = guard.DecoderGuard().fit(
            healthy[d][r.choice(len(healthy[d]), FIT_WINDOWS, replace=False)])
        for e in eps:
            X = ds.neural[e.block_id]
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12:
                continue
            Y, _ = inj.apply_episode(X, e)
            ow = int(np.searchsorted(starts, e.onset_bin))
            if ow < 6:
                continue
            F = det.window_features(Y, starts, WINDOW_BINS)
            g.recenter(F[:ow])
            sc = g.score(F)
            if not crossed.get(e.episode_id, False):
                recs.append({"day": d, "group": "healthy", "score": float(np.median(sc))})
            else:
                cw = crossing.get(e.episode_id, -1)
                if cw > ow and len(sc) >= cw:
                    recs.append({"day": d, "group": "faulted",
                                 "score": float(np.median(sc[ow:cw]))})
        print(f"  day {d}: scored")

    D = pd.DataFrame(recs)
    D.to_csv(OUT / f"pooling_scores{'' if P=='T11' else '_'+P}.csv", index=False)

    # 1. within-day
    per_day = []
    for d, g in D.groupby("day"):
        a = auc(g[g.group == "faulted"].score.values, g[g.group == "healthy"].score.values)
        if np.isfinite(a):
            per_day.append(a)

    # 2. pooled, raw
    pooled_raw = auc(D[D.group == "faulted"].score.values,
                     D[D.group == "healthy"].score.values)

    # 3. pooled after per-day robust standardisation against that day's HEALTHY
    #    episodes only -- the faulted ones must not set the scale they are judged
    #    against, or the normalisation would be doing the detector's job.
    z = []
    for d, g in D.groupby("day"):
        h = g[g.group == "healthy"].score.values
        if len(h) < 3:
            continue
        med = float(np.median(h))
        mad = float(np.median(np.abs(h - med))) * 1.4826
        scale = mad if mad > 1e-9 else (float(np.std(h)) or 1.0)
        gg = g.copy(); gg["z"] = (gg.score - med) / scale
        z.append(gg)
    Z = pd.concat(z) if z else D.assign(z=np.nan)
    pooled_z = auc(Z[Z.group == "faulted"].z.values, Z[Z.group == "healthy"].z.values)

    res = {
        "participant": P,
        "n_days": int(D.day.nunique()),
        "n_faulted": int((D.group == "faulted").sum()),
        "n_healthy": int((D.group == "healthy").sum()),
        "within_day_auc_mean": round(float(np.mean(per_day)), 4),
        "within_day_auc_min": round(float(np.min(per_day)), 4),
        "within_day_auc_max": round(float(np.max(per_day)), 4),
        "pooled_auc_raw": round(float(pooled_raw), 4),
        "pooled_auc_after_per_day_normalisation": round(float(pooled_z), 4),
    }
    res["loss_from_pooling"] = round(res["within_day_auc_mean"] - res["pooled_auc_raw"], 4)
    res["recovered_by_normalisation"] = round(
        res["pooled_auc_after_per_day_normalisation"] - res["pooled_auc_raw"], 4)
    frac = (res["recovered_by_normalisation"] / res["loss_from_pooling"]
            if abs(res["loss_from_pooling"]) > 1e-9 else float("nan"))
    res["fraction_of_loss_recovered"] = round(float(frac), 3)
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"pooling_loss{'' if P=='T11' else '_'+P}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
