#!/usr/bin/env python3
"""
analyze_leadtime.py — experiment P-3: how early does the warning come?

=============================================================================
THE MEASUREMENT THIS APPARATUS EXISTS TO MAKE
=============================================================================
On an archived human recording, nobody wrote down when the electrodes started
going bad. So "how early did the monitor warn?" has no fixed answer there: it
depends on which moment the analyst decides to call the start, and two analysts
get two answers from the same recording.

Here the moment was drawn at random and locked under a checksum **before the
recording existed** (`draw_onset.py`). Nothing about it can be adjusted
afterwards to flatter a result, and someone who does not trust the experimenter
can verify the checksum.

=============================================================================
THREE DIFFERENT THINGS, KEPT APART
=============================================================================
    detection delay   warning time minus the drawn onset.
                      "How long did it take to notice?"
                      **New here.** Not computable on archived recordings.

    lead time         performance failure time minus warning time.
                      "How much warning before the decoder became unusable?"
                      Positive means the warning came first. Defined exactly
                      as in the computational half, so the two compare.

    detection rate    the share of degraded sessions warned about at all.

A monitor can be slow to notice and still give useful warning, if the decoder
keeps working for a while after the fault starts. It can also be fast and
useless, if performance collapses immediately. Reporting one number would hide
that, so all three are reported.

=============================================================================
TWO KINDS OF SESSION THAT ARE NOT DETECTIONS, AND MUST NOT BE COUNTED AS ONE
=============================================================================
**Warned before the fault began.** The warning window ends before the onset, so
it contains no faulty data at all. However early it looks, it is a false alarm
that happened to land inside a degraded session. Counting these as detections
is the easiest available way to manufacture a positive result, so they are
counted separately and excluded from every timing figure.

**The fault never broke anything.** Some degradations — especially mild ones —
are imposed and decoding carries on regardless. There is no failure to have led,
so lead time is undefined. These are reported in their own row rather than
dropped, because "the monitor warned about something that turned out not to
matter" is itself a false alarm from the user's point of view.

=============================================================================
A WARNING NEVER STANDS ALONE
=============================================================================
Lead time can be made arbitrarily long by lowering the threshold until the
monitor warns constantly. So this script always prints the false-alarm rate
from P-2 beside the lead time, measured at the same threshold. **Neither number
means anything without the other**, and reporting lead time alone is the
failure mode this project has been most careful to avoid.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/make_session_table.py    # first
    python3 physical/code/analyze_leadtime.py

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/results/lead_time.json
    physical/data/results/P3_LEAD_TIME.md
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import monitor as M

DATA = M.DATA
RESULTS = DATA / "results"


def median_ci(x: np.ndarray, reps: int = 5000, seed: int = 0) -> tuple:
    """Median with a bootstrap interval. Returns NaNs rather than a fake number."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return (float(np.median(x)) if len(x) else float("nan"),
                float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    b = np.median(rng.choice(x, (reps, len(x))), axis=1)
    return float(np.median(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def describe(d: pd.DataFrame) -> dict:
    """The three numbers for one group of degraded sessions."""
    n = len(d)
    early = int(d.warn_before_onset.sum())
    detected = d[d.warned & ~d.warn_before_onset]
    broke = detected[detected.fail_seconds.notna()]
    dm, dlo, dhi = median_ci(detected.detect_seconds.to_numpy())
    lm, llo, lhi = median_ci(broke.lead_seconds.to_numpy())
    return {
        "n_sessions": n,
        "n_detected": int(len(detected)),
        "detection_rate": float(len(detected) / n) if n else float("nan"),
        "n_warned_before_onset": early,
        "n_with_performance_failure": int(len(broke)),
        "median_detection_delay_s": dm, "detection_delay_ci95": [dlo, dhi],
        "median_lead_s": lm, "lead_ci95": [llo, lhi],
        "fraction_warned_before_failure": (float((broke.lead_seconds > 0).mean())
                                           if len(broke) else float("nan")),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    table = DATA / f"sessions{a.tag}.csv"
    if not table.exists():
        print(f"No session table at {table}.")
        print("Build it first:  python3 physical/code/make_session_table.py")
        return 1
    df = pd.read_csv(table)
    meta_file = DATA / "processed" / f"table_meta{a.tag}.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    fa_file = RESULTS / f"false_alarm{a.tag}.json"
    fa = json.loads(fa_file.read_text()) if fa_file.exists() else None

    deg = df[~df.healthy.astype(bool) & (df.kind != "calibration")].copy()
    if not len(deg):
        print("No degraded sessions in the table. Record some with:")
        print("    python3 physical/code/run_campaign.py plan --session 20 "
              "--degraded 101")
        return 1

    overall = describe(deg)
    by_type = {t: describe(d) for t, d in deg.groupby("fault_type") if len(d)}
    by_sev = {str(s): describe(d) for s, d in deg.groupby("severity") if len(d)}

    result = {"experiment": "P-3",
              "detector": meta.get("detector"), "decoder": meta.get("decoder"),
              "warn_threshold": meta.get("warn_threshold"),
              "overall": overall, "by_fault_type": by_type,
              "by_severity": by_sev,
              "false_alarms_per_hour": (fa or {}).get("false_alarms_per_hour"),
              "false_alarm_upper_bound": (fa or {}).get(
                  "zero_event_upper_bound_per_hour"),
              "false_alarm_hours": (fa or {}).get("healthy_test_hours")}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"lead_time{a.tag}.json").write_text(json.dumps(result, indent=2))

    # ------------------------------------------------------------- report
    o = overall
    L = ["# P-3 — How early does the monitor warn?\n",
         "**Generated by `physical/code/analyze_leadtime.py` — "
         "do not edit by hand.**\n",
         f"Measured on **{o['n_sessions']} degraded sessions**, each with an "
         f"onset drawn at random and checksummed before the recording existed.\n"]
    A = L.append

    A("## The pair\n")
    A("Lead time and false-alarm rate are reported together, always. Either can "
      "be made to look excellent by sacrificing the other.\n")
    A("| Quantity | Value |")
    A("|---|---|")
    A(f"| Faults detected | **{o['n_detected']} of {o['n_sessions']}** "
      f"({o['detection_rate']:.0%}) |")
    def with_ci(value, ci, n):
        # An interval from fewer than three sessions would be invented rather
        # than estimated, so it is left out and the count is shown instead.
        if np.isfinite(ci[0]) and np.isfinite(ci[1]):
            return f"**{value:+.0f} s** (95% CI {ci[0]:.0f} to {ci[1]:.0f})"
        return f"**{value:+.0f} s** (no interval — only {n} sessions)"

    if np.isfinite(o["median_detection_delay_s"]):
        A(f"| Time to notice, after the fault began | "
          + with_ci(o["median_detection_delay_s"], o["detection_delay_ci95"],
                    o["n_detected"]) + " |")
    if np.isfinite(o["median_lead_s"]):
        A(f"| Lead time before decoding failed | "
          + with_ci(o["median_lead_s"], o["lead_ci95"],
                    o["n_with_performance_failure"]) + " |")
        A(f"| Warned before the failure | "
          f"{o['fraction_warned_before_failure']:.0%} of "
          f"{o['n_with_performance_failure']} sessions where decoding did fail |")
    else:
        A("| Lead time | not computable — see below |")
    if fa:
        if fa.get("false_alarms"):
            A(f"| False alarms, same threshold | "
              f"**{fa['false_alarms_per_hour']:.3f} per hour** over "
              f"{fa['healthy_test_hours']:.2f} healthy hours |")
        else:
            A(f"| False alarms, same threshold | **0** in "
              f"{fa['healthy_test_hours']:.2f} healthy hours "
              f"(95% upper bound {fa['zero_event_upper_bound_per_hour']:.2f}/h) |")
    else:
        A("| False alarms | **not measured — run analyze_falsealarm.py** |")
    A("")

    A("## Sessions that are not detections\n")
    A("| Category | Sessions | Why it is not a detection |")
    A("|---|---|---|")
    A(f"| Warned before the fault started | {o['n_warned_before_onset']} | "
      f"The warning window ends before the onset, so it contains no faulty "
      f"data. It is a false alarm inside a degraded session. |")
    never = o["n_detected"] - o["n_with_performance_failure"]
    A(f"| Fault imposed, decoding never failed | {never} | "
      f"There is no failure to have warned about, so lead time is undefined. |")
    A(f"| Never warned | {o['n_sessions'] - o['n_detected'] - o['n_warned_before_onset']} | "
      f"The monitor missed the fault entirely. |")
    A("")

    def table(title: str, groups: dict, head: str):
        A(f"## {title}\n")
        A(f"| {head} | Sessions | Detected | Time to notice | Lead time |")
        A("|---|---|---|---|---|")
        for k, g in sorted(groups.items()):
            dd = (f"{g['median_detection_delay_s']:+.0f} s"
                  if np.isfinite(g["median_detection_delay_s"]) else "—")
            ll = (f"{g['median_lead_s']:+.0f} s"
                  if np.isfinite(g["median_lead_s"]) else "—")
            A(f"| {k} | {g['n_sessions']} | "
              f"{g['n_detected']} ({g['detection_rate']:.0%}) | {dd} | {ll} |")
        A("")

    table("By fault type", by_type, "Fault")
    table("By severity", by_sev, "Severity")
    A("A difference between fault types is a more useful result than a single "
      "average. If some kinds of failure are catchable and others are not, "
      "that tells a designer which ones need a different approach — and it is "
      "invisible in a pooled number.\n")

    A("## Reading these numbers honestly\n")
    A(f"- A warning is timestamped at the **end** of the window that produced "
      f"it, because that is the earliest moment its score could have been "
      f"computed. Windows are {M.WINDOW_FRAMES / M.FPS:.0f} seconds long and "
      f"start every {M.STEP_FRAMES / M.FPS:.0f} seconds, so a fault first "
      f"appears in a window that is only partly faulty. A detection delay "
      f"shorter than {M.WINDOW_FRAMES / M.FPS:.0f} seconds therefore means the "
      f"fault was strong enough to move a window it only partly occupied — it "
      f"is not an error. What the windowing does set is the **resolution**: "
      f"delays and lead times can only be resolved to about "
      f"{M.STEP_FRAMES / M.FPS:.0f} seconds, so differences smaller than that "
      f"are not real.")
    A("- Lead time is measured against decoding performance crossing its own "
      "pre-onset baseline by 10 degrees — the threshold fixed in "
      "`scripts/17_fault_injector.py` before any detector existed, and reused "
      "unchanged here.")
    A("- The warning threshold was chosen on held-out healthy sessions to meet "
      "the false-alarm budget, then applied here without adjustment. It was "
      "not tuned on these recordings.")
    A("- Median rather than mean throughout: a single session where the "
      "monitor never warned would otherwise dominate the average.")

    (RESULTS / f"P3_LEAD_TIME{a.tag}.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {RESULTS / f'P3_LEAD_TIME{a.tag}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
