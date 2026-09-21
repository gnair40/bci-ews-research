#!/usr/bin/env python3
"""
78_decision_rate_paired.py
==========================
The decision-rate comparison, done as a paired test.

WHY THIS EXISTS
---------------
`scripts/76` reports a detection rate at each decision rate, each with its own
bootstrap interval, and the published reading was that the intervals are wide
and overlapping, so the question "does deciding less often help?" cannot be
settled on archived data.

**Overlap of two marginal intervals is not a test of a difference.** It is a
well-known way to under-call an effect, and it is especially wrong here,
because both rates are scored on **the same degraded episodes against the same
fault-free episodes**. Most of the uncertainty in each rate comes from having
only 29 and 21 fault-free episodes to place the threshold — and that uncertainty
is *shared*, so it largely cancels in the difference.

This file resamples episodes **once** and scores both decision rates on the same
draw, giving an interval on the difference rather than on each rate separately.

WHAT IT CHANGES
---------------
The marginal reading was "neither direction is established on either
participant". The paired reading is sharper, and less comfortable:

  * T11's rise is **not** established — the interval still includes zero.
  * T5's fall **is** established, and it is large.

So the archived data does not merely fail to answer the question. It contains
one statistically established result, and that result points **against** the
mechanism the physical phase predicts in PP-7. That is a better reason to run
the experiment than "we cannot tell", and a worse position to start from than
this project had assumed.

A CAVEAT THAT MATTERS
---------------------
The two participants' curves do not end at the same decision rate. T11's
episodes are 55 windows long so the slowest rate tested is 13 decisions an hour;
T5's are 42, so it stops at 27. The endpoint comparison is therefore not
like-for-like, and the matched-range comparison is reported alongside it.

Usage: python3 scripts/78_decision_rate_paired.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"
N_BOOT = 4000
SEED = 20260921


def _dr():
    spec = importlib.util.spec_from_file_location(
        "dr76", REPO / "scripts" / "76_decision_rate_curve.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["dr76"] = m
    spec.loader.exec_module(m)
    return m


def paired(dr, pos_y, neg_y, k_fast, k_slow, rng) -> dict:
    sc = lambda k, ys: np.array([dr.episode_score(y, k) for y in ys])
    Pf, Ps = sc(k_fast, pos_y), sc(k_slow, pos_y)
    Nf, Ns = sc(k_fast, neg_y), sc(k_slow, neg_y)
    m = np.isfinite(Pf) & np.isfinite(Ps); Pf, Ps = Pf[m], Ps[m]
    m = np.isfinite(Nf) & np.isfinite(Ns); Nf, Ns = Nf[m], Ns[m]
    det = dr.detection_at
    obs = det(Ps, Ns, dr.FALSE_FLAG) - det(Pf, Nf, dr.FALSE_FLAG)
    d = []
    for _ in range(N_BOOT):
        ip = rng.integers(0, len(Pf), len(Pf))
        i_n = rng.integers(0, len(Nf), len(Nf))
        d.append(det(Ps[ip], Ns[i_n], dr.FALSE_FLAG)
                 - det(Pf[ip], Nf[i_n], dr.FALSE_FLAG))
    d = np.array(d); d = d[np.isfinite(d)]
    lo, hi = np.percentile(d, [2.5, 97.5])
    return {"k_fast": k_fast, "k_slow": k_slow,
            "decisions_fast": 3600 / (k_fast * dr.STEP_S),
            "decisions_slow": 3600 / (k_slow * dr.STEP_S),
            "n_degraded": int(len(Pf)), "n_fault_free": int(len(Nf)),
            "change": float(obs), "ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo * hi > 0)}


def main() -> int:
    dr = _dr()
    rng = np.random.default_rng(SEED)
    result = {"what_this_is": "The decision-rate change, tested as paired.",
              "n_boot": N_BOOT, "participants": {}}

    per = {}
    for fname, pname in dr.sources():
        s = pd.read_csv(OUT / fname)
        s = s[s.detector == "decoder_guard"]
        pos_y = [np.fromstring(r.scores, sep=",") for _, r in s[s.crossed].iterrows()]
        neg_y = [np.fromstring(r.scores, sep=",")
                 for _, r in s[s.severity == "none"].iterrows()]
        ks = [k for k in dr.K_VALUES
              if len([y for y in neg_y if len(y) >= k]) >= 5]
        per[pname] = (pos_y, neg_y, ks)
        result["participants"][pname] = {
            "own_range": paired(dr, pos_y, neg_y, ks[0], ks[-1], rng)}

    # A matched range, so the two are compared like for like.
    common = min(max(v[2]) for v in per.values())
    for pname, (pos_y, neg_y, ks) in per.items():
        result["participants"][pname]["matched_range"] = paired(
            dr, pos_y, neg_y, ks[0], common, rng)
    result["matched_k"] = int(common)

    (OUT / "decision_rate_paired.json").write_text(json.dumps(result, indent=2))

    L = ["# Does deciding less often help? The comparison, done paired\n",
         "**Reproduce:** `python3 scripts/78_decision_rate_paired.py`\n",
         "> `scripts/76` reports each decision rate's detection with its own "
         "interval, and the published reading was that the intervals overlap so "
         "nothing can be settled. **Overlap of two marginal intervals is not a "
         "test of a difference**, and here both rates are scored on the same "
         "episodes against the same fault-free set, so most of the uncertainty "
         "is shared and cancels in the difference.\n",
         "## Each participant's full range\n",
         "| | Decision rate | Degraded | Fault-free | Change | Paired 95% CI | Established? |",
         "|---|---|---|---|---|---|---|"]
    A = L.append
    for pname, v in result["participants"].items():
        r = v["own_range"]
        A(f"| **{pname}** | {r['decisions_fast']:.0f} → {r['decisions_slow']:.0f}/h "
          f"| {r['n_degraded']} | {r['n_fault_free']} | **{r['change']:+.1%}** "
          f"| {r['ci95'][0]:+.1%} to {r['ci95'][1]:+.1%} "
          f"| {'**yes**' if r['excludes_zero'] else 'no'} |")
    A("")
    A(f"## Matched range — both to {3600 / (common * dr.STEP_S):.0f} decisions "
      f"an hour\n")
    A("The two participants' episodes are different lengths, so their own "
      "ranges end at different decision rates. This row compares like with "
      "like.\n")
    A("| | Change | Paired 95% CI | Established? |")
    A("|---|---|---|---|")
    for pname, v in result["participants"].items():
        r = v["matched_range"]
        A(f"| **{pname}** | {r['change']:+.1%} | "
          f"{r['ci95'][0]:+.1%} to {r['ci95'][1]:+.1%} | "
          f"{'**yes**' if r['excludes_zero'] else 'no'} |")
    A("")
    A("## What this changes\n")
    est = [p for p, v in result["participants"].items()
           if v["own_range"]["excludes_zero"]]
    if est:
        A(f"**The archived data is not silent on this question.** On "
          f"{', '.join(est)} the change is established at the 95% level. The "
          f"earlier reading — that nothing can be said — came from comparing "
          f"intervals instead of testing the difference.\n")
        falls = [p for p, v in result["participants"].items()
                 if v["own_range"]["excludes_zero"] and v["own_range"]["change"] < 0]
        if falls:
            A(f"**And the established result points the wrong way for the "
              f"hypothesis.** On {', '.join(falls)} deciding less often makes "
              f"detection **worse**, not better. The physical phase's "
              f"prediction PP-7 expects the opposite.\n")
            A("That is a better reason to run the experiment than \"we cannot "
              "tell\", and a worse position to start from than this project had "
              "assumed. A preregistered prediction that contradicts the only "
              "established evidence available is still a legitimate "
              "prediction — but it has to be made knowing that, and PP-7 now "
              "says so.\n")
    else:
        A("Neither change is established even paired, so the original reading "
          "stands: the archived data cannot settle the direction.\n")

    A("## What this does not change\n")
    A("- **n = 2, and they still disagree.** A paired test tightens each "
      "participant's own interval; it cannot reconcile two participants who "
      "point in opposite directions.")
    A("- The threshold still rests on 29 and 21 fault-free episodes. Pairing "
      "cancels that uncertainty **in the difference**, not in the levels, so "
      "the absolute detection rates remain as uncertain as `scripts/76` says.")
    A("- Nothing here is about the physical apparatus. It is a re-reading of "
      "the archived analysis.")

    (REPORTS / "DECISION_RATE_PAIRED.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'DECISION_RATE_PAIRED.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
