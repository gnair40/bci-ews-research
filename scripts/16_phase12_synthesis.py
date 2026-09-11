#!/usr/bin/env python3
"""
16_phase12_synthesis.py
=======================
Close out Phases 1 and 2: the summary figures, and the out-of-distribution check
that the literature review flagged but that had not been run.

TWO JOBS
--------
1. THE FIGURE THAT EXPLAINS THE NEGATIVE RESULT.
   Three quantities plotted against the same time axis for each participant:
   the early-warning indicator, task performance, and mean firing rate. Stacked
   rather than overlaid, because they have different units and a shared y-axis
   would be meaningless. The baseline period is shaded so it is immediately
   visible that the indicator is already climbing while performance is perfect.

2. THE OUT-OF-DISTRIBUTION CHECK.
   The deposit contains two extra T11 sessions on different tasks -- about 16
   minutes of free web browsing on day 658, and a random-target task on day 665.
   The literature review called these "a free out-of-distribution robustness
   check sitting in the download", and they had not been used.

   They answer a sharp question. If the indicator measures the state of the
   RECORDING, its value on those days should match the main-cohort value from
   the SAME day, even though the task is completely different. If it measures
   something about task performance, it should differ. This is a direct test of
   the interpretation reached in scripts/15.

HOW TO RUN
----------
    python3 scripts/16_phase12_synthesis.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"
FIG_DIR = REPO_ROOT / "reports" / "figures"
FREEZE = REPO_ROOT / "research" / "FROZEN_DESIGN.json"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)
ZWIN, PCA_DIM = 9000, 5

# Palette slots 1-3, validated all-pairs in both light and dark modes.
C_IND, C_PERF, C_RATE = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_MUTED, GRID, SHADE = "#0b0b0b", "#52514e", "#e6e5e1", "#eef2f4"


def trailing_z(X, win=ZWIN):
    X = np.asarray(X, float); n, d = X.shape
    c1 = np.vstack([np.zeros((1, d)), np.cumsum(X, 0)])
    c2 = np.vstack([np.zeros((1, d)), np.cumsum(X * X, 0)])
    i = np.arange(1, n + 1); lo = np.maximum(i - win, 0); cnt = (i - lo).reshape(-1, 1)
    m = (c1[i] - c1[lo]) / cnt
    v = np.maximum((c2[i] - c2[lo]) / cnt - m ** 2, 0.0)
    sd = np.sqrt(v); sd[sd < 1e-12] = 1.0
    return (X - m) / sd


def robust_dispersion(Y):
    if Y.ndim != 2 or len(Y) < 3:
        return np.nan
    mad = np.median(np.abs(Y - np.median(Y, 0)), 0) * 1.4826
    return float((mad ** 2).sum())


def load_feats(blk: Path):
    d = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)
    X = np.asarray(d["nctx"], float)
    if "spikePower" in d:
        X = np.hstack([X, np.asarray(d["spikePower"], float)])
    return trailing_z(X), float(np.asarray(d["nctx"], float).mean())


def baseline_space(blocks):
    A = np.vstack([load_feats(b)[0][::5] for b in blocks])
    mu = A.mean(0); A = A - mu
    w, v = np.linalg.eigh(np.cov(A, rowvar=False))
    return mu, v[:, -PCA_DIM:]


def style(ax, ylabel, title=None):
    ax.set_ylabel(ylabel, fontsize=9.5, color=INK_MUTED)
    if title:
        ax.set_title(title, fontsize=10.5, color=INK, loc="left", pad=6)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, labelsize=8.5)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def make_figure(df, participant, baseline_days, cut, out_name):
    """Three quantities, one shared time axis, stacked - never overlaid."""
    d = df[df.participant == participant].sort_values(["trial_day", "block"])
    if d.empty:
        return None
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.4), sharex=True)
    lo, hi = min(baseline_days), max(baseline_days)

    series = [
        (axes[0], "primary", C_IND, "Robust dispersion",
         "Early-warning indicator — already climbing during the healthy baseline"),
        (axes[1], "median_angle_error", C_PERF, "Median angle error (deg)",
         "Task performance — flat through the baseline, then collapses"),
        (axes[2], "mean_firing", C_RATE, "Mean threshold crossings",
         "Mean firing rate — falls steadily throughout"),
    ]
    for ax, col, colour, ylab, title in series:
        if col not in d:
            continue
        ax.axvspan(lo, hi, color=SHADE, zorder=0)
        if cut is not None:
            ax.axvline(cut, color=INK, linestyle="--", linewidth=1.3, zorder=2)
        ax.plot(d.trial_day, d[col], color=colour, linewidth=1.8, marker="o",
                markersize=4.5, markeredgecolor="white", markeredgewidth=0.9,
                zorder=3)
        style(ax, ylab, title)

    axes[0].text(lo, axes[0].get_ylim()[1], "  healthy baseline", va="top",
                 fontsize=9, color=INK_MUTED)
    if cut is not None:
        axes[0].text(cut, axes[0].get_ylim()[1], f"  deterioration (day {cut})",
                     va="top", fontsize=9, color=INK)
    axes[2].set_xlabel("Trial day", fontsize=10, color=INK_MUTED)
    fig.suptitle(f"{participant} — why the significant result is not an early "
                 f"warning: the indicator rises before performance does anything",
                 fontsize=11.5, color=INK, x=0.01, ha="left", y=1.0)
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    p = FIG_DIR / out_name
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def additional_cohort(mu, P):
    """Indicator on the two extra T11 sessions, which use different tasks."""
    root = None
    for c in RAW.rglob("*"):
        if c.is_dir() and c.name.startswith("T11(") :
            root = c; break
    if root is None:
        return pd.DataFrame()
    rows = []
    for task_dir in sorted(x for x in root.iterdir() if x.is_dir()):
        for day_dir in sorted(x for x in task_dir.iterdir()
                              if x.is_dir() and DAY_RE.match(x.name)):
            day = int(DAY_RE.match(day_dir.name).group(1))
            for blk in sorted(x for x in day_dir.iterdir()
                              if x.is_dir() and BLOCK_RE.match(x.name)):
                Z, fr = load_feats(blk)
                rows.append({"task": task_dir.name, "trial_day": day,
                             "block": int(re.search(r"(\d+)", blk.name).group(1)),
                             "primary": robust_dispersion((Z - mu) @ P),
                             "mean_firing": fr})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    args = ap.parse_args()

    ind_p = PROCESSED / "ews_result_indicators.csv"
    drift_p = PROCESSED / "drift_diagnosis_blocks.csv"
    if not ind_p.exists():
        print("Run scripts/14 first.", file=sys.stderr)
        return 1
    F = json.loads(FREEZE.read_text())
    cut = F["design"]["primary"]["boundary_trial_day"]
    t11_base = F["design"]["reversibility_tests"][1]["baseline_days"]
    t5_base = F["design"]["reversibility_tests"][0]["baseline_days"]

    ind = pd.read_csv(ind_p)
    if drift_p.exists():
        dr = pd.read_csv(drift_p)[["trial_day", "block", "mean_firing"]]
        ind = ind.merge(dr, on=["trial_day", "block"], how="left")

    print("=" * 78)
    print("PHASE 1-2 SYNTHESIS")
    print("=" * 78)
    print("\n1. Summary figures")
    for part, base, c in (("T11", t11_base, cut), ("T5", t5_base, 2133)):
        p = make_figure(ind, part, base, c, f"11_{part.lower()}_why_negative.png")
        if p:
            print(f"   wrote {p.relative_to(REPO_ROOT)}")

    print("\n2. Out-of-distribution check — the extra T11 sessions")
    print("-" * 78)
    blocks = []
    for pdir in sorted(x for x in RAW.rglob("*")
                       if x.is_dir() and x.name.upper() == "T11"):
        for dd in sorted(x for x in pdir.iterdir()
                         if x.is_dir() and DAY_RE.match(x.name)):
            if int(DAY_RE.match(dd.name).group(1)) in t11_base:
                blocks += [b for b in sorted(dd.iterdir())
                           if b.is_dir() and BLOCK_RE.match(b.name)]
    mu, P = baseline_space(blocks)
    extra = additional_cohort(mu, P)
    if extra.empty:
        print("   no additional-cohort blocks found")
        return 0

    print("   Indicator on DIFFERENT TASKS, compared with the main cursor task")
    print("   recorded on the SAME DAY:\n")
    print(f"   {'task':<18} {'day':>5} {'blk':>4} {'indicator':>11} {'firing':>9}")
    print("   " + "-" * 52)
    for r in extra.itertuples():
        print(f"   {r.task:<18} {r.trial_day:>5} {r.block:>4} "
              f"{r.primary:>11.2f} {r.mean_firing:>9.2f}")
    print()
    main11 = ind[ind.participant == "T11"]
    for day in sorted(extra.trial_day.unique()):
        same = main11[main11.trial_day == day]
        if same.empty:
            continue
        e = extra[extra.trial_day == day]
        print(f"   day {day}:  main cursor task {same.primary.mean():7.2f}   "
              f"other task {e.primary.mean():7.2f}   "
              f"difference {abs(same.primary.mean()-e.primary.mean()):.2f} "
              f"({100*abs(same.primary.mean()-e.primary.mean())/same.primary.mean():.1f}%)")

    extra.to_csv(PROCESSED / "additional_cohort_indicator.csv", index=False)
    print("""
   HOW TO READ THIS
   A close match across completely different tasks on the same day means the
   indicator is tracking the state of the RECORDING, not anything about the task
   or the participant's performance - which is the interpretation reached in
   scripts/15. A large difference would mean the opposite.""")
    print(f"\n   Wrote {(PROCESSED/'additional_cohort_indicator.csv').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
