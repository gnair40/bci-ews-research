#!/usr/bin/env python3
"""
Report the calibration-efficiency curves.

Reads the four CSVs written by 39_calibration_curve.py and produces the figure
and the numbers quoted in reports/CALIBRATION_CURVE.md. Also recomputes the
conditioning diagnostic that decides whether the n=10 grid point is
interpretable, so the exclusion is evidenced rather than asserted.

Usage: python3 scripts/40_calibration_report.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
FIG = REPO / "reports" / "figures"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def conditioning(participant: str) -> pd.DataFrame:
    """Condition number of the profile-subspace covariance vs fit size.

    K = 10, so a fit of n windows gives a rank-min(n-1, 10) covariance. Below
    n = K + 1 the matrix is singular and only the 1e-6 ridge makes it
    invertible -- the resulting Mahalanobis distance is not a measurement.
    """
    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    rd = _load("rd", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    _, mp = rd.decoder_paths(participant)
    meta = json.loads(mp.read_text())
    ds = loader.load_dataset(participant=participant, load_neural=True, verbose=False)
    H = []
    for b in meta["train_blocks"]:
        if b not in ds.neural:
            continue
        X = ds.neural[b]
        st = np.arange(0, X.shape[0] - 1500 + 1, 250)
        H.append(det.window_features(X, st, 1500))
    H = np.vstack(H)

    rng = np.random.default_rng(20260902)
    rows = []
    for n in [10, 20, 40, 80, 160, len(H)]:
        Hs = H if n == len(H) else H[rng.choice(len(H), n, replace=False)]
        g = guard.DecoderGuard().fit(Hs)
        ev = np.linalg.eigvalsh(np.linalg.inv(g.Si))
        rows.append({"participant": participant, "n_windows": n,
                     "min_eigenvalue": float(ev[0]), "max_eigenvalue": float(ev[-1]),
                     "condition_number": float(ev[-1] / max(ev[0], 1e-30)),
                     "singular": bool(ev[0] <= 1e-5)})
    return pd.DataFrame(rows)


def main() -> int:
    curves = {}
    for p, sfx in [("T11", ""), ("T5", "_T5")]:
        for draw in ["scattered", "contiguous"]:
            f = OUT / f"calibration_curve{sfx}{'' if draw=='scattered' else '_contiguous'}.csv"
            curves[(p, draw)] = pd.read_csv(f)

    cond = pd.concat([conditioning("T11"), conditioning("T5")], ignore_index=True)
    cond.to_csv(OUT / "calibration_conditioning.csv", index=False)
    bad = sorted(set(cond.loc[cond.singular, "n_windows"]))
    print("singular fit sizes:", bad)

    FIG.mkdir(parents=True, exist_ok=True)
    # Two rows on purpose. Auto-scaling alone turns a 0.006 AUC change into a
    # dramatic slope; the top row on a fixed 0.5-0.8 axis is what the curve
    # actually looks like, and the bottom row is the zoom, labelled as such.
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.4))
    for col, p_ in enumerate(["T11", "T5"]):
        for row in (0, 1):
            ax = axes[row][col]
            for draw, style in [("scattered", "-o"), ("contiguous", "--s")]:
                d = curves[(p_, draw)]
                d = d[d.draw == draw]
                ax.errorbar(d.n_windows, d.auc_mean, yerr=d.auc_sd, fmt=style,
                            capsize=3, label=f"{draw} draw")
            pooled = curves[(p_, "scattered")]
            pooled = pooled[pooled.draw == "all-pooled"]
            ax.plot(pooled.n_windows, pooled.auc_mean, "k*", ms=13,
                    label="all healthy windows")
            for n in bad:
                ax.axvspan(n * 0.87, n * 1.15, color="0.85", zorder=0)
            ax.set_xscale("log")
            ax.grid(alpha=0.3)
            ax.set_ylabel("session-level AUC")
            if row == 0:
                ax.set_ylim(0.5, 0.8)
                ax.axhline(0.5, color="r", lw=1, ls=":")
                ax.set_title(f"{p_} — true scale (0.5 = chance)", fontsize=10)
                ax.legend(fontsize=8, loc="lower right")
            else:
                ax.set_title(f"{p_} — zoomed; note the axis range", fontsize=10)
                ax.set_xlabel("healthy windows used for the global fit")
    fig.suptitle("How much healthy recording does commissioning need?\n"
                 "grey band = fit is singular (n <= K = 10), not interpretable",
                 fontsize=12)
    fig.tight_layout()
    out = FIG / "14_calibration_curve.png"
    fig.savefig(out, dpi=150)
    print("wrote", out)

    # numbers quoted in the report, recomputed rather than typed by hand
    summary = {}
    for p in ["T11", "T5"]:
        s = curves[(p, "scattered")]
        c = curves[(p, "contiguous")]
        usable = s[(s.n_windows >= 20) & (s.draw == "scattered")]
        summary[p] = {
            "auc_at_20_scattered": float(s.loc[s.n_windows == 20, "auc_mean"].iloc[0]),
            "auc_at_20_contiguous": float(c.loc[c.n_windows == 20, "auc_mean"].iloc[0]),
            "auc_pooled": float(s.loc[s.draw == "all-pooled", "auc_mean"].iloc[0]),
            "range_from_20_up": float(usable.auc_mean.max() - usable.auc_mean.min()),
        }
        summary[p]["gain_from_20_to_all"] = round(
            summary[p]["auc_pooled"] - summary[p]["auc_at_20_scattered"], 4)
    (OUT / "calibration_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
