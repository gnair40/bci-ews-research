#!/usr/bin/env python3
"""
analyze_falsealarm.py — experiment P-2: how often does it cry wolf?

=============================================================================
WHAT THIS MEASURES, AND WHY IT IS THE CENTRE OF THE PHASE
=============================================================================
A monitor that warns when nothing is wrong is worse than no monitor, because
people stop listening to it. So the question "how often does it warn during
completely normal operation?" has to be answered before "how early does it
warn?" is worth asking at all.

**Nobody has been able to answer it for a brain-implant decoder-health monitor.**
The archived human recordings contain about 1.4 hours that are genuinely
fault-free. A budget of one false alarm per ten hours cannot be checked against
1.4 hours of evidence, by anyone, ever. That is not a criticism of the people
who collected those recordings — it is a limit of what recording sessions with
a human participant can produce.

This apparatus can run all night, so it can.

=============================================================================
THE TWO NUMBERS, AND THE DIFFERENCE BETWEEN THEM
=============================================================================
If the monitor produces some false alarms, there is a **rate**: alarms divided
by hours, with a confidence interval.

If it produces none, there is no rate — there is an **upper bound**. Seeing
zero events in H hours does not mean the true rate is zero; it means the true
rate is probably below about 3/H per hour (the "rule of three", the standard
way to bound a rate from no events). With 4 hours of recording, "zero false
alarms" supports a bound of 0.75 per hour, which is seven times the budget.

**Reporting "zero false alarms" without the bound would be the single most
misleading thing this project could do**, because it sounds like the strongest
possible result and is, on a short recording, almost no result at all. The
script therefore always prints the bound, and the number of hours still needed.

=============================================================================
THE SILENCE GATE
=============================================================================
Separately from counting alarms, there is a stricter question: on a healthy
session, does the monitor's risk score **drift upward at all**?

A score that climbs steadily through every healthy session will eventually
cross any threshold. It may not have crossed it yet in a five-minute recording,
but the monitor is on its way to alarming for reasons that have nothing to do
with the decoder. The gate tests each healthy session for a monotonic trend
(Kendall's tau) and requires that no more than 10% of sessions show a
significant one.

This is the same gate, with the same 10% bar, that the computational half
applied — and **failed**, on fault-free neural data. Whether it fails here too
is one of the genuinely open questions of this phase. If it passes, the
computational failure is specific to neural recordings. If it fails, the
limitation is more general than one dataset.

The gate is run twice: on the risk score as it comes, and after removing a
linear trend. If silence only survives detrending, that is worth knowing, and
it is reported separately rather than merged.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/make_session_table.py     # first
    python3 physical/code/analyze_falsealarm.py

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/results/false_alarm.json
    physical/data/results/P2_FALSE_ALARM_RATE.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import monitor as M

DATA = M.DATA
RESULTS = DATA / "results"
RULE_OF_THREE = 3.0
SILENCE_BAR = 0.10          # at most 10% of healthy sessions may trend
ALPHA = 0.05


def poisson_ci(k: int, hours: float) -> tuple[float, float]:
    """95% interval for a rate, from k events in `hours` hours.

    Exact (Garwood) rather than the square-root approximation, because the
    counts here are small and the approximation is poor below about ten events.
    """
    if hours <= 0:
        return float("nan"), float("nan")
    lo = 0.0 if k == 0 else stats.chi2.ppf(0.025, 2 * k) / 2 / hours
    hi = stats.chi2.ppf(0.975, 2 * (k + 1)) / 2 / hours
    return float(lo), float(hi)


def linear_detrend(y: np.ndarray) -> np.ndarray:
    """Remove a straight line fitted to the WHOLE series.

    This is a diagnostic, not something a deployed monitor could do: it uses
    the end of the session to correct its beginning, which a live monitor does
    not have. It answers one narrow question — is the drift close enough to a
    straight line that subtracting one would fix it? — and the answer is only
    interesting if the gate fails without it.

    It is the same whole-series detrend the computational half used for this
    gate (`scripts/21_score_report.py`), not the causal pre-onset detrend used
    for lead time. Using one where the other belongs would make the two halves
    incomparable, so both are kept, separately named, and never mixed.
    """
    y = np.asarray(y, dtype=float)
    x = np.arange(len(y), dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 4:
        return y
    b, c = np.polyfit(x[ok], y[ok], 1)
    return y - (c + b * x)


def trend_fraction(series: list[np.ndarray]) -> dict:
    """Share of healthy sessions whose risk score climbs significantly."""
    taus, ps = [], []
    for y in series:
        y = np.asarray(y, dtype=float)
        if len(y) < 8:
            continue
        t, p = stats.kendalltau(np.arange(len(y)), y)
        if np.isfinite(t):
            taus.append(float(t))
            ps.append(float(p))
    if not ps:
        return {"n": 0, "fraction_significant": None, "median_tau": None,
                "pass": None}
    frac = float(np.mean(np.array(ps) < ALPHA))
    return {"n": len(ps), "fraction_significant": round(frac, 3),
            "median_tau": round(float(np.median(taus)), 3),
            "pass": bool(frac <= SILENCE_BAR)}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="")
    ap.add_argument("--budget", type=float, default=M.FALSE_ALARM_BUDGET_PER_HOUR)
    a = ap.parse_args()

    table = DATA / f"sessions{a.tag}.csv"
    meta_file = DATA / "processed" / f"table_meta{a.tag}.json"
    if not table.exists():
        print(f"No session table at {table}.")
        print("Build it first:  python3 physical/code/make_session_table.py")
        return 1
    df = pd.read_csv(table)
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}

    # Only healthy sessions in the TEST group. Sessions used to build the
    # monitor or to choose its threshold cannot also measure it.
    h = df[(df.group == "test") & df.healthy.astype(bool)]
    if not len(h):
        print("No healthy sessions in the test group, so there is nothing to")
        print("measure a false-alarm rate on. Record more healthy sessions.")
        return 1

    hours = float(h.duration_seconds.sum() / 3600)
    k = int(h.warned.sum())
    rate = k / hours if hours else float("nan")
    lo, hi = poisson_ci(k, hours)
    bound = RULE_OF_THREE / hours if hours else float("inf")
    needed = RULE_OF_THREE / a.budget

    # --- the silence gate, on the same sessions ---------------------------
    W = DATA / "processed" / "windows"
    raw_series, flat_series = [], []
    for name in h.folder:
        f = W / f"{name}{a.tag}.npz"
        if not f.exists():
            continue
        z = np.load(f)
        raw_series.append(z["risk"])
        flat_series.append(linear_detrend(z["risk"]))
    g1 = trend_fraction(raw_series)
    g5 = trend_fraction(flat_series)

    result = {
        "experiment": "P-2",
        "detector": meta.get("detector"), "decoder": meta.get("decoder"),
        "warn_threshold": meta.get("warn_threshold"),
        "budget_per_hour": a.budget,
        "healthy_test_sessions": int(len(h)),
        "healthy_test_hours": hours,
        "false_alarms": k,
        "false_alarms_per_hour": rate,
        "rate_ci95": [lo, hi],
        "zero_event_upper_bound_per_hour": bound if k == 0 else None,
        "hours_needed_for_budget": needed,
        "within_budget": bool(hi <= a.budget),
        "G1_silence": g1, "G5_detrend": g5,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"false_alarm{a.tag}.json").write_text(json.dumps(result, indent=2))

    # ------------------------------------------------------------- report
    L = ["# P-2 — How often does the monitor warn when nothing is wrong?\n",
         "**Generated by `physical/code/analyze_falsealarm.py` — "
         "do not edit by hand.**\n",
         f"Measured on **{len(h)} healthy sessions ({hours:.2f} hours)** that "
         f"were used neither to build the monitor nor to choose its warning "
         f"threshold.\n",
         "## The count\n",
         "| Quantity | Value |", "|---|---|",
         f"| Healthy sessions held out | {len(h)} |",
         f"| Hours of healthy recording | **{hours:.2f}** |",
         f"| False alarms | **{k}** |"]
    A = L.append
    if k:
        A(f"| False-alarm rate | **{rate:.3f} per hour** |")
        A(f"| 95% interval | {lo:.3f} to {hi:.3f} per hour |")
        A(f"| Budget | {a.budget} per hour |")
        A("")
        A(f"**The monitor {'meets' if hi <= a.budget else 'does not meet'} the "
          f"budget.** The upper end of the interval is what matters: a rate "
          f"that might be {hi:.3f} per hour has not been shown to be below "
          f"{a.budget}.")
    else:
        A(f"| 95% upper bound | **{bound:.2f} per hour** |")
        A(f"| Budget | {a.budget} per hour |")
        A("")
        A(f"**Zero false alarms is not the same as a rate of zero.** With "
          f"{hours:.2f} hours of held-out healthy recording, the most that can "
          f"be claimed is that the true rate is probably below "
          f"**{bound:.2f} per hour** (rule of three).")
        if bound > a.budget:
            short = needed - hours
            A("")
            A(f"That bound is **{bound / a.budget:.0f} times the "
              f"{a.budget}/hour budget**, so this recording does not yet show "
              f"the monitor meets it. Demonstrating the budget needs about "
              f"**{needed:.0f} hours** of held-out healthy recording — roughly "
              f"{short * 3600 / 300:.0f} more five-minute sessions, or "
              f"{short:.0f} more hours.")
            A("")
            A("This is a statement about how much evidence exists, not about "
              "the monitor. It is stated plainly because the alternative — "
              "reporting \"zero false alarms\" and stopping — would read as the "
              "strongest possible result while being nearly no result at all.")
        else:
            A("")
            A(f"That bound is **within the {a.budget}/hour budget**. This is, "
              f"as far as this project can establish, the first time a "
              f"decoder-health monitor has been shown to meet a stated "
              f"false-alarm budget on enough fault-free recording to support "
              f"the claim.")

    A("")
    A("## The silence gate\n")
    A("Counting alarms is not the whole question. A risk score that climbs "
      "steadily through every healthy session will cross any threshold "
      "eventually, even if it has not yet crossed this one. The gate tests "
      "each healthy session for a monotonic trend and allows at most 10% to "
      "show one.\n")
    A("| Version | Sessions | Median trend | Share trending | Gate |")
    A("|---|---|---|---|---|")
    for label, g in (("Risk score as measured", g1),
                     ("After removing a linear trend", g5)):
        if g["n"]:
            A(f"| {label} | {g['n']} | tau = {g['median_tau']:+.3f} | "
              f"{g['fraction_significant']:.1%} | "
              f"{'**PASS**' if g['pass'] else '**FAIL**'} |")
        else:
            A(f"| {label} | 0 | — | — | not testable |")
    A("")
    if g1["pass"] is True:
        A("**The gate passes.** On this apparatus the monitor stays flat "
          "during healthy operation. The computational half failed this same "
          "gate with the same 10% bar on fault-free neural recordings, so this "
          "result says the failure there was a property of those recordings "
          "rather than of the monitor — which is a more useful finding than "
          "either half produces alone.")
    elif g1["pass"] is False:
        A("**The gate fails**, as it did on the neural recordings. The risk "
          "score drifts upward during healthy operation on an apparatus with "
          "no brain in it, no electrodes, and nothing biological at all. That "
          "makes the computational failure much harder to blame on the "
          "recordings, and points at the monitoring approach itself.")
        if g5["pass"]:
            A("")
            A("Removing a linear trend rescues it. That is worth reporting: it "
              "says the drift is close to linear and can be subtracted — but a "
              "deployed monitor has to do that subtraction **causally**, from "
              "past windows only, which is harder than doing it afterwards "
              "with the whole session in hand.")
    else:
        A("*Not enough windows per session to test the gate.*")

    A("")
    A("## What this cannot show\n")
    A("- One apparatus, in one room. A false-alarm rate measured here does not "
      "transfer to an implanted array, and no claim is made that it does.")
    A("- The false-alarm rate depends on the warning threshold, which was "
      "chosen to meet this budget on held-out healthy sessions. A different "
      "budget gives a different threshold and a different rate. The pair is "
      "the result; neither number alone is.")
    A(f"- Sessions are {h.duration_seconds.median() / 60:.0f} minutes long. A "
      f"monitor that only misbehaves after an hour of continuous running would "
      f"not be caught here.")

    (RESULTS / f"P2_FALSE_ALARM_RATE{a.tag}.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {RESULTS / f'P2_FALSE_ALARM_RATE{a.tag}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
