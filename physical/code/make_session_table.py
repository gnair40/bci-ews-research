#!/usr/bin/env python3
"""
make_session_table.py — turn raw recordings into one row per session.

=============================================================================
WHAT THIS SCRIPT DOES
=============================================================================
It reads every recording in `physical/data/raw/`, runs the decoder and the
monitor over each one, and writes two things: a table with one row per session,
and, for each session, the monitor's risk and the decoder's error window by
window.

Every analysis script downstream reads those outputs rather than the raw
recordings. That way the decoding is done once, in one place, and four scripts
cannot disagree about what a recording contained.

**It never modifies anything in `physical/data/raw/`.** Raw data is written
once, by the recording scripts, and read forever after.

=============================================================================
THE THREE GROUPS, AND WHY A SESSION MUST BE IN EXACTLY ONE
=============================================================================
    fit    The decoder and the monitor are built from these sessions, and from
           nothing else. All healthy.
    val    The WARN threshold -- the monitor's single adjustable number -- is
           chosen on these. All healthy.
    test   Everything else. The false-alarm rate and the lead time are reported
           from here, and only from here.

The separation is the entire reason the numbers mean anything. A threshold
chosen on the same sessions the false-alarm rate is then measured on will
always look good, because it was chosen to look good on exactly those
recordings. That is not a measurement; it is a description of a fitting
procedure. Keeping the three groups apart is what turns it back into a
measurement.

Sessions are assigned in recording order, never at random, so that re-running
this script gives the same answer and so that the fit group is genuinely the
earliest data — a decoder built from the future would be a decoder no real
system could have had.

=============================================================================
HOW MUCH HEALTHY RECORDING IS ENOUGH? (READ THIS ONE)
=============================================================================
The false-alarm budget is **0.1 warnings per hour**. Suppose the monitor is
perfect and produces zero false alarms in the test group. How many hours does
that have to be before "zero" is evidence of anything?

The standard answer is the **rule of three**: seeing no events in H hours puts
a 95% upper bound of 3/H per hour on the true rate. To get that bound down to
0.1 per hour you need **H = 30 hours of held-out healthy recording** — and the
test group is only part of the total, so the campaign needs more than that.

At five minutes a session, 30 test hours is about **360 sessions** in the test
group alone. The experiment plan's figure of 101 healthy sessions gives roughly
four test hours, which can only support an upper bound of about 0.75 per hour —
seven times the budget.

**101 healthy sessions is enough to detect a monitor that is noisy. It is not
enough to demonstrate that a quiet monitor meets the budget.** This script
prints the arithmetic for whatever you have actually recorded, so the claim in
the write-up can be the one the data supports. If the result is an upper bound
rather than a rate, say "upper bound" — the difference is the whole argument.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/make_session_table.py

with the defaults, or:

    python3 physical/code/make_session_table.py --detector mean_activity
    python3 physical/code/make_session_table.py --decoder per-session

Run it once per detector you want to compare. Each run overwrites the table, so
pass `--tag` to keep several side by side:

    python3 physical/code/make_session_table.py --detector mean_activity --tag mean

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/sessions.csv                  one row per session
    physical/data/processed/windows/*.npz       per-window risk and error
    physical/data/processed/table_meta.json     the settings and the split

=============================================================================
WHERE IT FITS
=============================================================================
    run_session.py -> make_session_table.py -> analyze_leadtime.py
                                            -> analyze_falsealarm.py
                                            -> analyze_correlation.py
                                            -> analyze_decision_rate.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import monitor as M

DATA = M.DATA
PROCESSED = DATA / "processed"
WINDOWS = PROCESSED / "windows"

MIN_FIT_SESSIONS = 5        # below this the decoder fit is not trustworthy
RULE_OF_THREE = 3.0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=None, help="folder of recordings")
    ap.add_argument("--detector", default="decoder_guard",
                    choices=sorted(M.DETECTORS))
    ap.add_argument("--decoder", default="frozen",
                    choices=["frozen", "per-session"],
                    help="frozen: one decoder from the fit sessions, as a real "
                         "implant has. per-session: refit every session, which "
                         "hides drift between sessions")
    ap.add_argument("--val-fraction", type=float, default=0.35,
                    help="share of the remaining healthy sessions used to "
                         "choose the threshold")
    ap.add_argument("--budget", type=float, default=M.FALSE_ALARM_BUDGET_PER_HOUR,
                    help="false alarms per hour the threshold must respect")
    ap.add_argument("--lag", type=float, default=None,
                    help="camera-behind-screen delay in seconds; "
                         "default reads physical/data/lag.json, else 0")
    ap.add_argument("--tag", default="", help="suffix for the output filenames")
    a = ap.parse_args()

    folders = M.find_sessions(a.raw)
    if not folders:
        print(f"No recordings found in {a.raw or DATA / 'raw'}.")
        print("Record some first:  python3 physical/code/run_session.py --help")
        return 1

    lag = a.lag
    if lag is None:
        f = DATA / "lag.json"
        lag = json.loads(f.read_text()).get("lag_seconds", 0.0) if f.exists() else 0.0
        if not f.exists():
            print("No physical/data/lag.json, so assuming the camera is perfectly")
            print("in step with the screen. Measure it once with:")
            print("    python3 physical/code/bench.py lag --session 0 --block 1")
            print()

    # Metadata only. A five-minute session is 46 MB of camera data, so a
    # 480-session campaign is 22 GB -- more than any machine this will run on,
    # and it would crash on the fourth night of recording, which is the worst
    # possible moment to find out. Working out which group a session belongs to
    # needs a few hundred bytes, not 46 MB, so that is read first and the
    # recordings are loaded one at a time later.
    print(f"reading metadata for {len(folders)} recordings "
          f"(lag {lag * 1000:.0f} ms)")
    sessions = []
    for f in folders:
        try:
            sessions.append(M.session_info(f))
        except Exception as e:
            # Loudly, not silently. A recording that will not load is a fact
            # about the campaign, and quietly dropping it changes every
            # denominator downstream.
            print(f"  COULD NOT READ {f.name}: {type(e).__name__}: {e}")
    if not sessions:
        print("Nothing loaded.")
        return 1

    # ------------------------------------------------------------ exclusions
    # The protocol says a session is discarded only for a recorded mechanical
    # reason, never because of how it turned out, and that every discard is
    # written down. That needs a mechanism, or the only ways to exclude a bad
    # session are to delete raw data (forbidden) or to edit this script (worse).
    #
    # physical/data/EXCLUSIONS.csv, columns: folder,reason,excluded_at
    # A row with no reason is refused outright -- an unexplained exclusion is
    # indistinguishable from dropping a session for its result.
    excl_file = DATA / "EXCLUSIONS.csv"
    excluded = {}
    if excl_file.exists():
        import csv as _csv
        with excl_file.open() as fh:
            for row in _csv.DictReader(fh):
                name = (row.get("folder") or "").strip()
                reason = (row.get("reason") or "").strip()
                if not name:
                    continue
                if not reason:
                    print(f"\nREFUSING: {excl_file} excludes {name!r} with no "
                          f"reason given.")
                    print("Every exclusion needs a recorded mechanical reason.")
                    print("An exclusion with no reason cannot be told apart from")
                    print("dropping a session because of how it turned out.")
                    return 1
                excluded[name] = reason
    if excluded:
        print(f"\n{len(excluded)} session(s) excluded by {excl_file.name}:")
        for k, v in excluded.items():
            print(f"  {k:<14} {v}")
        print("These are left out of every group and every number below.")
        sessions = [x for x in sessions if x.folder.name not in excluded]
        if not sessions:
            print("\nEverything was excluded. Nothing to analyse.")
            return 1

    # ---------------------------------------------------------------- split
    def kind(s):
        return s.kind

    # A P-5 session whose onset has not been written down yet looks, to every
    # piece of code here, like a healthy session -- it has no plan, so nothing
    # says a fault happened. It would then enter the false-alarm arm and
    # silently corrupt the one measurement this phase exists to make. Caught
    # here, loudly, and excluded.
    orphans = [s for s in sessions
               if kind(s) == "undesigned" and s.plan is None]
    if orphans:
        print()
        print(f"{len(orphans)} undesigned-fault session(s) have no noted onset:")
        for s in orphans:
            print(f"  {s.folder.name}")
        print("They are EXCLUDED from everything below. A P-5 session with no")
        print("noted onset cannot be scored, and leaving it in would put a")
        print("session that contains a fault into the fault-free arm.")
        print("Write the onsets down:")
        print("    python3 physical/code/note_onset.py --session N --block N "
              "--at-clock HH:MM:SS")
        # Compared by folder name, not by object. A Session holds numpy arrays,
        # and comparing two of them with `==` gives an array rather than a
        # yes/no, which would raise instead of filtering.
        drop = {s.folder.name for s in orphans}
        sessions = [s for s in sessions if s.folder.name not in drop]

    calib = [s for s in sessions if kind(s) == "calibration"]
    healthy = [s for s in sessions
               if kind(s) not in ("calibration", "undesigned") and s.healthy]
    degraded = [s for s in sessions
                if kind(s) != "calibration" and not s.healthy]

    fit = list(calib)
    borrowed = 0
    if len(fit) < MIN_FIT_SESSIONS:
        borrowed = min(MIN_FIT_SESSIONS - len(fit), len(healthy))
        fit += healthy[:borrowed]
        healthy = healthy[borrowed:]
        if borrowed:
            print(f"\nOnly {len(calib)} calibration sessions, so the first "
                  f"{borrowed} healthy sessions were used to build the decoder.")
            print("Those sessions are now OUT of the false-alarm arm — a monitor")
            print("cannot be tested for false alarms on the data it was built")
            print("from. Record more calibration sessions to get them back.")
    if len(fit) < 3:
        print(f"\nOnly {len(fit)} sessions available to build the decoder. "
              f"That is not enough; record more healthy sessions.")
        return 1

    n_val = max(1, int(round(len(healthy) * a.val_fraction)))
    val, test_healthy = healthy[:n_val], healthy[n_val:]
    if not test_healthy:
        print("\nEvery healthy session was used to build or tune the monitor, so")
        print("there is nothing left to measure the false-alarm rate on. Record")
        print("more healthy sessions before reporting a false-alarm rate.")

    group = {}
    for s in fit:
        group[s.folder.name] = "fit"
    for s in val:
        group[s.folder.name] = "val"
    for s in test_healthy + degraded:
        group[s.folder.name] = "test"

    # ------------------------------------------------------------- decoder
    frozen_dec = M.fit_decoder_streaming([s.folder for s in fit], lag)
    frames_fit = sum(s.n_frames for s in fit)
    print(f"\ndecoder fitted on {len(fit)} sessions, "
          f"{frames_fit} frames ({frames_fit / M.FPS / 60:.1f} minutes)")

    def decoder_for(sess):
        """`sess` here is a loaded Session, not a SessionInfo."""
        if a.decoder == "frozen":
            return frozen_dec
        half = len(sess.X) // 2
        return M.fit_decoder(sess.X[:half], sess.heading[:half])

    # ------------------------------------------------------------ detector
    # One session at a time. Windows are tiny compared with the frames they
    # come from -- 55 x 384 floats against 15000 x 384 -- so the accumulated
    # windows are affordable even for a large fit set; the raw frames are not.
    chunks = []
    for info in fit:
        sess = M.load_session(info.folder, lag)
        chunks.append(M.window_means(sess.X, M.window_starts(len(sess.X))))
        del sess
    fit_windows = np.vstack(chunks)
    del chunks
    detector = M.fit_detector(a.detector, fit_windows)
    print(f"monitor '{a.detector}' fitted on {len(fit_windows)} healthy windows")

    # -------------------------------------------- score everything, once
    WINDOWS.mkdir(parents=True, exist_ok=True)
    rows, scores = [], {}
    for info in sessions:
        # Loaded here and released at the end of the loop body, so peak memory
        # is one session whatever the campaign size.
        try:
            s = M.load_session(info.folder, lag)
        except Exception as e:
            print(f"  COULD NOT LOAD {info.name}: {type(e).__name__}: {e}")
            continue
        starts = M.window_starts(len(s.X))
        if not len(starts):
            print(f"  {s.folder.name}: too short to make a single 30 s window, "
                  f"skipped")
            del s
            continue
        F = M.window_means(s.X, starts)
        raw = detector.score(F)
        ow = M.onset_window_index(s.onset_frame, starts)
        flat = M.detrend(raw, ow)
        perf = M.window_error(s.X, s.heading, starts, decoder_for(s))
        t_end = (starts + M.WINDOW_FRAMES) / M.FPS

        fw = M.fail_window(perf, ow)
        np.savez(WINDOWS / f"{s.folder.name}{a.tag}.npz",
                 start_frame=starts, window_end_seconds=t_end,
                 risk=raw, risk_detrended=flat, error_deg=perf,
                 onset_window=-1 if ow is None else ow,
                 fail_window=-1 if fw is None else fw,
                 onset_seconds=np.nan if s.onset_frame is None
                 else s.onset_frame / M.FPS)
        scores[s.folder.name] = raw

        p = s.plan or {}
        rows.append({
            "session": s.session, "block": s.block,
            "folder": s.folder.name, "group": group.get(s.folder.name, "test"),
            "kind": info.kind, "healthy": bool(s.healthy),
            "fault_type": p.get("fault_type") or "",
            "severity": p.get("severity", 0.0),
            "onset_seconds": p.get("onset_seconds", np.nan),
            # "drawn" was fixed and checksummed before the recording existed;
            # "stopwatch" was written down afterwards by the experimenter. The
            # analysis reports them in separate tables and never pools them.
            "onset_provenance": (p.get("onset_provenance", "drawn")
                                 if p.get("onset_frame") is not None else ""),
            "duration_seconds": s.duration_seconds,
            "n_windows": len(starts),
            "risk_score": float(np.median(raw)),
            "performance": float(np.nanmedian(perf)),
            "chance_deg": M.chance_error(s.heading),
            "fail_seconds": M.window_end_seconds(fw, starts),
        })
        del s, F, perf

    df = pd.DataFrame(rows)
    df["margin_deg"] = df.chance_deg - df.performance

    # -------------------------------------------------- the one free number
    val_names = [s.folder.name for s in val if s.folder.name in scores]
    val_hours = float(df[df.folder.isin(val_names)].duration_seconds.sum() / 3600)
    if val_names and val_hours > 0:
        threshold = M.choose_threshold([scores[n] for n in val_names],
                                       val_hours, a.budget)
        print(f"WARN threshold {threshold:.3g}, chosen on {len(val_names)} "
              f"held-out healthy sessions ({val_hours:.2f} h)")
    else:
        threshold = float("nan")
        print("No validation sessions, so no threshold could be chosen.")

    # ------------------------------------------------------- when it warned
    warn_s, warned, early = [], [], []
    for _, r in df.iterrows():
        z = np.load(WINDOWS / f"{r.folder}{a.tag}.npz")
        w = M.warn_index(z["risk"], threshold) if np.isfinite(threshold) else None
        ws = M.warn_seconds(w, z["start_frame"])
        warn_s.append(ws)
        warned.append(w is not None)
        # A warning whose window ENDS before the fault began contains no faulty
        # data at all, so it cannot be a detection of that fault however good it
        # looks. It is a false alarm that happened to occur inside a degraded
        # session, and counting it as a detection would be the single easiest
        # way to fake a positive result here.
        early.append(bool(w is not None and np.isfinite(r.onset_seconds)
                          and ws <= r.onset_seconds))
    df["warn_seconds"], df["warned"] = warn_s, warned
    df["warn_before_onset"] = early

    # The two times, as defined in monitor.py. Neither is computed for a warning
    # that arrived before the fault did.
    valid = df.warned & ~df.warn_before_onset
    df["lead_seconds"] = np.where(valid, df.fail_seconds - df.warn_seconds, np.nan)
    df["detect_seconds"] = np.where(valid, df.warn_seconds - df.onset_seconds, np.nan)

    out = DATA / f"sessions{a.tag}.csv"
    df.sort_values(["session", "block"]).to_csv(out, index=False)

    # ----------------------------------------------------- the arithmetic
    t_h = df[(df.group == "test") & df.healthy]
    test_hours = float(t_h.duration_seconds.sum() / 3600)
    fa = int(t_h.warned.sum())
    bound = RULE_OF_THREE / test_hours if test_hours > 0 else float("inf")
    needed_hours = RULE_OF_THREE / a.budget

    meta = {
        "detector": a.detector, "decoder": a.decoder, "lag_seconds": lag,
        "budget_per_hour": a.budget, "warn_threshold": threshold,
        "n_sessions": int(len(df)),
        "n_fit": len(fit), "n_val": len(val_names),
        "n_test_healthy": int(len(t_h)), "n_degraded": len(degraded),
        "n_undesigned": int((df.kind == "undesigned").sum()) if len(df) else 0,
        "n_orphaned_undesigned": len(orphans),
        "borrowed_healthy_for_fit": borrowed,
        "excluded": excluded,
        "test_healthy_hours": test_hours,
        "false_alarms_in_test": fa,
        "false_alarms_per_hour": fa / test_hours if test_hours else None,
        "upper_bound_if_zero_per_hour": bound,
        "hours_needed_for_budget": needed_hours,
        "window_frames": M.WINDOW_FRAMES, "step_frames": M.STEP_FRAMES,
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    (PROCESSED / f"table_meta{a.tag}.json").write_text(json.dumps(meta, indent=2))

    print()
    print("=" * 70)
    print(f"{len(df)} sessions  ->  {out}")
    n_undesigned = int((df.kind == "undesigned").sum()) if len(df) else 0
    print(f"  fit {len(fit)}   val {len(val_names)}   "
          f"test healthy {len(t_h)}   degraded {len(degraded)}"
          + (f"   (of which {n_undesigned} undesigned, reported separately)"
             if n_undesigned else ""))
    print(f"  median decoding error {df.performance.median():.1f} deg "
          f"vs chance {df.chance_deg.median():.1f} deg "
          f"(margin {df.margin_deg.median():.1f} deg, neural is 36.1)")
    print()
    print(f"  false alarms in the test group: {fa} in {test_hours:.2f} h")
    if fa:
        print(f"  false-alarm rate {fa / test_hours:.3f}/h "
              f"against a budget of {a.budget}/h")
    else:
        print(f"  zero false alarms. With {test_hours:.2f} h of held-out healthy")
        print(f"  recording, the 95% upper bound on the true rate is "
              f"{bound:.2f}/h.")
        if bound > a.budget:
            print(f"  That is ABOVE the {a.budget}/h budget, so this does not yet")
            print(f"  show the monitor meets it. {needed_hours:.0f} h of held-out")
            print(f"  healthy recording would; you have {test_hours:.2f} h.")
            short = needed_hours - test_hours
            print(f"  That is about {short * 3600 / 300:.0f} more five-minute "
                  f"healthy sessions, or {short:.0f} more hours.")
        else:
            print(f"  That is within the {a.budget}/h budget.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
