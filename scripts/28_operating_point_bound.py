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
question, and at that rate the same detector faces a looser per-decision budget.

CORRECTED 20 SEPTEMBER 2026 -- TWO ERRORS IN THAT ARGUMENT
----------------------------------------------------------
This file used to say the once-per-session budget is "four orders of magnitude
looser", and used to report a session-level target of 0.933. Both were wrong,
and the second was wrong in a way that flattered the conclusion.

**The looseness is the pooling factor, nothing more.** One decision per episode
instead of one per window divides the number of decisions by the number of
windows in an episode -- 55 on T11, 42 on T5. That is a factor of 55, i.e. 1.7
orders of magnitude, not 10,000. Four orders would need one decision per
~14 hours. The figure is now computed from the data rather than asserted.

**The 0.933 target was never derived from the budget.** It answers "what AUC
gives 80% detection at a 10% false-flag rate?" -- a fixed 10% that appeared
nowhere in the design. At one decision per 4.6-minute episode, flagging 10% of
healthy episodes is 1.3 false alarms an HOUR, which is 13x the 0.1/hour budget
this project set. Judged at the actual budget the requirement is an AUC of about
**0.990**, against an observed 0.673 and 0.742.

So aggregating to session level does help, and the direction of the
decision-rate argument survives -- but it moves the requirement from 0.9992 to
0.990, not from 0.9992 to 0.933, and the gap to what the monitor achieves stays
very large. Both numbers are reported below, each labelled with the question it
answers, because the 10% figure is a legitimate answer to a different question
and deleting it would hide the mistake rather than correct it.

This file reports both framings side by side, and the design target that follows.

