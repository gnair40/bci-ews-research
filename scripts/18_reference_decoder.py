#!/usr/bin/env python3
"""
Reference decoder: the thing that says whether performance dropped.

WHAT THIS IS FOR
----------------
`decoder-guard` never looks at the decoder -- it watches the feature stream
going IN. The decoder exists here only to GRADE: it turns a degraded feature
stream into a performance number, so that "the monitor warned before performance
fell" becomes checkable.

That means the decoder does not need to be good. It needs exactly two properties:

  1. It works better than chance on healthy held-out data.
  2. It is FROZEN -- fitted once, then never refitted. If it adapted, it would
     absorb the degradation and there would be nothing left to detect. This was
     the original reason this dataset was chosen: its sessions were run without
     recalibration.

Chasing decoder accuracy beyond property 1 is wasted effort and is explicitly
not a goal.

WHAT IT PREDICTS
----------------
The participant's INTENDED direction of movement at each 20 ms bin, taken as the
unit vector from the current cursor position to the target. This is the standard
intention-based linear velocity decoder.

Performance is then the angle between the decoded direction and the intended
direction, in degrees. 0 is perfect; 90 is chance (a decoder pointing in a
direction unrelated to the target); 180 is exactly backwards. The same quantity,
at trial level, is what Phase 1-2 used throughout.

NORMALISATION IS FROZEN, AND THAT IS A DELIBERATE CHOICE
--------------------------------------------------------
Feature means and standard deviations are fixed at training time and never
updated. The real system used ADAPTIVE normalisation, which Phase 1-2 identified
as a compensator that masked degradation until it saturated. Freezing it here
isolates the effect of degradation on the decoder from the effect of a
compensator fighting it. Re-running with adaptive normalisation is a separate,
worthwhile condition and is left as such rather than silently mixed in.

Usage
-----
    python3 scripts/18_reference_decoder.py fit
    python3 scripts/18_reference_decoder.py check
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "processed"
DECODER_PATH = OUT_DIR / "reference_decoder.npz"
META_PATH = OUT_DIR / "reference_decoder.json"


def decoder_paths(participant: str = "T11") -> tuple[Path, Path]:
    """T11 keeps the original filenames so existing references stay valid."""
    if participant == "T11":
        return DECODER_PATH, META_PATH
    return (OUT_DIR / f"reference_decoder_{participant}.npz",
            OUT_DIR / f"reference_decoder_{participant}.json")


# Healthy training/validation days per participant. T11's are the Phase 1-2
# healthy baseline. T5's are simply its earliest days, since it has no separately
# established baseline -- stated rather than implied.
DAYS = {
    "T11": {"train": (658, 665, 670), "val": (671, 675)},
    "T5":  {"train": None, "val": None},        # filled at fit time from the data
}

# The healthy baseline established in Phase 1-2: T11 performing at 93-100%.
# Split within it, so the decoder is fitted and selected entirely on healthy
# data and never sees a degraded block during fitting.
TRAIN_DAYS = (658, 665, 670)
VAL_DAYS = (671, 675)

RIDGE_GRID = (1e-1, 1e0, 1e1, 1e2, 1e3, 1e4)

# Bins where the cursor is essentially on the target have no defined intended
# direction -- normalising a near-zero vector amplifies noise into an arbitrary
# angle. Those bins are excluded from both fitting and scoring.
MIN_TARGET_DIST = 0.02


def load_loader():
    spec = importlib.util.spec_from_file_location(
        "loader", REPO_ROOT / "scripts" / "03_load_dataset.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["loader"] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# TARGETS AND MASKS
# --------------------------------------------------------------------------

def intended_direction(kin: dict) -> tuple[np.ndarray, np.ndarray]:
    """Unit vector from cursor to target at each bin, plus a validity mask."""
    cur = np.asarray(kin["cursorPos"], dtype=np.float64)
    tgt = np.asarray(kin["targetPos"], dtype=np.float64)
    d = tgt - cur
    dist = np.linalg.norm(d, axis=1)
    ok = np.isfinite(dist) & (dist > MIN_TARGET_DIST)
    unit = np.zeros_like(d)
    unit[ok] = d[ok] / dist[ok, None]
    return unit, ok


def in_trial_mask(trials: pd.DataFrame, block_id: str, n_bins: int) -> np.ndarray:
    """True for bins inside a non-excluded trial.

    Between-trial bins are not goal-directed, and excluded trials were marked
    unusable by the original investigators. Neither belongs in fitting or
    scoring, so both are masked rather than quietly averaged in.
    """
    m = np.zeros(n_bins, dtype=bool)
    rows = trials[(trials["block_id"] == block_id) & (~trials["excluded"].astype(bool))]
    for a, b in zip(rows["start_bin"].to_numpy(), rows["stop_bin"].to_numpy()):
        a = max(0, int(a)); b = min(n_bins, int(b))
        if b > a:
            m[a:b] = True
    return m


def angular_error_deg(pred: np.ndarray, target_unit: np.ndarray) -> np.ndarray:
    """Angle between each predicted vector and the intended unit vector."""
    n = np.linalg.norm(pred, axis=1)
    out = np.full(len(pred), np.nan)
    ok = n > 1e-12
    cos = np.einsum("ij,ij->i", pred[ok] / n[ok, None], target_unit[ok])
    out[ok] = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
    return out


# --------------------------------------------------------------------------
# FITTING -- accumulated block by block, never all in memory at once
# --------------------------------------------------------------------------

def accumulate(ds, trials, block_ids, mean=None, std=None):
    """Build X'X, X'Y over blocks without concatenating them.

    An earlier stage of this project was killed by the OOM killer for holding
    every neural matrix at once. Accumulating the normal equations keeps memory
    flat regardless of how many blocks are involved.
    """
    p = None
    XtX = XtY = None
    n_used = 0
    s1 = s2 = None

    for bid in block_ids:
        X = ds.neural[bid]
        kin = ds.kinematics[bid]
        if "cursorPos" not in kin or "targetPos" not in kin:
            continue
        unit, ok_dir = intended_direction(kin)
        ok = ok_dir & in_trial_mask(trials, bid, X.shape[0])
        if ok.sum() < 100:
            continue

        Xb = X[ok]
        if p is None:
            p = Xb.shape[1]
            s1 = np.zeros(p); s2 = np.zeros(p)
            XtX = np.zeros((p + 1, p + 1)); XtY = np.zeros((p + 1, 2))

        if mean is None:                      # first pass: collect scaling only
            s1 += Xb.sum(axis=0)
            s2 += (Xb ** 2).sum(axis=0)
            n_used += len(Xb)
            continue

        Z = (Xb - mean) / std
        Z = np.hstack([Z, np.ones((len(Z), 1))])
        XtX += Z.T @ Z
        XtY += Z.T @ unit[ok]
        n_used += len(Z)

    if mean is None:
        m = s1 / n_used
        sd = np.sqrt(np.maximum(s2 / n_used - m ** 2, 1e-12))
        return m, sd, n_used
    return XtX, XtY, n_used


def solve_ridge(XtX, XtY, lam):
    p = XtX.shape[0]
    reg = np.eye(p) * lam
    reg[-1, -1] = 0.0                      # never penalise the intercept
    return np.linalg.solve(XtX + reg, XtY)


def score_blocks(ds, trials, block_ids, W, mean, std) -> float:
    """Median angular error in degrees over all valid bins in these blocks."""
    errs = []
    for bid in block_ids:
        X = ds.neural[bid]
        kin = ds.kinematics[bid]
        if "cursorPos" not in kin:
            continue
        unit, ok_dir = intended_direction(kin)
        ok = ok_dir & in_trial_mask(trials, bid, X.shape[0])
        if ok.sum() < 100:
            continue
        Z = np.hstack([(X[ok] - mean) / std, np.ones((int(ok.sum()), 1))])
        errs.append(angular_error_deg(Z @ W, unit[ok]))
    if not errs:
        return float("nan")
    return float(np.nanmedian(np.concatenate(errs)))


def decode_stream(X: np.ndarray, W, mean, std) -> np.ndarray:
    """Apply the frozen decoder to any feature stream, degraded or not."""
    Z = np.hstack([(X - mean) / std, np.ones((len(X), 1))])
    return Z @ W


# --------------------------------------------------------------------------
# COMMANDS
# --------------------------------------------------------------------------

def cmd_fit(participant: str = "T11") -> int:
    dec_path, meta_path = decoder_paths(participant)
    loader = load_loader()
    ds = loader.load_dataset(participant=participant, load_neural=True, verbose=False)
    trials = pd.read_csv(OUT_DIR / "trials.csv")
    blocks = pd.read_csv(OUT_DIR / "blocks.csv")
    blocks = blocks[(blocks["cohort"] == "main") & (blocks["block_id"].isin(ds.neural))]

    cfg = DAYS.get(participant, {"train": None, "val": None})
    train_days, val_days = cfg["train"], cfg["val"]
    if train_days is None:
        # No established healthy baseline for this participant: take the
        # earliest days, which is the closest available thing to "before it
        # degraded", and say so rather than implying a baseline exists.
        days = sorted(blocks["trial_day"].unique())
        cut = max(2, int(round(len(days) * 0.6)))
        # Cast off numpy integer types: they survive arithmetic happily and
        # then fail at json.dumps, several minutes of fitting later.
        train_days = tuple(int(d) for d in days[:cut])
        val_days = tuple(int(d) for d in days[cut:cut + 2])
        print(f"  [{participant}] no established baseline; using earliest days")

    TRAIN_DAYS_L, VAL_DAYS_L = train_days, val_days
    train_ids = sorted(blocks[blocks["trial_day"].isin(TRAIN_DAYS_L)]["block_id"])
    val_ids = sorted(blocks[blocks["trial_day"].isin(VAL_DAYS_L)]["block_id"])
    if not train_ids or not val_ids:
        raise SystemExit("no train/val blocks found -- check TRAIN_DAYS/VAL_DAYS")

    print(f"Fitting on {len(train_ids)} healthy blocks (days {TRAIN_DAYS_L})")
    print(f"Selecting on {len(val_ids)} held-out healthy blocks (days {VAL_DAYS_L})")
    print("The decoder never sees a degraded block.\n")

    mean, std, n_scale = accumulate(ds, trials, train_ids)
    XtX, XtY, n_fit = accumulate(ds, trials, train_ids, mean, std)
    print(f"  {n_fit:,} usable bins for fitting "
          f"({n_fit * 0.02 / 60:.1f} min of goal-directed movement)\n")

    print(f"  {'ridge':>10} {'train err':>11} {'val err':>11}")
    best = (None, np.inf, None)
    for lam in RIDGE_GRID:
        W = solve_ridge(XtX, XtY, lam)
        tr = score_blocks(ds, trials, train_ids, W, mean, std)
        va = score_blocks(ds, trials, val_ids, W, mean, std)
        flag = ""
        if va < best[1]:
            best = (lam, va, W)
            flag = "  <-"
        print(f"  {lam:>10.1e} {tr:>10.2f}d {va:>10.2f}d{flag}")

    lam, val_err, W = best
    train_err = score_blocks(ds, trials, train_ids, W, mean, std)

    # Chance level, measured rather than assumed: shuffle the pairing between
    # neural features and intended direction. A decoder that beats this is
    # using the neural data; one that does not is not.
    rng = np.random.default_rng(0)
    chance = []
    for bid in val_ids:
        X = ds.neural[bid]; kin = ds.kinematics[bid]
        unit, ok_dir = intended_direction(kin)
        ok = ok_dir & in_trial_mask(trials, bid, X.shape[0])
        if ok.sum() < 100:
            continue
        Z = np.hstack([(X[ok] - mean) / std, np.ones((int(ok.sum()), 1))])
        pred = Z @ W
        chance.append(angular_error_deg(pred, unit[ok][rng.permutation(int(ok.sum()))]))
    chance_err = float(np.nanmedian(np.concatenate(chance)))

    np.savez(dec_path, W=W, mean=mean, std=std)
    meta = {
        "fitted_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "participant": participant,
        "train_days": list(TRAIN_DAYS_L), "val_days": list(VAL_DAYS_L),
        "train_blocks": train_ids, "val_blocks": val_ids,
        "n_fit_bins": int(n_fit),
        "ridge_lambda": float(lam),
        "normalisation": "frozen at training (see module docstring)",
        "median_angular_error_train_deg": round(train_err, 3),
        "median_angular_error_val_deg": round(val_err, 3),
        "median_angular_error_chance_deg": round(chance_err, 3),
        "target": "unit vector from cursorPos to targetPos",
        "min_target_dist": MIN_TARGET_DIST,
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"\n  chosen ridge {lam:.1e}")
    print(f"  train  {train_err:.2f} deg")
    print(f"  val    {val_err:.2f} deg   <- held-out healthy")
    print(f"  chance {chance_err:.2f} deg  (shuffled pairing, measured not assumed)")

    margin = chance_err - val_err
    print(f"\n  Property 1 -- better than chance by {margin:.1f} deg: "
          f"{'PASS' if margin > 5 else 'FAIL'}")
    print(f"  Property 2 -- frozen: weights and normalisation written to")
    print(f"                {dec_path.name}, never refitted downstream.")
    print("\n  This decoder is not tuned for accuracy beyond clearing chance,")
    print("  and it should not be. It is a measuring instrument, not a result.")
    return 0


def cmd_check() -> int:
    """Does degradation actually move the performance number?

    If injected faults do not degrade decoding, there is nothing for a monitor
    to warn about and the corpus is worthless. This has to be established before
    any detector is written.
    """
    if not DECODER_PATH.exists():
        raise SystemExit("no decoder -- run: python3 scripts/18_reference_decoder.py fit")
    d = np.load(DECODER_PATH)
    W, mean, std = d["W"], d["mean"], d["std"]
    meta = json.loads(META_PATH.read_text())

    inj_spec = importlib.util.spec_from_file_location(
        "injector", REPO_ROOT / "scripts" / "17_fault_injector.py")
    inj = importlib.util.module_from_spec(inj_spec)
    sys.modules["injector"] = inj
    inj_spec.loader.exec_module(inj)

    loader = load_loader()
    ds = loader.load_dataset(participant="T11", load_neural=True, verbose=False)
    trials = pd.read_csv(OUT_DIR / "trials.csv")
    plan, episodes = inj.load_plan()

    target = meta["val_blocks"][0]
    X = ds.neural[target]
    kin = ds.kinematics[target]
    unit, ok_dir = intended_direction(kin)
    ok = ok_dir & in_trial_mask(trials, target, X.shape[0])

    print(f"Does injected degradation move decoding performance?")
    print(f"  block {target}   {int(ok.sum()):,} scorable bins")
    print(f"  healthy val error was {meta['median_angular_error_val_deg']:.2f} deg, "
          f"chance {meta['median_angular_error_chance_deg']:.2f} deg\n")

    rows = []
    for ep in episodes:
        if ep.block_id != target or ep.rate_label not in ("medium", "none"):
            continue
        if ep.severity_label == "mild":
            continue
        Y, _ = inj.apply_episode(X, ep)
        post = np.zeros(len(X), dtype=bool)
        post[ep.onset_bin:] = True
        pre_ok, post_ok = ok & ~post, ok & post
        if pre_ok.sum() < 50 or post_ok.sum() < 50:
            continue
        e_pre = np.nanmedian(angular_error_deg(decode_stream(Y[pre_ok], W, mean, std),
                                               unit[pre_ok]))
        e_post = np.nanmedian(angular_error_deg(decode_stream(Y[post_ok], W, mean, std),
                                                unit[post_ok]))
        rows.append((ep.mode, e_pre, e_post))

    base = next((r for r in rows if r[0] == "NONE"), None)
    base_delta = (base[2] - base[1]) if base else 0.0

    print(f"{'mode':<20} {'pre-onset':>10} {'post-onset':>11} {'delta':>8} {'vs control':>11}")
    print("-" * 64)
    for mode, e_pre, e_post in rows:
        delta = e_post - e_pre
        print(f"{mode:<20} {e_pre:>9.2f}d {e_post:>10.2f}d {delta:>+7.2f}d "
              f"{delta - base_delta:>+10.2f}d")

    print(f"\n  The control's own drift is {base_delta:+.2f} deg. Same lesson as the")
    print("  injector: a before/after number has a floor that is not the fault.")
    print("  Column 4 is the one to read.")
    return 0


CAL_SEEDS = (11, 23, 37, 51, 73)   # draw variance is large; one seed is not enough

SEVERITY_SWEEP = {
    "RATE_LOSS":         [0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 0.95],
    "CHANNEL_DROPOUT":   [0.05, 0.15, 0.3, 0.45, 0.6, 0.8, 0.95],
    "GAIN_DRIFT":        [0.2, 0.5, 0.8, 1.2, 1.6, 2.2, 3.0],
    "GEOMETRY_ROTATION": [0.15, 0.45, 0.8, 1.2, 1.57, 2.0, 2.5],
}


def cmd_calibrate() -> int:
    """How severe does each mode have to be before decoding actually suffers?

    The design always specified two severity levels, "sub-threshold" and
    "threshold-crossing", and deliberately did NOT assume which numbers those
    were -- that is an empirical question about this decoder and this data.
    This command answers it.

    It matters because lead time is undefined for an event that never happens.
    If a mode never degrades performance, a monitor cannot warn "before" the
    degradation, and including it as a positive case would be incoherent.

    Severity is applied as a STEP at onset (no ramp), so the reported number is
    the effect of severity alone, uncontaminated by ramp shape.
    """
    if not DECODER_PATH.exists():
        raise SystemExit("no decoder -- run: python3 scripts/18_reference_decoder.py fit")
    d = np.load(DECODER_PATH)
    W, mean, std = d["W"], d["mean"], d["std"]
    meta = json.loads(META_PATH.read_text())

    spec = importlib.util.spec_from_file_location(
        "injector", REPO_ROOT / "scripts" / "17_fault_injector.py")
    inj = importlib.util.module_from_spec(spec)
    sys.modules["injector"] = inj
    spec.loader.exec_module(inj)

    loader = load_loader()
    ds = loader.load_dataset(participant="T11", load_neural=True, verbose=False)
    trials = pd.read_csv(OUT_DIR / "trials.csv")

    block_ids = meta["val_blocks"]
    print("Severity calibration -- how hard must each fault hit before it matters?")
    print(f"  blocks: {', '.join(block_ids)}")
    print("  step at onset, no ramp; error is median over post-onset scorable bins\n")

    # Control drift, measured on the same blocks, so every number below is a
    # change relative to doing nothing rather than a raw before/after.
    ctrl = []
    per_block = []
    for bid in block_ids:
        X = ds.neural[bid]; kin = ds.kinematics[bid]
        unit, ok_dir = intended_direction(kin)
        ok = ok_dir & in_trial_mask(trials, bid, X.shape[0])
        onset = int(round(0.4 * X.shape[0]))
        pre, post = ok.copy(), ok.copy()
        pre[onset:] = False; post[:onset] = False
        if pre.sum() < 50 or post.sum() < 50:
            continue
        e_pre = np.nanmedian(angular_error_deg(decode_stream(X[pre], W, mean, std), unit[pre]))
        e_post = np.nanmedian(angular_error_deg(decode_stream(X[post], W, mean, std), unit[post]))
        ctrl.append(e_post - e_pre)
        per_block.append((bid, X, unit, ok, onset, e_pre))
    ctrl_drift = float(np.mean(ctrl))
    print(f"  control drift (no fault at all): {ctrl_drift:+.2f} deg\n")

    results = {}
    for mode, grid in SEVERITY_SWEEP.items():
        print(f"{mode}")
        print(f"  {'severity':>9} {'delta err':>10} {'vs control':>11} {'sd':>9}")
        results[mode] = []
        for sev in grid:
            deltas = []
            for seed in CAL_SEEDS:
              for bid, X, unit, ok, onset, e_pre in per_block:
                groups = inj.feature_groups_for(X.shape[1], "nctx+spikePower")
                ep = inj.Episode(
                    episode_id="CAL", block_id=bid, n_bins=X.shape[0],
                    n_feats=X.shape[1], mode=mode, rate_label="step",
                    severity_label="sweep", severity=float(sev),
                    onset_bin=onset, ramp_bins=0, ramp_shape="linear",
                    seed=seed, feature_groups=groups)
                Y, _ = inj.apply_episode(X, ep)
                post = ok.copy(); post[:onset] = False
                e_post = np.nanmedian(
                    angular_error_deg(decode_stream(Y[post], W, mean, std), unit[post]))
                deltas.append(e_post - e_pre)
            delta = float(np.mean(deltas))
            spread = float(np.std(deltas))
            rel = delta - ctrl_drift
            results[mode].append((sev, rel, spread))
            print(f"  {sev:>9.2f} {delta:>+9.2f}d {rel:>+10.2f}d {spread:>8.2f}d")
        print()

    print("Reading this table:")
    print("  A mode is usable as a positive case only where 'vs control' is")
    print("  clearly positive. Where it stays near zero, the fault is real in the")
    print("  data but INVISIBLE TO THE DECODER -- there is no performance event,")
    print("  so there is nothing for a monitor to warn about, and lead time is")
    print("  undefined. Such a mode belongs in the corpus as a NEGATIVE case:")
    print("  a change a good monitor should NOT raise a failure warning about.")

    out = OUT_DIR / "severity_calibration.csv"
    rows = [{"mode": m, "severity": s, "delta_vs_control_deg": round(r, 3),
             "sd_across_seeds_and_blocks_deg": round(sd, 3)}
            for m, vals in results.items() for s, r, sd in vals]
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\n  wrote {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="fit and freeze the reference decoder")
    f.add_argument("--participant", default="T11")
    sub.add_parser("check", help="confirm degradation moves the performance number")
    sub.add_parser("calibrate", help="find the severity at which each mode bites")
    args = ap.parse_args()
    if args.cmd == "fit":
        return cmd_fit(args.participant)
    if args.cmd == "check":
        return cmd_check()
    return cmd_calibrate()


if __name__ == "__main__":
    raise SystemExit(main())
