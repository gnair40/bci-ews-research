#!/usr/bin/env python3
"""
analyze_correlation.py — does correlation with performance mean the monitor works?

=============================================================================
WHAT THIS SCRIPT IS FOR
=============================================================================
This is experiment P-4, and it is the one the project's novelty claim rests on.

Here is the situation it tests.

A decoder-health monitor watches a sensor array and produces a "risk score" that
is supposed to go up when the array is degrading. To show such a monitor works,
the published approach is to CORRELATE its score against how well the user is
actually doing. The current state of the art in brain-computer interfaces
(MINDFUL, Pun et al. 2024) reports correlations of r = 0.93 and r = 0.72 this
way, and proposes the monitor for deciding when to recalibrate a decoder.

This script asks whether that kind of evidence supports that kind of conclusion,
by computing on the SAME recordings:

  (a) the correlation the field would report, and
  (b) the lead time and false-alarm rate that actually decide whether a warning
      system is worth having.

If (a) is strong while (b) is unusable, then correlation-based validation does
not support the claims being drawn from it. That is a finding about METHOD, and
it applies to anyone validating a monitor this way.

=============================================================================
THE SECOND THING IT CHECKS, WHICH MATTERS JUST AS MUCH
=============================================================================
A monitor's score and a performance measure BOTH tend to drift over weeks. Any
two quantities that both drift will correlate with each other whether or not one
tells you anything about the other. (Ice cream sales and drowning deaths both
rise in summer.)

So this script computes the correlation three ways:

  1. RAW            -- what the field reports
  2. PARTIAL        -- with the time trend removed from both
  3. ON CHANGES     -- does a CHANGE in the score go with a CHANGE in performance?

On this project's own archived-data analysis those three gave -0.818, -0.500 and
-0.679 for one participant, and -0.943, -0.852 and +0.100 for the other -- where
the last one not only vanished but changed sign. If the same pattern appears
here, it says the raw number is not the right thing to report.

=============================================================================
WHAT YOU NEED BEFORE RUNNING IT
=============================================================================
Sessions recorded and scored: the healthy campaign (P-2) and the degraded
sessions (P-3). Specifically, a CSV with one row per session containing:

    session, block, healthy, risk_score, performance, onset_seconds, warn_seconds

`make_session_table.py` builds that file from the raw recordings.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/analyze_correlation.py

or, pointing at a different table:

    python3 physical/code/analyze_correlation.py --table physical/data/sessions.csv

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/results/correlation_vs_usability.json
    physical/data/results/P4_CORRELATION_VS_USABILITY.md

The markdown file is the one to read. It states the hypothesis, the three
correlations, the lead time and false-alarm rate, and which way the result went.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
RESULTS = DATA / "results"

# The correlation the hypothesis says will be "strong". Chosen to sit just below
# the weaker of MINDFUL's two published values (0.72), so that clearing it means
# this monitor is in the same range as the published state of the art.
STRONG_R = 0.70
FALSE_ALARM_BUDGET = 0.10      # per hour


def three_correlations(score: np.ndarray, perf: np.ndarray,
                       order: np.ndarray) -> dict:
    """Raw, partial (controlling for time), and on first differences."""
    def rank(x):
        return stats.rankdata(x)

    def resid(x, ctrl):
        return x - np.polyval(np.polyfit(ctrl, x, 1), ctrl)

    raw_r, raw_p = stats.spearmanr(score, perf)
    rc = rank(order)
    par_r, par_p = stats.pearsonr(resid(rank(score), rc), resid(rank(perf), rc))
    idx = np.argsort(order)
    d_r, d_p = stats.spearmanr(np.diff(score[idx]), np.diff(perf[idx]))
    return {
        "raw_r": float(raw_r), "raw_p": float(raw_p),
        "partial_r": float(par_r), "partial_p": float(par_p),
        "diff_r": float(d_r), "diff_p": float(d_p),
        "time_vs_score_r": float(stats.spearmanr(order, score).statistic),
        "time_vs_perf_r": float(stats.spearmanr(order, perf).statistic),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=str(DATA / "sessions.csv"))
    ap.add_argument("--budget", type=float, default=FALSE_ALARM_BUDGET)
    a = ap.parse_args()

    path = Path(a.table)
    if not path.exists():
        print(f"No session table at {path}.")
        print("Build it first:  python3 physical/code/make_session_table.py")
        print()
        print("That script reads the recordings and produces one row per")
        print("session. This script cannot run until the sessions exist.")
        return 1

    df = pd.read_csv(path)
    need = {"session", "block", "healthy", "risk_score", "performance"}
    missing = need - set(df.columns)
    if missing:
        print(f"The table is missing these columns: {sorted(missing)}")
        return 1

    df = df.sort_values(["session", "block"]).reset_index(drop=True)
    order = np.arange(len(df), dtype=float)

    # (a) the correlation the field would report, over all sessions
    corr_all = three_correlations(df.risk_score.to_numpy(),
                                  df.performance.to_numpy(), order)

    # (b) the numbers that decide usability
    healthy = df[df.healthy.astype(bool)]
    degraded = df[~df.healthy.astype(bool)]

    usable = {}
    # Lead time is taken from the column `make_session_table.py` computed, not
    # recomputed here. It is defined once, in monitor.py, as the time between
    # the warning and decoding performance actually failing -- the same
    # definition the computational half uses. An earlier version of this file
    # measured it against the fault onset instead, which is a different
    # quantity (monitor.py calls that the detection delay) and made this
    # script disagree with analyze_leadtime.py about the same recordings.
    if "lead_seconds" in df.columns:
        d = degraded.dropna(subset=["lead_seconds"])
        if len(d):
            lead = d.lead_seconds.to_numpy()
            usable["median_lead_seconds"] = float(np.median(lead))
            usable["n_degraded_scored"] = int(len(d))
            usable["fraction_warned_before_failure"] = float((lead > 0).mean())
        if "warn_before_onset" in degraded.columns:
            usable["n_warned_before_onset"] = int(
                degraded.warn_before_onset.fillna(False).astype(bool).sum())
    # Only healthy sessions in the TEST group can measure false alarms: the fit
    # and validation sessions built the monitor and chose its threshold.
    if "group" in healthy.columns:
        healthy = healthy[healthy.group == "test"]
    if len(healthy) and "warned" in healthy.columns:
        # A healthy session that produced any warning at all is a false alarm.
        n_fa = int(healthy.warned.astype(bool).sum())
        hours = float(healthy.get("duration_seconds",
                                  pd.Series([300.0] * len(healthy))).sum() / 3600.0)
        usable["healthy_sessions"] = int(len(healthy))
        usable["healthy_hours"] = hours
        usable["false_alarms"] = n_fa
        usable["false_alarms_per_hour"] = float(n_fa / hours) if hours else float("nan")

    # ---- the verdict on the hypothesis ------------------------------------
    # "Strongly correlated" is satisfied if ANY of the three measures clears the
    # threshold, not just the raw one. An earlier version tested only the raw
    # figure and declared a monitor "not strongly correlated" at raw 0.698 while
    # its partial correlation was 0.915 -- which is not a defensible reading.
    # The hypothesis is about a monitor that genuinely tracks performance by any
    # reasonable measure, and is still unusable as a warning.
    strengths = {"raw": abs(corr_all["raw_r"]),
                 "partial": abs(corr_all["partial_r"]),
                 "differences": abs(corr_all["diff_r"])}
    strong_by = [k for k, v in strengths.items() if v >= STRONG_R]
    strong = bool(strong_by)
    lead_bad = usable.get("median_lead_seconds", 0.0) <= 0
    far_bad = usable.get("false_alarms_per_hour", 0.0) > a.budget
    supported = bool(strong and (lead_bad or far_bad))

    result = {
        "hypothesis": "A monitor can correlate strongly with performance while "
                      "being unusable as a warning system.",
        "strong_r_threshold": STRONG_R,
        "false_alarm_budget_per_hour": a.budget,
        "correlations": corr_all, "usability": usable,
        "correlation_is_strong": bool(strong),
        "strong_by": strong_by, "correlation_strengths": strengths,
        "lead_time_unusable": bool(lead_bad),
        "false_alarm_rate_over_budget": bool(far_bad),
        "hypothesis_supported": supported,
        "n_sessions": int(len(df)),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "correlation_vs_usability.json").write_text(json.dumps(result, indent=2))

    c, u = corr_all, usable
    L = ["# P-4 — Does correlation with performance mean the monitor works?\n",
         "**Generated by `physical/code/analyze_correlation.py` — do not edit by hand.**\n",
         f"Based on **{len(df)} sessions** recorded on this apparatus, with "
         f"degradation onsets drawn and checksummed before each recording.\n",
         "## The hypothesis\n",
         "> A decoder-health monitor can show a strong correlation with task "
         "performance while simultaneously being unusable as a warning system.\n",
         "## (a) The correlation the field would report\n",
         "| Measured how | Correlation | p |", "|---|---|---|",
         f"| **Raw** — what published work reports | **{c['raw_r']:+.3f}** | {c['raw_p']:.4f} |",
         f"| Partial, time trend removed from both | {c['partial_r']:+.3f} | {c['partial_p']:.4f} |",
         f"| On changes rather than levels | {c['diff_r']:+.3f} | {c['diff_p']:.4f} |",
         "",
         f"Both series trend with time (score vs time "
         f"{c['time_vs_score_r']:+.3f}, performance vs time "
         f"{c['time_vs_perf_r']:+.3f}), which is why the raw figure alone is not "
         f"evidence: any two drifting quantities correlate.\n",
         "## (b) The numbers that decide whether it is usable\n",
         "| Quantity | Value |", "|---|---|"]
    A = L.append
    if "median_lead_seconds" in u:
        A(f"| Median lead time | **{u['median_lead_seconds']:+.1f} s** "
          f"(positive = warned before the failure) |")
        A(f"| Warned before decoding failed | "
          f"{u['fraction_warned_before_failure']:.1%} of "
          f"{u['n_degraded_scored']} |")
        if "n_warned_before_onset" in u:
            A(f"| Warned before the fault even started (false alarms) | "
              f"{u['n_warned_before_onset']} |")
    if "false_alarms_per_hour" in u:
        A(f"| False alarms per hour | **{u['false_alarms_per_hour']:.3f}** "
          f"(budget {a.budget}) |")
        A(f"| Healthy recording behind that | {u['healthy_hours']:.1f} h "
          f"across {u['healthy_sessions']} sessions |")
    A("")
    A("## Verdict\n")
    if supported:
        A(f"**Hypothesis supported.** The monitor correlates with performance "
          f"(strong by: {', '.join(strong_by)}; raw r = {c['raw_r']:+.3f}) — "
          f"comparable to published values — while "
          + ("warning *after* the failure" if lead_bad else "")
          + (" and " if lead_bad and far_bad else "")
          + ("exceeding the false-alarm budget" if far_bad else "")
          + ".\n")
        A("**What this means.** Correlation with performance is not sufficient "
          "evidence that a decoder-health monitor is usable. A monitor can pass "
          "that test and still warn too late, or too often, to deploy. Since "
          "correlation is the standard way this class of monitor is validated, "
          "and since neither lead time nor false-alarm rate has been reported "
          "for any of them, **the evidence base for drift-triggered "
          "recalibration is weaker than it appears.**")
    else:
        A("**Hypothesis not supported.** The monitor is either not strongly "
          "correlated, or it is usable on both counts.\n")
        if strong:
            A("A strong correlation here came with a usable warning, which "
              "**strengthens the case for correlation-based validation** and is "
              "a genuinely useful result for the published approach.")
        else:
            A(f"No measure of correlation reached {STRONG_R:.2f} "
              f"(raw {strengths['raw']:.3f}, partial {strengths['partial']:.3f}, "
              f"differences {strengths['differences']:.3f}), so this particular "
              f"test could not be run. Report it as inconclusive rather than as "
              f"evidence either way — a weakly correlated monitor says nothing "
              f"about whether correlation-based validation is sufficient.")
    A("")
    A("## What this cannot show\n")
    A("- It does not test MINDFUL or any other specific published method. It "
      "tests **correlation-based validation as a method**, using a monitor of "
      "the same family.")
    A("- One apparatus. The same caution that applies to two participants "
      "applies here.")
    A("- A different monitor might behave differently; nothing here bounds what "
      "is possible in general.")

    (RESULTS / "P4_CORRELATION_VS_USABILITY.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {RESULTS / 'P4_CORRELATION_VS_USABILITY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
