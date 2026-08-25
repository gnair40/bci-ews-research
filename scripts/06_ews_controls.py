#!/usr/bin/env python3
"""
06_ews_controls.py
==================
Validate the early-warning-signal (EWS) detector on simulated data whose answer
we already know, BEFORE applying it to real neural recordings.

WHY THIS MUST COME FIRST
------------------------
An early-warning indicator is supposed to detect a system approaching a critical
transition. The standard indicators -- rising variance and rising lag-1
autocorrelation -- are motivated by "critical slowing down" (CSD): as a system
nears a bifurcation, it recovers from perturbations more and more slowly, so its
fluctuations grow larger and more correlated in time.

The problem is that **many things that are not bifurcations also make variance
rise.** A detector that fires on any nonstationary series is useless: it would
report a warning for ordinary drift and you would have no way to know.

So before touching real data, the detector is run on three simulated systems
whose true nature is known by construction:

  1. POSITIVE CONTROL -- a saddle-node (fold) bifurcation.
     CSD genuinely occurs. The detector SHOULD fire.
  2. NEGATIVE CONTROL -- monotonic decline plus noise, no bifurcation.
     The recovery rate never changes. The detector SHOULD stay silent.
  3. NEGATIVE CONTROL -- rising noise, no bifurcation.
     Variance rises but the recovery rate is constant, so lag-1 autocorrelation
     should NOT rise. This separates "variance went up" from "the system slowed".

If the detector fires on all three, it measures nonstationarity, not CSD -- and
it is better to learn that here than from real data.

THE MODELS, IN PLAIN LANGUAGE
-----------------------------
1. Saddle-node:   dx = (mu(t) - x^2) dt + sigma dW
   The stable equilibrium sits at x* = +sqrt(mu). Its recovery rate is
   lambda = 2*sqrt(mu). As mu is slowly lowered toward 0, that recovery rate
   goes to zero -- this IS critical slowing down, by construction. At mu = 0
   the equilibrium vanishes and the system collapses.

2. Monotonic drift:  dx = -lambda (x - m(t)) dt + sigma dW
   An Ornstein-Uhlenbeck process: it is always pulled back toward a moving mean
   m(t) with a CONSTANT recovery rate lambda. The mean declines steadily, so the
   series looks like it is deteriorating, but nothing is slowing down.

3. Rising noise:  same as (2) but lambda and m are constant while sigma grows.

"dW" is a random kick each time step (Brownian motion). "dt" is the step size.

WHAT THE DETECTOR DOES
----------------------
  * De-trend, by subtracting a Gaussian-smoothed version of the series. Without
    this, a falling mean alone inflates the variance in every window and the
    indicators become meaningless.
  * In a rolling window, compute variance and lag-1 autocorrelation.
  * Summarise each indicator's trend with Kendall's tau, a rank statistic that
    asks "does this generally go up?" without assuming a straight line.
  * Test tau against a SURROGATE NULL: generate many artificial series with the
    same length and the same short-term correlation structure but no transition,
    compute tau for each, and see where the real tau falls in that distribution.
    This is the two-sided test the literature review requires -- we ask whether
    |tau| is extreme, not merely whether tau is positive, because the indicator
    sign can invert (Titus et al. 2019; "critical speeding up").

HOW TO RUN
----------
    python3 scripts/06_ews_controls.py
    python3 scripts/06_ews_controls.py --n-surrogates 2000 --seed 7
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import gaussian_filter1d
from scipy.signal import lfilter
from scipy.stats import kendalltau

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "reports" / "figures"
PROCESSED = REPO_ROOT / "data" / "processed"

# Categorical slots 1-3 of the project palette. These three validate on the
# all-pairs test in both light and dark mode, so they are safe for a
# three-condition comparison.
C_POS, C_NEG, C_NOISE = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"


# ---------------------------------------------------------------------------
# SIMULATIONS
# ---------------------------------------------------------------------------

def simulate_saddle_node(n=8000, dt=0.01, sigma=0.06, mu0=1.0, mu1=0.02,
                         rng=None) -> tuple[np.ndarray, np.ndarray]:
    """
    POSITIVE CONTROL. A system driven slowly toward a fold bifurcation.

    dx = (mu - x^2) dt + sigma dW,  with mu lowered linearly from mu0 to mu1.

    The stable branch is x* = sqrt(mu) and its recovery rate is 2*sqrt(mu),
    which shrinks toward zero as mu does. Critical slowing down is therefore
    present *by construction* -- this is the ground truth the detector must find.

    We stop just short of mu = 0 so the series does not actually collapse; the
    question is whether the approach is detectable BEFORE the transition.
    """
    rng = rng or np.random.default_rng()
    mu = np.linspace(mu0, mu1, n)
    x = np.empty(n)
    x[0] = np.sqrt(mu0)
    for t in range(1, n):
        drift = (mu[t-1] - x[t-1]**2) * dt
        x[t] = x[t-1] + drift + sigma * np.sqrt(dt) * rng.standard_normal()
    return x, mu


def simulate_monotonic_drift(n=8000, dt=0.01, sigma=0.06, lam=2.0,
                             start=1.0, end=0.15, rng=None):
    """
    NEGATIVE CONTROL 1. Steady deterioration with NO bifurcation.

    dx = -lam (x - m(t)) dt + sigma dW,  m declining linearly.

    The pull-back strength `lam` is constant, so the recovery rate never
    changes: there is no critical slowing down at any point. The series
    nevertheless *looks* like a system getting worse -- which is exactly the
    trap. A detector that fires here is measuring drift, not CSD.
    """
    rng = rng or np.random.default_rng()
    m = np.linspace(start, end, n)
    x = np.empty(n)
    x[0] = start
    for t in range(1, n):
        x[t] = x[t-1] - lam * (x[t-1] - m[t-1]) * dt \
               + sigma * np.sqrt(dt) * rng.standard_normal()
    return x, m


def simulate_rising_noise(n=8000, dt=0.01, lam=2.0, mean=1.0,
                          sigma0=0.03, sigma1=0.15, rng=None):
    """
    NEGATIVE CONTROL 2. Growing noise, constant recovery rate.

    Variance rises here for a reason that has nothing to do with a bifurcation.
    A useful detector should show rising variance but NOT rising lag-1
    autocorrelation, because the system's speed of recovery is unchanged.
    This is the sharpest test of whether the two indicators are doing different
    work, or whether they are both just reading "the series got noisier".
    """
    rng = rng or np.random.default_rng()
    sig = np.linspace(sigma0, sigma1, n)
    x = np.empty(n)
    x[0] = mean
    for t in range(1, n):
        x[t] = x[t-1] - lam * (x[t-1] - mean) * dt \
               + sig[t-1] * np.sqrt(dt) * rng.standard_normal()
    return x, sig


# ---------------------------------------------------------------------------
# THE DETECTOR
# ---------------------------------------------------------------------------

def detrend(x: np.ndarray, smooth_sigma: float) -> np.ndarray:
    """
    Remove the slow-moving mean, keeping only the fluctuations around it.

    Why this is mandatory: if the mean of the series is falling, then any window
    that spans part of that fall contains the trend itself, and the computed
    "variance" is dominated by the trend rather than by the fluctuations. Every
    indicator would then rise for a trivial reason.

    A Gaussian filter is a weighted moving average; subtracting it leaves the
    residual. `smooth_sigma` sets how much is treated as "trend" -- a genuine
    analysis choice, which is why it is swept rather than fixed (see --help).
    """
    return x - gaussian_filter1d(x, sigma=smooth_sigma, mode="nearest")


def lag1_autocorr(w: np.ndarray) -> float:
    """
    Correlation of the series with itself shifted by one step.

    Interpretation: how much does this moment's value tell you about the next?
    A slow system "remembers" longer, so this rises as recovery slows. That is
    the core CSD prediction.
    """
    if len(w) < 3:
        return np.nan
    a, b = w[:-1], w[1:]
    sa, sb = a.std(), b.std()
    if sa == 0 or sb == 0:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def rolling_indicators(x: np.ndarray, window: int, step: int) -> dict:
    """
    Compute variance and lag-1 autocorrelation in a sliding window.

    Implemented with `sliding_window_view`, which produces every window as a row
    of one array without copying the data, so the statistics are computed for
    all windows at once instead of in a Python loop. Same numbers, ~100x faster
    -- which is what makes the parameter sweep in scripts/07 feasible.
    """
    if len(x) < window:
        return {"index": np.array([]), "variance": np.array([]),
                "ar1": np.array([])}
    w = sliding_window_view(x, window)[::step]          # (n_windows, window)
    idx = np.arange(0, len(x) - window + 1, step) + window // 2
    var = w.var(axis=1)

    a, b = w[:, :-1], w[:, 1:]
    a_c = a - a.mean(axis=1, keepdims=True)
    b_c = b - b.mean(axis=1, keepdims=True)
    denom = np.sqrt((a_c**2).sum(axis=1) * (b_c**2).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        ac1 = np.where(denom > 0, (a_c * b_c).sum(axis=1) / denom, np.nan)
    return {"index": idx, "variance": var, "ar1": ac1}


def kendall_trend(y: np.ndarray) -> float:
    """Kendall's tau: +1 = always rising, -1 = always falling, 0 = no trend."""
    good = np.isfinite(y)
    if good.sum() < 4:
        return np.nan
    tau, _ = kendalltau(np.arange(good.sum()), y[good])
    return float(tau)


