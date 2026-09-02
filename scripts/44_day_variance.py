#!/usr/bin/env python3
"""
Is the day-to-day swing in monitor performance real, or an artefact?

The staleness study produced a same-day AUC per target day ranging 0.316 to
0.979 on T11 -- roughly fifty times the effect of the fit's age. Before that can
be called a finding it has to survive two much duller explanations:

  1. SAMPLING NOISE. Each day's AUC comes from ~40 episodes, split into a
     faulted and a healthy group. An AUC from groups that size has a standard
     error near 0.1 all on its own.

  2. FAULT MIX. The 40 episodes per day were drawn at random, so one day may
     have received more severe faults than another. A day of severe faults is
     easier regardless of anything about the day.

This script measures both, and compares the between-day variance against them.
A finding that does not survive is reported as not surviving.

Usage: python3 scripts/44_day_variance.py --participant T11|T5
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
N_BOOT = 2000


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

    # Reproduce the SAME episode draw the staleness run used, so the numbers
    # explain that run rather than a different one.
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
        g = guard.DecoderGuard().fit(H_fit)

        E, Hp, sev, sev_num, mode = [], [], [], [], []
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
                Hp.append(float(np.median(sc)))
            else:
                cw = crossing.get(e.episode_id, -1)
                if cw > ow and len(sc) >= cw:
                    E.append(float(np.median(sc[ow:cw])))
                    # BUG FIXED: this read e.severity, which is the numeric
                    # magnitude, and compared it to the string "high" -- always
                    # False, so the fault-mix control silently measured nothing
                    # on the first run. The categorical label is severity_label
                    # (benign / sub / crossing).
                    sev.append(str(e.severity_label)); mode.append(str(e.mode))
                    sev_num.append(float(e.severity))
        a = auc(E, Hp)
        if not np.isfinite(a):
            print(f"  day {d}: too few usable episodes ({len(E)} faulted, {len(Hp)} healthy)")
            continue

        # 1. sampling noise: bootstrap the two groups
        rb = np.random.default_rng(SEED + d)
        E_, H_ = np.array(E), np.array(Hp)
        bs = [auc(E_[rb.integers(0, len(E_), len(E_))],
                  H_[rb.integers(0, len(H_), len(H_))]) for _ in range(N_BOOT)]
        bs = np.array([b for b in bs if np.isfinite(b)])

        rows.append({"participant": P, "day": d, "auc": round(a, 4),
                     "n_faulted": len(E), "n_healthy": len(Hp),
                     "boot_se": round(float(np.std(bs)), 4),
                     "ci_lo": round(float(np.percentile(bs, 2.5)), 4),
                     "ci_hi": round(float(np.percentile(bs, 97.5)), 4),
                     # 2. fault mix actually drawn for this day
                     "frac_crossing": round(float(np.mean([s == "crossing" for s in sev])), 3),
                     "frac_benign": round(float(np.mean([s == "benign" for s in sev])), 3),
                     "mean_severity": round(float(np.mean(sev_num)), 4) if sev_num else None,
                     "n_modes": len(set(mode))})
        print(f"  day {d}: AUC {a:.3f}  [{rows[-1]['ci_lo']:.3f}, {rows[-1]['ci_hi']:.3f}]"
              f"  se {rows[-1]['boot_se']:.3f}  n={len(E)}/{len(Hp)}"
              f"  crossing-sev {rows[-1]['frac_crossing']:.2f}")

    d = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    d.to_csv(OUT / f"day_variance{sfx}.csv", index=False)

    obs_sd = float(d.auc.std(ddof=1))
    mean_se = float(np.sqrt((d.boot_se ** 2).mean()))
    excess = obs_sd ** 2 - mean_se ** 2
    summ = {
        "participant": P, "n_days": len(d),
        "auc_min": float(d.auc.min()), "auc_max": float(d.auc.max()),
        "observed_sd_across_days": round(obs_sd, 4),
        "mean_sampling_se_within_day": round(mean_se, 4),
        "excess_sd_after_removing_sampling":
            round(float(np.sqrt(excess)) if excess > 0 else 0.0, 4),
        "variance_share_from_sampling": round(min(1.0, mean_se ** 2 / obs_sd ** 2), 3),
    }
    # Cochran's Q -- the standard heterogeneity test. Under the null that every
    # day shares one true AUC, Q ~ chi-square with n-1 df, and I^2 is the share
    # of the spread not attributable to within-day sampling error. This is the
    # test the eyeball variance decomposition above only gestures at.
    if len(d) > 2:
        w = 1.0 / (d.boot_se.values ** 2)
        pooled = float((w * d.auc.values).sum() / w.sum())
        Q = float((w * (d.auc.values - pooled) ** 2).sum())
        dfree = len(d) - 1
        summ["cochran_Q"] = round(Q, 2)
        summ["cochran_df"] = dfree
        summ["cochran_p"] = float(f"{stats.chi2.sf(Q, dfree):.3g}")
        summ["I_squared"] = round(max(0.0, (Q - dfree) / Q), 3) if Q > 0 else 0.0
        summ["inverse_variance_pooled_auc"] = round(pooled, 4)

    if len(d) > 3:
        for col in ["frac_crossing", "frac_benign", "n_faulted"]:
            if d[col].nunique() < 2:
                summ[f"spearman_{col}_vs_auc"] = "constant, not defined"
                continue
            r, pv = stats.spearmanr(d[col], d.auc)
            summ[f"spearman_{col}_vs_auc"] = round(float(r), 3)
            summ[f"spearman_{col}_p"] = round(float(pv), 4)
    print("\n" + json.dumps(summ, indent=2))
    (OUT / f"day_variance_summary{sfx}.json").write_text(json.dumps(summ, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
