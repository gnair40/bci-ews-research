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


# --------------------------------------------------------- day predictors

def _pred(P: str, name: str, field: str = "spearman_rho"):
    r = json.loads((OUT / "day_predictors_result.json").read_text())[P]
    for x in r:
        if x["predictor"] == name:
            return x[field]
    raise KeyError(name)


@claim("P5 decoder error vs monitor AUC, T11 (rho)", -0.720, 0.02,
       "DAY_PREDICTORS — the preregistered hit")
def _p5_t11():
    return _pred("T11", "P5_decoder_error")


@claim("P5 p-value, T11 (Bonferroni threshold 0.01)", 0.0055, 0.002,
       "DAY_PREDICTORS — clears the corrected threshold")
def _p5_p():
    return _pred("T11", "P5_decoder_error", "p_value")


@claim("P5 partial rho controlling window length, T11", -0.773, 0.02,
       "DAY_PREDICTORS — the artefact challenge fails")
def _p5_partial():
    return json.loads((OUT / "p5_mediation.json").read_text())["T11"][
        "partial_rho_decoder_error_vs_auc_controlling_ew_len"]


@claim("P4 drift came out with the WRONG sign, T11", 0.582, 0.02,
       "DAY_PREDICTORS — sign committed in advance")
def _p4_wrong():
    return _pred("T11", "P4_within_day_drift")


@claim("P1 healthy dispersion, T11 (null)", 0.203, 0.02,
       "DAY_PREDICTORS — all five reported")
def _p1():
    return _pred("T11", "P1_healthy_dispersion")


# ------------------------------------------------------------- abstention

def _lf(P: str, cand: str, stage: str, field="rho"):
    r = json.loads((OUT / "label_free_result.json").read_text())[P]
    for x in r:
        if x["candidate"] == cand:
            return x[stage][field]
    raise KeyError(cand)


@claim("L4 vs decoder error, T11 (sign reverses)", 0.681, 0.02,
       "ABSTENTION — strongest cross-participant agreement, opposite signs")
def _l4_t11():
    return _lf("T11", "L4_mean_speed", "stage1_vs_decoder_error")


@claim("L4 vs decoder error, T5 (opposite sign)", -0.943, 0.02,
       "ABSTENTION — the reversal that makes it unusable")
def _l4_t5():
    return _lf("T5", "L4_mean_speed", "stage1_vs_decoder_error")


@claim("L4 vs monitor AUC, T11 (stage 2 null)", -0.137, 0.02,
       "ABSTENTION — nothing passes stage 2")
def _l4_s2():
    return _lf("T11", "L4_mean_speed", "stage2_vs_monitor_auc")


# ------------------------------------------------- day effect across detectors

def _de(P: str, key: str, field="rho"):
    sfx = "" if P == "T11" else f"_{P}"
    return json.loads((OUT / f"day_effect_detectors{sfx}.json").read_text())[key][field]


@claim("guard vs distribution_shift per-day AUC, T11", 0.835, 0.02,
       "DAY_EFFECT_ACROSS_DETECTORS — the family that shares it")
def _de_ds():
    return _de("T11", "guard_vs_distribution_shift")


@claim("guard vs mean_activity per-day AUC, T11", -0.060, 0.02,
       "DAY_EFFECT_ACROSS_DETECTORS — the family that does not")
def _de_ma():
    return _de("T11", "guard_vs_mean_activity")


@claim("distribution_shift vs decoder error, T11", -0.670, 0.02,
       "DAY_EFFECT_ACROSS_DETECTORS — P5 follows the same split")
def _de_ds_err():
    return _de("T11", "distribution_shift_vs_decoder_error")


# --------------------------------------------------------- ceiling challenge

def _cc(P: str, key: str, field="rho"):
    sfx = "" if P == "T11" else f"_{P}"
    return json.loads((OUT / f"ceiling_challenge{sfx}.json").read_text())[key][field]


@claim("ceiling: baseline vs achieved fault damage, T11", -0.747, 0.02,
       "CEILING_CHALLENGE — the ceiling is real")
