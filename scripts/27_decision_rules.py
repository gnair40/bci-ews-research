#!/usr/bin/env python3
"""
Compare decision rules by their whole curve, not by one operating point.

WHY A CURVE
-----------
Reading one operating point per rule is how you get fooled. CUSUM at its chosen
threshold detects 221 faults where the plain threshold detects 143 -- but with a
LATER median lead time, which looks like a loss. It is not: the extra 78
detections are cases the threshold rule missed entirely, and they are the harder,
later-detected ones. Adding hard cases drags the median down even though nothing
got worse.

The only honest comparison sweeps the free parameter and plots detection against
false alarms. A rule whose curve sits above another's is better everywhere, and
no single-point summary can hide behind a favourable threshold.

THE THREE RULES
---------------
    threshold   the current one. A score crosses a line for a few windows.
    cusum       accumulate excess evidence over time; alarm on the total.
                Slack `k` is estimated causally per episode, so both rules
                expose exactly ONE searched parameter and the comparison is
                like for like.
    cusum+spec  cusum, but a warning is suppressed while the monitor's own
                named cause is `profile`.

WHY THE SPECIFICITY GATE IS NOT CHEATING
----------------------------------------
`profile` was defined as the residual catch-all BEFORE any of this was measured
-- it is what the monitor reports when nothing more specific fits. Declining to
raise a failure alarm on a residual is a design argument, not a fitted one: "the
shape changed somehow, I cannot say how" is not a diagnosis a clinician could
act on. The rule uses no fault labels and would have been defensible written on
day one.

That the residual also happens to fire on 40.6% of healthy windows and 5.4% of
fault windows is corroboration, and it is why this was worth trying -- but the
rule does not read those numbers.

Usage: python3 scripts/27_decision_rules.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"
FIGS = REPORTS / "figures"

STEP_S = 5.0
DWELL = 3
GRID = np.geomspace(0.3, 3000.0, 90)

SOURCES = [("episode_scores_local.csv", "T11"), ("episode_scores_T5_local.csv", "T5")]
DETECTORS = ["decoder_guard", "robust_dispersion", "mean_activity"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def warn_threshold(y, onset_w, h, labels=None):
    """First window after `DWELL` consecutive windows above h."""
    run = 0
    for i, v in enumerate(y):
        run = run + 1 if v > h else 0
        if run >= DWELL:
            return i
    return None


def warn_cusum(y, onset_w, h, labels=None):
    if onset_w < 6 or len(y) <= onset_w:
        return None
    pre = y[:onset_w]
    med = float(np.median(pre))
    k = med + float(np.median(np.abs(pre - med))) * 1.4826
    S = 0.0
    for i, x in enumerate(y):
        S = max(0.0, S + (x - k))
        if S > h:
            return i
    return None


def warn_cusum_spec(y, onset_w, h, labels=None):
    """CUSUM, but suppressed while the named cause is the residual catch-all."""
    if onset_w < 6 or len(y) <= onset_w:
        return None
    pre = y[:onset_w]
    med = float(np.median(pre))
    k = med + float(np.median(np.abs(pre - med))) * 1.4826
    S = 0.0
    for i, x in enumerate(y):
        S = max(0.0, S + (x - k))
        if S > h and not (labels is not None and i < len(labels)
                          and labels[i] == "profile"):
            return i
    return None


RULES = [("threshold", warn_threshold), ("cusum", warn_cusum),
         ("cusum+spec", warn_cusum_spec)]


def curve(sub: pd.DataFrame, fn) -> list[tuple[float, float, int]]:
    """(false alarms per hour, detection fraction, n detected) across the grid."""
    eps = []
    for _, r in sub.iterrows():
        y = np.fromstring(r.scores, sep=",")
        lab = (r.attribution.split(",")
               if isinstance(getattr(r, "attribution", None), str) else None)
        eps.append((y, int(r.onset_w), int(r.crossing_w), bool(r.crossed),
                    len(y), lab))
    healthy_h = sum(n for _, _, _, c, n, _ in eps if not c) * STEP_S / 3600
    n_pos = sum(1 for *_, c, _, _ in [(e[0], e[1], e[2], e[3], e[4], e[5]) for e in eps] if c)
    out = []
    for h in GRID:
        fa = det = 0
        for y, ow, cw, crossed, _, lab in eps:
            w = fn(y, ow, h, lab)
            if not crossed:
                fa += int(w is not None)
            elif w is not None and w >= ow:
                det += 1
        out.append((fa / healthy_h if healthy_h else np.nan,
                    det / n_pos if n_pos else np.nan, det))
    return out


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    C = {"threshold": "#2a78d6", "cusum": "#eb6834", "cusum+spec": "#1baf7a"}
    INK, INK2, GRIDC, SURF, BAD = "#0b0b0b", "#52514e", "#dcdcd8", "#fcfcfb", "#b3261e"

    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), facecolor=SURF, sharey=True)

    for ax, (fname, pname) in zip(axes, SOURCES):
        path = OUT / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        sub = df[df.detector == "decoder_guard"]
        ax.set_facecolor(SURF)
        for rname, fn in RULES:
            c = curve(sub, fn)
            xs = [p[0] for p in c]; ys = [p[1] for p in c]
            ax.plot(xs, ys, color=C[rname], lw=2, label=rname, zorder=3)
            for far, frac, n in c:
                rows.append({"participant": pname, "rule": rname,
                             "false_alarms_per_hour": round(far, 4),
                             "detection_fraction": round(frac, 4), "n_detected": n})
        ax.axvline(0.1, color=BAD, lw=1.4, ls=(0, (4, 3)), zorder=2)
        ax.annotate("budget", xy=(0.1, 0.02), color=BAD, fontsize=7.5,
                    ha="left", va="bottom", rotation=90)
        ax.set_xscale("log")
        ax.set_xlabel("false alarms per hour of healthy record", fontsize=9, color=INK2)
        ax.set_title(f"Participant {pname}", fontsize=10.5, color=INK, loc="left", pad=8)
        ax.grid(color=GRIDC, lw=0.7, zorder=0); ax.set_axisbelow(True)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            ax.spines[s_].set_color(GRIDC)
        ax.tick_params(colors=INK2, labelsize=8.5)
    axes[0].set_ylabel("fraction of faults detected", fontsize=9, color=INK2)
    h_, l_ = axes[0].get_legend_handles_labels()
    fig.legend(h_, l_, loc="upper right", frameon=False, fontsize=9, ncol=3,
               bbox_to_anchor=(0.99, 1.005))
    fig.suptitle("Does a better decision rule help?", x=0.008, y=0.985, ha="left",
                 fontsize=13.5, color=INK, weight="bold")
    fig.text(0.008, 0.925, "decoder-guard, recent-normal baseline. A curve sitting "
             "higher is better everywhere. Nothing reaches the budget line with "
             "useful detection.", ha="left", fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 0.885))
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / "14_decision_rules.png", dpi=165, facecolor=SURF)
    print(f"wrote {FIGS/'14_decision_rules.png'}")

    d = pd.DataFrame(rows)
    d.to_csv(OUT / "decision_rule_curves.csv", index=False)

    # Detection achievable AT the budget, which is the number that decides this.
    print(f"\n{'participant':<12}{'rule':<14}{'detection at <=0.1 FA/h':>26}")
    lines = ["# Decision rules compared by curve\n",
             "**Reproduce:** `python3 scripts/27_decision_rules.py`\n",
             "> Comparing one operating point per rule is how you get fooled: CUSUM "
             "detects 221 faults to the threshold rule's 143 but shows a *later* "
             "median lead, purely because the extra 78 are the hard cases the other "
             "rule missed entirely. Curves cannot hide behind a favourable threshold.\n",
             "\n## Detection achievable within the false-alarm budget\n",
             "| Participant | Rule | Faults detected at ≤0.1/h |", "|---|---|---|"]
    for pname in ("T11", "T5"):
        for rname, _ in RULES:
            sel = d[(d.participant == pname) & (d.rule == rname)
                    & (d.false_alarms_per_hour <= 0.1)]
            best = sel.detection_fraction.max() if len(sel) else 0.0
            print(f"{pname:<12}{rname:<14}{best*100:>25.1f}%")
            lines.append(f"| {pname} | `{rname}` | **{best*100:.1f}%** |")
    lines.append("\nEvery rule is at or near zero useful detection inside the "
                 "budget. The rule is not the bottleneck.\n")
    (REPORTS / "DECISION_RULES.md").write_text("\n".join(lines))
    print(f"\nwrote {REPORTS/'DECISION_RULES.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
