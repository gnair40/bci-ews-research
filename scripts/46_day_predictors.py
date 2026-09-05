#!/usr/bin/env python3
"""
What makes a day good or bad for the monitor?

PREREGISTERED in research/DAY_PREDICTOR_PREREGISTRATION.md, which fixes the five
predictors, their PREDICTED SIGNS, the Bonferroni threshold (0.05/5 = 0.01), and
the requirement to report all five on both participants whatever they show.

The preregistration also states the power limit before looking: at n = 13 days a
Spearman correlation must reach |rho| ~ 0.68 to clear the corrected threshold, so
a null here means underpowered, not absent.

Predictors, all computed from that day's HEALTHY (uninjected) recordings only:
  P1 healthy dispersion   predicted NEGATIVE  (a wide reference hides departures)
  P2 mean firing rate     predicted POSITIVE  (more spikes, less counting noise)
  P3 active channels      predicted POSITIVE  (more places to see a fault)
  P4 within-day drift     predicted NEGATIVE  (already moving as a fault would)
  P5 decoder error        predicted NEGATIVE  (a day the decoder handles badly)

Usage: python3 scripts/46_day_predictors.py
"""
from __future__ import annotations

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
SILENT_FRACTION = 0.02          # same floor the guard uses
N_PREDICTORS = 5
ALPHA = 0.05 / N_PREDICTORS

PREDICTED_SIGN = {
    "P1_healthy_dispersion": -1,
    "P2_mean_firing_rate": +1,
    "P3_active_channels": +1,
    "P4_within_day_drift": -1,
    "P5_decoder_error": -1,
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def predictors_for(P: str) -> pd.DataFrame:
    det = _load("det", "19_detectors.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    # P5 needs the frozen reference decoder's error on each day's healthy data.
    dec_err = day_decoder_error(P, rd, ds)

    per_day: dict[int, list[np.ndarray]] = {}
    for b, X in ds.neural.items():
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(st) == 0:
            continue
        per_day.setdefault(day_of(b), []).append(det.window_features(X, st, WINDOW_BINS))

    rows = []
    for d, mats in sorted(per_day.items()):
        F = np.vstack(mats)
        if len(F) < 8:
            continue
        # P1: robust spread of each channel across the day's healthy windows,
        # summarised by the median channel. Robust so one odd window cannot set
        # it, and per-channel so it is not just the level in disguise.
        mad = np.median(np.abs(F - np.median(F, axis=0)), axis=0) * 1.4826
        p1 = float(np.median(mad))
        # P2: overall activity level.
        p2 = float(F.mean())
        # P3: channels above the guard's own silence floor, relative to the
        # day's own median channel, so this is not a rescaling of P2.
        ref = np.median(F, axis=0)
        p3 = float((ref > SILENT_FRACTION * np.median(ref)).sum())
        # P4: how far the day moves from its first quarter to its last, in units
        # of the day's own dispersion -- otherwise a high-rate day looks drifty
        # purely because its numbers are bigger.
        q = max(2, len(F) // 4)
        drift = np.abs(F[-q:].mean(axis=0) - F[:q].mean(axis=0))
        p4 = float(np.median(drift / (mad + 1e-9)))
        rows.append({"day": d, "n_healthy_windows": len(F),
                     "P1_healthy_dispersion": p1, "P2_mean_firing_rate": p2,
                     "P3_active_channels": p3, "P4_within_day_drift": p4,
                     "P5_decoder_error": dec_err.get(d, np.nan)})
    return pd.DataFrame(rows)


def day_decoder_error(P: str, rd, ds) -> dict[int, float]:
    """Frozen reference decoder's median angular error on each day's real data.

    Uses the decoder exactly as fitted -- no refitting per day, which would
    measure the day's fittability rather than the day's difficulty.
    """
    dec_path, _ = rd.decoder_paths(P)
    if not dec_path.exists():
        print(f"  P5 unavailable: {dec_path.name} missing — reported as NaN")
        return {}
    d = np.load(dec_path)
    W, mean, std = d["W"], d["mean"], d["std"]
    by_day: dict[int, list[str]] = {}
    for b in ds.neural:
        by_day.setdefault(day_of(b), []).append(b)
    out = {}
    for day, ids in by_day.items():
        e = rd.score_blocks(ds, ds.trials, ids, W, mean, std)
        if np.isfinite(e):
            out[day] = float(e)
    return out


def main() -> int:
    results = {}
    for P, sfx in [("T11", ""), ("T5", "_T5")]:
        dv = OUT / f"day_variance{sfx}.csv"
        if not dv.exists():
            print(f"missing {dv.name}; run 44_day_variance.py first")
            continue
        auc_by_day = pd.read_csv(dv)[["day", "auc"]]
        pred = predictors_for(P)
        d = auc_by_day.merge(pred, on="day", how="inner")
        d.to_csv(OUT / f"day_predictors{sfx}.csv", index=False)
        print(f"\n=== {P}: {len(d)} days ===")
        print(d.round(4).to_string(index=False))

        res = []
        for name, sign in PREDICTED_SIGN.items():
            v = d[name]
            if v.isna().all() or v.nunique() < 3:
                res.append({"predictor": name, "status": "not computable",
                            "predicted_sign": sign})
                continue
            m = v.notna()
            r, p = stats.spearmanr(v[m], d.auc[m])
            res.append({
                "predictor": name, "predicted_sign": sign,
                "spearman_rho": round(float(r), 3), "p_value": round(float(p), 4),
                "n_days": int(m.sum()),
                "sign_as_predicted": bool(np.sign(r) == sign),
                "significant_bonferroni": bool(p < ALPHA),
                # A result only supports the mechanism if it is BOTH significant
                # and in the direction committed before looking.
                "supports_mechanism": bool(p < ALPHA and np.sign(r) == sign),
            })
        results[P] = res
        print(f"\n  {'predictor':<26}{'pred':>6}{'rho':>8}{'p':>9}   verdict")
        for x in res:
            if x.get("status"):
                print(f"  {x['predictor']:<26}{'':>6}{'—':>8}{'—':>9}   not computable")
                continue
            v = ("SUPPORTS mechanism" if x["supports_mechanism"]
                 else "sig, WRONG SIGN" if x["significant_bonferroni"]
                 else "not significant")
            print(f"  {x['predictor']:<26}{x['predicted_sign']:>+6}"
                  f"{x['spearman_rho']:>8.3f}{x['p_value']:>9.4f}   {v}")
        print(f"  (Bonferroni threshold p < {ALPHA})")

    (OUT / "day_predictors_result.json").write_text(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
