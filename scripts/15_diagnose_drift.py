#!/usr/bin/env python3
"""
15_diagnose_drift.py
====================
EXPLORATORY. What is the monotonic drift that the preregistered indicator picked
up?

STATUS AND STANDING
-------------------
This is **exploratory**, run AFTER the confirmatory analysis was completed and
reported (`reports/EWS_RESULTS.md`). It does not revise that result and nothing
here may be presented as confirmatory. Its purpose is to characterise the
dataset so a corrected study can be designed.

THE QUESTION
------------
The frozen analysis found the indicator rising steeply across the pre-transition
period -- and rising just as steeply during the HEALTHY baseline, which is why it
cannot be read as an early warning. Something is drifting monotonically
regardless of performance. Identifying it matters for two reasons: it explains
the negative result, and if it corresponds to a measurable recording property it
can be removed or controlled for in a future design.

CANDIDATES TESTED
-----------------
All are properties of the recording rather than of the task:

  avgOutliers      the deposit's own artifact measure -- the maximum average
                   outlier across channels per time bin
  silent channels  how many channels have essentially no variance in a block
  mean firing      average threshold-crossing rate across channels
  total raw power  mean raw variance across channels before normalisation

If the indicator tracks one of these closely, the "early warning" was recording
drift wearing a different name.

HOW TO RUN
----------
    python3 scripts/15_diagnose_drift.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)


def recording_properties(blk: Path) -> dict:
    """Per-block properties of the RECORDING, independent of task performance."""
    d = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)
    info = sio.loadmat(blk / "info.mat", squeeze_me=True, struct_as_record=False)
    X = np.asarray(d["nctx"], dtype=np.float64)
    if "spikePower" in d:
        X = np.hstack([X, np.asarray(d["spikePower"], dtype=np.float64)])
    v = X.var(axis=0)
    out = {
        "n_silent_channels": int((v < 1e-6).sum()),
        "n_lowvar_channels": int((v < np.median(v) * 0.01).sum()),
        "mean_firing": float(np.asarray(d["nctx"], float).mean()),
        "mean_raw_variance": float(v.mean()),
        "median_raw_variance": float(np.median(v)),
    }
    if "avgOutliers" in info:
        ao = np.asarray(info["avgOutliers"], float)
        out["mean_avg_outliers"] = float(np.nanmean(ao))
        out["p95_avg_outliers"] = float(np.nanpercentile(ao, 95))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()

    ind_path = PROCESSED / "ews_result_indicators.csv"
    if not ind_path.exists():
        print("Run scripts/14_run_ews_analysis.py first.", file=sys.stderr)
        return 1
    ind = pd.read_csv(ind_path)
    ind = ind[ind.participant == args.participant]

    print("=" * 78)
    print("EXPLORATORY — what is the monotonic drift?")
    print("=" * 78)
    print("Run after the confirmatory analysis. Nothing here revises it.\n")

    rows = []
    for pdir in sorted(p for p in RAW.rglob("*")
                       if p.is_dir() and p.name.upper() == args.participant):
        for dd in sorted((x for x in pdir.iterdir()
                          if x.is_dir() and DAY_RE.match(x.name)),
                         key=lambda q: int(DAY_RE.match(q.name).group(1))):
            day = int(DAY_RE.match(dd.name).group(1))
            for b in sorted(x for x in dd.iterdir()
                            if x.is_dir() and BLOCK_RE.match(x.name)):
                r = recording_properties(b)
                r.update({"trial_day": day,
                          "block": int(re.search(r"(\d+)", b.name).group(1))})
                rows.append(r)
                print(f"    {args.participant} day_{day} blk {r['block']}",
                      end="\r", flush=True)
    print(" " * 50, end="\r")

    rec = pd.DataFrame(rows)
    df = ind.merge(rec, on=["trial_day", "block"], how="inner")
    df = df.sort_values(["trial_day", "block"]).reset_index(drop=True)
    df["block_order"] = np.arange(len(df))

    print(f"How well does each RECORDING property explain the indicator?  "
          f"(n = {len(df)} blocks)\n")
    print(f"  {'property':<26} {'Spearman rho':>13} {'p':>10}")
    print("  " + "-" * 52)
    cand = [c for c in ("mean_avg_outliers", "p95_avg_outliers",
                        "n_silent_channels", "n_lowvar_channels",
                        "mean_firing", "mean_raw_variance",
                        "median_raw_variance", "block_order") if c in df]
    res = []
    for c in cand:
        y = df[c].to_numpy(float)
        if np.nanstd(y) == 0:
            print(f"  {c:<26} {'constant':>13} {'':>10}")
            continue
        rho, p = spearmanr(df["primary"], y, nan_policy="omit")
        flag = "  <-- strong" if abs(rho) > 0.7 else ""
        print(f"  {c:<26} {rho:>+13.3f} {p:>10.4f}{flag}")
        res.append({"property": c, "spearman_rho": float(rho), "p": float(p)})

    print(f"\n  For reference, the indicator vs PERFORMANCE (median angle error):")
    rho, p = spearmanr(df["primary"], df["median_angle_error"], nan_policy="omit")
    print(f"  {'median_angle_error':<26} {rho:>+13.3f} {p:>10.4f}")
    res.append({"property": "median_angle_error", "spearman_rho": float(rho),
                "p": float(p)})

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "drift_diagnosis_blocks.csv", index=False)
    pd.DataFrame(res).to_csv(PROCESSED / "drift_diagnosis_correlations.csv",
                             index=False)

    print("""
  READING THIS
  ------------
  A recording property that correlates strongly with the indicator is a
  candidate explanation for the negative result: the indicator would then be
  measuring the state of the electrodes rather than the state of the system.

  'block_order' is included as the null explanation -- if nothing beats simple
  elapsed time, the drift has no identified cause in these variables and the
  next design must control for time itself rather than for a specific artifact.
""")
    print("Wrote drift_diagnosis_blocks.csv and drift_diagnosis_correlations.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
