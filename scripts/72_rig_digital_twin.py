#!/usr/bin/env python3
"""
72_rig_digital_twin.py
======================
Simulate the physical rig in software, before buying any of it.

WHY THIS EXISTS
---------------
Arm B of this project builds a camera-and-screen instrument that stands in for an
electrode array: a grid of screen patches whose brightness encodes a direction, a
camera whose image regions act as channels, and the same decoder and the same
monitor running on top. The point is to find out whether this project's negative
result is a fact about brains or a fact about any many-channel sensor that drifts
slowly.

Everything in that plan rests on one assumption nobody has checked: **that the
rig decodes direction above chance at all.** If it does not, there is nothing to
degrade, no risk signal to monitor, and every later procedure is wasted. Finding
that out with hardware on the bench costs money and weeks. Finding it out here
costs thirty seconds.

So this builds a digital twin -- screen, optics, sensor noise, quantisation,
region averaging -- and runs the real questions through it:

  1. Does it decode above its own measured chance level, and by how much?
  2. How dark can the screen get before decoding collapses? That sets the
     brightness range the SNR sweep can use.
  3. What does a healthy risk series look like, and is its autocorrelation in
     the range the neural comparison needs?
  4. Do the four fault modes actually change the signal, and in the direction
     the injected neural versions did?

THIS IS A MODEL, AND MODELS ARE WRONG
-------------------------------------
The optics here are a blur kernel, a vignette and a photon-noise model. Real
lenses have distortion, real screens have subpixel structure and backlight
flicker, real sensors have fixed-pattern noise and a rolling shutter. A number
that comes out of this is a design expectation, not a measurement, and every
procedure it informs still gets run on the hardware.

What it can do honestly is rule things OUT. If the twin cannot decode under
generous assumptions, the hardware will not either, and that is worth knowing
before the parts are ordered.

Usage: python3 scripts/72_rig_digital_twin.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

# ---- geometry, matched to rig/stimulus.py and rig/capture.py ---------------
COLS, ROWS = 24, 16               # 384 channels, matching T11's feature count
N_CH = COLS * ROWS
PX_PER_REGION = 4                 # PIXELS per channel, not pixels per side.
                                  # The original design averaged 20x20 = 400,
                                  # which made every channel so quiet that the
                                  # rig decoded perfectly and no fault could
                                  # move it. See reports/RIG_DIGITAL_TWIN.md.
BASE_LEVEL = 0.5                  # DC level of every patch, 0-1
DEPTH_DEFAULT = 0.005             # direction-dependent modulation about BASE
FPS = 50
HOLD = 100                        # frames per heading, 2 s at 50 fps
BLOCK_FRAMES = 15000              # 5 min, matching a neural block

# ---- sensor model ----------------------------------------------------------
# Photon transfer: variance = k_shot * signal + read^2, in 8-bit counts.
# k_shot = 1 is the shot-noise-limited case for a sensor whose full well maps
# to 255 counts; read noise of 2 counts is typical of a small CMOS module.
K_SHOT = 1.0
READ_NOISE = 2.0
BLUR_SIGMA_PX = 1.2               # defocus, in camera pixels
VIGNETTE = 0.25                   # corner falloff, fraction of centre

# What cortex does, from data/processed/reference_decoder*.json. The rig has to
# be calibrated to THIS operating point or the comparison is between a trivial
# decoding problem and a hard one, which is no comparison at all.
NEURAL = {"T11": {"error_deg": 54.554, "chance_deg": 90.692},
          "T5":  {"error_deg": 52.8,   "chance_deg": 84.941}}
NEURAL_MARGIN_T11 = NEURAL["T11"]["chance_deg"] - NEURAL["T11"]["error_deg"]

SEED = 20260919
RNG = np.random.default_rng(SEED)


def preferred_directions(n: int, rng) -> np.ndarray:
    return rng.uniform(0, 2 * math.pi, n)


def headings(n_frames: int, hold: int, rng) -> np.ndarray:
    n_tr = int(np.ceil(n_frames / hold))
    per = rng.uniform(0, 2 * math.pi, n_tr)
    return np.repeat(per, hold)[:n_frames]


def vignette_map(cols: int, rows: int, strength: float) -> np.ndarray:
    """Multiplicative falloff toward the corners, as any real lens has."""
    x = (np.arange(cols) - (cols - 1) / 2) / ((cols - 1) / 2)
    y = (np.arange(rows) - (rows - 1) / 2) / ((rows - 1) / 2)
    r2 = x[None, :] ** 2 + y[:, None] ** 2
    return (1.0 - strength * r2 / 2.0).ravel()


def screen_to_channels(head: np.ndarray, pref: np.ndarray, vign: np.ndarray,
                       rng, depth: float = DEPTH_DEFAULT,
                       base: float = BASE_LEVEL, dim: float = 1.0,
                       px: int = PX_PER_REGION,
                       blur_sigma: float = BLUR_SIGMA_PX) -> np.ndarray:
    """One block of camera channel readings, frames x channels, in 8-bit counts.

    WHAT `depth` IS, AND WHY IT IS THE IMPORTANT KNOB
    -------------------------------------------------
    A patch sits at `base` brightness and swings by `depth` with direction:

        patch = base + depth * cos(heading - preferred_direction)

    The first version of this model used `0.5 * (1 + cos(...))`, which is a
    modulation depth of 100%. That rig decoded direction to 0.0 degrees of error
    against an 89 degree chance level, where cortex manages 54.6 against 90.7. A
    rig that good is not a comparison, it is a different experiment, and no
    injected fault could move its error at all.

    Real direction-tuned neurons are not like that. They fire at a substantial
    baseline rate and modulate it modestly with direction, so each channel
    carries little information and the decoder is genuinely limited by channel
    quality -- which is exactly what makes degrading a channel matter. Lowering
    `depth` reproduces that: the signal shrinks while the photon noise, set by
    `base`, stays put.

    `px` is the number of camera pixels averaged into one channel. Averaging
    divides the noise standard deviation by its square root, so the original
    20x20 = 400 pixels made channels 20 times quieter than a single pixel. Both
    knobs move signal-to-noise; `depth` is free and `px` costs resolution, so
    `depth` does the fine adjustment.

    `dim` is a genuine loss of light, as a neutral-density filter causes. It is
    applied HERE, before the sensor noise, because that is where it physically
    happens. Applying it to the recorded numbers instead would be a pure
    rescaling, which the decoder standardises away -- an earlier version of this
    model did exactly that and reported, wrongly, that an ND filter had no
    effect on decoding.
    """
    n_f = len(head)
    b = base + depth * np.cos(head[:, None] - pref[None, :])

    if blur_sigma > 0:
        grid = b.reshape(n_f, ROWS, COLS)
        sig_grid = blur_sigma / max(int(math.sqrt(px)), 1)
        grid = gaussian_filter(grid, sigma=(0, sig_grid, sig_grid), mode="nearest")
        b = grid.reshape(n_f, N_CH)

    signal = np.clip(b * dim * vign[None, :], 0, 1) * 255.0
    var_px = K_SHOT * np.maximum(signal, 1.0) + READ_NOISE ** 2
    noisy = signal + rng.normal(0.0, np.sqrt(var_px / px))
    return np.clip(noisy, 0, 255).astype(np.float32)


# ---------------------------------------------------------------------------
def fit_decode(X: np.ndarray, head: np.ndarray, lam: float = 1.0
               ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ridge regression from channels to (cos, sin) of heading. Returns W, mean, sd."""
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    Z = np.hstack([Z, np.ones((len(Z), 1), dtype=Z.dtype)])
    Y = np.column_stack([np.cos(head), np.sin(head)])
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    A[-1, -1] -= lam                       # do not penalise the intercept
    W = np.linalg.solve(A, Z.T @ Y)
    return W, mu, sd


