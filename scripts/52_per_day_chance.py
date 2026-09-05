#!/usr/bin/env python3
"""
Is the decoder already at chance on the bad days?

WHY THIS MATTERS, AND WHY IT IS A CHECK ON MY OWN RECOMMENDATION
----------------------------------------------------------------
reports/UNAMBIGUOUS_EPISODES.md concluded that injected faults do no measurable
damage on high-error sessions because the performance METRIC saturates, and
recommended a measure with more dynamic range at the bad end.

That recommendation is only right if the decoder still holds usable signal on
those days. If it is already indistinguishable from chance, there is nothing left
for a fault to destroy, and NO change of metric recovers anything -- a random
decoder produces a random trajectory under any measure. The recommendation would
then be wrong, and it is in the README.

So: measure each day's decoder error against ITS OWN chance level, using the same
shuffled-pairing procedure the reference decoder used, and test whether the two
are distinguishable.

Usage: python3 scripts/52_per_day_chance.py --participant T11|T5
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
N_SHUFFLE = 200
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

    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    dec_path, _ = rd.decoder_paths(P)
    dz = np.load(dec_path)
    W, mean, std = dz["W"], dz["mean"], dz["std"]
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    by_day: dict[int, list[str]] = {}
    for b in ds.neural:
        by_day.setdefault(day_of(b), []).append(b)

    rng = np.random.default_rng(SEED)
    rows = []
    # Directional concentration of the day's intended movements. This is NOT a
    # side quantity: a day whose targets all lie in similar directions has a LOW
    # shuffled-chance level, because pointing the popular way already scores
    # well. So the per-day chance level -- and therefore the margin over it --
    # depends on the task's geometry that day, not only on the decoder. Without
    # this column the margins are not comparable across days and the "at chance"
    # flag is easy to misread.
    for day, ids in sorted(by_day.items()):
        errs, chances, units = [], [], []
        for bid in ids:
            X = ds.neural[bid]
            kin = ds.kinematics.get(bid, {})
            if "cursorPos" not in kin:
                continue
            unit, ok_dir = rd.intended_direction(kin)
            ok = ok_dir & rd.in_trial_mask(ds.trials, bid, X.shape[0])
            n = int(ok.sum())
            if n < 100:
                continue
            Z = np.hstack([(X[ok] - mean) / std, np.ones((n, 1))])
            pred = Z @ W
            u = unit[ok]
            errs.append(rd.angular_error_deg(pred, u))
            units.append(u)
            # Chance for THIS day: same predictions, same intended directions,
            # pairing destroyed. Repeated so the estimate is not one draw.
            for _ in range(max(1, N_SHUFFLE // max(1, len(ids)))):
                chances.append(rd.angular_error_deg(pred, u[rng.permutation(n)]))
        if not errs:
            continue
        e = np.concatenate(errs)
        c = np.concatenate(chances)
        U = np.vstack(units)
        concentration = float(np.linalg.norm(U.mean(axis=0)))
        obs = float(np.nanmedian(e))
        ch = float(np.nanmedian(c))
        # Is this day's decoder distinguishable from its own chance level?
        ee, cc = e[np.isfinite(e)], c[np.isfinite(c)]
        u_stat, p = stats.mannwhitneyu(ee, cc, alternative="less")
        # scipy returns U1, the count of pairs with x > y (ties at half), so
        # U1/(nm) is P(error EXCEEDS chance error). It was previously stored
        # under the name prob_better_than_chance, which inverts its meaning --
        # a decoder 55 deg better than chance was recorded as 0.273 and read as
        # if that were its probability of beating chance. Both directions are
        # now written out so the number cannot be misread again.
        p_exceeds = float(u_stat / (len(ee) * len(cc)))
        p_better = 1.0 - p_exceeds
        rows.append({"day": day, "n_bins": int(len(ee)),
                     "median_error_deg": round(obs, 2),
                     "day_chance_deg": round(ch, 2),
                     "margin_deg": round(ch - obs, 2),
                     "direction_concentration": round(concentration, 4),
                     "prob_error_exceeds_chance": round(p_exceeds, 4),
                     "prob_better_than_chance": round(p_better, 4),
                     "p_vs_own_chance": float(f"{p:.3g}"),
                     "barely_beats_own_chance": bool(p_better < 0.55)})
        print(f"  day {day}: error {obs:6.2f}   own-chance {ch:6.2f}   "
              f"margin {ch-obs:+6.2f}   P(better) {p_better:.3f}   "
              f"concentration {concentration:.3f}"
              f"{'   BARELY BEATS OWN CHANCE' if p_better < 0.55 else ''}")

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    D.to_csv(OUT / f"per_day_chance{sfx}.csv", index=False)

    known = pd.read_csv(OUT / f"day_predictors{sfx}.csv")[["day", "auc"]]
    M = D.merge(known, on="day", how="inner")
    res = {"participant": P, "n_days": int(len(M)),
           "n_barely_beats_own_chance": int(M.barely_beats_own_chance.sum()),
           "days_barely_beating_own_chance":
               [int(x) for x in M.loc[M.barely_beats_own_chance, "day"]]}
    if len(M) >= 4:
        # The decisive comparison. Absolute angular error predicts the monitor's
        # accuracy strongly (P5, rho = -0.720). If margin over the day's OWN
        # chance does not, then P5 is not about how much real signal the decoder
        # retains -- which is what "the decoder is failing" was taken to mean.
        for a_, b_, k in [("margin_deg", "auc", "margin_vs_monitor_auc"),
                          ("direction_concentration", "auc",
                           "concentration_vs_monitor_auc"),
                          ("direction_concentration", "day_chance_deg",
                           "concentration_vs_day_chance")]:
            r, p = stats.spearmanr(M[a_], M[b_])
            res[k] = {"rho": round(float(r), 3), "p": round(float(p), 4)}
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"per_day_chance{sfx}.json").write_text(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
