#!/usr/bin/env python3
"""
Label-free attribution on permutation-invariant features.

Preregistered in research/INVARIANT_ATTRIBUTION_NOTE.md: the mode -> feature
mapping, the rule, the success criteria and the prediction were all committed
before this was written, including the stated uncertainty about GEOMETRY_ROTATION.

WHY IT HAD TO BE TESTED
-----------------------
PERMUTATION_INVARIANT.md recommended invariant summaries for attribution on the
strength of a SUPERVISED probe. 63_invariant_detector.py then took the analogous
step for detection, unsupervised, and it failed on both axes. A supervised probe
showing information exists does not mean an unsupervised rule can use it, and the
attribution half of that recommendation was exposed to the same risk.

WHAT LABEL-FREE MEANS HERE
--------------------------
No episode labels at run time: nothing is fitted to which fault occurred, and
calibration comes from each episode's own clean prefix. It DOES use knowledge of
how the faults are injected to assign each mode a feature -- the same standing as
EXPECTED_ATTRIBUTION in 22_decoder_guard.py, which is what makes this comparable
to the guard's 56%. It is not the standing of a monitor facing an unknown fault.

Usage: python3 scripts/64_invariant_attribution.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250
MIN_CLEAN = 3

# Committed in the preregistration, before this file existed. Index into the
# twelve summaries defined in 62_permutation_invariant.py, in their fixed order:
# mean sd skew kurtosis p05 p25 p50 p75 p95 frac_unchanged frac_severely_down
# participation_ratio
FEATURE_INDEX = {"mean": 0, "sd": 1, "skew": 2, "kurtosis": 3,
                 "frac_severely_down": 10}
MAPPING = {
    "CHANNEL_DROPOUT": "frac_severely_down",
    "RATE_LOSS": "mean",
    "GAIN_DRIFT": "sd",
    "GEOMETRY_ROTATION": "skew",
}
# Current values the rule must beat on BOTH participants, from ATTRIBUTION_ACCURACY.
CURRENT = {"T11": 0.563, "T5": 0.525}
CHANCE = 0.25


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def robust_z(v: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Calibrate against the episode's own clean prefix, as DecoderGuard does."""
    med = float(np.median(ref))
    mad = float(np.median(np.abs(ref - med))) * 1.4826
    scale = mad if mad > 1e-9 else (float(np.std(ref)) or 1.0)
    return (v - med) / scale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    inj = _load("inj", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")
    pinv = _load("pinv", "62_permutation_invariant.py")

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    sc = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    sc = sc[(sc.detector == "decoder_guard") & (sc.split == "test") & sc.crossed]
    crossing = dict(zip(sc.episode_id, sc.crossing_w))
    keep = set(sc.episode_id)

    modes = list(MAPPING)
    idx = [FEATURE_INDEX[MAPPING[m]] for m in modes]

    conf: Counter = Counter()
    for e in episodes:
        if e.episode_id not in keep or e.block_id not in ds.neural or e.mode == "NONE":
            continue
        X = ds.neural[e.block_id]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        ow = int(np.searchsorted(starts, e.onset_bin))
        ow_strict = int(np.searchsorted(starts + WINDOW_BINS, e.onset_bin, side="right"))
        cw = int(crossing[e.episode_id])
        if ow_strict < MIN_CLEAN or cw <= ow:
            continue

        Y, _ = inj.apply_episode(X, e)
        F = det.window_features(Y, starts, WINDOW_BINS)
        ref_profile = np.median(F[:ow_strict], axis=0)
        L = np.log1p(np.maximum(F, 0.0)) - np.log1p(np.maximum(ref_profile, 0.0))[None, :]
        A = np.vstack([pinv.invariant_features(L[i]) for i in range(len(L))])

        # Calibrate each assigned feature against the clean prefix, then the
        # attributed cause is the mode whose feature is most elevated. Majority
        # vote over the early-warning window: one window is noisy and the point
        # is a stable diagnosis.
        Z = np.vstack([np.abs(robust_z(A[:, j], A[:ow_strict, j])) for j in idx])
        seg = Z[:, ow:cw]
        if seg.shape[1] == 0:
            continue
        picks = [modes[int(np.argmax(seg[:, k]))] for k in range(seg.shape[1])]
        conf[(e.mode, Counter(picks).most_common(1)[0][0])] += 1

    rows, total, right = [], 0, 0
    for m in sorted({a for a, _ in conf}):
        n = sum(conf[(m, c)] for c in modes)
        # Correct means the attributed mode equals the injected one.
        ok = conf[(m, m)]
        total += n; right += ok
        rows.append({"injected_mode": m, "n": n, "n_correct": ok,
                     "accuracy": round(ok / n, 3) if n else None,
                     **{f"named_{c}": conf[(m, c)] for c in modes}})
    acc = right / total if total else float("nan")

    rot = next((r for r in rows if r["injected_mode"] == "GEOMETRY_ROTATION"), None)
    res = {
        "participant": P, "mapping": MAPPING,
        "n_episodes": total, "correct": right,
        "accuracy": round(acc, 4),
        "accuracy_current_guard": CURRENT[P],
        "change": round(acc - CURRENT[P], 4),
        "beats_current": bool(acc > CURRENT[P]),
        "rotation_accuracy": rot["accuracy"] if rot else None,
        "rotation_beats_chance": bool(rot and rot["accuracy"] > CHANCE),
        "by_mode": rows,
    }
    res["both_criteria_met"] = bool(res["beats_current"] and res["rotation_beats_chance"])

    print(f"=== {P}: {total} episodes ===")
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"\n  OVERALL   {right}/{total} = {100*acc:.1f}%   "
          f"vs guard {100*CURRENT[P]:.1f}%   change {100*(acc-CURRENT[P]):+.1f} pts   "
          f"{'BEATS' if res['beats_current'] else 'does not beat'}")
    print(f"  ROTATION  {100*(rot['accuracy'] if rot else 0):.1f}%   "
          f"vs guard 0.0%   (chance {100*CHANCE:.0f}%)   "
          f"{'beats chance' if res['rotation_beats_chance'] else 'AT OR BELOW CHANCE'}")
    print(f"\n  both criteria met: {res['both_criteria_met']}")

    sfx = "" if P == "T11" else f"_{P}"
    (OUT / f"invariant_attribution{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
