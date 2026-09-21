#!/usr/bin/env python3
"""
09_reproduce_mindful.py
=======================
Reproduce the published MINDFUL result (Pun et al. 2024, Fig. 1b) from the raw
deposit, as an end-to-end check that our pipeline is correct.

WHY REPRODUCE SOMEONE ELSE'S RESULT
-----------------------------------
Every step so far -- reading the .mat files, mapping trials onto bins, choosing
the indexing convention, assembling neural features -- could contain a quiet
error that produces plausible-looking output. The most powerful way to check a
pipeline is to run it on a question whose answer has already been published and
see whether the number comes back.

The target is the paper's Fig. 1b. It reports the relationship between neural
instability (a Kullback-Leibler divergence) and cursor-control performance
(angle error):

    T11: Pearson r = 0.985
    T5 : Pearson r = 0.983

If our independent implementation lands near those, the pipeline is sound and
the project can build on it. If it does not, something upstream is wrong and
must be found before any new analysis is trusted.

WHAT KL DIVERGENCE IS, IN PLAIN LANGUAGE
----------------------------------------
A number measuring how different two probability distributions are. Zero means
identical. Here, one distribution is the neural activity during periods of known
GOOD control (the reference), and the other is neural activity during some other
period. A large value means the neural activity has moved away from where it was
when control was good.

THE PROCEDURE (following the authors' MATLAB code exactly)
----------------------------------------------------------
1. For each block, z-score every neural feature using a TRAILING 180-second
   rolling window (their `BGzscoreNew`, avgWin_s = 180, winFs = 50 Hz,
   trailingMoving = true). "Trailing" means each time point is normalised using
   only the preceding 3 minutes -- causal, so it could run online.
2. Pool all bins whose instantaneous angle error is below 4 degrees. These are
   the moments of best control, and they form the REFERENCE.
3. Fit a PCA on the reference bins and keep the top 5 components (their
   `pcaDim = 5`). This reduces 384 (or 192) features to 5 numbers per bin.
4. Group every bin by its angle error into 4-degree bands from 0 to 180.
5. For each band, estimate a Gaussian and compute its KL divergence from the
   reference Gaussian.
6. Correlate band KL divergence against band mean angle error.

TWO IMPLEMENTATION DETAILS THAT ARE EASY TO GET WRONG
-----------------------------------------------------
* Their `ProbDistributionEst` uses `sigma = X' * X / n` -- the UNCENTERED second
  moment matrix, not the covariance. It does not subtract the mean. Using a
  covariance instead gives different numbers.
* `CalcKL(pd1, pd2)` treats pd2 as the reference in the denominator, and
  Fig. 1b calls it as `CalcDistance(ref_pd, pd)`, i.e. KL(reference || target).

HOW TO RUN
----------
    python3 scripts/09_reproduce_mindful.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.stats import pearsonr, spearmanr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"
FIG_DIR = REPO_ROOT / "reports" / "figures"
PROCESSED = REPO_ROOT / "data" / "processed"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)

ZSCORE_WIN_BINS = 180 * 50      # 180 s at 50 Hz = 9000 bins
PCA_DIM = 5
REF_AE_MAX = 4.0                # degrees; "good control"
AE_BAND = 4.0                   # degrees per band

# Published values we are trying to match (Pun et al. 2024, Fig. 1b).
PUBLISHED = {"T11": 0.985, "T5": 0.983}

C = {"T11": "#2a78d6", "T5": "#eb6834"}
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"


# ---------------------------------------------------------------------------
# STEP 1 — trailing rolling z-score
# ---------------------------------------------------------------------------

def trailing_zscore(X: np.ndarray, win: int) -> np.ndarray:
    """
    Z-score each column using a TRAILING moving mean and standard deviation.

    Each time point is normalised using only the `win` samples up to and
    including itself -- never the future. That causality matters: the original
    was applied online during cursor control, so it could not look ahead.

    Implemented with cumulative sums so the whole series is done in a few array
    operations rather than a Python loop over time points. Computed in float64
    because cumulative sums over hundreds of thousands of values lose precision
    badly in float32.
    """
    X = np.asarray(X, dtype=np.float64)
    n, d = X.shape
    c1 = np.vstack([np.zeros((1, d)), np.cumsum(X, axis=0)])
    c2 = np.vstack([np.zeros((1, d)), np.cumsum(X * X, axis=0)])
    idx = np.arange(1, n + 1)
    lo = np.maximum(idx - win, 0)
    cnt = (idx - lo).reshape(-1, 1)
    s1 = c1[idx] - c1[lo]
    s2 = c2[idx] - c2[lo]
    mean = s1 / cnt
    var = np.maximum(s2 / cnt - mean ** 2, 0.0)
    sd = np.sqrt(var)
    sd[sd < 1e-12] = 1.0                     # silent channels: leave at zero
    return (X - mean) / sd


# ---------------------------------------------------------------------------
# STEP 5 — the authors' Gaussian estimate and KL divergence
# ---------------------------------------------------------------------------

def prob_distribution_est(X: np.ndarray) -> dict | None:
    """
    Port of the authors' `ProbDistributionEst`.

    NOTE the uncentered second moment: sigma = X' X / n, with no mean
    subtraction. This is what their code does, so it is what we do -- matching
    an existing result means matching its conventions, not improving on them.
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2 or len(X) <= X.shape[1]:
        return None
    n, p = X.shape
    mu = X.mean(axis=0)
    sigma = (X.T @ X) / n
    s = np.linalg.svd(sigma, compute_uv=False)
    if np.any(s <= 0):
        return None
    return {"n": n, "p": p, "mu": mu, "sigma": sigma,
            "logdetsigma": float(np.sum(np.log(s)))}