Usage: python3 scripts/28_operating_point_bound.py
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
        # The session-level decision rate, measured rather than assumed: one
        # decision per episode, and an episode is n_windows steps long.
        # From the episode length itself, not from winE -- those are SLICES
        # between onset and crossing, so their length is not an episode's.
        wins = float(sub.n_windows.median())
        ep_hours = wins * STEP_S / 3600
        ep_per_hour = 1.0 / ep_hours
        fpr_ep_budget = BUDGET_PER_HOUR / ep_per_hour
        stats_by[pname].update({
            "windows_per_episode": wins,
            "episode_minutes": ep_hours * 60,
            "episodes_per_hour": ep_per_hour,
            "pooling_factor": wins,
            "fpr_ep_budget": fpr_ep_budget,
            "auc_ep_needed_at_budget": auc_needed(fpr_ep_budget),
            "alarms_per_hour_at_10pct": 0.10 * ep_per_hour,
        })

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
    fac = stats_by[SOURCES[0][1]]["pooling_factor"] if stats_by else float("nan")
    A(f"A deployed monitor need not re-decide every 5 seconds. *\"Should this "
      f"session be flagged for a recalibration check?\"* is a once-per-session "
      f"question, and at that rate the per-decision budget is looser by exactly "
      f"the pooling factor — the number of windows in an episode, "
      f"**{fac:.0f}** on {SOURCES[0][1]} — which is about "
      f"{np.log10(fac):.1f} orders of magnitude.\n")
    A("> **Corrected 20 September 2026.** This paragraph used to say \"four "
      "orders of magnitude looser\". It is not: the looseness is the pooling "
      "factor and nothing else, and four orders would need one decision per "
      "fourteen hours. The figure is now computed from the data rather than "
      "asserted.\n")

    A("### The same detector, judged once per session\n")
    A("| | " + " | ".join(p for _, p in SOURCES) + " |")
    A("|---|" + "---|" * len(SOURCES))
    row("Session-level AUC", "auc_ep", lambda v: f"{v:.3f}")
    row("Detection at 10% false-flag rate", "tpr_ep_10", lambda v: f"{v*100:.1f}%")
    row("Detection at 5% false-flag rate", "tpr_ep_5", lambda v: f"{v*100:.1f}%")
    row("Episode length (minutes)", "episode_minutes", lambda v: f"{v:.1f}")
    row("Decisions per hour at that rate", "episodes_per_hour", lambda v: f"{v:.1f}")
    row("AUC needed for 80% detection at 10%", "auc_ep_needed", lambda v: f"{v:.3f}")
    row("**False alarms/hour that 10% implies**", "alarms_per_hour_at_10pct",
        lambda v: f"**{v:.2f}**")
    row("**Per-decision FPR the 0.1/h budget allows**", "fpr_ep_budget",
        lambda v: f"**{v:.4f}**")
    row("**AUC needed for 80% detection at the budget**",
        "auc_ep_needed_at_budget", lambda v: f"**{v:.3f}**")
    A("")
    A("Aggregating to session level helps one participant and not the other "
      "(T5 0.707 → 0.742; T11 0.693 → 0.673), so it is **not** the rescue "
      "either — the disagreement between participants shows up here too.\n")

    A("### Two targets, and which one the budget actually implies\n")
    b = stats_by[SOURCES[0][1]] if stats_by else {}
    A("> **Corrected 20 September 2026.** Earlier versions of this report gave "
      "**0.933** as *the* session-level design target. That number answers "
      "\"what AUC gives 80% detection at a **10%** false-flag rate?\" — and the "
      "10% was a round figure that appears nowhere in the design. It is not the "
      "budget.\n")
    if b:
        A(f"At one decision per {b['episode_minutes']:.1f}-minute episode, "
          f"flagging 10% of healthy episodes is **{b['alarms_per_hour_at_10pct']:.2f} "
          f"false alarms an hour** — about "
          f"{b['alarms_per_hour_at_10pct'] / BUDGET_PER_HOUR:.0f} times the "
          f"0.1/hour budget this project set and never relaxed.\n")
        A("| Question | Target AUC | What it costs in false alarms |")
        A("|---|---|---|")
        A(f"| 80% detection at a 10% false-flag rate | {b['auc_ep_needed']:.3f} | "
          f"{b['alarms_per_hour_at_10pct']:.2f}/hour |")
        A(f"| 80% detection **inside the 0.1/hour budget** | "
          f"**{b['auc_ep_needed_at_budget']:.3f}** | 0.1/hour |")
        A("")
        A(f"So the honest statement is: deciding once per episode moves the "
          f"requirement from **0.9992 to "
          f"{b['auc_ep_needed_at_budget']:.3f}**, not from 0.9992 to 0.933. "
          f"That is a real reduction and the direction of the argument "
          f"survives — but against an observed **0.673 and 0.742** the gap "
          f"stays very large, and describing it as \"merely hard\" was "
          f"premature.\n")

    A("## The design target that follows\n")
    tgt = b.get("auc_ep_needed_at_budget", float("nan"))
    A(f"To flag 80% of degrading sessions **while staying inside the 0.1/hour "
      f"budget**, a session-level AUC of about **{tgt:.3f}** is required. The "
      f"current monitor achieves **0.67–0.74**.\n")
    A("That is a real gap and a specific one, and it is larger than this report "
      "previously said. It is still the difference between *\"this cannot "
      "work\"* and *\"this needs a measurement roughly this much better\"* — but "
      "the second is now a harder programme than the 0.933 figure implied.\n")
    A("The 10% figure is kept in the table above rather than deleted, because "
      "it is a legitimate answer to a different question and because removing "
      "it would hide the mistake instead of correcting it.\n")
    A("`reports/SESSION_MONITOR_DESIGN.md` and "
      "`reports/COMBINATION_STUDY_RESULT.md` were regenerated against the "
      "corrected target on the same day, and both now read it from this "
      "script's output rather than holding it as a hand-copied literal. "
      "`research/RIG_PREREGISTRATION.md`, `research/BUILD_MANUAL.md` and "
      "`research/EXPERIMENTAL_PROCEDURES.md` still quote 0.933; they are "
      "superseded documents, kept unchanged as the record, and each carries a "
      "banner saying so.\n")

    A("## What this does not license\n")
    A("Relaxing a target after failing to meet it is the classic way to "
      "manufacture a success, so the reasoning matters more than the number. The "
      "argument here is **not** that 0.1/h was too strict. It is that a "
      "per-hour alarm budget and a per-5-second decision rate are different "
      "quantities, and the design conflated them. The per-hour figure is "
      "unchanged; what changes is how many decisions it is divided among.\n")
    A("The honest headline stays as it was: **on this data, at the operating "
      "point the design specified, no configuration works.**\n")

    # Written so that later scripts can READ the targets instead of copying
    # them out of this report by hand. scripts/75 held 0.933 as a literal for
    # that reason, which is how it kept a superseded number after this one was
    # corrected -- a hand-copied constant has no producer and no audit trail.
    (OUT / "operating_point_bound.json").write_text(json.dumps(
        {"budget_per_hour": BUDGET_PER_HOUR, "target_tpr": TARGET_TPR,
         "step_seconds": STEP_S, "by_participant": stats_by}, indent=2,
        default=float))

    (REPORTS / "OPERATING_POINT_BOUND.md").write_text("\n".join(L))
    print("\n".join(L[3:]).replace("**", ""))
    print(f"\nwrote {REPORTS/'OPERATING_POINT_BOUND.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
