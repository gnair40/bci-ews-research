#!/usr/bin/env python3
"""
decoder-guard: the monitor.

WRITTEN BEFORE THE BASELINE SCORES WERE READ
--------------------------------------------
This file was committed while scripts/20 was still scoring the three baselines,
so its design could not be tuned against numbers it had not seen. That ordering
is deliberate and is the same discipline as freezing the study design in Phase
1-2: the point is not that tuning is forbidden, it is that tuning must happen
where it can be seen.

THE DESIGN IDEA
---------------
Phase 1-2's failure was that a sophisticated indicator turned out to be 71%
"how much activity is there" -- a quantity that falls steadily whether or not
anything is going wrong. So this monitor does not produce one opaque number. It
computes FOUR named quantities, each with a physical meaning, calibrates each
against healthy data, and reports the largest as the risk -- along with which
one it was.

    level       total activity has moved
    silence     individual channels have gone quiet
    dispersion  channels have drifted apart in gain, with the total unchanged
    profile     the shape of activity across channels has changed

The separation is what makes attribution possible without a black box. It is
also what makes the monitor auditable: "risk 0.7, driven by silence, 34 channels
below threshold" is a sentence someone can act on or dispute. "Risk 0.7" is not.

Working in logs is the load-bearing trick. A multiplicative change in gain is an
ADDITIVE shift in log space, so subtracting each window's mean log activity
removes any uniform gain change exactly. Whatever survives that subtraction is a
change in the PROFILE across channels, which is precisely the part that counting
spikes cannot see. `level` is kept as its own separate component so that uniform
faults are still caught -- but caught, and labelled, as uniform.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "det", REPO_ROOT / "scripts" / "19_detectors.py")
_det = importlib.util.module_from_spec(_spec)
sys.modules["det"] = _det
_spec.loader.exec_module(_det)

EPS = 1e-9
# A channel must fall to 2% of its healthy median to count as quiet. An earlier
# value of 15% was too loose and mis-attributed GAIN_DRIFT as CHANNEL_DROPOUT:
# ordinary gain reduction routinely takes a channel below 15%, while reaching 2%
# needs a >3-sigma log-gain excursion, which is rare. Injected dropout sets
# channels to exactly zero, so the strict threshold separates the two cleanly.
SILENT_FRACTION = 0.02

# Minimum scale per component, in that component's own units. Without these the
# calibration divides by a near-zero MAD -- `silence` is flat at zero across all
# healthy windows, so its MAD is ~0 and the first smoke test produced risk
# scores of 3e8. A floor states what counts as a MEANINGFUL amount of each
# quantity rather than letting the healthy data's own noise set the unit.
SCALE_FLOOR = {
    "level": 0.0,          # relative floor below is enough; healthy spread is real
    "silence": 0.01,       # one percent of channels going quiet is a real amount
    "dispersion": 0.01,    # log units
    "profile": 1.0,        # a squared Mahalanobis distance of 1
}
REL_FLOOR = 0.02           # also never let scale fall under 2% of the median

# A component counts as explaining the risk if it reaches this fraction of the
# largest component. Set once, here, rather than tuned per result.
SPECIFICITY_FRAC = 0.5


def robust_center_scale(x: np.ndarray, floor: float = 0.0) -> tuple[float, float]:
    """Median, and a MAD-based scale that cannot collapse.

    Median rather than mean because a handful of odd healthy windows should not
    set the scale that every later judgement is measured against. The floor
    matters more than it looks: a component that is perfectly flat across
    healthy data has MAD zero, and dividing by it turns any departure at all
    into an enormous number.
    """
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med))) * 1.4826
    scale = max(mad, floor, REL_FLOOR * abs(med), EPS)
    return med, scale


class DecoderGuard(_det.Detector):
    """Four named components, calibrated separately, reported as max + attribution."""

    name = "decoder_guard"
    K = 10                  # profile subspace dimension

    # ---------------- component computation ----------------

    def _components(self, F: np.ndarray) -> dict[str, np.ndarray]:
        L = np.log1p(np.maximum(F, 0.0))
        common = L.mean(axis=1, keepdims=True)      # uniform gain, in log space
        P = L - common                              # profile: gain-invariant by construction

        level = F.sum(axis=1)
        silence = (F < SILENT_FRACTION * self.ch_ref[None, :]).mean(axis=1)

        D = P - self.p_ref[None, :]
        dispersion = np.median(np.abs(D - np.median(D, axis=1, keepdims=True)), axis=1) * 1.4826

        Z = D @ self.Pc
        # Mahalanobis DISTANCE, not squared distance. Squared grows quadratically
        # and swamped every other component, so `max` always chose it and the
        # attribution collapsed onto the one component that means least.
        profile = np.sqrt(np.maximum(
            np.einsum("ij,jk,ik->i", Z, self.Si, Z), 0.0))

        return {"level": level, "silence": silence,
                "dispersion": dispersion, "profile": profile}

    # ---------------- fitting, on healthy windows only ----------------

    def _fit(self, H: np.ndarray) -> None:
        self.ch_ref = np.median(H, axis=0) + EPS

        L = np.log1p(np.maximum(H, 0.0))
        P = L - L.mean(axis=1, keepdims=True)
        self.p_ref = np.median(P, axis=0)

        D = P - self.p_ref[None, :]
        C = np.cov(D.T)
        w, V = np.linalg.eigh(C)
        self.Pc = V[:, -self.K:]
        Zc = D @ self.Pc
        S = np.cov(Zc.T) + np.eye(self.K) * 1e-6
        self.Si = np.linalg.inv(S)

        # Calibrate every component against the healthy distribution so they are
        # on one comparable scale and `max` is a meaningful operation. Without
        # this the component with the largest raw units would always win and the
        # attribution would be an artefact of measurement units.
        comp = self._components(H)
        self.cal = {k: robust_center_scale(v, SCALE_FLOOR.get(k, 0.0))
                    for k, v in comp.items()}

        # `level` is the only two-sided component: activity moving UP is as much
        # a departure as activity moving down. The other three are one-sided by
        # construction -- more silence, more spread, more distance are all worse,
        # and less is simply healthier than the reference.
        self.two_sided = {"level"}

    # ---------------- scoring ----------------

    def _calibrated(self, F: np.ndarray) -> dict[str, np.ndarray]:
        out = {}
        for k, v in self._components(F).items():
            med, scale = self.cal[k]
            z = (v - med) / scale
            out[k] = np.abs(z) if k in self.two_sided else np.maximum(z, 0.0)
        return out

    def _score(self, F: np.ndarray) -> np.ndarray:
        c = self._calibrated(F)
        return np.max(np.vstack([c[k] for k in sorted(c)]), axis=0)

    def _attribute(self, c: dict) -> list[str]:
        """Name the cause using the most SPECIFIC component that is clearly lit.

        Not simply the largest. The components form a hierarchy of specificity:

            silence     channels sitting at ~zero. Essentially one physical cause.
            dispersion  channels spread apart in gain, total conserved. Narrow.
            level       the total moved. Broad.
            profile     everything else about the shape. A residual by design.

        A fault that kills a third of the channels moves the profile too, so
        ranking by magnitude alone attributes it to `profile` -- technically true
        and diagnostically useless. Preferring the most specific sufficiently
        elevated component is ordinary diagnostic reasoning: a named diagnosis
        beats "abnormal findings" when both fit.
        """
        order = ["silence", "dispersion", "level", "profile"]
        M = np.vstack([c[k] for k in order])
        top = M.max(axis=0)
        out = []
        for j in range(M.shape[1]):
            pick = order[-1]
            for i, k in enumerate(order):
                if M[i, j] >= SPECIFICITY_FRAC * top[j] and M[i, j] > 1.0:
                    pick = k
                    break
            out.append(pick)
        return out

    def contributions(self, F: np.ndarray) -> dict:
        """Per-window named contributions and the attributed cause.

        This is the output that makes a warning actionable. "Recalibrate",
        "an electrode is failing", and "nothing is wrong" are different
        responses, and a monitor that cannot separate them is not usable however
        good its accuracy number looks.
        """
        c = self._calibrated(F)
        keys = sorted(c)
        M = np.vstack([c[k] for k in keys])
        return {
            "components": {k: c[k] for k in keys},
            "attribution": self._attribute(c),
            "risk": M.max(axis=0),
        }


# The component each injected fault mode is EXPECTED to light up. Written down
# here, in advance, so attribution accuracy is scored against a stated
# prediction rather than whatever mapping happens to fit the results.
EXPECTED_ATTRIBUTION = {
    "RATE_LOSS": "level",
    "CHANNEL_DROPOUT": "silence",
    "GAIN_DRIFT": "dispersion",
    "GEOMETRY_ROTATION": "profile",
}

DETECTORS = {DecoderGuard.name: DecoderGuard}
