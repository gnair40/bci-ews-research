#!/usr/bin/env python3
"""
The four candidate feature families, F1-F4.

FROZEN BEFORE ANY OF THIS WAS COMPUTED
--------------------------------------
`research/FEATURE_STUDY_FROZEN.json`, commit 0950c04, records the
preregistration's checksum and proves no feature result file existed at that
moment. The list of four families is closed; anything not here is a new study.

Phase 3 ruled out better decision rules, longer windows, and better aggregators,
each on measurement. A better *measurement* is the only direction left, and it is
the direction most vulnerable to fishing: with two participants who disagree, a
family that helps one can be found by trying enough of them. Hence the freeze,
and hence the rule that a family helping only one participant is a NULL RESULT.

WHAT EACH FAMILY NEEDS THAT THE CURRENT FEATURES DO NOT HAVE
------------------------------------------------------------
The existing monitor sees one number per channel per window: its mean activity.
Every family below adds a kind of information that summary discards.

    F1  how STEADILY each channel fires, not just how much
    F2  which channels move TOGETHER
    F3  the TIMESCALE on which each channel fluctuates
    F4  the SHAPE of the distribution across channels, not its moments

All four consume raw bins rather than pre-computed window means, so each defines
its own `window_features`. They are then fitted on healthy data only, scored
through the unchanged harness, and reported for both participants whatever the
outcome.

Usage: imported by scripts/33_run_feature_study.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("det", REPO / "scripts" / "19_detectors.py")
_det = importlib.util.module_from_spec(_spec)
sys.modules["det"] = _det
_spec.loader.exec_module(_det)

EPS = 1e-9


# ---------------------------------------------------------------------------
# F1 -- per-channel variability
# ---------------------------------------------------------------------------

def feat_fano(X: np.ndarray, starts: np.ndarray, win: int) -> np.ndarray:
    """Fano factor per channel per window: variance / mean.

    A channel firing 10 spikes steadily and one firing 0, 30, 0, 10 have the
    same mean and completely different Fano factors. The current features cannot
    tell them apart. A failing electrode plausibly becomes erratic before it
    becomes quiet, and that would be invisible to a mean.
    """
    out = np.empty((len(starts), X.shape[1]))
    for i, s in enumerate(starts):
        seg = X[s:s + win]
        m = seg.mean(axis=0)
        out[i] = seg.var(axis=0) / (m + EPS)
    return out


# ---------------------------------------------------------------------------
# F2 -- cross-channel covariance structure
# ---------------------------------------------------------------------------

def feat_covstruct(X: np.ndarray, starts: np.ndarray, win: int, k: int = 24) -> np.ndarray:
    """How concentrated the correlation structure is, plus its leading directions.

    Losing an electrode changes which channels co-vary, and no per-channel
    summary sees that. This is closest in spirit to the published MINDFUL
    measure, so it carries the strongest prior of the four.

    A full 384x384 correlation matrix per window is far too many numbers to
    model from a few dozen healthy windows, so each window is summarised by the
    eigenvalue spectrum of its correlation matrix -- the shares of variance
    explained by the leading k directions. That is a compact description of "how
    much do these channels move together", which is the question.
    """
    out = np.empty((len(starts), k))
    for i, s in enumerate(starts):
        seg = X[s:s + win]
        sd = seg.std(axis=0)
        keep = sd > EPS
        Z = (seg[:, keep] - seg[:, keep].mean(axis=0)) / sd[keep]
        if Z.shape[1] < k + 1:
            out[i] = 0.0
            continue
        C = (Z.T @ Z) / len(Z)
        w = np.linalg.eigvalsh(C)[::-1][:k]
        out[i] = w / (w.sum() + EPS)
    return out


# ---------------------------------------------------------------------------
# F3 -- spectral content
# ---------------------------------------------------------------------------

def feat_spectral(X: np.ndarray, starts: np.ndarray, win: int) -> np.ndarray:
    """Slow-band share of each channel's fluctuation power.

    Every current feature is timescale-blind: a channel drifting slowly and one
    flickering fast look identical to a mean. Drift and fault plausibly live at
    different timescales, and if they do, this is the only family that can see
    the difference.

    Reported as a RATIO of slow to total power, not absolute power, so it does
    not simply restate overall activity -- which is the confound that defeated
    every scale-based measure in Phase 1-2.
    """
    out = np.empty((len(starts), X.shape[1]))
    n_fft = win // 2 + 1
    slow = slice(1, max(2, n_fft // 8))          # lowest eighth, excluding DC
    for i, s in enumerate(starts):
        seg = X[s:s + win]
        seg = seg - seg.mean(axis=0)
        P = np.abs(np.fft.rfft(seg, axis=0)) ** 2
        out[i] = P[slow].sum(axis=0) / (P[1:].sum(axis=0) + EPS)
    return out


# ---------------------------------------------------------------------------
# F4 -- channel-count distribution statistics
# ---------------------------------------------------------------------------

class ChannelCounts:
    """Fraction of channels sitting at each multiple of their own healthy median.

    Moments are fragile on heavy-tailed data -- Phase 1-2 found raw variance
    swinging ~100x between healthy blocks, which is why robust estimators were
    needed at all. Counting how many channels fall in each band sidesteps that
    entirely: it is a histogram, and a histogram does not care about tails.

    The reference medians come from healthy data only and are held fixed, so the
    bands mean the same thing throughout an episode.
    """
    BANDS = (0.02, 0.15, 0.4, 0.7, 1.0, 1.5, 2.5, 5.0)

    def __init__(self, ref: np.ndarray):
        self.ref = ref + EPS

    def __call__(self, X, starts, win):
        out = np.empty((len(starts), len(self.BANDS) + 1))
        for i, s in enumerate(starts):
            r = X[s:s + win].mean(axis=0) / self.ref
            out[i] = np.histogram(r, bins=[-np.inf, *self.BANDS, np.inf])[0][:len(self.BANDS) + 1]
        return out / X.shape[1]


FAMILIES = {
    "F1_variability": feat_fano,
    "F2_covariance": feat_covstruct,
    "F3_spectral": feat_spectral,
    # F4 needs a healthy reference, so it is constructed at fit time.
}