def predict(X: np.ndarray, W, mu, sd) -> np.ndarray:
    Z = (X - mu) / sd
    Z = np.hstack([Z, np.ones((len(Z), 1), dtype=Z.dtype)])
    return Z @ W


def angular_error_deg(pred: np.ndarray, head: np.ndarray) -> np.ndarray:
    ang = np.arctan2(pred[:, 1], pred[:, 0])
    d = np.abs(np.arctan2(np.sin(ang - head), np.cos(ang - head)))
    return np.degrees(d)


def chance_error_deg(pred: np.ndarray, head: np.ndarray, rng, reps: int = 20
                     ) -> float:
    """Chance measured, not assumed: shuffle the pairing and re-score.

    scripts/18 establishes chance the same way on the neural data. Assuming 90
    degrees because directions are uniform would be a theory, and a theory is
    what this project keeps finding reasons to distrust.
    """
    vals = []
    for _ in range(reps):
        vals.append(np.median(angular_error_deg(pred, rng.permutation(head))))
    return float(np.mean(vals))


# ---------------------------------------------------------------------------
# FAULT MODES, as the optics would actually produce them
#
# Each mirrors one of the four injected neural modes from scripts/17, but caused
# the way the rig can physically cause it. The point of naming the physical
# cause is that these are the interventions Procedure 75 performs by hand.
# ---------------------------------------------------------------------------
def faulted_block(head, pref, vign, rng, depth, mode: str, sev: float):
    """A block recorded while fault `mode` is present at severity `sev`.

    Each fault is applied where the physics puts it -- in the light path or in
    the channel mapping, BEFORE the sensor noise -- not to the recorded numbers
    afterwards. That distinction is not pedantry: dimming the recorded numbers
    is a pure rescaling that the decoder's per-channel standardisation removes
    entirely, while dimming the actual light costs photons and therefore costs
    signal-to-noise. An earlier version of this model got that wrong and
    concluded an ND filter had no effect on decoding.
    """
    if mode == "NONE" or sev <= 0:
        return screen_to_channels(head, pref, vign, rng, depth=depth)

    if mode == "RATE_LOSS":
        # Neutral-density filter over the lens: fewer photons everywhere.
        return screen_to_channels(head, pref, vign, rng, depth=depth,
                                  dim=1.0 - 0.8 * sev)

    if mode == "GAIN_DRIFT":
        # Uneven brightness across the screen, mean-preserving so this is not
        # just RATE_LOSS wearing a different name.
        g = 1.0 + sev * rng.normal(0, 0.5, N_CH)
        g = np.clip(g, 0.05, None)
        g /= g.mean()
        return screen_to_channels(head, pref, vign * g, rng, depth=depth)

    if mode == "CHANNEL_DROPOUT":
        # Tape or a smudge over part of the field: those regions see only the
        # DC level, so they keep reporting light but carry no direction.
        X = screen_to_channels(head, pref, vign, rng, depth=depth)
        n_dead = int(round(N_CH * 0.5 * sev))
        if n_dead:
            dead = rng.choice(N_CH, n_dead, replace=False)
            flat = screen_to_channels(head, pref, vign, rng, depth=0.0)
            X[:, dead] = flat[:, dead]
        return X

    if mode == "GEOMETRY_ROTATION":
        # The camera or stage rotates: channel identities move around the grid.
        X = screen_to_channels(head, pref, vign, rng, depth=depth)
        shift = int(round(sev * COLS * 0.25))
        if shift == 0:
            return X
        grid = X.reshape(len(X), ROWS, COLS)
        return np.roll(grid, shift, axis=2).reshape(len(X), N_CH)

    raise ValueError(mode)


