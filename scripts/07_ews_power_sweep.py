#!/usr/bin/env python3
"""
07_ews_power_sweep.py
=====================
Measure the EWS detector's statistical POWER and FALSE-POSITIVE RATE as a
function of its two main analysis choices: rolling-window length and
de-trending strength.

WHY THIS EXISTS
---------------
Running `scripts/06_ews_controls.py` once, on one random seed, told us almost
nothing. Repeating it across ten seeds revealed the real behaviour: at the
default settings the detector missed a genuine saddle-node bifurcation in most
runs, while never producing a false alarm on the negative controls. It was
**underpowered**, not over-eager.

A single pass/fail on one seed is not a validation. What a method needs is:

  * **Power** — when critical slowing down IS present, how often is it detected?
    (Detection rate on the positive control. Higher is better.)
  * **False-positive rate** — when it is NOT present, how often does the detector
    fire anyway? (Detection rate on the negative controls. Should be at or below
    the significance level, here 0.05.)

Both depend on choices that are usually made silently. The literature review for
this project puts it directly: *the choice of window length and sampling cadence
is a scientific hypothesis, not a preprocessing detail — treat it as an
experimental variable and sweep it, and report the full surface.* That is what
this script does.

WHAT "POWER" MEANS, IN PLAIN LANGUAGE
-------------------------------------
Power is the probability of noticing something that is really there. A detector
with 40% power will miss a real transition 6 times out of 10. Reporting a
negative result from an underpowered detector is meaningless — the absence of a
signal would tell you about the detector, not about the system.

This is exactly the concern raised by van der Bolt, van Nes & Scheffer (2021),
"No warning for slow transitions": if the observational record is too short
relative to the system's response rate, no warning can be resolved even in
principle.

HOW TO READ THE OUTPUT
----------------------
A configuration is only usable if it has BOTH high power AND a false-positive
rate near or below the significance level. High power with a high false-positive
rate is a detector that fires at everything.

HOW TO RUN
----------
    python3 scripts/07_ews_power_sweep.py                    # default grid
    python3 scripts/07_ews_power_sweep.py --seeds 30 --n-surrogates 300
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "reports" / "figures"
PROCESSED = REPO_ROOT / "data" / "processed"

INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
# Sequential ramp: ONE hue, light -> dark, as magnitude encoding requires.
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95",
             "#0d366b"]


def load_ews():
    """Import the detector from 06_ews_controls.py (name starts with a digit)."""
    path = Path(__file__).resolve().parent / "06_ews_controls.py"
    spec = importlib.util.spec_from_file_location("ews_controls", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ews_controls"] = mod
    spec.loader.exec_module(mod)
    return mod


def run_grid(ews, windows, sigmas, seeds, n_surr, n, step, alpha) -> pd.DataFrame:
    rows = []
    total = len(windows) * len(sigmas)
    for ci, window in enumerate(windows):
        for si, sigma in enumerate(sigmas):
            fired = {(m, i): 0 for m in ("saddle", "drift", "noise")
                     for i in ("variance", "ar1")}
            for seed in range(seeds):
                rng = np.random.default_rng(10_000 + seed)
                series = {
                    "saddle": ews.simulate_saddle_node(n=n, rng=rng)[0],
                    "drift": ews.simulate_monotonic_drift(n=n, rng=rng)[0],
                    "noise": ews.simulate_rising_noise(n=n, rng=rng)[0],
                }
                for mname, x in series.items():
                    xd = ews.detrend(x, sigma)
                    ind = ews.rolling_indicators(xd, window, step)
                    if len(ind["index"]) < 8:
                        continue
                    # One surrogate set serves both indicators.
                    nulls = ews.surrogate_null_taus(xd, window, step, sigma,
                                                    n_surr, rng)
                    for iname in ("variance", "ar1"):
                        tau = ews.kendall_trend(ind[iname])
                        null = nulls[iname][np.isfinite(nulls[iname])]
                        if not len(null) or not np.isfinite(tau):
                            continue
                        p = float(np.mean(np.abs(null) >= abs(tau)))
                        if p < alpha:
                            fired[(mname, iname)] += 1
            row = {"window": window, "smooth_sigma": sigma,
                   "n_windows": len(ind["index"]), "seeds": seeds}
            for (m, i), c in fired.items():
                row[f"{m}_{i}_rate"] = c / seeds
            rows.append(row)
            done = ci * len(sigmas) + si + 1
            print(f"  [{done}/{total}] window={window} sigma={sigma}  "
                  f"power(ar1)={row['saddle_ar1_rate']:.2f}  "
                  f"power(var)={row['saddle_variance_rate']:.2f}  "
                  f"FP(drift,ar1)={row['drift_ar1_rate']:.2f}", flush=True)
    return pd.DataFrame(rows)


def heat(ax, df, value, windows, sigmas, title, vmax=1.0):
    grid = df.pivot(index="smooth_sigma", columns="window", values=value)
    grid = grid.reindex(index=sigmas, columns=windows)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("b", BLUE_RAMP)
    im = ax.imshow(grid.values, cmap=cmap, vmin=0, vmax=vmax, aspect="auto",
                   origin="lower")
    ax.set_xticks(range(len(windows)), [str(w) for w in windows])
    ax.set_yticks(range(len(sigmas)), [str(s) for s in sigmas])
    ax.set_xlabel("Rolling window (time steps)", fontsize=9, color=INK_MUTED)
    ax.set_ylabel("De-trend sigma", fontsize=9, color=INK_MUTED)
    ax.set_title(title, fontsize=10, color=INK, loc="left", pad=8)
    ax.tick_params(colors=INK_MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_visible(False)
    # Direct labels: the value matters more than the shade, and this keeps the
    # figure readable for colour-vision-deficient readers and in print.
    for r in range(grid.shape[0]):
        for c in range(grid.shape[1]):
            v = grid.values[r, c]
            if np.isfinite(v):
                ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=8.5,
                        color="white" if v > 0.55 * vmax else INK)
    return im


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--step", type=int, default=50)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--n-surrogates", type=int, default=150)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--windows", type=int, nargs="+",
                    default=[400, 800, 1600, 3000])
    ap.add_argument("--sigmas", type=float, nargs="+",
                    default=[100.0, 400.0, 1000.0])
    args = ap.parse_args()

    ews = load_ews()
    print("=" * 74)
    print("EWS DETECTOR — POWER AND FALSE-POSITIVE SWEEP")
    print("=" * 74)
    print(f"{args.seeds} seeds per cell · {args.n_surrogates} surrogates · "
          f"alpha={args.alpha}")
    print("power = detection rate on the saddle-node (higher is better)")
    print("FP    = detection rate on a negative control (should be <= alpha)\n")

    df = run_grid(ews, args.windows, args.sigmas, args.seeds,
                  args.n_surrogates, args.n, args.step, args.alpha)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "ews_power_sweep.csv", index=False)

    print("\n" + "=" * 74)
    print("RESULTS")
    print("=" * 74)
    show = df[["window", "smooth_sigma", "n_windows",
               "saddle_variance_rate", "saddle_ar1_rate",
               "drift_variance_rate", "drift_ar1_rate", "noise_ar1_rate"]]
    print(show.to_string(index=False))

    # ---- resolution caveat ------------------------------------------------
    # With N seeds, the smallest non-zero rate observable is 1/N. If 1/N is
    # larger than alpha, a single chance false positive already "exceeds" alpha
    # and the comparison is meaningless. Say so rather than reporting a
    # spurious failure.
    resolution = 1.0 / args.seeds
    print("\n" + "-" * 74)
    print(f"Resolution: with {args.seeds} seeds the smallest non-zero rate "
          f"measurable is {resolution:.3f}.")
    if resolution > args.alpha:
        print(f"  That is coarser than alpha={args.alpha}, so a false-positive "
              f"rate of {resolution:.3f}\n  (one chance hit in {args.seeds} runs) "
              f"cannot be distinguished from the nominal rate.\n"
              f"  Judge false positives against this floor, not against alpha, "
              f"or re-run with\n  more seeds (--seeds {int(np.ceil(2/args.alpha))}+).")
    # Highest AR(1) power among cells whose false-positive rates are at or below
    # the larger of alpha and the resolution floor.
    fp_ceiling = max(args.alpha, resolution)
    ok = df[(df["drift_variance_rate"] <= fp_ceiling)
            & (df["drift_ar1_rate"] <= fp_ceiling)
            & (df["noise_ar1_rate"] <= fp_ceiling)]
    print("-" * 74)
    if len(ok):
        best = ok.loc[ok["saddle_ar1_rate"].idxmax()]
        print("Best configuration keeping ALL false-positive rates <= "
              f"{fp_ceiling:.3f}:")
        print(f"  window={int(best['window'])}  sigma={best['smooth_sigma']}")
        print(f"  power: AR(1) {best['saddle_ar1_rate']:.2f}, "
              f"variance {best['saddle_variance_rate']:.2f}")
        if best["saddle_ar1_rate"] < 0.8:
            print("\n  WARNING: power is below 0.8. A negative result from this")
            print("  detector would be uninformative -- it would say more about")
            print("  the detector than about the system.")
    else:
        print("No configuration kept every false-positive rate at or below "
              f"{fp_ceiling:.3f}.")

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.4))
    heat(axes[0], df, "saddle_ar1_rate", args.windows, args.sigmas,
         "POWER — AR(1) on the saddle-node\n(higher is better; want ≥ 0.80)")
    heat(axes[1], df, "saddle_variance_rate", args.windows, args.sigmas,
         "POWER — variance on the saddle-node\n(higher is better)")
    floor = 1.0 / args.seeds
    heat(axes[2], df, "drift_ar1_rate", args.windows, args.sigmas,
         f"FALSE POSITIVES — AR(1) on monotonic drift\n(lower is better; "
         f"alpha={args.alpha}, but {args.seeds} seeds resolve no finer "
         f"than {floor:.2f})", vmax=0.5)
    fig.suptitle("Detector behaviour across analysis choices — a usable setting "
                 "needs HIGH power (left) and LOW false positives (right)",
                 fontsize=11.5, color=INK, x=0.01, ha="left", y=1.04)
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "09_ews_power_sweep.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\nWrote {out.relative_to(REPO_ROOT)}")
    print(f"Wrote {(PROCESSED / 'ews_power_sweep.csv').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
