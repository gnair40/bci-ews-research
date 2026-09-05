#!/usr/bin/env python3
"""
08_record_length_check.py
=========================
Does the real dataset provide a long enough record for the EWS detector to work?

THE QUESTION THIS ANSWERS
-------------------------
The synthetic controls (scripts 06 and 07) established that detection power
depends on how long the record is *relative to the system's own correlation
time* -- the timescale over which the system "remembers" a perturbation. On the
simulated saddle-node the measured relationship was roughly:

    ~11 correlation times  ->  power 0.25
    ~22 correlation times  ->  power 0.42
    ~56 correlation times  ->  power 0.83

That is a general, data-independent statement about the method. This script
turns it into a specific statement about *this* dataset: it estimates the
correlation time of candidate observables in the real recordings, expresses the
available record in those units, and reports where each candidate analysis level
falls on that curve.

WHY THE ANALYSIS LEVEL IS THE WHOLE ARGUMENT
--------------------------------------------
The same dataset gives wildly different record lengths depending on what you
treat as one observation:

  * SESSION level  -- 15 observations for T11, 6 for T5.
  * BLOCK level    -- 29 and 21.
  * WINDOW level   -- MINDFUL's own resolution: a 60 s window advanced every
                      10 s over the concatenated recording, giving hundreds.
  * BIN level      -- 440,045 bins for T11 at 20 ms.

These are not interchangeable, and the choice is a scientific claim about where
the transition lives, not a convenience. This script computes the numbers for
each so the choice can be made on evidence.

AN IMPORTANT CAVEAT, STATED UP FRONT
------------------------------------
Correlation time measured *within* a block describes fast, within-session
dynamics. If the slow variable driving the transition actually drifts over
*days*, then the relevant record is the 15 sessions, and no amount of dense
within-block sampling substitutes for it -- you would be sampling the fast
dynamics finely while sampling the slow variable 15 times. This script reports
both and does not decide between them; that is the researcher's call, and it is
the central design decision of the project.

HOW TO RUN
----------
    python3 scripts/08_record_length_check.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"

BIN_SECONDS = 0.02                      # 20 ms bins, confirmed from the paper
MINDFUL_WINDOW_BINS = 3000              # 60 s, as used by the original authors
MINDFUL_STEP_BINS = 500                 # advanced every 10 s

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)

# Power as a function of record length, in units of correlation time,
# measured on the synthetic saddle-node in scripts/06 and 07.
POWER_CURVE = [(11, 0.25), (22, 0.42), (56, 0.83)]


def correlation_time_bins(x: np.ndarray) -> float:
    """
    Estimate how many bins the series "remembers", from its lag-1 correlation.

    For a process that decays exponentially, the lag-1 autocorrelation `a`
    implies a correlation time of -1/ln(a) steps. Intuitively: the closer `a`
    is to 1, the longer the memory. a=0.5 gives ~1.4 steps; a=0.99 gives ~100.

    Returns NaN when the series is constant or anti-correlated, where the
    quantity is not defined.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return np.nan
    x = x - x.mean()
    a, b = x[:-1], x[1:]
    denom = np.sqrt((a**2).sum() * (b**2).sum())
    if denom == 0:
        return np.nan
    r = float((a * b).sum() / denom)
    if not (0 < r < 1):
        return np.nan
    return float(-1.0 / np.log(r))


def expected_power(n_units: float) -> str:
    """Read the measured power curve, interpolating between its points."""
    if not np.isfinite(n_units):
        return "n/a"
    pts = POWER_CURVE
    if n_units <= pts[0][0]:
        return f"< {pts[0][1]:.2f}"
    if n_units >= pts[-1][0]:
        return f">= {pts[-1][1]:.2f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= n_units <= x1:
            y = y0 + (y1 - y0) * (n_units - x0) / (x1 - x0)
            return f"~{y:.2f}"
    return "n/a"


OBSERVABLES = ("angleError", "cursorVel_x", "neural_pc1", "neural_mean")