def ar1_surrogates(x: np.ndarray, n_surr: int, rng) -> np.ndarray:
    """
    Generate `n_surr` AR(1) surrogates at once, as an (n_surr, len(x)) array.

    `lfilter` applies the recursion s[t] = a*s[t-1] + e[t] in compiled code
    across every surrogate simultaneously, replacing a nested Python loop.
    """
    n = len(x)
    a = lag1_autocorr(x)
    a = 0.0 if not np.isfinite(a) else float(np.clip(a, -0.99, 0.99))
    sd = float(np.std(x))
    resid_sd = sd * np.sqrt(max(1e-12, 1 - a**2))
    e = rng.standard_normal((n_surr, n)) * resid_sd
    e[:, 0] = rng.standard_normal(n_surr) * sd          # stationary start
    return lfilter([1.0], [1.0, -a], e, axis=1)


def ar1_surrogate(x: np.ndarray, rng) -> np.ndarray:
    """
    Build one artificial series with the same length, variance and lag-1
    correlation as `x`, but with NO transition in it.

    Why: a tau of, say, +0.6 means nothing on its own -- short, autocorrelated
    series produce large trends by chance all the time. Comparing against many
    such surrogates tells us how often chance alone would do this well.
    """
    n = len(x)
    a = lag1_autocorr(x)
    a = 0.0 if not np.isfinite(a) else float(np.clip(a, -0.99, 0.99))
    resid_sd = np.std(x) * np.sqrt(max(1e-12, 1 - a**2))
    s = np.empty(n)
    s[0] = rng.standard_normal() * np.std(x)
    for t in range(1, n):
        s[t] = a * s[t-1] + resid_sd * rng.standard_normal()
    return s


