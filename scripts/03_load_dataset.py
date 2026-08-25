#!/usr/bin/env python3
"""
03_load_dataset.py
==================
Load the nested MINDFUL .mat files into tidy pandas tables.

WHAT THIS SCRIPT IS FOR
-----------------------
The dataset is stored the way MATLAB code wants to read it: a deep folder tree
of small .mat files, one folder per block, with neural data and behavioural
data in separate files. That is awkward for analysis in Python.

This script is a Python translation of the authors' own loader
(`utils/ConcatSavedSessionsData.m` in github.com/ewinapun/MINDFUL). It walks the
tree and produces two flat tables plus the neural arrays:

  trials  -- ONE ROW PER TRIAL. Columns identify the participant, trial day,
             block and trial, and carry the behavioural performance measures
             (angle error, success, time to target, path efficiency, ...).
  blocks  -- ONE ROW PER BLOCK. Bookkeeping: how many bins, how many trials,
             which task, how many neural features.
  neural  -- the neural feature matrices, keyed by block.

"Tidy" is a specific idea, not a compliment: each row is one observation, each
column is one variable. Nearly every pandas operation assumes this shape, so
converting once at the start saves pain everywhere later.

WHAT THIS SCRIPT DELIBERATELY DOES *NOT* DO
-------------------------------------------
It does not z-score, smooth, detrend, exclude outlier trials, or align neural
data to behaviour. Those are not "loading" -- they are *preprocessing*, and
every one of them is a scientific decision that changes what your results mean.
The authors' MATLAB loader applies a rolling z-score by default; this one does
not, on purpose, so that the raw values are visible first.

Excluded trials are FLAGGED (`excluded` column), never dropped. You decide.

A SUBTLETY THAT MATTERS: 1-BASED VS 0-BASED INDEXING
----------------------------------------------------
MATLAB numbers the first element of an array `1`. Python numbers it `0`. The
`startStops` variable holds MATLAB indices, so a trial recorded as starting at
bin 1 actually starts at Python index 0. Getting this wrong shifts every trial
by one bin -- a small error that silently corrupts any neural/behavioural
alignment.

This script converts to Python convention and keeps BOTH versions
(`start_bin_matlab` / `start_bin`) so the conversion is auditable rather than
hidden. See `--index-base` if the assumption turns out to be wrong.

HOW TO RUN
----------
    python3 scripts/03_load_dataset.py                       # load data/raw
    python3 scripts/03_load_dataset.py --root PATH           # load elsewhere
    python3 scripts/03_load_dataset.py --save                # write CSVs to data/processed
    python3 scripts/03_load_dataset.py --participant T5      # just one participant

USE IT FROM OTHER CODE
----------------------
    from importlib import import_module
    loader = import_module("03_load_dataset")
    ds = loader.load_dataset(Path("data/raw"))
    ds.trials.head()
"""

from __future__ import annotations

import argparse
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import scipy.io as sio
except ImportError:
    sys.exit("scipy is required. Install it with:  pip install -r requirements.txt")
try:
    import h5py
except ImportError:
    h5py = None


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# FIELD LAYOUT -- confirmed against the deposit's own README.md and against the
# files themselves. Note this CORRECTS an earlier guess: startStops,
# excludeTrials and moveDirVect live in task.mat, NOT data.mat.
# ---------------------------------------------------------------------------

# data.mat -- neural features and kinematics, one row per 20 ms bin.
#   nctx       [nStep x nChan] threshold crossings (non-causal, RMS < -3.5)
#   spikePower [nStep x nChan] spike band power (250-5000 Hz)  -- T11 only
#   labels     [nStep x 2]     inferred cursor-to-target vector [x, y]
#   cursorVel  [nStep x 2]     decoded velocity out of the decoder [x, y]
NEURAL_PRIMARY = "nctx"
NEURAL_SECONDARY = "spikePower"
KINEMATIC_NAMES = ("labels", "cursorVel")

# task.mat -- per-trial task structure and block metadata.
TASK_TRIAL_FIELDS = ("excludeTrials", "useClick", "moveDirVect")
TASK_SCALAR_FIELDS = ("name", "nPointsPerBlock")

