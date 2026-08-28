#!/usr/bin/env python3
"""
The grading system. Built BEFORE the monitor, on purpose.

WHY THE ORDER MATTERS
---------------------
If you build a detector first and a metric second, you choose the metric that
flatters the detector -- usually without noticing. Phase 1-2 lost a headline
result to exactly that family of mistake. So this file exists, and is committed,
before `decoder-guard` is written. The only detectors it can currently score are
three baselines, none of which this project invented.

WHAT IT MEASURES
----------------
    lead time        seconds between the monitor saying WARN and decoding
                     performance crossing its degradation threshold.
                     Positive means the warning came first.
    false-alarm rate WARNs per hour on episodes where nothing ever breaks.
    five gates       pass/fail conditions that come BEFORE any of the above is
                     allowed to be interpreted. The silence gate is first.

A single number cannot express this. A detector that warns instantly on
everything has infinite lead time and is useless; one that never warns has a
perfect false-alarm rate and is useless. They are reported as a pair, always,
and the operating point is chosen to satisfy the false-alarm constraint and
then left alone.

SPLITS
------
    fit    healthy windows from the decoder's own training days. Detectors are
           fitted here, on healthy data only, with no degradation labels.
    val    the decoder's held-out healthy days. The single free parameter -- the
           WARN threshold -- is chosen here to meet the false-alarm budget.
    test   every remaining day. Scored once.

Usage
-----
    python3 scripts/20_evaluation_harness.py run [--limit N] [--detector NAME]
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
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "data" / "processed"

# ---- windowing ----------------------------------------------------------
BIN_S = 0.02
WINDOW_BINS = 1500          # 30 s -- long enough to estimate a 384-channel mean
STEP_BINS = 250             # 5 s  -- the resolution of any lead-time claim
MIN_SCORABLE = 60           # bins of goal-directed movement needed to score a window

# ---- the performance event ---------------------------------------------
# Fixed in scripts/17 before any detector existed. Repeated here, not redefined.
THRESHOLD_DEG = 10.0
PERF_SMOOTH = 3             # windows of rolling median, so one noisy window is not an event

# ---- the state machine --------------------------------------------------
DWELL = 3                   # consecutive windows above threshold before a state is entered
WATCH_FRAC = 0.5            # WATCH threshold as a fraction of the WARN threshold
FAIL_MULT = 2.0             # FAIL-LIKELY threshold as a multiple of it

# ---- the operating point ------------------------------------------------
FALSE_ALARM_BUDGET_PER_HOUR = 0.1     # 1 false WARN per 10 hours of healthy record
THRESHOLD_GRID = np.concatenate([np.arange(1.0, 10.0, 0.25), np.arange(10.0, 60.0, 1.0)])

STATES = ("NOMINAL", "WATCH", "WARN", "FAIL-LIKELY")


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# STATE MACHINE
# --------------------------------------------------------------------------

def run_state_machine(score: np.ndarray, t_warn: float) -> np.ndarray:
    """Turn a risk series into states, with dwell and hysteresis.

    Dwell stops a single noisy window from raising an alarm. Hysteresis stops
    the state flapping up and down while the score sits on a threshold -- a
    monitor that chatters is one people learn to ignore, which is a failure
    mode that never shows up in an accuracy number.
    """
    t = np.array([0.0, t_warn * WATCH_FRAC, t_warn, t_warn * FAIL_MULT])
    out = np.zeros(len(score), dtype=int)
    cur = 0
    up = 0
    down = 0
    for i, s in enumerate(score):
        want = int(np.searchsorted(t, s, side="right") - 1)
        if want > cur:
            up += 1; down = 0
            if up >= DWELL:
                cur = want; up = 0
        elif want < cur:
            down += 1; up = 0
            # Falling back needs the score under the LOWER edge of the current
            # band, not merely under the band it is in -- that gap is the
            # hysteresis.
            if down >= DWELL and s < t[cur] * 0.8:
                cur = want; down = 0
        else:
            up = down = 0
        out[i] = cur
    return out


def first_index(states: np.ndarray, level: int) -> int | None:
    hit = np.flatnonzero(states >= level)
    return int(hit[0]) if len(hit) else None


# --------------------------------------------------------------------------
# PER-WINDOW PERFORMANCE
# --------------------------------------------------------------------------

def window_performance(Y, starts, win, ok, unit, dec) -> np.ndarray:
    """Median angular error per window, on scorable bins only. NaN if too few."""
    W, mean, std = dec
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        sl = slice(s, s + win)
        m = ok[sl]
        if m.sum() < MIN_SCORABLE:
            continue
        seg = Y[sl][m]
        Z = np.hstack([(seg - mean) / std, np.ones((len(seg), 1))])
        pred = Z @ W
        n = np.linalg.norm(pred, axis=1)
        good = n > 1e-12
        if good.sum() < MIN_SCORABLE:
            continue
        cos = np.einsum("ij,ij->i", pred[good] / n[good, None], unit[sl][m][good])
        out[i] = np.degrees(np.arccos(np.clip(cos, -1, 1))).mean()
    return out


def crossing_window(perf: np.ndarray, onset_w: int) -> int | None:
    """First window where smoothed performance exceeds the pre-onset baseline + threshold."""
    pre = perf[:onset_w]
    pre = pre[np.isfinite(pre)]
    if len(pre) < 3:
        return None
    base = float(np.median(pre))
    sm = pd.Series(perf).rolling(PERF_SMOOTH, min_periods=2).median().to_numpy()
    hit = np.flatnonzero(np.isfinite(sm) & (sm > base + THRESHOLD_DEG))
    hit = hit[hit >= onset_w]
    return int(hit[0]) if len(hit) else None


# --------------------------------------------------------------------------
# MAIN EVALUATION
# --------------------------------------------------------------------------

def evaluate(limit: int | None, only: str | None, participant: str = "T11",
             local: bool = False) -> int:
    inj = _load("injector", "17_fault_injector.py")
    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    ALL = {**det.BASELINES, **guard.DETECTORS}
    rd = _load("refdec", "18_reference_decoder.py")
    loader = _load("loader", "03_load_dataset.py")

    dec_path, meta_path = rd.decoder_paths(participant)
    dz = np.load(dec_path)
    dec = (dz["W"], dz["mean"], dz["std"])
    meta = json.loads(meta_path.read_text())
    plan, episodes = inj.load_plan(participant)

    ds = loader.load_dataset(participant=participant, load_neural=True, verbose=False)
    trials = pd.read_csv(OUT / "trials.csv")

    fit_blocks = set(meta["train_blocks"])
    val_blocks = set(meta["val_blocks"])
    all_blocks = sorted({e.block_id for e in episodes})
    test_blocks = [b for b in all_blocks if b not in fit_blocks and b not in val_blocks]

    print("Splits")
    print(f"  fit   {len(fit_blocks):>3} blocks -- detectors fitted here, healthy only")
    print(f"  val   {len(val_blocks):>3} blocks -- WARN threshold chosen here")
    print(f"  test  {len(test_blocks):>3} blocks -- scored once\n")

    # ---- geometry per block, computed once ------------------------------
    geom = {}
    for bid in all_blocks:
        X = ds.neural[bid]
        kin = ds.kinematics[bid]
        if "cursorPos" not in kin:
            continue
        unit, ok_dir = rd.intended_direction(kin)
        ok = ok_dir & rd.in_trial_mask(trials, bid, X.shape[0])
        starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(starts) < 12:
            continue
        geom[bid] = (starts, ok, unit)

    # ---- fit detectors on healthy windows -------------------------------
    Hs = []
    for bid in sorted(fit_blocks & set(geom)):
        starts, _, _ = geom[bid]
        Hs.append(det.window_features(ds.neural[bid], starts, WINDOW_BINS))
    H = np.vstack(Hs)
    print(f"Fitting detectors on {len(H)} healthy windows "
          f"({len(H) * STEP_BINS * BIN_S / 60:.0f} min of record)\n")

    names = [only] if only else list(ALL)
    detectors = {}
    for n in names:
        detectors[n] = ALL[n]().fit(H)
        print(f"  fitted {n}")

    # ---- score every episode --------------------------------------------
    eps = [e for e in episodes if e.block_id in geom]
    if limit:
        eps = eps[:limit]
    print(f"\nScoring {len(eps)} episodes...")

    rows = []
    by_block: dict[str, list] = {}
    for e in eps:
        by_block.setdefault(e.block_id, []).append(e)

    done = 0
    for bid, block_eps in by_block.items():
        X = ds.neural[bid]
        starts, ok, unit = geom[bid]
        split = ("fit" if bid in fit_blocks else "val" if bid in val_blocks else "test")

        for e in block_eps:
            Y, diag = inj.apply_episode(X, e)
            F = det.window_features(Y, starts, WINDOW_BINS)
            perf = window_performance(Y, starts, WINDOW_BINS, ok, unit, dec)
            onset_w = int(np.searchsorted(starts, e.onset_bin))
            cw = crossing_window(perf, onset_w)

            base = {
                "episode_id": e.episode_id, "block_id": bid, "split": split,
                "mode": e.mode, "rate": e.rate_label, "severity": e.severity_label,
                "onset_w": onset_w, "n_windows": len(starts),
                "crossing_w": -1 if cw is None else cw,
                "crossed": cw is not None,
                "clipped_fraction": round(diag.get("clipped_fraction", 0.0), 5),
            }
            for n, D in detectors.items():
                if local:
                    # Re-baseline on this episode's own pre-onset windows. Causal:
                    # only data from before the fault started is used, so nothing
                    # from the future leaks into the judgement.
                    pre = F[:onset_w]
                    if len(pre) >= 6:
                        D.recenter(pre)
                    else:
                        continue
                sc = D.score(F)
                row = {**base, "detector": n,
                       "scores": ",".join(f"{v:.4f}" for v in sc)}
                con = D.contributions(F)
                if con:
                    row["attribution"] = ",".join(con["attribution"])
                rows.append(row)
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(eps)}")

    df = pd.DataFrame(rows)
    suffix = ("" if participant == "T11" else f"_{participant}") + ("_local" if local else "")
    scores_path = OUT / f"episode_scores{suffix}.csv"
    df.to_csv(scores_path, index=False)
    print(f"\nwrote {scores_path}  ({len(df)} detector-episode rows)")

    # window time in seconds, needed for lead time
    meta_out = {
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "participant": participant,
        "window_bins": WINDOW_BINS, "step_bins": STEP_BINS, "bin_s": BIN_S,
        "threshold_deg": THRESHOLD_DEG, "dwell": DWELL,
        "false_alarm_budget_per_hour": FALSE_ALARM_BUDGET_PER_HOUR,
        "fit_blocks": sorted(fit_blocks), "val_blocks": sorted(val_blocks),
        "test_blocks": test_blocks,
        "detectors": list(detectors),
        "local_rebaseline": local,
        "n_episodes_scored": len(eps),
    }
    meta_out_path = OUT / f"harness_meta{suffix}.json"
    meta_out_path.write_text(json.dumps(meta_out, indent=2))
    print(f"wrote {meta_out_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="score every episode with every detector")
    r.add_argument("--limit", type=int)
    r.add_argument("--detector")
    r.add_argument("--participant", default="T11")
    r.add_argument("--local", action="store_true",
                   help="re-baseline each episode on its own pre-onset windows")
    a = ap.parse_args()
    return evaluate(a.limit, a.detector, a.participant, a.local)


if __name__ == "__main__":
    raise SystemExit(main())
