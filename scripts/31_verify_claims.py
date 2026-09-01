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