def block_correlation_times(blk: Path) -> dict:
    """
    Compute the correlation time of each candidate observable for ONE block,
    returning only scalars.

    MEMORY NOTE -- this matters. An earlier version of this script loaded every
    block's neural matrix into a list and only then computed statistics. For
    T11 that is 440,045 bins x 384 features x 8 bytes = about 1.3 GB held at
    once, plus a full SVD on top; it exhausted the machine's memory and the
    process was killed. Processing one block at a time and keeping only the
    resulting numbers uses a few tens of MB and gives identical results.

    The general lesson: when a dataset is large, reduce inside the loop rather
    than accumulating raw arrays and reducing at the end.
    """
    info = sio.loadmat(blk / "info.mat", squeeze_me=True, struct_as_record=False)
    data = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)

    out = {"n_bins": int(np.asarray(data["nctx"]).shape[0])}

    if "angleError" in info:
        out["angleError"] = correlation_time_bins(np.asarray(info["angleError"], float))
    if "cursorVel" in data:
        out["cursorVel_x"] = correlation_time_bins(
            np.asarray(data["cursorVel"], float)[:, 0])

    # Neural features: build the z-scored matrix, take the two summaries we
    # need, then release it before moving on.
    X = np.asarray(data["nctx"], dtype=np.float32)
    if "spikePower" in data:
        X = np.hstack([X, np.asarray(data["spikePower"], dtype=np.float32)])
    sd = X.std(0); sd[sd == 0] = 1
    Z = (X - X.mean(0)) / sd
    del X
    out["neural_mean"] = correlation_time_bins(Z.mean(axis=1))
    # Leading principal component via the covariance of a subsample -- far
    # cheaper than an SVD of the full matrix and sufficient for a timescale.
    sub = Z[::10]
    cov = np.cov(sub, rowvar=False)
    w, v = np.linalg.eigh(cov)
    pc1_dir = v[:, -1]
    del cov, v, sub
    out["neural_pc1"] = correlation_time_bins(Z @ pc1_dir)
    del Z
    return out


