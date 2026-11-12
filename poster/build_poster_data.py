#!/usr/bin/env python3
"""
build_poster_data.py -- every number and every plotted point on the poster,
recomputed from data/processed/ and checked against the stored headline.

WHY THIS EXISTS
---------------
A poster is where a number is most likely to be typed from memory, and this
project's recurring failure is a value that was right where it was computed and
wrong where it was used. So nothing on the poster's computational charts is
typed. This script reads the stored results, recomputes what each chart plots,
and REFUSES TO WRITE if a recomputed value disagrees with the headline the
repository already publishes for it.

It computes nothing new. Every quantity here already exists in a report; this
only gathers them, with the file each came from, into one JSON the poster
builder reads.

WHAT IT DOES NOT CONTAIN
------------------------
No physical measurement, because none exists. The physical charts on the poster
are drawn in their "planned" state from the frozen preregistration alone.

Usage:
    python3 poster/build_poster_data.py          # writes poster/poster_data.json
"""
from __future__ import annotations

import csv
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
HERE = Path(__file__).resolve().parent

problems: list[str] = []


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(label: str, got, want, tol: float = 0.0) -> None:
    """A recomputed value must match the value the repository already quotes."""
    ok = (got == want) if tol == 0.0 else (abs(float(got) - float(want)) <= tol)
    print(f"   {'ok  ' if ok else 'FAIL'}  {label:<58} {got}  (stored: {want})")
    if not ok:
        problems.append(f"{label}: recomputed {got}, stored {want}")


def jload(name: str):
    return json.loads((OUT / name).read_text())


harness = _load("harness", "scripts/20_evaluation_harness.py")
score = _load("score21", "scripts/21_score_report.py")
STEP_S = harness.STEP_BINS * harness.BIN_S
WIN_S = harness.WINDOW_BINS * harness.BIN_S

data: dict = {
    "generated_by": "poster/build_poster_data.py",
    "window_s": WIN_S, "step_s": STEP_S,
    "performance_threshold_deg": harness.THRESHOLD_DEG,
}

# ---------------------------------------------------------------------------
# 1. Lead times at the frozen operating point -- the distribution, not only
#    its median. Uses scripts/21's own episode_outcome, so "a warning before
#    the onset is a false alarm, not a detection" is applied identically.
# ---------------------------------------------------------------------------
print("\n1. LEAD TIME at the stored operating point (scripts/21 logic)")
data["lead_time"] = {}
for part, sfx in (("T11", "_local"), ("T5", "_T5_local")):
    summ = jload(f"harness_summary{sfx}.json")["decoder_guard"]
    df = pd.read_csv(OUT / f"episode_scores{sfx}.csv")
    test = df[(df.detector == "decoder_guard") & (df.split == "test")]
    t_warn = float(summ["operating_point"])
    leads, n_pos = [], 0
    for _, r in test.iterrows():
        o = score.episode_outcome(score.series(r), r.onset_w, r.crossing_w, t_warn,
                                  harness.run_state_machine, STEP_S, "threshold")
        if r.crossed:
            n_pos += 1
            if o["detected"]:
                leads.append(float(o["lead_s"]))
    check(f"{part} detected / degraded episodes", f"{len(leads)}/{n_pos}",
          summ["detection_rate"])
    check(f"{part} median lead time (s)", float(np.median(leads)),
          float(summ["median_lead_s"]))
    data["lead_time"][part] = {
        "leads_s": sorted(leads), "n_detected": len(leads), "n_degraded": n_pos,
        "median_s": float(np.median(leads)),
        "ci95_s": summ.get("lead_ci95"),
        "fraction_positive": float(np.mean(np.array(leads) > 0)),
        "fraction_zero": float(np.mean(np.array(leads) == 0)),
        "fraction_negative": float(np.mean(np.array(leads) < 0)),
        "operating_point": t_warn,
        "false_alarms_per_hour": summ["false_alarms_per_hour"],
        "source": f"data/processed/episode_scores{sfx}.csv at the operating point "
                  f"in harness_summary{sfx}.json",
    }

