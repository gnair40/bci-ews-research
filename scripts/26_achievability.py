#!/usr/bin/env python3
"""
Is the information even there? An achievability bound for early warning.

THE QUESTION THIS ANSWERS
-------------------------
The benchmark reports that no configuration passes the gates. The obvious
challenge to that is: "is early warning impossible on this data, or did you
just fail to find the right detector?" Those are very different claims, and the
difference is measurable.

Strip away every threshold, every state machine, every dwell and hysteresis
setting. Ask only: taking a single window of neural features, can ANY threshold
on this detector's raw score tell apart

    a window AFTER a fault started but BEFORE performance dropped
    from
    a window from a recording where nothing is wrong at all

That is exactly the early-warning window -- the interval a warning has to live
in to be useful -- and the answer is one number, the area under the ROC curve.

    AUC ~ 0.50   the score carries no information about the fault. No threshold
                 scheme, no smoothing, no state machine can recover what is not
                 there. The negative result is a bound, not a failure of effort.
    AUC >> 0.50  the information IS present, and the failure is in the machinery
                 that turns scores into warnings -- a fixable engineering problem.

Reporting this is what separates "we could not do it" from "it cannot be done
this way", and only one of those is a finding.

Two comparisons are reported, because the contrast between them is informative:

    early    post-onset, pre-crossing   vs healthy   <- the one that matters
    late     post-crossing              vs healthy   <- the easy case, a sanity check

If `late` is high and `early` is at chance, the detector can see damage but not
anticipate it -- which is precisely a nowcast, the thing the published measure
already does and the thing this project set out to improve on.

Usage: python3 scripts/26_achievability.py
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

CONDITIONS = [
    ("episode_scores.csv", "T11", "calibrate once"),
    ("episode_scores_local.csv", "T11", "recent normal"),
    ("episode_scores_T5_local.csv", "T5", "recent normal"),
]
MIN_POOL = 40


def auc(pos: np.ndarray, neg: np.ndarray) -> tuple[float, float]:
    """Area under the ROC curve, via Mann-Whitney U, with its p-value.

    U / (n_pos * n_neg) IS the AUC -- no curve needs to be drawn. Reported
    two-sided: a detector that is reliably LOWER during faults is just as
    informative as one that is higher, and would be a sign error rather than
    an absence of signal.
    """
    if len(pos) < MIN_POOL or len(neg) < MIN_POOL:
        return float("nan"), float("nan")
    u, p = stats.mannwhitneyu(pos, neg, alternative="two-sided")
    return float(u / (len(pos) * len(neg))), float(p)


def main() -> int:
    lines = ["# Achievability: is the information there at all?\n",
             "**Reproduce:** `python3 scripts/26_achievability.py`\n",
             "> Every threshold, state machine, dwell and hysteresis setting is "
             "stripped away. This asks only whether a single window's raw score "
             "can separate the early-warning interval from healthy recording. "
             "AUC 0.50 is chance.\n"]
    A = lines.append

    for fname, participant, baseline in CONDITIONS:
        path = OUT / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        print("=" * 74)
        print(f"{participant} — {baseline} baseline")
        print("=" * 74)
        A(f"\n## {participant} — {baseline} baseline\n")
        A("| Detector | Early-warning AUC | p | Post-damage AUC | Verdict |")
        A("|---|---|---|---|---|")

        for det_name, sub in df.groupby("detector"):
            healthy, early, late = [], [], []
            for _, r in sub.iterrows():
                y = np.fromstring(r.scores, sep=",")
                if not len(y):
                    continue
                if not r.crossed:
                    healthy.append(y)
                    continue
                ow, cw = int(r.onset_w), int(r.crossing_w)
                if cw > ow:
                    early.append(y[ow:cw])
                if cw < len(y):
                    late.append(y[cw:])

            H = np.concatenate(healthy) if healthy else np.array([])
            E = np.concatenate(early) if early else np.array([])
            L = np.concatenate(late) if late else np.array([])

            a_e, p_e = auc(E, H)
            a_l, _ = auc(L, H)

            if not np.isfinite(a_e):
                verdict = "too few windows"
            elif abs(a_e - 0.5) < 0.05:
                verdict = "**at chance — no information**"
            elif a_e > 0.5:
                verdict = "information present"
            else:
                verdict = "informative but INVERTED"

            print(f"  {det_name:<20} early AUC {a_e:.3f} (p={p_e:.2g})   "
                  f"late AUC {a_l:.3f}   {verdict.replace('**','')}")
            A(f"| `{det_name}` | **{a_e:.3f}** | {p_e:.2g} | {a_l:.3f} | {verdict} |")

            # Per fault mode, for the early window only -- an average over four
            # very different faults can hide one that is perfectly detectable.
            per = {}
            for mode, msub in sub[sub.crossed].groupby("mode"):
                pool = []
                for _, r in msub.iterrows():
                    y = np.fromstring(r.scores, sep=",")
                    ow, cw = int(r.onset_w), int(r.crossing_w)
                    if cw > ow and len(y) >= cw:
                        pool.append(y[ow:cw])
                if pool:
                    a_m, _ = auc(np.concatenate(pool), H)
                    if np.isfinite(a_m):
                        per[mode] = a_m
            if per:
                bits = "  ".join(f"{m.split('_')[0].lower()} {v:.2f}"
                                 for m, v in sorted(per.items()))
                print(f"  {'':<20} by mode: {bits}")
                A(f"| | *by mode:* {'; '.join(f'{m} {v:.2f}' for m, v in sorted(per.items()))} | | | |")
        print()

    A("\n## How to read this\n")
    A("- **AUC at 0.50** means the score carries no information about the fault "
      "during the early-warning window. No amount of smoothing, thresholding or "
      "state machinery can recover information that is not present, so a "
      "negative result there is a **bound**, not a shortfall of effort.")
    A("- **A high post-damage AUC beside a chance early AUC** means the detector "
      "sees damage but cannot anticipate it. That is a *nowcast* — which is what "
      "the published instability measure already provides, and precisely what "
      "this project set out to improve on.")
    A("- **A high early AUC beside a failing benchmark** would mean the "
      "information is there and the failure is in the machinery — a fixable "
      "engineering problem rather than a limit of the data.")

    out = REPORTS / "ACHIEVABILITY.md"
    out.write_text("\n".join(lines))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
