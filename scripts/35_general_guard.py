#!/usr/bin/env python3
"""
The decoder-guard decomposition, generalised to any non-negative feature set.

FROZEN BEFORE IMPLEMENTATION
----------------------------
`research/COMBINATION_STUDY_FROZEN.json`, commit 7234964, fixes the four
structural roles below and the faithfulness check. This file implements that
specification; it does not choose it.

WHY A GENERALISATION IS NEEDED AT ALL
-------------------------------------
The feature study found two things that do not combine on their own:

    F1 and F2 are better FEATURES than per-channel means (+0.06 to +0.16
    against a matched control, on both participants)

    decoder_guard's advantage is mostly its four-component DECOMPOSITION
    (+0.10 and +0.23 over its own features under a generic scorer)

Nobody has applied the second to the first. But the original components are
defined for activity -- "channels gone silent" means nothing for an eigenvalue
share -- so they have to be restated structurally:

    level      overall magnitude of the feature vector
    extremes   fraction of dimensions in the far lower tail of healthy
    spread     robust dispersion across dimensions, common mode removed
    profile    Mahalanobis residual in that same subspace

Working in logs and removing the common mode is kept, because that is what makes
`spread` and `profile` invariant to a uniform rescaling -- the property the
original decomposition was built around and the reason it beats counting.

THE CHECK THAT CAN STOP THE STUDY
---------------------------------
Applied to the ORIGINAL features, this must approximately reproduce
decoder_guard v1. If it does not, it is not a generalisation, and the arms
cannot be read as "the same decomposition over better features". The
preregistration says the study stops in that case rather than reporting a
mislabelled comparison.

Usage: imported by scripts/36_run_combination_study.py
"""
from __future__ import annotations

import numpy as np

EPS = 1e-9
EXTREME_FRACTION = 0.02      # "far lower tail": 2% of the healthy median
SPECIFICITY_FRAC = 0.5
SUBSPACE_K = 10
SCALE_FLOOR = {"level": 0.0, "extremes": 0.01, "spread": 0.01, "profile": 1.0}
REL_FLOOR = 0.02
ORDER = ["extremes", "spread", "level", "profile"]     # most specific first


def robust_center_scale(x, floor=0.0):
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) * 1.4826
    return med, max(mad, floor, REL_FLOOR * abs(med), EPS)


class GeneralGuard:
    """decoder-guard's decomposition over an arbitrary non-negative feature set."""

    def __init__(self, name="general_guard"):
        self.name = name

    # ---- the four structural components ----
    def _components(self, F):
        F = np.nan_to_num(np.asarray(F, float), nan=0.0, posinf=0.0, neginf=0.0)
        F = np.maximum(F, 0.0)
        L = np.log1p(F)
        common = L.mean(axis=1, keepdims=True)     # uniform scaling, in log space
        P = L - common                             # invariant to it by construction

        level = F.sum(axis=1)
        extremes = (F < EXTREME_FRACTION * self.ref[None, :]).mean(axis=1)
        D = P - self.p_ref[None, :]
        spread = np.median(np.abs(D - np.median(D, axis=1, keepdims=True)), axis=1) * 1.4826
        Z = D @ self.Pc
        profile = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", Z, self.Si, Z), 0.0))
        return {"level": level, "extremes": extremes,
                "spread": spread, "profile": profile}

    def fit(self, H):
        H = np.nan_to_num(np.asarray(H, float), nan=0.0, posinf=0.0, neginf=0.0)
        H = np.maximum(H, 0.0)
        self.ref = np.median(H, axis=0) + EPS
        L = np.log1p(H)
        P = L - L.mean(axis=1, keepdims=True)
        self.p_ref = np.median(P, axis=0)
        D = P - self.p_ref[None, :]
        C = np.cov(D.T) if D.shape[1] > 1 else np.array([[D.var()]])
        w, V = np.linalg.eigh(np.atleast_2d(C))
        k = min(SUBSPACE_K, D.shape[1])
        self.Pc = V[:, -k:]
        Y = D @ self.Pc
        S = np.cov(Y.T) if k > 1 else np.array([[Y.var()]])
        self.Si = np.linalg.inv(np.atleast_2d(S) + np.eye(k) * 1e-6)
        comp = self._components(H)
        self.cal = {kk: robust_center_scale(v, SCALE_FLOOR.get(kk, 0.0))
                    for kk, v in comp.items()}
        self.two_sided = {"level"}
        return self

    def _calibrated(self, F):
        out = {}
        for k, v in self._components(F).items():
            med, sc = self.cal[k]
            z = (v - med) / sc
            out[k] = np.abs(z) if k in self.two_sided else np.maximum(z, 0.0)
        return out

    def score(self, F):
        c = self._calibrated(F)
        return np.max(np.vstack([c[k] for k in ORDER]), axis=0)

    def attribute(self, F):
        c = self._calibrated(F)
        M = np.vstack([c[k] for k in ORDER])
        top = M.max(axis=0)
        out = []
        for j in range(M.shape[1]):
            pick = ORDER[-1]
            for i, k in enumerate(ORDER):
                if M[i, j] >= SPECIFICITY_FRAC * top[j] and M[i, j] > 1.0:
                    pick = k; break
            out.append(pick)
        return out

    def recenter(self, pre):
        pre = np.maximum(np.nan_to_num(np.asarray(pre, float)), 0.0)
        self.ref = np.median(pre, axis=0) + EPS
        Lp = np.log1p(pre)
        self.p_ref = np.median(Lp - Lp.mean(axis=1, keepdims=True), axis=0)
        comp = self._components(pre)
        self.cal = {k: robust_center_scale(v, SCALE_FLOOR.get(k, 0.0))
                    for k, v in comp.items()}
        return self
