#!/usr/bin/env python3
"""
figures.py — every picture the physical phase needs, from the stored data.

=============================================================================
WHY THIS EXISTS
=============================================================================
The analysis scripts produce numbers and markdown. Numbers are what the write-up
argues from, but a poster, a slide, and a judge standing at your table all need
pictures — and a picture drawn by hand in a spreadsheet is a picture nobody can
reproduce or check.

Every figure here is regenerated from `physical/data/` by running one command.
If a number changes, re-run this and the figures change with it. **Never edit a
figure by hand**, for the same reason the reports say never to edit them by
hand: a hand-edited figure is one nobody can trace back to data.

=============================================================================
WHAT IT DRAWS, AND WHAT EACH ONE IS FOR
=============================================================================

    session      ONE session, in detail: the monitor's risk over time, the
                 moment the fault was drawn, the moment the decoder actually
                 failed, and the moment the monitor warned.
                 **This is the figure that explains the whole project.**

    leadtime     The distribution of lead times, with zero marked. Everything
                 left of zero is a warning that arrived too late.

    falsealarm   Fault-free hours accumulating against the false-alarm budget,
                 showing where the evidence becomes strong enough to say
                 anything at all.

    decisionrate Detection against how often the monitor decides, at equal
                 false-alarm cost, with confidence intervals.

    severity     Detection against how bad the fault is. A monitor that does
                 not respond to severity is not responding to the fault.

    correlation  The monitor's score against task performance — the figure the
                 field publishes — with the lead time and false-alarm rate
                 printed beside it. **The point of the phase in one panel.**

    all          every one of the above

=============================================================================
TWO THINGS THIS FILE DELIBERATELY DOES NOT DRAW
=============================================================================
**No dual-axis chart pairing lead time against false-alarm rate.** They have
different units and opposite signs of "good". Overlaying them on two scales is
the single most misleading thing this data could be made to do.

**No single combined "score".** A monitor that warns constantly has unlimited
lead time and is useless; one that never warns has a perfect false-alarm rate
and is useless. The trade-off *is* the finding, so it stays visible as two
separate things.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/make_session_table.py     # first
    python3 physical/code/figures.py all

or one at a time:

    python3 physical/code/figures.py session --session 20 --block 7
    python3 physical/code/figures.py leadtime

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/figures/*.png    at 200 dpi, sized for a poster

Each figure carries the date and the number of sessions behind it, burned into
the image. A figure that escapes into a slide deck without its caption should
still say what it rests on.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import monitor as M

DATA = M.DATA
FIGS = DATA / "figures"
WIN = DATA / "processed" / "windows"

INK = "#1a1a1a"
MUTED = "#6b6b6b"
WARN = "#c2410c"
GOOD = "#15803d"
FAULT = "#7c3aed"
GRID = "#e5e5e5"


def _setup():
    plt.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200,
        "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
        "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "grid.color": GRID, "axes.grid": True, "grid.linewidth": 0.6,
        "figure.facecolor": "white", "savefig.bbox": "tight",
    })


def _stamp(fig, df, note: str = ""):
    """Burn the provenance into the image itself."""
    import datetime
    n = len(df) if df is not None else 0
    txt = (f"physical/code/figures.py · {datetime.date.today().isoformat()}"
           f" · {n} sessions" + (f" · {note}" if note else ""))
    fig.text(0.005, 0.005, txt, fontsize=6, color=MUTED, ha="left", va="bottom")


def _table(tag: str) -> pd.DataFrame:
    f = DATA / f"sessions{tag}.csv"
    if not f.exists():
        raise SystemExit(
            f"No session table at {f}.\n"
            f"Build it first:  python3 physical/code/make_session_table.py")
    return pd.read_csv(f)


def _is_synthetic(tag: str) -> bool:
    """Did the table behind this figure come from dryrun.py?"""
    f = DATA / "processed" / f"table_meta{tag}.json"
    if not f.exists():
        return False
    try:
        return bool(json.loads(f.read_text()).get("synthetic"))
    except (OSError, ValueError):
        return False


def _save(fig, name: str, tag: str) -> Path:
    """Write the figure, marking it if the numbers in it are not data.

    Every figure goes through here, which is why the mark goes here and not in
    the six drawing functions -- one of them would eventually be added without
    it.

    The reports gained a NOT-DATA banner on 24 September 2026 after a
    dry-run P-7 report was found sitting in the real results folder. The
    figures did not, and a PNG travels further than a report: it is the thing
    that ends up pasted into a slide, a plan or a poster, with no surrounding
    text to say where it came from. A figure made of formulas must say so on
    its own face.
    """
    FIGS.mkdir(parents=True, exist_ok=True)
    if _is_synthetic(tag):
        fig.text(0.5, 0.5, "NOT DATA\nsynthetic rehearsal",
                 ha="center", va="center", rotation=30,
                 fontsize=34, color="crimson", alpha=0.20,
                 fontweight="bold", zorder=1000,
                 transform=fig.transFigure)
        # Top-left, not bottom-centre: every figure already writes its own
        # provenance footer along the bottom, and the first version of this
        # drew straight over it, leaving two overlapping lines of red and grey
        # text that were both unreadable.
        fig.text(0.005, 0.995,
                 "fake recordings from dryrun.py — remove with: "
                 "python3 physical/code/dryrun.py --cleanup",
                 ha="left", va="top", fontsize=6.5, color="crimson",
                 transform=fig.transFigure)
    out = FIGS / f"{name}{tag}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")
    return out


# ==========================================================================
def fig_session(a) -> int:
    """One session in detail. The figure that explains the project."""
    df = _table(a.tag)
    if a.session is None:
        # Default to a degraded session the monitor actually warned about, so
        # the figure shows all three markers. Falls back to any degraded one.
        cand = df[(~df.healthy.astype(bool)) & df.warned.astype(bool)
                  & df.lead_seconds.notna()]
        if not len(cand):
            cand = df[~df.healthy.astype(bool)]
        if not len(cand):
            raise SystemExit("No degraded sessions in the table.")
        row = cand.iloc[0]
    else:
        m = df[(df.session == a.session) & (df.block == a.block)]
        if not len(m):
            raise SystemExit(f"No session {a.session} block {a.block}.")
        row = m.iloc[0]

    z = np.load(WIN / f"{row.folder}{a.tag}.npz")
    t = z["window_end_seconds"]
    risk, err = z["risk"], z["error_deg"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True,
                                   gridspec_kw={"height_ratios": [1.15, 1]})

    ax1.plot(t, risk, color=INK, lw=1.6)
    ax1.set_ylabel("monitor's risk score")
    ax2.plot(t, err, color=MUTED, lw=1.6)
    ax2.set_ylabel("decoding error (degrees)")
    ax2.set_xlabel("seconds into the session")

    def mark(x, color, label, style="-"):
        if not np.isfinite(x):
            return
        for ax in (ax1, ax2):
            ax.axvline(x, color=color, lw=1.5, ls=style, alpha=0.9)
        ax1.annotate(label, xy=(x, ax1.get_ylim()[1]), xytext=(4, -10),
                     textcoords="offset points", color=color, fontsize=9,
                     rotation=90, va="top")

    mark(row.get("onset_seconds", np.nan), FAULT, "fault begins (drawn in advance)")
    mark(row.get("fail_seconds", np.nan), WARN, "decoding fails")
    mark(row.get("warn_seconds", np.nan), GOOD, "monitor warns", "--")

    lead = row.get("lead_seconds", np.nan)
    title = f"{row.folder} — "
    title += "fault-free" if row.healthy else f"{row.fault_type}, severity {row.severity}"
    if np.isfinite(lead):
        title += (f"   |   lead time {lead:+.0f} s "
                  f"({'warned in time' if lead > 0 else 'warned too late'})")
    ax1.set_title(title, fontsize=11, loc="left")

    fig.tight_layout()
    _stamp(fig, df, row.folder)
    _save(fig, "session_detail", a.tag)
    return 0


# ==========================================================================
def fig_leadtime(a) -> int:
    df = _table(a.tag)
    d = df[(~df.healthy.astype(bool)) & (df.kind != "undesigned")]
    lead = d.lead_seconds.dropna().to_numpy()
    if not len(lead):
        print("No lead times to plot — no degraded session both warned and "
              "then failed. That is itself a result; see P3_LEAD_TIME.md.")
        return 1

    fig, ax = plt.subplots(figsize=(8, 4.2))
    lo, hi = min(lead.min(), 0), max(lead.max(), 0)
    pad = max(10.0, 0.1 * (hi - lo))
    bins = np.linspace(lo - pad, hi + pad, 24)
    ax.hist(lead[lead > 0], bins=bins, color=GOOD, alpha=0.85,
            label=f"warned in time ({(lead > 0).sum()})")
    ax.hist(lead[lead <= 0], bins=bins, color=WARN, alpha=0.85,
            label=f"warned too late ({(lead <= 0).sum()})")
    ax.axvline(0, color=INK, lw=1.6)
    ax.annotate("the failure", xy=(0, ax.get_ylim()[1]), xytext=(5, -6),
                textcoords="offset points", fontsize=9, va="top", color=INK)
    ax.axvline(np.median(lead), color=INK, ls="--", lw=1.3)
    ax.set_xlabel("lead time (seconds) — positive means the warning came first")
    ax.set_ylabel("sessions")
    ax.set_title(f"How much warning, across {len(lead)} degraded sessions "
                 f"(median {np.median(lead):+.0f} s)", fontsize=11, loc="left")
    ax.legend(frameon=False)
    fig.tight_layout()
    _stamp(fig, d)
    _save(fig, "lead_time", a.tag)
    return 0


# ==========================================================================
def fig_falsealarm(a) -> int:
    """Hours accumulating against what the budget can actually be shown."""
    df = _table(a.tag)
    h = df[(df.group == "test") & df.healthy.astype(bool)].sort_values(
        ["session", "block"])
    if not len(h):
        raise SystemExit("No held-out fault-free sessions yet.")

    hours = np.cumsum(h.duration_seconds.to_numpy()) / 3600
    alarms = np.cumsum(h.warned.astype(bool).to_numpy())
    budget = M.FALSE_ALARM_BUDGET_PER_HOUR

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    # The bound a zero count supports: 3/H per hour, the rule of three.
    grid = np.linspace(max(hours[0], 0.2), max(hours[-1] * 1.35, 31), 300)
    ax.plot(grid, 3.0 / grid, color=MUTED, lw=1.4, ls="--",
            label="best claim possible with zero alarms (rule of three)")
    with np.errstate(divide="ignore", invalid="ignore"):
        observed = np.where(alarms > 0, alarms / hours, np.nan)
    ax.plot(hours, observed, color=WARN, lw=1.8, marker="o", ms=3,
            label="observed rate, once any alarm occurs")
    ax.axhline(budget, color=GOOD, lw=1.6,
               label=f"the budget ({budget}/hour)")
    ax.axvline(3.0 / budget, color=INK, lw=1.2, ls=":")
    ax.annotate(f"{3.0 / budget:.0f} h — the point where\n\"zero alarms\" "
                f"finally means\n\"inside the budget\"",
                xy=(3.0 / budget, budget * 6), xytext=(8, 0),
                textcoords="offset points", fontsize=8.5, color=INK, va="center")
    ax.set_yscale("log")
    ax.set_xlabel("hours of held-out fault-free recording")
    ax.set_ylabel("false alarms per hour")
    ax.set_title(f"What the recording so far can support — "
                 f"{hours[-1]:.1f} h, {alarms[-1]} alarms",
                 fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout()
    _stamp(fig, h)
    _save(fig, "false_alarm_evidence", a.tag)
    return 0


# ==========================================================================
def fig_decisionrate(a) -> int:
    f = DATA / "results" / f"decision_rate{a.tag}.json"
    if not f.exists():
        raise SystemExit(f"No {f}. Run analyze_decision_rate.py first.")
    d = json.loads(f.read_text())
    rows = d["curve"]
    x = [r["decisions_per_hour"] for r in rows]
    y = [r["detection_rate"] for r in rows]
    lo = [r["detection_ci95"][0] for r in rows]
    hi = [r["detection_ci95"][1] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.fill_between(x, lo, hi, color=INK, alpha=0.12)
    ax.plot(x, y, color=INK, lw=1.8, marker="o", ms=4)
    ax.set_xscale("log")
    ax.set_xlabel("decisions per hour (log scale) — fewer to the left")
    ax.set_ylabel("faults detected")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    sep = d.get("intervals_separated")
    ax.set_title("Does deciding less often help? "
                 + ("The intervals separate." if sep
                    else "The intervals overlap — not settled."),
                 fontsize=11, loc="left")
    ax.annotate("shaded band = 95% interval.\nOverlapping bands mean the\n"
                "difference is not established.",
                xy=(0.02, 0.04), xycoords="axes fraction", fontsize=8.5,
                color=MUTED, va="bottom")
    fig.tight_layout()
    _stamp(fig, None, f"{rows[0]['n_degraded']} degraded sessions")
    _save(fig, "decision_rate", a.tag)
    return 0


# ==========================================================================
def fig_severity(a) -> int:
    """The manipulation check, as a picture."""
    df = _table(a.tag)
    d = df[(~df.healthy.astype(bool)) & (df.kind != "undesigned")]
    if not len(d):
        raise SystemExit("No degraded sessions.")
    g = d.groupby("severity").apply(
        lambda x: pd.Series({
            "detected": float((x.warned & ~x.warn_before_onset).mean()),
            "n": len(x)}), include_groups=False).reset_index()

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(g.severity, g.detected, color=INK, lw=1.8, marker="o", ms=6)
    for _, r in g.iterrows():
        ax.annotate(f"n={int(r.n)}", xy=(r.severity, r.detected),
                    xytext=(0, 8), textcoords="offset points",
                    fontsize=8.5, ha="center", color=MUTED)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_xlabel("severity of the injected fault")
    ax.set_ylabel("faults detected")
    rising = len(g) > 1 and g.detected.iloc[-1] > g.detected.iloc[0]
    ax.set_title("Does the monitor respond to how bad the fault is? "
                 + ("Yes — it is tracking the fault."
                    if rising else "No — see PP-6 in the preregistration."),
                 fontsize=11, loc="left")
    fig.tight_layout()
    _stamp(fig, d)
    _save(fig, "severity_response", a.tag)
    return 0


# ==========================================================================
def fig_correlation(a) -> int:
    """The point of the phase, in one panel."""
    df = _table(a.tag).sort_values(["session", "block"])
    res = DATA / "results" / f"correlation_vs_usability{a.tag}.json"
    r = json.loads(res.read_text()) if res.exists() else None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6),
                                   gridspec_kw={"width_ratios": [1.25, 1]})

    healthy = df[df.healthy.astype(bool)]
    degraded = df[~df.healthy.astype(bool)]
    ax1.scatter(healthy.risk_score, healthy.performance, s=26, color=GOOD,
                alpha=0.75, label="fault-free")
    ax1.scatter(degraded.risk_score, degraded.performance, s=26, color=WARN,
                alpha=0.75, label="degraded")
    # Risk scores routinely span three orders of magnitude -- a healthy session
    # sits near zero and a severe fault reaches the hundreds. On a linear axis
    # every fault-free point collapses onto the y-axis and the figure shows
    # nothing about them, which is the half the false-alarm rate comes from.
    pos = df.risk_score[df.risk_score > 0]
    if len(pos) and pos.max() / max(pos.min(), 1e-9) > 50:
        ax1.set_xscale("symlog", linthresh=max(float(pos.min()), 1e-3))
        ax1.set_xlabel("the monitor's risk score (log scale)")
    else:
        ax1.set_xlabel("the monitor's risk score")
    ax1.set_ylabel("decoding error (degrees)")
    ax1.legend(frameon=False, fontsize=9, loc="lower right")
    if r:
        c = r["correlations"]
        ax1.set_title(
            f"What the field reports:  raw r = {c['raw_r']:+.2f}",
            fontsize=11, loc="left")
        ax1.annotate(
            f"with the time trend removed: {c['partial_r']:+.2f}\n"
            f"on changes rather than levels: {c['diff_r']:+.2f}",
            xy=(0.03, 0.96), xycoords="axes fraction", fontsize=9,
            va="top", color=MUTED)
    else:
        ax1.set_title("Monitor score against performance", fontsize=11, loc="left")

    ax2.axis("off")
    ax2.set_title("What decides whether it is usable", fontsize=11, loc="left")
    if r:
        u = r["usability"]
        lines = []
        if "median_lead_seconds" in u:
            v = u["median_lead_seconds"]
            lines.append((f"median lead time", f"{v:+.0f} s",
                          GOOD if v > 0 else WARN))
        if "false_alarms_per_hour" in u:
            v = u["false_alarms_per_hour"]
            lines.append(("false alarms per hour", f"{v:.2f}",
                          GOOD if v <= r["false_alarm_budget_per_hour"] else WARN))
            lines.append(("the budget",
                          f"{r['false_alarm_budget_per_hour']:.2f}", MUTED))
        if "healthy_hours" in u:
            lines.append(("fault-free hours behind that",
                          f"{u['healthy_hours']:.1f} h", MUTED))
        for i, (lab, val, col) in enumerate(lines):
            y = 0.84 - i * 0.15
            ax2.text(0.02, y, lab, fontsize=10.5, color=MUTED, va="center")
            ax2.text(0.98, y, val, fontsize=15, color=col, va="center",
                     ha="right", fontweight="bold")
        verdict = ("Hypothesis SUPPORTED — correlates well, unusable as a warning"
                   if r.get("hypothesis_supported") else
                   "Hypothesis not supported")
        ax2.text(0.02, 0.06, verdict, fontsize=10, color=INK, va="center",
                 fontweight="bold", wrap=True)
    else:
        ax2.text(0.02, 0.5, "Run analyze_correlation.py to fill this panel.",
                 fontsize=10, color=MUTED, va="center")

    fig.tight_layout()
    _stamp(fig, df)
    _save(fig, "correlation_vs_usability", a.tag)
    return 0


# ==========================================================================
def fig_all(a) -> int:
    bad = 0
    for fn in (fig_session, fig_leadtime, fig_falsealarm, fig_severity,
               fig_correlation, fig_decisionrate):
        try:
            bad += fn(a)
        except SystemExit as e:
            print(f"skipped {fn.__name__}: {e}")
        except Exception as e:
            print(f"FAILED {fn.__name__}: {type(e).__name__}: {e}")
            bad += 1
    print(f"\nfigures are in {FIGS}")
    return 1 if bad else 0


def main() -> int:
    _setup()
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, helptext in (
            ("session", fig_session, "one session in detail"),
            ("leadtime", fig_leadtime, "distribution of lead times"),
            ("falsealarm", fig_falsealarm, "evidence against the budget"),
            ("decisionrate", fig_decisionrate, "detection vs decision rate"),
            ("severity", fig_severity, "detection vs severity"),
            ("correlation", fig_correlation, "the hypothesis, in one panel"),
            ("all", fig_all, "every figure")):
        q = sub.add_parser(name, help=helptext)
        q.add_argument("--tag", default="")
        q.add_argument("--session", type=int, default=None)
        q.add_argument("--block", type=int, default=1)
        q.set_defaults(fn=fn)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