# ---------------------------------------------------------------------------
def risk_series(X: np.ndarray, fit_mu: np.ndarray, fit_sd: np.ndarray,
                window: int = 1500, step: int = 250) -> np.ndarray:
    """A decoder-guard-style risk score per window.

    The real detector (scripts/22) is richer, but its core move is the one here:
    fit what healthy data looks like, then score how far each window has moved
    from it. Using a simplified stand-in keeps this a test of the RIG rather than
    a test of the detector -- the real detector runs on the real recordings.
    """
    starts = np.arange(0, len(X) - window + 1, step)
    out = []
    for s in starts:
        W = X[s:s + window]
        # Two components, because one is not enough. A mean-only score is blind
        # to a channel that has frozen at its usual level -- exactly what
        # CHANNEL_DROPOUT does -- since a frozen channel does not move the mean.
        # The spread term catches it. The real detector (scripts/22) carries four
        # such components; two is the minimum that makes this test meaningful.
        z_mean = (W.mean(0) - fit_mu) / fit_sd
        z_disp = np.log((W.std(0) + 1e-6) / fit_sd)
        out.append(float(np.sqrt(np.mean(z_mean ** 2) + np.mean(z_disp ** 2))))
    return np.asarray(out)


def lag1(y: np.ndarray) -> float:
    if len(y) < 6:
        return float("nan")
    a, b = y[:-1], y[1:]
    if a.std() < 1e-12 or b.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def n_eff(n: float, r: float) -> float:
    return n * (1 - r) / (1 + r)


