#!/usr/bin/env python3
"""
11_define_deterioration.py
==========================
Locate the onset of performance deterioration using PERFORMANCE DATA ONLY.

WHAT THIS SCRIPT IS AND IS NOT
------------------------------
This script exists to answer one question before the main analysis begins:
**when does deterioration start?**

It uses only behavioural performance -- angle error and success rate. It never
touches the neural features, and it never computes an early-warning indicator.
That separation is the entire point. If the event were defined using the same
signal the early-warning indicator is built from, the analysis would be circular:
we would be asking whether a signal predicts an event that was defined by that
signal.

It also is not a menu to shop through. The methods below are applied to see
whether they AGREE. Agreement is the defence against arbitrariness: if
independent procedures converge on the same boundary, the change point is a
property of the data rather than a choice the researcher made. Disagreement is
equally informative and must be reported, not hidden.

THE METHODS, IN PLAIN LANGUAGE
------------------------------
1. LEAST-SQUARES CHANGE POINT
   Try every possible place to split the series in two. For each split, measure
   how much the values scatter around their own segment's average. The best
   split is the one leaving the least scatter -- i.e. the point where the series
   most cleanly separates into "before" and "after". No tuning parameters.

2. CUSUM (cumulative sum)
   Walk along the series adding up how far each value sits above or below the
   overall average. While values are near average the running total stays flat;
   once they are consistently above it, the total climbs. The change point is
   where that running total is furthest from zero. Also parameter-free.

3. RANK-BASED SCAN (Mann-Whitney)
   Like method 1, but comparing ranks instead of values, so a single wild outlier
   cannot drag the answer. Robust, at the cost of ignoring magnitude.

4. BASELINE-ANCHORED THRESHOLD WITH PERSISTENCE
   Define "normal" from the first few blocks only. Deterioration begins at the
   first block that is worse than normal by a stated margin AND stays worse for a
   stated number of consecutive blocks. Its great virtue: the rule can be written
   down having seen ONLY the early data, so it cannot be tuned to the collapse.

HOW SIGNIFICANCE IS TESTED
--------------------------
A change point can always be found, even in pure noise -- some split is always
best. To check whether one really exists, the values are shuffled many times and
the best split re-found each time. If the real split separates the data better
than nearly all shuffles, a change is present.

HOW TO RUN
----------
    python3 scripts/11_define_deterioration.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from math import comb

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = REPO_ROOT / "data" / "processed"

MIN_SEG = 3          # a segment must contain at least this many observations
N_PERM = 5000        # shuffles used to test whether a change point exists


# ---------------------------------------------------------------------------
# CANDIDATE METHODS
# ---------------------------------------------------------------------------

def cp_least_squares(y: np.ndarray, min_seg: int = MIN_SEG) -> tuple[int, float]:
    """
    Method 1. Split that minimises total within-segment squared error.

    Returns (index of first point AFTER the change, cost). The cost is the
    leftover scatter; lower means a cleaner separation.
    """
    n = len(y)
    best, best_cost = None, np.inf
    for k in range(min_seg, n - min_seg + 1):
        a, b = y[:k], y[k:]
        cost = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if cost < best_cost:
            best, best_cost = k, cost
    return best, float(best_cost)


def cp_cusum(y: np.ndarray, min_seg: int = MIN_SEG) -> int:
    """Method 2. Point where the running sum of deviations is furthest from 0."""
    s = np.cumsum(y - y.mean())
    inner = np.arange(min_seg, len(y) - min_seg + 1)
    if len(inner) == 0:
        return None
    return int(inner[np.argmax(np.abs(s[inner - 1]))])


def cp_rank_scan(y: np.ndarray, min_seg: int = MIN_SEG) -> int:
    """Method 3. Split maximising the rank-based separation of the two halves."""
    n = len(y)
    best, best_z = None, -np.inf
    for k in range(min_seg, n - min_seg + 1):
        try:
            u = mannwhitneyu(y[:k], y[k:], alternative="two-sided")
        except ValueError:
            continue
        n1, n2 = k, n - k
        mu = n1 * n2 / 2
        sd = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        z = abs((u.statistic - mu) / sd) if sd > 0 else 0
        if z > best_z:
            best, best_z = k, z
    return best


def cp_baseline_threshold(y: np.ndarray, baseline_n: int, n_sd: float,
                          persist: int, worse_is_higher: bool) -> int | None:
    """
    Method 4. First point exceeding a baseline-derived limit and STAYING beyond it.

    `baseline_n`, `n_sd` and `persist` must be fixed in advance. The limit is
    computed from the first `baseline_n` observations only, so the rule can be
    written down without having seen the deterioration.
    """
    if len(y) <= baseline_n + persist:
        return None
    base = y[:baseline_n]
    limit = (base.mean() + n_sd * base.std(ddof=1)) if worse_is_higher \
        else (base.mean() - n_sd * base.std(ddof=1))
    bad = (y > limit) if worse_is_higher else (y < limit)
    for i in range(baseline_n, len(y) - persist + 1):
        if bad[i:i + persist].all():
            return i
    return None


def permutation_p(y: np.ndarray, observed_cost: float, min_seg: int = MIN_SEG,
                  n_perm: int = N_PERM, seed: int = 0) -> float:
    """
    Does a change point exist at all?

    Shuffling destroys any time ordering. If the real series separates far better
    than shuffled versions of the same values, the ordering carries a real change.
    """
    rng = np.random.default_rng(seed)
    better = 0
    for _ in range(n_perm):
        _, c = cp_least_squares(rng.permutation(y), min_seg)
        if c <= observed_cost:
            better += 1
    return (better + 1) / (n_perm + 1)


# ---------------------------------------------------------------------------
# APPLYING THEM
# ---------------------------------------------------------------------------

def series_for(trials: pd.DataFrame, blocks: pd.DataFrame, part: str,
               level: str) -> pd.DataFrame:
    """Build the ordered performance series at block or session level."""
    t = trials[(trials.participant == part) & (trials.cohort == "main")]
    b = blocks[(blocks.participant == part) & (blocks.cohort == "main")]
    if level == "block":
        ae = (t.groupby(["trial_day", "block"])["angle_error_deg"]
                .median().rename("angle_error"))
        pc = (b.set_index(["trial_day", "block"])["percent_correct"]
                .rename("success"))
        df = pd.concat([ae, pc], axis=1).reset_index()
        df = df.sort_values(["trial_day", "block"]).reset_index(drop=True)
    else:
        ae = t.groupby("trial_day")["angle_error_deg"].median().rename("angle_error")
        pc = b.groupby("trial_day")["percent_correct"].mean().rename("success")
        df = pd.concat([ae, pc], axis=1).reset_index()
        df = df.sort_values("trial_day").reset_index(drop=True)
    return df.dropna(subset=["angle_error", "success"])


def label_of(df: pd.DataFrame, idx: int | None, level: str) -> str:
    if idx is None or idx >= len(df):
        return "none found"
    r = df.iloc[idx]
    return (f"day {int(r.trial_day)} blk {int(r.block)}"
            if level == "block" else f"day {int(r.trial_day)}")


def analyse(df: pd.DataFrame, part: str, level: str, args) -> list[dict]:
    rows = []
    for var, worse_high in (("angle_error", True), ("success", False)):
        y = df[var].to_numpy(float)
        if len(y) < 2 * MIN_SEG:
            print(f"    {var:<12s} too few points ({len(y)}) — skipped")
            continue
        k_ls, cost = cp_least_squares(y)
        p = permutation_p(y, cost, n_perm=args.n_perm)
        k_cs = cp_cusum(y)
        k_rk = cp_rank_scan(y)
        k_th = cp_baseline_threshold(y, args.baseline_n, args.n_sd,
                                     args.persist, worse_high)
        for name, k in (("least-squares", k_ls), ("CUSUM", k_cs),
                        ("rank scan", k_rk), ("baseline+persist", k_th)):
            rows.append({"participant": part, "level": level, "variable": var,
                         "method": name, "index": k,
                         "location": label_of(df, k, level),
                         "n_before": k if k is not None else None,
                         "n_after": (len(y) - k) if k is not None else None,
                         "change_point_p": round(p, 4) if name == "least-squares" else None})
        agree = len({k for k in (k_ls, k_cs, k_rk) if k is not None})
        print(f"    {var:<12s} least-sq {label_of(df,k_ls,level):<18s} "
              f"CUSUM {label_of(df,k_cs,level):<18s} rank {label_of(df,k_rk,level):<18s} "
              f"thresh {label_of(df,k_th,level):<18s}")
        print(f"    {'':12s} change point exists? p = {p:.4f}   "
              f"{'ALL THREE DATA-DRIVEN METHODS AGREE' if agree == 1 else f'{agree} distinct locations'}")
    return rows


# ---------------------------------------------------------------------------
# HOW WELL DETERMINED IS A THRESHOLD-BASED ONSET?
# ---------------------------------------------------------------------------

def threshold_sensitivity(df: pd.DataFrame, level: str,
                          baselines=(4, 6, 8), sds=(1.5, 2.0, 2.5, 3.0),
                          persists=(2, 3)) -> pd.DataFrame:
    """
    Re-run the baseline+persistence rule across every combination of its
    parameters, and see how much the answer moves.

    Why this matters: that rule has three numbers in it that someone has to
    choose (how much history counts as "normal", how far past normal counts as
    degraded, how long it must stay there). If the onset date barely moves as
    those change, the date is a property of the data. If it swings wildly, the
    date is really a property of the choice -- and should not be used to define
    the event a whole study is built on.
    """
    y = df["angle_error"].to_numpy(float)
    rows = []
    for bn in baselines:
        for sd in sds:
            for pr in persists:
                k = cp_baseline_threshold(y, bn, sd, pr, True)
                rows.append({"baseline_n": bn, "n_sd": sd, "persist": pr,
                             "index": k, "onset": label_of(df, k, level)})
    return pd.DataFrame(rows)


def session_vs_baseline(df: pd.DataFrame, n_baseline: int = 8) -> pd.DataFrame:
    """
    Test each session against the early blocks.

    IMPORTANT LIMITATION, reported alongside the numbers: with only 1-2 blocks
    per session the smallest attainable two-sided p-value is about 0.044, so a
    p of 0.044 means "as separated as this test can show" rather than "strong
    evidence". Identical p-values across sessions are the signature of that
    floor, not of equally strong effects.
    """
    from scipy.stats import mannwhitneyu
    y = df["angle_error"].to_numpy(float)
    early = y[:n_baseline]
    rows = []
    for day, g in df.groupby("trial_day"):
        v = y[(df.trial_day == day).to_numpy()]
        if len(v) == 0 or day in df.trial_day.unique()[:3]:
            continue
        try:
            u = mannwhitneyu(early, v, alternative="two-sided")
        except ValueError:
            continue
        rows.append({"trial_day": int(day), "n_blocks": len(v),
                     "mean_ae": round(float(np.mean(v)), 1),
                     "baseline_mean_ae": round(float(np.mean(early)), 1),
                     "p": round(float(u.pvalue), 4)})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_floor_for_this_n"] = out["n_blocks"].map(
            lambda n2: round(2 / comb(n_baseline + n2, n2), 4)
            if n2 > 0 else np.nan)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline-n", type=int, default=6,
                    help="observations defining 'normal' for method 4")
    ap.add_argument("--n-sd", type=float, default=2.0,
                    help="how many baseline SDs count as degraded")
    ap.add_argument("--persist", type=int, default=2,
                    help="consecutive degraded observations required")
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    ap.add_argument("--sensitivity", action="store_true",
                    help="also report how much a threshold-based onset moves "
                         "when its parameters change")
    args = ap.parse_args()

    tp, bp = PROCESSED / "trials.csv", PROCESSED / "blocks.csv"
    if not (tp.exists() and bp.exists()):
        print("Run scripts/04_explore_dataset.py first.", file=sys.stderr)
        return 1
    trials, blocks = pd.read_csv(tp), pd.read_csv(bp)

    print("=" * 78)
    print("LOCATING DETERIORATION ONSET — PERFORMANCE DATA ONLY")
    print("=" * 78)
    print("No neural features are read. No early-warning indicator is computed.")
    print(f"Method 4 parameters, fixed in advance: baseline = first "
          f"{args.baseline_n} observations, threshold = {args.n_sd} SD, "
          f"persistence = {args.persist}\n")

    rows = []
    for part in ("T11", "T5"):
        for level in ("block", "session"):
            df = series_for(trials, blocks, part, level)
            print(f"  {part} — {level} level  ({len(df)} observations)")
            rows += analyse(df, part, level, args)
            print()

    out = pd.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED / "deterioration_candidates.csv", index=False)

    if args.sensitivity:
        print("=" * 78)
        print("HOW WELL DETERMINED IS A THRESHOLD-BASED ONSET? (T11, block level)")
        print("=" * 78)
        df11 = series_for(trials, blocks, "T11", "block")
        sens = threshold_sensitivity(df11, "block")
        counts = sens["onset"].value_counts()
        print(f"\n{len(sens)} parameter combinations tried "
              f"(baseline x SD x persistence):\n")
        for lab, c in counts.items():
            print(f"   {lab:<22} {c:>2}/{len(sens)}   {'#' * int(c)}")
        spread = sens["index"].dropna()
        if len(spread) > 1:
            lo, hi = int(spread.min()), int(spread.max())
            d_lo = int(df11.iloc[lo].trial_day); d_hi = int(df11.iloc[hi].trial_day)
            print(f"\n   Onset ranges from trial day {d_lo} to {d_hi} "
                  f"— a spread of {d_hi - d_lo} days.")
            print("   A date that moves this much with its own parameters is a")
            print("   property of the choice, not of the data.")
        sens.to_csv(PROCESSED / "threshold_sensitivity.csv", index=False)

        print("\n" + "-" * 78)
        print("EACH SESSION AGAINST THE EARLY BLOCKS (T11)")
        print("-" * 78)
        sv = session_vs_baseline(df11)
        print(sv.to_string(index=False))
        print("\n   p_floor_for_this_n is the SMALLEST p-value the test could")
        print("   possibly return at that sample size. Where p equals the floor,")
        print("   the result means 'completely separated', which is easy with 2")
        print("   blocks — it is not strong evidence.")
        sv.to_csv(PROCESSED / "session_vs_baseline.csv", index=False)
        print()
    print("=" * 78)
    print(f"Wrote {(PROCESSED / 'deterioration_candidates.csv').relative_to(REPO_ROOT)}")
    print("""
This script does NOT choose a definition. It reports where each candidate lands
so that agreement between independent methods can be judged. The choice, and the
freezing of it, belongs in research/deterioration_definition.md and must happen
before any early-warning indicator is computed.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
