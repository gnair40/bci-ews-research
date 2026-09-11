#!/usr/bin/env python3
"""
10_design_power_analysis.py
===========================
How large a trend could this study actually detect, at each candidate analysis
level? Computes the numbers behind the study-design decision.

WHY THIS EXISTS
---------------
An early-warning analysis asks whether an indicator TRENDS UPWARD as a system
approaches failure. The statistic used for that in this literature is Kendall's
tau, and the sample size for a trend test is the number of independent
observations of the SLOW variable -- the thing that drifts toward the transition.

That last point is the one this script exists to make concrete, because it is
easy to get wrong. An earlier version of this project's analysis compared the
record length against the correlation time of a FAST observable (cursor
velocity, about 0.55 s) and concluded there were "16,144 correlation times" of
data and therefore ample power. That number is real but answers a different
question. Sampling more finely within a block gives a more PRECISE estimate at
each point; it does not give more POINTS. The trend test still has as many
observations as there are blocks or sessions.

So this script asks the right question directly: given n observations, how large
a trend must there be before it can be detected at all, and what is the power to
find a trend of a given size?

WHAT THE OUTPUTS MEAN
---------------------
  Smallest detectable |tau|
      Below this value, no result can reach significance at alpha regardless of
      how real it is. A hard floor imposed by sample size alone.

  Power
      The probability of detecting a trend that genuinely exists. Power 0.46
      means a real effect is missed more than half the time. Reporting a null
      from a low-power test says more about the test than about the data.

HOW TO RUN
----------
    python3 scripts/10_design_power_analysis.py
    python3 scripts/10_design_power_analysis.py --reps 8000
"""

from __future__ import annotations

import argparse
import sys
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = REPO_ROOT / "data" / "processed"

# The paper's own early/late boundaries, used to define "before the transition".
TRANSITION_DAY = {"T11": 758, "T5": 2133}


def alpha_achievable(n: int, alpha: float = 0.05) -> bool:
    """
    Can a two-sided test at this alpha even be performed with n points?

    With very few observations the null distribution is coarse. At n = 3 there
    are only 6 possible orderings, so the smallest attainable two-sided p-value
    is 1/3 -- no result can ever be significant at 0.05. Reporting "power" in
    that regime is meaningless: the numbers are just the false-positive rate.
    """
    if n < 3:
        return False
    if n <= 8:
        from math import factorial
        return 2.0 / factorial(n) <= alpha
    return True


def critical_tau(n: int, alpha: float = 0.05, n_perm: int = 20000,
                 seed: int = 0) -> float:
    """
    The smallest |tau| that reaches significance at `alpha`, two-sided.

    For n <= 8 every ordering is enumerated, giving the exact null distribution.
    Above that the null is approximated by random permutations, which is what
    "no trend" means: any ordering of the values is equally likely.
    """
    if n < 3:
        return float("nan")
    if n <= 8:
        taus = sorted(abs(kendalltau(range(n), p).statistic)
                      for p in permutations(range(n)))
        return float(taus[int(np.ceil((1 - alpha) * len(taus))) - 1])
    rng = np.random.default_rng(seed)
    x = np.arange(n)
    null = np.abs([kendalltau(x, rng.permutation(n)).statistic
                   for _ in range(n_perm)])
    return float(np.quantile(null, 1 - alpha))


def power(n: int, total_rise_sd: float, alpha: float = 0.05,
          reps: int = 4000, seed: int = 1) -> float:
    """
    Probability of detecting a linear trend of a given total size.

    `total_rise_sd` is how much the indicator rises across the WHOLE record,
    expressed in units of its own noise standard deviation. Expressing it that
    way makes the answer independent of what the indicator actually is.
    """
    if n < 3:
        return float("nan")
    crit = critical_tau(n, alpha)
    rng = np.random.default_rng(seed)
    x = np.arange(n)
    slope = total_rise_sd / (n - 1)
    hits = 0
    for _ in range(reps):
        y = slope * x + rng.normal(0, 1.0, n)
        if abs(kendalltau(x, y).statistic) >= crit:
            hits += 1
    return hits / reps


