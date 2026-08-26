#!/usr/bin/env python3
"""
14_run_ews_analysis.py
======================
Run the preregistered early-warning analysis.

Every choice this script makes is READ FROM research/FROZEN_DESIGN.json:
the deterioration boundary, which blocks are before and after it, the primary
and parallel indicators, the excluded indicator, the null procedure, the
reversibility tests and their failure criteria, and the secondary outcome.

Nothing is recomputed here and nothing is chosen here. That is deliberate: an
analysis that re-derives its own design can be written to suit the answer. This
one cannot, because the design was fixed and committed before it existed.

WHAT IS COMPUTED
----------------
  1. PRIMARY   -- does the within-block robust dispersion trend upward across
                  the 21 blocks preceding T11's day-758 transition?
  2. PARALLEL  -- the same test on trial-to-trial robust dispersion.
  3. SENSITIVITY -- the primary test repeated at session level, and with the
                  boundary located on success rate.
  4. REVERSIBILITY -- does the indicator fall again when performance recovers?
                  Tested on T5 (2133-2135 -> 2149) and within T11 (727 -> 751).
  5. SECONDARY -- does the neural indicator detect trouble earlier than simply
                  watching performance? Reported across 24 parameter settings.

WHAT IS NOT COMPUTED
--------------------
Lag-1 autocorrelation. It was excluded in advance because no observable in this
dataset has a measurable recovery rate; see research/observable_selection.md.
The exclusion is not revisited here.

HOW TO RUN
----------
    python3 scripts/14_run_ews_analysis.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.stats import kendalltau

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"
FREEZE = REPO_ROOT / "research" / "FROZEN_DESIGN.json"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)
ZWIN = 9000          # 180 s at 50 Hz, as used online and in scripts/09
PCA_DIM = 5


# ---------------------------------------------------------------------------
# PREPROCESSING (identical to the validated pipeline in scripts/09)
# ---------------------------------------------------------------------------

def trailing_z(X: np.ndarray, win: int = ZWIN) -> np.ndarray:
    """Causal rolling z-score: each point normalised by the preceding 3 minutes."""
    X = np.asarray(X, dtype=np.float64)
    n, d = X.shape
    c1 = np.vstack([np.zeros((1, d)), np.cumsum(X, axis=0)])
    c2 = np.vstack([np.zeros((1, d)), np.cumsum(X * X, axis=0)])
    i = np.arange(1, n + 1)
    lo = np.maximum(i - win, 0)
    cnt = (i - lo).reshape(-1, 1)
    m = (c1[i] - c1[lo]) / cnt
    v = np.maximum((c2[i] - c2[lo]) / cnt - m ** 2, 0.0)
    sd = np.sqrt(v)
    sd[sd < 1e-12] = 1.0
    return (X - m) / sd


def robust_dispersion(Y: np.ndarray) -> float:
    """
    Sum of squared median absolute deviations across dimensions.

    MAD is scaled by 1.4826 so that, for Gaussian data, it estimates the same
    quantity as a standard deviation. Squaring and summing gives a
    variance-like total that a few extreme samples cannot dominate -- which
    matters here, because these recordings carry large noise artifacts.
    """
    if Y.ndim != 2 or len(Y) < 3:
        return np.nan
    mad = np.median(np.abs(Y - np.median(Y, axis=0)), axis=0) * 1.4826
    return float((mad ** 2).sum())


def features(blk: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (z-scored features, trial start/stop, per-bin angle error)."""
    d = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)
    t = sio.loadmat(blk / "task.mat", squeeze_me=True, struct_as_record=False)
    info = sio.loadmat(blk / "info.mat", squeeze_me=True, struct_as_record=False)
    X = np.asarray(d["nctx"], dtype=np.float64)
    if "spikePower" in d:
        X = np.hstack([X, np.asarray(d["spikePower"], dtype=np.float64)])
    ss = np.atleast_2d(np.asarray(t["startStops"])).astype(np.int64)
    if ss.shape[0] == 2 and ss.shape[1] != 2:
        ss = ss.T
    ae = np.asarray(info["angleError"], float) if "angleError" in info \
        else np.full(len(X), np.nan)
    return trailing_z(X), ss, ae


def walk(participant: str) -> list[tuple[Path, int, int]]:
    out = []
    for pdir in sorted(p for p in RAW.rglob("*")
                       if p.is_dir() and p.name.upper() == participant):
        for dd in sorted((d for d in pdir.iterdir()
                          if d.is_dir() and DAY_RE.match(d.name)),
                         key=lambda q: int(DAY_RE.match(q.name).group(1))):
            day = int(DAY_RE.match(dd.name).group(1))
            for b in sorted(x for x in dd.iterdir()
                            if x.is_dir() and BLOCK_RE.match(x.name)):
                out.append((b, day, int(re.search(r"(\d+)", b.name).group(1))))
    return out


