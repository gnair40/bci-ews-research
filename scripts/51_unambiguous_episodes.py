#!/usr/bin/env python3
"""
Is the day effect failed detection, or degraded labels?

Predictions committed in the addendum to research/CEILING_CHALLENGE_NOTE.md
before running: weaken substantially but not vanish, and the worst days lose
most of their episodes.

THE TEST
--------
Keep only faulted episodes where the fault demonstrably did real damage --
achieved damage >= 10 deg, measured as the median over post-onset windows minus
the episode's own pre-onset baseline. On those the ground truth is unambiguous
whatever the day's noise level. Recompute per-day AUC and re-run the
decoder-error correlation on what remains.

The 10 deg threshold is the crossing rule's own threshold and is NOT adjustable
after seeing how many days survive -- a day with too few unambiguous episodes is
reported as unscoreable, which is itself the result for that day.

Usage: python3 scripts/51_unambiguous_episodes.py --participant T11|T5
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
DAMAGE_THRESHOLD_DEG = 10.0        # the crossing rule's own threshold
MIN_PER_GROUP = 5
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def auc(E, H):
    if len(E) < MIN_PER_GROUP or len(H) < MIN_PER_GROUP:
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
    harness = _load("harness", "20_evaluation_harness.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    dec_path, _ = rd.decoder_paths(P)
    dz = np.load(dec_path)
    dec = (dz["W"], dz["mean"], dz["std"])

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

    sc = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    sc = sc[sc.detector == "decoder_guard"]
    crossed = dict(zip(sc.episode_id, sc.crossed))
    crossing = dict(zip(sc.episode_id, sc.crossing_w))

    rng = np.random.default_rng(SEED)
    by_day: dict[int, list] = {}
    for e in episodes:
        if e.block_id in ds.neural:
            by_day.setdefault(day_of(e.block_id), []).append(e)

    rows = []
    for day in sorted(by_day):
        if day not in healthy or len(healthy[day]) < FIT_WINDOWS:
            continue
        eps = by_day[day]
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        r = np.random.default_rng(SEED + day)
        g = guard.DecoderGuard().fit(
            healthy[day][r.choice(len(healthy[day]), FIT_WINDOWS, replace=False)])

        E_all, E_unamb, H = [], [], []
        for e in eps:
            bid = e.block_id
            X = ds.neural[bid]
            kin = ds.kinematics.get(bid, {})
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12 or "cursorPos" not in kin:
                continue
            Y, _ = inj.apply_episode(X, e)
            ow = int(np.searchsorted(starts, e.onset_bin))
            if ow < 6:
                continue
            F = det.window_features(Y, starts, WINDOW_BINS)
            g.recenter(F[:ow])
            s = g.score(F)

            if not crossed.get(e.episode_id, False):
                H.append(float(np.median(s)))
                continue
            cw = crossing.get(e.episode_id, -1)
            if not (cw > ow and len(s) >= cw):
                continue
            val = float(np.median(s[ow:cw]))
            E_all.append(val)

            unit, ok_dir = rd.intended_direction(kin)
            ok = ok_dir & rd.in_trial_mask(ds.trials, bid, X.shape[0])
            perf = harness.window_performance(Y, starts, WINDOW_BINS, ok, unit, dec)
            pre, post = perf[:ow], perf[ow:]
            pre = pre[np.isfinite(pre)]; post = post[np.isfinite(post)]
            if len(pre) < 3 or len(post) < 3:
                continue
            if float(np.median(post) - np.median(pre)) >= DAMAGE_THRESHOLD_DEG:
                E_unamb.append(val)

        a_all, a_un = auc(E_all, H), auc(E_unamb, H)
        rows.append({"day": day, "n_healthy": len(H),
                     "n_faulted_all": len(E_all), "n_faulted_unambiguous": len(E_unamb),
                     "retained_fraction": round(len(E_unamb) / max(1, len(E_all)), 3),
                     "auc_all": round(a_all, 4) if np.isfinite(a_all) else np.nan,
                     "auc_unambiguous": round(a_un, 4) if np.isfinite(a_un) else np.nan})
        note = "" if np.isfinite(a_un) else "   UNSCOREABLE (too few unambiguous)"
        print(f"  day {day}: {len(E_unamb):>2}/{len(E_all):>2} retained"
              f"   AUC all {a_all:.3f}"
              f"   AUC unambiguous {a_un:.3f}{note}"
              if np.isfinite(a_un) else
              f"  day {day}: {len(E_unamb):>2}/{len(E_all):>2} retained"
              f"   AUC all {a_all:.3f}{note}")

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    known = pd.read_csv(OUT / f"day_predictors{sfx}.csv")[["day", "P5_decoder_error"]]
    M = D.merge(known, on="day", how="inner")
    M.to_csv(OUT / f"unambiguous{sfx}.csv", index=False)

    res = {"participant": P, "n_days_total": int(len(M)),
           "n_days_scoreable": int(M.auc_unambiguous.notna().sum()),
           "damage_threshold_deg": DAMAGE_THRESHOLD_DEG}
    for col, key in [("auc_all", "P5_all_episodes"),
                     ("auc_unambiguous", "P5_unambiguous_only")]:
        ok = M[col].notna() & M.P5_decoder_error.notna()
        if ok.sum() >= 4:
            r, p = stats.spearmanr(M.loc[ok, col], M.loc[ok, "P5_decoder_error"])
            res[key] = {"rho": round(float(r), 3), "p": round(float(p), 4),
                        "n_days": int(ok.sum())}
    ok = M.retained_fraction.notna() & M.P5_decoder_error.notna()
    if ok.sum() >= 4:
        r, p = stats.spearmanr(M.loc[ok, "retained_fraction"], M.loc[ok, "P5_decoder_error"])
        res["retained_fraction_vs_decoder_error"] = {"rho": round(float(r), 3),
                                                     "p": round(float(p), 4)}
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"unambiguous{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
