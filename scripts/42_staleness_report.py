#!/usr/bin/env python3
"""
Report the recalibration-cadence curves.

Reads data/processed/staleness*.csv from 41_staleness_curve.py and produces the
figure plus the numbers quoted in reports/STALENESS_CURVE.md.

The primary quantity is delta = AUC(A->B) - AUC(B->B), fixed in the scope note
before running: each cross-day fit against the same-day fit on the SAME target
day, so differences in how hard a day's episodes are cannot be mistaken for
staleness.

Usage: python3 scripts/42_staleness_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
FIG = REPO / "reports" / "figures"


def summarise(d: pd.DataFrame) -> dict:
    fwd = d[d.gap_days > 0].dropna(subset=["delta"])
    back = d[d.gap_days < 0].dropna(subset=["delta"])
    s = {
        "n_pairs": int(len(d)),
        "n_forward": int(len(fwd)),
        "gap_min": int(fwd.gap_days.min()) if len(fwd) else None,
        "gap_max": int(fwd.gap_days.max()) if len(fwd) else None,
        "mean_delta_forward": round(float(fwd.delta.mean()), 4) if len(fwd) else None,
        "median_delta_forward": round(float(fwd.delta.median()), 4) if len(fwd) else None,
        "mean_same_day_auc": round(float(d[d.gap_days == 0].auc_mean.mean()), 4),
    }
    if len(fwd) > 3:
        r, p = stats.spearmanr(fwd.gap_days, fwd.delta)
        s["spearman_gap_vs_delta"] = round(float(r), 4)
        s["spearman_p"] = round(float(p), 5)
        # slope in AUC per 100 days, so the number is readable
        sl = stats.linregress(fwd.gap_days, fwd.delta)
        s["auc_lost_per_100_days"] = round(float(sl.slope * 100), 4)
        s["slope_p"] = round(float(sl.pvalue), 5)
    if len(back) > 3 and len(fwd) > 3:
        # A fit from the FUTURE is just as unavailable in practice, but if
        # backward gaps cost the same as forward ones the effect is distance,
        # not ageing. Worth knowing which.
        s["mean_delta_backward"] = round(float(back.delta.mean()), 4)
        u, pu = stats.mannwhitneyu(fwd.delta.abs(), back.delta.abs(),
                                   alternative="two-sided")
        s["fwd_vs_back_p"] = round(float(pu), 5)
    return s


def main() -> int:
    files = {"T11": OUT / "staleness.csv", "T5": OUT / "staleness_T5.csv"}
    data, summary = {}, {}
    for p, f in files.items():
        if not f.exists():
            print(f"missing {f.name} — skipping {p}")
            continue
        d = pd.read_csv(f)
        if "delta" not in d.columns:
            same = d[d.gap_days == 0].set_index("target_day")["auc_mean"].to_dict()
            d["auc_same_day"] = d.target_day.map(same)
            d["delta"] = d.auc_mean - d.auc_same_day
        data[p] = d
        summary[p] = summarise(d)
        print(p, json.dumps(summary[p], indent=2))

    (OUT / "staleness_summary.json").write_text(json.dumps(summary, indent=2))

    pf = OUT / "staleness_permutation.json"
    perm = json.loads(pf.read_text()) if pf.exists() else {}
    if not perm:
        print("NOTE: run 43_staleness_permutation.py — the figure will otherwise "
              "carry no valid p-value.")

    FIG.mkdir(parents=True, exist_ok=True)
    n = len(data)
    fig, axes = plt.subplots(2, n, figsize=(5.6 * n, 7.6), squeeze=False)
    for col, (p_, d) in enumerate(data.items()):
        fwd = d[d.gap_days > 0].dropna(subset=["delta"])
        # Top: the difference, on a fixed +/-0.2 AUC axis so a flat result
        # looks flat instead of being magnified by auto-scaling.
        ax = axes[0][col]
        ax.axhline(0, color="k", lw=1)
        ax.scatter(fwd.gap_days, fwd.delta, s=22, alpha=0.6)
        if len(fwd) > 3:
            sl = stats.linregress(fwd.gap_days, fwd.delta)
            xs = np.array([0, fwd.gap_days.max()])
            # The p-value shown is the DAY-LABEL PERMUTATION p from
            # 43_staleness_permutation.py, not the regression's own. The pairs
            # share source and target days, so the regression p assumes an
            # independence that does not hold and understates by 20-40x.
            pp = perm.get(p_, {}).get("permutation_p")
            lab = f"{sl.slope*100:+.3f} AUC / 100 days"
            lab += f"\npermutation p = {pp:.3f}" if pp is not None else ""
            ax.plot(xs, sl.intercept + sl.slope * xs, "r-", label=lab)
            ax.legend(fontsize=8)
        ax.set_ylim(-0.2, 0.2)
        ax.set_ylabel("AUC(A→B) − AUC(B→B)")
        ax.set_title(f"{p_} — what the gap costs (fixed ±0.2 axis)", fontsize=10)
        ax.grid(alpha=0.3)

        # Bottom: raw AUC, showing that target-day difficulty is the thing the
        # subtraction removes.
        ax = axes[1][col]
        for tgt, g in d.groupby("target_day"):
            g = g.sort_values("gap_days")
            ax.plot(g.gap_days, g.auc_mean, "-", lw=0.8, alpha=0.65)
        ax.axhline(0.5, color="r", ls=":", lw=1)
        ax.set_ylim(0.4, 0.9)
        ax.set_xlabel("gap in days  (target day − source day)")
        ax.set_ylabel("session-level AUC")
        ax.set_title(f"{p_} — raw AUC, one line per target day", fontsize=10)
        ax.grid(alpha=0.3)
    fig.suptitle("How long does a commissioned monitor stay valid?", fontsize=12)
    fig.tight_layout()
    out = FIG / "15_staleness_curve.png"
    fig.savefig(out, dpi=150)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
