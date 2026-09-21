#!/usr/bin/env python3
"""
71_drift_sweep_design.py
========================
Designing the drift sweep (Procedure 78) before building anything.

WHAT THIS IS
------------
Procedure 78 is the centrepiece of the physical experiment: impose a drift with a
time constant I control, sweep that constant, and measure how monitorable the
array is at each speed. That gives a curve of monitorability against drift speed,
with cortex marked as a point on it.

When I first wrote that procedure the numbers in it were guesses -- "sweep tau
from 5 s to 2000 s across 8 levels, 10 blocks each" sounded plausible and had
nothing behind it. This works out what they should be:

  1. Which tau values put the measurement where the curve actually moves.
  2. Which tau corresponds to what cortex shows, so I know whether cortex even
     falls inside the range the rig can produce.
  3. How many blocks per level the curve needs to be readable.

TWO THINGS THE FIRST VERSION OF THIS SCRIPT GOT WRONG
-----------------------------------------------------
The first version aimed at the wrong target and then hid the failure. Both are
worth stating because they change what the rig should be compared against.

1. It aimed at C18's pooled figures, 0.902 and 0.784. Those come from episodes
   carrying a sub-threshold injected fault ramp, not from fault-free recording
   (scripts/70). The rig's natural-drift arm has no injected fault, so the
   fault-free figures are the ones it has to match. This reads them from
   scripts/70's output rather than hardcoding them.

2. It inverted tau from a number the estimator cannot produce. At the no-overlap
   spacing an episode keeps about 10 windows, and the sample lag-1 correlation
   is badly biased downward at that length -- it tops out near 0.62 even when
   the true correlation is 0.99. Asking which tau gives a measured 0.902 has no
   answer, so the script produced NaN, and then asserted "both participants fall
   inside that band" anyway. It now reports the ceiling explicitly and refuses
   to invert past it.

THIS IS A DESIGN CALCULATION, NOT A RESULT
------------------------------------------
It rests on a model: brightness drifts as an Ornstein-Uhlenbeck process (a random
walk pulled back toward its mean, the standard way to write "drifts slowly but
does not wander off"), sensor noise is white, and the monitor's risk tracks the
window-averaged signal. Real optics will not obey that exactly.

So the output is a sweep range and a block count, not a prediction of what the
rig will show. If the model is wrong the curve still gets measured; I would just
have chosen the sampling points less well.

Requires: python3 scripts/70_autocorr_by_severity.py
Usage:    python3 scripts/71_drift_sweep_design.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

# Window geometry, identical to the neural analysis.
WINDOW_BINS = 1500
STEP_BINS = 250
FPS = 50                      # bins per second, from Procedure 52
WINDOW_S = WINDOW_BINS / FPS  # 30 s
STEP_S = STEP_BINS / FPS      # 5 s
BLOCK_BINS = 15000            # one recorded block, Procedure 66
N_WINDOWS = (BLOCK_BINS - WINDOW_BINS) // STEP_BINS + 1
DECIMATE = 6                  # every 6th window shares no data with its neighbour
N_KEPT = len(range(0, N_WINDOWS, DECIMATE))
SPACING_S = DECIMATE * STEP_S  # 30 s between kept windows

# Drift-to-noise ratio: 1.0 means slow drift and white sensor noise contribute
# equally per bin. A property of the built rig, not of cortex; swept below to
# check the design does not depend on it.
DNR = 1.0
DNR_SENSITIVITY = [0.3, 1.0, 3.0]

SEED = 20260826
REPS = 300
N_LEVELS = 8              # sweep points, as Procedure 78 was drafted
LONG_BLOCKS = 200             # blocks concatenated for the large-sample value


def ou(shape: tuple[int, int], tau_bins: float, rng: np.random.Generator) -> np.ndarray:
    """Ornstein-Uhlenbeck paths, unit stationary variance, one per row.

    An OU process sampled at fixed steps is an AR(1) recursion, so this is a
    one-pole IIR filter applied to white noise. `lfilter` runs that recursion in
    C across every row at once; a Python loop over 15,000 bins x hundreds of
    repeats x two dozen time constants does not finish in reasonable time.
    `zi` seeds the filter with a draw from the stationary distribution, so the
    paths start in equilibrium rather than at zero and warming up.
    """
    reps, n = shape
    if tau_bins <= 0:
        return rng.normal(0, 1, (reps, n))
    a = np.exp(-1.0 / tau_bins)
    s = np.sqrt(1 - a * a)
    eps = rng.normal(0, s, (reps, n))
    zi = (rng.normal(size=(reps, 1)) * a)          # x[-1] ~ N(0,1), scaled by the pole
    out, _ = lfilter([1.0], [1.0, -a], eps, axis=1, zi=zi)
    return out


def lag1(y: np.ndarray) -> np.ndarray:
    """Lag-1 sample correlation of each row. Rows with no variance give nan."""
    y = np.atleast_2d(y)
    a, b = y[:, :-1], y[:, 1:]
    am = a - a.mean(1, keepdims=True)
    bm = b - b.mean(1, keepdims=True)
    den = np.sqrt((am * am).sum(1) * (bm * bm).sum(1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 1e-12, (am * bm).sum(1) / den, np.nan)


def windows(sig: np.ndarray) -> np.ndarray:
    """Window means of each row, by cumulative sum rather than a slice per window."""
    sig = np.atleast_2d(sig)
    starts = np.arange(0, sig.shape[1] - WINDOW_BINS + 1, STEP_BINS)
    c = np.concatenate([np.zeros((sig.shape[0], 1)), np.cumsum(sig, axis=1)], axis=1)
    return (c[:, starts + WINDOW_BINS] - c[:, starts]) / WINDOW_BINS


def block_rs(tau_s: float, rng: np.random.Generator, dnr: float, reps: int) -> np.ndarray:
    """Lag-1 r that each of `reps` independent single blocks would report."""
    sig = ou((reps, BLOCK_BINS), tau_s * FPS, rng) \
        + rng.normal(0, 1 / max(dnr, 1e-9), (reps, BLOCK_BINS))
    return lag1(windows(sig)[:, ::DECIMATE])


def measured_r(tau_s: float, rng: np.random.Generator, dnr: float = DNR,
               reps: int = REPS) -> float:
    """Median lag-1 r a single block would report, at the no-overlap spacing.

    This is what the rig actually gets to see: one block, decimated to
    non-overlapping windows, and it inherits the estimator's small-sample bias.
    """
    return float(np.nanmedian(block_rs(tau_s, rng, dnr, reps)))


def asymptotic_r(tau_s: float, rng: np.random.Generator, dnr: float = DNR) -> float:
    """The underlying correlation, from a record long enough to be unbiased.

    One continuous record, not many blocks stitched together -- a join between
    two independent paths would break the correlation this is trying to measure.
    """
    n = BLOCK_BINS * LONG_BLOCKS
    sig = ou((1, n), tau_s * FPS, rng) + rng.normal(0, 1 / max(dnr, 1e-9), (1, n))
    return float(lag1(windows(sig)[:, ::DECIMATE])[0])


def estimator_ceiling(n: int, rng: np.random.Generator, reps: int = 20000) -> float:
    """Highest value the n-point lag-1 estimator typically reports, as rho -> 1.

    This is a property of the estimator and the series length alone, so it is
    measured on an AR(1) series at rho = 0.999 directly, not through the OU and
    sensor-noise model. Measuring it by pushing tau to infinity in that model
    gives the wrong answer: at very long tau the drift barely moves inside one
    block, so the window means are dominated by sensor noise and the reported r
    collapses toward zero rather than rising to the ceiling.
    """
    rho = 0.999
    a, sd = rho, np.sqrt(1 - rho * rho)
    eps = rng.normal(0, sd, (reps, n))
    zi = rng.normal(size=(reps, 1)) * a
    x, _ = lfilter([1.0], [1.0, -a], eps, axis=1, zi=zi)
    return float(np.nanmedian(lag1(x)))


def tau_label(t: float) -> str:
    """Enough precision that neighbouring sweep points do not print identically."""
    return f"{t:.1f} s" if t < 10 else f"{t:.0f} s"


def n_eff(n: float, r: float) -> float:
    return n * (1 - r) / (1 + r)


def invert(taus: np.ndarray, curve: np.ndarray, target: float) -> float:
    """Tau whose measured r equals `target`; nan if the target is off the curve.

    `curve` is forced monotone first, so np.interp is well defined. A target
    above the curve's ceiling has no tau -- returning nan there is the correct
    answer and the caller must say so rather than clamp.
    """
    mono = np.maximum.accumulate(curve)
    if not np.isfinite(target) or target < mono[0] or target > mono[-1]:
        return float("nan")
    return float(np.interp(target, mono, taus))


def load_fault_free_targets() -> dict:
    """The fault-free no-overlap correlations from scripts/70, with intervals."""
    p = OUT / "autocorr_by_severity.json"
    if not p.exists():
        raise SystemExit(
            "missing data/processed/autocorr_by_severity.json -- "
            "run `python3 scripts/70_autocorr_by_severity.py` first")
    d = json.loads(p.read_text())
    out = {}
    for name, pres in d["participants"].items():
        row = pres["by_severity"]["6"]["none"]
        out[name] = {"r": row["lag1_r_median"], "ci95": row["ci95"],
                     "n_windows": row["n_windows_median"],
                     "n_episodes": row["n_episodes"]}
    return out


def main() -> int:
    rng = np.random.default_rng(SEED)
    targets = load_fault_free_targets()

    # ---- 1. how the imposed time constant maps to what the rig would measure
    taus = np.logspace(np.log10(1.0), np.log10(3000.0), 24)
    rows = []
    for t in taus:
        m = measured_r(t, rng)
        rows.append({"tau_s": float(t), "measured_r_one_block": m,
                     "asymptotic_r": asymptotic_r(t, rng),
                     "n_eff_one_block": n_eff(N_KEPT, m)})
    mcurve = np.array([x["measured_r_one_block"] for x in rows])

    # ---- 2. the estimator's ceiling at this series length
    ceiling = estimator_ceiling(N_KEPT, rng)

    # ---- 3. where cortex lands, and whether it lands on the curve at all
    cortex = {}
    for name, t in targets.items():
        tau_pt = invert(taus, mcurve, t["r"])
        tau_lo = invert(taus, mcurve, t["ci95"][0])
        tau_hi = invert(taus, mcurve, t["ci95"][1])
        cortex[name] = {
            **t, "tau_s": tau_pt, "tau_ci95": [tau_lo, tau_hi],
            "on_curve": bool(np.isfinite(tau_pt)),
            "ci_fully_on_curve": bool(np.isfinite(tau_lo) and np.isfinite(tau_hi)),
        }

    # ---- 4. the informative band: where the measured curve still has slope
    mono = np.maximum.accumulate(mcurve)
    lo_r, hi_r = mono[0] + 0.05 * (mono[-1] - mono[0]), mono[0] + 0.95 * (mono[-1] - mono[0])
    band = [invert(taus, mcurve, lo_r), invert(taus, mcurve, hi_r)]

    # ---- 5. how many blocks per level, against the gap the sweep must resolve
    finite_taus = [c["tau_s"] for c in cortex.values() if np.isfinite(c["tau_s"])]
    probe_tau = float(np.median(finite_taus)) if finite_taus else 100.0
    # The sweep's job is to trace a curve, so the step it has to resolve is the
    # r difference between ADJACENT levels, not the distance between the two
    # participants. Eight levels log-spaced across the informative band:
    cortex_gap = abs(targets["T11"]["r"] - targets["T5"]["r"]) if len(targets) > 1 else 0.1

    def level_gap(nl: int) -> float:
        """Median step in measured r between adjacent levels, for `nl` levels.

        Read off the tau -> r curve already simulated above rather than
        re-simulating at each candidate level count, so every row of the cost
        table below and the 8-level figure quoted in the text come from one
        method and cannot disagree. `mono` is the curve forced monotone, which
        it is in truth -- slower drift cannot lower the correlation -- so the
        monotonicity removes simulation jitter rather than imposing a shape.
        """
        if not (np.isfinite(band[0]) and np.isfinite(band[1])) or nl < 2:
            return float("nan")
        lv = np.logspace(np.log10(band[0]), np.log10(band[1]), nl)
        return float(np.median(np.abs(np.diff(np.interp(lv, taus, mono)))))

    gap = level_gap(N_LEVELS)
    if not np.isfinite(gap):
        gap = cortex_gap

    prec = []
    for b in [5, 10, 20, 40, 80]:
        ests = [float(np.nanmedian(block_rs(probe_tau, rng, DNR, b))) for _ in range(200)]
        hw = float(1.96 * np.std(ests))
        prec.append({"blocks": b, "sd_of_r_estimate": float(np.std(ests)),
                     "half_width_95": hw,
                     "resolves_adjacent_levels": bool(hw < gap / 2),
                     "resolves_cortex_gap": bool(hw < cortex_gap / 2)})

    # The half-width falls as 1/sqrt(blocks), so the count needed for a given
    # target can be read off the fitted constant instead of only reporting
    # whichever tested value happened to clear it. Fitted on the measured points
    # rather than assumed, so the fit quality is visible in the JSON.
    bs = np.array([q["blocks"] for q in prec], float)
    hws = np.array([q["half_width_95"] for q in prec], float)
    k = float(np.mean(hws * np.sqrt(bs)))
    fit_resid = float(np.max(np.abs(hws - k / np.sqrt(bs))))

    def blocks_for(target_hw: float) -> int:
        return int(np.ceil((k / target_hw) ** 2))

    enough = next((q["blocks"] for q in prec if q["resolves_adjacent_levels"]), None)
    enough_fitted = blocks_for(gap / 2) if np.isfinite(gap) and gap > 0 else None

    # ---- 5b. levels against recording time. Packing more levels into the same
    #          band shrinks the step each one has to resolve, and the cost of
    #          resolving it grows as the square. This is the real design knob.
    cost = []
    if np.isfinite(band[0]) and np.isfinite(band[1]):
        for nl in [4, 5, 6, 8, 10]:
            g = level_gap(nl)
            if not np.isfinite(g) or g <= 0:
                continue
            b = blocks_for(g / 2)
            hours = nl * b * (BLOCK_BINS / FPS) / 3600.0
            cost.append({"levels": nl, "step_in_r": g, "blocks_per_level": b,
                         "total_blocks": nl * b, "recording_hours": hours})

    # ---- 6. does the design depend on the drift-to-noise ratio?
    sens = [{"dnr": d, "measured_r_at_probe_tau": measured_r(probe_tau, rng, dnr=d, reps=REPS)}
            for d in DNR_SENSITIVITY]

    result = {
        "model": "Ornstein-Uhlenbeck drift plus white sensor noise, "
                 "window-averaged. A DESIGN CALCULATION, NOT A MEASUREMENT.",
        "targets_are": "fault-free no-overlap correlations from scripts/70, "
                       "NOT C18's pooled 0.902/0.784",
        "drift_to_noise_ratio": DNR, "window_s": WINDOW_S, "step_s": STEP_S,
        "windows_per_block": N_WINDOWS, "windows_after_decimation": N_KEPT,
        "spacing_between_kept_windows_s": SPACING_S,
        "estimator_ceiling_at_this_length": ceiling,
        "cortex": cortex, "informative_band_s": band,
        "blocks_per_level_needed_tested": enough,
        "curve": rows, "precision": prec, "dnr_sensitivity": sens,
        "adjacent_level_gap": gap, "cortex_gap": cortex_gap,
        "half_width_fit_constant": k, "half_width_fit_max_resid": fit_resid,
        "blocks_per_level_fitted": enough_fitted,
        "levels_vs_recording_cost": cost,
    }
    (OUT / "drift_sweep_design.json").write_text(json.dumps(result, indent=2))

    # ---------------------------------------------------------------- report
    L = ["# Designing the drift sweep before building the rig\n",
         "**Generated by `scripts/71_drift_sweep_design.py` — do not edit by hand.**\n",
         "> ## SUPERSEDED 21 September 2026\n"
         ">\n"
         "> **The drift sweep is no longer an arm of this project.** It was "
         "demoted to optional on 19 September "
         "(`research/RIG_PREREGISTRATION.md` §13) and the study it belonged "
         "to was replaced entirely on 20 September (§14). The live design is "
         "`physical/docs/`, and the experiments are P-1 to P-6 in "
         "`physical/docs/02_EXPERIMENTS.md`.\n"
         ">\n"
         "> The calculation below is kept because it is correct, because the "
         "estimator ceiling it identifies applies to any short risk series, "
         "and because the route a design took is part of the research record. "
         "**Nothing in it should be read as a plan.**\n",
         "Procedure 78 sweeps an imposed drift time constant and measures how "
         "monitorable the array is at each speed. When that procedure was first "
         "written its numbers were guesses. This works out what they should be.\n",
         "> **This is a design calculation, not a result.** It assumes drift is an "
         "Ornstein-Uhlenbeck process, sensor noise is white, and the monitor's risk "
         "tracks the window-averaged signal. Real optics will not obey that exactly. "
         "The output is where to put the sampling points, not what the rig will show.\n",
         f"> **The comparison target is the fault-free figure, not C18's.** The rig's "
         f"natural-drift arm injects no fault, so it is compared against the "
         f"fault-free no-overlap correlations from `scripts/70` "
         f"(**{targets['T11']['r']:.3f}** on T11, **{targets['T5']['r']:.3f}** on "
         f"T5), not against C18's pooled 0.902 and 0.784, which are raised by the "
         f"injected ramp.\n"]
    A = L.append

    A("## The ceiling this measurement runs into\n")
    A(f"A block is {BLOCK_BINS / FPS:.0f} s, giving {N_WINDOWS} windows, "
      f"{N_KEPT} of them once decimated to zero overlap. The sample lag-1 "
      f"correlation is heavily biased downward at {N_KEPT} points: feed it a "
      f"series whose true correlation is 0.999 and the median value it reports "
      f"is **{ceiling:.2f}**. **No signal, however slowly it drifts, makes one "
      f"block read much above that.** Any target above it has no corresponding "
      f"time constant, which is why the first version of this script produced "
      f"NaN when asked which drift speed gives C18's 0.902.\n")

    A("## What the imposed drift speed does to the measurement\n")
    A("| Imposed time constant | What one block would measure | "
      "Underlying correlation | Effective independent windows per block |")
    A("|---|---|---|---|")
    for x in rows:
        A(f"| {tau_label(x['tau_s'])} | {x['measured_r_one_block']:.3f} | "
          f"{x['asymptotic_r']:.3f} | {x['n_eff_one_block']:.2f} |")
    A("")
    A(f"The two middle columns differ because of the small-sample bias: the "
      f"third column is what the drift really does, the second is what "
      f"{N_KEPT} windows can see of it. The rig reports the second, and so does "
      f"every no-overlap number already in this project.\n")

    A("## Where cortex falls on it\n")
    for name in ("T11", "T5"):
        c = cortex.get(name)
        if not c:
            continue
        A(f"- **{name}** measures **{c['r']:.3f}** fault-free "
          f"[{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}] on {c['n_episodes']} "
          f"episodes of {c['n_windows']:.0f} windows. "
          + (f"That corresponds to an imposed time constant of about "
             f"**{c['tau_s']:.0f} s**"
             + (f" (interval {c['tau_ci95'][0]:.0f} s to "
                f"{c['tau_ci95'][1]:.0f} s)." if c["ci_fully_on_curve"]
                else f", but its confidence interval runs off the end of the "
                     f"curve, so the interval is open-ended and the point "
                     f"estimate should not be quoted alone.")
             if c["on_curve"] else
             f"That is **above the {ceiling:.2f} ceiling**, so no imposed time "
             f"constant reproduces it and the rig cannot be asked to match it."))
    A("")
    on = [n for n, c in cortex.items() if c["on_curve"]]
    off = [n for n, c in cortex.items() if not c["on_curve"]]
    if off:
        verb = "cannot" if len(off) == 1 else "cannot"
        A(f"**{' and '.join(off)} {verb} be placed on this curve.** That is a "
          f"finding about the measurement, not a failure of the rig: at "
          f"{N_KEPT} windows the estimator saturates below the value, so the "
          f"comparison has to be made on a longer block or with a less biased "
          f"estimator.")
    if on:
        verb = "falls" if len(on) == 1 else "both fall"
        subj = on[0] if len(on) == 1 else " and ".join(on)
        A(f"**{subj} {verb} inside the range the rig can produce**, which is "
          f"what had to be true for the sweep to be worth running. Note that "
          f"this is a much weaker statement than the first version of this "
          f"script made: the intervals are wide, and on T11 the interval runs "
          f"off the end of the curve entirely.")

    A("")
    A("## How many blocks per level\n")
    A(f"Spread of the estimated r across repeats, at a cortex-like setting "
      f"(tau = {probe_tau:.0f} s):\n")
    A("| Blocks per level | SD of the r estimate | 95% half-width | "
      "Separates adjacent sweep levels? | Separates T11 from T5? |")
    A("|---|---|---|---|---|")
    for p in prec:
        A(f"| {p['blocks']} | {p['sd_of_r_estimate']:.4f} | "
          f"{p['half_width_95']:.4f} | "
          f"{'yes' if p['resolves_adjacent_levels'] else 'no'} | "
          f"{'yes' if p['resolves_cortex_gap'] else 'no'} |")
    A("")
    A(f"With {N_LEVELS} levels log-spaced across the informative band, "
      f"neighbouring levels differ by about **{gap:.3f}** in measured r. That, "
      f"not the participant gap, is what the sweep has to resolve to trace a "
      f"curve rather than a smear. Resolving it means a half-width below half "
      f"that. "
      + (f"**{enough} blocks per level** is the first tested count that clears it"
         + (" — the 10 the procedure guessed is enough." if enough <= 10 else
            " — more than the 10 the procedure guessed.")
         if enough else
         f"**No tested count clears it.** Eighty blocks per level still leaves "
         f"a half-width of {prec[-1]['half_width_95']:.3f} against a target of "
         f"{gap / 2:.3f}. The half-width falls as one over the square root of "
         f"the block count (fitted constant {k:.3f}, worst residual "
         f"{fit_resid:.4f}), so reaching the target needs about "
         f"**{enough_fitted} blocks per level** — "
         f"{N_LEVELS * enough_fitted * (BLOCK_BINS / FPS) / 3600.0:.0f} hours of "
         f"recording for the sweep alone. **That is not a feasible experiment**, "
         f"and it is the central thing this calculation found: Procedure 78 as "
         f"drafted cannot be run."))

    if cost:
        A("")
        A("## The way out: fewer levels\n")
        A("Spreading the same band over fewer levels makes each step bigger, and "
          "the cost of resolving a step falls as its square. That is the knob "
          "worth turning before anything else.\n")
        A("| Levels | Step in measured r | Blocks per level | Total blocks | "
          "Recording time |")
        A("|---|---|---|---|---|")
        for c in cost:
            A(f"| {c['levels']} | {c['step_in_r']:.3f} | "
              f"{c['blocks_per_level']} | {c['total_blocks']} | "
              f"{c['recording_hours']:.1f} h |")
        A("")
        feasible = [c for c in cost if c["recording_hours"] <= 25]
        if feasible:
            c = max(feasible, key=lambda z: z["levels"])
            A(f"Taking 25 hours as the most recording that fits the schedule, "
              f"**{c['levels']} levels at {c['blocks_per_level']} blocks each** "
              f"is the finest sweep that can actually be run "
              f"({c['recording_hours']:.1f} h). Eight levels, as Procedure 78 "
              f"was drafted, cannot.")
        else:
            A("**No level count tested fits inside 25 hours of recording.** The "
              "sweep needs a different measurement, not a different schedule — "
              "a longer block would give more windows and a less biased "
              "estimator, and that is the change to cost out next.")

    A("")
    A("## Does the answer depend on the drift-to-noise ratio?\n")
    A(f"The ratio is set to {DNR} as a stand-in; it is a property of the built "
      f"rig and is not known yet. At tau = {probe_tau:.0f} s:\n")
    A("| Drift-to-noise ratio | What one block would measure |")
    A("|---|---|")
    for s in sens:
        A(f"| {s['dnr']} | {s['measured_r_at_probe_tau']:.3f} |")
    spread = max(s["measured_r_at_probe_tau"] for s in sens) - \
        min(s["measured_r_at_probe_tau"] for s in sens)
    A("")
    A(f"Spread across the range tested is {spread:.3f}"
      + (f", comfortably under half the {gap:.3f} step the sweep has to "
         f"resolve, so the design does not hinge on getting this ratio right."
         if spread < gap / 2 else
         f", comparable to or larger than the {gap:.3f} gap the sweep has to "
         f"resolve. The ratio therefore has to be measured on the built rig "
         f"before the sweep results mean anything."))

    A("")
    A("## What to put in Procedure 78\n")
    if np.isfinite(band[0]) and np.isfinite(band[1]):
        A(f"- **Sweep range:** log-spaced between **{band[0]:.0f} s** and "
          f"**{band[1]:.0f} s**, which is where the measured curve still has "
          f"slope. Outside it the curve is flat and a level buys nothing.")
    else:
        A(f"- **Sweep range:** not determined — the measured curve does not "
          f"span a usable range at this block length.")
    best = max([c for c in cost if c["recording_hours"] <= 25],
               key=lambda z: z["levels"], default=None) if cost else None
    A(f"- **Number of levels and blocks per level:** "
      + (f"**{best['levels']} levels, {best['blocks_per_level']} blocks each** "
         f"({best['recording_hours']:.1f} h of recording). The drafted 8 levels "
         f"at 10 blocks would need about {enough_fitted} blocks per level to "
         f"resolve, which is not runnable." if best else
         f"**not settled.** Eight levels needs about {enough_fitted} blocks "
         f"each, and no level count tested fits a workable schedule. Resolve "
         f"this before buying parts."))
    A(f"- **Report on the no-overlap spacing** ({SPACING_S:.0f} s between kept "
      f"windows), against the fault-free cortical figures, and quote the "
      f"estimator's {ceiling:.2f} ceiling alongside any value near it.")
    A(f"- **The cortex comparison is weak and must be reported as weak.** The "
      f"fault-free figures rest on {targets['T11']['n_episodes']} and "
      f"{targets['T5']['n_episodes']} episodes; the sweep can say which imposed "
      f"speed the rig matches, not that cortex has been pinned to a time "
      f"constant.")
    A(f"- **Match the block length to the participant being compared.** T11 "
      f"episodes keep {targets['T11']['n_windows']:.0f} windows and T5 keep "
      f"{targets['T5']['n_windows']:.0f}; the bias depends on that length, so a "
      f"rig block of a different duration is not comparable without redoing "
      f"this calibration.")

    A("")
    A("## What this cannot tell me\n")
    A("- Whether real optical drift is Ornstein-Uhlenbeck. It probably is not "
      "exactly, and the natural-drift arm (Procedure 77) is the measurement that "
      "answers that rather than assuming it.")
    A("- What the rig will actually produce. This chooses sampling points; it "
      "does not predict the outcome.")
    A("- Whether the fault-free cortical figures are themselves reliable. They "
      "rest on 17 and 15 episodes and carry wide intervals (`scripts/70`).")

    (REPORTS / "DRIFT_SWEEP_DESIGN.md").write_text("\n".join(L))
    print("\n".join(L[5:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'DRIFT_SWEEP_DESIGN.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