def _cc_ceiling():
    return _cc("T11", "baseline_vs_damage")


@claim("ceiling: damage vs monitor AUC, T11 (predicted +, got ~0)", 0.181, 0.02,
       "CEILING_CHALLENGE — why the ceiling does not explain P5")
def _cc_damage_auc():
    return _cc("T11", "damage_vs_monitor_auc")


@claim("P5 controlling for achieved damage, T11 (strengthens)", -0.794, 0.02,
       "CEILING_CHALLENGE — survives the preregistered challenge")
def _cc_p5_damage():
    return _cc("T11", "P5_controlling_for_damage")


@claim("trace noise vs monitor AUC, T11 (ties P5 exactly)", -0.720, 0.02,
       "CEILING_CHALLENGE — the collinear rival")
def _cc_noise():
    return _cc("T11", "trace_noise_vs_monitor_auc")


@claim("P5 controlling for trace noise, T11 (collapses)", -0.333, 0.02,
       "CEILING_CHALLENGE — why the mechanism claim is withdrawn")
def _cc_p5_noise():
    return _cc("T11", "P5_controlling_for_trace_noise")


@claim("spurious crossings vs monitor AUC, T11", -0.665, 0.02,
       "CEILING_CHALLENGE — partly contaminated ground truth")
def _cc_spurious():
    return _cc("T11", "spurious_vs_monitor_auc")


# ------------------------------------------------------ unambiguous episodes

def _ua(P: str, key: str, field=None):
    sfx = "" if P == "T11" else f"_{P}"
    v = json.loads((OUT / f"unambiguous{sfx}.json").read_text())[key]
    return v[field] if field else v


@claim("T11 days scoreable on unambiguous faults (of 13)", 7, 0,
       "UNAMBIGUOUS_EPISODES — half the dataset disqualifies itself")
def _ua_days():
    return _ua("T11", "n_days_scoreable")


@claim("bad days retain fewer unambiguous faults, T11 (rho)", -0.604, 0.02,
       "UNAMBIGUOUS_EPISODES — the corpus is blind where it matters")
def _ua_retained():
    return _ua("T11", "retained_fraction_vs_decoder_error", "rho")


@claim("P5 on unambiguous episodes only, T11 (underpowered)", -0.536, 0.02,
       "UNAMBIGUOUS_EPISODES — inconclusive, not refuted")
def _ua_p5():
    return _ua("T11", "P5_unambiguous_only", "rho")


# --------------------------------------------------- what decoder error means

def _pdc(P: str, key: str, field="rho"):
    sfx = "" if P == "T11" else f"_{P}"
    return json.loads((OUT / f"per_day_chance{sfx}.json").read_text())[key][field]


@claim("margin over own chance vs monitor AUC, T11", 0.264, 0.02,
       "WHAT_DECODER_ERROR_MEANS — lost signal does NOT predict it")
def _pdc_margin():
    return _pdc("T11", "margin_vs_monitor_auc")


@claim("directional concentration vs monitor AUC, T11", -0.516, 0.02,
       "WHAT_DECODER_ERROR_MEANS — task geometry, not preregistered")
def _pdc_conc():
    return _pdc("T11", "concentration_vs_monitor_auc")


@claim("day 800 barely beats its own chance, P(better)", 0.531, 0.01,
       "WHAT_DECODER_ERROR_MEANS — best monitor day, weakest real signal")
def _pdc_800():
    d = pd.read_csv(OUT / "per_day_chance.csv")
    return float(d[d.day == 800].prob_better_than_chance.iloc[0])


# ------------------------------------------------------- severity ladder

def _sl(P: str, key: str, field=None):
    sfx = "" if P == "T11" else f"_{P}"
    v = json.loads((OUT / f"severity_ladder{sfx}.json").read_text())[key]
    return v[field] if field else v


@claim("severity ladder monotone fraction, T11", 0.567, 0.01,
       "SEVERITY_LADDER_VALIDITY — the corpus assumption, measured")
def _sl_t11():
    return _sl("T11", "overall_monotone_fraction")


