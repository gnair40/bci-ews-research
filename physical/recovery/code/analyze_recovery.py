#!/usr/bin/env python3
"""
analyze_recovery.py: experiment P-8, what is a failure point worth?

=============================================================================
STATUS: DRAFT. NOT PREREGISTERED. NOTHING HAS BEEN MEASURED WITH IT.
=============================================================================
Part of the proposed recovery subphase. See `physical/recovery/02_DESIGN.md`.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
It needs no new recordings. It reads the sessions the rest of the physical
phase records anyway, and for each one asks: if a repair had started at a given
moment, how much better would decoding have been for the rest of the session.

"A given moment" is one of three failure points, because they answer three
different questions:

    onset     the sealed start of the fault. Nobody could know this in real use.
              It shows the most that ANY monitor could buy.
    failure   the moment decoding had measurably failed. A monitor with a lead
              time of exactly zero.
    warning   the moment this project's monitor actually warned. What this
              monitor buys, including when it is late.

and on fault-free sessions:

    matched      a moment chosen by the same rule that places onsets, where
                 nothing is wrong. It measures what a repair nobody needed costs.
    false_alarm  the moment of a real false alarm, if the monitor raised one.

At each failure point all four repairs in `repairs.py` are applied and all are
reported. A repair is scored only on the part of the session that comes AFTER
the stretch it was built from.

=============================================================================
HOW TO RUN IT
=============================================================================
After `make_session_table.py`, like every other analysis:

    python3 physical/recovery/code/analyze_recovery.py

It writes three files to `physical/data/results/`: the report `P8_RECOVERY.md`,
the numbers behind it in `recovery.json`, and one row per session and failure
point in `recovery_sessions.json`. All three say inside themselves whether they
came from rehearsal recordings, so `dryrun.py --cleanup` removes them.

**Do not edit the report by hand.** If a number looks wrong, fix this script and
run it again.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "code"))
import monitor as M  # noqa: E402
import repairs as R  # noqa: E402
from analyze_decision_rate import wilson  # noqa: E402
from analyze_leadtime import median_ci  # noqa: E402

DATA = M.DATA
RESULTS = DATA / "results"
FIXES = [r for r in R.REPAIRS if r != "R0_none"]
LABEL = {"R1_renormalise": "R1 renormalise", "R2_mask_refit": "R2 mask and refit",
         "R3_mask_renormalise": "R3 mask + renormalise", "R4_recalibrate": "R4 recalibrate"}
# Onsets are drawn from the middle three fifths of a session (draw_onset.py).
# A needless repair is placed by the same rule so the two are comparable.
LOW, HIGH = 0.20, 0.80


def frame_of(seconds, fps=M.FPS):
    return None if seconds is None or not np.isfinite(seconds) else int(round(seconds * fps))


def score_all(df: pd.DataFrame, raw: Path, lag: float, calib: dict) -> pd.DataFrame:
    """One row per session, failure point and adaptation length."""
    rows = []
    for _, r in df.iterrows():
        sess = M.load_session(raw / r.folder, lag)
        n = len(sess.X)
        healthy = bool(r.healthy)
        if healthy:
            rng = np.random.default_rng(int(r.session) * 1000 + int(r.block))
            points = {"matched": int(rng.uniform(LOW, HIGH) * n)}
            if bool(r.warned):
                points["false_alarm"] = frame_of(r.warn_seconds)
            base_end = None
            arm = "fault_free"
        else:
            onset = sess.onset_frame if sess.onset_frame is not None else frame_of(r.onset_seconds)
            points = {"onset": onset, "failure": frame_of(r.fail_seconds),
                      "warning": frame_of(r.warn_seconds) if bool(r.warned) else None}
            base_end = onset
            arm = "undesigned" if str(r.onset_provenance) != "drawn" else "sealed"
        for point, frame in points.items():
            for adapt in R.ADAPT_SWEEP:
                row = {"session": int(r.session), "block": int(r.block), "folder": r.folder,
                       "config": r.config, "arm": arm,
                       "fault_type": "NONE" if healthy else r.fault_type,
                       "severity": 0.0 if healthy else float(r.severity),
                       "failure_point": point, "adapt_seconds": adapt}
                res = None if frame is None else R.score_session(
                    sess.X, sess.heading, calib, frame, base_end, adapt)
                row["scored"] = res is not None
                row["why_not"] = ("" if res is not None else
                                  "no such moment in this session" if frame is None
                                  else "too little of the session left to score on")
                rows.append({**row, **(res or {})})
    return pd.DataFrame(rows)


def describe(d: pd.DataFrame) -> dict:
    """For one group of scored sessions: what each repair did, against doing nothing."""
    out = {"n_scored": int(len(d))}
    if not len(d):
        return out
    before, none = d.error_before.to_numpy(), d.R0_none.to_numpy()
    damaged = (none - before) >= R.DAMAGE_DEG
    out["n_damaged"] = int(np.nansum(damaged))
    out["median_error_before_deg"] = median_ci(before)[0]
    out["median_error_unrepaired_deg"] = median_ci(none)[0]
    out["median_lost_channels"] = float(np.median(d.n_lost_channels))
    for fix in FIXES:
        after = d[fix].to_numpy()
        gain = none - after                      # degrees recovered; negative = made worse
        frac = np.array([R.recovery_fraction(b, u, a) for b, u, a in zip(before, none, after)])
        k = int(np.sum(damaged & (after < before)))
        nd = int(np.sum(damaged))
        lo, hi = wilson(k, nd)
        m, m_lo, m_hi = median_ci(gain)
        f, f_lo, f_hi = median_ci(frac)
        out[fix] = {"median_error_after_deg": median_ci(after)[0],
                    "median_gain_deg": m, "gain_ci95": [m_lo, m_hi],
                    "share_improved": float(np.mean(gain > 0)),
                    "median_recovery_fraction": f, "recovery_fraction_ci95": [f_lo, f_hi],
                    "n_better_than_before": k, "n_damaged": nd,
                    "better_than_before_ci95": [lo, hi],
                    "needs_labels": R.NEEDS_LABELS[fix]}
    return out


def num(x, d=1):
    return "n/a" if x is None or not np.isfinite(x) else f"{x:.{d}f}"


def ci(pair, d=1):
    return "not estimable" if not np.all(np.isfinite(pair)) else f"{pair[0]:.{d}f} to {pair[1]:.{d}f}"


def table(groups: dict, first: str, frac: bool = True) -> list[str]:
    head = (f"| {first} | Repair | Sessions | Error before | Unrepaired | After repair "
            f"| Degrees recovered (95% interval) |")
    head += " Recovery fraction (95% interval) | Better than before |" if frac else ""
    lines = [head, "|" + "---|" * (9 if frac else 7)]
    for name, g in groups.items():
        if not g.get("n_scored"):
            lines.append(f"| {name} | none scored |" + " |" * (7 if frac else 5))
            continue
        for fix in FIXES:
            x = g[fix]
            row = (f"| {name} | {LABEL[fix]} | {g['n_scored']} | "
                   f"{num(g['median_error_before_deg'])}° | "
                   f"{num(g['median_error_unrepaired_deg'])}° | "
                   f"{num(x['median_error_after_deg'])}° | "
                   f"{num(x['median_gain_deg'])}° ({ci(x['gain_ci95'])}) |")
            if frac:
                row += (f" {num(x['median_recovery_fraction'], 2)} "
                        f"({ci(x['recovery_fraction_ci95'], 2)}) | "
                        f"{x['n_better_than_before']} of {x['n_damaged']} |")
            lines.append(row)
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="", help="suffix of the session table to read")
    a = ap.parse_args()

    table_file = DATA / f"sessions{a.tag}.csv"
    meta_file = DATA / "processed" / f"table_meta{a.tag}.json"
    if not table_file.exists() or not meta_file.exists():
        print(f"There is no session table at {table_file}.\n"
              "Run make_session_table.py first; this analysis reads what it writes.")
        return 1
    df = pd.read_csv(table_file)
    meta = json.loads(meta_file.read_text())
    raw = Path(meta["raw"])
    raw = raw if raw.is_absolute() else M.REPO / raw
    lag = float(meta.get("lag_seconds") or 0.0)

    fit = df[df.group == "fit"]
    test = df[df.group == "test"]
    if len(fit) == 0 or len(test) == 0:
        print("The session table has no calibration group or no reporting group. Nothing to do.")
        return 1
    print(f"calibration summary from {len(fit)} sessions; scoring {len(test)} reporting sessions")
    calib = R.calibration_stats(list(fit.folder), load=lambda f: M.load_session(raw / f, lag))
    per = score_all(test, raw, lag, calib)
    RESULTS.mkdir(parents=True, exist_ok=True)
    # Written as JSON that declares where it came from, not as a bare table: a
    # first version wrote a CSV, and the rehearsal clean-up left it behind
    # because nothing in the file said it was synthetic.
    (RESULTS / f"recovery_sessions{a.tag}.json").write_text(json.dumps(
        {"synthetic": bool(meta.get("synthetic")),
         "rows": json.loads(per.to_json(orient="records"))}, indent=1) + "\n")

    ok = per[per.scored]
    main_ = ok[ok.adapt_seconds == R.ADAPT_SECONDS]
    sealed = main_[main_.arm == "sealed"]
    result = {
        "status": "DRAFT analysis; the subphase is not preregistered",
        "synthetic": bool(meta.get("synthetic")),
        "settings": {"adapt_seconds": R.ADAPT_SECONDS, "adapt_sweep": R.ADAPT_SWEEP,
                     "min_eval_seconds": R.MIN_EVAL_SECONDS, "lost_ratio": R.LOST_RATIO,
                     "reference_quantile": R.REFERENCE_QUANTILE, "damage_deg": R.DAMAGE_DEG},
        "n_calibration_sessions": int(len(fit)), "n_reporting_sessions": int(len(test)),
        "not_scored": per[~per.scored & (per.adapt_seconds == R.ADAPT_SECONDS)]
        .groupby(["arm", "failure_point", "why_not"]).size().reset_index(name="n")
        .to_dict("records"),
        "sealed": {p: {**{t: describe(g) for t, g in sealed[sealed.failure_point == p]
                          .groupby("fault_type")},
                       "ALL": describe(sealed[sealed.failure_point == p])}
                   for p in ("onset", "failure", "warning")},
        "sealed_by_severity": {str(s): describe(g) for s, g in
                               sealed[sealed.failure_point == "onset"].groupby("severity")},
        "fault_free": {p: describe(main_[(main_.arm == "fault_free")
                                         & (main_.failure_point == p)])
                       for p in ("matched", "false_alarm")},
        "undesigned": {"onset": describe(main_[(main_.arm == "undesigned")
                                               & (main_.failure_point == "onset")])},
        "sweep": {str(s): describe(ok[(ok.arm == "sealed") & (ok.failure_point == "onset")
                                      & (ok.adapt_seconds == s)]) for s in R.ADAPT_SWEEP},
    }
    (RESULTS / f"recovery{a.tag}.json").write_text(json.dumps(result, indent=1) + "\n")

    A = ["# P-8: recovery from the failure point", ""]
    A += M.provenance_banner(meta)
    A += ["**Generated by `physical/recovery/code/analyze_recovery.py`. Do not edit by hand.**",
          "",
          "> **Draft analysis.** The recovery subphase has not been preregistered. Until it",
          "> is, anything below is exploratory and must be labelled so wherever it is quoted.",
          "",
          f"Calibration sessions: {len(fit)}. Reporting sessions scored: {len(test)}. "
          f"Adaptation period: {R.ADAPT_SECONDS:.0f} s. A repair is scored only on the part "
          f"of the session after its adaptation period, and only if at least "
          f"{R.MIN_EVAL_SECONDS:.0f} s remain.",
          "",
          "**How to read the columns.** *Degrees recovered* is the unrepaired error minus "
          "the error after the repair, per session, then the median; negative means the "
          "repair made decoding worse. *Recovery fraction* is that gain divided by the "
          f"damage, for sessions the fault damaged by at least {R.DAMAGE_DEG:.0f}°: 0 is "
          "nothing recovered, 1 is fully restored, above 1 is better than before the "
          "fault. *Better than before* counts those sessions.", ""]
    titles = {"onset": "Repair started at the sealed onset: the most any monitor could buy",
              "failure": "Repair started when decoding had failed: a lead time of zero",
              "warning": "Repair started when this monitor warned"}
    for p in ("onset", "failure", "warning"):
        A += [f"## {titles[p]}", ""] + table(result["sealed"][p], "Fault type") + [""]
    A += ["## By severity, repair started at the sealed onset", ""]
    A += table(result["sealed_by_severity"], "Severity") + [""]
    A += ["## The cost of a repair nobody needed (fault-free sessions)", "",
          "Negative degrees recovered means the repair made a healthy decoder worse.", ""]
    A += table({"matched moment": result["fault_free"]["matched"],
                "real false alarm": result["fault_free"]["false_alarm"]},
               "Failure point", frac=False) + [""]
    A += ["## Faults nobody designed (P-5), repair started at the noted onset", "",
          "Reported apart from the sealed faults, as everywhere else in this phase.", ""]
    A += table({"undesigned": result["undesigned"]["onset"]}, "Arm") + [""]
    A += ["## How long the repair watches before it acts", "",
          f"All fault types, repair started at the sealed onset. {R.ADAPT_SECONDS:.0f} s is "
          "the primary setting; the others are shown so that it cannot be mistaken for a "
          "choice made after the fact.", ""]
    A += table({f"{float(s):.0f} s": g for s, g in result["sweep"].items()},
               "Adaptation") + [""]
    if result["not_scored"]:
        A += ["## Not scored", "", "| Arm | Failure point | Reason | Sessions |", "|---|---|---|---|"]
        A += [f"| {x['arm']} | {x['failure_point']} | {x['why_not']} | {x['n']} |"
              for x in result["not_scored"]] + [""]
    A += ["## What this cannot show", "",
          "- The error here is decoding error on recorded frames. It is not a person "
          "controlling a cursor, and a person adapts in ways a recording cannot.",
          "- R4 uses the true direction, which the bench always knows. A real device "
          "knows it only during a calibration task that stops the user.",
          "- A repair started at the sealed onset is an upper bound, not a prediction of "
          "what a deployed system would achieve.",
          "- One apparatus in one room. See `physical/docs/07_ANALYSIS.md`."]
    out = RESULTS / f"P8_RECOVERY{a.tag}.md"
    out.write_text("\n".join(A) + "\n")
    print(f"wrote {out.relative_to(M.REPO)} and recovery{a.tag}.json")
    if meta.get("synthetic"):
        print("THESE ARE NOT DATA: the session table came from dryrun.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