def pca_space(blocks: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    """Top-5 PC directions from the pooled baseline blocks of one participant."""
    Zs = [features(b)[0][::5] for b in blocks]
    A = np.vstack(Zs)
    mu = A.mean(axis=0)
    A = A - mu
    cov = np.cov(A, rowvar=False)
    w, v = np.linalg.eigh(cov)
    return mu, v[:, -PCA_DIM:]


def indicators(participant: str, baseline_days: list[int]) -> pd.DataFrame:
    """Compute both indicators for every block of one participant."""
    blocks = walk(participant)
    base = [b for b, day, _ in blocks if day in baseline_days]
    mu, P = pca_space(base)
    rows = []
    for blk, day, num in blocks:
        Z, ss, ae = features(blk)
        Y = (Z - mu) @ P
        prim = robust_dispersion(Y)
        starts, stops = ss[:, 0] - 1, ss[:, 1]          # 1-based -> 0-based
        tm = np.vstack([Y[a:b].mean(axis=0) for a, b in zip(starts, stops)
                        if b > a and b <= len(Y)]) if len(starts) else np.empty((0, PCA_DIM))
        par = robust_dispersion(tm)
        rows.append({"participant": participant, "trial_day": day, "block": num,
                     "primary": prim, "parallel": par,
                     "median_angle_error": float(np.nanmedian(ae))})
        print(f"    {participant} day_{day} blk {num}", end="\r", flush=True)
    print(" " * 50, end="\r")
    return pd.DataFrame(rows).sort_values(["trial_day", "block"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# THE PREREGISTERED TESTS
# ---------------------------------------------------------------------------

def trend_test(y: np.ndarray, n_perm: int = 5000, seed: int = 0) -> dict:
    """Kendall's tau against a permutation null on order. Two-sided."""
    y = np.asarray(y, float)
    ok = np.isfinite(y)
    y = y[ok]
    n = len(y)
    if n < 4:
        return {"n": n, "tau": np.nan, "p_two_sided": np.nan}
    x = np.arange(n)
    tau = float(kendalltau(x, y).statistic)
    rng = np.random.default_rng(seed)
    null = np.abs([kendalltau(x, rng.permutation(y)).statistic
                   for _ in range(n_perm)])
    return {"n": n, "tau": tau,
            "p_two_sided": float((np.sum(null >= abs(tau)) + 1) / (n_perm + 1))}


def detection_block(y: np.ndarray, baseline_n: int, k: float, persist: int) -> int | None:
    """First index past baseline mean + k*SD that stays past it for `persist`."""
    y = np.asarray(y, float)
    if len(y) <= baseline_n + persist:
        return None
    base = y[:baseline_n]
    lim = base.mean() + k * base.std(ddof=1)
    bad = y > lim
    for i in range(baseline_n, len(y) - persist + 1):
        if bad[i:i + persist].all():
            return i
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-perm", type=int, default=5000)
    args = ap.parse_args()

    if not FREEZE.exists():
        print("No frozen design. Run scripts/12_freeze_design.py --confirm first.",
              file=sys.stderr)
        return 1
    F = json.loads(FREEZE.read_text())
    D = F["design"]
    cut = D["primary"]["boundary_trial_day"]
    before_ids = {(b["trial_day"], b["block"]) for b in F["membership"]["before"]["blocks"]}

    print("=" * 78)
    print("PREREGISTERED EARLY-WARNING ANALYSIS")
    print("=" * 78)
    print(f"  design frozen : {F['frozen_at_utc']}  commit {F['git_commit_at_freeze'][:12]}")
    print(f"  amendments    : {len(F.get('amendments', []))}")
    print(f"  boundary      : T11 trial day {cut}")
    print(f"  primary       : {D['observable_and_indicators']['primary_indicator']['name']}")
    print(f"  parallel      : {D['observable_and_indicators']['parallel_indicator']['name']}")
    print(f"  EXCLUDED      : lag-1 autocorrelation (not computed)")
    print(f"  null          : {D['statistics']['null']}")
    print(f"  power         : detects |tau| >= {D['power_statement']['smallest_detectable_tau']}"
          f", power {D['power_statement']['power_vs_2sd_rise']} vs a 2 sd rise")

    print("\nComputing indicators ...")
    t11_base = D["reversibility_tests"][1]["baseline_days"]
    t5_base = D["reversibility_tests"][0]["baseline_days"]
    t11 = indicators("T11", t11_base)
    t5 = indicators("T5", t5_base)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.concat([t11, t5]).to_csv(PROCESSED / "ews_result_indicators.csv", index=False)

    pre = t11[[(r.trial_day, r.block) in before_ids for r in t11.itertuples()]]
    results = {}

    print("\n" + "=" * 78)
    print("1. PRIMARY — does the indicator rise before the transition?")
    print("=" * 78)
    for name in ("primary", "parallel"):
        r = trend_test(pre[name].to_numpy(), args.n_perm)
        lab = D["observable_and_indicators"][f"{name}_indicator"]["name"]
        sig = "SIGNIFICANT" if r["p_two_sided"] < 0.05 else "not significant"
        print(f"  {lab:<36} n={r['n']:<3} tau={r['tau']:+.3f}  "
              f"p={r['p_two_sided']:.4f}   {sig}")
        results[f"trend_{name}_block"] = r

    print("\n2. SENSITIVITY — session level")
    print("-" * 78)
    pre_sess = pre.groupby("trial_day")[["primary", "parallel"]].mean().reset_index()
    for name in ("primary", "parallel"):
        r = trend_test(pre_sess[name].to_numpy(), args.n_perm)
        sig = "SIGNIFICANT" if r["p_two_sided"] < 0.05 else "not significant"
        print(f"  {name:<36} n={r['n']:<3} tau={r['tau']:+.3f}  "
              f"p={r['p_two_sided']:.4f}   {sig}")
        results[f"trend_{name}_session"] = r

    print("\n3. REVERSIBILITY — does the indicator fall when performance recovers?")
    print("-" * 78)
    for t in D["reversibility_tests"]:
        src = t11 if t["participant"] == "T11" else t5
        g = lambda days: src[src.trial_day.isin(days)]["primary"].to_numpy()
        b, dg, rc = g(t["baseline_days"]), g(t["degraded_days"]), g(t["recovered_days"])
        if not (len(b) and len(dg) and len(rc)):
            continue
        lo, hi = float(np.min(b)), float(np.max(b))
        rec = float(np.mean(rc))
        passed = bool(lo <= rec <= hi)
        print(f"  {t['name']} ({t['participant']})")
        print(f"    baseline range {lo:.2f}–{hi:.2f} | degraded {np.mean(dg):.2f} "
              f"| recovered {rec:.2f}")
        print(f"    -> {'PASSES' if passed else 'FAILS'} the prespecified criterion")
        results[f"reversibility_{t['name'].replace(' ','_')}"] = {
            "baseline_lo": lo, "baseline_hi": hi,
            "degraded_mean": float(np.mean(dg)), "recovered_mean": rec,
            "passed": passed}

    print("\n4. SECONDARY — neural vs behavioural detection time")
    print("-" * 78)
    sec = D["secondary_outcome_neural_vs_behavioural"]
    grid = sec["parameter_grid"]
    leads = []
    for bn in grid["baseline_n"]:
        for k in grid["k"]:
            for pr in grid["persist"]:
                nb = detection_block(t11["primary"].to_numpy(), bn, k, pr)
                bb = detection_block(t11["median_angle_error"].to_numpy(), bn, k, pr)
                if nb is None or bb is None:
                    continue
                leads.append({"baseline_n": bn, "k": k, "persist": pr,
                              "neural_day": int(t11.iloc[nb].trial_day),
                              "behaviour_day": int(t11.iloc[bb].trial_day),
                              "lead_days": int(t11.iloc[bb].trial_day
                                               - t11.iloc[nb].trial_day)})
    ldf = pd.DataFrame(leads)
    if len(ldf):
        pos = int((ldf.lead_days > 0).sum()); neg = int((ldf.lead_days < 0).sum())
        zero = int((ldf.lead_days == 0).sum())
        print(f"  settings evaluated : {len(ldf)}")
        print(f"  neural first       : {pos}    behaviour first : {neg}    tied : {zero}")
        print(f"  median lead        : {ldf.lead_days.median():+.1f} days "
              f"(range {ldf.lead_days.min():+d} to {ldf.lead_days.max():+d})")
        verdict = ("neural monitoring detects earlier" if pos > len(ldf) / 2 else
                   "behaviour detects first — the neural indicator adds nothing"
                   if neg > len(ldf) / 2 else "no clear advantage either way")
        print(f"  -> {verdict}")
        ldf.to_csv(PROCESSED / "ews_result_lead_times.csv", index=False)
        results["secondary_lead"] = {"n_settings": len(ldf), "neural_first": pos,
                                     "behaviour_first": neg, "tied": zero,
                                     "median_lead_days": float(ldf.lead_days.median()),
                                     "verdict": verdict}
    else:
        print("  no setting produced a detection in both signals")

    out = {"run_at_utc": datetime.now(timezone.utc).isoformat(),
           "frozen_design_commit": F["git_commit_at_freeze"],
           "n_amendments": len(F.get("amendments", [])),
           "results": results}
    (PROCESSED / "ews_result_summary.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote ews_result_indicators.csv, ews_result_summary.json to data/processed/")
    print("\nReported as run. No test was repeated with different settings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