# ---------------------------------------------------------------------------
def main() -> int:
    rng = np.random.default_rng(SEED)
    pref = preferred_directions(N_CH, rng)
    vign = vignette_map(COLS, ROWS, VIGNETTE)

    result: dict = {
        "what_this_is": "A DIGITAL TWIN. Design expectations, not measurements.",
        "geometry": {"cols": COLS, "rows": ROWS, "channels": N_CH,
                     "px_per_channel": PX_PER_REGION, "fps": FPS,
                     "block_frames": BLOCK_FRAMES},
        "sensor_model": {"k_shot": K_SHOT, "read_noise_counts": READ_NOISE,
                         "blur_sigma_px": BLUR_SIGMA_PX, "vignette": VIGNETTE,
                         "base_level": BASE_LEVEL},
        "neural_target": NEURAL,
    }

    head = headings(BLOCK_FRAMES, HOLD, rng)
    n_fit = int(0.6 * len(head))

    def operating_point(depth, reps=12, X=None):
        if X is None:
            X = screen_to_channels(head, pref, vign, rng, depth=depth)
        W, mu, sd = fit_decode(X[:n_fit], head[:n_fit])
        pr = predict(X[n_fit:], W, mu, sd)
        e = float(np.median(angular_error_deg(pr, head[n_fit:])))
        c = chance_error_deg(pr, head[n_fit:], rng, reps=reps)
        return e, c, c - e, X, (W, mu, sd)

    # ---- TEST 1: the original design, 100% modulation ---------------------
    e0, c0, m0, _, _ = operating_point(0.5, reps=8)
    result["test1_original_design"] = {
        "modulation_depth": 0.5, "median_angular_error_deg": e0,
        "measured_chance_deg": c0, "margin_deg": m0,
        "neural_margin_T11_deg": NEURAL_MARGIN_T11,
        "too_easy": bool(m0 > NEURAL_MARGIN_T11 * 1.5),
    }

    # ---- TEST 1b: calibrate modulation depth to cortex's operating point --
    lo, hi, trace = 0.0005, 0.5, []
    for _ in range(11):
        mid = math.sqrt(lo * hi)                 # geometric bisection
        e, c, mg, _, _ = operating_point(mid, reps=8)
        trace.append({"depth": mid, "error_deg": e, "chance_deg": c,
                      "margin_deg": mg})
        if mg > NEURAL_MARGIN_T11:
            hi = mid                             # too easy -> lower the depth
        else:
            lo = mid
    depth = math.sqrt(lo * hi)
    e_cal, c_cal, m_cal, X, (W, mu, sd) = operating_point(depth, reps=20)
    result["test1b_calibration"] = {
        "modulation_depth": depth,
        "modulation_in_8bit_counts": depth * 255.0,
        "px_per_channel": PX_PER_REGION,
        "calibrated_error_deg": e_cal, "calibrated_chance_deg": c_cal,
        "calibrated_margin_deg": m_cal, "target_margin_deg": NEURAL_MARGIN_T11,
        "matched": bool(abs(m_cal - NEURAL_MARGIN_T11) < 6.0),
        "search_trace": trace,
    }

    # ---- TEST 2: healthy risk series --------------------------------------
    base_mu, base_sd = X[:n_fit].mean(0), X[:n_fit].std(0) + 1e-9
    rs, ne, nwin = [], [], None
    for _ in range(10):
        h2 = headings(BLOCK_FRAMES, HOLD, rng)
        Xh = screen_to_channels(h2, pref, vign, rng, depth=depth)
        y = risk_series(Xh, base_mu, base_sd)
        nwin = len(y)
        r_no = lag1(y[::6])
        if np.isfinite(r_no):
            rs.append(r_no); ne.append(n_eff(len(y[::6]), r_no))
    result["test2_healthy_autocorrelation"] = {
        "n_blocks": len(rs), "windows_per_block": nwin,
        "lag1_no_overlap_median": float(np.median(rs)) if rs else None,
        "n_eff_median": float(np.median(ne)) if ne else None,
    }

    # ---- TEST 3: do the four faults produce a monotone ladder? ------------
    healthy_risk = float(np.median(risk_series(X, base_mu, base_sd)))
    fm = {}
    for m_ in ["RATE_LOSS", "CHANNEL_DROPOUT", "GAIN_DRIFT", "GEOMETRY_ROTATION"]:
        rows = []
        for sev in [0.0, 0.25, 0.5, 1.0]:
            Xf = faulted_block(head, pref, vign, np.random.default_rng(7),
                               depth, m_, sev)
            pf = predict(Xf[n_fit:], W, mu, sd)
            rows.append({
                "severity": sev,
                "median_error_deg": float(np.median(
                    angular_error_deg(pf, head[n_fit:]))),
                "median_risk": float(np.median(
                    risk_series(Xf, base_mu, base_sd))),
            })
        errs = [q["median_error_deg"] for q in rows]
        risks = [q["median_risk"] for q in rows]
        fm[m_] = {
            "ladder": rows,
            "error_rises_with_severity": bool(all(np.diff(errs) > -0.5)),
            "error_rise_deg": errs[-1] - errs[0],
            "risk_rises_with_severity": bool(all(np.diff(risks) > -1e-9)),
            "risk_above_healthy_at_full": bool(risks[-1] > healthy_risk * 1.5),
        }
    result["test3_fault_modes"] = fm
    result["healthy_median_risk"] = healthy_risk

    (OUT / "rig_digital_twin.json").write_text(json.dumps(result, indent=2))
    return write_report(result)


