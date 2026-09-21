#!/usr/bin/env python3
"""
analyze_apparatus.py — experiment P-7: is any of this a property of one box?

=============================================================================
WHY THIS EXISTS
=============================================================================
This project spends a great deal of effort pointing out that the archived
recordings come from **two participants**, that they disagree, and that a
conclusion drawn from two is fragile. It was then going to draw conclusions
from **one apparatus**, in one room, with one screen and one camera.

That is the same defect. Unlike the participant problem it is cheap to fix:
run a reduced campaign under several deliberately different configurations of
the apparatus and see whether the answers move.

=============================================================================
WHAT COUNTS AS A DIFFERENT CONFIGURATION
=============================================================================
Something that changes the apparatus while leaving the **task difficulty the
same**. Each configuration is re-calibrated to the 36.1° margin before use —
otherwise a difference in result is just a difference in how hard the job was,
which is the one confound this phase cannot afford.

    A   the calibrated baseline
    B   exposure doubled, modulation depth halved to compensate
    C   smaller patches, so fewer screen pixels average into each channel
    D   a coarser channel grid: 96 channels instead of 384

=============================================================================
THE TWO QUESTIONS, BOTH PREREGISTERED
=============================================================================
**PP-9 — does the decision-rate direction hold?** If deciding less often helps
(or hurts) because of something about monitoring drifting many-channel sensors,
the *sign* should not depend on the exposure or the channel count. If it flips,
the effect depends on something the design has not identified — which is a
finding, and a more interesting one.

**PP-10 — do the headline numbers move?** Lead time and false-alarm rate are
reported from one apparatus. If four configurations of the same box disagree,
those numbers are apparatus-specific and must be reported with their spread
rather than as a value.

**This experiment is designed to be able to embarrass the rest of the phase.**
That is its job.

=============================================================================
HOW TO RUN IT
=============================================================================
Each configuration is a separate apparatus and gets its **own** decoder,
threshold and reports — pooling them would average over the thing being varied.

    for C in A B C D; do
        python3 physical/code/make_session_table.py --config $C --tag _$C
        python3 physical/code/analyze_leadtime.py --tag _$C
        python3 physical/code/analyze_falsealarm.py --tag _$C
        python3 physical/code/analyze_decision_rate.py --tag _$C
    done
    python3 physical/code/analyze_apparatus.py --configs A,B,C,D

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/results/apparatus_variation.json
    physical/data/results/P7_APPARATUS_VARIATION.md
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import monitor as M

DATA = M.DATA
RESULTS = DATA / "results"

LEAD_MARGIN_S = 10.0      # PP-10: "differ by more than 10 seconds"
FAR_FACTOR = 2.0          # PP-10: "or by more than a factor of two"


def load_config(cfg: str) -> dict | None:
    """Everything already computed for one configuration."""
    tag = f"_{cfg}"
    table = DATA / f"sessions{tag}.csv"
    if not table.exists():
        return None
    df = pd.read_csv(table)
    out = {"config": cfg, "n_sessions": int(len(df))}

    meta = DATA / "processed" / f"table_meta{tag}.json"
    if meta.exists():
        m = json.loads(meta.read_text())
        out["threshold"] = m.get("warn_threshold")
        out["test_healthy_hours"] = m.get("test_healthy_hours")
        out["false_alarms"] = m.get("false_alarms_in_test")
        out["false_alarms_per_hour"] = m.get("false_alarms_per_hour")

    deg = df[~df.healthy.astype(bool) & (df.kind != "undesigned")]
    lead = deg.lead_seconds.dropna()
    out["median_lead_s"] = float(lead.median()) if len(lead) else float("nan")
    out["n_lead"] = int(len(lead))
    out["detection_rate"] = (float((deg.warned & ~deg.warn_before_onset).mean())
                             if len(deg) else float("nan"))
    out["margin_deg"] = float(df.margin_deg.median()) if "margin_deg" in df else float("nan")

    dr = RESULTS / f"decision_rate{tag}.json"
    if dr.exists():
        d = json.loads(dr.read_text())
        out["decision_change"] = d.get("change_slowest_minus_fastest")
        out["decision_separated"] = d.get("intervals_separated")
        curve = d.get("curve", [])
        if curve:
            out["decision_best_rate"] = d.get("best", {}).get("decisions_per_hour")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", default="A,B,C,D",
                    help="comma-separated configuration labels")
    ap.add_argument("--tag", default="", help="suffix for the output filenames")
    a = ap.parse_args()

    labels = [c.strip() for c in a.configs.split(",") if c.strip()]
    rows = [r for r in (load_config(c) for c in labels) if r]
    missing = [c for c in labels if c not in {r["config"] for r in rows}]
    if len(rows) < 2:
        print("Need at least two configurations with a session table.")
        print("Build each one first:")
        for c in labels:
            print(f"    python3 physical/code/make_session_table.py "
                  f"--config {c} --tag _{c}")
        return 1
    if missing:
        print(f"No session table for: {', '.join(missing)} — "
              f"reporting the {len(rows)} that exist.\n")

    # ---- PP-9: does the decision-rate direction hold? --------------------
    # A "change" of exactly zero is not evidence that the direction holds; it
    # is evidence of no direction. The first version of this dropped flat
    # configurations and then announced that all of them agreed -- computing a
    # unanimous verdict from a single configuration. A check that can report
    # agreement from one observation is worse than no check.
    FLAT = 0.02      # smaller than this is flat, not a direction
    signs, flat = {}, []
    for r in rows:
        ch = r.get("decision_change")
        if ch is None:
            signs[r["config"]] = None
        elif abs(ch) < FLAT:
            signs[r["config"]] = 0
            flat.append(r["config"])
        else:
            signs[r["config"]] = int(np.sign(ch))
    directed = {k: v for k, v in signs.items() if v not in (None, 0)}
    if len(directed) < 2:
        pp9_holds = None          # not enough configurations with a direction
    else:
        pp9_holds = len(set(directed.values())) == 1

    # ---- PP-10: do the headline numbers move? ----------------------------
    leads = [r["median_lead_s"] for r in rows if np.isfinite(r["median_lead_s"])]
    # `if r.get(...)` drops a rate of 0.0, which is the most informative value
    # there is -- a configuration that never alarms beside one that alarms six
    # times an hour is the biggest difference the experiment can find, and the
    # first version of this silently excluded it and then reported "no move".
    fars = [r["false_alarms_per_hour"] for r in rows
            if r.get("false_alarms_per_hour") is not None]
    lead_spread = (max(leads) - min(leads)) if len(leads) > 1 else float("nan")
    if len(fars) > 1:
        far_span = max(fars) - min(fars)
        far_ratio = (max(fars) / min(fars)) if min(fars) > 0 else float("inf")
    else:
        far_span = far_ratio = float("nan")
    # A ratio is undefined when one configuration alarms and another does not,
    # so the budget itself is the fallback yardstick.
    far_moves = bool(np.isfinite(far_span) and
                     (far_ratio > FAR_FACTOR or
                      far_span > M.FALSE_ALARM_BUDGET_PER_HOUR))
    pp10_moves = bool((np.isfinite(lead_spread) and lead_spread > LEAD_MARGIN_S)
                      or far_moves)

    result = {"experiment": "P-7", "configurations": rows,
              "PP9_direction_holds": pp9_holds, "PP9_signs": {k: (None if v is None else int(v)) for k, v in signs.items()},
              "PP10_numbers_move": pp10_moves,
              "PP9_flat_configs": flat,
              "lead_spread_seconds": lead_spread,
              "false_alarm_ratio": far_ratio,
              "false_alarm_span": far_span,
              "lead_margin_seconds": LEAD_MARGIN_S,
              "false_alarm_factor": FAR_FACTOR}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"apparatus_variation{a.tag}.json").write_text(
        json.dumps(result, indent=2, default=float))

    # ------------------------------------------------------------- report
    L = ["# P-7 — Is any of this a property of one box?\n",
         "**Generated by `physical/code/analyze_apparatus.py` — "
         "do not edit by hand.**\n",
         f"{len(rows)} apparatus configurations, each re-calibrated to the same "
         f"difficulty and analysed separately with its own decoder and "
         f"threshold.\n",
         "| Config | Sessions | Margin | Median lead | False alarms/h | "
         "Decision-rate change |", "|---|---|---|---|---|---|"]
    A = L.append
    for r in rows:
        lead = (f"{r['median_lead_s']:+.0f} s"
                if np.isfinite(r["median_lead_s"]) else "—")
        far = (f"{r['false_alarms_per_hour']:.2f}"
               if r.get("false_alarms_per_hour") is not None else "—")
        dc = (f"{r['decision_change']:+.1%}"
              if r.get("decision_change") is not None else "—")
        mg = f"{r['margin_deg']:.1f}°" if np.isfinite(r["margin_deg"]) else "—"
        A(f"| **{r['config']}** | {r['n_sessions']} | {mg} | {lead} | {far} | {dc} |")
    A("")

    A("## PP-9 — does the decision-rate direction hold?\n")
    if flat:
        A(f"**{len(flat)} of {len(rows)} configurations show no direction at "
          f"all** ({', '.join(flat)} — change smaller than {FLAT:.0%}). A flat "
          f"curve is not agreement; it is the absence of an effect, and it is "
          f"counted as neither.\n")
    if pp9_holds is None:
        A(f"**Not testable.** Only {len(directed)} configuration(s) show a "
          f"direction at all, and one observation cannot establish that a "
          f"direction holds across configurations. Either the effect is absent "
          f"on this apparatus, or the campaign is too small to see it — and "
          f"those are different conclusions that this experiment, as run, "
          f"cannot separate.\n")
    elif pp9_holds:
        A(f"**Yes.** All {len(directed)} configurations with a direction move "
          f"the same way. That is "
          f"the strongest form of this finding: the effect is not a property of "
          f"the exposure, the patch size or the channel count, which is what "
          f"would let it be stated as a design rule rather than an observation "
          f"about one apparatus.\n")
    else:
        pos = [k for k, v in directed.items() if v > 0]
        neg = [k for k, v in directed.items() if v < 0]
        A(f"**No — the sign flips.** Rises on {', '.join(pos)}; falls on "
          f"{', '.join(neg)}.\n")
        A("This is a finding, not a failure. It says the decision-rate effect "
          "depends on something the design has not identified, and it names "
          "which configurations differ. **It also means the decision-rate "
          "result cannot be stated as a general design rule**, which is what "
          "P-6 was promoted to co-primary in order to do. Report that plainly.\n")

    A("## PP-10 — do the headline numbers move?\n")
    A("| Quantity | Spread across configurations | Threshold | Moves? |")
    A("|---|---|---|---|")
    A(f"| Median lead time | {lead_spread:.0f} s | > {LEAD_MARGIN_S:.0f} s | "
      f"{'**yes**' if np.isfinite(lead_spread) and lead_spread > LEAD_MARGIN_S else 'no'} |"
      if np.isfinite(lead_spread) else "| Median lead time | — | — | not measurable |")
    if np.isfinite(far_span):
        shown = ("one config never alarms" if not np.isfinite(far_ratio)
                 else f"{far_ratio:.1f}×")
        A(f"| False alarms per hour | {shown} "
          f"(span {far_span:.2f}/h) | > {FAR_FACTOR:.0f}× or "
          f"> {M.FALSE_ALARM_BUDGET_PER_HOUR}/h | "
          f"{'**yes**' if far_moves else 'no'} |")
    else:
        A("| False alarms per hour | — | — | not measurable |")
    A("")
    if pp10_moves:
        A("**The numbers are apparatus-specific.** A single lead time or "
          "false-alarm rate from this apparatus is not a property of the "
          "monitor — it is a property of the monitor *on this box*. Every "
          "report of those quantities must carry the spread across "
          "configurations, not a single value.\n")
        A("This is uncomfortable and it is the point of running P-7. Finding "
          "it here costs a table; finding it after publication costs the "
          "result.\n")
    else:
        A("**The numbers hold across configurations.** That is the outcome "
          "that most strengthens everything else here: it says the measured "
          "lead time and false-alarm rate are not artefacts of one particular "
          "exposure or channel count.\n")

    A("## What this does not fix\n")
    A("- **One room, one experimenter, one camera model, one screen "
      "technology.** Varying the settings is not the same as varying the "
      "apparatus independently. This narrows the single-apparatus objection; "
      "it does not close it.")
    A(f"- **{len(rows)} configurations is a small family.** The honest "
      f"presentation is {len(rows)} points with their intervals, never an "
      f"average that hides them.")
    A("- Every configuration shares the same code, the same detector and the "
      "same analyst. A bug in the shared core would move all four together "
      "and look like agreement.")

    out = RESULTS / f"P7_APPARATUS_VARIATION{a.tag}.md"
    out.write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
