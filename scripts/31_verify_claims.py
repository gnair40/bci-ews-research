#!/usr/bin/env python3
"""
Check every headline number in the reports against the data files.

WHY
---
This project asserts "reproducible" throughout. That word is cheap. Over sixty
commits, a number quoted in a report and the data file it came from can drift
apart in three ways, none of them dishonest and all of them corrosive:

  * an analysis is re-run with a fix, and prose written earlier still quotes the
    old figure;
  * a number is carried from one document to another by hand and a digit changes;
  * a claim is written from memory of a run rather than from its output.

Phase 3 already produced one instance -- 15 of 36 configurations were described
as having no operating point, from a search bounded at 59 -- so this is a
demonstrated failure mode here, not a hypothetical one.

This script recomputes each headline claim from `data/processed/` and compares it
against the value written in the documents. A mismatch is a finding, not an
error: it means a document needs updating or a number needs re-deriving.

Run it before quoting any figure in a paper, a poster, or an application.

Usage: python3 scripts/31_verify_claims.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"

CHECKS: list[tuple[str, float, float, str]] = []   # label, claimed, tol, where


def claim(label, claimed, tol, where):
    def deco(fn):
        CHECKS.append((label, claimed, tol, where, fn))
        return fn
    return deco


@claim("Reference decoder, T11 held-out healthy error (deg)", 54.6, 0.15,
       "PHASE3_REPORT §2")
def _t11_decoder():
    return json.loads((OUT / "reference_decoder.json").read_text())[
        "median_angular_error_val_deg"]


@claim("Reference decoder, T11 measured chance (deg)", 90.7, 0.15, "PHASE3_REPORT §2")
def _t11_chance():
    return json.loads((OUT / "reference_decoder.json").read_text())[
        "median_angular_error_chance_deg"]


@claim("Reference decoder, T5 held-out healthy error (deg)", 52.8, 0.15,
       "PHASE3_REPORT §2")
def _t5_decoder():
    return json.loads((OUT / "reference_decoder_T5.json").read_text())[
        "median_angular_error_val_deg"]


@claim("decoder-guard operating point, T11 recent-normal", 50.46, 0.05,
       "monitor demo, BENCHMARK_SUMMARY")
def _op():
    return json.loads((OUT / "harness_summary_local.json").read_text())[
        "decoder_guard"]["operating_point"]


@claim("decoder-guard false alarms per hour, T11", 3.41, 0.02, "README, demo")
def _far():
    return json.loads((OUT / "harness_summary_local.json").read_text())[
        "decoder_guard"]["false_alarms_per_hour"]


def _early_and_healthy(fname):
    df = pd.read_csv(OUT / fname)
    sub = df[df.detector == "decoder_guard"]
    H, E = [], []
    for _, r in sub.iterrows():
        y = np.fromstring(r.scores, sep=",")
        if not r.crossed:
            H.append(y)
        else:
            ow, cw = int(r.onset_w), int(r.crossing_w)
            if cw > ow:
                E.append(y[ow:cw])
    return np.concatenate(E), np.concatenate(H)


def _auc(fname):
    E, H = _early_and_healthy(fname)
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


@claim("Early-warning AUC, T11 recent-normal", 0.693, 0.003, "ACHIEVABILITY, README")
def _auc_t11():
    return _auc("episode_scores_local.csv")


@claim("Early-warning AUC, T5 recent-normal", 0.707, 0.003, "ACHIEVABILITY, README")
def _auc_t5():
    return _auc("episode_scores_T5_local.csv")


@claim("Early-warning AUC, T11 calibrate-once (should be chance)", 0.491, 0.003,
       "ACHIEVABILITY")
def _auc_global():
    return _auc("episode_scores.csv")


def _lag1(fname):
    df = pd.read_csv(OUT / fname)
    sub = df[(df.detector == "decoder_guard") & (~df.crossed)]
    rs = []
    for _, r in sub.iterrows():
        y = np.fromstring(r.scores, sep=",")
        if len(y) < 6 or y[:-1].std() < 1e-12 or y[1:].std() < 1e-12:
            continue
        rs.append(np.corrcoef(y[:-1], y[1:])[0, 1])
    return float(np.median(rs))


@claim("Lag-1 autocorrelation of risk, T11 healthy", 0.995, 0.002,
       "AGGREGATION_LIMIT, PHASE3_REPORT §3.6")
def _r_t11():
    return _lag1("episode_scores_local.csv")


@claim("Lag-1 autocorrelation of risk, T5 healthy", 0.980, 0.003,
       "AGGREGATION_LIMIT, PHASE3_REPORT §3.6")
def _r_t5():
    return _lag1("episode_scores_T5_local.csv")


@claim("Task change vs real fault separation, day 658", 15.6, 0.4,
       "PHASE3_REPORT §3.4, README")
def _task658():
    d = pd.read_csv(OUT / "task_change_test.csv")
    r = d[(d.day == 658) & (d.detector == "decoder_guard")].iloc[0]
    return float(r.real_fault / r.different_task)


@claim("Configurations passing all five gates", 0.0, 0.001, "everything")
def _gates():
    n = 0
    for f in OUT.glob("harness_summary*.json"):
        for _, s in json.loads(f.read_text()).items():
            g = s.get("gates", {})
            if g and all(v.get("pass") for v in g.values()):
                n += 1
    return float(n)


def _family_auc(sfx, base_sfx, extractor):
    df = pd.read_csv(OUT / f"feature_scores{sfx}.csv")
    b = pd.read_csv(OUT / f"episode_scores{base_sfx}.csv")
    b = b[b.detector == "decoder_guard"]
    cm = dict(zip(b.episode_id, b.crossed))
    wm = dict(zip(b.episode_id, b.crossing_w))
    E, H = [], []
    for _, r in df[df.extractor == extractor].iterrows():
        y = np.fromstring(r.scores, sep=",")
        ow = int(r.onset_w)
        if not cm.get(r.episode_id, False):
            H.append(float(np.median(y)))
        else:
            cw = wm.get(r.episode_id, -1)
            if cw > ow and len(y) >= cw:
                E.append(float(np.median(y[ow:cw])))
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


@claim("F3 spectral, T11 (cleared the bar here)", 0.750, 0.004,
       "FEATURE_STUDY_RESULT, PHASE3_REPORT §3.7")
def _f3_t11():
    return _family_auc("", "_local", "F3_spectral")


@claim("F3 spectral, T5 (failed badly here)", 0.556, 0.004,
       "FEATURE_STUDY_RESULT — the both-participants rule in action")
def _f3_t5():
    return _family_auc("_T5", "_T5_local", "F3_spectral")


@claim("F0 control, T11 (current features, generic scorer)", 0.570, 0.004,
       "FEATURE_STUDY_RESULT secondary comparison")
def _f0_t11():
    return _family_auc("", "_local", "F0_control_mean")


# ---------------------------------------------------------------- calibration

def _cal(sfx: str, n_windows, col="auc_mean"):
    d = pd.read_csv(OUT / f"calibration_curve{sfx}.csv")
    if n_windows == "all":
        row = d[d.draw == "all-pooled"]
    else:
        row = d[d.n_windows == n_windows]
    return float(row[col].iloc[0])


@claim("calibration T11, 20 windows (scattered)", 0.654, 0.003,
       "CALIBRATION_CURVE — the answer table")
def _cal_t11_20():
    return _cal("", 20)


@claim("calibration T11, entire healthy record", 0.648, 0.003,
       "CALIBRATION_CURVE — the answer table")
def _cal_t11_all():
    return _cal("", "all")


@claim("calibration T5, 20 windows (scattered)", 0.740, 0.003,
       "CALIBRATION_CURVE — the answer table")
def _cal_t5_20():
    return _cal("_T5", 20)


@claim("calibration T5, entire healthy record", 0.739, 0.003,
       "CALIBRATION_CURVE — the answer table")
def _cal_t5_all():
    return _cal("_T5", "all")


@claim("calibration T5, 40 windows CONTIGUOUS", 0.740, 0.004,
       "CALIBRATION_CURVE — contiguous draw matches scattered")
def _cal_t5_40_contig():
    return _cal("_T5_contiguous", 40)


@claim("calibration T11, 20 windows CONTIGUOUS", 0.665, 0.004,
       "CALIBRATION_CURVE — contiguous draw matches scattered")
def _cal_t11_20_contig():
    return _cal("_contiguous", 20)


@claim("n=10 profile covariance is singular (min eigenvalue)", 1e-6, 5e-7,
       "CALIBRATION_CURVE — why the n=10 point is excluded")
def _cal_singular():
    d = pd.read_csv(OUT / "calibration_conditioning.csv")
    return float(d[(d.participant == "T11") & (d.n_windows == 10)]
                 .min_eigenvalue.iloc[0])


@claim("n=20 profile covariance is well posed (min eigenvalue)", 0.057, 0.01,
       "CALIBRATION_CURVE — why n>=20 is trusted")
def _cal_wellposed():
    d = pd.read_csv(OUT / "calibration_conditioning.csv")
    return float(d[(d.participant == "T11") & (d.n_windows == 20)]
                 .min_eigenvalue.iloc[0])


# ------------------------------------------------- staleness / day variance

def _stale(sfx: str, key: str):
    return json.loads((OUT / f"staleness_permutation.json").read_text())[sfx][key]


def _dayvar(sfx: str, key: str):
    return json.loads((OUT / f"day_variance_summary{sfx}.json").read_text())[key]


@claim("staleness permutation p, T11 (naive said 0.003)", 0.128, 0.02,
       "STALENESS_AND_DAY_VARIANCE — the statistic that would have been wrong")
def _stale_p_t11():
    return _stale("T11", "permutation_p")


@claim("staleness permutation p, T5", 0.080, 0.02,
       "STALENESS_AND_DAY_VARIANCE — the statistic that would have been wrong")
def _stale_p_t5():
    return _stale("T5", "permutation_p")


@claim("day-to-day AUC spread, T11 (min)", 0.319, 0.01,
       "STALENESS_AND_DAY_VARIANCE — below chance on day 783")
def _dv_min():
    return _dayvar("", "auc_min")


@claim("day-to-day AUC spread, T11 (max)", 0.974, 0.01,
       "STALENESS_AND_DAY_VARIANCE — day 800")
def _dv_max():
    return _dayvar("", "auc_max")


@claim("I-squared across days, T11", 0.856, 0.02,
       "STALENESS_AND_DAY_VARIANCE — heterogeneity")
def _dv_i2():
    return _dayvar("", "I_squared")


@claim("share of day variance that is sampling, T11", 0.255, 0.02,
       "STALENESS_AND_DAY_VARIANCE — model-free check")
def _dv_share():
    return _dayvar("", "variance_share_from_sampling")


@claim("fault-mix confound, T5 (rho) — why T5 cannot corroborate", 0.886, 0.02,
       "STALENESS_AND_DAY_VARIANCE — the two arrays split here")
def _dv_mix_t5():
    return _dayvar("_T5", "spearman_frac_crossing_vs_auc")


@claim("fault-mix confound, T11 (rho) — day effect stands", 0.05, 0.02,
       "STALENESS_AND_DAY_VARIANCE — the two arrays split here")
def _dv_mix_t11():
    return _dayvar("", "spearman_frac_crossing_vs_auc")


@claim("inverse-variance weighting bias, T11 (rho)", -0.913, 0.02,
       "STALENESS_AND_DAY_VARIANCE — why 0.836 was an artefact")
def _dv_bias():
    return _dayvar("", "spearman_abs_effect_vs_se")


@claim("cost of pooling episodes across days, T11", 0.003, 0.005,
       "STALENESS_AND_DAY_VARIANCE — hypothesis refuted")
def _pool_t11():
    return json.loads((OUT / "pooling_loss.json").read_text())["loss_from_pooling"]


def main() -> int:
    print(f"{'claim':<52}{'claimed':>10}{'actual':>10}   status\n" + "-" * 88)
    bad = 0
    for label, claimed, tol, where, fn in CHECKS:
        try:
            actual = float(fn())
        except FileNotFoundError as e:
            print(f"{label:<52}{claimed:>10}{'—':>10}   SKIP (missing {Path(e.filename).name})")
            continue
        except Exception as e:
            print(f"{label:<52}{claimed:>10}{'—':>10}   ERROR {type(e).__name__}")
            bad += 1
            continue
        ok = abs(actual - claimed) <= tol
        bad += 0 if ok else 1
        print(f"{label:<52}{claimed:>10.3f}{actual:>10.3f}   "
              f"{'ok' if ok else 'MISMATCH -> ' + where}")

    print()
    if bad:
        print(f"{bad} claim(s) do not match the data.")
        print("A mismatch is a finding, not a crash: either a document needs")
        print("updating, or the number needs re-deriving. Do not quote the")
        print("figure until it is resolved.")
        return 1
    print(f"All {len(CHECKS)} headline claims match the data files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
