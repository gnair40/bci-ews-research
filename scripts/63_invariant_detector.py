#!/usr/bin/env python3
"""
A one-class detector on permutation-invariant features.

Preregistered in research/INVARIANT_DETECTOR_NOTE.md with numeric success
criteria and a prediction. ONE candidate: if it fails, that is the result, and no
tuned variant follows.

WHAT IT IS
----------
decoder_guard reduces each window to four scalars (silence, dispersion, level,
profile) and takes the largest. 62_permutation_invariant.py showed that the
information distinguishing faults lives in the SHAPE of the per-channel change
distribution, which those four scalars discard. This scores that shape instead.

Structure deliberately mirrors DecoderGuard so the comparison is about the
features and nothing else:

  global, fitted on healthy windows only   the covariance of the 12 invariant
                                           summaries -- their normal joint shape
  local, re-estimated per episode          the reference channel profile and the
                                           centre/scale, from that episode's own
                                           strictly-clean pre-onset windows

No fault ever touches the fit. The twelve features are imported from
62_permutation_invariant.py unchanged -- not re-chosen, not tuned.

DIFFERENT PROBLEM FROM THE PROBE THAT MOTIVATED IT
--------------------------------------------------
That probe was supervised and separated faults FROM EACH OTHER. This is
unsupervised and must separate a fault FROM HEALTHY RECORDING. The second is
harder and the first does not guarantee it.

Usage: python3 scripts/63_invariant_detector.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250
MIN_CLEAN = 3
EPS = 1e-9
SEED = 20260902

# Fixed in advance, in the preregistration.
CURRENT_AUC = {"T11": 0.672, "T5": 0.742}
SILENCE_GATE = 0.10


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def auc(pos, neg):
    if len(pos) < 5 or len(neg) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(pos, neg, alternative="two-sided")
    return float(u / (len(pos) * len(neg)))


def robust_center_scale(v: np.ndarray) -> tuple[float, float]:
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med))) * 1.4826
    return med, (mad if mad > 1e-9 else float(np.std(v)) or 1.0)


class InvariantGuard:
    """One-class. Global covariance of the invariant summaries, local centring."""

    def __init__(self, invariant_features):
        self._inv = invariant_features
        self.Si = None
        self.ref = None
        self.cal = None

    @staticmethod
    def _deviation(F: np.ndarray, ref: np.ndarray) -> np.ndarray:
        return np.log1p(np.maximum(F, 0.0)) - np.log1p(np.maximum(ref, 0.0))[None, :]

    def _summaries(self, F: np.ndarray, ref: np.ndarray) -> np.ndarray:
        D = self._deviation(F, ref)
        return np.vstack([self._inv(D[i]) for i in range(len(D))])

    def fit(self, healthy_blocks: list[np.ndarray]) -> "InvariantGuard":
        """healthy_blocks: per-block window-feature matrices, faults never seen."""
        S = []
        for Fb in healthy_blocks:
            if len(Fb) < 8:
                continue
            S.append(self._summaries(Fb, np.median(Fb, axis=0)))
        A = np.vstack(S)
        # Standardise before the covariance so a percentile and a fraction are
        # not weighted by their units, then ridge it -- 12 dimensions from a few
        # hundred windows is well posed, but the ridge keeps it so if a summary
        # is nearly constant on a quiet array.
        self.mu_, self.sd_ = A.mean(axis=0), A.std(axis=0) + EPS
        Z = (A - self.mu_) / self.sd_
        C = np.cov(Z.T) + np.eye(Z.shape[1]) * 1e-3
        self.Si = np.linalg.inv(C)
        return self

    def recenter(self, pre: np.ndarray) -> "InvariantGuard":
        """Local notion of normal, from this episode's clean prefix only."""
        self.ref = np.median(pre, axis=0)
        A = self._summaries(pre, self.ref)
        Z = (A - self.mu_) / self.sd_
        d = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", Z, self.Si, Z), 0.0))
        self.cal = robust_center_scale(d)
        return self

    def score(self, F: np.ndarray, clip: bool = True) -> np.ndarray:
        A = self._summaries(F, self.ref)
        Z = (A - self.mu_) / self.sd_
        d = np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", Z, self.Si, Z), 0.0))
        med, scale = self.cal
        z = (d - med) / scale
        # clip=False exists for one diagnostic only. Clipping at zero is the
        # convention DecoderGuard uses for its one-sided components, so keeping
        # it makes the comparison fair -- but it also pins early windows at the
        # floor, which could MANUFACTURE the upward trend that fails the silence
        # gate. The unclipped series answers whether the gate failure is the
        # idea or the convention.
        return np.maximum(z, 0.0) if clip else z


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")
    pinv = _load("pinv", "62_permutation_invariant.py")

    _, meta_path = rd.decoder_paths(P)
    meta = json.loads(meta_path.read_text())
    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    sc = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    sc = sc[(sc.detector == "decoder_guard") & (sc.split == "test")]
    crossed = dict(zip(sc.episode_id, sc.crossed))
    crossing = dict(zip(sc.episode_id, sc.crossing_w))
    in_test = set(sc.episode_id)

    # Global fit: healthy training blocks only. No fault, no test episode.
    fit_blocks = []
    for b in meta["train_blocks"]:
        if b not in ds.neural:
            continue
        X = ds.neural[b]
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(st) >= 8:
            fit_blocks.append(det.window_features(X, st, WINDOW_BINS))
    guard = InvariantGuard(pinv.invariant_features).fit(fit_blocks)
    print(f"  fitted on {sum(len(f) for f in fit_blocks)} healthy windows "
          f"from {len(fit_blocks)} blocks\n")

    E, H, healthy_series, healthy_series_raw = [], [], [], []
    for e in episodes:
        if e.episode_id not in in_test or e.block_id not in ds.neural:
            continue
        X = ds.neural[e.block_id]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        ow = int(np.searchsorted(starts, e.onset_bin))
        ow_strict = int(np.searchsorted(starts + WINDOW_BINS, e.onset_bin, side="right"))
        if ow_strict < MIN_CLEAN:
            continue
        Y, _ = inj.apply_episode(X, e)
        F = det.window_features(Y, starts, WINDOW_BINS)
        guard.recenter(F[:ow_strict])
        s = guard.score(F)
        if not crossed.get(e.episode_id, False):
            H.append(float(np.median(s)))
            healthy_series.append(s)
            healthy_series_raw.append(guard.score(F, clip=False))
        else:
            cw = int(crossing.get(e.episode_id, -1))
            if cw > ow and len(s) >= cw:
                E.append(float(np.median(s[ow:cw])))

    a = auc(np.array(E), np.array(H))

    # G1 SILENCE -- the gate definition copied from 21_score_report.py, unchanged.
    taus, ps = [], []
    for y in healthy_series:
        if len(y) < 8:
            continue
        t, p = stats.kendalltau(np.arange(len(y)), y)
        if np.isfinite(t):
            taus.append(t); ps.append(p)
    frac_sig = float(np.mean(np.array(ps) < 0.05)) if ps else float("nan")

    # Same gate on the UNCLIPPED series. If the trend survives, the drift is
    # real; if it collapses, the clipping produced it and the finding is about
    # my convention rather than about invariant features.
    taus_r, ps_r = [], []
    for y in healthy_series_raw:
        if len(y) < 8:
            continue
        t, p = stats.kendalltau(np.arange(len(y)), y)
        if np.isfinite(t):
            taus_r.append(t); ps_r.append(p)
    frac_sig_raw = float(np.mean(np.array(ps_r) < 0.05)) if ps_r else float("nan")

    res = {
        "participant": P,
        "n_faulted": len(E), "n_healthy": len(H),
        "auc_invariant": round(a, 4),
        "auc_current_decoder_guard": CURRENT_AUC[P],
        "auc_change": round(a - CURRENT_AUC[P], 4),
        "beats_current": bool(a > CURRENT_AUC[P]),
        "silence_median_tau": round(float(np.median(taus)), 3) if taus else None,
        "silence_fraction_significant": round(frac_sig, 3),
        "silence_gate_pass": bool(frac_sig <= SILENCE_GATE),
        "n_healthy_episodes_tested": len(ps),
        "silence_median_tau_unclipped": round(float(np.median(taus_r)), 3) if taus_r else None,
        "silence_fraction_significant_unclipped": round(frac_sig_raw, 3),
        "clipping_explains_the_trend": bool(frac_sig - frac_sig_raw > 0.30),
    }
    print(f"  DETECTION   AUC {a:.4f}   vs current {CURRENT_AUC[P]:.3f}   "
          f"change {a - CURRENT_AUC[P]:+.4f}   "
          f"{'BEATS' if res['beats_current'] else 'does not beat'}")
    print(f"  SILENCE     {frac_sig:.1%} of healthy episodes trend   "
          f"(gate needs <= {SILENCE_GATE:.0%})   "
          f"{'PASS' if res['silence_gate_pass'] else 'FAIL'}")
    print(f"  UNCLIPPED   {frac_sig_raw:.1%} trend, median tau "
          f"{res['silence_median_tau_unclipped']}   "
          f"({'clipping was the cause' if res['clipping_explains_the_trend'] else 'the drift is real'})")
    print("\n" + json.dumps(res, indent=2))
    sfx = "" if P == "T11" else f"_{P}"
    (OUT / f"invariant_detector{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
