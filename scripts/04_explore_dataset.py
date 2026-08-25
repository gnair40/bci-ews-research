#!/usr/bin/env python3
"""
04_explore_dataset.py
=====================
Basic exploratory analysis, and generate reports/DATASET_EXPLORATION.md.

WHAT THIS SCRIPT IS FOR
-----------------------
"Exploratory" analysis means describing what is in the data -- counts,
distributions, missing values, ranges -- BEFORE testing any hypothesis. It
answers "what do I actually have?", not "is my idea right?".

That order matters. If you compute a hypothesis test first and a descriptive
statistic second, you have no way of knowing whether the test was meaningful.
Descriptives can invalidate an analysis plan before you waste a month on it.

This script deliberately does NOT:
  * test any hypothesis
  * compute early-warning-signal indicators (variance, AR(1), Kendall's tau)
  * claim that anything is or is not testable

It produces numbers and figures. **Interpretation is left to you.** The report
it writes marks every interpretive section as needing your judgement rather
than filling one in.

WHAT IT PRODUCES
----------------
  reports/DATASET_EXPLORATION.md   the write-up, with computed facts filled in
  reports/figures/*.png            five figures
  data/processed/trials.csv        tidy trial table
  data/processed/blocks.csv        tidy block table

HOW TO RUN
----------
    python3 scripts/04_explore_dataset.py
    python3 scripts/04_explore_dataset.py --root data/raw
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")            # render to files, not to a screen
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "reports"
FIG_DIR = REPORT_DIR / "figures"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# Categorical colours, validated colourblind-safe for this pair
# (protan Delta E 24.7, tritan 32.7, normal-vision 33.6; all >= their floors).
# Assigned to participants in fixed order -- never cycled, so a participant
# keeps its colour across every figure.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e6e5e1"


def load_loader():
    """Import 03_load_dataset.py (its name starts with a digit, so needs this)."""
    path = Path(__file__).resolve().parent / "03_load_dataset.py"
    spec = importlib.util.spec_from_file_location("loader", path)
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE executing: @dataclass resolves its annotations by looking
    # the module up in sys.modules, and fails if it is not there yet.
    sys.modules["loader"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# PLOT STYLING
# ---------------------------------------------------------------------------

def style_axes(ax, title: str, xlabel: str, ylabel: str):
    """
    Apply a consistent, recessive style.

    'Recessive' means the grid and axes are quiet so the data stand out. Heavy
    gridlines and boxes compete with the marks for attention; the data should
    always win.
    """
    ax.set_title(title, fontsize=12, color=INK, pad=12, loc="left")
    ax.set_xlabel(xlabel, fontsize=10, color=INK_MUTED)
    ax.set_ylabel(ylabel, fontsize=10, color=INK_MUTED)
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)                     # grid behind the data
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    # Trial days and trial counts are whole numbers; fractional ticks like
    # "1.5 trial days" are meaningless, so force integers on the x-axis.
    if "day" in xlabel.lower() or "number" in xlabel.lower():
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))


def rel(path: Path) -> str:
    """Show a path relative to the repo when possible, else in full."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def save_fig(fig, name: str) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"    wrote {rel(path)}")
    return f"figures/{name}"


def participant_colors(parts) -> dict:
    return {p: SERIES[i % len(SERIES)] for i, p in enumerate(sorted(parts))}


# ---------------------------------------------------------------------------
# FIGURES
# ---------------------------------------------------------------------------

def fig_session_timeline(blocks: pd.DataFrame, colors: dict) -> str:
    """
    When did recording sessions happen? Dot plot along the trial-day axis.

    Form choice: the question is "where do these sit on a timeline, and are the
    gaps even?" -- that is identity-on-an-axis, so a strip of dots, not a line
    (there is nothing continuous between sessions) and not a bar (no magnitude).
    Uneven spacing is the thing to look for: most time-series methods assume
    evenly spaced samples.
    """
    parts = sorted(blocks["participant"].unique())
    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.7 * len(parts)))
    for i, p in enumerate(parts):
        days = sorted(blocks.loc[blocks["participant"] == p, "trial_day"].unique())
        ax.scatter(days, [i] * len(days), s=60, color=colors[p],
                   edgecolor="white", linewidth=1.2, zorder=3, label=p)
        ax.text(min(days), i + 0.28,
                f"{p} — {len(days)} session{'s' if len(days) != 1 else ''}, "
                f"days {min(days)}–{max(days)}",
                fontsize=9, color=INK_MUTED, va="bottom")
    ax.set_yticks(range(len(parts)))
    ax.set_yticklabels(parts, fontsize=10, color=INK)
    ax.set_ylim(-0.6, len(parts) - 0.1)
    style_axes(ax, "Recording sessions over time",
               "Trial day (days since array implantation)", "")
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "01_session_timeline.png")