def scan_main_blocks(root: Path) -> pd.DataFrame:
    """Walk the main-cohort blocks, one at a time, collecting only scalars."""
    rows = []
    part_dirs = sorted(p for p in root.rglob("*")
                       if p.is_dir() and re.fullmatch(r"T\d+", p.name))
    for part_dir in part_dirs:
        part = part_dir.name.upper()
        days = sorted((d for d in part_dir.iterdir()
                       if d.is_dir() and DAY_RE.match(d.name)),
                      key=lambda q: int(DAY_RE.match(q.name).group(1)))
        for day_dir in days:
            day = int(DAY_RE.match(day_dir.name).group(1))
            for blk in sorted(b for b in day_dir.iterdir()
                              if b.is_dir() and BLOCK_RE.match(b.name)):
                rec = block_correlation_times(blk)
                rec.update({"participant": part, "trial_day": day,
                            "block": blk.name})
                rows.append(rec)
                print(f"    {part} day_{day} {blk.name}", end="\r", flush=True)
    print(" " * 60, end="\r")
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()

    print("=" * 78)
    print("IS THE REAL RECORD LONG ENOUGH FOR THE DETECTOR TO WORK?")
    print("=" * 78)
    print("Power measured on the synthetic saddle-node, by record length:")
    for n, p in POWER_CURVE:
        print(f"    {n:>3} correlation times -> power {p:.2f}")

    print("\nScanning blocks (one at a time, to keep memory small) ...")
    df = scan_main_blocks(args.root)
    if df.empty:
        print("\nNo blocks found.", file=sys.stderr)
        return 1

    # ---- correlation times of real observables --------------------------
    print("\n" + "-" * 78)
    print("STEP 1 — correlation time of real observables (within blocks, 20 ms bins)")
    print("-" * 78)
    tau_rows = []
    for obs in OBSERVABLES:
        if obs not in df.columns:
            continue
        for part in sorted(df["participant"].unique()):
            taus = df.loc[df.participant == part, obs].dropna().tolist()
            taus = [t for t in taus if np.isfinite(t)]
            if not taus:
                continue
            med = float(np.median(taus))
            tau_rows.append({"observable": obs, "participant": part,
                             "median_tau_bins": med,
                             "median_tau_seconds": med * BIN_SECONDS,
                             "n_blocks": len(taus)})
            flag = ""
            if med < 2.0:
                flag = "   <-- ESSENTIALLY WHITE NOISE; see warning below"
            print(f"  {obs:<12s} {part:<4s} median correlation time = "
                  f"{med:8.1f} bins = {med * BIN_SECONDS:6.2f} s "
                  f"(across {len(taus)} blocks){flag}")
    tau_df = pd.DataFrame(tau_rows)

    if (tau_df["median_tau_bins"] < 2.0).any():
        print("""
  WARNING — an observable whose correlation time is around one bin has almost
  no memory: it is close to white noise at this sampling rate. Dividing the
  record length by such a tiny number produces an enormous count of
  "correlation times", which looks reassuring and means nothing. Critical
  slowing down is a statement about a system's recovery rate, so the observable
  must be one that HAS a recovery to slow down. Prefer angleError, cursorVel or
  a population component over the raw channel mean.""")

    # ---- how long is the record, at each candidate level ----------------
    print("\n" + "-" * 78)
    print("STEP 2 — record length at each candidate analysis level")
    print("-" * 78)
    rows = []
    for part, g in df.groupby("participant"):
        total_bins = int(g["n_bins"].sum())
        n_windows = sum(max(0, (int(nb) - MINDFUL_WINDOW_BINS)
                            // MINDFUL_STEP_BINS + 1) for nb in g["n_bins"])
        levels = {
            "session": g["trial_day"].nunique(),
            "block": len(g),
            "MINDFUL window (60 s / 10 s)": n_windows,
            "bin (20 ms)": total_bins,
        }
        for lvl, n in levels.items():
            rows.append({"participant": part, "level": lvl, "n_observations": n})
        print(f"\n  {part}:")
        for lvl, n in levels.items():
            print(f"    {lvl:<30s} {n:>10,} observations")
        print(f"    {'total recording':<30s} {total_bins * BIN_SECONDS / 3600:>10.2f} hours"
              f"  over {g['trial_day'].max() - g['trial_day'].min()} days")
    level_df = pd.DataFrame(rows)

    # ---- the comparison that matters -------------------------------------
    print("\n" + "-" * 78)
    print("STEP 3 — record length in units of correlation time, and the power")
    print("          the synthetic controls predict there")
    print("-" * 78)
    print("\n  (a) FAST framing: the transition is treated as living in the")
    print("      concatenated within-session dynamics.")
    verdicts = []
    # cursorVel has the longest correlation time of the candidates, i.e. the
    # most memory, so it is the observable with the most room for a recovery
    # rate to slow. The raw neural features are near-white at 20 ms and cannot
    # support a critical-slowing-down measurement at that resolution at all.
    fast_obs = "cursorVel_x"
    print(f"      (using {fast_obs} as the observable)")
    for _, t in tau_df[tau_df.observable == fast_obs].iterrows():
        part = t["participant"]
        total_bins = int(df.loc[df.participant == part, "n_bins"].sum())
        n_tau = total_bins / t["median_tau_bins"]
        print(f"      {part}: {total_bins:,} bins / {t['median_tau_bins']:.1f} bins "
              f"= {n_tau:,.0f} correlation times  -> power {expected_power(n_tau)}")
        verdicts.append({"framing": "fast (concatenated bins)", "participant": part,
                         "n_correlation_times": n_tau,
                         "expected_power": expected_power(n_tau)})

    print("\n  (b) SLOW framing: the transition is treated as living across")
    print("      sessions, so one session is one observation.")
    for part, g in df.groupby("participant"):
        n_sessions = g["trial_day"].nunique()
        # With session-level sampling, the shortest resolvable correlation
        # time is one session, so the record is at best n_sessions long.
        print(f"      {part}: {n_sessions} sessions -> at best {n_sessions} "
              f"correlation times -> power {expected_power(n_sessions)}")
        verdicts.append({"framing": "slow (session level)", "participant": part,
                         "n_correlation_times": float(n_sessions),
                         "expected_power": expected_power(n_sessions)})

    print("\n" + "=" * 78)
    print("READING THIS HONESTLY  --  IMPORTANT CORRECTION")
    print("=" * 78)
    print("""
  The "fast framing" number above is real but it answers the WRONG QUESTION,
  and an earlier version of this project drew the wrong conclusion from it.

  It compares the record length against the correlation time of a FAST
  observable (cursor velocity, about half a second). What an early-warning
  test actually asks is whether an indicator TRENDS UPWARD across time, and
  the sample size for a trend test is the number of independent observations
  of the SLOW variable -- the thing drifting toward the transition.

  Sampling more finely inside a block gives a more PRECISE estimate at each
  point. It does not give more POINTS.

  So the fast framing does not deliver thousands of usable observations. The
  usable counts are:

      T11   21 blocks (or 11 sessions) before its transition
      T5     9 blocks (or  3 sessions) before its transition

  Run scripts/10_design_power_analysis.py for what those sample sizes can
  actually detect, and see research/design_decisions.md for the consequences.

  What this script IS good for: the correlation times in STEP 1. Those show
  that raw binned neural features are near-white at 20 ms (0.3-0.5 bins of
  memory) while cursor velocity has 27-52 bins. An observable with no memory
  has no recovery rate to slow down, so critical slowing down cannot be
  measured on raw features at that resolution. That finding stands.
""")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    tau_df.to_csv(PROCESSED / "correlation_times.csv", index=False)
    level_df.to_csv(PROCESSED / "record_levels.csv", index=False)
    pd.DataFrame(verdicts).to_csv(PROCESSED / "record_length_verdict.csv", index=False)
    print(f"Wrote correlation_times.csv, record_levels.csv, "
          f"record_length_verdict.csv to data/processed/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
