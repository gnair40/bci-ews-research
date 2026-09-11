#!/usr/bin/env python3
"""
13_select_observable.py
=======================
Choose which neural quantity the early-warning indicator should be computed on
-- using BASELINE DATA ONLY, and never any information about how it changes
over time.

THE PROBLEM THIS SOLVES
-----------------------
Critical slowing down is a statement about a system's RECOVERY RATE: as it nears
a transition, it takes longer to bounce back from a disturbance. Measuring that
requires an observable which HAS a recovery to slow -- one that remembers its
recent past.

`scripts/08` established that the raw binned neural features do not. At 20 ms
their memory is 0.3-0.5 bins for T11: essentially white noise. There is nothing
there to slow down. So a different neural quantity has to carry the indicator,
and this script characterises the candidates.

THE TRAP: SMOOTHING MANUFACTURES MEMORY
---------------------------------------
The obvious fix is to smooth the signal. **Do not.** A moving average of pure
white noise is strongly autocorrelated -- the memory belongs to the filter, not
the system. An indicator built on a smoothed signal would measure the smoothing
window and rise or fall with it, telling you nothing about the brain.

Non-overlapping REBINNING is different and is safe. Summing counts into wider,
adjacent, non-overlapping bins never creates correlation between bins: rebinned
white noise stays white. So if a rebinned neural signal shows real memory, that
memory was in the system and the finer bins were simply too noisy to reveal it.

This script demonstrates that difference on synthetic white noise before applying
anything to real data, so the distinction is verified rather than asserted.

WHY BASELINE DATA ONLY
----------------------
Lag-1 autocorrelation is itself one of the early-warning indicators. If the
observable were chosen by looking at how its autocorrelation behaves across the
whole record, the choice would be made using the very quantity the study is
about -- and the analysis would be circular.

So selection uses only the frozen baseline: T11 trial days 658-675, the first 8
blocks, which `research/FROZEN_DESIGN.json` already designates as the reference
period. The question asked of each candidate is "does this have a measurable
recovery rate at all?" -- a property of the observable, not a trend.

HOW TO RUN
----------
    python3 scripts/13_select_observable.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW = REPO_ROOT / "data" / "raw"
PROCESSED = REPO_ROOT / "data" / "processed"
FREEZE = REPO_ROOT / "research" / "FROZEN_DESIGN.json"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)
BIN_S = 0.02


def ac1(x: np.ndarray) -> float:
    """Lag-1 autocorrelation: how much this moment predicts the next."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 10:
        return np.nan
    x = x - x.mean()
    d = np.sqrt((x[:-1] ** 2).sum() * (x[1:] ** 2).sum())
    return float((x[:-1] * x[1:]).sum() / d) if d > 0 else np.nan


def memory_bins(x: np.ndarray) -> float:
    """Convert lag-1 autocorrelation into a memory length, in samples."""
    r = ac1(x)
    return float(-1.0 / np.log(r)) if np.isfinite(r) and 0 < r < 1 else np.nan


