#!/usr/bin/env python3
"""
Run the frozen feature study: F1-F4 against the current features.

FAIRNESS: ONE SCORER FOR EVERYTHING
-----------------------------------
Each family produces a different kind of number, so comparing them through
different one-class models would confound "better feature" with "better
model" -- the same error the detector contract was written to avoid.

Every family here, and the control, goes through the SAME one-class scorer:
standardise on healthy windows, project to a fixed-dimension subspace, take the
Mahalanobis distance, calibrate robustly. Nothing is tuned per family.

**F0 is a control, not a fifth family.** It is the CURRENT feature -- per-channel
mean activity -- pushed through that identical scorer. Without it, a family
beating `decoder_guard` could be winning because of the shared scorer rather than
because of its features, and the study would not be able to tell the difference.
F0 is what "the current measurement, modelled the same way" scores.

The success criterion is the frozen one: **+0.05 session-level AUC over
`decoder_guard` v1 on BOTH participants in the same direction.** A family
helping one and not the other is a null result.

Usage: python3 scripts/33_run_feature_study.py [--participant T11|T5]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"

WINDOW_BINS, STEP_BINS, BIN_S = 1500, 250, 0.02
SUBSPACE_K = 10
EPS = 1e-9


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


class UniformOneClass:
    """The single scorer every family is judged through. Fitted on healthy only."""

    def fit(self, H: np.ndarray) -> "UniformOneClass":
        H = np.nan_to_num(H, nan=0.0, posinf=0.0, neginf=0.0)
        self.mu = H.mean(axis=0)
        self.sd = H.std(axis=0) + EPS
        Z = (H - self.mu) / self.sd
        C = np.cov(Z.T) if Z.shape[1] > 1 else np.array([[Z.var()]])
        w, V = np.linalg.eigh(np.atleast_2d(C))
        k = min(SUBSPACE_K, Z.shape[1])
        self.P = V[:, -k:]
        Y = Z @ self.P
        S = np.cov(Y.T) if k > 1 else np.array([[Y.var()]])
        self.Si = np.linalg.inv(np.atleast_2d(S) + np.eye(k) * 1e-6)
        d = self._d(H)
        med = float(np.median(d))
        mad = float(np.median(np.abs(d - med))) * 1.4826
        self.c, self.s = med, max(mad, 0.02 * abs(med), EPS)
        return self

    def _d(self, F):
        F = np.nan_to_num(F, nan=0.0, posinf=0.0, neginf=0.0)
        Y = ((F - self.mu) / self.sd) @ self.P
        return np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", Y, self.Si, Y), 0.0))

    def score(self, F):
        return np.maximum((self._d(F) - self.c) / self.s, 0.0)

    def recenter(self, pre):
        d = self._d(pre)
        med = float(np.median(d))
        mad = float(np.median(np.abs(d - med))) * 1.4826
        self.c, self.s = med, max(mad, 0.02 * abs(med), EPS)
        return self


def auc(E, H):
    E, H = np.asarray(E, float), np.asarray(H, float)
    if len(E) < 5 or len(H) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def boot_ci(E, H, n=2000, seed=0):
    """Bootstrap over EPISODES. Windows are 99.5% autocorrelated (Phase 3), so
    resampling them would give intervals roughly sqrt(55) too narrow."""
    rng = np.random.default_rng(seed)
    E, H = np.asarray(E, float), np.asarray(H, float)
    vals = [auc(rng.choice(E, len(E)), rng.choice(H, len(H))) for _ in range(n)]
    return tuple(round(float(v), 4) for v in np.percentile(vals, [2.5, 97.5]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    ff = _load("ff", "32_feature_families.py")
    inj = _load("injector", "17_fault_injector.py")
    det = _load("det", "19_detectors.py")
    rd = _load("refdec", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    _, meta_path = rd.decoder_paths(P)
    meta = json.loads(meta_path.read_text())
    plan, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    fit_blocks = [b for b in meta["train_blocks"] if b in ds.neural]
    ref = np.median(np.vstack([ds.neural[b][:3000] for b in fit_blocks]), axis=0)

    extractors = {
        "F0_control_mean": det.window_features,
        **ff.FAMILIES,
        "F4_counts": ff.ChannelCounts(ref),
    }

    print(f"Feature study — participant {P}")
    print(f"  frozen at {json.loads((REPO/'research/FEATURE_STUDY_FROZEN.json').read_text())['git_commit_at_freeze'][:12]}")
    print(f"  {len(episodes)} episodes, {len(extractors)} extractors "
          f"(F0 is a control, not a family)\n")

    # Fit each extractor's scorer on healthy windows from the training blocks.
    scorers = {}
    for name, fn in extractors.items():
        Hs = []
        for b in fit_blocks:
            X = ds.neural[b]
            st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            Hs.append(fn(X, st, WINDOW_BINS))
        scorers[name] = UniformOneClass().fit(np.vstack(Hs))
        print(f"  fitted {name}")

    rows = []
    by_block = {}
    for e in episodes:
        by_block.setdefault(e.block_id, []).append(e)

    done = 0
    for bid, eps in by_block.items():
        if bid not in ds.neural:
            continue
        X = ds.neural[bid]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        for e in eps:
            Y, _ = inj.apply_episode(X, e)
            onset_w = int(np.searchsorted(starts, e.onset_bin))
            if onset_w < 6:
                continue
            for name, fn in extractors.items():
                F = fn(Y, starts, WINDOW_BINS)
                sc = scorers[name].recenter(F[:onset_w]).score(F)
                rows.append({"episode_id": e.episode_id, "block_id": bid,
                             "extractor": name, "mode": e.mode,
                             "severity": e.severity_label, "onset_w": onset_w,
                             "scores": ",".join(f"{v:.4f}" for v in sc)})
            done += 1
            if done % 100 == 0:
                print(f"  {done} episodes")

    df = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    df.to_csv(OUT / f"feature_scores{sfx}.csv", index=False)
    print(f"\nwrote {OUT/f'feature_scores{sfx}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
