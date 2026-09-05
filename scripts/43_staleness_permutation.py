#!/usr/bin/env python3
"""
Is the staleness trend real, given that the day pairs are not independent?

95 forward pairs on T11 come from only 15 sessions, so every pair shares a source
or target day with many others. Spearman's p-value assumes independent
observations and is therefore not usable here -- quoting p = 0.003 from it would
overstate the evidence, possibly by a lot.

THE TEST
--------
Shuffle which calendar date belongs to which session, keeping the AUC matrix
exactly as measured, recompute every gap, and recompute the correlation. This
destroys only the relationship between elapsed time and performance while
preserving the full dependency structure of the pairs -- which is precisely the
null hypothesis of interest: "the AUC differences are real, but calendar distance
has nothing to do with them."

Usage: python3 scripts/43_staleness_permutation.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
N_PERM = 20000
SEED = 20260902


def permute(d: pd.DataFrame, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    days = np.array(sorted(set(d.source_day) | set(d.target_day)))
    fwd = d[d.gap_days > 0].dropna(subset=["delta"])
    obs = stats.spearmanr(fwd.gap_days, fwd.delta).statistic

    rng = np.random.default_rng(seed)
    hits = 0
    null = np.empty(n_perm)
    for i in range(n_perm):
        relabel = dict(zip(days, rng.permutation(days)))
        g = d.target_day.map(relabel) - d.source_day.map(relabel)
        m = (g > 0) & d.delta.notna()
        if m.sum() < 5:
            null[i] = np.nan
            continue
        r = stats.spearmanr(g[m], d.delta[m]).statistic
        null[i] = r
        if abs(r) >= abs(obs):
            hits += 1
    valid = int(np.isfinite(null).sum())
    return {
        "observed_spearman": round(float(obs), 4),
        "n_permutations": valid,
        # +1 in numerator and denominator: the observed arrangement is itself one
        # of the possible labellings, so a p of exactly 0 is not attainable.
        "permutation_p": round((hits + 1) / (valid + 1), 5),
        "null_spearman_sd": round(float(np.nanstd(null)), 4),
        "naive_spearman_p": round(float(stats.spearmanr(fwd.gap_days, fwd.delta).pvalue), 5),
    }


def main() -> int:
    res = {}
    for p, f in [("T11", OUT / "staleness.csv"), ("T5", OUT / "staleness_T5.csv")]:
        if not f.exists():
            continue
        d = pd.read_csv(f)
        res[p] = permute(d)
        print(p, json.dumps(res[p], indent=2))
        inflation = res[p]["permutation_p"] / max(res[p]["naive_spearman_p"], 1e-12)
        print(f"   the naive p understates the true p by {inflation:.0f}x\n")
    (OUT / "staleness_permutation.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