# info.mat -- performance. Per-trial measures:
TRIAL_METRICS = (
    "angleErrorPerTrial",   # MEDIAN angular error for the trial, degrees
    "trialSuccess",         # bool: target acquired
    "timeToTarget",         # seconds
    "pathEfficiency",       # 0-1, higher is more direct
    "orthChanges",          # count of orthogonal direction changes
)
# info.mat -- per-bin measures (same length as the neural matrix):
STEP_METRICS = ("angleError", "targetPos", "cursorPos", "magEst", "avgOutliers")
# info.mat -- per-block scalars:
BLOCK_METRICS = ("percentCorrect",)

# Folder-name patterns. 'day_37' -> 37 ; 'block_2' -> 2
DAY_RE = re.compile(r"^day[_-]?(\d+)$", re.IGNORECASE)
BLOCK_RE = re.compile(r"^block[_-]?(\d+)$", re.IGNORECASE)
# Participant folders are 'T5' and 'T11'. The deposit also has a folder named
# 'T11(additional)' holding two extra reference tasks (personal use, random
# targets) for the SAME participant, so the pattern allows an optional suffix
# and the suffix is recorded separately rather than being lost.
PARTICIPANT_RE = re.compile(r"^(T\d+)(\(.*\))?$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# RESULT CONTAINER
# ---------------------------------------------------------------------------

@dataclass
class Dataset:
    """Everything the loader produces, in one object."""
    trials: pd.DataFrame                       # one row per trial
    blocks: pd.DataFrame                       # one row per block
    neural: dict[str, np.ndarray] = field(default_factory=dict)   # block_id -> (bins, feats)
    kinematics: dict[str, dict] = field(default_factory=dict)     # block_id -> arrays
    problems: list[str] = field(default_factory=list)             # anything suspicious

    def summary(self) -> str:
        lines = [
            f"trials : {len(self.trials):,} rows x {len(self.trials.columns)} columns",
            f"blocks : {len(self.blocks):,} rows x {len(self.blocks.columns)} columns",
            f"neural : {len(self.neural)} block matrices loaded",
        ]
        if self.problems:
            lines.append(f"PROBLEMS FLAGGED: {len(self.problems)} (see .problems)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# READING .mat FILES
# ---------------------------------------------------------------------------

def _is_hdf5(path: Path) -> bool:
    """v7.3 .mat files are HDF5; identify by magic bytes, not by filename."""
    try:
        with path.open("rb") as fh:
            return fh.read(8) == b"\x89HDF\r\n\x1a\n"
    except OSError:
        return False


def read_mat(path: Path) -> dict:
    """
    Read a .mat file into a plain dict, whichever MATLAB format it uses.

    Returns {} and warns if the file cannot be read, rather than crashing --
    one unreadable block should not abort a load of hundreds.
    """
    if not path.exists():
        return {}
    try:
        if _is_hdf5(path):
            if h5py is None:
                warnings.warn(f"{path.name} is v7.3 but h5py is not installed")
                return {}
            out = {}
            with h5py.File(path, "r") as f:
                for key in f.keys():
                    if key.startswith("#"):
                        continue
                    obj = f[key]
                    if isinstance(obj, h5py.Dataset):
                        arr = np.asarray(obj)
                        # MATLAB writes HDF5 transposed relative to how it
                        # displays the matrix, so 2-D arrays come back rotated.
                        out[key] = arr.T if arr.ndim == 2 else arr
            return out
        md = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
        return {k: v for k, v in md.items() if not k.startswith("__")}
    except Exception as exc:                     # noqa: BLE001
        warnings.warn(f"could not read {path}: {exc}")
        return {}


def _as_1d(value) -> np.ndarray:
    """Coerce a MATLAB value into a flat 1-D numpy array."""
    arr = np.atleast_1d(np.asarray(value))
    return arr.ravel()


# ---------------------------------------------------------------------------
# ASSEMBLING ONE BLOCK
# ---------------------------------------------------------------------------

def load_block(block_dir: Path, participant: str, trial_day: int,
               block_num: int, index_base: int,
               problems: list[str], cohort: str = "main") -> tuple[dict, pd.DataFrame, np.ndarray | None, dict]:
    """
    Read one block_<M> folder into (block_row, trial_rows, neural_matrix, kinematics).

    Every consistency check that fails appends a human-readable note to
    `problems` instead of raising. A load that half-fails silently is far more
    dangerous than one that tells you exactly what looked wrong.
    """
    suffix = "" if cohort == "main" else f"[{cohort}]"
    block_id = f"{participant}{suffix}/day_{trial_day}/block_{block_num}"

    data = read_mat(block_dir / "data.mat")
    info = read_mat(block_dir / "info.mat")
    task = read_mat(block_dir / "task.mat")

    # ---- neural features -------------------------------------------------
    # nctx is always present. spikePower exists for T11 but NOT for T5, so the
    # two participants have different feature counts (192 vs 384). That is a
    # property of the dataset, not an error -- but any analysis pooling them
    # must handle it, so it is recorded rather than smoothed over.
    neural = None
    neural_source = None
    if NEURAL_PRIMARY in data:
        neural = np.asarray(data[NEURAL_PRIMARY], dtype=np.float64)
        neural_source = NEURAL_PRIMARY
        if NEURAL_SECONDARY in data:
            sp = np.asarray(data[NEURAL_SECONDARY], dtype=np.float64)
            if sp.ndim == 2 and neural.ndim == 2 and sp.shape[0] == neural.shape[0]:
                neural = np.hstack([neural, sp])
                neural_source = f"{NEURAL_PRIMARY}+{NEURAL_SECONDARY}"
            else:
                problems.append(
                    f"{block_id}: {NEURAL_SECONDARY} shape {sp.shape} does not "
                    f"match {NEURAL_PRIMARY} shape {neural.shape}; not concatenated"
                )
    if neural is None:
        problems.append(f"{block_id}: no '{NEURAL_PRIMARY}' in data.mat; "
                        f"keys present: {sorted(data)}")
    elif neural.ndim != 2:
        problems.append(f"{block_id}: neural array is {neural.ndim}-D, expected 2-D")

    n_bins = int(neural.shape[0]) if neural is not None and neural.ndim == 2 else 0
    n_feats = int(neural.shape[1]) if neural is not None and neural.ndim == 2 else 0

    # ---- trial boundaries ------------------------------------------------
    start_stop = task.get("startStops")
    if start_stop is None:
        problems.append(f"{block_id}: no 'startStops' in task.mat; cannot define trials")
        starts_m = stops_m = np.array([], dtype=int)
    else:
        ss = np.atleast_2d(np.asarray(start_stop))
        # Accept either (n_trials, 2) or (2, n_trials).
        if ss.shape[0] == 2 and ss.shape[1] != 2:
            ss = ss.T
        if ss.ndim != 2 or ss.shape[1] != 2:
            problems.append(f"{block_id}: startStops has shape {ss.shape}, expected (n,2)")
            starts_m = stops_m = np.array([], dtype=int)
        else:
            starts_m = ss[:, 0].astype(np.int64)
            stops_m = ss[:, 1].astype(np.int64)

    n_trials = len(starts_m)

    # Convert MATLAB's 1-based inclusive range to Python's 0-based half-open.
    #   MATLAB  data(start:stop)      includes both ends, first element is 1
    #   Python  data[start:stop]      excludes the end,   first element is 0
    starts_py = starts_m - index_base
    stops_py = stops_m - index_base + 1        # +1 makes the end exclusive

    if n_trials and n_bins:
        if starts_py.min() < 0:
            problems.append(
                f"{block_id}: converted start index {starts_py.min()} is negative. "
                f"startStops may already be 0-based -- try --index-base 0."
            )
        if stops_py.max() > n_bins:
            problems.append(
                f"{block_id}: trial end {stops_py.max()} exceeds the {n_bins} bins "
                f"in the neural matrix."
            )

    # ---- per-trial behavioural metrics -----------------------------------
    trial_cols: dict[str, np.ndarray] = {}
    for key in TRIAL_METRICS:
        if key not in info:
            continue
        vals = _as_1d(info[key])
        if n_trials and len(vals) != n_trials:
            problems.append(
                f"{block_id}: '{key}' has {len(vals)} values but there are "
                f"{n_trials} trials; column left empty for this block"
            )
            continue
        trial_cols[key] = vals

    # excludeTrials and useClick are per-trial and live in task.mat.
    for key in ("excludeTrials", "useClick"):
        raw = task.get(key)
        if raw is None:
            continue
        vals = _as_1d(raw)
        if n_trials and len(vals) == n_trials:
            trial_cols[key] = vals.astype(bool)
        elif n_trials and vals.size == 1:
            # useClick is sometimes a single block-wide flag rather than per trial.
            trial_cols[key] = np.repeat(bool(vals[0]), n_trials)
        elif n_trials:
            problems.append(
                f"{block_id}: '{key}' has {len(vals)} values but {n_trials} trials"
            )

    # ---- build the trial table for this block ----------------------------
    friendly = {
        "angleErrorPerTrial": "angle_error_deg",
        "trialSuccess": "success",
        "timeToTarget": "time_to_target",
        "pathEfficiency": "path_efficiency",
        "orthChanges": "orth_changes",
        "excludeTrials": "excluded",
        "useClick": "used_click",
    }
    trials = pd.DataFrame({
        "participant": participant,
        "cohort": cohort,
        "trial_day": trial_day,
        "block": block_num,
        "block_id": block_id,
        "trial_in_block": np.arange(n_trials, dtype=int),
        "start_bin_matlab": starts_m,
        "stop_bin_matlab": stops_m,
        "start_bin": starts_py,
        "stop_bin": stops_py,
        "n_bins_in_trial": stops_py - starts_py,
    })
    for key, vals in trial_cols.items():
        trials[friendly.get(key, key)] = vals
    if "success" in trials:
        trials["success"] = trials["success"].astype(bool)
    if "excluded" in trials:
        trials["excluded"] = trials["excluded"].astype(bool)

    # ---- task name -------------------------------------------------------
    task_name = task.get("name")
    if isinstance(task_name, np.ndarray):
        task_name = task_name.item() if task_name.size == 1 else str(task_name)
    task_name = str(task_name) if task_name is not None else None

    pct_correct = info.get("percentCorrect")
    if pct_correct is not None:
        pct_correct = float(np.asarray(pct_correct))

    n_points = task.get("nPointsPerBlock")
    n_points = int(np.asarray(n_points)) if n_points is not None else None
    if n_points is not None and n_bins and n_points != n_bins:
        problems.append(
            f"{block_id}: nPointsPerBlock ({n_points}) disagrees with the "
            f"{n_bins} rows in the neural matrix"
        )

    block_row = {
        "participant": participant,
        "cohort": cohort,
        "trial_day": trial_day,
        "block": block_num,
        "block_id": block_id,
        "task_name": task_name,
        "task_group": (task_name or "").strip().lower() or None,
        "n_bins": n_bins,
        "n_features": n_feats,
        "n_trials": n_trials,
        "neural_variable": neural_source,
        "duration_s_at_20ms": round(n_bins * 0.02, 2) if n_bins else 0.0,
        "percent_correct": pct_correct,
        "has_spike_power": NEURAL_SECONDARY in data,
        "has_labels": "labels" in data,
        "has_cursor_vel": "cursorVel" in data,
        "path": str(block_dir),
    }

    kin = {k: np.asarray(data[k]) for k in KINEMATIC_NAMES if k in data}
    for k in STEP_METRICS:
        if k in info:
            kin[k] = np.asarray(info[k])
    if "moveDirVect" in task:
        kin["moveDirVect"] = np.asarray(task["moveDirVect"])

    return block_row, trials, neural, kin


# ---------------------------------------------------------------------------
# WALKING THE TREE
# ---------------------------------------------------------------------------

def find_block_dirs(root: Path) -> list[tuple[Path, str, int, int, str]]:
    """
    Find every block folder, returning
    (path, participant, trial_day, block, cohort).

    Rather than assuming an exact depth, this searches for any folder matching
    'block_<N>' whose parent matches 'day_<N>'. That tolerates the deposit being
    wrapped in one extra folder (e.g. after unzipping), which is likely.
    """
    found = []
    for block_dir in sorted(root.rglob("*")):
        if not block_dir.is_dir():
            continue
        bm = BLOCK_RE.match(block_dir.name)
        if not bm:
            continue
        day_dir = block_dir.parent
        dm = DAY_RE.match(day_dir.name)
        if not dm:
            continue
        # Participant = nearest ancestor that looks like T5 / T11 / T11(additional).
        participant, cohort = "unknown", "main"
        for anc in day_dir.parents:
            m = PARTICIPANT_RE.match(anc.name)
            if m:
                participant = m.group(1).upper()
                if m.group(2):
                    # e.g. 'T11(additional)' -> cohort named by the task folder
                    # that sits between the participant folder and the day.
                    rel_parts = block_dir.relative_to(anc).parts
                    cohort = rel_parts[0] if len(rel_parts) > 2 else "additional"
                break
            if anc == root:
                break
        found.append((block_dir, participant, int(dm.group(1)),
                      int(bm.group(1)), cohort))
    return found


def load_dataset(root: Path = DEFAULT_ROOT, participant: str | None = None,
                 index_base: int = 1, load_neural: bool = True,
                 verbose: bool = True) -> Dataset:
    """Load the whole dataset (or one participant) into a Dataset object."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"{root} does not exist")

    block_dirs = find_block_dirs(root)
    if participant:
        block_dirs = [b for b in block_dirs if b[1].upper() == participant.upper()]

    if not block_dirs:
        raise FileNotFoundError(
            f"No 'day_<N>/block_<M>' folders found under {root}.\n"
            "If the download is a .zip, unpack it first:\n"
            "    python3 scripts/02_inspect_dataset.py --extract"
        )

    problems: list[str] = []
    block_rows, trial_frames = [], []
    neural: dict[str, np.ndarray] = {}
    kinematics: dict[str, dict] = {}

    for i, (bdir, part, day, blk, cohort) in enumerate(block_dirs, start=1):
        if verbose and (i == 1 or i % 25 == 0 or i == len(block_dirs)):
            print(f"  [{i}/{len(block_dirs)}] {part} day_{day} block_{blk}")
        row, trials, nd, kin = load_block(bdir, part, day, blk, index_base,
                                          problems, cohort)
        block_rows.append(row)
        if len(trials):
            trial_frames.append(trials)
        if load_neural and nd is not None:
            neural[row["block_id"]] = nd
        if kin:
            kinematics[row["block_id"]] = kin

    blocks = pd.DataFrame(block_rows).sort_values(
        ["participant", "cohort", "trial_day", "block"]).reset_index(drop=True)

    if trial_frames:
        trials = pd.concat(trial_frames, ignore_index=True)
        trials = trials.sort_values(
            ["participant", "cohort", "trial_day", "block",
             "trial_in_block"]).reset_index(drop=True)
        # A stable, unique identifier for every trial in the dataset.
        trials.insert(0, "trial_uid",
                      trials["participant"]
                      + trials["cohort"].map(lambda c: "" if c == "main" else f"-{c}")
                      + "_d" + trials["trial_day"].astype(str)
                      + "_b" + trials["block"].astype(str)
                      + "_t" + trials["trial_in_block"].astype(str))
    else:
        trials = pd.DataFrame()
        problems.append("no trials were loaded from any block")

    # ---- evidence for/against the index-base assumption ------------------
    # We cannot prove whether startStops is 1-based or 0-based from the data
    # alone, but we CAN report the evidence instead of assuming silently.
    # If the smallest raw start index anywhere is 1, 1-based is consistent.
    # If it is 0, the data are 0-based and --index-base 1 is shifting everything.
    if not trials.empty and "start_bin_matlab" in trials:
        min_raw = int(trials["start_bin_matlab"].min())
        if min_raw == 0 and index_base == 1:
            problems.append(
                f"index base: the smallest raw start index in the dataset is 0, "
                f"but --index-base 1 was used. The data look 0-based; every trial "
                f"is being shifted by one bin. Re-run with --index-base 0."
            )
        elif min_raw == 1 and index_base == 0:
            problems.append(
                f"index base: the smallest raw start index is 1, which is what "
                f"1-based (MATLAB) data look like, but --index-base 0 was used. "
                f"If these are MATLAB indices, every trial is off by one bin."
            )
        # A minimum above 1 is entirely normal -- trials need not begin on the
        # first bin of a block -- so it is not reported as a problem. The
        # decisive test lives in load_dataset(): whether any trial's stop index
        # equals nPointsPerBlock (1-based) or nPointsPerBlock - 1 (0-based).

    # Cross-block sanity checks.
    feat_counts = blocks.loc[blocks["n_features"] > 0]\
                        .groupby("participant")["n_features"].nunique()  # noqa: E501
    for part, n in feat_counts.items():
        if n > 1:
            seen = sorted(int(v) for v in blocks.loc[
                (blocks["participant"] == part) & (blocks["n_features"] > 0),
                "n_features"].unique())
            problems.append(
                f"{part}: neural feature count is not constant across blocks "
                f"({seen}). Any analysis pooling blocks must handle this."
            )

    return Dataset(trials=trials, blocks=blocks, neural=neural,
                   kinematics=kinematics, problems=problems)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--participant", type=str, default=None)
    ap.add_argument("--index-base", type=int, choices=(0, 1), default=1,
                    help="whether startStops is 1-based (MATLAB, default) or 0-based")
    ap.add_argument("--no-neural", action="store_true",
                    help="skip loading the big neural matrices (much faster)")
    ap.add_argument("--save", action="store_true",
                    help="write trials.csv and blocks.csv into data/processed/")
    args = ap.parse_args()

    print("=" * 72)
    print(f"Loading from {args.root}")
    print("=" * 72)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ds = load_dataset(args.root, participant=args.participant,
                          index_base=args.index_base,
                          load_neural=not args.no_neural)

    print("\n" + ds.summary())

    if not ds.blocks.empty:
        print("\nPer participant:")
        agg = ds.blocks.groupby("participant").agg(
            sessions=("trial_day", "nunique"),
            blocks=("block_id", "count"),
            trials=("n_trials", "sum"),
            bins=("n_bins", "sum"),
            features=("n_features", "max"),
        )
        agg["hours_at_20ms"] = (agg["bins"] * 0.02 / 3600).round(2)
        print(agg.to_string())

        print("\nTrial days per participant:")
        for part, grp in ds.blocks.groupby("participant"):
            days = sorted(grp["trial_day"].unique())
            span = max(days) - min(days) if len(days) > 1 else 0
            print(f"  {part}: {len(days)} session(s), days {min(days)}-{max(days)} "
                  f"(span {span} days)")

    if not ds.trials.empty:
        print(f"\nTrial table columns: {list(ds.trials.columns)}")
        print("\nFirst 5 trials:")
        print(ds.trials.head().to_string())

    if caught:
        print(f"\nWarnings raised while reading files: {len(caught)}")
        for w in caught[:10]:
            print(f"  - {w.message}")

    if ds.problems:
        print("\n" + "!" * 72)
        print("CONSISTENCY PROBLEMS FLAGGED -- read these before analysing:")
        for p in ds.problems[:25]:
            print(f"  - {p}")
        if len(ds.problems) > 25:
            print(f"  ... and {len(ds.problems) - 25} more")
        print("!" * 72)
    else:
        print("\nNo consistency problems flagged.")

    if args.save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ds.trials.to_csv(PROCESSED_DIR / "trials.csv", index=False)
        ds.blocks.to_csv(PROCESSED_DIR / "blocks.csv", index=False)
        print(f"\nWrote {PROCESSED_DIR/'trials.csv'} and {PROCESSED_DIR/'blocks.csv'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
