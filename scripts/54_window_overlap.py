#!/usr/bin/env python3
"""
How much does window-overlap contamination cost?

Prediction committed in research/WINDOW_OVERLAP_NOTE.md before running: removing
the contaminated windows should RAISE AUC slightly on both participants, because
contaminating the healthy reference with faulted data drags the reference toward
the fault and makes detection harder.

THE DEFECT
----------
Windows are 1500 bins long, stepped every 250. Local re-baselining takes an
episode's pre-onset windows as F[:ow] where ow is the first window STARTING at or
after onset -- but a window starting before onset still extends 1500 bins past
its start, so up to 6 of them contain faulted data while counted as healthy.

Both references are computed on the SAME episodes in the same pass, so this is a
paired comparison and nothing but the reference changes.

Usage: python3 scripts/54_window_overlap.py --participant T11|T5
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
WINDOW_BINS, STEP_BINS = 1500, 250
FIT_WINDOWS = 40
EPISODES_PER_DAY = 40
MIN_CLEAN = 3
SEED = 20260902


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def auc(E, H):
    if len(E) < 5 or len(H) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def day_of(b): return int(re.search(r"day_(\d+)", b).group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    P = args.participant

    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    inj = _load("inj", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")

    _, episodes = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)

    healthy: dict[int, np.ndarray] = {}
    for b, X in ds.neural.items():
        st = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
        if len(st) == 0:
            continue
        F = det.window_features(X, st, WINDOW_BINS)
        d = day_of(b)
        healthy[d] = F if d not in healthy else np.vstack([healthy[d], F])
    days = sorted(d for d, F in healthy.items() if len(F) >= FIT_WINDOWS)

    sc = pd.read_csv(OUT / f"episode_scores{'_local' if P=='T11' else '_T5_local'}.csv")
    sc = sc[sc.detector == "decoder_guard"]
    crossed = dict(zip(sc.episode_id, sc.crossed))
    crossing = dict(zip(sc.episode_id, sc.crossing_w))

    rng = np.random.default_rng(SEED)
    by_day: dict[int, list] = {}
    for e in episodes:
        if e.block_id in ds.neural:
            by_day.setdefault(day_of(e.block_id), []).append(e)

    rows, contaminated_counts = [], []
    for day in days:
        eps = by_day.get(day, [])
        if len(eps) > EPISODES_PER_DAY:
            eps = [eps[i] for i in rng.choice(len(eps), EPISODES_PER_DAY, replace=False)]
        r = np.random.default_rng(SEED + day)
        g = guard.DecoderGuard().fit(
            healthy[day][r.choice(len(healthy[day]), FIT_WINDOWS, replace=False)])

        E_loose, E_strict, H_loose, H_strict = [], [], [], []
        for e in eps:
            X = ds.neural[e.block_id]
            starts = np.arange(0, X.shape[0] - WINDOW_BINS + 1, STEP_BINS)
            if len(starts) < 12:
                continue
            ow = int(np.searchsorted(starts, e.onset_bin))
            # Strictly clean: the window must END at or before onset.
            ow_strict = int(np.searchsorted(starts + WINDOW_BINS, e.onset_bin,
                                            side="right"))
            if ow < 6 or ow_strict < MIN_CLEAN:
                continue          # excluded from BOTH arms, so the pair holds
            contaminated_counts.append(ow - ow_strict)

            Y, _ = inj.apply_episode(X, e)
            F = det.window_features(Y, starts, WINDOW_BINS)

            g.recenter(F[:ow])
            s_loose = g.score(F)
            g.recenter(F[:ow_strict])
            s_strict = g.score(F)

            if not crossed.get(e.episode_id, False):
                H_loose.append(float(np.median(s_loose)))
                H_strict.append(float(np.median(s_strict)))
            else:
                cw = crossing.get(e.episode_id, -1)
                if cw > ow and len(s_loose) >= cw:
                    E_loose.append(float(np.median(s_loose[ow:cw])))
                    E_strict.append(float(np.median(s_strict[ow:cw])))

        a_l, a_s = auc(E_loose, H_loose), auc(E_strict, H_strict)
        if not (np.isfinite(a_l) and np.isfinite(a_s)):
            continue
        rows.append({"day": day, "n_faulted": len(E_loose), "n_healthy": len(H_loose),
                     "auc_loose": round(a_l, 4), "auc_strict": round(a_s, 4),
                     "delta": round(a_s - a_l, 4)})
        print(f"  day {day}: loose {a_l:.4f}   strict {a_s:.4f}   "
              f"delta {a_s - a_l:+.4f}")

    D = pd.DataFrame(rows)
    sfx = "" if P == "T11" else f"_{P}"
    D.to_csv(OUT / f"window_overlap{sfx}.csv", index=False)

    res = {
        "participant": P, "n_days": int(len(D)),
        "mean_contaminated_windows_per_episode":
            round(float(np.mean(contaminated_counts)), 2) if contaminated_counts else None,
        "mean_delta": round(float(D.delta.mean()), 4),
        "median_delta": round(float(D.delta.median()), 4),
        "max_abs_delta": round(float(D.delta.abs().max()), 4),
        "days_improved": int((D.delta > 0).sum()),
        "days_worsened": int((D.delta < 0).sum()),
    }
    if len(D) >= 5:
        # Paired test: same episodes, only the reference differs.
        w, p = stats.wilcoxon(D.auc_strict, D.auc_loose)
        res["wilcoxon_p"] = round(float(p), 4)
        res["direction_matches_prediction"] = bool(res["mean_delta"] > 0)
    print("\n" + json.dumps(res, indent=2))
    (OUT / f"window_overlap{sfx}.json").write_text(json.dumps(res, indent=2))

    sign_test_across_participants()
    return 0


def sign_test_across_participants() -> None:
    """Combined sign test, once both participants' files exist.

    Most of the Wilcoxon's power goes to ties -- six of nineteen days come out
    exactly equal -- so the per-participant tests look weak at p = 0.13. The
    direction was committed before running, so a one-sided sign test across both
    arrays is the appropriate test, and it is computed HERE rather than in an
    ad-hoc shell one-liner. It was written that way first, which left
    31_verify_claims.py depending on a file no committed script produced; the
    reproducibility audit caught it.
    """
    parts = []
    for f in ("window_overlap.csv", "window_overlap_T5.csv"):
        if (OUT / f).exists():
            parts.append(pd.read_csv(OUT / f))
    if len(parts) < 2:
        print("\n(sign test skipped: run both participants first)")
        return
    d = pd.concat(parts)
    nz = d[d.delta != 0]
    up, n = int((nz.delta > 0).sum()), len(nz)
    if n == 0:
        return
    out = {
        "n_days_total": int(len(d)),
        "n_tied_exactly": int((d.delta == 0).sum()),
        "n_nonzero": n, "n_improved": up, "n_worsened": n - up,
        "sign_test_p_one_sided":
            round(float(stats.binomtest(up, n, 0.5, alternative="greater").pvalue), 4),
        "sign_test_p_two_sided":
            round(float(stats.binomtest(up, n, 0.5, alternative="two-sided").pvalue), 4),
        "pooled_mean_delta": round(float(d.delta.mean()), 4),
        "pooled_max_delta": round(float(d.delta.max()), 4),
    }
    (OUT / "window_overlap_signtest.json").write_text(json.dumps(out, indent=2))
    print("\nsign test across both participants:")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