def rebin(x: np.ndarray, factor: int) -> np.ndarray:
    """Average into WIDER, NON-OVERLAPPING bins. Cannot create correlation."""
    n = (len(x) // factor) * factor
    if n == 0:
        return np.array([])
    return x[:n].reshape(-1, factor).mean(axis=1)


def smooth(x: np.ndarray, w: int) -> np.ndarray:
    """Overlapping moving average. DOES create correlation -- shown for contrast."""
    if w < 2 or len(x) < w:
        return x
    k = np.ones(w) / w
    return np.convolve(x, k, mode="valid")


def demonstrate_the_trap(rng) -> None:
    """Prove the smoothing/rebinning distinction on data with no memory at all."""
    white = rng.standard_normal(20000)
    print("  Starting from PURE WHITE NOISE (no memory whatsoever):")
    print(f"    untouched                       lag-1 r = {ac1(white):+.3f}")
    for w in (5, 25, 50):
        print(f"    smoothed, {w:>3}-sample window     lag-1 r = "
              f"{ac1(smooth(white, w)):+.3f}   <-- INVENTED by the filter")
    for f in (5, 25, 50):
        print(f"    rebinned, {f:>3}-sample bins       lag-1 r = "
              f"{ac1(rebin(white, f)):+.3f}   <-- stays white, as it must")


def baseline_blocks() -> list[Path]:
    """The blocks the frozen design designates as the reference period."""
    if not FREEZE.exists():
        print(f"{FREEZE} not found. Freeze the design first.", file=sys.stderr)
        sys.exit(1)
    frozen = json.loads(FREEZE.read_text())
    before = frozen["membership"]["before"]["blocks"]
    baseline_days = sorted({b["trial_day"] for b in before})[:4]   # 658,665,672,675
    wanted = {(b["trial_day"], b["block"]) for b in before
              if b["trial_day"] in baseline_days}
    found = []
    for part_dir in sorted(p for p in RAW.rglob("*")
                           if p.is_dir() and p.name.upper() == "T11"):
        for day_dir in sorted(d for d in part_dir.iterdir()
                              if d.is_dir() and DAY_RE.match(d.name)):
            day = int(DAY_RE.match(day_dir.name).group(1))
            for blk in sorted(b for b in day_dir.iterdir()
                              if b.is_dir() and BLOCK_RE.match(b.name)):
                num = int(re.search(r"(\d+)", blk.name).group(1))
                if (day, num) in wanted:
                    found.append(blk)
    return found, sorted(baseline_days)


def candidates_for_block(blk: Path) -> dict[str, np.ndarray]:
    """Build every candidate observable from one block."""
    d = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)
    X = np.asarray(d["nctx"], dtype=np.float64)
    if "spikePower" in d:
        X = np.hstack([X, np.asarray(d["spikePower"], dtype=np.float64)])
    sd = X.std(0); sd[sd == 0] = 1.0
    Z = (X - X.mean(0)) / sd

    Zc = Z - Z.mean(0)
    cov = np.cov(Zc[::10], rowvar=False)
    w, v = np.linalg.eigh(cov)
    pc1 = Zc @ v[:, -1]
    pop_mean = Z.mean(axis=1)

    out = {
        "neural PC1, 20 ms": pc1,
        "neural PC1, rebinned 500 ms": rebin(pc1, 25),
        "neural PC1, rebinned 1 s": rebin(pc1, 50),
        "neural PC1, rebinned 5 s": rebin(pc1, 250),
        "population mean, 20 ms": pop_mean,
        "population mean, rebinned 1 s": rebin(pop_mean, 50),
        "population mean, rebinned 5 s": rebin(pop_mean, 250),
    }
    if "cursorVel" in d:
        cv = np.asarray(d["cursorVel"], float)[:, 0]
        out["decoder output (cursorVel x), 20 ms"] = cv
        out["decoder output, rebinned 1 s"] = rebin(cv, 50)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    print("=" * 78)
    print("CHOOSING THE OBSERVABLE FOR THE EARLY-WARNING INDICATOR")
    print("=" * 78)

    print("\nSTEP 1 — smoothing invents memory; rebinning does not")
    print("-" * 78)
    demonstrate_the_trap(rng)
    print("\n  This is why no candidate below uses a moving average.")

    blocks, days = baseline_blocks()
    print(f"\nSTEP 2 — candidates, measured on BASELINE BLOCKS ONLY")
    print("-" * 78)
    print(f"  T11 trial days {days} — {len(blocks)} blocks, the reference period")
    print("  named in research/FROZEN_DESIGN.json. No trend information is used,")
    print("  because lag-1 autocorrelation is itself an early-warning indicator.\n")

    per_block: dict[str, list[float]] = {}
    for blk in blocks:
        for name, series in candidates_for_block(blk).items():
            per_block.setdefault(name, []).append(memory_bins(series))

    rows = []
    for name, mems in per_block.items():
        mems = [m for m in mems if np.isfinite(m)]
        if not mems:
            rows.append({"observable": name, "median_memory_samples": np.nan,
                         "median_memory_seconds": np.nan, "usable": False})
            continue
        med = float(np.median(mems))
        # Sample interval implied by the label.
        if "20 ms" in name:
            dt = BIN_S
        elif "500 ms" in name:
            dt = 0.5
        elif "1 s" in name:
            dt = 1.0
        elif "5 s" in name:
            dt = 5.0
        else:
            dt = BIN_S
        rows.append({"observable": name, "median_memory_samples": round(med, 2),
                     "median_memory_seconds": round(med * dt, 3),
                     "n_blocks": len(mems), "usable": med >= 2.0})

    df = pd.DataFrame(rows).sort_values("median_memory_samples", ascending=False)
    print(f"  {'observable':<38} {'memory':>10} {'=':>2} {'seconds':>9}   usable?")
    print("  " + "-" * 74)
    for r in df.itertuples():
        mem = "n/a" if not np.isfinite(r.median_memory_samples) \
            else f"{r.median_memory_samples:.2f}"
        sec = "n/a" if not np.isfinite(r.median_memory_seconds) \
            else f"{r.median_memory_seconds:.2f} s"
        mark = "YES" if r.usable else "no — too close to white"
        print(f"  {r.observable:<38} {mem:>10} {'':>2} {sec:>9}   {mark}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "observable_candidates.csv", index=False)

    print("\n" + "=" * 78)
    print("READING THIS")
    print("=" * 78)
    print("""
  'Memory' is how many samples the observable remembers its own past. An
  observable near 1 sample has no recovery to slow down and cannot carry a
  critical-slowing-down measurement, however good the rest of the method is.

  Note what rebinning does and does not do here. Where a rebinned signal shows
  more memory IN SAMPLES than the 20 ms version, that memory is real -- rebinning
  cannot manufacture it, as STEP 1 shows. Where it does not, the signal genuinely
  has no slow structure to find.

  This script does NOT choose. The choice is a scientific decision about what the
  early-warning indicator is a statement about, and it should be made
  deliberately and recorded, like the deterioration definition was.
""")
    print(f"Wrote {(PROCESSED / 'observable_candidates.csv').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