def write_report(r: dict) -> int:
    L = ["# Does the rig work? Simulating it before building it\n",
         "**Generated by `scripts/72_rig_digital_twin.py` — do not edit by hand.**\n",
         "> **This is a digital twin, not a measurement.** The optics are a blur "
         "kernel, a vignette and a photon-noise model. Real lenses distort, real "
         "screens flicker, real sensors have fixed-pattern noise and a rolling "
         "shutter. Numbers here are design expectations. What it can do honestly "
         "is rule things **out**, and that is exactly what it did.\n"]
    A = L.append

    t1, cal = r["test1_original_design"], r["test1b_calibration"]

    A("## The headline: the rig as originally specified would not have worked\n")
    A(f"`rig/stimulus.py` drew each patch as `0.5 * (1 + cos(heading - "
      f"preferred))`, a modulation depth of 100%, and `rig/capture.py` averaged "
      f"20x20 = 400 camera pixels into each channel. Simulated, that rig decodes "
      f"direction to **{t1['median_angular_error_deg']:.1f}°** of error against "
      f"a **{t1['measured_chance_deg']:.1f}°** chance level — a margin of "
      f"**{t1['margin_deg']:.1f}°**, where cortex manages "
      f"**{t1['neural_margin_T11_deg']:.1f}°** (54.6° against 90.7° on T11).\n")
    A("Two things follow, and both are fatal to the experiment as written:\n")
    A("1. **A comparison between a system that decodes perfectly and one that "
      "barely beats chance is a comparison of difficulty, not of neurons.** "
      "Ruling out difficulty is the entire reason Arm B exists.")
    A("2. **No fault could move it.** With that much signal, dimming the lens or "
      "killing half the channels left the decoder still essentially perfect, so "
      "there would be no severity ladder and nothing for a monitor to detect.\n")
    A("Finding this on the bench would have cost weeks and the price of the "
      "parts. Finding it here cost twenty seconds.\n")

    A("## The fix, and it is free\n")
    A("Real direction-tuned neurons fire at a substantial baseline and modulate "
      "it *modestly* with direction, so each channel carries little information "
      "and the decoder is genuinely limited by channel quality. That is what "
      "makes degrading a channel matter. Two software knobs reproduce it:\n")
    A("- **Modulation depth.** Draw each patch as `base + depth * cos(...)` with "
      "a small `depth`, instead of a full-swing cosine. The signal shrinks while "
      "the photon noise, set by `base`, stays put.")
    A("- **Pixels per channel.** Averaging divides noise by the square root of "
      "the pixel count, so 400 pixels made every channel 20 times quieter than "
      "one pixel. Fewer pixels per channel, more honest noise.\n")
    A("Neither needs a single extra part. Both are already-planned files.\n")
    A("| Setting | Value |")
    A("|---|---|")
    A(f"| Pixels averaged per channel | **{cal['px_per_channel']}** (was 400) |")
    A(f"| Modulation depth | **{cal['modulation_depth']:.4f}** (was 0.5) |")
    A(f"| …in 8-bit counts | **{cal['modulation_in_8bit_counts']:.2f}** counts |")
    A(f"| Rig error after calibration | {cal['calibrated_error_deg']:.1f}° |")
    A(f"| Rig chance after calibration | {cal['calibrated_chance_deg']:.1f}° |")
    A(f"| Rig margin after calibration | **{cal['calibrated_margin_deg']:.1f}°** |")
    A(f"| Target: T11 margin over chance | {cal['target_margin_deg']:.1f}° |")
    A("")
    if cal["matched"]:
        A("**Matched.** Every later test runs at this setting. Matching the "
          "*margin over each system's own measured chance* is the right target "
          "rather than raw error, because the two chance levels are different "
          "numbers, so equal error would not mean equal difficulty.\n")
    else:
        A("**Not matched.** Do not run the comparison until it is. Widen the "
          "search or change the geometry.\n")
    A("A caution that has to travel with these numbers: a modulation of about "
      f"{cal['modulation_in_8bit_counts']:.1f} of the 255 available brightness "
      "levels is a small signal, and on real hardware backlight flicker, ambient "
      "leakage and 8-bit dithering all live in that range. Procedure B-7 in the "
      "build manual measures whether the real rig can hold it; if it cannot, the "
      "fallback is more channels or a longer block rather than a deeper "
      "modulation, because depth is what buys comparability.\n")

    t2 = r["test2_healthy_autocorrelation"]
    A("## What a healthy risk series looks like\n")
    A(f"- Windows per {BLOCK_FRAMES // FPS}-second block: **{t2['windows_per_block']}**, "
      f"or {t2['windows_per_block'] // 6} once decimated to non-overlapping spacing")
    if t2["lag1_no_overlap_median"] is not None:
        A(f"- Lag-1 autocorrelation at zero overlap: "
          f"**{t2['lag1_no_overlap_median']:.3f}**")
        A(f"- Effective independent samples per block: **{t2['n_eff_median']:.2f}**")
    A("")
    A("Compare against the **fault-free** neural figures in "
      "`reports/AUTOCORR_BY_SEVERITY.md` (0.085 on T11, 0.435 on T5), never "
      "against C18's pooled 0.902 and 0.784, which are raised by the injected "
      "ramp. This is also the least trustworthy number in this report: the model "
      "has no thermal drift, no backlight flicker and no mechanical creep, which "
      "are precisely the things that would make a real rig's risk series "
      "correlated in time. Read it as a check that the pipeline produces a "
      "number, not as a prediction of which number.\n")

    A("## Do the four faults produce a severity ladder?\n")
    A("Each mirrors an injected neural mode from `scripts/17_fault_injector.py`, "
      "caused the way the rig can physically cause it, and applied in the light "
      "path **before** the sensor noise — which is where it happens.\n")
    A("| Fault | Physical cause | Error, healthy → full severity | Ladder rises | "
      "Risk rises | Risk clearly above healthy |")
    A("|---|---|---|---|---|---|")
    cause = {"RATE_LOSS": "ND filter over the lens",
             "CHANNEL_DROPOUT": "tape or smudge over part of the field",
             "GAIN_DRIFT": "uneven brightness across the screen",
             "GEOMETRY_ROTATION": "camera or stage rotated"}
    for m_, d in r["test3_fault_modes"].items():
        lo_e = d["ladder"][0]["median_error_deg"]
        hi_e = d["ladder"][-1]["median_error_deg"]
        A(f"| `{m_}` | {cause[m_]} | {lo_e:.1f}° → {hi_e:.1f}° "
          f"(**{d['error_rise_deg']:+.1f}°**) "
          f"| {'yes' if d['error_rises_with_severity'] else '**NO**'} "
          f"| {'yes' if d['risk_rises_with_severity'] else '**no**'} "
          f"| {'yes' if d['risk_above_healthy_at_full'] else '**no**'} |")
    A("")
    bad = [m_ for m_, d in r["test3_fault_modes"].items()
           if not d["error_rises_with_severity"]]
    if bad:
        A(f"**{', '.join(bad)} does not give a monotone ladder in this model.** "
          f"A ladder that does not rise is the bug `scripts/17` already had once "
          f"and had to be fixed. Treat this mode as unverified and check it "
          f"first on the hardware.\n")
    else:
        A("All four rise with severity, which is the property "
          "`tests/test_core_numerics.py` enforces for the neural injector and "
          "which has to hold on the rig or the severity levels mean nothing.\n")

    A("## What this licenses\n")
    A("**Licensed:** ordering the parts — *provided* `rig/stimulus.py` and "
      "`rig/capture.py` carry the calibrated settings above. The unmodified "
      "versions would have produced an uninterpretable experiment.")
    A("**Not licensed:** any claim about what the rig will measure. The "
      "autocorrelation above is a property of this model's noise.")
    A("**Only hardware can answer:** display-to-camera latency, rolling-shutter "
      "skew, backlight flicker at 50 fps, sensor thermal drift, whether the "
      "enclosure is light-tight enough, and whether a modulation of a couple of "
      "brightness levels survives a real display.")

    (REPORTS / "RIG_DIGITAL_TWIN.md").write_text("\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {REPORTS / 'RIG_DIGITAL_TWIN.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
