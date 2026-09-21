#!/usr/bin/env python3
"""
analyze_decision_rate.py — experiment P-6: how often should a monitor decide?

=============================================================================
THE QUESTION
=============================================================================
The computational half of this project produced a monitor that failed, and the
reason turned out to have little to do with the detector. It was being asked to
make a decision **every five seconds** — 720 decisions an hour. Spread a budget
of 0.1 false alarms per hour across 720 decisions and each one is allowed a
false-positive rate of 0.00014. A detector needs to be almost perfect to work
at that operating point, and almost perfect is not available.

So: what if it decided less often?

Deciding less often should help in two separate ways.

1. **A looser budget per decision.** Twelve decisions an hour rather than 720
   means each is allowed 0.0083 instead of 0.00014 — sixty times as much room.
2. **More evidence behind each decision.** A decision covering five minutes has
   sixty windows behind it instead of one.

If that holds, there is a design rule for monitoring any drifting many-channel
sensor: *check this often, and no more often.* The rule would apply well beyond
brain implants.

=============================================================================
WHY IT COULD NOT BE SETTLED COMPUTATIONALLY
=============================================================================
On the archived data the two participants **disagree about which way the curve
goes** — detection rising 11.5% on one and falling 18.2% on the other — with
confidence intervals spanning 62% to 99%. The thresholds rest on 29 and 21
fault-free sessions, which is not enough to place them. The question is real
and the data cannot answer it.

This apparatus can record as many fault-free sessions as the calendar allows,
which is the only thing that would settle it.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
It re-scores recordings that already exist, at every decision rate from one
decision per window down to one per session. **No extra recording is needed**,
because the decision rate is a choice made in analysis, not in the apparatus.

At each rate:

1. Windows are pooled into blocks, one decision per block.
2. A fresh threshold is chosen **on the held-out healthy sessions**, to meet
   the same false-alarm budget per hour at that rate.
3. Detection is measured on the degraded sessions at that threshold.

Step 2 is what makes the comparison fair. Comparing decision rates at a fixed
threshold would just be comparing how often the statistic is sampled; the whole
point is that each rate gets the best threshold available to it, and they are
then compared at equal false-alarm cost.

=============================================================================
A MISTAKE THIS SCRIPT EXISTS NOT TO REPEAT
=============================================================================
An earlier version of this test, on the computational data, scored "one
decision per session" by taking the session's **first window** instead of
pooling the session. That is not a slower decision — it is the same fast
decision with less data — and it produced a fake collapse in detection that
looked like a finding. The pooling is the entire mechanism being tested, so it
is done explicitly here, and `--aggregate` names which pooling is in use.

The default is the **mean** of the windows in the block. Taking the maximum
would be tempting and wrong: the maximum of a block is just a rescaled
threshold, so it delivers none of the evidence-pooling the hypothesis is about.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/make_session_table.py     # first
    python3 physical/code/analyze_decision_rate.py

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/results/decision_rate.json
    physical/data/results/P6_DECISION_RATE.md
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from scipy import stats

import monitor as M

DATA = M.DATA
RESULTS = DATA / "results"
STEP_SECONDS = M.STEP_FRAMES / M.FPS          # 5 s -> 720 decisions per hour

AGGREGATORS = {"mean": np.mean, "median": np.median, "max": np.max}


def blocks(n_windows: int, k: int) -> list[slice]:
    return [slice(i, min(i + k, n_windows)) for i in range(0, n_windows, k)]


def decisions(risk: np.ndarray, ends: np.ndarray, k: int, agg) -> tuple:
    """Pool windows into blocks. Returns one statistic and one time per block."""
    stat, when = [], []
    for sl in blocks(len(risk), k):
        stat.append(float(agg(risk[sl])))
        when.append(float(ends[sl][-1]))
    return np.array(stat), np.array(when)


def threshold_for(healthy: list[np.ndarray], hours: float, budget: float) -> float:
    """Lowest threshold whose alarm count on healthy sessions fits the budget."""
    allowed = budget * hours
    for t in M.harness.THRESHOLD_GRID:
        n = sum(int((s >= t).any()) for s in healthy)
        if n <= allowed:
            return float(t)
    return float(M.harness.THRESHOLD_GRID[-1])


def wilson(k: int, n: int) -> tuple[float, float]:
    """Interval for a proportion that behaves sensibly at 0 and at 1."""
    if n == 0:
        return float("nan"), float("nan")
    z = stats.norm.ppf(0.975)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(max(0.0, c - h)), float(min(1.0, c + h))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="")
    ap.add_argument("--budget", type=float, default=M.FALSE_ALARM_BUDGET_PER_HOUR)
    ap.add_argument("--aggregate", default="mean", choices=sorted(AGGREGATORS))
    a = ap.parse_args()

    table = DATA / f"sessions{a.tag}.csv"
    if not table.exists():
        print(f"No session table at {table}.")
        print("Build it first:  python3 physical/code/make_session_table.py")
        return 1
    df = pd.read_csv(table)
    W = DATA / "processed" / "windows"
    agg = AGGREGATORS[a.aggregate]

    def load(rows):
        out = []
        for _, r in rows.iterrows():
            f = W / f"{r.folder}{a.tag}.npz"
            if f.exists():
                z = np.load(f)
                out.append((r, z["risk"], z["window_end_seconds"]))
        return out

    val = load(df[(df.group == "val") & df.healthy.astype(bool)])
    test = load(df[(df.group == "test") & df.healthy.astype(bool)])
    deg = load(df[~df.healthy.astype(bool) & (df.kind != "calibration")])
    if not val or not deg:
        print("Need healthy validation sessions and degraded sessions. Have "
              f"{len(val)} and {len(deg)}.")
        return 1

    val_hours = sum(r.duration_seconds for r, _, _ in val) / 3600
    test_hours = sum(r.duration_seconds for r, _, _ in test) / 3600
    max_windows = max(len(risk) for _, risk, _ in val + deg)

    # Block sizes from one window per decision up to a whole session.
    ks = sorted({1, 2, 3, 6, 12, 24, max_windows})
    ks = [k for k in ks if k <= max_windows]

    rows = []
    for k in ks:
        rate = 3600.0 / (k * STEP_SECONDS)
        t = threshold_for([decisions(r_, e, k, agg)[0] for _, r_, e in val],
                          val_hours, a.budget)

        hit, early = 0, 0
        for r, risk, ends in deg:
            stat, when = decisions(risk, ends, k, agg)
            above = np.flatnonzero(stat >= t)
            if not len(above):
                continue
            first = when[above[0]]
            if np.isfinite(r.onset_seconds) and first <= r.onset_seconds:
                early += 1          # warned before the fault: a false alarm
            else:
                hit += 1
        lo, hi = wilson(hit, len(deg))

        fa = sum(int((decisions(r_, e, k, agg)[0] >= t).any()) for _, r_, e in test)
        rows.append({
            "windows_per_decision": int(k),
            "decisions_per_hour": round(rate, 2),
            "seconds_per_decision": round(k * STEP_SECONDS, 1),
            "per_decision_fpr_allowed": a.budget / rate,
            "threshold": t,
            "n_degraded": len(deg), "n_detected": hit,
            "detection_rate": hit / len(deg),
            "detection_ci95": [lo, hi],
            "n_warned_before_onset": early,
            "false_alarms_in_test": fa,
            "false_alarms_per_hour": fa / test_hours if test_hours else None,
        })

    best = max(rows, key=lambda r: r["detection_rate"])
    fastest, slowest = rows[0], rows[-1]
    change = slowest["detection_rate"] - fastest["detection_rate"]
    # "Settled" means the two ends' intervals do not overlap. With the session
    # counts this phase can reach, that is a real possibility rather than a
    # formality -- and if they do overlap, the honest answer is that it is still
    # open, which is what the computational half had to say.
    separated = (fastest["detection_ci95"][1] < slowest["detection_ci95"][0] or
                 slowest["detection_ci95"][1] < fastest["detection_ci95"][0])

    result = {"experiment": "P-6", "aggregate": a.aggregate,
              "budget_per_hour": a.budget,
              "validation_hours": val_hours, "test_healthy_hours": test_hours,
              "curve": rows, "best": best,
              "change_slowest_minus_fastest": change,
              "intervals_separated": bool(separated)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"decision_rate{a.tag}.json").write_text(json.dumps(result, indent=2))

    # ------------------------------------------------------------- report
    L = ["# P-6 — How often should the monitor decide?\n",
         "**Generated by `physical/code/analyze_decision_rate.py` — "
         "do not edit by hand.**\n",
         f"Every row below is the **same recordings**, re-scored at a different "
         f"decision rate. No extra sessions were needed. "
         f"{len(deg)} degraded sessions, {len(test)} held-out healthy "
         f"({test_hours:.2f} h), pooled by **{a.aggregate}**.\n",
         "| Decisions/hour | Seconds each | FPR allowed per decision | "
         "Threshold | Detected | 95% CI | False alarms/h |",
         "|---|---|---|---|---|---|---|"]
    A = L.append
    for r in rows:
        far = (f"{r['false_alarms_per_hour']:.2f}"
               if r["false_alarms_per_hour"] is not None else "—")
        A(f"| {r['decisions_per_hour']:.0f} | {r['seconds_per_decision']:.0f} | "
          f"{r['per_decision_fpr_allowed']:.2e} | {r['threshold']:.3g} | "
          f"{r['detection_rate']:.0%} ({r['n_detected']}/{r['n_degraded']}) | "
          f"{r['detection_ci95'][0]:.0%}–{r['detection_ci95'][1]:.0%} | {far} |")
    A("")

    A("## Which way does it go?\n")
    direction = ("**rises**" if change > 0 else
                 "**falls**" if change < 0 else "**is flat**")
    A(f"From {fastest['decisions_per_hour']:.0f} decisions an hour to "
      f"{slowest['decisions_per_hour']:.1f}, detection {direction} by "
      f"**{abs(change):.1%}** "
      f"({fastest['detection_rate']:.0%} to {slowest['detection_rate']:.0%}), "
      f"at equal false-alarm cost.\n")

    if not separated:
        A("**The intervals overlap, so this does not settle the question.** "
          "That is the same position the computational half was left in, and "
          "saying so is the only honest reading. More sessions — degraded ones "
          "especially — would narrow the intervals; nothing else will.\n")
    elif change > 0:
        A("**Deciding less often genuinely helps**, and the intervals do not "
          "overlap. Both proposed mechanisms point this way: a looser budget "
          "per decision, and more evidence behind each one. This supports a "
          "design rule for monitoring any drifting many-channel sensor — check "
          "on the timescale the failure develops over, and no faster. The "
          "extra checks are not free; they are paid for in false alarms.\n")
    else:
        A("**Deciding less often makes things worse**, and the intervals do "
          "not overlap. Pooling destroys more than the looser budget buys, "
          "which means the correct design move is the opposite of the obvious "
          "one. This is the more surprising outcome and the more useful one: "
          "it says the limitation is in what the statistic can see, not in how "
          "often it is consulted.\n")

    A(f"The best rate tested is **{best['decisions_per_hour']:.0f} decisions "
      f"an hour** (one every {best['seconds_per_decision']:.0f} seconds), at "
      f"{best['detection_rate']:.0%} detection.\n")

    A("## How to read the FPR column\n")
    A("It is the false-positive rate each individual decision is allowed, if "
      "the whole system is to stay inside "
      f"{a.budget} false alarms an hour. At 720 decisions an hour that is "
      "0.00014 — a detector would need an AUC of about 0.9992 to manage it. "
      "At one decision per five-minute session it is 0.0083, needing about "
      "0.990. **That column, not the detector, is where the computational "
      "monitor actually failed.**\n")
    A("Both of those are a long way above the 0.673 and 0.742 the computational "
      "monitor achieved, so deciding less often is not on its own a rescue — "
      "the looseness it buys is exactly the pooling factor, no more. What the "
      "curve above measures is whether the *second* mechanism, more evidence "
      "behind each decision, adds anything beyond that. **That is the open "
      "question, and it is why this is measured rather than argued.**\n")

    A("## What this cannot show\n")
    A("- Every row uses the same recordings, so the rows are not independent. "
      "The comparison between them is fair; treating each as a separate "
      "experiment would not be.")
    A(f"- The slowest rate here is one decision per session "
      f"({slowest['seconds_per_decision'] / 60:.0f} minutes). Anything slower "
      f"would need longer recordings, not more of them.")
    A("- Pooling by mean is one choice among several. `--aggregate median` and "
      "`--aggregate max` are available; max is included only to show that it "
      "delivers no pooling benefit, which is the point of not using it.")

    (RESULTS / f"P6_DECISION_RATE{a.tag}.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {RESULTS / f'P6_DECISION_RATE{a.tag}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
