#!/usr/bin/env python3
"""
Fault injector: deliberately degrade a COPY of real recorded neural data, at a
time chosen and written down in advance.

WHY THIS EXISTS
---------------
Phases 1-2 established that the public dataset cannot answer the question the
project asks, because nobody recorded when deterioration actually began. Without
a known onset:

  * "lead time" is measured against a moment the analyst chose after the fact,
    so it is partly an artefact of that choice; and
  * the false-alarm rate cannot be estimated at all, because there is no stretch
    of record known to be healthy with nothing coming.

Injecting a fault at a time we choose fixes both. This is standard engineering
practice (fault injection); nothing is injected into a person, and no raw file is
modified. Every function here returns a NEW array.

THE FOUR MODES ARE NOT ARBITRARY
--------------------------------
They were chosen to span the axis that Phase 1-2 showed actually matters --
how visible the fault is to the trivial comparator, mean activity:

    RATE_LOSS          fully visible to mean activity   (the easy case)
    CHANNEL_DROPOUT    partly visible
    GAIN_DRIFT         approximately mean-preserving by construction
    GEOMETRY_ROTATION  norm-preserving; invisible to mean activity

Phase 1-2 found that mean firing rate alone matched a five-dimensional pipeline
(rho = -0.880 vs +0.858). GEOMETRY_ROTATION is the mode that a mean-rate detector
must fail, so it is the mode that makes gate S4 -- "beat the trivial comparator"
-- a real test rather than a formality. If a monitor only ever detects
RATE_LOSS, it has learned nothing that counting spikes did not already know.

THE PLAN/APPLY SPLIT IS THE POINT
---------------------------------
`plan` draws the onsets and writes them to disk with a git commit hash and a
checksum. `apply` can only read that file. You cannot move an onset after seeing
how the monitor did, because re-planning refuses to overwrite without an
explicit, recorded reason. Same discipline as scripts/12_freeze_design.py.

Usage
-----
    python3 scripts/17_fault_injector.py plan
    python3 scripts/17_fault_injector.py verify
    python3 scripts/17_fault_injector.py apply --episode <id> --out <file.npy>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = REPO_ROOT / "data" / "processed" / "injection_plan.json"


def plan_path(participant: str = "T11") -> Path:
    """Where a participant's locked plan lives.

    T11 keeps the original filename so its three recorded amendments and their
    checksums stay valid without being rewritten.
    """
    if participant == "T11":
        return PLAN_PATH
    return PLAN_PATH.parent / f"injection_plan_{participant}.json"

# --------------------------------------------------------------------------
# DESIGN CONSTANTS -- these define the corpus and are frozen by `plan`
# --------------------------------------------------------------------------

MODES = ("NONE", "RATE_LOSS", "CHANNEL_DROPOUT", "GAIN_DRIFT", "GEOMETRY_ROTATION")

# Ramp length as a fraction of the bins available AFTER onset. "fast" means the
# fault reaches full severity in a tenth of the remaining record.
RATE_FRACTIONS = {"fast": 0.10, "medium": 0.35, "slow": 0.80}

# Severity at the endpoint, in each mode's own natural units.
#
# These values are CALIBRATED, not chosen: scripts/18_reference_decoder.py
# calibrate sweeps severity against the frozen decoder and reports how much
# each level actually degrades decoding. The design always specified levels
# spanning a performance threshold and deliberately declined to guess the
# numbers; this is the measurement that supplied them.
# See data/processed/severity_calibration.csv.
#
#   benign    a real change to the data that does NOT degrade decoding.
#             A monitor should notice a change but must not call it a failure.
#             These are false-alarm material, alongside NONE.
#   sub       degrades, but by less than the crossing threshold.
#   crossing  degrades well past the threshold.
#
# The labels are the DESIGN INTENT. Whether a given episode actually crossed is
# determined per episode by measurement, because draw-to-draw variance is large
# (see CHANNEL_DROPOUT, where sd across seeds is ~13 deg at low severity: losing
# 5% of channels is harmless or ruinous depending on WHICH channels die).
SEVERITIES = {
    "RATE_LOSS":         {"benign": 0.10, "sub": 0.25, "crossing": 0.55},
    "CHANNEL_DROPOUT":   {"benign": 0.05, "sub": 0.30, "crossing": 0.60},
    "GAIN_DRIFT":        {"benign": 0.20, "sub": 0.50, "crossing": 1.20},
    "GEOMETRY_ROTATION": {"benign": 0.15, "sub": 0.45, "crossing": 1.20},
    "NONE":              {"none": 0.0},
}

# Measured degradation vs control, in degrees of angular error, at these levels:
#   RATE_LOSS          +0.3  /  +5.0  / +24.5
#   CHANNEL_DROPOUT    +2.7  /  +11.1 / +24.1
#   GAIN_DRIFT         +1.3  /  +9.0  / +23.3
#   GEOMETRY_ROTATION  -11.0 /  +7.3  / +31.1
#
# Note GEOMETRY_ROTATION's benign level: mild rotation IMPROVES decoding by
# about 11 deg, consistently across seeds. Mixing correlated channels appears to
# average away noise for this heavily-regularised decoder. It is kept precisely
# because it is a hard negative -- a large, real change in the neural statistics
# with no performance cost, which a monitor must not report as a failure.

# The performance threshold this is calibrated against: a +10 deg rise in median
# angular error above the episode's own pre-onset baseline. Fixed here, before
# any detector exists. Anchored by measurement, not taste: healthy held-out
# decoding is 54.6 deg and chance is 90.7 deg, so +10 deg consumes 28% of the
# distance from healthy to useless, and it is ~40x the control's own drift.
PERFORMANCE_THRESHOLD_DEG = 10.0

# Onset is drawn uniformly in this window, as a fraction of the block. The lower
# bound guarantees enough healthy record to fit a reference on; the upper bound
# guarantees enough post-onset record for the fault to develop and be caught.
ONSET_WINDOW = (0.25, 0.55)

RAMP_SHAPE = "linear"      # 'linear' or 'exp'
MASTER_SEED = 20260826


# --------------------------------------------------------------------------
# EPISODE SPEC
# --------------------------------------------------------------------------

@dataclass
class Episode:
    """One injected fault. Fully determines the degradation -- given the same
    source block and this record, `apply` is bit-for-bit reproducible."""
    episode_id: str
    block_id: str
    n_bins: int
    n_feats: int
    mode: str
    rate_label: str
    severity_label: str
    severity: float
    onset_bin: int
    ramp_bins: int
    ramp_shape: str
    seed: int
    feature_groups: list = field(default_factory=list)  # [[start, stop), ...]

    @property
    def onset_s(self) -> float:
        return round(self.onset_bin * 0.02, 2)


# --------------------------------------------------------------------------
# THE RAMP
# --------------------------------------------------------------------------

def ramp(n_bins: int, onset_bin: int, ramp_bins: int, shape: str = "linear") -> np.ndarray:
    """Fault progress in [0, 1]: exactly 0 before onset, rising to 1 after.

    Being exactly zero before onset matters. If the ramp leaked backwards even
    slightly, a detector could 'warn' before onset by picking up the leak, and
    the measured lead time would be an artefact of this function rather than a
    property of the detector.
    """
    f = np.zeros(n_bins, dtype=np.float64)
    t = np.arange(n_bins, dtype=np.float64) - onset_bin
    live = t >= 0
    if ramp_bins <= 0:
        f[live] = 1.0
    elif shape == "linear":
        f[live] = np.clip(t[live] / ramp_bins, 0.0, 1.0)
    elif shape == "exp":
        f[live] = 1.0 - np.exp(-t[live] / ramp_bins)
    else:
        raise ValueError(f"unknown ramp shape {shape!r}")
    return f


# --------------------------------------------------------------------------
# THE FOUR MODES -- all pure; none mutates its input
# --------------------------------------------------------------------------

def _rng(ep: Episode) -> np.random.Generator:
    return np.random.default_rng(ep.seed)


def apply_rate_loss(X: np.ndarray, ep: Episode, f: np.ndarray) -> np.ndarray:
    """Uniform loss of overall activity -- every channel scaled down together.

    This is the mode a mean-activity detector should catch trivially. It is here
    as the positive control for the trivial comparator, not as a challenge.
    """
    return X * (1.0 - ep.severity * f)[:, None]


def apply_channel_dropout(X: np.ndarray, ep: Episode, f: np.ndarray) -> np.ndarray:
    """Channels die one at a time, staggered across the ramp.

    Real arrays do not lose every electrode at once; units are lost
    individually over time (Sponheim et al. 2021). Each doomed channel is given
    its own threshold on the ramp, so dropouts are staggered rather than
    simultaneous.
    """
    rng = _rng(ep)
    n_feats = X.shape[1]

    # NESTED BY CONSTRUCTION. One permutation is drawn, and severity s takes the
    # FIRST k = s*n channels from it -- so a more severe episode kills a
    # superset of the channels a milder one kills.
    #
    # This is a fix, not a preference. The first version drew a fresh
    # rng.choice() sized by severity, which meant each severity hit a different
    # random set of channels rather than more of the same ones. Calibration
    # exposed it immediately: measured damage went +22.6d at severity 0.15, then
    # -6.2d at 0.30, then +26.8d at 0.60. A ladder that goes backwards is not a
    # ladder. The non-monotonicity was draw-to-draw variance -- some sets
    # happened to spare channels the decoder leans on -- masquerading as a
    # severity effect.
    order = rng.permutation(n_feats)
    thresholds_all = rng.uniform(0.0, 1.0, size=n_feats)
    k = max(1, int(round(ep.severity * n_feats)))
    doomed = order[:k]

    Y = X.copy()
    for col in doomed:
        Y[f >= thresholds_all[col], col] = 0.0
    return Y


def apply_gain_drift(X: np.ndarray, ep: Episode, f: np.ndarray) -> np.ndarray:
    """Per-channel gains drift apart, with the OVERALL level held ~constant.

    The log-gains are centred to zero mean, so this changes the relative
    scaling between channels without changing the average. That is what
    separates it from RATE_LOSS, and it is what makes it a test of whether a
    monitor is doing more than tracking overall level.
    """
    rng = _rng(ep)
    log_g = rng.normal(0.0, ep.severity, size=X.shape[1])
    log_g -= log_g.mean()

    G = np.exp(f[:, None] * log_g[None, :])          # (bins, channels)

    # Centring the LOG-gains preserves the geometric mean, not the arithmetic
    # one. At small sigma those are nearly the same; at the severities that
    # actually degrade decoding they are not. The first version did only the log
    # centring and verification caught it: at severity 1.2 the mode raised mean
    # activity by +116%, which would have made it trivially visible to the very
    # comparator it exists to be invisible to.
    #
    # Fix: rescale at every time step so the channel-mean-weighted total is
    # conserved exactly. This makes the mode mean-preserving by construction at
    # any severity, rather than approximately so at small ones.
    # Rescale so the TOTAL ACTIVITY IN EVERY BIN is exactly conserved. Only the
    # distribution across channels changes; the per-bin sum does not move at all.
    #
    # Two earlier attempts were wrong and both were caught by verification.
    # Centring the log-gains preserves the geometric mean, and at severity 1.2
    # that let mean activity rise +116%. Rescaling by the PRE-ONSET channel
    # profile fixed most of it but still left +20.8%, because the block's own
    # activity drifts ~15% within a block, so a profile measured before onset no
    # longer describes the data after it. Normalising against the current bin is
    # exact regardless of drift, and uses no information from the future.
    Y = X * G
    src = X.sum(axis=1)
    dst = Y.sum(axis=1)
    scale = np.ones_like(src)
    good = dst > 0
    scale[good] = src[good] / dst[good]
    return Y * scale[:, None]


def apply_geometry_rotation(X: np.ndarray, ep: Episode, f: np.ndarray) -> tuple[np.ndarray, float]:
    """Channels mix into each other: the covariance geometry turns, the norm does not.

    Implemented as Givens rotations on disjoint channel pairs, which preserve
    the vector norm exactly. Pairs are drawn only WITHIN a feature group, never
    across -- T11's matrix concatenates threshold crossings (192) with spike
    power (192), whose scales differ by orders of magnitude, and mixing across
    that boundary would be a units error dressed up as a fault.

    Returns the degraded array and the fraction of entries clipped at zero.
    """
    rng = _rng(ep)
    Y = X.copy()
    theta = ep.severity * f
    c, s = np.cos(theta), np.sin(theta)

    for start, stop in ep.feature_groups:
        idx = np.arange(start, stop)
        rng.shuffle(idx)
        n_pairs = len(idx) // 2
        for p in range(n_pairs):
            i, j = int(idx[2 * p]), int(idx[2 * p + 1])
            xi, xj = X[:, i], X[:, j]
            Y[:, i] = c * xi - s * xj
            Y[:, j] = s * xi + c * xj

    # These features are non-negative by construction (spike counts, power).
    # Rotation can produce negatives where one channel of a pair is much larger
    # than the other. Clipping is the physically correct choice, and the amount
    # clipped is REPORTED rather than hidden, because it is exactly the amount
    # by which this mode fails to be perfectly norm-preserving.
    neg = Y < 0.0
    clipped_fraction = float(neg.mean())
    Y[neg] = 0.0
    return Y, clipped_fraction


APPLIERS = {
    "RATE_LOSS": apply_rate_loss,
    "CHANNEL_DROPOUT": apply_channel_dropout,
    "GAIN_DRIFT": apply_gain_drift,
}


def apply_episode(X: np.ndarray, ep: Episode) -> tuple[np.ndarray, dict]:
    """Degrade a copy of X according to ep. X is never modified."""
    if X.shape[0] != ep.n_bins or X.shape[1] != ep.n_feats:
        raise ValueError(
            f"{ep.episode_id}: block is {X.shape}, plan recorded "
            f"({ep.n_bins}, {ep.n_feats}). Wrong block, or the loader changed."
        )

    diag: dict = {"clipped_fraction": 0.0}

    if ep.mode == "NONE":
        # The control still goes through the same diagnostic path as every other
        # mode. An earlier version returned here early and skipped the
        # diagnostics, which crashed the verifier -- and, worse, would have made
        # the control the one episode nobody checked.
        Y = X.copy()
    else:
        f = ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
        if ep.mode == "GEOMETRY_ROTATION":
            Y, clipped = apply_geometry_rotation(X, ep, f)
            diag["clipped_fraction"] = clipped
        else:
            Y = APPLIERS[ep.mode](X, ep, f)

    # Restore the pre-onset rows exactly. Several modes compute a scale factor
    # that is algebraically 1.0 before onset but differs in the last bits of
    # floating point, and "the record before onset is untouched" is too load-
    # bearing to leave to rounding: if it leaked, a detector could 'warn' by
    # sensing the leak and the measured lead time would be an artefact of this
    # file rather than a property of the detector.
    pre = slice(0, ep.onset_bin)
    Y[pre] = X[pre]
    diag["pre_onset_identical"] = bool(np.array_equal(X[pre], Y[pre]))
    diag["mean_before"] = float(X[pre].mean()) if ep.onset_bin > 0 else float("nan")
    diag["mean_after"] = float(Y[ep.onset_bin:].mean())
    return Y, diag


# --------------------------------------------------------------------------
# PLANNING
# --------------------------------------------------------------------------

def load_loader():
    spec = importlib.util.spec_from_file_location(
        "loader", REPO_ROOT / "scripts" / "03_load_dataset.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["loader"] = mod          # registered before exec so @dataclass works
    spec.loader.exec_module(mod)
    return mod


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def feature_groups_for(n_feats: int, neural_variable: str) -> list:
    """Where one feature type ends and the next begins.

    T11 is nctx+spikePower (384 columns, two groups of 192); T5 is nctx only
    (192 columns, one group). Read from the loader's recorded source string
    rather than guessed from the column count.
    """
    if "+" in str(neural_variable):
        half = n_feats // 2
        return [[0, half], [half, n_feats]]
    return [[0, n_feats]]


def build_plan(participant: str = "T11") -> dict:
    loader = load_loader()
    ds = loader.load_dataset(participant=participant, load_neural=True, verbose=False)

    blocks = ds.blocks
    blocks = blocks[blocks["block_id"].isin(ds.neural.keys())]
    if "cohort" in blocks.columns:
        blocks = blocks[blocks["cohort"] == "main"]
    block_ids = sorted(blocks["block_id"].tolist())
    if not block_ids:
        raise SystemExit(f"no usable blocks for {participant}")

    rng = np.random.default_rng(MASTER_SEED)
    episodes: list[Episode] = []
    counter = 0

    for block_id in block_ids:
        X = ds.neural[block_id]
        n_bins, n_feats = X.shape
        row = blocks[blocks["block_id"] == block_id].iloc[0]
        groups = feature_groups_for(n_feats, row.get("neural_variable", "nctx"))

        for mode in MODES:
            for rate_label, frac in (RATE_FRACTIONS.items() if mode != "NONE"
                                     else [("none", 0.0)]):
                for sev_label, sev in SEVERITIES[mode].items():
                    counter += 1
                    onset_frac = rng.uniform(*ONSET_WINDOW)
                    onset_bin = int(round(onset_frac * n_bins))
                    ramp_bins = int(round(frac * (n_bins - onset_bin)))
                    episodes.append(Episode(
                        episode_id=f"EP{counter:05d}",
                        block_id=block_id,
                        n_bins=int(n_bins),
                        n_feats=int(n_feats),
                        mode=mode,
                        rate_label=rate_label,
                        severity_label=sev_label,
                        severity=float(sev),
                        onset_bin=onset_bin,
                        ramp_bins=ramp_bins,
                        ramp_shape=RAMP_SHAPE,
                        seed=int(rng.integers(0, 2**31 - 1)),
                        feature_groups=groups,
                    ))

    plan = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "master_seed": MASTER_SEED,
        "participant": participant,
        "onset_window": list(ONSET_WINDOW),
        "ramp_shape": RAMP_SHAPE,
        "rate_fractions": RATE_FRACTIONS,
        "severities": SEVERITIES,
        "n_blocks": len(block_ids),
        "n_episodes": len(episodes),
        "episodes": [asdict(e) for e in episodes],
        "amendments": [],
        "note": (
            "Onsets in this file were drawn BEFORE any detector was run against "
            "them. They must not be changed. To change them, re-run `plan "
            "--amend REASON`, which preserves this record and appends the reason."
        ),
    }
    body = json.dumps(plan["episodes"], sort_keys=True).encode()
    plan["episodes_sha256"] = hashlib.sha256(body).hexdigest()
    return plan


def load_plan(participant: str = "T11") -> tuple[dict, list[Episode]]:
    pp = plan_path(participant)
    if not pp.exists():
        raise SystemExit(f"no plan at {pp}. Run: "
                         f"python3 scripts/17_fault_injector.py plan --participant {participant}")
    plan = json.loads(pp.read_text())
    body = json.dumps(plan["episodes"], sort_keys=True).encode()
    got = hashlib.sha256(body).hexdigest()
    if got != plan.get("episodes_sha256"):
        raise SystemExit(
            "PLAN CHECKSUM MISMATCH.\n"
            f"  recorded: {plan.get('episodes_sha256')}\n"
            f"  actual:   {got}\n"
            "The episode list has been edited since it was written. Investigate "
            "before using it -- this is exactly the tampering the checksum exists "
            "to catch."
        )
    return plan, [Episode(**e) for e in plan["episodes"]]


# --------------------------------------------------------------------------
# VERIFICATION -- the injector must be checked before anything is scored with it
# --------------------------------------------------------------------------

def cmd_verify(participant: str = "T11") -> int:
    plan, episodes = load_plan(participant)
    loader = load_loader()
    ds = loader.load_dataset(participant=plan["participant"],
                             load_neural=True, verbose=False)

    print(f"Plan: {plan['n_episodes']} episodes over {plan['n_blocks']} blocks")
    print(f"  created  {plan['created_utc']}   commit {plan['git_commit'][:12]}")
    print(f"  checksum {plan['episodes_sha256'][:16]}...  VERIFIED\n")

    # Work one block, all modes, so the comparison is like-for-like.
    target = episodes[0].block_id
    X = ds.neural[target]
    print(f"Behaviour check on {target}  shape {X.shape}\n")

    # The naive measure -- mean after onset vs mean before onset -- is
    # CONTAMINATED, and the NONE control is what reveals it: on this block an
    # untouched array already shows a large positive "change", because activity
    # genuinely drifts within a block. Any before/after statistic therefore has
    # a non-zero floor that has nothing to do with the injected fault.
    #
    # The honest measure is the change RELATIVE TO THE UNTOUCHED CONTROL on the
    # same block. That is what the last column reports, and it is the only
    # column that should be read as an effect of the fault.
    none_ep = next(e for e in episodes if e.block_id == target and e.mode == "NONE")
    _, none_diag = apply_episode(X, none_ep)
    baseline_change = none_diag["mean_after"] / none_diag["mean_before"] - 1.0

    print("Does the fault change overall activity? (this is the S4 question)")
    print(f"{'mode':<20} {'sev':<8} {'raw change':>11} {'vs control':>11} "
          f"{'clipped':>9}  pre-onset intact")
    print(f"{'':<20} {'':<8} {'(misleading)':>11} {'(the answer)':>11}")
    print("-" * 78)

    failures = []
    for ep in episodes:
        if ep.block_id != target or ep.rate_label not in ("medium", "none"):
            continue
        if ep.severity_label == "sub":
            continue
        Y, diag = apply_episode(X, ep)
        raw = diag["mean_after"] / diag["mean_before"] - 1.0
        rel = (1.0 + raw) / (1.0 + baseline_change) - 1.0
        ok = diag.get("pre_onset_identical", True)
        if not ok:
            failures.append(f"{ep.episode_id} {ep.mode}: ramp leaked before onset")
        print(f"{ep.mode:<20} {ep.severity_label:<8} {raw*100:>10.1f}% "
              f"{rel*100:>10.1f}% {diag['clipped_fraction']*100:>8.2f}%  "
              f"{'yes' if ok else 'NO'}")

    print(f"\n  The control's own drift on this block is {baseline_change*100:+.1f}%.")
    print("  That is the data moving, not a fault. It is subtracted in column 2.")
    print("\nWhat column 2 has to show, for the corpus to be worth anything:")
    print("  RATE_LOSS          large negative  -- mean activity sees this one")
    print("  CHANNEL_DROPOUT    negative        -- partly visible")
    print("  GAIN_DRIFT         near zero       -- mean activity is blind to it")
    print("  GEOMETRY_ROTATION  near zero       -- mean activity is blind to it")
    print("  NONE               exactly zero    -- by construction")
    print("\n  A monitor that only catches RATE_LOSS has learned nothing that")
    print("  counting spikes did not already know. That is gate S4.")
    print("\n  'clipped' is the fraction of entries rotation drove below zero and")
    print("  had to be floored. It is the amount by which GEOMETRY_ROTATION falls")
    print("  short of being exactly norm-preserving, and it is reported, not hidden.")

    # Hard invariants.
    print("\nInvariants:")
    none_ep = next(e for e in episodes if e.block_id == target and e.mode == "NONE")
    Y, _ = apply_episode(X, none_ep)
    identical = np.array_equal(X, Y)
    print(f"  NONE returns an identical array ................ {'PASS' if identical else 'FAIL'}")
    if not identical:
        failures.append("NONE episode altered the data")

    before = X.copy()
    rot = next(e for e in episodes if e.block_id == target
               and e.mode == "GEOMETRY_ROTATION" and e.severity_label == "crossing")
    apply_episode(X, rot)
    untouched = np.array_equal(before, X)
    print(f"  the source array is never mutated .............. {'PASS' if untouched else 'FAIL'}")
    if not untouched:
        failures.append("apply_episode mutated its input")

    r = ramp(1000, 400, 200, "linear")
    ramp_ok = (r[:400] == 0).all() and r[400] == 0 and abs(r[600] - 1.0) < 1e-12
    print(f"  ramp is exactly 0 before onset ................. {'PASS' if ramp_ok else 'FAIL'}")
    if not ramp_ok:
        failures.append("ramp leaks before onset")

    d1, _ = apply_episode(X, rot)
    d2, _ = apply_episode(X, rot)
    print(f"  same episode is bit-for-bit reproducible ....... "
          f"{'PASS' if np.array_equal(d1, d2) else 'FAIL'}")
    if not np.array_equal(d1, d2):
        failures.append("episode is not reproducible")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nAll invariants pass.")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_plan(amend: str | None, participant: str = "T11") -> int:
    pp = plan_path(participant)
    if pp.exists() and not amend:
        existing = json.loads(pp.read_text())
        print(f"A plan already exists: {pp}")
        print(f"  created {existing['created_utc']} with "
              f"{existing['n_episodes']} episodes")
        print("\nRefusing to overwrite. The onsets in that file were drawn before")
        print("any detector saw them, and that ordering is the only reason lead")
        print("time means anything. If you genuinely need to re-plan:")
        print("\n    python3 scripts/17_fault_injector.py plan --amend 'why'\n")
        return 1

    plan = build_plan(participant)
    if amend:
        old = json.loads(pp.read_text()) if pp.exists() else {}
        plan["amendments"] = old.get("amendments", []) + [{
            "at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reason": amend,
            "superseded_checksum": old.get("episodes_sha256"),
            "superseded_created": old.get("created_utc"),
        }]

    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(plan, indent=2))

    print(f"Wrote {pp}")
    print(f"  {plan['n_episodes']} episodes over {plan['n_blocks']} blocks")
    print(f"  commit   {plan['git_commit'][:12]}")
    print(f"  checksum {plan['episodes_sha256'][:16]}...")
    if amend:
        print(f"  AMENDED: {amend}")
    print("\nCommit this file before running any detector against it.")
    return 0


def cmd_apply(episode_id: str, out: str | None, participant: str = "T11") -> int:
    plan, episodes = load_plan(participant)
    match = [e for e in episodes if e.episode_id == episode_id]
    if not match:
        raise SystemExit(f"no episode {episode_id!r} in the plan")
    ep = match[0]

    loader = load_loader()
    ds = loader.load_dataset(participant=plan["participant"],
                            load_neural=True, verbose=False)
    X = ds.neural[ep.block_id]
    Y, diag = apply_episode(X, ep)

    print(f"{ep.episode_id}  {ep.mode}  {ep.severity_label} ({ep.severity})  "
          f"{ep.rate_label}")
    print(f"  block     {ep.block_id}  {X.shape}")
    print(f"  onset     bin {ep.onset_bin}  ({ep.onset_s} s)  "
          f"ramp {ep.ramp_bins} bins")
    for k, v in diag.items():
        print(f"  {k:<22} {v}")

    if out:
        np.save(out, Y)
        print(f"\n  wrote {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="draw onsets and lock them to disk")
    p.add_argument("--amend", metavar="REASON",
                   help="overwrite an existing plan, recording why")
    p.add_argument("--participant", default="T11")

    v = sub.add_parser("verify", help="check the injector behaves as specified")
    v.add_argument("--participant", default="T11")

    a = sub.add_parser("apply", help="degrade one block per one episode")
    a.add_argument("--episode", required=True)
    a.add_argument("--out", help="save the degraded array as .npy")
    a.add_argument("--participant", default="T11")

    args = ap.parse_args()
    if args.cmd == "plan":
        return cmd_plan(args.amend, args.participant)
    if args.cmd == "verify":
        return cmd_verify(args.participant)
    return cmd_apply(args.episode, args.out, args.participant)


if __name__ == "__main__":
    raise SystemExit(main())