def surrogate_test(x: np.ndarray, observed_tau: float, window: int, step: int,
                   smooth_sigma: float, indicator: str, n_surr: int,
                   rng) -> dict:
    """
    Two-sided significance test for an indicator's trend.

    TWO-SIDED, deliberately. The literature review requires it: a compressed
    basin of attraction can produce FALLING variance and autocorrelation before
    a transition ("critical speeding up", Titus et al. 2019), so a one-sided
    test for tau > 0 would miss real signals and is a weaker hypothesis. We ask
    instead whether |tau| is more extreme than chance.
    """
    surr = ar1_surrogates(x, n_surr, rng)
    # De-trend every surrogate in one call (axis=1 = along time).
    surr_d = surr - gaussian_filter1d(surr, sigma=smooth_sigma, axis=1,
                                      mode="nearest")
    taus = np.empty(n_surr)
    for i in range(n_surr):
        ind = rolling_indicators(surr_d[i], window, step)
        taus[i] = kendall_trend(ind[indicator])
    finite = taus[np.isfinite(taus)]
    p_two = float(np.mean(np.abs(finite) >= abs(observed_tau))) if len(finite) else np.nan
    return {"tau": observed_tau, "p_two_sided": p_two,
            "surrogate_tau_mean": float(np.mean(finite)) if len(finite) else np.nan,
            "surrogate_tau_sd": float(np.std(finite)) if len(finite) else np.nan,
            "n_surrogates": int(len(finite))}


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=8000, help="time steps per series")
    ap.add_argument("--window", type=int, default=1000, help="rolling window (steps)")
    ap.add_argument("--step", type=int, default=50, help="window advance (steps)")
    ap.add_argument("--smooth-sigma", type=float, default=200.0,
                    help="Gaussian sigma used for de-trending")
    ap.add_argument("--n-surrogates", type=int, default=500)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    print("=" * 74)
    print("EARLY-WARNING-SIGNAL DETECTOR — VALIDATION ON KNOWN SYSTEMS")
    print("=" * 74)
    print(f"window={args.window} steps · step={args.step} · "
          f"detrend sigma={args.smooth_sigma} · surrogates={args.n_surrogates}")

    models = {
        "saddle_node": {
            "label": "Saddle-node bifurcation",
            "role": "POSITIVE control — CSD is present",
            "expect": {"variance": "rise", "ar1": "rise"},
            "color": C_POS,
            "series": simulate_saddle_node(n=args.n, rng=rng)[0],
        },
        "monotonic_drift": {
            "label": "Monotonic decline + noise",
            "role": "NEGATIVE control — no bifurcation",
            "expect": {"variance": "flat", "ar1": "flat"},
            "color": C_NEG,
            "series": simulate_monotonic_drift(n=args.n, rng=rng)[0],
        },
        "rising_noise": {
            "label": "Rising noise, constant recovery rate",
            "role": "NEGATIVE control — variance rises, system does not slow",
            "expect": {"variance": "rise", "ar1": "flat"},
            "color": C_NOISE,
            "series": simulate_rising_noise(n=args.n, rng=rng)[0],
        },
    }

    results = {}
    for key, m in models.items():
        x = m["series"]
        xd = detrend(x, args.smooth_sigma)
        ind = rolling_indicators(xd, args.window, args.step)
        m["detrended"], m["ind"] = xd, ind

        print(f"\n--- {m['label']}")
        print(f"    {m['role']}")
        res = {}
        for name in ("variance", "ar1"):
            tau = kendall_trend(ind[name])
            st = surrogate_test(xd, tau, args.window, args.step,
                                args.smooth_sigma, name, args.n_surrogates, rng)
            fired = np.isfinite(st["p_two_sided"]) and st["p_two_sided"] < args.alpha
            verdict = "FIRES" if fired else "silent"
            expect = m["expect"][name]
            correct = (verdict == "FIRES") == (expect == "rise")
            mark = "OK " if correct else "!! "
            print(f"    {mark}{name:<9s} tau={tau:+.3f}  p={st['p_two_sided']:.4f}"
                  f"  -> {verdict:<7s} (expected {expect})")
            res[name] = {**st, "fired": bool(fired), "expected": expect,
                         "as_expected": bool(correct)}
        results[key] = {"label": m["label"], "role": m["role"], "indicators": res}

    # ---- overall verdict -------------------------------------------------
    all_ok = all(r["indicators"][k]["as_expected"]
                 for r in results.values() for k in ("variance", "ar1"))
    print("\n" + "=" * 74)
    if all_ok:
        print("PASS — the detector fires on the bifurcation and stays silent on")
        print("       ordinary drift. Lag-1 autocorrelation correctly separates")
        print("       'the system slowed' from 'the series got noisier'.")
    else:
        print("FAIL — the detector did not behave as required. Read the rows")
        print("       marked '!!' above. Do NOT apply it to real data yet.")
    print("=" * 74)

    # ---- figure ----------------------------------------------------------
    fig, axes = plt.subplots(3, 3, figsize=(16, 9), squeeze=False)
    for col, (key, m) in enumerate(models.items()):
        ind = m["ind"]
        rows = [("Simulated series", np.arange(len(m["series"])), m["series"], None),
                ("Rolling variance", ind["index"], ind["variance"], "variance"),
                ("Rolling lag-1 autocorrelation", ind["index"], ind["ar1"], "ar1")]
        for row, (title, xs, ys, ind_name) in enumerate(rows):
            ax = axes[row][col]
            ax.plot(xs, ys, color=m["color"], linewidth=1.0 if row == 0 else 1.8)
            if row == 0:
                ax.set_title(f"{m['label']}\n{m['role']}", fontsize=10,
                             color=INK, loc="left", pad=8)
            else:
                r = results[key]["indicators"][ind_name]
                flag = "FIRES" if r["fired"] else "silent"
                ax.set_title(f"{title}   τ={r['tau']:+.2f}, p={r['p_two_sided']:.3f}"
                             f"  → {flag}", fontsize=9.5, color=INK,
                             loc="left", pad=6)
            ax.grid(True, color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            for s in ("left", "bottom"):
                ax.spines[s].set_color(GRID)
            ax.tick_params(colors=INK_MUTED, labelsize=8)
            if row == 2:
                ax.set_xlabel("Time step", fontsize=9, color=INK_MUTED)
    fig.suptitle("EWS detector validation — it must fire on the LEFT column only "
                 "(variance rises in two columns; only autocorrelation "
                 "distinguishes them)",
                 fontsize=11.5, color=INK, x=0.01, ha="left", y=1.02)
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "08_ews_controls.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\nWrote {out.relative_to(REPO_ROOT)}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    payload = {"settings": vars(args), "passed": bool(all_ok), "results": results}
    (PROCESSED / "ews_control_results.json").write_text(json.dumps(payload, indent=2))
    print(f"Wrote {(PROCESSED / 'ews_control_results.json').relative_to(REPO_ROOT)}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
