#!/usr/bin/env python3
"""
67_rig_format_check.py
======================
Can this pipeline accept a THIRD participant that is not a person?

=============================================================================
  READ THIS BEFORE RUNNING. THE DATA THIS SCRIPT GENERATES IS NOT DATA.
=============================================================================

This script fabricates a synthetic recording. Its ONLY legitimate use is to
answer a software question -- "does the pipeline load, fit and score a
participant it has never seen?" -- before $115 and two weekends are spent on
hardware that turns out to emit files nothing can read.

NO SCIENTIFIC CLAIM MAY EVER BE DERIVED FROM ITS OUTPUT.

The reason is the project's own rule, from PROJECT_DEFINITION.md 5.5:

    "The perturbation may be simulated. The response to it may not.
     Simulating the thing you are trying to detect is circular: you would be
     measuring your own generative assumptions."

An angular error, an AUC or an autocorrelation computed on this fixture is a
measurement of the equations below and nothing else. To keep that impossible
to forget, the fixture is written to a directory named `_FIXTURE_NOT_DATA`,
every file carries a marker field, and the script refuses to write anywhere
near `data/raw_rig/`, which is where real rig recordings will go.

WHAT IT ACTUALLY CHECKS
-----------------------
1. Can a non-"T<number>" participant even be represented? (Answer at the time
   of writing: NO -- see FINDING 1 below.)
2. Does `03_load_dataset.py` read a block written in the MINDFUL .mat layout
   by something other than the MINDFUL authors?
3. Does the frozen reference decoder fit against it, with no code change?
4. Which fields are genuinely mandatory, as opposed to merely present in the
   deposit?

FINDING 1, recorded 6 September 2026
------------------------------------
`03_load_dataset.py` matches participant folders with

    PARTICIPANT_RE = re.compile(r"^(T\\d+)(\\(.*\\))?$", re.IGNORECASE)

so a folder named `RIG` is invisible to the loader and the rig's recordings
would silently not exist. The two ways out are not equal:

  * Name the rig participant `T99`. Zero code change -- and a bad idea. This
    project went to the trouble of a dedicated commit (7102ff6) to say that
    "participant" never means a recruited person. Calling a cardboard box
    "participant T99" walks that straight back, in the one place a judge is
    most likely to look.

  * Widen the pattern to admit an explicitly non-human name. One line, and it
    keeps the human/instrument distinction visible in the data itself.

The second was taken. See `git log` for the change to `03_load_dataset.py`.

WHAT THE RIG WILL WRITE
-----------------------
Per block, a folder `RIG/day_<session>/block_<n>/` holding three files, which
is exactly the layout the deposit uses:

  data.mat   nctx        (n_bins x 384)  region-mean intensities
  info.mat   cursorPos   (n_bins x 2)    always (0, 0)
             targetPos   (n_bins x 2)    (cos heading, sin heading)
             angleErrorPerTrial, trialSuccess, percentCorrect, ...
  task.mat   startStops  (n_trials x 2)  MATLAB 1-BASED, one row per heading
             name        the task label

Setting cursorPos to the origin and targetPos to the heading unit vector makes
`intended_direction()` return the heading exactly, with no change to
`18_reference_decoder.py`. Because the rig writes .mat files directly, NO NEW
LOADER IS NEEDED -- which is a simpler answer than research/RIG_PROCEDURE.md
originally gave, and that document has been corrected.

Usage:
    python3 scripts/67_rig_format_check.py            # build fixture and check
    python3 scripts/67_rig_format_check.py --keep     # leave the fixture on disk
"""
from __future__ import annotations

import argparse
import shutil
import sys
from importlib import import_module
from pathlib import Path

import numpy as np
from scipy.io import savemat

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

# Deliberately NOT data/raw_rig/ -- that name is reserved for real recordings.
FIXTURE = REPO / "data" / "_FIXTURE_NOT_DATA"
FORBIDDEN = (REPO / "data" / "raw", REPO / "data" / "raw_rig")

N_COLS, N_ROWS = 24, 16
N_CHAN = N_COLS * N_ROWS          # 384, matching T11
BIN_S = 0.02
HOLD_BINS = 100                   # one "trial" per heading, 2 s at 50 Hz
SEED = 20260826                   # the project's master seed


def make_block(n_bins: int, rng: np.random.Generator,
               pref: np.ndarray) -> tuple[np.ndarray, dict, dict]:
    """One synthetic block. The physics here is a placeholder, not a model.

    A real rig replaces every line of this with photons. The only thing that
    must survive is the SHAPE of what comes out.
    """
    n_trials = n_bins // HOLD_BINS
    headings = rng.uniform(0, 2 * np.pi, n_trials)
    per_bin = np.repeat(headings, HOLD_BINS)[:n_bins]

    # Cosine tuning + noise + a slow multiplicative drift. Placeholder values.
    clean = 0.5 * (1 + np.cos(per_bin[:, None] - pref[None, :]))
    drift = 1.0 + 0.05 * np.sin(np.linspace(0, 2 * np.pi, n_bins))[:, None]
    nctx = (clean * drift * 40.0 + rng.normal(0, 12.0, (n_bins, N_CHAN)))
    nctx = np.clip(nctx, 0, None).astype(np.float32)

    cursor = np.zeros((n_bins, 2), dtype=np.float32)
    target = np.stack([np.cos(per_bin), np.sin(per_bin)], axis=1).astype(np.float32)

    starts = np.arange(n_trials) * HOLD_BINS + 1        # MATLAB is 1-based
    stops = starts + HOLD_BINS - 1
    start_stops = np.stack([starts, stops], axis=1).astype(np.float64)

    data = {"nctx": nctx, "FIXTURE_NOT_DATA": "synthetic; no claim may cite this"}
    info = {
        "cursorPos": cursor, "targetPos": target,
        "angleErrorPerTrial": rng.uniform(40, 70, n_trials).astype(np.float64),
        "trialSuccess": np.ones(n_trials, dtype=bool),
        "timeToTarget": rng.uniform(2, 5, n_trials).astype(np.float64),
        "pathEfficiency": rng.uniform(0.5, 0.9, n_trials).astype(np.float64),
        "orthChanges": rng.integers(0, 4, n_trials).astype(np.float64),
        "percentCorrect": 95.0,
        "FIXTURE_NOT_DATA": "synthetic; no claim may cite this",
    }
    task = {
        "startStops": start_stops,
        "name": "rigCosineField",
        "excludeTrials": np.zeros(n_trials, dtype=bool),
        "useClick": np.zeros(n_trials, dtype=bool),
        "FIXTURE_NOT_DATA": "synthetic; no claim may cite this",
    }
    return nctx, info, task, data


