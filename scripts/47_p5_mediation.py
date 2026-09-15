#!/usr/bin/env python3
"""
Is the P5 result real, or is it built into how the outcome is defined?

P5 (that day's frozen-decoder error) predicts the monitor's same-day AUC at
rho = -0.720, p = 0.0055 on T11 -- preregistered, correct sign, clears
Bonferroni. Before that can be called a finding it has to survive an obvious
alternative: THE OUTCOME IS ITSELF DEFINED BY DECODER PERFORMANCE.

The AUC compares faulted episodes, scored over the window from fault onset to
the moment decoder error crosses the deterioration threshold, against healthy
episodes. On a day whose baseline error is already near chance:

  - episodes may cross the threshold almost immediately, leaving a very short
    early-warning window with few points to take a median over, and
  - the crossed / not-crossed split shifts, changing which episodes land in
    which group.

Either would depress AUC on high-error days for reasons that have nothing to do
with whether the monitor can see faults. This script measures both, so the claim
either survives an explicit challenge or is withdrawn.

Usage: python3 scripts/47_p5_mediation.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def main() -> int:
    res = {}
    for P, sfx, scores in [("T11", "", "episode_scores_local.csv"),
                           ("T5", "_T5", "episode_scores_T5_local.csv")]:
        dp = OUT / f"day_predictors{sfx}.csv"
        if not dp.exists():
            continue
        d = pd.read_csv(dp)

        e = pd.read_csv(OUT / scores)
        e = e[e.detector == "decoder_guard"].copy()
        e["day"] = e.block_id.map(day_of)
        e["ew_len"] = np.where(e.crossed, e.crossing_w - e.onset_w, np.nan)

        agg = e.groupby("day").agg(
            frac_crossed=("crossed", "mean"),
            mean_ew_len=("ew_len", "mean"),
            median_ew_len=("ew_len", "median"),
            n_episodes=("episode_id", "nunique"),
        ).reset_index()
        m = d.merge(agg, on="day", how="inner")
        m.to_csv(OUT / f"p5_mediation{sfx}.csv", index=False)

        def sp(a, b):
            ok = m[a].notna() & m[b].notna()
            if ok.sum() < 4 or m.loc[ok, a].nunique() < 3:
                return None, None
            r, p = stats.spearmanr(m.loc[ok, a], m.loc[ok, b])
            return round(float(r), 3), round(float(p), 4)

        out = {"n_days": int(len(m))}
        for target in ["frac_crossed", "mean_ew_len", "median_ew_len"]:
            r, p = sp("P5_decoder_error", target)
            out[f"decoder_error_vs_{target}"] = {"rho": r, "p": p}
            r2, p2 = sp(target, "auc")
            out[f"{target}_vs_auc"] = {"rho": r2, "p": p2}

        # The decisive test: partial correlation of decoder error with AUC,
        # controlling for the early-warning window length. Spearman partial =
        # Pearson partial on the ranks, which is what is computed here.
        ok = m[["P5_decoder_error", "auc", "mean_ew_len"]].notna().all(axis=1)
        if ok.sum() >= 5:
            R = m.loc[ok, ["P5_decoder_error", "auc", "mean_ew_len"]].rank()
            C = np.corrcoef(R.T.values)
            inv = np.linalg.inv(C)
            partial = -inv[0, 1] / np.sqrt(inv[0, 0] * inv[1, 1])
            n, k = int(ok.sum()), 1
            dfree = n - 2 - k
            t = partial * np.sqrt(dfree / max(1e-12, 1 - partial ** 2))
            out["partial_rho_decoder_error_vs_auc_controlling_ew_len"] = round(float(partial), 3)
            out["partial_p"] = round(float(2 * stats.t.sf(abs(t), dfree)), 4)
            out["partial_df"] = dfree
        res[P] = out
        print(f"\n=== {P} ===")
        print(m[["day", "auc", "P5_decoder_error", "frac_crossed",
                 "mean_ew_len"]].round(3).to_string(index=False))
        print(json.dumps(out, indent=2))

    (OUT / "p5_mediation.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
