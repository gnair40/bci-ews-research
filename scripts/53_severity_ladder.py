#!/usr/bin/env python3
"""
Does the severity ladder mean the same thing on every session?

Prediction committed in addendum 2 of research/CEILING_CHALLENGE_NOTE.md before
running: the ladder holds on low-baseline sessions and collapses on high-baseline
ones.

WHY THIS IS A QUESTION ABOUT THE CORPUS, NOT A DETECTOR
-------------------------------------------------------
Every benchmark here treats fault severity as a CONTROLLED variable with three
ordered levels -- benign, sub, crossing -- calibrated once, globally, in
17_fault_injector.py. The ceiling result showed achieved damage ranges from
+19.8 deg on one session to +0.4 deg on another. If damage collapses on some
sessions, those three labels do not mean the same thing everywhere, and every
severity-stratified result in this project rests on an assumption that does not
hold uniformly.

A cell is monotone when median damage strictly increases benign -> sub ->
crossing. Cells with fewer than 2 episodes per level are reported as
unmeasurable, not dropped silently.

Usage: python3 scripts/53_severity_ladder.py --participant T11|T5
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
MIN_PER_CELL = 2
LEVELS = ["benign", "sub", "crossing"]
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    harness = _load("harness", "20_evaluation_harness.py")
    inj = _load("inj", "17_fault_injector.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    dec_path, _ = rd.decoder_paths(P)
    dz = np.load(dec_path)
    dec = (dz["W"], dz["mean"], dz["std"])

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    # Every faulted episode, so the ladder is measured on the whole corpus rather
    # than the 40-per-day subsample the detector analyses used.
    recs = []
    for e in episodes:
        bid = e.block_id
        if bid not in ds.neural or e.mode == "NONE":
            continue
        kin = ds.kinematics.get(bid, {})
        if "cursorPos" not in kin:
            continue
        X = ds.neural[bid]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        ow = int(np.searchsorted(starts, e.onset_bin))
        if ow < 6:
            continue
        unit, ok_dir = rd.intended_direction(kin)
        ok = ok_dir & rd.in_trial_mask(ds.trials, bid, X.shape[0])
        Y, _ = inj.apply_episode(X, e)
        perf = harness.window_performance(Y, starts, WINDOW_BINS, ok, unit, dec)
        pre, post = perf[:ow], perf[ow:]
        pre = pre[np.isfinite(pre)]; post = post[np.isfinite(post)]
        if len(pre) < 3 or len(post) < 3:
            continue
        recs.append({"day": day_of(bid), "mode": e.mode,
                     "severity": e.severity_label,
                     "damage": float(np.median(post) - np.median(pre)),
                     "baseline": float(np.median(pre))})
    D = pd.DataFrame(recs)
    sfx = "" if P == "T11" else f"_{P}"
    D.to_csv(OUT / f"severity_damage{sfx}.csv", index=False)
    print(f"  {len(D)} faulted episodes measured\n")

    cells, per_day = [], []
    for day, g in D.groupby("day"):
        mono, meas, total = 0, 0, 0
        for mode, gm in g.groupby("mode"):
            total += 1
            med = {}
            for lv in LEVELS:
                v = gm[gm.severity == lv].damage
                if len(v) >= MIN_PER_CELL:
                    med[lv] = float(np.median(v))
            if len(med) < 3:
                cells.append({"day": day, "mode": mode, "status": "unmeasurable",
                              **{f"med_{k}": round(v, 2) for k, v in med.items()}})
                continue
            meas += 1
            is_mono = med["benign"] < med["sub"] < med["crossing"]
            mono += int(is_mono)
            cells.append({"day": day, "mode": mode,
                          "status": "monotone" if is_mono else "NOT monotone",
                          **{f"med_{k}": round(v, 2) for k, v in med.items()}})
        per_day.append({"day": day, "modes_total": total, "modes_measurable": meas,
                        "modes_monotone": mono,
                        "monotone_fraction": round(mono / meas, 3) if meas else np.nan,
                        "baseline_deg": round(float(g.baseline.median()), 2)})

    C = pd.DataFrame(cells); M = pd.DataFrame(per_day)
    C.to_csv(OUT / f"severity_ladder_cells{sfx}.csv", index=False)
    M.to_csv(OUT / f"severity_ladder{sfx}.csv", index=False)
    print(M.to_string(index=False))

    res = {"participant": P, "n_days": int(len(M)),
           "n_cells": int(len(C)),
           "n_monotone": int((C.status == "monotone").sum()),
           "n_not_monotone": int((C.status == "NOT monotone").sum()),
           "n_unmeasurable": int((C.status == "unmeasurable").sum())}
    res["overall_monotone_fraction"] = round(
        res["n_monotone"] / max(1, res["n_monotone"] + res["n_not_monotone"]), 3)
    ok = M.monotone_fraction.notna()
    if ok.sum() >= 4:
        r, p = stats.spearmanr(M.loc[ok, "baseline_deg"], M.loc[ok, "monotone_fraction"])
        res["baseline_vs_monotone_fraction"] = {"rho": round(float(r), 3),
                                                "p": round(float(p), 4),
                                                "n_days": int(ok.sum())}
    worst = M.loc[ok].nsmallest(3, "monotone_fraction")
    res["worst_days"] = [int(x) for x in worst.day]
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"severity_ladder{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