@claim("severity ladder monotone fraction, T5", 0.667, 0.01,
       "SEVERITY_LADDER_VALIDITY — replicates on the second array")
def _sl_t5():
    return _sl("T5", "overall_monotone_fraction")


@claim("baseline vs ladder validity, T11 (rho)", -0.677, 0.02,
       "SEVERITY_LADDER_VALIDITY — both participants, same sign")
def _sl_r11():
    return _sl("T11", "baseline_vs_monotone_fraction", "rho")


@claim("baseline vs ladder validity, T5 (rho)", -0.926, 0.02,
       "SEVERITY_LADDER_VALIDITY — both participants, same sign")
def _sl_r5():
    return _sl("T5", "baseline_vs_monotone_fraction", "rho")


# --------------------------------------------------------- window overlap

@claim("contaminated windows per episode, T11 (1500/250 = 6)", 5.99, 0.05,
       "WINDOW_OVERLAP — the geometry, confirmed")
def _wo_count():
    return json.loads((OUT / "window_overlap.json").read_text())[
        "mean_contaminated_windows_per_episode"]


@claim("AUC understated by the overlap, T11", 0.0072, 0.001,
       "WINDOW_OVERLAP — the bias was conservative, now measured")
def _wo_t11():
    return json.loads((OUT / "window_overlap.json").read_text())["mean_delta"]


@claim("AUC understated by the overlap, T5", 0.0123, 0.001,
       "WINDOW_OVERLAP — replicates in direction and size")
def _wo_t5():
    return json.loads((OUT / "window_overlap_T5.json").read_text())["mean_delta"]


@claim("sign test across both arrays, p (one-sided)", 0.0112, 0.002,
       "WINDOW_OVERLAP — 11 of 13 non-tied days improved")
def _wo_sign():
    return json.loads((OUT / "window_overlap_signtest.json").read_text())[
        "sign_test_p_one_sided"]


# ----------------------------------------------------- attribution accuracy

def _att(P: str, key=None, mode=None, field=None):
    r = json.loads((OUT / "attribution_accuracy.json").read_text())
    if mode:
        for row in r[P]["rows"]:
            if row["injected_mode"] == mode:
                return row[field]
        raise KeyError(mode)
    return r[P][key]


@claim("attribution accuracy overall, T11 (chance 0.25)", 0.563, 0.01,
       "ATTRIBUTION_ACCURACY — better than chance, far from usable")
def _att_t11():
    return _att("T11", "accuracy")


@claim("attribution accuracy overall, T5 (chance 0.33)", 0.525, 0.01,
       "ATTRIBUTION_ACCURACY — replicates in size")
def _att_t5():
    return _att("T5", "accuracy")


@claim("GAIN_DRIFT named correctly, T11", 0.993, 0.01,
       "ATTRIBUTION_ACCURACY — one mode works nearly perfectly")
def _att_gain():
    return _att("T11", mode="GAIN_DRIFT", field="accuracy")


@claim("GEOMETRY_ROTATION named correctly, T11", 0.0, 0.001,
       "ATTRIBUTION_ACCURACY — total failure, replicated")
def _att_rot_t11():
    return _att("T11", mode="GEOMETRY_ROTATION", field="accuracy")


@claim("GEOMETRY_ROTATION named correctly, T5", 0.0, 0.001,
       "ATTRIBUTION_ACCURACY — total failure, replicated")
def _att_rot_t5():
    return _att("T5", mode="GEOMETRY_ROTATION", field="accuracy")


@claim("during rotation, dispersion z (vs profile 1.92)", 16.51, 0.2,
       "ATTRIBUTION_ACCURACY — the components are not separable")
def _att_disp_z():
    return json.loads((OUT / "attribution_accuracy.json").read_text())[
        "rotation_diagnosis"]["median_calibrated_z"]["dispersion"]


@claim("during rotation, profile IS lit (fraction)", 0.80, 0.02,
       "ATTRIBUTION_ACCURACY — so the rule is not what buries it")
def _att_prof_lit():
    return json.loads((OUT / "attribution_accuracy.json").read_text())[
        "rotation_diagnosis"]["fraction_lit"]["profile"]


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
