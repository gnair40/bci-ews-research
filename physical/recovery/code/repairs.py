#!/usr/bin/env python3
"""
repairs.py: four ways to carry on after a fault, and the rule for scoring them.

=============================================================================
STATUS: DRAFT. NOT PREREGISTERED. NOTHING HAS BEEN MEASURED WITH IT.
=============================================================================
This file belongs to the proposed recovery subphase (experiment P-8), described
in `physical/recovery/02_DESIGN.md`. The subphase is a draft that the researcher
has not yet approved or frozen. No bench exists, so no result exists.

=============================================================================
WHAT THIS FILE DOES
=============================================================================
The rest of the physical phase asks whether a monitor can WARN that decoding is
about to fail. This file is about what happens next. Once there is a moment at
which something is known to have gone wrong (the "failure point"), a repair is
applied to the decoder, and the decoding error after the repair is compared
with the error if nothing had been done.

A "decoder" here is the straight-line fit in `physical/code/monitor.py`: one
weight per camera channel, plus the average and spread of each channel that the
weights were fitted with. Every repair below changes one or both of those, and
nothing else.

    R0  no repair          the frozen decoder carries on. The comparison.
    R1  renormalise        measure each channel's new average and spread, and
                           use those instead of the old ones. Needs no labels.
    R2  mask and refit     find the channels that have gone dark, and refit the
                           weights WITHOUT them from the stored calibration
                           data. Needs no new labels.
    R3  mask + renormalise R1 and R2 together.
    R4  recalibrate        fit a new decoder from a short labelled block. This
                           is the only repair that needs to know the true
                           direction, which in a real device means stopping the
                           user for a calibration task.

"Labels" means the true direction on each frame. The bench always knows it. A
real device knows it only while the user performs a set task, so R4 has a cost
in the user's time that R1 to R3 do not.

=============================================================================
WHY THE SETTINGS ARE FIXED HERE AND NOT CHOSEN LATER
=============================================================================
Every number below is written down before any recording exists. If the length
of the adaptation period or the rule for "this channel has gone dark" were
chosen after seeing which choice gave the best recovery, the recovery would be
partly an effect of the choosing. All four repairs are always reported. None is
picked afterwards as "the" repair.

Run the built-in check with:

    python3 physical/recovery/code/repairs.py --selftest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "code"))
import monitor as M  # noqa: E402

# ---------------------------------------------------------------------------
# settings, fixed in advance (see 03_PREREGISTRATION_DRAFT.md, judgement calls)
# ---------------------------------------------------------------------------
ADAPT_SECONDS = 30.0        # how long a repair may watch the new signal before it acts.
                            # One analysis window, the unit the rest of the phase uses.
ADAPT_SWEEP = [10.0, 30.0, 60.0]   # reported in full as a curve; 30 is the primary
MIN_EVAL_SECONDS = 30.0     # a session with less than this left after the repair is not scored
LOST_RATIO = 0.5            # a channel is "lost" if its brightness fell to less than half ...
REFERENCE_QUANTILE = 0.75   # ... of what the better-preserved channels kept
# The same 10 degrees that defines "decoding has failed" everywhere else in the
# project. Imported, not retyped, so the two cannot drift apart.
DAMAGE_DEG = float(M.harness.THRESHOLD_DEG)

REPAIRS = ["R0_none", "R1_renormalise", "R2_mask_refit", "R3_mask_renormalise",
           "R4_recalibrate"]
NEEDS_LABELS = {"R0_none": False, "R1_renormalise": False, "R2_mask_refit": False,
                "R3_mask_renormalise": False, "R4_recalibrate": True}


# ---------------------------------------------------------------------------
# what is kept from calibration
# ---------------------------------------------------------------------------
def calibration_stats(items, load=lambda item: item) -> dict:
    """Everything the repairs need from the calibration recordings, in one small object.

    `items` is a list of calibration recordings, or of anything `load` can turn
    into one: an object with `.X` (frames x channels) and `.heading` (radians).
    Each is loaded twice and held one at a time, so the calibration set can be
    as large as the campaign makes it.

    What is kept is the per-channel average and spread, and two summary tables
    (`A` and `B`) from which the decoder's weights can be solved again for ANY
    subset of channels without opening the recordings a second time. That is
    what makes "refit without the lost channels" possible with no new labels.
    """
    items = list(items)
    n, s1, s2 = 0, None, None
    for item in items:
        X = np.asarray(load(item).X, dtype=np.float64)
        s1 = X.sum(axis=0) if s1 is None else s1 + X.sum(axis=0)
        s2 = (X ** 2).sum(axis=0) if s2 is None else s2 + (X ** 2).sum(axis=0)
        n += len(X)
    mean = s1 / n
    std = np.sqrt(np.maximum(s2 / n - mean ** 2, 0.0))
    std[std < 1e-12] = 1.0
    d = len(mean) + 1
    A, B = np.zeros((d, d)), np.zeros((d, 2))
    for item in items:
        s = load(item)
        Z = np.hstack([(np.asarray(s.X, dtype=np.float64) - mean) / std,
                       np.ones((len(s.X), 1))])
        Y = np.column_stack([np.cos(s.heading), np.sin(s.heading)])
        A += Z.T @ Z
        B += Z.T @ Y
    return {"mean": mean, "std": std, "A": A, "B": B, "n": n}


def solve_weights(calib: dict, keep: np.ndarray | None = None) -> np.ndarray:
    """The decoder's weights, from the calibration summary, using only the channels in `keep`.

    Channels that are not kept get a weight of exactly zero, so the result has
    the same shape as an ordinary decoder and every other function can use it
    unchanged.
    """
    c = len(calib["mean"])
    keep = np.ones(c, dtype=bool) if keep is None else np.asarray(keep, dtype=bool)
    idx = np.append(np.flatnonzero(keep), c)            # the kept channels, plus the constant
    A = calib["A"][np.ix_(idx, idx)] + M.RIDGE * calib["n"] * np.eye(len(idx))
    W = np.zeros((c + 1, 2))
    W[idx] = np.linalg.solve(A, calib["B"][idx])
    return W


def frozen_decoder(calib: dict) -> tuple:
    """The decoder as it was at calibration: all channels, the old average and spread."""
    return solve_weights(calib), calib["mean"], calib["std"]


# ---------------------------------------------------------------------------
# what a repair may look at
# ---------------------------------------------------------------------------
def channel_stats(X: np.ndarray) -> tuple:
    """Average and spread of each channel over a stretch of recording."""
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std < 1e-12] = 1.0
    return mean, std


def lost_channels(mean_now: np.ndarray, calib: dict) -> np.ndarray:
    """Which channels have gone dark, judged against the channels that have not.

    Each channel's brightness now is divided by its brightness at calibration.
    If a filter dims the whole field, every channel's ratio falls by the same
    amount, nothing stands out, and nothing is called lost. That is correct: a
    dimmer channel still carries the signal. If tape covers part of the field,
    the covered channels fall far below the rest, and those are the lost ones.

    The comparison is with the 75th percentile of the ratios, not the middle,
    so the rule still works when up to three quarters of the field is covered.
    """
    ratio = mean_now / np.where(np.abs(calib["mean"]) < 1e-12, 1.0, calib["mean"])
    reference = np.quantile(ratio, REFERENCE_QUANTILE)
    return ratio < LOST_RATIO * reference


# ---------------------------------------------------------------------------
# the repairs
# ---------------------------------------------------------------------------
def build_repairs(calib: dict, X_adapt: np.ndarray, heading_adapt: np.ndarray) -> dict:
    """One decoder per repair, each built ONLY from what that repair is allowed to see.

    `X_adapt` is the stretch of recording that starts at the failure point and
    lasts for the adaptation period. `heading_adapt` is the true direction over
    that stretch. Only R4 is given it.
    """
    mean_now, std_now = channel_stats(X_adapt)
    lost = lost_channels(mean_now, calib)
    keep = ~lost
    W_all = solve_weights(calib)
    W_kept = solve_weights(calib, keep) if lost.any() else W_all
    return {
        "R0_none": (W_all, calib["mean"], calib["std"]),
        "R1_renormalise": (W_all, mean_now, std_now),
        "R2_mask_refit": (W_kept, calib["mean"], calib["std"]),
        "R3_mask_renormalise": (W_kept, mean_now, std_now),
        "R4_recalibrate": M.fit_decoder(X_adapt, heading_adapt),
        "_lost": lost,
    }


def median_error(X: np.ndarray, heading: np.ndarray, dec) -> float:
    e = M.angular_error(X, heading, dec)
    e = e[np.isfinite(e)]
    return float(np.median(e)) if len(e) else float("nan")


def score_session(X: np.ndarray, heading: np.ndarray, calib: dict, trigger_frame: int,
                  baseline_end_frame: int | None = None,
                  adapt_seconds: float = ADAPT_SECONDS, fps: int = M.FPS) -> dict | None:
    """Apply every repair at one failure point in one session, and score each.

    The session is cut into three stretches that never overlap:

        before `baseline_end_frame`      the decoder as it was while healthy
        trigger ... trigger + adapt      what the repairs may look at
        after that, to the end           where every repair is scored

    A repair is never scored on the stretch it was built from. Returns None if
    less than MIN_EVAL_SECONDS is left to score on, so a short tail cannot
    produce a number that looks like a measurement.
    """
    n = len(X)
    a0 = int(trigger_frame)
    a1 = a0 + int(round(adapt_seconds * fps))
    if a0 < 0 or n - a1 < int(round(MIN_EVAL_SECONDS * fps)):
        return None
    base_end = a0 if baseline_end_frame is None else int(baseline_end_frame)
    decs = build_repairs(calib, X[a0:a1], heading[a0:a1])
    frozen = decs["R0_none"]
    out = {"n_eval_frames": int(n - a1), "n_lost_channels": int(decs["_lost"].sum()),
           "error_before": median_error(X[:base_end], heading[:base_end], frozen)
           if base_end > 0 else float("nan")}
    for name in REPAIRS:
        out[name] = median_error(X[a1:], heading[a1:], decs[name])
    return out


def recovery_fraction(before: float, unrepaired: float, repaired: float) -> float:
    """How much of the damage a repair undid.

        0    nothing was recovered
        1    the error is back to what it was before the fault
        >1   the error is LOWER than before the fault: an enhancement
        <0   the repair made things worse

    Defined only when the fault did real damage: an unrepaired error at least
    DAMAGE_DEG above the error before. Without that, the fraction would be a
    small number divided by a smaller one, and would mean nothing.
    """
    damage = unrepaired - before
    if not np.isfinite(damage) or damage < DAMAGE_DEG:
        return float("nan")
    return float((unrepaired - repaired) / damage)


# ---------------------------------------------------------------------------
# a check with known answers
# ---------------------------------------------------------------------------
class _Fake:
    def __init__(self, X, heading):
        self.X, self.heading = X, heading


def _fake(n_frames, pref, depth, rng):
    """A recording made from a formula, the same one monitor.py uses for its own check."""
    heading = np.repeat(rng.uniform(0, 2 * np.pi, n_frames // 100 + 1), 100)[:n_frames]
    X = 128.0 + depth * 128.0 * np.cos(heading[:, None] - pref[None, :])
    return X + rng.normal(0, 1.0, X.shape), heading


def selftest() -> int:
    """Formula-made recordings with known faults. Checks the wiring, and nothing else.

    These are not data. They show that each repair does what its description
    says on a fault built to suit it, and that the scoring refuses to invent
    numbers. They say nothing about any apparatus.
    """
    rng = np.random.default_rng(3)
    n_ch, depth, onset, n = 96, 0.02, 6000, 12000
    pref = rng.uniform(0, 2 * np.pi, n_ch)
    calib = calibration_stats(_Fake(*_fake(9000, pref, depth, rng)) for _ in range(3))
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  {'ok  ' if cond else 'FAIL'}  {label}{('  ' + detail) if detail else ''}")

    # the stored summary gives back the same decoder as an ordinary fit
    Xc, hc = _fake(9000, pref, depth, np.random.default_rng(11))
    one = calibration_stats([_Fake(Xc, hc)])
    W_direct, _, _ = M.fit_decoder(Xc, hc)
    check("weights solved from the stored summary equal an ordinary fit",
          np.allclose(solve_weights(one), W_direct, atol=1e-8))

    def run(fault):
        X, h = _fake(n, pref, depth, np.random.default_rng(21))
        X = X.copy()
        fault(X)
        return score_session(X, h, calib, onset, onset)

    def dim(X):
        X[onset:] *= 0.25
    r = run(dim)
    check("whole-field dimming: nothing is called lost", r["n_lost_channels"] == 0)
    check("whole-field dimming: renormalising recovers most of the damage",
          recovery_fraction(r["error_before"], r["R0_none"], r["R1_renormalise"]) > 0.5,
          f"before {r['error_before']:.1f}, unrepaired {r['R0_none']:.1f}, "
          f"renormalised {r['R1_renormalise']:.1f} deg")

    def tape(X):
        X[onset:, : n_ch // 3] = 2.0 + np.random.default_rng(5).normal(0, 1.0, (n - onset, n_ch // 3))
    r = run(tape)
    check("a third of the field covered: exactly those channels are called lost",
          r["n_lost_channels"] == n_ch // 3, f"{r['n_lost_channels']} of {n_ch}")
    check("a third of the field covered: masking beats doing nothing",
          r["R2_mask_refit"] < r["R0_none"],
          f"unrepaired {r['R0_none']:.1f}, masked {r['R2_mask_refit']:.1f} deg")

    def nothing(X):
        pass
    r = run(nothing)
    check("no fault: nothing is called lost", r["n_lost_channels"] == 0)
    check("no fault: the recovery fraction is refused, not invented",
          not np.isfinite(recovery_fraction(r["error_before"], r["R0_none"],
                                            r["R1_renormalise"])))
    check("a session with too little left to score on is refused",
          score_session(*_fake(n, pref, depth, rng), calib, n - 2000) is None)
    check("the fraction reads 1 at full restoration and above 1 for an enhancement",
          recovery_fraction(20, 60, 20) == 1.0 and recovery_fraction(20, 60, 10) > 1.0)

    print("\nPASS: the repairs and the scoring are wired up correctly" if ok
          else "\nFAIL: see the lines marked FAIL above")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="run the built-in check on formula-made recordings")
    a = ap.parse_args()
    if a.selftest:
        print("recovery subphase self-test: no camera or recordings needed\n")
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