# ---------------------------------------------------------------------------
# 2. AUC by fault mode, monitor against counting activity. Same computation as
#    scripts/23_benchmark_figures.py figure_auc(): window-level, descriptive,
#    no inference attached (see reports/UNIT_OF_ANALYSIS.md).
# ---------------------------------------------------------------------------
print("\n2. AUC BY FAULT MODE (scripts/23 figure_auc logic, window-level)")
MODES = ["RATE_LOSS", "CHANNEL_DROPOUT", "GAIN_DRIFT", "GEOMETRY_ROTATION"]
PUBLISHED = {   # reports/PHASE3_REPORT.md section 3.3, two decimals
    ("T11", "decoder_guard"): [0.61, 0.65, 0.79, 0.76],
    ("T11", "mean_activity"): [0.80, 0.73, 0.41, 0.52],
    ("T5", "decoder_guard"): [0.64, 0.75, 0.73, 0.71],
    ("T5", "mean_activity"): [0.78, 0.77, 0.40, 0.51],
}
data["fault_mode_auc"] = {"modes": MODES, "level": "window", "values": {}}
for part, fname in (("T11", "episode_scores_local.csv"),
                    ("T5", "episode_scores_T5_local.csv")):
    df = pd.read_csv(OUT / fname)
    data["fault_mode_auc"]["values"][part] = {}
    for det in ("decoder_guard", "mean_activity"):
        sub = df[df.detector == det]
        H = np.concatenate([np.fromstring(r.scores, sep=",")
                            for _, r in sub[~sub.crossed].iterrows()])
        vals = []
        for m in MODES:
            pool = []
            for _, r in sub[(sub.crossed) & (sub["mode"] == m)].iterrows():
                y = np.fromstring(r.scores, sep=",")
                ow, cw = int(r.onset_w), int(r.crossing_w)
                if cw > ow and len(y) >= cw:
                    pool.append(y[ow:cw])
            P = np.concatenate(pool)
            u, _ = stats.mannwhitneyu(P, H, alternative="two-sided")
            vals.append(float(u / (len(P) * len(H))))
        for m, v, want in zip(MODES, vals, PUBLISHED[(part, det)]):
            check(f"{part} {det} {m}", round(v, 2), want, tol=0.0051)
        data["fault_mode_auc"]["values"][part][det] = vals
data["fault_mode_auc"]["source"] = ("data/processed/episode_scores_local.csv, "
                                    "episode_scores_T5_local.csv")

# ---------------------------------------------------------------------------
# 3. Detection against false alarms per hour -- the full curve, threshold rule.
# ---------------------------------------------------------------------------
print("\n3. DETECTION vs FALSE ALARMS (data/processed/decision_rule_curves.csv)")
cur = pd.read_csv(OUT / "decision_rule_curves.csv")
data["detection_vs_fa"] = {"rule": "threshold", "curves": {},
                           "source": "data/processed/decision_rule_curves.csv"}
for part in ("T11", "T5"):
    c = cur[(cur.participant == part) & (cur.rule == "threshold")]
    pts = [[float(a), float(b)] for a, b in
           zip(c.false_alarms_per_hour, c.detection_fraction)]
    data["detection_vs_fa"]["curves"][part] = pts
    inside = [d for f, d in pts if f <= 0.1]
    print(f"   {part}: {len(pts)} points, best detection inside the 0.1/h budget: "
          f"{max(inside) if inside else 'no point inside budget'}")
    data["detection_vs_fa"][f"best_inside_budget_{part}"] = max(inside) if inside else None

