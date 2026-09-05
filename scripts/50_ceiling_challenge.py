#!/usr/bin/env python3
"""
Does the P5 result survive a ceiling effect in the ground truth?

Predictions committed in research/CEILING_CHALLENGE_NOTE.md before running,
including that I EXPECT to find the confound.

THE CHANNEL
-----------
An episode crosses when smoothed decoder error exceeds its own pre-onset baseline
plus 10 degrees. Measured chance on T11 is 90.7 deg; day 783's baseline is
89.3 deg. A fault there has ~1.4 deg of headroom before the metric saturates. If
faults do less measurable damage on high-error days, the ground truth is weaker
there and any detector scores lower -- which would reframe P5 from a statement
about the monitor into a statement about the measuring instrument.

WHAT IS MEASURED
----------------
For every faulted episode, the decoder error is recomputed window by window on
the injected data, exactly as the harness does it, and

    achieved damage = median(post-onset error) - median(pre-onset error)

using the same pre-onset baseline the crossing rule uses. Aggregated per day by
median, then correlated against decoder error and monitor AUC, and finally
partialled out of the P5 relationship.

Usage: python3 scripts/50_ceiling_challenge.py --participant T11|T5
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
EPISODES_PER_DAY = 40
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def partial_spearman(d: pd.DataFrame, x: str, y: str, z: str):
    """Spearman partial correlation = Pearson partial on the ranks."""
    ok = d[[x, y, z]].notna().all(axis=1)
    if ok.sum() < 5:
        return None, None, None
    R = d.loc[ok, [x, y, z]].rank()
    C = np.corrcoef(R.T.values)
    inv = np.linalg.inv(C)
    r = -inv[0, 1] / np.sqrt(inv[0, 0] * inv[1, 1])
    dfree = int(ok.sum()) - 3
    t = r * np.sqrt(dfree / max(1e-12, 1 - r ** 2))
    return float(r), float(2 * stats.t.sf(abs(t), dfree)), dfree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    harness = _load("harness", "20_evaluation_harness.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    dec_path, _ = rd.decoder_paths(P)
    dz = np.load(dec_path)
    dec = (dz["W"], dz["mean"], dz["std"])

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    scores = OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv"
    sc = pd.read_csv(scores)
    sc = sc[sc.detector == "decoder_guard"]
    crossed = dict(zip(sc.episode_id, sc.crossed))

    rng = np.random.default_rng(SEED)
    by_day: dict[int, list] = {}
    for e in episodes:
        if e.block_id in ds.neural:
            by_day.setdefault(day_of(e.block_id), []).append(e)

    # Trial geometry, exactly as the harness builds it, so the error numbers are
    # the same quantity the crossing rule was applied to.
    rows = []
    for day, eps in sorted(by_day.items()):
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        damages, baselines, excursions, spreads = [], [], [], []
        for e in eps:
            if not crossed.get(e.episode_id, False):
                continue                      # damage is only defined for faults
            bid = e.block_id
            X = ds.neural[bid]
            kin = ds.kinematics.get(bid, {})
            if "cursorPos" not in kin:
                continue
            unit, ok_dir = rd.intended_direction(kin)
            ok = ok_dir & rd.in_trial_mask(ds.trials, bid, X.shape[0])
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12:
                continue
            Y, _ = inj.apply_episode(X, e)
            perf = harness.window_performance(Y, starts, WINDOW_BINS, ok, unit, dec)
            ow = int(np.searchsorted(starts, e.onset_bin))
            pre, post = perf[:ow], perf[ow:]
            pre = pre[np.isfinite(pre)]; post = post[np.isfinite(post)]
            if len(pre) < 3 or len(post) < 3:
                continue
            damages.append(float(np.median(post) - np.median(pre)))
            baselines.append(float(np.median(pre)))

            # SPURIOUS-CROSSING RATE, measured where no fault exists at all.
            # The crossing rule fires on the first SMOOTHED window above
            # base + 10 deg. Apply exactly that rule to the PRE-onset windows,
            # which are untouched by definition: any excursion there is the
            # threshold being cleared by noise. Only 1-2 uninjected control
            # episodes exist per day, far too few to estimate this from, so it
            # is measured on every episode's own clean prefix instead.
            sm_pre = (pd.Series(perf[:ow])
                      .rolling(harness.PERF_SMOOTH, min_periods=2)
                      .median().to_numpy())
            sm_pre = sm_pre[np.isfinite(sm_pre)]
            if len(sm_pre) >= 3:
                b = float(np.median(pre))
                excursions.append(float((sm_pre > b + harness.THRESHOLD_DEG).mean()))
                spreads.append(float(np.median(np.abs(sm_pre - b)) * 1.4826))
        if len(damages) < 5:
            print(f"  day {day}: only {len(damages)} usable faulted episodes, skipped")
            continue
        rows.append({"day": day, "n_faulted": len(damages),
                     "achieved_damage_deg": round(float(np.median(damages)), 3),
                     "pre_onset_baseline_deg": round(float(np.median(baselines)), 3),
                     "spurious_crossing_rate": round(float(np.mean(excursions)), 4)
                         if excursions else np.nan,
                     "pre_onset_spread_deg": round(float(np.median(spreads)), 3)
                         if spreads else np.nan})
        print(f"  day {day}: damage {rows[-1]['achieved_damage_deg']:+.2f} deg"
              f"  baseline {rows[-1]['pre_onset_baseline_deg']:.1f} deg"
              f"  spurious {rows[-1]['spurious_crossing_rate']:.3f}"
              f"  n={len(damages)}")

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    known = pd.read_csv(OUT / f"day_predictors{sfx}.csv")[["day", "auc", "P5_decoder_error"]]
    M = D.merge(known, on="day", how="inner")
    M.to_csv(OUT / f"ceiling_challenge{sfx}.csv", index=False)

    res = {"participant": P, "n_days": int(len(M))}
    for a, b, key in [("achieved_damage_deg", "P5_decoder_error", "damage_vs_decoder_error"),
                      ("achieved_damage_deg", "auc", "damage_vs_monitor_auc"),
                      ("pre_onset_baseline_deg", "achieved_damage_deg",
                       "baseline_vs_damage"),
                      ("spurious_crossing_rate", "P5_decoder_error",
                       "spurious_vs_decoder_error"),
                      ("spurious_crossing_rate", "auc", "spurious_vs_monitor_auc"),
                      ("pre_onset_spread_deg", "auc", "trace_noise_vs_monitor_auc")]:
        ok = M[a].notna() & M[b].notna()
        if ok.sum() >= 4:
            r, p = stats.spearmanr(M.loc[ok, a], M.loc[ok, b])
            res[key] = {"rho": round(float(r), 3), "p": round(float(p), 4),
                        "n": int(ok.sum())}

    raw_r, raw_p = stats.spearmanr(M.P5_decoder_error, M.auc)
    res["P5_raw"] = {"rho": round(float(raw_r), 3), "p": round(float(raw_p), 4)}
    for ctrl, key in [("achieved_damage_deg", "P5_controlling_for_damage"),
                      ("spurious_crossing_rate", "P5_controlling_for_spurious"),
                      ("pre_onset_spread_deg", "P5_controlling_for_trace_noise")]:
        pr, pp, pdf = partial_spearman(M, "P5_decoder_error", "auc", ctrl)
        if pr is not None:
            res[key] = {"rho": round(pr, 3), "p": round(pp, 4), "df": pdf}
    k = res.get("P5_controlling_for_damage", {})
    k2 = res.get("P5_controlling_for_spurious", {})
    res["P5_survives_the_challenge"] = bool(
        abs(k.get("rho", 0)) > 0.5 and k.get("p", 1) < 0.05
        and abs(k2.get("rho", 0)) > 0.5 and k2.get("p", 1) < 0.05)

    print("\n" + json.dumps(res, indent=2))
    (OUT / f"ceiling_challenge{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
