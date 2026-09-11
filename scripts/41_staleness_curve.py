#!/usr/bin/env python3
"""
How long does a commissioned monitor stay valid?

Scope fixed in `research/STALENESS_STUDY_NOTE.md` before this ran, including the
prediction that the effect would be small.

DESIGN
------
Fit the guard's global fit on 40 healthy windows from ONE source day, then score
episodes from ONE target day. Gap = target day - source day. Fit size is pinned
so it cannot confound the gap; the calibration curve justifies 40 (above the
singular regime, on the flat part).

The primary quantity is a DIFFERENCE, AUC(A->B) - AUC(B->B): each cross-day fit
against the same-day fit on the SAME target day. Days differ in how hard their
episodes are, and without this subtraction that difficulty would be
indistinguishable from staleness.

Checkpoints after every target day. Two container restarts have already cost
long runs in this project.

Usage: python3 scripts/41_staleness_curve.py --participant T11|T5
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
REPEATS = 5
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


def day_of(block_id: str) -> int:
    return int(re.search(r"day_(\d+)", block_id).group(1))


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

    # Healthy window features per day, from the untouched recordings.
    healthy: dict[int, np.ndarray] = {}
    for b, X in ds.neural.items():
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(st) == 0:
            continue
        F = det.window_features(X, st, WINDOW_BINS)
        d = day_of(b)
        healthy[d] = F if d not in healthy else np.vstack([healthy[d], F])
    days = sorted(d for d, F in healthy.items() if len(F) >= FIT_WINDOWS)
    print(f"Staleness — {P}")
    print(f"  {len(days)} days with >= {FIT_WINDOWS} healthy windows: {days}\n")

    base = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    base = base[base.detector == "decoder_guard"]
    crossed = dict(zip(base.episode_id, base.crossed))
    crossing = dict(zip(base.episode_id, base.crossing_w))

    rng = np.random.default_rng(SEED)
    by_day: dict[int, list] = {}
    for e in episodes:
        if e.block_id in ds.neural:
            by_day.setdefault(day_of(e.block_id), []).append(e)

    # Cache episode features once per target day -- injection and feature
    # extraction dominate the cost and do not depend on the fit.
    cache: dict[int, list] = {}
    for d in days:
        eps = by_day.get(d, [])
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        got = []
        for e in eps:
            X = ds.neural[e.block_id]
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12:
                continue
            Y, _ = inj.apply_episode(X, e)
            ow = int(np.searchsorted(starts, e.onset_bin))
            if ow < 6:
                continue
            got.append((e.episode_id,
                        det.window_features(Y, starts, WINDOW_BINS).astype(np.float32), ow))
        cache[d] = got
        print(f"  day {d}: {len(got)} episodes cached")
    print()

    def score(fit_H, target_day):
        g = guard.DecoderGuard().fit(fit_H)
        E, Hp = [], []
        for eid, F, ow in cache[target_day]:
            g.recenter(F[:ow])
            sc = g.score(F)
            if not crossed.get(eid, False):
                Hp.append(float(np.median(sc)))
            else:
                cw = crossing.get(eid, -1)
                if cw > ow and len(sc) >= cw:
                    E.append(float(np.median(sc[ow:cw])))
        return auc(E, Hp)

    rows = []
    ckpt = OUT / f"staleness{'' if P=='T11' else '_'+P}.csv"
    for tgt in days:
        if len(cache[tgt]) < 8:
            print(f"  day {tgt}: too few episodes, skipped")
            continue
        for src in days:
            vals = []
            for rep in range(REPEATS):
                r = np.random.default_rng(SEED + 1000 * rep + src)
                H = healthy[src][r.choice(len(healthy[src]), FIT_WINDOWS, replace=False)]
                a = score(H, tgt)
                if np.isfinite(a):
                    vals.append(a)
            if not vals:
                continue
            rows.append({"participant": P, "source_day": src, "target_day": tgt,
                         "gap_days": tgt - src, "auc_mean": float(np.mean(vals)),
                         "auc_sd": float(np.std(vals)), "repeats": len(vals),
                         "n_episodes": len(cache[tgt])})
        pd.DataFrame(rows).to_csv(ckpt, index=False)   # checkpoint every target day
        print(f"  target day {tgt} done  ({len(rows)} pairs so far)")

    d = pd.DataFrame(rows)
    same = d[d.gap_days == 0].set_index("target_day")["auc_mean"].to_dict()
    d["auc_same_day"] = d.target_day.map(same)
    d["delta"] = d.auc_mean - d.auc_same_day
    d.to_csv(ckpt, index=False)
    print(f"\nwrote {ckpt}  ({len(d)} day pairs)")

    fwd = d[d.gap_days > 0].dropna(subset=["delta"])
    if len(fwd) > 3:
        r, p = stats.spearmanr(fwd.gap_days, fwd.delta)
        print(f"\nforward pairs: {len(fwd)}   gap {fwd.gap_days.min()}-{fwd.gap_days.max()} days")
        print(f"  mean delta (AUC lost vs same-day fit): {fwd.delta.mean():+.4f}")
        print(f"  Spearman(gap, delta) = {r:+.3f}, p = {p:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