# ---------------------------------------------------------------------------
# 4. Decision-rate curve on the archived data, with its paired test.
# ---------------------------------------------------------------------------
print("\n4. DECISION RATE (decision_rate_curve.json, decision_rate_paired.json)")
drc = jload("decision_rate_curve.json")
data["decision_rate"] = {"false_flag_rate": drc["false_flag_rate"], "curves": {},
                         "paired": jload("decision_rate_paired.json"),
                         "source": "data/processed/decision_rate_curve.json"}
for part, p in drc["participants"].items():
    data["decision_rate"]["curves"][part] = [
        {"per_hour": q["decisions_per_hour"], "detection": q["detection"],
         "lo": q["ci95"][0], "hi": q["ci95"][1],
         "n_fault_free": q["n_fault_free"], "n_positive": q["n_positive"]}
        for q in p["curve"]]
    first, last = p["curve"][0], p["curve"][-1]
    print(f"   {part}: {first['detection']:.3f} at {first['decisions_per_hour']:.0f}/h "
          f"-> {last['detection']:.3f} at {last['decisions_per_hour']:.0f}/h")

# ---------------------------------------------------------------------------
# 5. Per-session monitor accuracy against that session's decoder error (C09).
# ---------------------------------------------------------------------------
print("\n5. SESSION ACCURACY vs DECODER ERROR (day_predictors.csv, claim C09)")
dp = pd.read_csv(OUT / "day_predictors.csv")
rho, p = stats.spearmanr(dp["P5_decoder_error"], dp["auc"])
check("Spearman rho, decoder error vs session AUC (T11)", round(float(rho), 3), -0.720,
      tol=0.0006)
check("its p-value", round(float(p), 4), 0.0055, tol=0.00006)
dv = pd.read_csv(OUT / "day_variance.csv")
dv = dv[dv.participant == "T11"]
check("lowest session AUC (T11)", round(float(dv.auc.min()), 2), 0.32)
check("highest session AUC (T11)", round(float(dv.auc.max()), 2), 0.97)
data["session_scatter"] = {
    "participant": "T11", "n_sessions": int(len(dp)),
    "points": [{"day": int(d), "decoder_error_deg": float(e), "auc": float(a)}
               for d, e, a in zip(dp.day, dp["P5_decoder_error"], dp.auc)],
    "spearman_rho": float(rho), "p": float(p),
    "auc_min": float(dv.auc.min()), "auc_max": float(dv.auc.max()),
    "source": "data/processed/day_predictors.csv",
}

# ---------------------------------------------------------------------------
# 6. Scalars, each with its file.
# ---------------------------------------------------------------------------
print("\n6. SCALARS")
cert = {p: jload(f"monitorability_certificate_{p}.json") for p in ("T11", "T5")}
opb = jload("operating_point_bound.json")
ac = jload("autocorr_by_severity.json")["participants"]
slm = jload("session_level_monitor.json")["participants"]
ref = {"T11": jload("reference_decoder.json"), "T5": jload("reference_decoder_T5.json")}
inj = {"T11": jload("injection_plan.json"), "T5": jload("injection_plan_T5.json")}

bench = (REPO / "reports" / "BENCHMARK_SUMMARY.md").read_text()


def bench_count(label: str) -> int:
    m = re.search(r"\|\s*\**" + re.escape(label) + r"[^|]*\|\s*\**(\d+)\**\s*\|", bench)
    if not m:
        raise SystemExit(f"could not find '{label}' in BENCHMARK_SUMMARY.md")
    return int(m.group(1))


funnel = {
    "run": bench_count("Configurations run"),
    "operating_point": bench_count("Found any operating point"),
    "positive_lead": bench_count("Achieved a **positive** median lead time"),
    "met_budget": bench_count("Met the false-alarm budget"),
    "silence": bench_count("Passed the silence gate"),
    "all_gates": bench_count("Passed all five gates"),
}
check("benchmark funnel", list(funnel.values()), [48, 47, 10, 3, 0, 0])

