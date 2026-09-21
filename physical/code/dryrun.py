#!/usr/bin/env python3
"""
dryrun.py — build fake recordings so the analysis can be tested before the
hardware exists.

=============================================================================
WHY THIS EXISTS
=============================================================================
The analysis chain has five scripts in it. Finding out that the fourth one
crashes — or, far worse, quietly produces a wrong number — during the week the
sessions are being recorded is an expensive way to discover it.

This script manufactures recordings in exactly the format the real apparatus
produces, so the whole chain can be run end to end today, on a laptop, with no
camera and no box. Every script downstream can then be checked against answers
that are known in advance, because this script chose them.

=============================================================================
WHAT IT IS NOT
=============================================================================
**It is not data, and no number produced from it belongs in the write-up.**

The fake recordings come from a formula chosen by the person writing the
analysis. A monitor tested only on those is being tested against its author's
own assumptions about what degradation looks like — which is precisely the
criticism experiment P-5 exists to answer for the real apparatus.

To make that impossible to get wrong by accident, everything is written under
`physical/data/dryrun/`, never into `physical/data/raw/`, and the analysis has
to be pointed at it deliberately.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/dryrun.py --healthy 12 --degraded 8

then run the analysis against it:

    python3 physical/code/make_session_table.py \\
        --raw physical/data/dryrun/raw --tag _dryrun

=============================================================================
WHAT IT PRODUCES
=============================================================================
    physical/data/dryrun/raw/s<session>_b<block>/{capture.npy,
                                                  capture_t.npy,
                                                  stim.csv,
                                                  session.json}
    physical/data/dryrun/onsets/...   the plans, drawn the same way

The fake apparatus has the same 384 channels, the same 50 frames per second,
and degradations of the same four kinds. What it does not have is optics, a
camera sensor, a room that warms up overnight, or anything else real.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DRY = HERE.parent / "data" / "dryrun"
FPS = 50
FAULTS = ["RATE_LOSS", "CHANNEL_DROPOUT", "GAIN_DRIFT", "GEOMETRY_ROTATION"]


def make_one(folder: Path, plan: dict, pref: np.ndarray, depth: float,
             noise: float, drift: float, rng) -> None:
    n, nch = plan["frames"], len(pref)
    heading = np.repeat(rng.uniform(0, 2 * np.pi, n // 100 + 1), 100)[:n]

    base = 128.0
    X = base + depth * base * np.cos(heading[:, None] - pref[None, :])
    # A slow warming of the whole array, which is what an evening in a closed
    # box actually does. Present in healthy sessions too -- that is the point:
    # a monitor must not call ordinary drift a fault.
    X *= (1.0 + drift * np.linspace(0, 1, n))[:, None]
    X += rng.normal(0, noise, X.shape)

    onset, sev, kind = plan["onset_frame"], plan["severity"], plan["fault_type"]
    if onset is not None:
        if kind == "RATE_LOSS":
            X[onset:] *= (1.0 - 0.5 * sev)
        elif kind == "CHANNEL_DROPOUT":
            dead = rng.choice(nch, int(nch * 0.3 * sev), replace=False)
            X[onset:, dead] = base * 0.01
        elif kind == "GAIN_DRIFT":
            X[onset:] *= np.clip(1.0 + sev * rng.normal(0, 0.5, nch), 0.05, None)
        elif kind == "GEOMETRY_ROTATION":
            X[onset:] = np.roll(X[onset:], int(round(sev * nch * 0.06)), axis=1)
        elif kind == "UNDESIGNED":
            # Several things at once, mildly, which is what a real physical
            # fault does -- a loosened connector dims the image, shifts it, and
            # adds noise together. The first version of this file applied no
            # degradation at all to an UNDESIGNED session, so the fake P-5
            # recordings were healthy ones wearing a fault label, and the fake
            # P-5 detection rate came out at 0%. That is what a dry run is for.
            X[onset:] *= (1.0 - 0.15 * sev)
            X[onset:] *= np.clip(1.0 + 0.3 * sev * rng.normal(0, 0.5, nch),
                                 0.05, None)
            X[onset:] = np.roll(X[onset:], int(round(sev * nch * 0.02)), axis=1)
            X[onset:] += rng.normal(0, 0.5 * sev, X[onset:].shape)

    folder.mkdir(parents=True, exist_ok=True)
    np.save(folder / "capture.npy", X.astype(np.float32))
    t0 = time.time()
    t = t0 + np.arange(n) / FPS
    np.save(folder / "capture_t.npy", t)
    with (folder / "stim.csv").open("w") as f:
        f.write("frame,t_unix,heading_rad,trial,fault_active\n")
        for i in range(n):
            f.write(f"{i},{t[i] - 0.004:.6f},{heading[i]:.6f},{i // 100},"
                    f"{int(onset is not None and i >= onset)}\n")
    (folder / "session.json").write_text(json.dumps(
        {"session": plan["session"], "block": plan["block"],
         "kind": plan.get("kind", "experiment"), "healthy": plan["healthy"],
         "SYNTHETIC": True,
         "warning": "Made by dryrun.py. Not data. Not for the write-up."},
        indent=2))
    # A P-5 session keeps its onset beside the recording rather than in the
    # onsets folder, because it was noted afterwards rather than drawn.
    if plan.get("kind") == "undesigned":
        (folder / "observed_onset.json").write_text(json.dumps(
            {**{k: v for k, v in plan.items() if k != "kind"},
             "onset_provenance": "stopwatch", "SYNTHETIC": True}, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--healthy", type=int, default=12)
    ap.add_argument("--degraded", type=int, default=8)
    ap.add_argument("--undesigned", type=int, default=0,
                    help="P-5 sessions: fault caused by hand, onset noted "
                         "afterwards rather than drawn")
    ap.add_argument("--orphans", type=int, default=0,
                    help="P-5 sessions with NO noted onset, to check the "
                         "analysis refuses to score them")
    ap.add_argument("--frames", type=int, default=6000, help="6000 = 2 minutes")
    ap.add_argument("--channels", type=int, default=384)
    ap.add_argument("--depth", type=float, default=0.004,
                    help="how strongly direction shows in the channels")
    ap.add_argument("--noise", type=float, default=1.0)
    ap.add_argument("--drift", type=float, default=0.02,
                    help="slow warming across a session, healthy or not")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--clean", action="store_true", help="delete previous fakes first")
    a = ap.parse_args()

    if a.clean and DRY.exists():
        shutil.rmtree(DRY)
    raw, onsets = DRY / "raw", DRY / "onsets"
    raw.mkdir(parents=True, exist_ok=True)
    onsets.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(a.seed)
    pref = rng.uniform(0, 2 * np.pi, a.channels)
    # Saved where bench.py will look for it, so the bench checks can be
    # exercised on the fakes too -- and kept out of physical/data/, so it can
    # never be mistaken for the real apparatus's channel definitions.
    np.save(DRY / "preferred_directions.npy", pref)

    plans = []
    for i in range(a.healthy):
        plans.append({"session": 1, "block": i + 1, "healthy": True,
                      "fault_type": None, "severity": 0.0,
                      "onset_frame": None, "onset_seconds": None,
                      "frames": a.frames, "fps": FPS})
    for i in range(a.degraded):
        onset = int(rng.integers(int(a.frames * 0.2), int(a.frames * 0.8)))
        plans.append({"session": 2, "block": i + 1, "healthy": False,
                      "fault_type": FAULTS[i % len(FAULTS)],
                      "severity": float(rng.choice([0.25, 0.5, 1.0])),
                      "onset_frame": onset,
                      "onset_seconds": round(onset / FPS, 2),
                      "frames": a.frames, "fps": FPS})

    # P-5: caused by hand, onset written down afterwards. Its plan lives beside
    # the recording, not in the onsets folder, so the two provenances cannot be
    # confused for one another even on fake data.
    undesigned = []
    for i in range(a.undesigned + a.orphans):
        onset = int(rng.integers(int(a.frames * 0.2), int(a.frames * 0.8)))
        undesigned.append({"session": 3, "block": i + 1, "healthy": False,
                           "kind": "undesigned",
                           "fault_type": "UNDESIGNED",
                           "severity": float(rng.choice([0.5, 1.0])),
                           "onset_frame": onset,
                           "onset_seconds": round(onset / FPS, 2),
                           "frames": a.frames, "fps": FPS,
                           # The last `--orphans` of them get no noted onset.
                           "_note_it": i < a.undesigned})

    for p in plans:
        name = f"s{p['session']}_b{p['block']}"
        (onsets / f"{name}.json").write_text(json.dumps(p, indent=2))
        make_one(raw / name, p, pref, a.depth, a.noise, a.drift, rng)

    for p in undesigned:
        name = f"s{p['session']}_b{p['block']}"
        note_it = p.pop("_note_it")
        make_one(raw / name, p if note_it else {**p, "kind": "undesigned"},
                 pref, a.depth, a.noise, a.drift, rng)
        if not note_it:
            (raw / name / "observed_onset.json").unlink(missing_ok=True)

    print(f"wrote {len(plans) + len(undesigned)} fake recordings to {raw}")
    print(f"      {a.healthy} healthy, {a.degraded} degraded, "
          f"{a.undesigned} undesigned, {a.orphans} undesigned with no noted "
          f"onset, {a.frames / FPS / 60:.1f} minutes each")
    print()
    print("These are NOT data. Run the analysis against them like this:")
    print(f"    python3 physical/code/make_session_table.py \\")
    print(f"        --raw {raw.relative_to(HERE.parent.parent)} --tag _dryrun")
    print()
    print("and delete them when you are done:  rm -rf physical/data/dryrun")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
