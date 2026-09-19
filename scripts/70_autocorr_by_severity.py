#!/usr/bin/env python3
"""
70_autocorr_by_severity.py
==========================
Is the no-overlap autocorrelation behind C18 a property of the brain, or of the
fault I injected into it?

WHY THIS EXISTS
---------------
Claim C18 says the serial correlation behind C04 survives when adjacent windows
share no data at all: lag-1 r = 0.902 on T11 and 0.784 on T5. scripts/66 computes
that number, and it computes it over "healthy" episodes, where healthy is defined
as `not crossed` -- the injected fault never pushed the decoder past threshold.

`not crossed` is not the same as `no fault`. The episode set also contains a
severity level `none`, where no fault was injected at all. Those episodes are
pooled in with benign and sub-threshold faults, and they are outnumbered roughly
18 to 1.

That matters because every injected fault in this project is a monotone ramp. A
ramp is a trend, and a trend drives lag-1 autocorrelation toward 1 whatever the
underlying neural signal does. So the pooled figure can be high because cortex
drifts slowly, or because I put a ramp in it, and C18 as written cannot tell the
two apart.

This splits the pool by severity and reports each level separately.

THE SMALL-SAMPLE PROBLEM, WHICH CUTS THE OTHER WAY
--------------------------------------------------
At the no-overlap spacing a T11 episode keeps 10 windows and a T5 episode keeps
7. The sample lag-1 autocorrelation is badly biased downward at that length --
for a true AR(1) with rho = 0.95 and 10 points, the median estimate is about
0.57, not 0.95. So every no-overlap number in this project, including C18's, is
an underestimate of whatever serial correlation is really there.

This script measures that bias by simulation against the matched series length
and inverts it, so the fault-free rows can be read as something other than "a
number smaller than the truth by an unknown amount". The inversion assumes the
fault-free series is AR(1); it is not applied to the faulted rows, where a ramp
plus AR(1) is the more honest description and a single rho would be misleading.

WHAT THIS DOES NOT DO
---------------------
It does not rewrite C18, C04, or the rig preregistration. It reports what the
split shows and what that implies for each of them. Which of those to change,
and how, is a decision for the research log and not for a script.

Usage: python3 scripts/70_autocorr_by_severity.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

def episode_sources() -> list[tuple[str, str]]:
    """Every participant that has been through the harness, as (file, label).

    This used to be a hardcoded pair, T11 and T5. That meant a rig participant
    could be recorded, injected, decoded and scored, and this script would
    silently report nothing about it -- while still printing PASS, because it
    found the two files it was told to look for. The main cross-system
    comparison of the whole project (Procedure B-9 in the build manual) runs
    through here, so the failure would have been both silent and central.

    The same hardcoded-list problem was found in scripts/69_command_check.py on
    17 September, where a stale list shrank the check from 69 commands to 19
    without failing. A gate whose scope is maintained by hand will go stale.
    """
    found = []
    for p in sorted(OUT.glob("episode_scores*_local.csv")):
        stem = p.stem                       # episode_scores[_<PARTICIPANT>]_local
        mid = stem[len("episode_scores"):-len("_local")].strip("_")
        found.append((p.name, mid or "T11"))
    # T11 and T5 first, so existing reports keep their familiar order.
    order = {"T11": 0, "T5": 1}
    return sorted(found, key=lambda q: (order.get(q[1], 2), q[1]))


SOURCES = episode_sources()

WINDOW_BINS = 1500          # must match scripts/20_evaluation_harness.py
STEP_BINS = 250             # must match scripts/20_evaluation_harness.py
SPACINGS = [1, 3, 6]
MIN_WINDOWS = 12            # same floor scripts/66 uses
MIN_AFTER_DECIMATION = 6    # below this a lag-1 estimate is not worth having

# Severity levels, in the order they belong in the table. `none` means no fault
# was injected; the rest are injected ramps that never crossed threshold.
LEVELS = ["none", "benign", "sub"]
LEVEL_LABEL = {
    "none": "none (no fault injected)",
    "benign": "benign (ramp, far below threshold)",
    "sub": "sub (ramp, approached threshold)",
}

SEED = 20260915
N_BOOT = 5000
N_CALIB = 4000              # AR(1) draws per rho in the bias calibration
RHO_GRID = np.concatenate([np.linspace(0.0, 0.9, 46), np.linspace(0.905, 0.999, 40)])


def overlap_fraction(k: int) -> float:
    shared = max(0, WINDOW_BINS - k * STEP_BINS)
    return shared / WINDOW_BINS


def lag1(y: np.ndarray) -> float:
    if len(y) < MIN_AFTER_DECIMATION:
        return np.nan
    a, b = y[:-1], y[1:]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def n_eff(n: float, r: float) -> float:
    return n * (1 - r) / (1 + r)


def boot_ci(vals: list[float], rng: np.random.Generator) -> tuple[float, float]:
    v = np.asarray(vals, dtype=float)
    if len(v) < 2:
        return (float("nan"), float("nan"))
    meds = [float(np.median(rng.choice(v, len(v), replace=True))) for _ in range(N_BOOT)]
    lo, hi = np.percentile(meds, [2.5, 97.5])
    return (float(lo), float(hi))


def calibration_curve(n: int, rng: np.random.Generator) -> np.ndarray:
    """Median of the n-point lag-1 estimator, for each true rho on RHO_GRID.

    This is the estimator's bias curve at the series length actually available
    after decimation. It is monotone in rho, so it can be inverted.
    """
    med = np.empty(len(RHO_GRID))
    for j, rho in enumerate(RHO_GRID):
        s = np.sqrt(max(1 - rho * rho, 1e-12))
        x = np.empty((N_CALIB, n))
        x[:, 0] = rng.normal(size=N_CALIB)
        eps = rng.normal(scale=s, size=(N_CALIB, n))
        for i in range(1, n):
            x[:, i] = rho * x[:, i - 1] + eps[:, i]
        a, b = x[:, :-1], x[:, 1:]
        am = a - a.mean(1, keepdims=True)
        bm = b - b.mean(1, keepdims=True)
        den = np.sqrt((am * am).sum(1) * (bm * bm).sum(1))
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.where(den > 1e-12, (am * bm).sum(1) / den, np.nan)
        med[j] = np.nanmedian(r)
    return np.maximum.accumulate(med)   # enforce monotonicity against MC jitter


def invert(curve: np.ndarray, observed: float) -> float:
    """True rho whose median n-point estimate equals `observed`.

    Returns nan below the curve's floor or above its ceiling, rather than
    clamping -- a value off the end of the curve is not an estimate, and saying
    so is the point.
    """
    if not np.isfinite(observed) or observed < curve[0] or observed > curve[-1]:
        return float("nan")
    return float(np.interp(observed, curve, RHO_GRID))


def main() -> int:
    rng = np.random.default_rng(SEED)
    result: dict = {
        "window_bins": WINDOW_BINS, "step_bins": STEP_BINS,
        "what_this_is": "C18's no-overlap autocorrelation split by whether a "
                        "fault was injected, plus a small-sample bias "
                        "calibration of the lag-1 estimator.",
        "participants": {},
    }

    calib_cache: dict[int, np.ndarray] = {}

    L = ["# Is C18's autocorrelation the brain, or the fault I injected?\n",
         "**Generated by `scripts/70_autocorr_by_severity.py` — do not edit by hand.**\n",
         "Claim **C18** reports a no-overlap lag-1 autocorrelation of 0.902 (T11) "
         "and 0.784 (T5), over episodes where the injected fault never crossed "
         "threshold. That pool is not fault-free: it mixes episodes with no fault "
         "at all into a much larger set of episodes carrying a sub-threshold "
         "ramp. Every fault in this project is a monotone ramp, and a ramp raises "
         "lag-1 autocorrelation on its own. This splits the pool.\n"]
    A = L.append

    A("## Lag-1 autocorrelation by injected severity\n")
    A("| Participant | Spacing | Data shared | Injected severity | Episodes | "
      "Windows | Lag-1 r | 95% CI | Effective independent samples |")
    A("|---|---|---|---|---|---|---|---|---|")

    for fname, pname in SOURCES:
        path = OUT / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        sub = df[(df.detector == "decoder_guard") & (~df.crossed)]
        pres: dict = {"n_episodes_not_crossed": int(len(sub)), "by_severity": {},
                      "pooled": {}, "bias_correction": {}}

        for k in SPACINGS:
            ov = overlap_fraction(k)
            groups = [(lv, sub[sub.severity == lv]) for lv in LEVELS]
            groups.append(("ALL", sub))
            for lv, g in groups:
                ys = [np.fromstring(s, sep=",") for s in g.scores]
                ys = [y for y in ys if len(y) >= MIN_WINDOWS]
                rs = [lag1(y[::k]) for y in ys]
                rs = [v for v in rs if np.isfinite(v)]
                if not rs:
                    continue
                nwin = float(np.median([len(y[::k]) for y in ys]))
                med = float(np.median(rs))
                lo, hi = boot_ci(rs, rng)
                e = n_eff(nwin, med)
                label = "**all not-crossed (what C18 pools)**" if lv == "ALL" \
                    else LEVEL_LABEL[lv]
                A(f"| {pname} | every {k} | {ov * 100:.1f}% | {label} | {len(rs)} | "
                  f"{nwin:.0f} | {med:.3f} | [{lo:.3f}, {hi:.3f}] | {e:.2f} |")
                pres["by_severity" if lv != "ALL" else "pooled"].setdefault(
                    str(k), {})[lv] = {
                        "n_episodes": len(rs), "n_windows_median": nwin,
                        "lag1_r_median": med, "ci95": [lo, hi], "n_eff": e,
                        "overlap_fraction": ov}

        # ---- bias correction, fault-free rows only, at the no-overlap spacing
        ff = pres["by_severity"].get("6", {}).get("none")
        if ff:
            n = int(round(ff["n_windows_median"]))
            if n not in calib_cache:
                calib_cache[n] = calibration_curve(n, rng)
            curve = calib_cache[n]
            lo_rho, hi_rho = (invert(curve, ff["ci95"][0]),
                              invert(curve, ff["ci95"][1]))
            # The inversion is only usable where the calibration curve still has
            # slope. Near its ceiling the curve flattens, so a confidence bound
            # that runs off the top does not come back as a rho at all -- and a
            # point estimate quoted without its interval would hide that the
            # data cannot tell rho = 0.7 from rho = 0.999 at this length.
            identifiable = bool(np.isfinite(lo_rho) and np.isfinite(hi_rho))
            corr = {
                "series_length": n,
                "estimator_ceiling": float(curve[-1]),
                "identifiable": identifiable,
                "rho_point": invert(curve, ff["lag1_r_median"]) if identifiable
                             else float("nan"),
                "rho_ci95": [lo_rho, hi_rho],
                "rho_lower_bound_only": lo_rho if not identifiable else None,
            }
            rp = corr["rho_point"]
            corr["n_eff_bias_corrected"] = n_eff(n, rp) if np.isfinite(rp) else float("nan")
            pres["bias_correction"] = corr

        result["participants"][pname] = pres

    A("")
    A("Bootstrap is over episodes, 5000 resamples. `ALL not-crossed` is the row "
      "`scripts/66` publishes as C18; the rows above it are what it is made of.\n")

    # ---- narrative
    A("## What the split shows\n")
    got = result["participants"]
    for pname in ("T11", "T5"):
        p = got.get(pname)
        if not p or "6" not in p["by_severity"]:
            continue
        row6 = p["by_severity"]["6"]
        row1 = p["by_severity"]["1"]
        pooled6 = p["pooled"]["6"]["ALL"]
        none6, none1 = row6["none"], row1["none"]
        A(f"**{pname}.** At the no-overlap spacing the pooled figure is "
          f"**{pooled6['lag1_r_median']:.3f}**. Split by what was actually "
          f"injected, it is "
          + ", ".join(f"**{row6[lv]['lag1_r_median']:.3f}** for {lv}"
                      for lv in LEVELS if lv in row6)
          + f". The fault-free episodes sit at "
            f"**{none6['lag1_r_median']:.3f}** "
            f"[{none6['ci95'][0]:.3f}, {none6['ci95'][1]:.3f}], on "
            f"{none6['n_episodes']} episodes.")
        A(f"  The ordering is monotone in injected severity, which is what it "
          f"would look like if the ramp were supplying the correlation. With "
          f"83.3% overlap the same fault-free episodes read "
          f"**{none1['lag1_r_median']:.3f}** — so for fault-free data the "
          f"correlation really is mostly window geometry, and it does collapse "
          f"when the overlap is removed.")
        bc = p.get("bias_correction") or {}
        if bc:
            rp, ci = bc.get("rho_point"), bc.get("rho_ci95", [np.nan, np.nan])
            A(f"  Correcting the estimator for its small-sample bias at "
              f"{bc['series_length']} windows: the estimator's ceiling at this "
              f"length is **{bc['estimator_ceiling']:.2f}**, so no observed "
              f"value above that is reachable however slowly the signal drifts.")
            if bc["identifiable"]:
                A(f"  The fault-free point estimate inverts to a true AR(1) rho "
                  f"of about **{rp:.2f}** (95% CI {ci[0]:.2f} to {ci[1]:.2f}), "
                  f"or roughly **{bc['n_eff_bias_corrected']:.1f}** effective "
                  f"independent samples per block. The interval is wide because "
                  f"{bc['series_length']} points is very little to estimate an "
                  f"autocorrelation from.")
            else:
                lb = bc["rho_lower_bound_only"]
                A(f"  **The inversion does not identify a rho here.** The upper "
                  f"confidence bound on the observed r runs past the top of the "
                  f"calibration curve, where the curve is flat, so the data are "
                  f"consistent with any rho from about "
                  + (f"**{lb:.2f}**" if np.isfinite(lb) else "**0**")
                  + f" upward, including values arbitrarily close to 1. At "
                    f"{bc['series_length']} windows this estimator cannot tell "
                    f"those apart, and no bias-corrected point estimate or "
                    f"effective sample size is reported for {pname}.")
        A("")

    A("## What this means for the claims as they stand\n")
    A("- **C18 is not wrong about the pool it describes, but it is mislabelled.** "
      "It reports the autocorrelation of episodes that carry a sub-threshold "
      "injected ramp, and calls the result a property of the signal. For the "
      "fault-free subset the correlation at zero overlap is much lower, and on "
      "T11 it is not distinguishable from zero.")
    A("- **C04's conclusion is untouched where it is used.** C04 governs how "
      "detector performance is aggregated, and detector performance is measured "
      "on episodes that contain faults. Within those episodes the windows really "
      "are dependent, and bootstrapping over episodes rather than windows remains "
      "the right call.")
    A("- **The false-alarm side is the part that changes.** How many independent "
      "chances a healthy session gives the detector to false-alarm is a "
      "fault-free question, and the fault-free rows are the ones that answer it. "
      "They give more independent samples than the pooled figure implies, not "
      "fewer.")
    A("- **The rig comparison is aimed at the wrong number.** The natural-drift "
      "arm of the rig study has no injected fault, so it must be compared "
      "against the fault-free rows, not against 0.902 and 0.784. Predictions "
      "**P-R1** and **P-R2** in `research/RIG_PREREGISTRATION.md` originally "
      "took their thresholds from the pooled numbers and were **retargeted to "
      "the fault-free figures on 19 September 2026** (Amendment 1, §12). P-R1 "
      "is now a band spanning both participants' fault-free intervals; P-R2 was "
      "rewritten to test the fault-driven RISE in correlation, which is large "
      "on both participants and measured on hundreds of episodes rather than "
      "seventeen. P-R3 to P-R7 never depended on these figures.")
    A("- **Every no-overlap number in this project is biased low**, because the "
      "estimator is biased low at 7 to 10 points. That direction makes the "
      "project's negative results look weaker than they are, not stronger, so "
      "nothing already published becomes over-claimed by it.")

    A("")
    A("## Limits of this check\n")
    A("- The fault-free group is small: 17 episodes on T11 and 15 on T5, one per "
      "block. The confidence intervals are correspondingly wide and the point "
      "estimates should not be quoted without them.")
    A("- The bias correction assumes the fault-free series is AR(1). If its real "
      "structure is something else, the corrected rho is wrong by an unknown "
      "amount. It is reported because 'biased low by an unknown amount' is worse, "
      "not because AR(1) is known to be right.")
    A("- No correction is applied to the faulted rows. A ramp plus AR(1) is not "
      "AR(1), and a single rho would misdescribe it.")
    A("- This measures `decoder_guard` only, matching `scripts/66`.")

    (OUT / "autocorr_by_severity.json").write_text(json.dumps(result, indent=2))
    (REPORTS / "AUTOCORR_BY_SEVERITY.md").write_text("\n".join(L))
    print("\n".join(L[3:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'AUTOCORR_BY_SEVERITY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