def calc_kl(pd1: dict, pd2: dict) -> float:
    """
    Port of the authors' `CalcKL(pd1, pd2)` for multivariate Gaussians.

    pd2 plays the role of the denominator distribution. Fig. 1b calls this as
    CalcDistance(ref_pd, pd), i.e. KL(reference || target).
    """
    if pd1 is None or pd2 is None:
        return np.nan
    try:
        inv2 = np.linalg.inv(pd2["sigma"])
    except np.linalg.LinAlgError:
        return np.nan
    diff = pd2["mu"] - pd1["mu"]
    term1 = float(np.trace(inv2 @ pd1["sigma"]))
    term2 = float(diff @ inv2 @ diff)
    term3 = pd2["logdetsigma"] - pd1["logdetsigma"]
    return 0.5 * (term1 + term2 - pd1["p"] + term3)


# ---------------------------------------------------------------------------
# DATA ACCESS
# ---------------------------------------------------------------------------

def main_blocks(root: Path, participant: str) -> list[Path]:
    out = []
    for part_dir in sorted(p for p in root.rglob("*")
                           if p.is_dir() and p.name.upper() == participant):
        days = sorted((d for d in part_dir.iterdir()
                       if d.is_dir() and DAY_RE.match(d.name)),
                      key=lambda q: int(DAY_RE.match(q.name).group(1)))
        for day_dir in days:
            out.extend(sorted(b for b in day_dir.iterdir()
                              if b.is_dir() and BLOCK_RE.match(b.name)))
    return out


