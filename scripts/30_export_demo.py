#!/usr/bin/env python3
"""
Export a few real episodes for the live demonstration.

WHAT THE DEMO HAS TO SHOW, INCLUDING THE PART THAT DOES NOT WORK
---------------------------------------------------------------
The obvious demo replays a fault, shows the monitor turning red before
performance falls, and stops there. That demo would be dishonest: this project
measured that at any usable false-alarm rate the monitor detects about 1% of
faults, and a viewer shown only a success would leave with a false impression.

So three episodes are exported, and the demo shows all three:

    a fault the monitor catches     -- what working looks like
    a fault it misses               -- the common case, not the exception
    a healthy recording             -- where it raises a false alarm anyway

Same monitor, same threshold, same session. The viewer sees the tradeoff rather
than being told about it.

Everything is real: real recorded neural data, the real frozen decoder, the real
monitor, and onsets from the locked injection plan. Nothing is staged.

Usage: python3 scripts/30_export_demo.py
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
WINDOW_BINS, STEP_BINS, BIN_S = 1500, 250, 0.02


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def main() -> int:
    inj = _load("injector", "17_fault_injector.py")
    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    rd = _load("refdec", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")
    harness = _load("harness", "20_evaluation_harness.py")

    dz = np.load(OUT / "reference_decoder.npz")
    dec = (dz["W"], dz["mean"], dz["std"])
    meta = json.loads((OUT / "reference_decoder.json").read_text())
    plan, episodes = inj.load_plan("T11")
    ds = loader.load_dataset(participant="T11", load_neural=True, verbose=False)
    trials = pd.read_csv(OUT / "trials.csv")

    # Fit the monitor exactly as the benchmark did: healthy windows only.
    Hs = []
    for bid in meta["train_blocks"]:
        if bid not in ds.neural:
            continue
        X = ds.neural[bid]
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        Hs.append(det.window_features(X, st, WINDOW_BINS))
    G = guard.DecoderGuard().fit(np.vstack(Hs))

    scored = pd.read_csv(OUT / "episode_scores_local.csv")
    g = scored[scored.detector == "decoder_guard"]

    # Choose the three episodes against the REAL operating point, not by eye and
    # not by a relative rise. An earlier version picked episodes whose risk rose
    # threefold above their own baseline, which sounds reasonable and selected
    # three episodes that never came near the actual WARN threshold of 50.5 --
    # so the "caught" case was not caught and the "false alarm" case raised no
    # alarm. The demo has to use the threshold the benchmark actually used.
    summary = json.loads((OUT / "harness_summary_local.json").read_text())
    t_warn = float(summary["decoder_guard"]["operating_point"])
    print(f"  selecting against the benchmark's own WARN threshold: {t_warn:.1f}\n")

    # FOUR roles, because three was not enough to be honest.
    #
    # An earlier version had a single "caught" case labelled as reporting the
    # fault BEFORE performance collapsed. The episode it chose warned 35 seconds
    # AFTER performance had already crossed the degradation threshold, so the
    # label asserted a capability the episode did not show.
    #
    # Checking the whole distribution: of 132 detected faults on T11, 48% are
    # warned before performance drops and 52% after, with a median lead of
    # exactly 0 seconds. Detection and early warning are different things here,
    # and a demo with one "caught" tab cannot express that. So both appear.
    want = {}
    for _, r in g.iterrows():
        y = np.fromstring(r.scores, sep=",")
        ow = int(r.onset_w)
        if len(y) <= ow:
            continue
        fired = np.flatnonzero(y > t_warn)
        fired = fired[fired >= ow]
        first = int(fired[0]) if len(fired) else None
        if r.crossed:
            cw = int(r.crossing_w)
            if cw <= ow or len(y) < cw:
                continue
            if first is None:
                want.setdefault("missed", r.episode_id)
            elif (cw - first) * 5 >= 40:
                want.setdefault("early", r.episode_id)
            elif (cw - first) * 5 <= -20:
                want.setdefault("late", r.episode_id)
        elif first is not None:
            want.setdefault("false_alarm", r.episode_id)
        if len(want) == 4:
            break

    by_id = {e.episode_id: e for e in episodes}
    out = {"generated": "scripts/30_export_demo.py", "participant": "T11",
           "window_s": WINDOW_BINS * BIN_S, "step_s": STEP_BINS * BIN_S,
           "threshold_deg": harness.THRESHOLD_DEG,
           "warn_threshold": round(t_warn, 2),
           "operating_point_note": (
               "Chosen on validation data to meet the false-alarm budget, then "
               "frozen. At this point the monitor detects 143 of 586 faults and "
               "raises 3.41 false alarms per hour against a 0.1/h budget."),
           "lead_time_distribution": (
               "Of the 132 detected faults on T11, 48% are warned before "
               "performance drops and 52% after. Median lead: 0 s."),
           "episodes": []}

    for role, eid in want.items():
        ep = by_id[eid]
        X = ds.neural[ep.block_id]
        kin = ds.kinematics[ep.block_id]
        unit, ok_dir = rd.intended_direction(kin)
        ok = ok_dir & rd.in_trial_mask(trials, ep.block_id, X.shape[0])
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        Y, _ = inj.apply_episode(X, ep)
        F = det.window_features(Y, starts, WINDOW_BINS)
        onset_w = int(np.searchsorted(starts, ep.onset_bin))

        pre = F[:onset_w]
        if len(pre) >= 6:
            G.recenter(pre)
        con = G.contributions(F)
        perf = harness.window_performance(Y, starts, WINDOW_BINS, ok, unit, dec)

        base = float(np.nanmedian(perf[:onset_w])) if onset_w > 2 else float("nan")
        out["episodes"].append({
            "role": role,
            "id": ep.episode_id,
            "block": ep.block_id,
            "mode": ep.mode,
            "severity": ep.severity_label,
            "rate": ep.rate_label,
            "onset_window": onset_w,
            "onset_s": round(ep.onset_bin * BIN_S, 1),
            "risk": [round(float(v), 3) for v in con["risk"]],
            "cause": con["attribution"],
            "performance_deg": [None if not np.isfinite(v) else round(float(v), 2)
                                for v in perf],
            "baseline_deg": None if not np.isfinite(base) else round(base, 2),
            "components": {k: [round(float(x), 3) for x in v]
                           for k, v in con["components"].items()},
        })
        print(f"  {role:<8} {ep.episode_id}  {ep.mode:<18} "
              f"{len(starts)} windows, onset at window {onset_w}")

    dest = OUT / "demo_episodes.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest}  ({dest.stat().st_size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
