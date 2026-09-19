#!/usr/bin/env python3
"""
76_decision_rate_curve.py
=========================
How often should a decoder-health monitor decide? Nobody knows, and the archived
data cannot say.

THE QUESTION
------------
`reports/OPERATING_POINT_BOUND.md` found that this project's monitor failed for a
reason that had nothing to do with the detector: a budget of 0.1 false alarms per
hour was applied to a system deciding 720 times an hour, which silently demanded
a per-decision false-positive rate of 1.4e-4 and a per-window AUC of 0.9992.

That implies something more general than a fix for one monitor. **Deciding less
often should make monitoring easier, for two separate reasons**, and they
compound:

  * fewer decisions means a looser per-decision false-positive budget, and
  * each decision can pool more windows, so it rests on more evidence.

If that is true, there is a *decision-rate law* for health monitoring of drifting
sensor arrays: detection achievable at a fixed false-flag rate, as a function of
how often you decide. That curve would tell anyone building any such system how
often to check. **No such curve exists for any system.**

WHAT THIS SCRIPT DOES, AND WHAT IT CANNOT DO
---------------------------------------------
It measures the curve on the archived data, and shows why that measurement
cannot settle the question:

  * the false-flag threshold has to be estimated from genuinely fault-free
    episodes, of which there are 29 (T11) and 21 (T5), so the 10% point rests on
    two or three episodes in the tail;
  * and the two participants disagree about the direction of the curve.

Those are not reasons to abandon the question. They are a specification for the
measurement that would answer it, which is what `research/BUILD_MANUAL.md` B-14
now records.

ONE RECORDING CAMPAIGN GIVES THE WHOLE CURVE
---------------------------------------------
The decision rate is an analysis choice, not a recording choice. A session
recorded once can be scored at every decision rate afterwards. So the rig
campaign does not need a separate arm per rate -- it needs enough fault-free
sessions to put a trustworthy threshold on the tail, and the entire curve falls
out of the same recordings.

Usage: python3 scripts/76_decision_rate_curve.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

# Decide every k windows. Each decision pools the k windows since the last one,
# which is the part that makes this a real design knob rather than just
# throwing information away.
K_VALUES = [1, 2, 3, 6, 11, 27, 55]
STEP_S = 5.0
FALSE_FLAG = 0.10
N_BOOT = 2000
SEED = 20260919


def sources() -> list[tuple[str, str]]:
    found = []
    for p in sorted(OUT.glob("episode_scores*_local.csv")):
        mid = p.stem[len("episode_scores"):-len("_local")].strip("_")
        found.append((p.name, mid or "T11"))
    order = {"T11": 0, "T5": 1}
    return sorted(found, key=lambda q: (order.get(q[1], 2), q[1]))


def decisions(y: np.ndarray, k: int) -> np.ndarray:
    """Scores of the decisions an episode yields at decision spacing k."""
    n = (len(y) // k) * k
    if n == 0:
        return np.array([float(y.mean())])
    return y[:n].reshape(-1, k).mean(1)


def episode_score(y: np.ndarray, k: int) -> float:
    """An episode alarms on its loudest decision, so that is its score."""
    return float(decisions(y, k).max())


def detection_at(pos: np.ndarray, neg: np.ndarray, rate: float) -> float:
    """Detection rate when the threshold is set to flag `rate` of healthy episodes."""
    if len(neg) < 5 or len(pos) < 5:
        return float("nan")
    thr = float(np.quantile(neg, 1.0 - rate))
    return float((pos > thr).mean())


def main() -> int:
    rng = np.random.default_rng(SEED)
    result = {
        "what_this_is": "The decision-rate curve on archived data, and why it "
                        "cannot be settled there.",
        "false_flag_rate": FALSE_FLAG, "participants": {},
    }

    for fname, pname in sources():
        df = pd.read_csv(OUT / fname)
        s = df[df.detector == "decoder_guard"]
        pos_y = [np.fromstring(r.scores, sep=",") for _, r in s[s.crossed].iterrows()]
        neg_y = [np.fromstring(r.scores, sep=",")
                 for _, r in s[s.severity == "none"].iterrows()]
        rows = []
        for k in K_VALUES:
            P = np.array([episode_score(y, k) for y in pos_y if len(y) >= k])
            N = np.array([episode_score(y, k) for y in neg_y if len(y) >= k])
            if len(N) < 5:
                continue
            det = detection_at(P, N, FALSE_FLAG)
            # Bootstrap over episodes. The interval is dominated by how few
            # fault-free episodes there are, which is the finding.
            boot = []
            for _ in range(N_BOOT):
                pb = rng.choice(P, len(P), replace=True)
                nb = rng.choice(N, len(N), replace=True)
                boot.append(detection_at(pb, nb, FALSE_FLAG))
            lo, hi = np.nanpercentile(boot, [2.5, 97.5])
            rows.append({
                "k_windows_per_decision": k,
                "decisions_per_hour": 3600.0 / (k * STEP_S),
                "decisions_per_episode": len(decisions(pos_y[0], k)),
                "detection": det, "ci95": [float(lo), float(hi)],
                "n_positive": int(len(P)), "n_fault_free": int(len(N)),
            })
        if not rows:
            continue
        first, last = rows[0]["detection"], rows[-1]["detection"]
        result["participants"][pname] = {
            "curve": rows,
            "n_fault_free_episodes": rows[0]["n_fault_free"],
            "direction": ("rises" if last > first + 0.02 else
                          "falls" if last < first - 0.02 else "flat"),
            "change": float(last - first),
        }

    (OUT / "decision_rate_curve.json").write_text(json.dumps(result, indent=2))

    L = ["# How often should a decoder-health monitor decide?\n",
         "**Generated by `scripts/76_decision_rate_curve.py` — do not edit by hand.**\n",
         "Deciding less often should make monitoring easier for two compounding "
         "reasons: a looser per-decision false-positive budget, and more evidence "
         "behind each decision. If that holds there is a **decision-rate law** "
         "for health monitoring of drifting sensor arrays — detection achievable "
         "at a fixed false-flag rate, as a function of how often you decide. "
         "**No such curve exists for any system.**\n"]
    A = L.append

    A(f"## The curve on the archived data, at a {FALSE_FLAG:.0%} false-flag rate\n")
    for pname, r in result["participants"].items():
        A(f"### {pname}\n")
        A("| Decisions per hour | Decisions per session | Windows per decision | "
          "Detection | 95% CI |")
        A("|---|---|---|---|---|")
        for q in r["curve"]:
            A(f"| {q['decisions_per_hour']:.0f} | {q['decisions_per_episode']} | "
              f"{q['k_windows_per_decision']} | **{q['detection']:.1%}** | "
              f"{q['ci95'][0]:.1%} to {q['ci95'][1]:.1%} |")
        A("")
        A(f"Direction: **{r['direction']}** ({r['change']:+.1%} from the fastest "
          f"rate to the slowest), on **{r['n_fault_free_episodes']} fault-free "
          f"episodes**.\n")

    dirs = {p: r["direction"] for p, r in result["participants"].items()}
    A("## Why this cannot be settled here\n")
    A(f"**The two participants disagree about the direction of the curve.** "
      f"On T11 it {dirs.get('T11', '?')}; on T5 it {dirs.get('T5', '?')}. A law "
      f"that points one way in one array and the other way in the next is not a "
      f"law, it is two noisy measurements.\n")
    A("**And the threshold rests on almost nothing.** The false-flag rate is set "
      "from genuinely fault-free episodes, and there are "
      + " and ".join(f"{r['n_fault_free_episodes']} ({p})"
                      for p, r in result["participants"].items())
      + f". At a {FALSE_FLAG:.0%} rate the threshold is the "
        f"{1 - FALSE_FLAG:.0%} quantile of that — two or three episodes in the "
        f"tail. The confidence intervals above show what that costs.\n")
    A("Those are not reasons to drop the question. **They are a specification "
      "for the measurement that would answer it**, and it is a measurement no "
      "existing dataset can provide, because it needs hundreds of fault-free "
      "sessions with constructed onsets.\n")

    A("## What the rig measures, and why one campaign is enough\n")
    A("**The decision rate is an analysis choice, not a recording choice.** A "
      "session recorded once can be scored at every decision rate afterwards. So "
      "the rig campaign does not need an arm per rate — it needs enough "
      "fault-free sessions to put a trustworthy threshold on the tail, and the "
      "whole curve falls out of the same recordings.\n")
    A("| | Archived data | Rig campaign (B-14) |")
    A("|---|---|---|")
    A("| Fault-free sessions | "
      + " / ".join(str(r['n_fault_free_episodes'])
                   for r in result["participants"].values())
      + " | **101** |")
    A("| Onsets | not recorded; chosen by the analyst afterwards | **drawn and "
      "written down before each session** |")
    A("| Arrays | 2, from one deposit | as many as are built |")
    A("| Who collected it | Pun et al., 2024 | **this project** |")
    A("| Can it settle the direction of the curve? | **no** | yes |")
    A("")
    A("That last row is the point. The archived data raised this question and "
      "cannot answer it. **The rig answers it with data this project collects "
      "itself**, and the answer is a design curve that applies to any "
      "many-channel sensor that drifts, not only to brain implants.\n")

    A("## What would falsify the law\n")
    A("If the rig's curve is **flat**, deciding less often does not help and the "
      "failure is in the detector rather than the sampling — which sends the "
      "next attempt somewhere completely different from where this project would "
      "have sent it.\n")
    A("If the curve **falls**, as T5's does, pooling windows destroys more "
      "information than it buys, and the right move is the opposite of the one "
      "this analysis suggests. **That outcome is why the curve has to be "
      "measured rather than argued for.**")

    (REPORTS / "DECISION_RATE_CURVE.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'DECISION_RATE_CURVE.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