def block_features(blk: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (z-scored features, per-bin angle error) for one block."""
    data = sio.loadmat(blk / "data.mat", squeeze_me=True, struct_as_record=False)
    info = sio.loadmat(blk / "info.mat", squeeze_me=True, struct_as_record=False)
    X = np.asarray(data["nctx"], dtype=np.float64)
    if "spikePower" in data:
        X = np.hstack([X, np.asarray(data["spikePower"], dtype=np.float64)])
    ae = np.asarray(info["angleError"], dtype=np.float64) if "angleError" in info \
        else np.full(len(X), np.nan)
    return trailing_zscore(X, ZSCORE_WIN_BINS), ae


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run_participant(root: Path, part: str) -> dict:
    blocks = main_blocks(root, part)
    if not blocks:
        return {}
    print(f"\n{part}: {len(blocks)} blocks")

    # ---- pass 1: collect reference bins (good control) to fit the PCA ------
    print("  pass 1/2 — collecting reference bins (angle error < 4 deg) ...")
    ref_chunks = []
    for blk in blocks:
        Z, ae = block_features(blk)
        m = np.isfinite(ae) & (ae < REF_AE_MAX)
        if m.any():
            ref_chunks.append(Z[m].astype(np.float32))
    ref = np.vstack(ref_chunks).astype(np.float64)
    del ref_chunks
    print(f"    {len(ref):,} reference bins, {ref.shape[1]} features")

    # PCA fitted on the reference only (MATLAB `pca` centres the data).
    mu = ref.mean(axis=0)
    _, _, vt = np.linalg.svd(ref - mu, full_matrices=False)
    coeff = vt[:PCA_DIM].T
    del ref

    # ---- pass 2: project every bin into the 5-D space ---------------------
    print("  pass 2/2 — projecting all bins into the 5-D reference space ...")
    proj_chunks, ae_chunks = [], []
    for blk in blocks:
        Z, ae = block_features(blk)
        proj_chunks.append(((Z - mu) @ coeff).astype(np.float32))
        ae_chunks.append(ae.astype(np.float32))
    P = np.vstack(proj_chunks).astype(np.float64)
    AE = np.concatenate(ae_chunks)
    del proj_chunks, ae_chunks
    print(f"    {len(P):,} bins projected")

    ref_mask = np.isfinite(AE) & (AE < REF_AE_MAX)
    ref_pd = prob_distribution_est(P[ref_mask])

    # ---- group by angle error and compute KL ------------------------------
    edges = np.arange(0, 180, AE_BAND)
    rows = []
    for lo in edges:
        hi = lo + AE_BAND
        m = np.isfinite(AE) & (AE >= lo) & (AE < hi)
        if m.sum() < PCA_DIM + 2:
            continue
        kl = calc_kl(ref_pd, prob_distribution_est(P[m]))
        rows.append({"ae_lo": lo, "ae_hi": hi, "mean_ae": float(AE[m].mean()),
                     "n_bins": int(m.sum()), "kld": kl})
    df = pd.DataFrame(rows).dropna(subset=["kld"])

    r, rp = pearsonr(df["mean_ae"], df["kld"])
    rho, sp = spearmanr(df["mean_ae"], df["kld"])
    print(f"    {len(df)} angle-error bands")
    print(f"    Pearson  r = {r:.3f}  (published {PUBLISHED[part]:.3f})")
    print(f"    Spearman rho = {rho:.3f}")
    return {"participant": part, "table": df, "pearson_r": float(r),
            "pearson_p": float(rp), "spearman_rho": float(rho),
            "spearman_p": float(sp), "n_ref_bins": int(ref_mask.sum()),
            "n_bins": int(len(P))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--participants", nargs="+", default=["T11", "T5"])
    args = ap.parse_args()

    print("=" * 74)
    print("REPRODUCING THE PUBLISHED MINDFUL RESULT (Pun et al. 2024, Fig. 1b)")
    print("=" * 74)
    print("Target: Pearson r = 0.985 (T11), 0.983 (T5)")

    results = [r for r in (run_participant(args.root, p)
                           for p in args.participants) if r]
    if not results:
        print("No data found.", file=sys.stderr)
        return 1

    print("\n" + "=" * 74)
    print("COMPARISON WITH THE PUBLISHED VALUES")
    print("=" * 74)
    ok = True
    for r in results:
        pub = PUBLISHED[r["participant"]]
        diff = abs(r["pearson_r"] - pub)
        verdict = "MATCH" if diff < 0.05 else ("close" if diff < 0.15 else "MISMATCH")
        if diff >= 0.15:
            ok = False
        print(f"  {r['participant']:<4s} ours r = {r['pearson_r']:.3f} | "
              f"published {pub:.3f} | difference {diff:.3f}  -> {verdict}")
    print("\n" + ("Pipeline reproduces the published relationship."
                  if ok else
                  "Pipeline does NOT reproduce the published relationship.\n"
                  "Something upstream needs investigating before building on it."))

    # ---- figure ----------------------------------------------------------
    fig, axes = plt.subplots(1, len(results), figsize=(5.6 * len(results), 4.4),
                             squeeze=False)
    for ax, r in zip(axes[0], results):
        d, p = r["table"], r["participant"]
        ax.scatter(d["mean_ae"], d["kld"], s=34, color=C.get(p, "#2a78d6"),
                   edgecolor="white", linewidth=0.8, zorder=3)
        b = np.polyfit(d["mean_ae"], d["kld"], 1)
        xs = np.linspace(0, 180, 20)
        ax.plot(xs, np.polyval(b, xs), "--", color=INK, linewidth=1.5)
        ax.set_title(f"{p} — ours r = {r['pearson_r']:.3f}   "
                     f"(published {PUBLISHED[p]:.3f})",
                     fontsize=11, color=INK, loc="left", pad=8)
        ax.set_xlabel("Angle error (degrees)", fontsize=10, color=INK_MUTED)
        ax.set_ylabel("KL divergence from good-control reference",
                      fontsize=10, color=INK_MUTED)
        ax.set_xticks([0, 45, 90, 135, 180])
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK_MUTED, labelsize=9)
    fig.suptitle("Neural instability against cursor-control performance — "
                 "independent reproduction of Pun et al. (2024) Fig. 1b",
                 fontsize=11.5, color=INK, x=0.01, ha="left", y=1.04)
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "10_mindful_reproduction.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\nWrote {out.relative_to(REPO_ROOT)}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.concat([r["table"].assign(participant=r["participant"]) for r in results]
              ).to_csv(PROCESSED / "mindful_kld_vs_ae.csv", index=False)
    pd.DataFrame([{k: v for k, v in r.items() if k != "table"} for r in results]
                 ).to_csv(PROCESSED / "mindful_reproduction_summary.csv", index=False)
    print("Wrote mindful_kld_vs_ae.csv and mindful_reproduction_summary.csv")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