tc = pd.read_csv(OUT / "task_change_test.csv")
g = tc[tc.detector == "decoder_guard"].set_index("day")
sep = {int(d): float(g.loc[d, "real_fault"] / g.loc[d, "different_task"]) for d in g.index}
check("task-change separation, day 658 (x)", round(sep[658], 1), 15.6)
check("task-change separation, day 665 (x)", round(sep[665]), 70, tol=0.5)

data["scalars"] = {
    "budget_per_hour": cert["T11"]["false_alarm_budget_per_hour"],
    "false_alarms_per_hour": {p: cert[p]["false_alarms_per_hour"] for p in cert},
    "median_lead_s": {p: cert[p]["median_lead_s"] for p in cert},
    "lead_ci95_s": {p: cert[p]["lead_ci95"] for p in cert},
    "detection_rate": {p: cert[p]["detection_rate"] for p in cert},
    "gates_passed": {p: [cert[p]["gates_passed"], cert[p]["gates_total"]] for p in cert},
    "fault_free_episodes": {p: ac[p]["silence_gate_by_severity"]["none"]["n_episodes"]
                            for p in ac},
    "silence_fault_free_fraction": {
        p: ac[p]["silence_gate_by_severity"]["none"]["fraction_significant"] for p in ac},
    "lag1_pooled": {p: ac[p]["pooled"]["1"]["ALL"]["lag1_r_median"] for p in ac},
    "n_eff_pooled": {p: ac[p]["pooled"]["1"]["ALL"]["n_eff"] for p in ac},
    "windows_per_session": {p: opb["by_participant"][p]["windows_per_episode"] for p in cert},
    "auc_session": {p: opb["by_participant"][p]["auc_ep"] for p in cert},
    "auc_needed_at_budget": {p: opb["by_participant"][p]["auc_ep_needed_at_budget"]
                             for p in cert},
    "fpr_per_decision_720": opb["by_participant"]["T11"]["fpr"],
    "fpr_per_session": {p: opb["by_participant"][p]["fpr_ep_budget"] for p in cert},
    "decoder_error_deg": {p: ref[p]["median_angular_error_val_deg"] for p in ref},
    "decoder_chance_deg": {p: ref[p]["median_angular_error_chance_deg"] for p in ref},
    "episodes": {p: inj[p]["n_episodes"] for p in inj},
    "injection_commit": inj["T11"]["git_commit"][:7],
    "funnel": funnel,
    "task_change_separation": sep,
    "session_level_correlation_T11": {
        "series": slm["T11"]["series"],
        "failure_threshold_deg": slm["T11"]["failure_threshold_deg"],
        "n_sessions": slm["T11"]["n_sessions"],
        "raw": slm["T11"]["robustness"]["raw_rho"],
        "partial": slm["T11"]["robustness"]["partial_rho"],
        "diff": slm["T11"]["robustness"]["diff_rho"],
        "status": "exploratory, not preregistered",
    },
}
s = data["scalars"]
check("T11 false alarms per hour", round(s["false_alarms_per_hour"]["T11"], 2), 3.41)
check("T5 false alarms per hour", round(s["false_alarms_per_hour"]["T5"], 3), 0.225)
check("T11 lag-1 autocorrelation", round(s["lag1_pooled"]["T11"], 3), 0.995)
check("T5 lag-1 autocorrelation", round(s["lag1_pooled"]["T5"], 3), 0.980)
check("T11 fault-free episodes trending", round(s["silence_fault_free_fraction"]["T11"], 3),
      0.765)
check("T5 fault-free episodes trending", round(s["silence_fault_free_fraction"]["T5"], 3), 1.0)
check("T11 session AUC", round(s["auc_session"]["T11"], 3), 0.673)
check("T5 session AUC", round(s["auc_session"]["T5"], 3), 0.742)
check("T11 session AUC needed at budget", round(s["auc_needed_at_budget"]["T11"], 3), 0.990)
check("T5 session AUC needed at budget", round(s["auc_needed_at_budget"]["T5"], 3), 0.991)
check("T11 decoder error (deg)", round(s["decoder_error_deg"]["T11"], 1), 54.6)
check("T11 measured chance (deg)", round(s["decoder_chance_deg"]["T11"], 1), 90.7)
check("T5 decoder error (deg)", round(s["decoder_error_deg"]["T5"], 1), 52.8)
check("T5 measured chance (deg)", round(s["decoder_chance_deg"]["T5"], 1), 84.9)
check("session-level partial rho, T11", round(s["session_level_correlation_T11"]["partial"], 3),
      -0.500, tol=0.0006)
