#!/usr/bin/env python3
"""
Why averaging more windows does not help, and what that rules out.

THE PUZZLE
----------
Per-window AUC is 0.693 (T11). Averaging N independent measurements should
improve discriminability by sqrt(N), and a session holds roughly 55 windows.
Session-level AUC should therefore be far higher. It is 0.673 -- slightly
WORSE.

Something is wrong with the independence assumption, and which thing decides the
entire next direction of the project:

    If windows are strongly correlated, the effective sample size per session is
    a handful rather than 55, aggregation cannot help however it is done, and
    LONGER WINDOWS OR MORE OF THEM ARE A DEAD END. The only remaining path is a
    better measurement -- different features, not more averaging.

    If windows are near-independent, the aggregator is simply a poor one and a
    better statistic should recover the sqrt(N) gain cheaply.

These call for completely different work, so the question is worth measuring
rather than guessing.

WHAT IS COMPUTED
----------------
1. Lag-1 autocorrelation of the risk series within healthy episodes, and the
   effective sample size it implies:

       n_eff = n * (1 - r) / (1 + r)

   the standard first-order correction for serially correlated samples.

2. Several session-level aggregators, to check directly whether a better
   statistic than the median rescues anything.

Usage: python3 scripts/29_aggregation_limit.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

SOURCES = [("episode_scores_local.csv", "T11"), ("episode_scores_T5_local.csv", "T5")]

AGGREGATORS = {
    "median": np.median,
    "mean": np.mean,
    "90th percentile": lambda y: np.percentile(y, 90),
    "max": np.max,
    "top-decile mean": lambda y: np.mean(np.sort(y)[-max(1, len(y) // 10):]),
    "fraction above own median": lambda y: np.mean(y > np.median(y)),
}


def auc(E, H) -> float:
    E, H = np.asarray(E, float), np.asarray(H, float)
    if len(E) < 5 or len(H) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def lag1(y: np.ndarray) -> float:
    if len(y) < 6:
        return np.nan
    a, b = y[:-1], y[1:]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def main() -> int:
    L = ["# Why averaging does not rescue the detector\n",
         "**Reproduce:** `python3 scripts/29_aggregation_limit.py`\n",
         "> Per-window AUC is ~0.70 and a session holds ~55 windows. If those "
         "were independent, aggregation would raise discriminability by roughly "
         "sqrt(55). It does not. This measures why, because the answer decides "
         "which direction is worth pursuing.\n"]
    A = L.append
    A("## Serial correlation and effective sample size\n")
    A("| Participant | Windows per session | Lag-1 autocorrelation | "
      "Effective independent samples |")
    A("|---|---|---|---|")

    agg_rows = []
    for fname, pname in SOURCES:
        path = OUT / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        sub = df[df.detector == "decoder_guard"]

        rs, ns = [], []
        H_by, E_by = [], []
        for _, r in sub.iterrows():
            y = np.fromstring(r.scores, sep=",")
            if not r.crossed:
                v = lag1(y)
                if np.isfinite(v):
                    rs.append(v); ns.append(len(y))
                H_by.append(y)
            else:
                ow, cw = int(r.onset_w), int(r.crossing_w)
                if cw > ow:
                    E_by.append(y[ow:cw])

        r_med = float(np.median(rs)) if rs else np.nan
        n_med = float(np.median(ns)) if ns else np.nan
        n_eff = n_med * (1 - r_med) / (1 + r_med) if np.isfinite(r_med) else np.nan
        A(f"| {pname} | {n_med:.0f} | **{r_med:.3f}** | **{n_eff:.1f}** |")

        for aname, fn in AGGREGATORS.items():
            a = auc([fn(y) for y in E_by if len(y) >= 3],
                    [fn(y) for y in H_by if len(y) >= 3])
            agg_rows.append({"participant": pname, "aggregator": aname, "auc": a})

    A("")
    A("## Session-level aggregators\n")
    A("| Aggregator | " + " | ".join(p for _, p in SOURCES) + " |")
    A("|---|" + "---|" * len(SOURCES))
    d = pd.DataFrame(agg_rows)
    for aname in AGGREGATORS:
        cells = []
        for _, p in SOURCES:
            v = d[(d.participant == p) & (d.aggregator == aname)].auc
            cells.append(f"{v.iloc[0]:.3f}" if len(v) and np.isfinite(v.iloc[0]) else "—")
        A(f"| {aname} | " + " | ".join(cells) + " |")
    A("")
    A("Per-window AUC for comparison: **0.693** (T11), **0.707** (T5).\n")

    d.to_csv(OUT / "aggregation_limit.csv", index=False)
    (REPORTS / "AGGREGATION_LIMIT.md").write_text("\n".join(L))
    print("\n".join(L[3:]).replace("**", ""))
    print(f"\nwrote {REPORTS/'AGGREGATION_LIMIT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