def build_fixture(n_days: int = 5, n_blocks: int = 2, n_bins: int = 15000) -> None:
    for f in FORBIDDEN:
        if FIXTURE == f or f in FIXTURE.parents:
            raise SystemExit(f"refusing to write a fixture inside {f}")
    if FIXTURE.exists():
        shutil.rmtree(FIXTURE)
    rng = np.random.default_rng(SEED)
    pref = rng.uniform(0, 2 * np.pi, N_CHAN)
    for d in range(n_days):
        for b in range(1, n_blocks + 1):
            bd = FIXTURE / "RIG" / f"day_{d + 1}" / f"block_{b}"
            bd.mkdir(parents=True, exist_ok=True)
            _, info, task, data = make_block(n_bins, rng, pref)
            savemat(bd / "data.mat", data, do_compression=True)
            savemat(bd / "info.mat", info, do_compression=True)
            savemat(bd / "task.mat", task, do_compression=True)
    (FIXTURE / "README.md").write_text(
        "# NOT DATA\n\n"
        "Synthetic fixture generated by `scripts/67_rig_format_check.py` to "
        "test whether the pipeline accepts a new participant. It is not a "
        "recording, it is not a simulation of cortex, and **no claim in this "
        "project may cite it**. Delete it freely; it regenerates in seconds.\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true",
                    help="leave the fixture on disk for inspection")
    a = ap.parse_args()

    print(__doc__.split("WHAT IT ACTUALLY CHECKS")[0].strip()[:0] or "", end="")
    print("=" * 74)
    print("  RIG FORMAT CHECK -- the fixture below is NOT DATA and no claim")
    print("  in this project may cite any number it produces.")
    print("=" * 74)

    print("\n1. Building a synthetic fixture in the MINDFUL .mat layout ...")
    build_fixture()
    n_files = len(list(FIXTURE.rglob("*.mat")))
    print(f"   wrote {n_files} .mat files under {FIXTURE.relative_to(REPO)}")

    print("\n2. Can the existing loader see a participant called RIG?")
    loader = import_module("03_load_dataset")
    ok_regex = bool(loader.PARTICIPANT_RE.match("RIG"))
    print(f"   PARTICIPANT_RE matches 'RIG': {ok_regex}")
    if not ok_regex:
        print("   FAIL -- the rig's recordings would be silently invisible.")
        print("   See FINDING 1 in this file's docstring.")
        return 1

    print("\n3. Loading the fixture with the UNMODIFIED archived loader ...")
    ds = loader.load_dataset(FIXTURE, load_neural=True, verbose=False)
    print(f"   blocks : {len(ds.blocks)}")
    print(f"   trials : {len(ds.trials)}")
    print(f"   neural : {len(ds.neural)} matrices")
    if ds.problems:
        print(f"   problems reported by the loader: {len(ds.problems)}")
        for p in ds.problems[:5]:
            print(f"     - {p}")
    bad = []
    if len(ds.blocks) == 0:
        bad.append("no blocks loaded")
    if len(ds.neural) == 0:
        bad.append("no neural matrices loaded")
    else:
        shape = next(iter(ds.neural.values())).shape
        print(f"   first neural matrix shape: {shape}")
        if shape[1] != N_CHAN:
            bad.append(f"expected {N_CHAN} features, got {shape[1]}")

    print("\n4. Are the fields the reference decoder needs present?")
    bid = ds.blocks.iloc[0]["block_id"] if len(ds.blocks) else None
    if bid is not None:
        kin = ds.kinematics.get(bid, {})
        for f in ("cursorPos", "targetPos"):
            present = f in kin
            print(f"   kinematics['{f}'] present: {present}")
            if not present:
                bad.append(f"missing kinematic field {f}")
        if "cursorPos" in kin and "targetPos" in kin:
            dec = import_module("18_reference_decoder")
            unit, ok = dec.intended_direction(kin)
            print(f"   intended_direction() -> {int(ok.sum()):,} scorable bins "
                  f"of {len(ok):,}")
            if ok.sum() == 0:
                bad.append("intended_direction() found no scorable bins")
            else:
                norms = np.linalg.norm(unit[ok], axis=1)
                print(f"   heading unit-vector norms: "
                      f"min {norms.min():.4f}, max {norms.max():.4f}")

    print("\n" + "=" * 74)
    if bad:
        print("FAIL")
        for b in bad:
            print(f"  - {b}")
    else:
        print("PASS -- the pipeline accepts a non-human participant unchanged.")
        print("  No new loader is needed: the rig writes .mat files directly.")
    print("=" * 74)

    if not a.keep:
        shutil.rmtree(FIXTURE)
        print(f"\nfixture deleted (use --keep to retain it)")
    else:
        print(f"\nfixture kept at {FIXTURE.relative_to(REPO)} -- NOT DATA")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
