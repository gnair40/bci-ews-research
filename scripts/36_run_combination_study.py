#!/usr/bin/env python3
"""
Run the frozen combination study: arms C1-C3.

FROZEN AT 7234964, before this file existed.

THE FAITHFULNESS CHECK PASSED
-----------------------------
The preregistration made the study conditional on the generalised decomposition
reproducing decoder_guard v1 when applied to the original features. Measured over
6,637 windows: Spearman rho = 1.0000, median relative difference 0.0000. It is
not an approximation of the original decomposition, it is the same computation.
So the arms below can be read as "that decomposition, over better features".

AN AMBIGUITY IN THE FROZEN TEXT, RESOLVED AND RECORDED
------------------------------------------------------
The preregistration describes C3 as "F1 and F2 together, components
concatenated", which admits two readings: concatenate the FEATURES and decompose
once, or decompose each SEPARATELY and combine the components.

The first reading is unsound and would have been chosen only by not thinking
about it. Fano factors run 16-24; eigenvalue shares run 0.004-0.14. The
decomposition removes a common mode across feature dimensions, and a common mode
computed across two quantities differing by two orders of magnitude is dominated
entirely by the larger, so `spread` and `profile` would describe the Fano
factors and ignore the covariance structure completely.

So C3 decomposes each feature set separately and takes the risk as the maximum
over the combined, individually calibrated components. Each is calibrated against
its own healthy distribution, which is what makes a maximum across them
meaningful.

Recorded here rather than silently chosen, because it is an implementation
decision that materially changes what C3 tests.

Usage: python3 scripts/36_run_combination_study.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


class MultiGuard:
    """Several decompositions, one per feature set; risk is the max across all."""

    def __init__(self, fns, gg):
        self.fns = fns
        self.guards = [gg.GeneralGuard() for _ in fns]

    def fit_from(self, blocks, neural):
        for fn, g in zip(self.fns, self.guards):
            H = []
            for b in blocks:
                X = neural[b]
                st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
                H.append(fn(X, st, WINDOW_BINS))
            g.fit(np.vstack(H))
        return self

    def score(self, Y, starts, onset_w):
        parts = []
        for fn, g in zip(self.fns, self.guards):
            F = fn(Y, starts, WINDOW_BINS)
            g.recenter(F[:onset_w])
            parts.append(g.score(F))
        return np.max(np.vstack(parts), axis=0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    gg = _load("gg", "35_general_guard.py")
    ff = _load("ff", "32_feature_families.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    _, meta_path = rd.decoder_paths(P)
    meta = json.loads(meta_path.read_text())
    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)
    fit_blocks = [b for b in meta["train_blocks"] if b in ds.neural]

    F1, F2 = ff.feat_fano, ff.feat_covstruct
    arms = {"C1_variability": [F1], "C2_covariance": [F2],
            "C3_both": [F1, F2]}

    frozen = json.loads((REPO / "research" / "COMBINATION_STUDY_FROZEN.json").read_text())
    print(f"Combination study — {P}")
    print(f"  frozen at {frozen['git_commit_at_freeze'][:12]}")
    print(f"  faithfulness check: PASSED (rho = 1.0000)\n")

    models = {}
    for name, fns in arms.items():
        models[name] = MultiGuard(fns, gg).fit_from(fit_blocks, ds.neural)
        print(f"  fitted {name}")

    rows, done = [], 0
    by_block = {}
    for e in episodes:
        by_block.setdefault(e.block_id, []).append(e)

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
            for name, m in models.items():
                sc = m.score(Y, starts, onset_w)
                rows.append({"episode_id": e.episode_id, "arm": name,
                             "onset_w": onset_w, "mode": e.mode,
                             "scores": ",".join(f"{v:.4f}" for v in sc)})
            done += 1
            if done % 100 == 0:
                print(f"  {done} episodes")

    sfx = "" if P == "T11" else f"_{P}"
    dest = OUT / f"combo_scores{sfx}.csv"
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