def sample_sizes() -> pd.DataFrame:
    """Read the real sample sizes out of the tidy block table."""
    path = PROCESSED / "blocks.csv"
    if not path.exists():
        print(f"{path} not found. Run scripts/04_explore_dataset.py first.",
              file=sys.stderr)
        return pd.DataFrame()
    b = pd.read_csv(path)
    b = b[b["cohort"] == "main"]
    rows = []
    for part, g in b.groupby("participant"):
        cut = TRANSITION_DAY.get(part)
        pre = g[g["trial_day"] < cut] if cut else g
        rows += [
            {"participant": part, "level": "session (all)",
             "n": int(g["trial_day"].nunique())},
            {"participant": part, "level": "session (pre-transition)",
             "n": int(pre["trial_day"].nunique())},
            {"participant": part, "level": "block (all)", "n": int(len(g))},
            {"participant": part, "level": "block (pre-transition)",
             "n": int(len(pre))},
        ]
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--effects", type=float, nargs="+",
                    default=[0.5, 1.0, 2.0, 4.0, 8.0])
    args = ap.parse_args()

    print("=" * 78)
    print("HOW LARGE A TREND COULD THIS STUDY DETECT?")
    print("=" * 78)
    print("The sample size for a trend test is the number of independent")
    print("observations of the SLOW variable -- blocks or sessions, not 20 ms bins.\n")

    sizes = sample_sizes()
    if not sizes.empty:
        print("-" * 78)
        print("REAL SAMPLE SIZES IN THIS DATASET")
        print("-" * 78)
        print(sizes.pivot(index="level", columns="participant",
                          values="n").to_string())

    ns = sorted(set(sizes["n"].tolist()) | {6, 11, 15, 21, 29}) if not sizes.empty \
        else [6, 11, 15, 21, 29]
    ns = [n for n in ns if n >= 3]

    print("\n" + "-" * 78)
    print("SMALLEST DETECTABLE |tau|  (below this, nothing can reach significance)")
    print("-" * 78)
    crit_rows = []
    for n in ns:
        ok = alpha_achievable(n, args.alpha)
        c = critical_tau(n, args.alpha)
        verdict = ("NO VALID TEST" if not ok else
                   "usable" if c <= 0.32 else
                   "marginal" if c <= 0.50 else "unusable")
        crit_rows.append({"n": n, "critical_tau": round(c, 3),
                          "alpha_achievable": ok, "verdict": verdict})
        note = "" if ok else f"   (alpha={args.alpha} unreachable with {n} points)"
        print(f"  n = {n:>3}   |tau| >= {c:.3f}   {verdict}{note}")

    print("\n" + "-" * 78)
    print("POWER TO DETECT A REAL TREND")
    print("(effect = total rise across the record, in noise standard deviations)")
    print("-" * 78)
    header = "    n  " + "".join(f"{e:>8g} sd" for e in args.effects)
    print(header)
    pow_rows = []
    for n in ns:
        row = {"n": n, "alpha_achievable": alpha_achievable(n, args.alpha)}
        line = f"  {n:>3}  "
        if not row["alpha_achievable"]:
            print(f"  {n:>3}  " + "  no valid test at this alpha".ljust(44))
            pow_rows.append(row)
            continue
        for e in args.effects:
            p = power(n, e, args.alpha, args.reps)
            row[f"power_{e:g}sd"] = round(p, 3)
            line += f"{p:>11.2f}"
        pow_rows.append(row)
        print(line)

    print("\n" + "=" * 78)
    print("WHAT THIS MEANS FOR THE DESIGN")
    print("=" * 78)
    print("""
  Choosing BLOCK rather than SESSION as the unit of observation roughly doubles
  the pre-transition sample at essentially no cost -- blocks are already separate
  recordings, and each still contains enough bins for the indicator at that point
  to be precisely estimated.

  What it costs: blocks within one session are not fully independent. Acknowledge
  that, and test it by comparing within-session against between-session variability.

  What it does NOT license: treating overlapping sliding windows as independent
  observations. Adjacent 60 s windows advanced every 10 s share most of their data;
  the effective sample size stays near the block count no matter how many windows
  are produced.
""")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    if not sizes.empty:
        sizes.to_csv(PROCESSED / "design_sample_sizes.csv", index=False)
    pd.DataFrame(crit_rows).to_csv(PROCESSED / "design_critical_tau.csv", index=False)
    pd.DataFrame(pow_rows).to_csv(PROCESSED / "design_power.csv", index=False)
    print("Wrote design_sample_sizes.csv, design_critical_tau.csv, "
          "design_power.csv to data/processed/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
