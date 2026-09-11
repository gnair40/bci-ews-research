#!/usr/bin/env python3
"""
Why no decision rule can meet the false-alarm budget: the arithmetic.

THE CORRECTION THIS MAKES
-------------------------
An earlier conclusion in this project was that the information is present
(AUC 0.69-0.71) and the failure therefore lies "in the machinery that turns
scores into warnings -- a fixable engineering problem". Comparing decision rules
by their full detection/false-alarm curve refuted that: threshold, CUSUM, and
CUSUM with a specificity gate all detect ~0% of faults inside the budget. The
rule is not the bottleneck, and this file works out what is.

THE ARITHMETIC
--------------
The budget is 0.1 false alarms per HOUR. The monitor decides every 5 seconds,
which is 720 decisions per hour. Over the healthy test record the budget permits
about 2.4 alarms across ~17,000 windows, so the per-window false-positive rate
must be about 1.4e-4.

Detection achievable at that false-positive rate, from the observed score
distributions, is 0.18% (T11) and 0.03% (T5). The per-window AUC that WOULD
deliver 80% detection there is 0.9992. Observed is 0.693 and 0.707.

That gap is not closable by a smarter rule. It is the multiple-comparisons
burden of asking a weak detector 720 questions an hour and then forbidding it
to be wrong.

SO THE OPERATING POINT WAS MIS-SPECIFIED
----------------------------------------
"0.1 false alarms per hour" was set in the design as a usability requirement,
and it is a reasonable one for an ALARM. But it was then applied to a system
making a decision every 5 seconds, which silently converted a mild usability
requirement into a demand for near-perfect per-window discrimination.

A deployed decoder-health monitor does not need to re-decide every 5 seconds.
"Should this session be flagged for a recalibration check?" is a once-per-session
question, and at that rate the same detector faces a per-decision false-positive
budget four orders of magnitude looser.

This file reports both framings side by side, and the design target that follows.

Usage: python3 scripts/28_operating_point_bound.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

STEP_S = 5.0
BUDGET_PER_HOUR = 0.1
TARGET_TPR = 0.80
SOURCES = [("episode_scores_local.csv", "T11"), ("episode_scores_T5_local.csv", "T5")]


def auc_of(E, H) -> float:
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def auc_needed(fpr: float, tpr: float = TARGET_TPR) -> float:
    """AUC required for `tpr` detection at `fpr`, equal-variance normal model.

    An idealisation, and stated as one: real score distributions are skewed and
    the normal model will be optimistic in the far tail. That makes the number a
    LOWER bound on what is required, which is the safe direction for a target.
    """
    d = stats.norm.ppf(tpr) + stats.norm.ppf(1 - fpr)
    return float(stats.norm.cdf(d / np.sqrt(2)))


def main() -> int:
    L = ["# Why the false-alarm budget is unreachable\n",
         "**Reproduce:** `python3 scripts/28_operating_point_bound.py`\n",
         "> This corrects an earlier conclusion. Having measured that the "
         "information is present (AUC 0.69-0.71), this project concluded the "
         "failure was in the machinery converting scores to warnings and would "
         "be fixable. Comparing decision rules by their full curve refuted that: "
         "threshold, CUSUM and CUSUM-with-a-specificity-gate all detect ~0% "
         "inside the budget. What follows is the reason.\n"]
    A = L.append

    A("## The multiple-comparisons burden\n")
    A("| | " + " | ".join(p for _, p in SOURCES) + " |")
    A("|---|" + "---|" * len(SOURCES))
    stats_by = {}

    for fname, pname in SOURCES:
        path = OUT / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        sub = df[df.detector == "decoder_guard"]
        winH, winE, epH, epE = [], [], [], []
        for _, r in sub.iterrows():
            y = np.fromstring(r.scores, sep=",")
            if not r.crossed:
                winH.append(y); epH.append(float(np.median(y)))
            else:
                ow, cw = int(r.onset_w), int(r.crossing_w)
                if cw > ow:
                    winE.append(y[ow:cw]); epE.append(float(np.median(y[ow:cw])))
        H, E = np.concatenate(winH), np.concatenate(winE)
        hours = len(H) * STEP_S / 3600
        allowed = BUDGET_PER_HOUR * hours
        fpr = allowed / len(H)
        thr = np.quantile(H, 1 - fpr)
        stats_by[pname] = {
            "windows": len(H), "hours": hours, "allowed": allowed, "fpr": fpr,
            "auc_win": auc_of(E, H), "tpr_at_budget": float((E > thr).mean()),
            "auc_win_needed": auc_needed(fpr),
            "auc_ep": auc_of(np.array(epE), np.array(epH)),
            "tpr_ep_10": float((np.array(epE) > np.quantile(epH, 0.90)).mean()),
            "tpr_ep_5": float((np.array(epE) > np.quantile(epH, 0.95)).mean()),
            "auc_ep_needed": auc_needed(0.10),
        }

    def row(label, key, fmt):
        A(f"| {label} | " + " | ".join(fmt(stats_by[p][key]) for _, p in SOURCES
                                       if p in stats_by) + " |")

    row("Healthy windows in test", "windows", lambda v: f"{v:,}")
    row("Healthy hours", "hours", lambda v: f"{v:.1f}")
    row("Alarms the budget permits", "allowed", lambda v: f"{v:.1f}")
    row("**Required per-window false-positive rate**", "fpr", lambda v: f"**{v:.1e}**")
    row("Observed per-window AUC", "auc_win", lambda v: f"{v:.3f}")
    row("**Detection achievable there**", "tpr_at_budget", lambda v: f"**{v*100:.2f}%**")
    row("**AUC needed for 80% detection there**", "auc_win_needed", lambda v: f"**{v:.4f}**")
    A("")
    A("An AUC of 0.999 is not a detector that needs tuning. It is a different "
      "measurement problem. **The budget, as applied, demands near-perfect "
      "discrimination on every one of 720 decisions an hour.**\n")

    A("## The operating point was mis-specified\n")
    A("`0.1 false alarms per hour` was set as a usability requirement, and as a "
      "requirement on an *alarm* it is sensible — more than one spurious alert "
      "per ten hours would train a user to ignore it. The error was applying it "
      "to a system that re-decides every 5 seconds, which quietly converts a "
      "mild usability constraint into a demand for 0.9992 AUC.\n")
    A("A deployed monitor need not re-decide every 5 seconds. *\"Should this "
      "session be flagged for a recalibration check?\"* is a once-per-session "
      "question, and at that rate the false-positive budget per decision is four "
      "orders of magnitude looser.\n")

    A("### The same detector, judged once per session\n")
    A("| | " + " | ".join(p for _, p in SOURCES) + " |")
    A("|---|" + "---|" * len(SOURCES))
    row("Session-level AUC", "auc_ep", lambda v: f"{v:.3f}")
    row("Detection at 10% false-flag rate", "tpr_ep_10", lambda v: f"{v*100:.1f}%")
    row("Detection at 5% false-flag rate", "tpr_ep_5", lambda v: f"{v*100:.1f}%")
    row("AUC needed for 80% detection at 10%", "auc_ep_needed", lambda v: f"{v:.3f}")
    A("")
    A("Aggregating to session level helps one participant and not the other "
      "(T5 0.707 → 0.742; T11 0.693 → 0.673), so it is **not** the rescue "
      "either — the disagreement between participants shows up here too. But it "
      "moves the problem from impossible to merely hard.\n")

    A("## The design target that follows\n")
    tgt = stats_by[SOURCES[0][1]]["auc_ep_needed"] if stats_by else float("nan")
    A(f"To flag 80% of degrading sessions while wrongly flagging 10% of healthy "
      f"ones, a session-level AUC of about **{tgt:.2f}** is required. The "
      f"current monitor achieves **0.67–0.74**.\n")
    A("That is a real gap and a specific one. It is the difference between "
      "*\"this cannot work\"* and *\"this needs a measurement roughly this much "
      "better\"*, and only the second is a research programme.\n")

    A("## What this does not license\n")
    A("Relaxing a target after failing to meet it is the classic way to "
      "manufacture a success, so the reasoning matters more than the number. The "
      "argument here is **not** that 0.1/h was too strict. It is that a "
      "per-hour alarm budget and a per-5-second decision rate are different "
      "quantities, and the design conflated them. The per-hour figure is "
      "unchanged; what changes is how many decisions it is divided among.\n")
    A("The honest headline stays as it was: **on this data, at the operating "
      "point the design specified, no configuration works.**\n")

    (REPORTS / "OPERATING_POINT_BOUND.md").write_text("\n".join(L))
    print("\n".join(L[3:]).replace("**", ""))
    print(f"\nwrote {REPORTS/'OPERATING_POINT_BOUND.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