def fig_performance_over_time(trials: pd.DataFrame, colors: dict) -> str:
    """
    Does performance change across sessions?

    Form choice: a measure over ordered time -> line chart, with per-session
    points shown. Median (not mean) because angle error is bounded 0-180 and
    can be skewed; the median is less pulled around by a few bad trials.
    Shaded band = interquartile range, showing spread without a second axis.
    """
    if "angle_error_deg" not in trials:
        return ""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for p in sorted(trials["participant"].unique()):
        sub = trials[trials["participant"] == p]
        g = sub.groupby("trial_day")["angle_error_deg"]
        med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
        days = med.index.values
        ax.fill_between(days, q1.values, q3.values, color=colors[p], alpha=0.15,
                        linewidth=0)
        ax.plot(days, med.values, color=colors[p], linewidth=2,
                marker="o", markersize=5, markeredgecolor="white",
                markeredgewidth=1, label=f"{p} (median)")
    style_axes(ax, "Angle error per session — lower is better",
               "Trial day", "Angle error (degrees)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    return save_fig(fig, "02_performance_over_time.png")


def fig_error_distribution(trials: pd.DataFrame, colors: dict) -> str:
    """
    What does the spread of angle error look like overall?

    Form choice: distribution of one continuous measure -> histogram. Separate
    panels per participant rather than overlaid, so neither hides the other.
    """
    if "angle_error_deg" not in trials:
        return ""
    parts = sorted(trials["participant"].unique())
    fig, axes = plt.subplots(1, len(parts), figsize=(5 * len(parts), 3.6),
                             squeeze=False)
    for ax, p in zip(axes[0], parts):
        vals = trials.loc[trials["participant"] == p, "angle_error_deg"].dropna()
        ax.hist(vals, bins=36, range=(0, 180), color=colors[p], alpha=0.85)
        ax.axvline(vals.median(), color=INK, linewidth=1.5, linestyle="--")
        ax.text(vals.median() + 4, ax.get_ylim()[1] * 0.92,
                f"median {vals.median():.1f}°", fontsize=9, color=INK)
        style_axes(ax, f"{p} — {len(vals):,} trials",
                   "Angle error (degrees)", "Trials")
        ax.set_xticks([0, 45, 90, 135, 180])
    fig.suptitle("Distribution of per-trial angle error", fontsize=12,
                 color=INK, x=0.02, ha="left")
    return save_fig(fig, "03_error_distribution.png")


def fig_missingness(trials: pd.DataFrame) -> str:
    """
    Which columns have missing values, and how many?

    Form choice: comparing magnitudes across named categories -> horizontal
    bars, sorted, so the longest bar is unmistakable. Columns with no missing
    values are included so absence is visible too.
    """
    # Missingness applies to every column, so use them all rather than
    # filtering by dtype (which changed meaning in pandas 3).
    pct = (trials.isna().mean() * 100).sort_values()
    pct = pct[pct.index != "trial_uid"]
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(pct) + 1.6))
    colors = [SERIES[1] if v > 0 else GRID for v in pct.values]
    ax.barh(pct.index, pct.values, color=colors, height=0.62)
    for i, v in enumerate(pct.values):
        ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=9,
                color=INK if v > 0 else INK_MUTED)
    style_axes(ax, "Missing values per column (trial table)",
               "Percent of trials missing", "")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(pct.max() * 1.25, 5))
    return save_fig(fig, "04_missingness.png")


