#!/usr/bin/env python3
"""
Detectors: everything that turns a window of neural features into a risk score.

THE CONTRACT
------------
A detector sees ONLY the feature stream the decoder sees. It never sees the
decoder's output, the task, the performance number, or any degradation label.
It is fitted on healthy windows alone.

    fit(healthy_windows)   healthy data only, once
    score(windows)         -> one raw score per window, higher = less healthy

Everything downstream -- calibration, thresholds, states, lead time -- is the
harness's job, not the detector's. Keeping that boundary sharp is what makes
the baselines and the monitor comparable: they differ only in this one function.

WHY THE BASELINES ARE HERE
--------------------------
Phase 1-2 found that mean firing rate alone predicted performance as well as a
five-dimensional pipeline with robust statistics. So "did the monitor beat
something trivial?" is the question that decides whether any of this was worth
building, and it can only be answered if the trivial things are implemented to
the same standard and scored by the same harness.

Three baselines, in increasing order of sophistication:

    MeanActivity        counting spikes. The bar that must be cleared.
    RobustDispersion    the Phase 1-2 indicator, reimplemented on windows.
    DistributionShift   a KL-divergence-style distance to a healthy reference,
                        in the spirit of the published MINDFUL measure that
                        scripts/09 reproduced at r = 0.985.
"""
from __future__ import annotations

import numpy as np

EPS = 1e-9


# --------------------------------------------------------------------------
# WINDOW FEATURES -- the common input every detector consumes
# --------------------------------------------------------------------------

def window_features(X: np.ndarray, starts: np.ndarray, win: int) -> np.ndarray:
    """Per-window, per-channel mean activity. Shape (n_windows, n_channels).

    Deliberately simple and deliberately shared. If each detector computed its
    own features from raw bins, differences between detectors would confound
    "better detector" with "better preprocessing", and the comparison would say
    nothing. They all get the same view; only what they do with it differs.
    """
    out = np.empty((len(starts), X.shape[1]), dtype=np.float64)
    for i, s in enumerate(starts):
        out[i] = X[s:s + win].mean(axis=0)
    return out


class Detector:
    """Base class. Subclasses implement _fit and _score."""
    name = "base"
    needs = "window_means"

    def fit(self, H: np.ndarray) -> "Detector":
        if H.ndim != 2 or len(H) < 8:
            raise ValueError(f"{self.name}: need at least 8 healthy windows, got {H.shape}")
        self._fit(H)
        return self

    def score(self, F: np.ndarray) -> np.ndarray:
        s = self._score(F)
        return np.asarray(s, dtype=np.float64).reshape(-1)

    def _fit(self, H: np.ndarray) -> None: raise NotImplementedError
    def _score(self, F: np.ndarray) -> np.ndarray: raise NotImplementedError

    def contributions(self, F: np.ndarray) -> dict:
        """Named, unit-carrying components of the score. Empty unless overridden."""
        return {}


# --------------------------------------------------------------------------
# BASELINE 1 -- counting spikes
# --------------------------------------------------------------------------

class MeanActivity(Detector):
    """Absolute z-score of total activity against the healthy distribution.

    One line of arithmetic. In Phase 1-2 this matched the entire sophisticated
    pipeline (rho = -0.880 vs +0.858), so it is not a straw man -- it is the
    incumbent, and anything that fails to beat it has added nothing.

    Two-sided on purpose: activity going UP is as much a departure from healthy
    as activity going down, and a one-sided detector would be silently blind to
    half of the fault space.
    """
    name = "mean_activity"

    def _fit(self, H):
        t = H.sum(axis=1)
        self.mu = float(t.mean())
        self.sd = float(t.std()) + EPS

    def _score(self, F):
        return np.abs(F.sum(axis=1) - self.mu) / self.sd


# --------------------------------------------------------------------------
# BASELINE 2 -- the Phase 1-2 indicator
# --------------------------------------------------------------------------

class RobustDispersion(Detector):
    """Sum of squared robust spread across a projection fitted on healthy data.

    This is the indicator the frozen Phase 1-2 design used, reimplemented at
    window level. It is included because a project should be able to say what
    its own earlier attempt scores under its own later test -- and because it
    failed the silence gate once already, which makes it a useful negative.
    """
    name = "robust_dispersion"
    K = 5

    def _fit(self, H):
        self.mu = H.mean(axis=0)
        C = np.cov((H - self.mu).T)
        w, V = np.linalg.eigh(C)
        self.P = V[:, -self.K:]                      # top-K principal directions
        Z = (H - self.mu) @ self.P
        d = self._disp(Z)
        self.dmu, self.dsd = float(d.mean()), float(d.std()) + EPS

    @staticmethod
    def _disp(Z):
        # MAD scaled to be comparable to a standard deviation for normal data.
        med = np.median(Z, axis=1, keepdims=True)
        mad = np.median(np.abs(Z - med), axis=1) * 1.4826
        return mad ** 2

    def _score(self, F):
        Z = (F - self.mu) @ self.P
        return np.abs(self._disp(Z) - self.dmu) / self.dsd


# --------------------------------------------------------------------------
# BASELINE 3 -- distance to the healthy distribution
# --------------------------------------------------------------------------

class DistributionShift(Detector):
    """Symmetrised Gaussian KL divergence from healthy, in a reduced subspace.

    The published MINDFUL measure compares the neural distribution against a
    reference and correlates with concurrent performance. It was reproduced
    exactly in scripts/09 (r = 0.985), so it belongs in the comparison as the
    strongest published baseline.

    Reduced to K dimensions first: a 384x384 covariance estimated from a few
    dozen windows is singular, and inverting it would produce large, confident,
    meaningless numbers.
    """
    name = "distribution_shift"
    K = 12

    def _fit(self, H):
        self.mu = H.mean(axis=0)
        C = np.cov((H - self.mu).T)
        w, V = np.linalg.eigh(C)
        self.P = V[:, -self.K:]
        Z = (H - self.mu) @ self.P
        self.m0 = Z.mean(axis=0)
        self.S0 = np.cov(Z.T) + np.eye(self.K) * 1e-6
        self.S0i = np.linalg.inv(self.S0)
        self.ld0 = np.linalg.slogdet(self.S0)[1]
        # Local reference for a single window: how far a healthy window sits.
        d = self._kl_points(Z)
        self.dmu, self.dsd = float(d.mean()), float(d.std()) + EPS

    def _kl_points(self, Z):
        # Per-window Mahalanobis distance to the healthy reference. The full
        # symmetrised KL needs two distributions; a single window has only a
        # point, so the mean term is what survives, which is exactly this.
        D = Z - self.m0
        return np.einsum("ij,jk,ik->i", D, self.S0i, D)

    def _score(self, F):
        Z = (F - self.mu) @ self.P
        return np.abs(self._kl_points(Z) - self.dmu) / self.dsd


BASELINES = {d.name: d for d in (MeanActivity, RobustDispersion, DistributionShift)}
