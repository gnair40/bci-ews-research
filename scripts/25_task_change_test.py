#!/usr/bin/env python3
"""
Does the monitor confuse "the user is doing something else" with "something broke"?

WHY THIS IS THE TEST THAT MATTERS FOR DEPLOYMENT
------------------------------------------------
A monitor that fires whenever a person switches from a typing app to browsing
the web is worse than no monitor: it trains its user to ignore it. No accuracy
number captures this, because in a corpus of injected faults the task never
changes.

This dataset happens to contain the exact control needed. On two days T11 did
the structured cursor task AND something completely different, on the same day,
with the same array:

    day 658   circleOfCircles   vs   free personal use (web browsing)
    day 665   circleOfCircles   vs   fitts (random targets)

Nothing is wrong with the recording in either case. If risk rises anyway, the
monitor is measuring behaviour rather than hardware.

Phase 1-2 already found the OLD indicator was essentially task-invariant --
8.4% difference between the cursor task and web browsing, against a threefold
range across the record. That was reported as evidence the indicator tracked the
recording rather than the task. The question here is the reverse and equally
important: does the NEW monitor over-react to task instead?

THREE REFERENCE POINTS, SO THE ANSWER IS INTERPRETABLE
------------------------------------------------------
    same task, healthy     what normal looks like       -> risk should be low
    DIFFERENT task, healthy the thing under test        -> ?
    same task, injected fault  what a real fault looks like -> risk should be high

The question is which of the two extremes the middle row resembles.

Usage: python3 scripts/25_task_change_test.py
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

WINDOW_BINS = 1500
STEP_BINS = 250

PAIRS = [
    (658, "T11/day_658/block_5", "T11/day_658/block_7",
     ["T11[personal_use]/day_658/block_8", "T11[personal_use]/day_658/block_9"],
     "free personal use (web browsing)"),
    (665, "T11/day_665/block_6", "T11/day_665/block_7",
     ["T11[random_targets]/day_665/block_8", "T11[random_targets]/day_665/block_9"],
     "fitts (random targets)"),
]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def main() -> int:
    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    inj = _load("injector", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")

    ds = loader.load_dataset(participant="T11", load_neural=True, verbose=False)
    _, episodes = inj.load_plan("T11")

    def feats(bid):
        X = ds.neural[bid]
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        return X, starts, det.window_features(X, starts, WINDOW_BINS)

    print("Does a task change look like a fault?\n")
    rows = []
    for day, fit_block, held_block, other_blocks, other_name in PAIRS:
        if fit_block not in ds.neural or held_block not in ds.neural:
            print(f"  day {day}: blocks missing, skipping"); continue

        _, _, Hfit = feats(fit_block)
        _, _, Hheld = feats(held_block)

        for name, D in (("decoder_guard", guard.DecoderGuard()),
                        ("mean_activity", det.MeanActivity()),
                        ("robust_dispersion", det.RobustDispersion())):
            D.fit(Hfit)
            same = float(np.median(D.score(Hheld)))

            others = []
            for ob in other_blocks:
                if ob in ds.neural:
                    _, _, Ho = feats(ob)
                    others.append(float(np.median(D.score(Ho))))
            diff = float(np.mean(others)) if others else np.nan

            # A real fault on the SAME task, for scale. Crossing severity,
            # medium rate, taken from the locked plan rather than improvised.
            faulted = []
            for e in episodes:
                if (e.block_id == held_block and e.severity_label == "crossing"
                        and e.rate_label == "medium"):
                    X = ds.neural[held_block]
                    Y, _ = inj.apply_episode(X, e)
                    starts = np.arange(0, Y.shape[0] - WINDOW_BINS + 1, STEP_BINS)
                    Fy = det.window_features(Y, starts, WINDOW_BINS)
                    post = starts >= e.onset_bin
                    if post.sum() >= 4:
                        faulted.append(float(np.median(D.score(Fy)[post])))
            fault = float(np.mean(faulted)) if faulted else np.nan

            rows.append({"day": day, "other_task": other_name, "detector": name,
                         "same_task": same, "different_task": diff, "real_fault": fault})

    df = pd.DataFrame(rows)
    for day, sub in df.groupby("day"):
        other = sub.other_task.iloc[0]
        print(f"Day {day} — cursor task vs {other}")
        print(f"  {'detector':<20}{'same task':>11}{'diff task':>11}"
              f"{'real fault':>12}   verdict")
        for _, r in sub.iterrows():
            span = r.real_fault - r.same_task
            # Where does the task change sit on the line from healthy to broken?
            frac = ((r.different_task - r.same_task) / span) if span > 1e-9 else np.nan
            if not np.isfinite(frac):
                v = "—"
            elif frac < 0.25:
                v = "looks healthy  OK"
            elif frac < 0.6:
                v = "ambiguous"
            else:
                v = "looks like a FAULT  <-- would false-alarm"
            print(f"  {r.detector:<20}{r.same_task:>11.2f}{r.different_task:>11.2f}"
                  f"{r.real_fault:>12.2f}   {v}")
        print()

    print("Reading this: the middle column is a healthy recording of a different")
    print("activity. The closer it sits to the right column, the more the monitor")
    print("is measuring what the person is DOING rather than what the hardware is.")
    print("A monitor that cannot tell those apart alarms every time the user")
    print("switches app, and users stop believing it.")

    df.to_csv(OUT / "task_change_test.csv", index=False)
    print(f"\nwrote {OUT/'task_change_test.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
