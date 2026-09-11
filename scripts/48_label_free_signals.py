#!/usr/bin/env python3
"""
Is there a label-free stand-in for decoder error?

Scope fixed in research/ABSTENTION_NOTE.md before running, including the
admission that NO SIGN IS PREDICTED for these four candidates -- so a sign that
emerges here carries less weight than P5's did.

Everything below is computed from the frozen decoder's OUTPUT STREAM on that
day's real recording. No target, no intended direction, no label is used at any
point. That is the whole requirement: the signal has to exist at run time.

  L1 output speed variability   robust spread of decoded speed
  L2 direction reversal rate    fraction of bins whose direction flips > 90 deg
  L3 output autocorrelation     lag-1 correlation of the decoded velocity vector
  L4 mean output speed

Two stages, each Bonferroni-corrected at 0.05/4 = 0.0125:
  stage 1  candidate vs DECODER ERROR   -- does it stand in for P5 at all?
  stage 2  candidate vs MONITOR AUC     -- does it predict what abstention needs?

Usage: python3 scripts/48_label_free_signals.py
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
ALPHA = 0.05 / 4
CANDIDATES = ["L1_speed_variability", "L2_reversal_rate",
              "L3_output_autocorr", "L4_mean_speed"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def signals_for_block(V: np.ndarray) -> dict[str, float]:
    """V is the decoded velocity stream, shape (n_bins, 2). Output only."""
    speed = np.linalg.norm(V, axis=1)
    med = float(np.median(speed))
    mad = float(np.median(np.abs(speed - med))) * 1.4826
    # L1 is scaled by the median so it is a coefficient of variation, not a
    # restatement of L4 -- otherwise a day with bigger commands would look more
    # variable purely because its numbers are bigger.
    l1 = mad / med if med > 1e-9 else np.nan

    ok = speed > 1e-9
    U = V[ok] / speed[ok, None]
    if len(U) > 2:
        cos = np.einsum("ij,ij->i", U[:-1], U[1:])
        l2 = float((cos < 0.0).mean())          # flip of more than 90 degrees
        l3 = float(np.mean(cos))                # lag-1 directional autocorrelation
    else:
        l2 = l3 = np.nan
    return {"L1_speed_variability": l1, "L2_reversal_rate": l2,
            "L3_output_autocorr": l3, "L4_mean_speed": float(np.mean(speed))}


def main() -> int:
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    results = {}
    for P, sfx in [("T11", ""), ("T5", "_T5")]:
        dp = OUT / f"day_predictors{sfx}.csv"
        if not dp.exists():
            print(f"missing {dp.name}; run 46_day_predictors.py first")
            continue
        known = pd.read_csv(dp)

        dec_path, _ = rd.decoder_paths(P)
        d = np.load(dec_path)
        W, mean, std = d["W"], d["mean"], d["std"]
        ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

        per_day: dict[int, list[dict]] = {}
        for b, X in ds.neural.items():
            V = rd.decode_stream(X, W, mean, std)
            per_day.setdefault(day_of(b), []).append(signals_for_block(V))
        rows = []
        for day, sigs in sorted(per_day.items()):
            r = {"day": day}
            for k in CANDIDATES:
                v = [s[k] for s in sigs if np.isfinite(s[k])]
                r[k] = float(np.mean(v)) if v else np.nan
            rows.append(r)
        lab = pd.DataFrame(rows)
        m = known.merge(lab, on="day", how="inner")
        m.to_csv(OUT / f"label_free_signals{sfx}.csv", index=False)

        print(f"\n=== {P}: {len(m)} days ===")
        print(m[["day", "auc", "P5_decoder_error"] + CANDIDATES].round(4).to_string(index=False))

        res = []
        for k in CANDIDATES:
            row = {"candidate": k}
            for stage, target in [("stage1_vs_decoder_error", "P5_decoder_error"),
                                  ("stage2_vs_monitor_auc", "auc")]:
                ok = m[k].notna() & m[target].notna()
                if ok.sum() < 4 or m.loc[ok, k].nunique() < 3:
                    row[stage] = {"rho": None, "p": None, "note": "not computable"}
                    continue
                r, p = stats.spearmanr(m.loc[ok, k], m.loc[ok, target])
                row[stage] = {"rho": round(float(r), 3), "p": round(float(p), 4),
                              "passes": bool(p < ALPHA), "n": int(ok.sum())}
            s1 = row["stage1_vs_decoder_error"].get("passes", False)
            s2 = row["stage2_vs_monitor_auc"].get("passes", False)
            row["passes_both_stages"] = bool(s1 and s2)
            res.append(row)
        results[P] = res

        print(f"\n  {'candidate':<24}{'vs error':>18}{'vs AUC':>18}   verdict")
        for x in res:
            a, b = x["stage1_vs_decoder_error"], x["stage2_vs_monitor_auc"]
            f = lambda z: ("—" if z.get("rho") is None
                           else f"{z['rho']:+.3f} p={z['p']:.4f}")
            v = ("PASSES BOTH" if x["passes_both_stages"]
                 else "stage 1 only" if a.get("passes")
                 else "stage 2 only" if b.get("passes")
                 else "no")
            print(f"  {x['candidate']:<24}{f(a):>18}{f(b):>18}   {v}")
        print(f"  (Bonferroni threshold p < {ALPHA} within each stage)")

    (OUT / "label_free_result.json").write_text(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
