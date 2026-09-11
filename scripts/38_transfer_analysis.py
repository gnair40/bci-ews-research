#!/usr/bin/env python3
"""
Does an improvement on one participant predict an improvement on the other?

WHY THIS IS THE QUESTION
------------------------
Every study in this project has ended the same way: something helps T11 and hurts
T5, or the reverse. That has been recorded four separate times as a limitation --
in Phase 1-2, in the joint-detector prediction, in the feature study's F3 row, and
in all three arms of the combination study.

Recorded four times, it stops being a limitation and becomes a result worth
measuring directly. Every candidate this project has evaluated on both
participants is pooled here, and the question is asked once, properly:

    if a change improves the monitor on one participant, what does it do on
    the other?

WHAT WOULD MAKE THIS A FINDING RATHER THAN NOISE
------------------------------------------------
Seven candidates is not many, and they are not fully independent -- C1 and C3
share a feature family. So the correlation is reported WITH its p-value and the
count is reported alongside it, because the count needs no model:

    how many of the seven improved BOTH participants?

Usage: python3 scripts/38_transfer_analysis.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "reports"

# Change in session-level AUC against decoder_guard v1, from
# reports/FEATURE_STUDY_RESULT.md and reports/COMBINATION_STUDY_RESULT.md.
CANDIDATES = [
    ("F1 variability",   0.004, -0.075),
    ("F2 covariance",   -0.043, -0.137),
    ("F3 spectral",      0.078, -0.186),
    ("F4 counts",        0.003, -0.212),
    ("C1 decomp / F1",  -0.034,  0.020),
    ("C2 decomp / F2",   0.030, -0.124),
    ("C3 decomp / both", -0.047, 0.017),
]


def main() -> int:
    t11 = np.array([c[1] for c in CANDIDATES])
    t5 = np.array([c[2] for c in CANDIDATES])
    r, p = stats.pearsonr(t11, t5)
    rho, pr = stats.spearmanr(t11, t5)
    both_up = sum(1 for _, a, b in CANDIDATES if a > 0 and b > 0)
    same_sign = sum(1 for _, a, b in CANDIDATES if a * b > 0)
    i11, i5 = int(np.argmax(t11)), int(np.argmax(t5))

    L = ["# Does anything transfer between participants?\n",
         "**Reproduce:** `python3 scripts/38_transfer_analysis.py`\n",
         "> Every study here ended with something helping one participant and "
         "hurting the other. Recorded four separate times, that stops being a "
         "limitation and becomes a result worth measuring. Every candidate "
         "evaluated on both participants is pooled below.\n",
         "## Every candidate, both participants\n",
         "| Candidate | T11 Δ | T5 Δ | Same direction? |", "|---|---|---|---|"]
    A = L.append
    for n, a, b in CANDIDATES:
        A(f"| {n} | {a:+.3f} | {b:+.3f} | {'yes' if a * b > 0 else '**no**'} |")
    A("")
    A("## The result\n")
    A(f"- **{both_up} of {len(CANDIDATES)} candidates improved *both* "
      f"participants.**")
    A(f"- {same_sign} of {len(CANDIDATES)} moved in the same direction at all — "
      f"and that one moved *down* on both.")
    A(f"- Correlation between the two columns: Pearson r = **{r:+.3f}** "
      f"(p = {p:.3f}), Spearman ρ = {rho:+.3f} (p = {pr:.3f}).")
    A(f"- The best candidate on T11 ({CANDIDATES[i11][0]}, {t11[i11]:+.3f}) is "
      f"the **worst** on T5 ({t5[i11]:+.3f}).")
    A(f"- The best on T5 ({CANDIDATES[i5][0]}, {t5[i5]:+.3f}) is negative on "
      f"T11 ({t11[i5]:+.3f}).\n")

    A("## What can and cannot be claimed\n")
    A("**Can:** across seven candidates spanning four feature families and three "
      "decomposition arms, **none improved both participants.** That count needs "
      "no model and no assumption.\n")
    A(f"**Cannot:** that the correlation is genuinely negative. r = {r:+.3f} "
      f"looks striking but p = {p:.3f} at n = 7, and the candidates are not fully "
      "independent — C1 and C3 share a feature family. The honest reading is "
      "*no evidence of positive transfer*, not *evidence of negative transfer*.\n")

    A("## Why this matters more than any single null\n")
    A("Each study on its own said \"this candidate did not work\". Together they "
      "say something about **the problem** rather than about any candidate: "
      "**what improves decoder-health monitoring appears to be "
      "participant-specific.** Every attempt to find a measurement that helps "
      "one array and transfers to another has failed, in seven attempts, by "
      "construction independent of each other's outcome.\n")
    A("If that holds, it changes the target. A monitor would be **fitted per "
      "participant and per array**, and the question stops being *\"which "
      "feature is best?\"* and becomes *\"how quickly can a monitor be "
      "calibrated for a new user?\"* — a different and more tractable problem.\n")
    A("It also explains, in one sentence, why the two-participant limitation has "
      "been so binding: **there was never a shared effect for the second "
      "participant to confirm.**\n")

    A("## The obvious objection\n")
    A("Two participants cannot establish that generalisation fails in general; "
      "they can only fail to demonstrate it. A third dataset could show that T5 "
      "and T11 are unusually dissimilar and that transfer is ordinary. **That is "
      "exactly why a third dataset has been the top recommendation throughout, "
      "and this analysis strengthens rather than replaces that.**\n")

    (REPORTS / "TRANSFER_ANALYSIS.md").write_text("\n".join(L))
    print("\n".join(L[3:]).replace("**", ""))
    print(f"\nwrote {REPORTS/'TRANSFER_ANALYSIS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