check("session-level first-difference rho, T11",
      round(s["session_level_correlation_T11"]["diff"], 3), -0.679)
check("episodes T11 + T5", s["episodes"]["T11"] + s["episodes"]["T5"], 1850)
check("session-level raw rho, T11", round(s["session_level_correlation_T11"]["raw"], 3),
      -0.818)

# ---------------------------------------------------------------------------
# 7. One real episode, for the figure that defines lead time.
#
#    Chosen by a rule, not by eye: the FIRST test-split episode, in file order,
#    whose lead time equals the median. That is the typical case, and the
#    typical case is a late warning.
#
#    reports/monitor_demo.html offers ready-made "early" and "late" examples
#    and they are NOT used here. scripts/30_export_demo.py picks them with a
#    bare threshold, while the benchmark uses the WARN state machine and counts
#    a warning raised before the onset as a false alarm. Under the benchmark's
#    rule the demo's "early" episode (EP00170) warns one window before its
#    onset, so it is a false alarm, not an early detection. Recorded in the
#    research log, 12 November 2026.
# ---------------------------------------------------------------------------
print("\n7. THE MEDIAN EPISODE (first test episode whose lead equals the median)")
df = pd.read_csv(OUT / "episode_scores_local.csv")
test = df[(df.detector == "decoder_guard") & (df.split == "test") & (df.crossed)]
t_warn = float(jload("harness_summary_local.json")["decoder_guard"]["operating_point"])
median_lead = data["lead_time"]["T11"]["median_s"]
chosen = None
for _, r in test.iterrows():
    o = score.episode_outcome(score.series(r), r.onset_w, r.crossing_w, t_warn,
                              harness.run_state_machine, STEP_S, "threshold")
    if o["detected"] and float(o["lead_s"]) == median_lead:
        chosen = (r, o)
        break
if chosen is None:
    problems.append("no test episode has a lead time equal to the median")
else:
    r, o = chosen
    delay = (int(o["warn_w"]) - int(r.onset_w)) * STEP_S
    print(f"   {r.episode_id}  {r.block_id}  {r['mode']}  onset w{int(r.onset_w)}  "
          f"warn w{int(o['warn_w'])}  failure w{int(r.crossing_w)}  "
          f"lead {float(o['lead_s']):+.0f} s  detection delay {delay:+.0f} s")
    data["median_episode"] = {
        "id": r.episode_id, "block": r.block_id, "mode": r["mode"],
        "severity": r.severity, "rate": r.rate,
        "risk": [float(x) for x in score.series(r)],
        "n_windows": int(r.n_windows),
        "onset_w": int(r.onset_w), "warn_w": int(o["warn_w"]),
        "crossing_w": int(r.crossing_w),
        "lead_s": float(o["lead_s"]), "detection_delay_s": float(delay),
        "warn_threshold": t_warn,
        "selection_rule": "first test-split episode, in file order, whose lead time "
                          "equals the median lead time",
        "source": "data/processed/episode_scores_local.csv",
    }

# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
if problems:
    print("FAIL -- nothing written. A poster number disagrees with the repository:")
    for q in problems:
        print("   " + q)
    raise SystemExit(1)
(HERE / "poster_data.json").write_text(json.dumps(data, indent=1))
print("PASS -- every recomputed value matches its stored headline.")
print(f"wrote {(HERE / 'poster_data.json').relative_to(REPO)}")