def fig_trials_per_session(blocks: pd.DataFrame, colors: dict) -> str:
    """
    How much data is there per session?

    Form choice: magnitude per ordered session -> bars. This determines whether
    a rolling-window analysis is possible; a session with very few trials
    cannot support one.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    for p in sorted(blocks["participant"].unique()):
        g = blocks[blocks["participant"] == p].groupby("trial_day")["n_trials"].sum()
        ax.bar(g.index, g.values, color=colors[p], alpha=0.85, width=0.8, label=p)
    style_axes(ax, "Trials per session", "Trial day", "Number of trials")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    return save_fig(fig, "05_trials_per_session.png")


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub markdown table."""
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append(f"{v:,.2f}" if abs(v) < 1e6 else f"{v:.3g}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def build_report(ds, figs: dict, root: Path) -> str:
    trials, blocks = ds.trials, ds.blocks
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    per_part = blocks.groupby("participant").agg(
        sessions=("trial_day", "nunique"),
        blocks=("block_id", "count"),
        trials=("n_trials", "sum"),
        bins=("n_bins", "sum"),
        features=("n_features", "max"),
    ).reset_index()
    per_part["hours"] = (per_part["bins"] * 0.02 / 3600).round(2)
    per_part["day_range"] = [
        f"{blocks.loc[blocks.participant == p, 'trial_day'].min()}–"
        f"{blocks.loc[blocks.participant == p, 'trial_day'].max()}"
        for p in per_part["participant"]
    ]

    # Gaps between consecutive sessions -- directly relevant to whether
    # time-series methods that assume even spacing can be used.
    gap_rows = []
    for p in sorted(blocks["participant"].unique()):
        days = np.array(sorted(blocks.loc[blocks.participant == p, "trial_day"].unique()))
        if len(days) < 2:
            continue
        gaps = np.diff(days)
        gap_rows.append({"participant": p, "n_gaps": len(gaps),
                         "min_gap_days": int(gaps.min()),
                         "median_gap_days": float(np.median(gaps)),
                         "max_gap_days": int(gaps.max()),
                         "evenly_spaced": bool(len(set(gaps.tolist())) == 1)})
    gaps_df = pd.DataFrame(gap_rows)

    # Column-by-column description of the trial table.
    col_rows = []
    for c in trials.columns:
        s = trials[c]
        r = {"column": c, "dtype": str(s.dtype),
             "missing_%": round(100 * float(s.isna().mean()), 2),
             "n_unique": int(s.nunique(dropna=True))}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            d = s.dropna()
            r["min"] = round(float(d.min()), 3) if len(d) else None
            r["median"] = round(float(d.median()), 3) if len(d) else None
            r["max"] = round(float(d.max()), 3) if len(d) else None
        col_rows.append(r)
    cols_df = pd.DataFrame(col_rows).fillna("")

    perf_cols = [c for c in ["angle_error_deg", "time_to_target",
                             "path_efficiency", "orth_changes"] if c in trials]
    perf_desc = (trials.groupby("participant")[perf_cols].describe().T
                 .round(3).reset_index() if perf_cols else pd.DataFrame())

    tasks = (blocks.groupby(["participant", "task_name"]).size()
             .reset_index(name="n_blocks") if "task_name" in blocks else pd.DataFrame())

    excl = ""
    if "excluded" in trials:
        e = trials.groupby("participant")["excluded"].agg(["sum", "count"])
        e["percent"] = (100 * e["sum"] / e["count"]).round(2)
        excl = md_table(e.reset_index().rename(columns={"sum": "n_excluded",
                                                        "count": "n_trials"}))

    problems = ("\n".join(f"- {p}" for p in ds.problems)
                if ds.problems else "_None flagged by the loader._")

    figs_md = "\n\n".join(
        f"### {t}\n\n![{t}]({p})" for t, p in figs.items() if p)

    return f"""# DATASET_EXPLORATION — what is actually in this dataset

**Generated:** {now} by `scripts/04_explore_dataset.py`
**Source:** `{root}` (Dryad DOI 10.5061/dryad.n2z34tn5s)
**Companion document:** `DATASET_README.md` (provenance, file structure, variable dictionary)

> **How to read this.** Everything under a **Computed** heading was calculated
> from the data by the script and is factual. Everything under a **Requires your
> judgement** heading is deliberately left unfilled — those are scientific
> decisions, and the script does not make them for you.

---

## 1. What the dataset contains — *Computed*

{md_table(per_part[["participant", "sessions", "blocks", "trials", "bins",
                    "hours", "features", "day_range"]])}

- **{len(blocks):,} blocks** across **{blocks['trial_day'].nunique()} distinct trial days**,
  **{int(blocks['n_trials'].sum()):,} trials** in total.
- At 20 ms per bin, **{blocks['n_bins'].sum() * 0.02 / 3600:.2f} hours** of recording.

### Session spacing

{md_table(gaps_df) if len(gaps_df) else "_Only one session per participant; no gaps to report._"}

> Spacing matters: most time-series methods assume evenly spaced samples. If
> `evenly_spaced` is False, that assumption is violated and any windowed
> analysis must account for it explicitly.

### Tasks present

{md_table(tasks) if len(tasks) else "_No task names recovered from task.mat._"}

---

## 2. What the observational unit is — *Computed*

The data are **nested**:

```
participant ({blocks['participant'].nunique()})
  └── session / trial day ({blocks['trial_day'].nunique()} distinct)
        └── block ({len(blocks):,})
              └── trial ({int(blocks['n_trials'].sum()):,})
                    └── time bin ({int(blocks['n_bins'].sum()):,} @ 20 ms)
```

- Behavioural measures are **per trial**.
- Neural features are **per 20 ms bin**.
- `start_bin` / `stop_bin` map each trial onto its bins.

**Consequence:** observations within a participant are not independent. With
**n = {blocks['participant'].nunique()} participants**, no population-level claim is available. Any
finding is a within-participant result, replicated or not in the second person.

---

## 3. What variables are available — *Computed*

### Trial table (`data/processed/trials.csv`)

{md_table(cols_df)}

### Block table (`data/processed/blocks.csv`)

{md_table(blocks.head(10))}

_(first 10 of {len(blocks):,} rows)_

### Neural arrays

{md_table(pd.DataFrame([
    {"participant": p,
     "blocks_with_neural": int((blocks.participant == p).sum()),
     "features": int(blocks.loc[blocks.participant == p, "n_features"].max()),
     "total_bins": int(blocks.loc[blocks.participant == p, "n_bins"].sum())}
    for p in sorted(blocks.participant.unique())]))}

### Excluded trials

{excl or "_No `excludeTrials` variable found._"}

---

## 4. Performance measures — *Computed*

{md_table(perf_desc) if len(perf_desc) else "_No behavioural performance columns found._"}

{figs_md}

---

## 5. Data quality problems flagged by the loader — *Computed*

{problems}

---

## 6. What measurements appear relevant to the research question — *Requires your judgement*

The project asks whether early-warning signals precede BCI performance
deterioration. That requires (a) a performance measure over time and (b) a
neural measure over the same time. Both exist — §3 lists them.

**Decisions only you should make, with reasons written down:**

- Which variable *operationally defines* "performance"? `angle_error_deg` is what
  the original paper uses, but `time_to_target`, `path_efficiency` and
  `orth_changes` are also present and are not the same quantity.
- What counts as "deterioration"? A threshold? A relative drop? A change point?
  Until this is defined, no analysis can be specified.
- At what level is the analysis? Per trial, per block, or per session? The
  answer changes the sample size and the meaning of the result.

---

## 7. What the dataset does NOT contain — *Computed where possible*

- **No electrode impedance measurements** and no explicit array-health variable —
  so the physical degradation parameter discussed in the literature review cannot
  be measured directly here; it can only be inferred from the neural signal.
- **Only {blocks['participant'].nunique()} participants.** No population-level inference.
- **No ground-truth failure labels.** Nothing in the data marks a "failure event",
  so any deterioration event must be defined by you and justified.
- Anything else absent is listed in §8; verify against the Dryad README.

---

## 8. What still needs verification — *Requires your judgement*

Carried over from `DATASET_README.md` §8, still open:

1. Is the decoder genuinely fixed across all sessions, with no recalibration?
2. Are `day_<N>` values truly days since implantation?
3. Confirm the 20 ms bin width from the paper's Methods.
4. What exactly do the neural feature columns represent?
5. What criterion produced `excludeTrials`?
6. Are `angle_error` units and sign convention as assumed?

---

## 9. What preprocessing may eventually be necessary — *Requires your judgement*

Candidates suggested by what is above — **none decided**:

- Normalisation across sessions (the original code rolling z-scores; whether
  that is appropriate for an early-warning analysis is an open question, since
  normalisation can remove the very drift being studied).
- Handling the missing values quantified in §3.
- A decision on excluded trials.
- Aggregation from bins to trials or sessions.
- Handling uneven session spacing (§1).

---

## 10. What analyses appear potentially possible — *Requires your judgement*

**Not filled in deliberately.** Whether the dataset can support the research
question depends on the numbers in §1 and §4 and on the definitions in §6.
Work through those first, then write this section yourself — that is the
argument the project rests on, and it should be yours.

---

*Regenerate with:* `python3 scripts/04_explore_dataset.py`
"""


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=REPO_ROOT / "data" / "raw")
    ap.add_argument("--index-base", type=int, choices=(0, 1), default=1)
    ap.add_argument("--out", type=Path, default=REPORT_DIR / "DATASET_EXPLORATION.md")
    args = ap.parse_args()

    loader = load_loader()
    print("=" * 72)
    print(f"Loading from {args.root}")
    print("=" * 72)
    ds = loader.load_dataset(args.root, index_base=args.index_base,
                             load_neural=False, verbose=True)
    print("\n" + ds.summary())

    if ds.trials.empty:
        print("\nNo trials loaded; cannot explore.", file=sys.stderr)
        return 1

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ds.trials.to_csv(PROCESSED_DIR / "trials.csv", index=False)
    ds.blocks.to_csv(PROCESSED_DIR / "blocks.csv", index=False)
    print(f"\nWrote tidy tables to {rel(PROCESSED_DIR)}/")

    colors = participant_colors(ds.blocks["participant"].unique())
    print("\nBuilding figures:")
    figs = {
        "Recording sessions over time": fig_session_timeline(ds.blocks, colors),
        "Angle error per session": fig_performance_over_time(ds.trials, colors),
        "Distribution of angle error": fig_error_distribution(ds.trials, colors),
        "Missing values": fig_missingness(ds.trials),
        "Trials per session": fig_trials_per_session(ds.blocks, colors),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_report(ds, figs, args.root))
    print(f"\nWrote {rel(args.out)}")
    print("\nSections 6, 9 and 10 are intentionally left for you to complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
