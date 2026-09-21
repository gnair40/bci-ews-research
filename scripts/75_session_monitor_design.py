#!/usr/bin/env python3
"""
75_session_monitor_design.py
============================
How many rig sessions does it take to find out whether a session-level monitor
can reach the target?

WHY THIS REPLACES THE DRIFT SWEEP AS THE CENTREPIECE
-----------------------------------------------------
Arm B was designed to ask whether this project's negative result is specific to
cortex or general to any slowly drifting sensor array. Three findings since have
made that the wrong question to spend twenty-two hours of recording on.

1. `reports/OPERATING_POINT_BOUND.md` located the failure precisely. A budget of
   0.1 false alarms per hour divided among 720 decisions an hour demands a
   per-decision false-positive rate of 1.4e-4, which needs a per-window AUC of
   0.9992 against an observed 0.693. Asked **once per session** instead, the same
   detector needs an AUC of about **0.99** to flag 80% of degrading sessions
   while staying inside that same budget (this was quoted as 0.933 until
   20 September 2026; 0.933 is the target at a 10% false-flag rate, which is
   thirteen times the budget). It achieves **0.673** (T11) and **0.742**
   (T5).

   That is the difference between "this cannot work" and "this needs to be about
   this much better", and only the second is a research programme.

2. `reports/AUTOCORR_BY_SEVERITY.md` showed the false-alarm rate **cannot be
   measured on the archived data at all**. Restricted to genuinely fault-free
   episodes it rests on 17 and 15 episodes, about 1.4 hours, against a budget of
   0.1 per hour. You cannot estimate a rate that low from that little.

3. The silence gate fails fault-free too (76.5% and 100% against a 10% bar), so
   the negative result is real and does not need re-confirming on a camera.

Put together: the open question is no longer *whether* monitoring fails, it is
**how much better a monitor would have to be, and whether that is reachable.**
And the measurement that question needs -- hundreds of fault-free sessions with
constructed onsets -- is exactly what a rig can provide and a person cannot. No
BCI participant can sit for two hundred sessions so somebody can estimate a
false-alarm rate. A box with a camera in it can run unattended for a fortnight.

**That is the argument for building the rig, and it is a much better one than the
argument it was originally built on.**

WHAT THIS SCRIPT DOES
---------------------
Works out the recording schedule: how many healthy and how many degrading
sessions are needed to measure a session-level AUC precisely enough to tell
"reaches the target" from "does not", and what that costs in hours.

Usage: python3 scripts/75_session_monitor_design.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

# Read from scripts/28's output rather than copied out of its report. This used
# to be `AUC_TARGET = 0.933`, a literal transcribed by hand, and when scripts/28
# was corrected on 20 September 2026 this file went on quoting the superseded
# number. A constant with no producer is a constant nobody can audit.
def _target() -> tuple[float, float, dict]:
    """(budget-consistent target, the 10%-FPR target, the full record)."""
    f = REPO / "data" / "processed" / "operating_point_bound.json"
    if not f.exists():
        raise SystemExit(
            "data/processed/operating_point_bound.json is missing.\n"
            "Run:  python3 scripts/28_operating_point_bound.py")
    d = json.loads(f.read_text())
    by = d["by_participant"]
    # The stricter of the participants' budget-consistent targets, because a
    # design sized against the easier one would be under-powered for the other.
    at_budget = max(v["auc_ep_needed_at_budget"] for v in by.values())
    at_10 = max(v["auc_ep_needed"] for v in by.values())
    return float(at_budget), float(at_10), d


AUC_TARGET, AUC_TARGET_AT_10PCT, OPBOUND = _target()
AUC_OBSERVED = {"T11": 0.673, "T5": 0.742}
SESSION_MINUTES = 5.0     # one rig block
ALPHA = 0.05
POWER = 0.80


def auc_se(auc: float, n_pos: int, n_neg: int) -> float:
    """Standard error of an AUC (Hanley & McNeil, 1982).

    The exponential-distribution approximation for Q1 and Q2. It is the standard
    choice and it is conservative for the skewed score distributions this project
    actually has, which is the safe direction for a sample-size calculation.
    """
    q1 = auc / (2.0 - auc)
    q2 = 2.0 * auc * auc / (1.0 + auc)
    var = (auc * (1 - auc)
           + (n_pos - 1) * (q1 - auc * auc)
           + (n_neg - 1) * (q2 - auc * auc)) / (n_pos * n_neg)
    return math.sqrt(max(var, 0.0))


def n_for_precision(auc: float, half_width: float, ratio: float = 1.0) -> int:
    """Degrading sessions needed for a 95% CI of the given half-width."""
    for n in range(5, 4001):
        se = auc_se(auc, n, int(round(n * ratio)))
        if 1.96 * se <= half_width:
            return n
    return -1


def n_for_discrimination(auc_alt: float, auc_null: float, ratio: float = 1.0) -> int:
    """Sessions needed to distinguish auc_alt from auc_null at ALPHA/POWER."""
    z_a = stats.norm.ppf(1 - ALPHA / 2)
    z_b = stats.norm.ppf(POWER)
    for n in range(5, 4001):
        se = auc_se((auc_alt + auc_null) / 2, n, int(round(n * ratio)))
        if abs(auc_alt - auc_null) >= (z_a + z_b) * se:
            return n
    return -1


def main() -> int:
    result = {
        "what_this_is": "Recording schedule for the session-level monitor study.",
        "auc_target": AUC_TARGET, "auc_observed": AUC_OBSERVED,
        "target_from": "reports/OPERATING_POINT_BOUND.md — the AUC needed for "
                       "80% detection at a 10% false-flag rate",
    }

    # ---- 1. how precisely can an AUC be measured, per session count? ------
    prec = []
    for n in [20, 40, 60, 100, 150, 200, 300]:
        se = auc_se(AUC_TARGET, n, n)
        prec.append({"sessions_each_arm": n, "total_sessions": 2 * n,
                     "auc_se": se, "ci95_half_width": 1.96 * se,
                     "hours": 2 * n * SESSION_MINUTES / 60.0})
    result["precision"] = prec

    # ---- 2. how many to tell "reaches target" from "does not"? ------------
    disc = []
    for name, obs in AUC_OBSERVED.items():
        n = n_for_discrimination(AUC_TARGET, obs)
        disc.append({"against": name, "observed_auc": obs, "sessions_each_arm": n,
                     "total_sessions": 2 * n,
                     "hours": 2 * n * SESSION_MINUTES / 60.0})
    # and the harder, more useful comparison: target vs a near miss
    for gap, label in [(0.05, "a near miss"), (0.10, "a clear miss")]:
        n = n_for_discrimination(AUC_TARGET, AUC_TARGET - gap)
        disc.append({"against": label, "observed_auc": AUC_TARGET - gap,
                     "sessions_each_arm": n, "total_sessions": 2 * n,
                     "hours": 2 * n * SESSION_MINUTES / 60.0})
    result["discrimination"] = disc

    # ---- 3. the false-flag rate, which is the thing that cannot be measured
    #        on the archived data at all
    ff = []
    for rate in [0.10, 0.05, 0.02]:
        # To see a rate p with a relative standard error of ~30% you need about
        # 1/(0.09 p) healthy sessions: se(p) = sqrt(p(1-p)/n).
        n = int(math.ceil((1 - rate) / (rate * 0.09)))
        ff.append({"false_flag_rate": rate, "healthy_sessions_needed": n,
                   "hours": n * SESSION_MINUTES / 60.0,
                   "archived_equivalent_hours": 1.4})
    result["false_flag_measurement"] = ff

    # The binding constraints are AUC precision and the false-flag rate, NOT
    # beating the archived value. Proving the rig exceeds 0.673 is a straw man:
    # nobody doubts it can, and a study powered only for that answers nothing.
    n_auc = next(q for q in prec if q["ci95_half_width"] <= 0.04)
    n_ff = ff[0]["healthy_sessions_needed"]
    per_arm = max(n_auc["sessions_each_arm"], n_ff)
    result["recommended"] = {
        "healthy_sessions": per_arm, "degrading_sessions": per_arm,
        "total_sessions": 2 * per_arm,
        "hours": 2 * per_arm * SESSION_MINUTES / 60.0,
        "auc_ci95_half_width": 1.96 * auc_se(AUC_TARGET, per_arm, per_arm),
        "binding_constraint": ("false-flag rate" if n_ff >= n_auc["sessions_each_arm"]
                               else "AUC precision"),
    }

    (OUT / "session_monitor_design.json").write_text(json.dumps(result, indent=2))

    # ------------------------------------------------------------------ report
    L = ["# What the rig should actually measure\n",
         "**Generated by `scripts/75_session_monitor_design.py` — do not edit by hand.**\n",
         "> **This replaces the drift sweep as the centrepiece of Arm B.** The "
         "reasons are three findings from the September audit, set out below. "
         "The original design is not wrong, it answers a question that is no "
         "longer the open one.\n"]
    A = L.append

    A("## Why the question changed\n")
    A(f"**1. The failure was located precisely.** A budget of 0.1 false alarms "
      f"per hour, divided among 720 decisions an hour, demands a per-decision "
      f"false-positive rate of 1.4e-4 — needing a per-window AUC of **0.9992** "
      f"against an observed 0.693. Asked **once per session** instead, the same "
      f"detector needs **{AUC_TARGET:.3f}** to flag 80% of degrading sessions "
      f"while staying inside the same 0.1/hour budget. It achieves **0.673** "
      f"(T11) and **0.742** (T5).\n")
    A(f"> **Corrected 20 September 2026.** This paragraph, and the tables below, "
      f"used to quote **{AUC_TARGET_AT_10PCT:.3f}** as the session-level target. "
      f"That figure is the AUC needed for 80% detection at a **10% false-flag "
      f"rate**, which at one decision per episode is about 1.3 false alarms an "
      f"hour — thirteen times the budget. The budget-consistent target is "
      f"**{AUC_TARGET:.3f}**. See `reports/OPERATING_POINT_BOUND.md`, which now "
      f"reports both and says which question each answers.\n")
    A("That is the difference between *this cannot work* and *this needs to be "
      "about this much better*, and only the second is a research programme — "
      "though at the corrected target the second is a harder programme than "
      "this report used to imply.\n")
    A("**2. The false-alarm rate cannot be measured on the archived data at "
      "all.** Restricted to genuinely fault-free episodes it rests on 17 and 15 "
      "episodes — about **1.4 hours** — against a budget of 0.1 per hour. A rate "
      "that low cannot be estimated from that much data by anyone.\n")
    A("**3. The negative result is real and does not need re-confirming.** The "
      "silence gate fails on fault-free episodes too, 76.5% and 100% against a "
      "10% bar. Spending twenty-two hours of rig time to watch a camera fail the "
      "same way would confirm something already established.\n")
    A("So the open question is no longer *whether* monitoring fails. It is "
      "**how much better a monitor must be, and whether that is reachable** — "
      "and the measurement that answers it needs hundreds of fault-free sessions "
      "with constructed onsets.\n")
    A("**That is the argument for building the rig, and it is a far better one "
      "than the argument it was built on.** No BCI participant can sit through "
      "two hundred sessions so somebody can estimate a false-alarm rate. A box "
      "with a camera in it can run unattended for a fortnight.\n")

    A("## How precisely can a session-level AUC be measured?\n")
    A("| Sessions per arm | Total | 95% CI half-width | Recording time |")
    A("|---|---|---|---|")
    for q in prec:
        A(f"| {q['sessions_each_arm']} | {q['total_sessions']} | "
          f"±{q['ci95_half_width']:.3f} | {q['hours']:.1f} h |")
    A("")
    A("Half the sessions healthy, half with a constructed degradation. "
      "Standard error by Hanley and McNeil, which is conservative for skewed "
      "score distributions — the safe direction for a sample size.\n")

    A("## How many sessions to answer the actual question?\n")
    A("| Comparison | Sessions per arm | Total | Recording time |")
    A("|---|---|---|---|")
    for q in disc:
        A(f"| Target {AUC_TARGET:.3f} vs {q['against']} "
          f"({q['observed_auc']:.3f}) | "
          f"{q['sessions_each_arm']} | {q['total_sessions']} | {q['hours']:.1f} h |")
    A("")
    n_t11 = next(q for q in disc if q["against"] == "T11")
    A(f"**Do not take the first row as the schedule.** Showing the rig beats "
      f"0.673 needs only {n_t11['sessions_each_arm']} sessions per arm, and it "
      f"is a straw man: nobody doubts it can, and a study powered only for that "
      f"answers nothing. Resolving a *near miss* — is it {AUC_TARGET:.2f} or "
      f"{AUC_TARGET - 0.05:.2f}? — is the hard case, and it costs an order of "
      f"magnitude more.\n")

    A("## The measurement nobody can currently make\n")
    A("| False-flag rate to measure | Healthy sessions needed | Recording time | "
      "Archived data has |")
    A("|---|---|---|---|")
    for q in ff:
        A(f"| {q['false_flag_rate']:.0%} | {q['healthy_sessions_needed']} | "
          f"{q['hours']:.1f} h | {q['archived_equivalent_hours']} h |")
    A("")
    A("To measure a 10% false-flag rate to within about a third of itself takes "
      f"{ff[0]['healthy_sessions_needed']} healthy sessions. The archived data "
      f"offers 1.4 hours of genuinely fault-free recording. **This is the gap "
      f"the rig exists to close**, and it is a gap of nearly two orders of "
      f"magnitude.\n")

    rec = result["recommended"]
    A("## The recommended schedule\n")
    A(f"- **{rec['healthy_sessions']} healthy sessions and "
      f"{rec['degrading_sessions']} with a constructed degradation**")
    A(f"- **{rec['total_sessions']} sessions total, about {rec['hours']:.0f} "
      f"hours** of unattended recording")
    A(f"- Gives a session-level AUC to ±{rec['auc_ci95_half_width']:.3f} and a "
      f"10% false-flag rate to within about a third of itself")
    A(f"- Binding constraint: **{rec['binding_constraint']}**")
    A("")
    A("For comparison, the drift sweep this replaces costs about 22 hours. "
      "**The new design costs about the same and answers the question that is "
      "actually open.**\n")

    A("## What Arm B becomes\n")
    A("| | Old design | New design |")
    A("|---|---|---|")
    A(f"| Question | Is the within-session limit neural-specific? | Can a "
      f"session-level monitor reach AUC {AUC_TARGET:.2f}, and at what "
      f"false-flag rate? |")
    A(f"| Centrepiece | Drift sweep, 5 levels x 53 blocks, 22 h | Session-level "
      f"monitor study, {rec['total_sessions']} sessions, {rec['hours']:.0f} h |")
    A("| Compared against | Cortex's autocorrelation | A design target derived "
      "from this project's own arithmetic |")
    A("| If it succeeds | The limit generalises beyond brains | **A monitor that "
      "flags sessions for recalibration, with a measured false-flag rate** |")
    A("| If it fails | The limit is neural-specific | The target is out of reach "
      "for this detector class, measured rather than asserted |")
    A("")
    A("Both outcomes are still informative, which is the test of whether this is "
      "an experiment. But the success case is now **a working device** rather "
      "than a confirmed negative, and the failure case is a number rather than a "
      "shrug.\n")

    A("## What this does not license\n")
    A("Relaxing a target after failing to meet it is how a success gets "
      "manufactured, so the reasoning matters more than the number. The argument "
      "is **not** that 0.1 per hour was too strict. It is that a per-hour alarm "
      "budget and a per-five-second decision rate are different quantities and "
      "the original design conflated them. The per-hour figure is unchanged; "
      "what changes is how many decisions it is divided among.\n")
    A("The headline stays as it was: **on the archived data, at the operating "
      "point the design specified, no configuration works.**")

    (REPORTS / "SESSION_MONITOR_DESIGN.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'SESSION_MONITOR_DESIGN.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
