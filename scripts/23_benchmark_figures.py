#!/usr/bin/env python3
"""
Benchmark figures: the two conditions side by side.

The whole story is one comparison. A monitor calibrated once at install and left
alone, versus the same monitor holding a recent notion of normal. Three panels
share a detector axis so the reader tracks one detector across all three
questions rather than re-orienting each time.

Deliberately NOT here:
  * a dual-axis chart pairing lead time against false alarms -- they have
    different units and different signs of "good", and overlaying them on two
    scales is the single most misleading thing this data could be made to do.
  * a single "score" combining the two. A detector that warns instantly on
    everything has infinite lead time and is useless; the tradeoff is the
    finding, so it stays visible as two panels.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
FIGS = REPO / "reports" / "figures"

# Two conditions, two hues. Validated (CVD dE 24.7 protan, 33.6 normal).
C_GLOBAL = "#2a78d6"
C_LOCAL = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dcdcd8"
SURFACE = "#fcfcfb"
BAD = "#b3261e"

NICE = {"decoder_guard": "decoder-guard", "mean_activity": "mean activity",
        "robust_dispersion": "robust dispersion", "distribution_shift": "distribution shift"}


def load(sfx: str) -> dict:
    p = OUT / f"harness_summary{sfx}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def panel(ax, dets, gv, lv, title, ylabel, ref=None, ref_label=None, log=False):
    x = np.arange(len(dets))
    w = 0.36
    for off, vals, colour, lab in ((-w / 2, gv, C_GLOBAL, "calibrate once"),
                                   (w / 2, lv, C_LOCAL, "recent normal")):
        v = [np.nan if q is None else q for q in vals]
        ax.bar(x + off, v, w * 0.92, color=colour, label=lab,
               edgecolor=SURFACE, linewidth=2, zorder=3)
        for xi, q in zip(x + off, v):
            if np.isnan(q):
                ax.text(xi, 0, "none", ha="center", va="bottom", fontsize=7.5,
                        color=BAD, rotation=90, zorder=4)
    if ref is not None:
        ax.axhline(ref, color=BAD, lw=1.4, ls=(0, (4, 3)), zorder=2)
        ax.text(len(dets) - 0.45, ref, f" {ref_label}", color=BAD, fontsize=8,
                va="bottom", ha="right")
    if log:
        ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([NICE.get(d, d) for d in dets], fontsize=8.5, color=INK2)
    ax.set_title(title, fontsize=10.5, color=INK, pad=8, loc="left")
    ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8.5)


def main() -> int:
    g, l = load(""), load("_local")
    if not g or not l:
        raise SystemExit("need both harness_summary.json and harness_summary_local.json")

    dets = [d for d in ("decoder_guard", "mean_activity", "robust_dispersion",
                        "distribution_shift") if d in g or d in l]

    def get(src, d, key, default=None):
        return src.get(d, {}).get(key, default)

    def gate(src, d, gk):
        gv = src.get(d, {}).get("gates", {}).get(gk)
        return None if gv is None else (gv.get("fraction_significant")
                                        or gv.get("fraction_significant_after_detrend"))

    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.1), facecolor=SURFACE)
    fig.patch.set_facecolor(SURFACE)
    for a in axes:
        a.set_facecolor(SURFACE)

    panel(axes[0], dets,
          [get(g, d, "median_lead_s") for d in dets],
          [get(l, d, "median_lead_s") for d in dets],
          "Median lead time", "seconds  (positive = warned first)", ref=0,
          ref_label="warning arrives too late below this line")

    panel(axes[1], dets,
          [get(g, d, "false_alarms_per_hour") for d in dets],
          [get(l, d, "false_alarms_per_hour") for d in dets],
          "False alarms", "per hour of healthy record", ref=0.1,
          ref_label="budget", log=True)

    panel(axes[2], dets,
          [gate(g, d, "G1_silence") for d in dets],
          [gate(l, d, "G1_silence") for d in dets],
          "Silence gate", "fraction of healthy episodes that trend", ref=0.10,
          ref_label="pass below")

    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper right", frameon=False, fontsize=9,
               ncol=2, bbox_to_anchor=(0.99, 1.005))
    fig.suptitle("Calibrate once, or hold a recent normal?", x=0.008, y=0.99,
                 ha="left", fontsize=13.5, color=INK, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    out = FIGS / "12_baseline_conditions.png"
    fig.savefig(out, dpi=165, facecolor=SURFACE)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
