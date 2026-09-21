#!/usr/bin/env python3
"""
05_check_decoder_stability.py
=============================
Test, from the data alone, whether the decoder was held fixed across sessions.

WHY THIS SCRIPT EXISTS
----------------------
The whole project rests on one claim: that these sessions were run with a
**fixed decoder** -- no recalibration. If the decoder had been retrained partway
through, the drift we want to study would have been partly erased, and any
early-warning analysis would be measuring something different.

The paper asserts fixed decoders in its abstract. That is someone else's word.
This script looks for the signature in the data itself.

THE LOGIC
---------
`cursorVel` is the decoder's own output. `nctx` (+ `spikePower`) are its inputs.
If the decoder is a fixed function, then the input -> output mapping is the same
function in every session.

So: fit a simple linear map from neural features to `cursorVel` separately in
each block, and compare the fitted maps over time.

  * A **recalibration** replaces the decoder's weights. The estimated map would
    change **discontinuously** at that session -- and, since recalibration is
    done to restore performance, performance would jump back up too.
  * A **fixed decoder** with drifting neural signal gives a **smooth** decline
    in similarity, because channels fall silent and contribute less, while the
    underlying function stays the same.

WHAT THIS IS NOT
----------------
This is a **diagnostic, not a proof**, and the limitation is worth stating
plainly:

  * T11's decoder is (per the companion paper, Hosman & Pun) an **LSTM** -- a
    network with internal memory. Its output depends on the recent history of
    inputs, not only the current bin. A memoryless linear fit can therefore only
    approximate it, which is why R-squared here is modest by construction. A low
    R-squared is expected and is not evidence of anything.
  * A recalibration that happened to produce a very similar mapping would be
    hard to see this way.

Absence of a discontinuity is evidence *consistent with* a fixed decoder. It is
not the same as the authors stating it in their Methods. Read the Methods too.

HOW TO RUN
----------
    python3 scripts/05_check_decoder_stability.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"
FIG_DIR = REPO_ROOT / "reports" / "figures"
PROCESSED = REPO_ROOT / "data" / "processed"

SERIES = ["#2a78d6", "#eb6834"]
INK, INK_MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

BLOCK_RE = re.compile(r"^block[_-]?\d+$", re.IGNORECASE)
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)


def style_axes(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=11, color=INK, pad=10, loc="left")
    ax.set_xlabel(xlabel, fontsize=10, color=INK_MUTED)
    ax.set_ylabel(ylabel, fontsize=10, color=INK_MUTED)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def fit_blocks(root: Path) -> pd.DataFrame:
    """Fit a linear neural -> cursorVel map in every main-cohort block."""
    rows = []
    # Only the main cohort: the personal-use blocks have no target task.
    for part_dir in sorted(p for p in root.rglob("*")
                           if p.is_dir() and re.fullmatch(r"T\d+", p.name)):
        part = part_dir.name.upper()
        days = sorted((d for d in part_dir.iterdir()
                       if d.is_dir() and DAY_RE.match(d.name)),
                      key=lambda p: int(DAY_RE.match(p.name).group(1)))
        for day_dir in days:
            day = int(DAY_RE.match(day_dir.name).group(1))
            for blk in sorted(b for b in day_dir.iterdir()
                              if b.is_dir() and BLOCK_RE.match(b.name)):
                d = sio.loadmat(blk / "data.mat", squeeze_me=True,
                                struct_as_record=False)
                if "nctx" not in d or "cursorVel" not in d:
                    continue
                X = np.asarray(d["nctx"], dtype=np.float64)
                if "spikePower" in d:
                    X = np.hstack([X, np.asarray(d["spikePower"], dtype=np.float64)])
                Y = np.asarray(d["cursorVel"], dtype=np.float64)

                # z-score each feature within the block, so channels with very
                # different scales are comparable. Channels with zero variance
                # (silent) get sd=1, which drives their fitted weight to ~0 --
                # exactly the behaviour we want when a channel dies.
                mu, sd = X.mean(0), X.std(0)
                sd[sd == 0] = 1.0
                Xz = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])

                W, *_ = np.linalg.lstsq(Xz, Y, rcond=None)
                pred = Xz @ W
                ss_tot = ((Y - Y.mean(0)) ** 2).sum(0)
                r2 = float((1 - ((Y - pred) ** 2).sum(0) / ss_tot).mean())

                rows.append({"participant": part, "trial_day": day,
                             "block": blk.name, "n_bins": len(X),
                             "r2": r2, "weights": W[:-1].ravel()})
                print(f"    {part} day_{day} {blk.name}: R2={r2:.3f}")
    return pd.DataFrame(rows)


def similarity_to_first(df: pd.DataFrame) -> pd.DataFrame:
    """Cosine similarity of each session's fitted map to the first session's."""
    out = []
    for part, sub in df.groupby("participant"):
        first_day = sub["trial_day"].min()
        ref = np.mean(np.stack(sub.loc[sub.trial_day == first_day, "weights"]), axis=0)
        for day, g in sub.groupby("trial_day"):
            w = np.mean(np.stack(g["weights"]), axis=0)
            cos = float(w @ ref / (np.linalg.norm(w) * np.linalg.norm(ref)))
            out.append({"participant": part, "trial_day": day,
                        "cosine_to_first_session": cos,
                        "mean_r2": float(g["r2"].mean()),
                        "n_blocks": len(g)})
    return pd.DataFrame(out)


def make_figure(sim: pd.DataFrame) -> Path:
    parts = sorted(sim["participant"].unique())
    colors = {p: SERIES[i % len(SERIES)] for i, p in enumerate(parts)}
    fig, axes = plt.subplots(1, len(parts), figsize=(6.2 * len(parts), 4.2),
                             squeeze=False)
    for ax, p in zip(axes[0], parts):
        s = sim[sim.participant == p].sort_values("trial_day")
        ax.plot(s["trial_day"], s["cosine_to_first_session"], color=colors[p],
                linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1)
        ax.set_ylim(0, 1.05)
        style_axes(ax, f"{p} — estimated decoder map vs first session",
                   "Trial day", "Cosine similarity")
    fig.suptitle("Is the decoder fixed?  A recalibration would show as a JUMP "
                 "back toward 1.0 — a smooth decline is what a fixed decoder "
                 "with drifting signal looks like",
                 fontsize=11, color=INK, x=0.02, ha="left", y=1.06)
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "07_decoder_stability.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()

    print("Fitting a linear neural -> cursorVel map per block ...")
    df = fit_blocks(args.root)
    if df.empty:
        print("No blocks found.", file=sys.stderr)
        return 1

    sim = similarity_to_first(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    sim.to_csv(PROCESSED / "decoder_stability.csv", index=False)

    print("\n" + "=" * 72)
    print("SIMILARITY OF THE ESTIMATED DECODER MAP TO THE FIRST SESSION")
    print("=" * 72)
    for p, g in sim.groupby("participant"):
        print(f"\n{p}:")
        print(g.sort_values("trial_day")[
            ["trial_day", "cosine_to_first_session", "mean_r2", "n_blocks"]
        ].to_string(index=False))
        c = g.sort_values("trial_day")["cosine_to_first_session"].values
        jumps = np.diff(c)
        biggest_up = jumps.max() if len(jumps) else 0.0
        print(f"  largest single-session INCREASE in similarity: {biggest_up:+.3f}")
        print("  (a recalibration would show as a large jump back toward 1.0)")

    path = make_figure(sim)
    print(f"\nWrote {path.relative_to(REPO_ROOT)}")
    print(f"Wrote {(PROCESSED / 'decoder_stability.csv').relative_to(REPO_ROOT)}")
    print("\nREMINDER: this is a diagnostic consistent with a fixed decoder, "
          "not a substitute\nfor reading the paper's Methods.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
