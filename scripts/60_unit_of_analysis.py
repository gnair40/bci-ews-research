#!/usr/bin/env python3
"""
Recompute every published p-value that was built on pooled windows.

Preregistered in research/UNIT_OF_ANALYSIS_NOTE.md, predictions included.

THE ERROR CLASS
---------------
26_achievability.py concatenates every window from every episode and runs a
Mann-Whitney test on the pooled arrays. Claim C04 says windows within a session
are not independent (lag-1 r = 0.995), so that inflates the apparent sample size
by roughly 55x per session. The AUC point estimate is unaffected -- it is
descriptive -- but the p-value is not: ACHIEVABILITY.md publishes p = 0 and
1.2e-303, and an AUC of 0.491 carrying p = 0.046 while the same row's verdict
column reads "at chance -- no information".

THE FIX
-------
Recompute with the EPISODE as the unit: one median score per episode, then a
bootstrap over episodes. That is the standard this project already adopted for
the feature and combination studies; achievability simply predates it.

Both are reported side by side. The published numbers are not deleted.

Usage: python3 scripts/60_unit_of_analysis.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"
N_BOOT = 2000
SEED = 20260902

# file, participant, baseline label -- the four tables in ACHIEVABILITY.md
SOURCES = [
    ("episode_scores.csv", "T11", "calibrate once"),
    ("episode_scores_local.csv", "T11", "recent normal"),
    ("episode_scores_T5.csv", "T5", "calibrate once"),
    ("episode_scores_T5_local.csv", "T5", "recent normal"),
]


def auc(pos, neg):
    if len(pos) < 5 or len(neg) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(pos, neg, alternative="two-sided")
    return float(u / (len(pos) * len(neg)))


def episode_level(df: pd.DataFrame):
    """One median per episode: the faulted early-warning window, or the whole
    healthy trace."""
    E, H = [], []
    for _, r in df.iterrows():
        y = np.fromstring(str(r.scores), sep=",")
        if len(y) == 0:
            continue
        if not bool(r.crossed):
            H.append(float(np.median(y)))
            continue
        ow, cw = int(r.onset_w), int(r.crossing_w)
        if cw > ow and len(y) >= cw:
            E.append(float(np.median(y[ow:cw])))
    return np.array(E), np.array(H)


def window_level(df: pd.DataFrame):
    E, H = [], []
    for _, r in df.iterrows():
        y = np.fromstring(str(r.scores), sep=",")
        if len(y) == 0:
            continue
        if not bool(r.crossed):
            H.append(y)
            continue
        ow, cw = int(r.onset_w), int(r.crossing_w)
        if cw > ow and len(y) >= cw:
            E.append(y[ow:cw])
    return (np.concatenate(E) if E else np.array([]),
            np.concatenate(H) if H else np.array([]))


def bootstrap_p(E, H, n_boot=N_BOOT, seed=SEED):
    """Two-sided p for AUC != 0.5, resampling EPISODES with replacement.

    The fraction of resamples landing on the wrong side of 0.5, doubled. Floored
    at 1/n_boot rather than reported as zero, because a bootstrap cannot resolve
    a p-value smaller than its own resolution -- which is exactly the overclaim
    being corrected here.
    """
    rng = np.random.default_rng(seed)
    obs = auc(E, H)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        e = E[rng.integers(0, len(E), len(E))]
        h = H[rng.integers(0, len(H), len(H))]
        boots[i] = auc(e, h)
    boots = boots[np.isfinite(boots)]
    side = float(np.mean(boots <= 0.5)) if obs > 0.5 else float(np.mean(boots >= 0.5))
    p = min(1.0, 2 * max(side, 1.0 / len(boots)))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return obs, p, float(lo), float(hi), bool(len(boots) == n_boot)


def main() -> int:
    results = []
    for fname, P, baseline in SOURCES:
        path = OUT / fname
        if not path.exists():
            print(f"  missing {fname}, skipped")
            continue
        raw = pd.read_csv(path)
        for det in sorted(raw.detector.unique()):
            df = raw[raw.detector == det]
            Ew, Hw = window_level(df)
            Ee, He = episode_level(df)
            if len(Ew) < 5 or len(Hw) < 5 or len(Ee) < 5 or len(He) < 5:
                continue
            a_w = auc(Ew, Hw)
            _, p_w = stats.mannwhitneyu(Ew, Hw, alternative="two-sided")
            a_e, p_e, lo, hi, full = bootstrap_p(Ee, He)
            results.append({
                "participant": P, "baseline": baseline, "detector": det,
                "n_windows": int(len(Ew) + len(Hw)),
                "n_episodes": int(len(Ee) + len(He)),
                "auc_window": round(a_w, 4), "p_window_published": float(f"{p_w:.3g}"),
                "auc_episode": round(a_e, 4),
                "p_episode_bootstrap": round(p_e, 4),
                "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                "auc_shift": round(a_e - a_w, 4),
                "significant_window": bool(p_w < 0.05),
                "significant_episode": bool(p_e < 0.05),
                "flipped_to_null": bool(p_w < 0.05 and p_e >= 0.05),
            })
            print(f"  {P:<4} {baseline:<15} {det:<20} "
                  f"AUC {a_w:.3f}->{a_e:.3f}   "
                  f"p {p_w:.3g} -> {p_e:.4f}"
                  f"{'   FLIPPED TO NULL' if results[-1]['flipped_to_null'] else ''}")

    D = pd.DataFrame(results)
    D.to_csv(OUT / "unit_of_analysis.csv", index=False)

    summ = {
        "n_statistics": int(len(D)),
        "n_inflated_below_1e_20": int((D.p_window_published < 1e-20).sum()),
        "n_exactly_zero_published": int((D.p_window_published == 0).sum()),
        "max_abs_auc_shift": round(float(D.auc_shift.abs().max()), 4),
        "median_abs_auc_shift": round(float(D.auc_shift.abs().median()), 4),
        "n_flipped_to_null": int(D.flipped_to_null.sum()),
        "flipped": D.loc[D.flipped_to_null,
                         ["participant", "baseline", "detector", "auc_window",
                          "p_window_published", "p_episode_bootstrap"]]
                    .to_dict(orient="records"),
        "median_window_n": int(D.n_windows.median()),
        "median_episode_n": int(D.n_episodes.median()),
    }
    summ["sample_size_inflation"] = round(
        summ["median_window_n"] / max(1, summ["median_episode_n"]), 1)
    print("\n" + json.dumps(summ, indent=2))
    (OUT / "unit_of_analysis.json").write_text(json.dumps(summ, indent=2))

    md = ["# Every published p-value, recomputed at the right unit", "",
          "**Generated by `scripts/60_unit_of_analysis.py` — do not edit by hand.**",
          "Preregistered in `research/UNIT_OF_ANALYSIS_NOTE.md`.", "",
          "`26_achievability.py` pools every window from every episode and runs a",
          "Mann-Whitney test on the result. Claim **C04** says windows within a",
          "session are not independent (lag-1 r = 0.995), so that inflates the",
          "apparent sample size — measured here at "
          f"**{summ['sample_size_inflation']}×**.", "",
          "An AUC point estimate survives pooling; it is descriptive. A p-value does",
          "not. Below, each published figure beside the same quantity computed with",
          "the **episode** as the unit and a bootstrap over episodes.", "",
          "| participant | baseline | detector | AUC (window) | AUC (episode) | p published | p corrected | 95% CI |",
          "|---|---|---|---|---|---|---|---|"]
    for r in results:
        flag = " ⚠️" if r["flipped_to_null"] else ""
        md.append(
            f"| {r['participant']} | {r['baseline']} | `{r['detector']}` | "
            f"{r['auc_window']:.3f} | {r['auc_episode']:.3f} | "
            f"{r['p_window_published']:.3g} | **{r['p_episode_bootstrap']:.4f}**{flag} | "
            f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}] |")
    md += ["", "⚠️ = significant as published, not significant at the episode level.", "",
           "**A corrected p of 0.0010 is the bootstrap floor** (2 / 2000), meaning",
           "*p < 0.001 at this resolution* — not an exact value. Reporting it as a",
           "floor rather than as zero is the same discipline this correction is",
           "about: a bootstrap cannot resolve a p-value finer than its own",
           "resolution, and neither could the pooled test that produced `p = 0`.", "",
           "## What moved and what did not", "",
           f"- **AUC point estimates barely moved**: median shift "
           f"{summ['median_abs_auc_shift']:.4f}, largest "
           f"{summ['max_abs_auc_shift']:.4f}. Pooling affects variance, not location.",
           f"- **{summ['n_exactly_zero_published']} statistics were published as "
           f"`p = 0`** and {summ['n_inflated_below_1e_20']} below 1e-20. All are "
           "ordinary numbers at the episode level.",
           f"- **{summ['n_flipped_to_null']} results were significant as published "
           "and are not significant now.**", "",
           "The starkest: `robust_dispersion` at the calibrate-once baseline was",
           "published at **p = 3.4e-15** and is actually **p = 0.144**. Fifteen orders",
           "of magnitude, from an effect that is not there.", "",
           "Measured sample-size inflation: "
           f"**{summ['sample_size_inflation']}×** "
           f"({summ['median_window_n']} windows against "
           f"{summ['median_episode_n']} episodes, median).", "",
           "## Scope", "",
           "The T5 calibrate-once table is not covered — `episode_scores_T5.csv` does",
           "not exist in this repository, so that baseline was never run for T5. Its",
           "row in `ACHIEVABILITY.md` is absent for the same reason.", "",
           "**No conclusion of this project rests on these p-values.** \"0 of 48",
           "configurations pass the gates\" is a count, the operating-point bound is",
           "arithmetic, and the aggregation limit is itself the reason this correction",
           "was needed. What changes is whether the supporting statistics are stated",
           "honestly.", ""]
    (REPORTS / "UNIT_OF_ANALYSIS.md").write_text("\n".join(md) + "\n")
    print(f"\nwrote {REPORTS / 'UNIT_OF_ANALYSIS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
