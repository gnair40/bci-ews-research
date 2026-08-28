#!/usr/bin/env python3
"""
Turn scored episodes into the two numbers that matter, and run the five gates.

READ THE GATES FIRST
--------------------
The gates come before lead time in this report, and that ordering is not
cosmetic. Phase 1-2 produced a significant, publishable-looking trend that was
worthless because the indicator was also rising while the participant was
perfectly healthy. A detector that fails gate 1 has not earned the right to have
its lead time discussed.

    G1  SILENCE       no significant trend in risk during healthy operation
    G2  RATE          risk is not merely a restatement of total activity
    G3  COMPARATOR    beats counting spikes, at a matched false-alarm rate
    G4  TIME          survives controlling for elapsed time
    G5  DETREND       trend tests are run on de-trended series

THE OPERATING POINT
-------------------
One free parameter: the WARN threshold. It is chosen on the validation split as
the LOWEST threshold whose false-alarm rate fits the budget -- lowest because,
subject to the budget, earlier warnings are better. It is then frozen and
applied unchanged to the test split. The test split is read once.

Usage
-----
    python3 scripts/21_score_report.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "data" / "processed"
REPORTS = REPO_ROOT / "reports"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def parse_scores(s: str) -> np.ndarray:
    return np.fromstring(s, sep=",")


def detrend(y: np.ndarray) -> np.ndarray:
    """Remove a linear trend. Gate 5: monotonic drift is not an early warning.

    The Phase 1-2 preregistration omitted this, and that omission is precisely
    why steady electrode decline registered as p = 0.0002.
    """
    x = np.arange(len(y), dtype=float)
    ok = np.isfinite(y)
    if ok.sum() < 4:
        return y
    b, a = np.polyfit(x[ok], y[ok], 1)
    return y - (a + b * x)


def episode_outcome(scores, onset_w, crossing_w, t_warn, sm, step_s):
    """Lead time for one episode at one threshold, or a false alarm."""
    states = sm(scores, t_warn)
    warn_at = np.flatnonzero(states >= 2)
    warn_w = int(warn_at[0]) if len(warn_at) else None

    if crossing_w < 0:                       # nothing ever broke
        return {"false_alarm": warn_w is not None, "warn_w": warn_w,
                "lead_s": np.nan, "detected": False}

    if warn_w is None:
        return {"false_alarm": False, "warn_w": None, "lead_s": np.nan, "detected": False}

    # A warning raised before the fault even started is not prescience, it is a
    # false alarm that happens to sit in a positive episode. Counting it as a
    # very early detection would be the most flattering possible error.
    if warn_w < onset_w:
        return {"false_alarm": True, "warn_w": warn_w, "lead_s": np.nan, "detected": False}

    return {"false_alarm": False, "warn_w": warn_w,
            "lead_s": (crossing_w - warn_w) * step_s, "detected": True}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--participant", default="T11")
    args = ap.parse_args()
    sfx = "" if args.participant == "T11" else f"_{args.participant}"
    df = pd.read_csv(OUT / f"episode_scores{sfx}.csv")
    meta = json.loads((OUT / f"harness_meta{sfx}.json").read_text())
    print(f"Participant: {args.participant}")
    harness = _load("harness", "20_evaluation_harness.py")
    step_s = meta["step_bins"] * meta["bin_s"]
    budget = meta["false_alarm_budget_per_hour"]
    win_s = meta["window_bins"] * meta["bin_s"]

    print(f"Episodes scored: {df.episode_id.nunique()}   "
          f"detectors: {df.detector.nunique()}")
    print(f"Window {win_s:.0f}s, step {step_s:.0f}s, "
          f"performance threshold +{harness.THRESHOLD_DEG:.0f} deg\n")

    lines = []
    summary = {}

    for name, sub in df.groupby("detector"):
        print("=" * 72)
        print(f"DETECTOR: {name}")
        print("=" * 72)

        val = sub[sub.split == "val"]
        test = sub[sub.split == "test"]
        healthy_val = val[~val.crossed]
        healthy_test = test[~test.crossed]

        # ---------- gates, on healthy episodes only ----------
        g = {}

        # G1 SILENCE -- risk must not trend while nothing is wrong.
        taus, ps = [], []
        for _, r in healthy_test.iterrows():
            y = parse_scores(r.scores)
            if len(y) < 8:
                continue
            t, p = stats.kendalltau(np.arange(len(y)), y)
            if np.isfinite(t):
                taus.append(t); ps.append(p)
        n_sig = int(np.sum(np.array(ps) < 0.05)) if ps else 0
        frac_sig = n_sig / len(ps) if ps else np.nan
        g["G1_silence"] = {
            "n_healthy_episodes": len(ps),
            "median_tau": round(float(np.median(taus)), 3) if taus else None,
            "fraction_significant": round(frac_sig, 3) if ps else None,
            "pass": bool(ps) and frac_sig <= 0.10,
        }

        # G5 DETREND -- the same test after removing a linear trend.
        taus_d, ps_d = [], []
        for _, r in healthy_test.iterrows():
            y = detrend(parse_scores(r.scores))
            if len(y) < 8:
                continue
            t, p = stats.kendalltau(np.arange(len(y)), y)
            if np.isfinite(t):
                taus_d.append(t); ps_d.append(p)
        frac_sig_d = (np.mean(np.array(ps_d) < 0.05) if ps_d else np.nan)
        g["G5_detrend"] = {
            "fraction_significant_after_detrend": round(float(frac_sig_d), 3) if ps_d else None,
            "pass": bool(ps_d) and frac_sig_d <= 0.10,
        }

        # G2 RATE -- is the risk score just total activity wearing a hat?
        #    Correlate this detector's healthy series against mean_activity's.
        ma = df[(df.detector == "mean_activity") & (df.split == "test")]
        ma_map = dict(zip(ma.episode_id, ma.scores))
        rhos = []
        for _, r in healthy_test.iterrows():
            other = ma_map.get(r.episode_id)
            if other is None:
                continue
            a, b = parse_scores(r.scores), parse_scores(other)
            n = min(len(a), len(b))
            if n < 8:
                continue
            rho, _ = stats.spearmanr(a[:n], b[:n])
            if np.isfinite(rho):
                rhos.append(abs(rho))
        med_rho = float(np.median(rhos)) if rhos else np.nan
        g["G2_rate_invariance"] = {
            "median_abs_rho_vs_mean_activity": round(med_rho, 3) if rhos else None,
            "pass": bool(rhos) and med_rho < 0.6,
            "note": "not applicable to mean_activity itself" if name == "mean_activity" else "",
        }

        # G4 TIME -- does risk track elapsed time within a healthy block?
        tt = []
        for _, r in healthy_test.iterrows():
            y = parse_scores(r.scores)
            if len(y) < 8:
                continue
            rho, _ = stats.spearmanr(np.arange(len(y)), y)
            if np.isfinite(rho):
                tt.append(abs(rho))
        med_t = float(np.median(tt)) if tt else np.nan
        g["G4_elapsed_time"] = {
            "median_abs_rho_vs_time": round(med_t, 3) if tt else None,
            "pass": bool(tt) and med_t < 0.5,
        }

        # ---------- operating point, chosen on val ----------
        healthy_hours_val = (healthy_val.n_windows.sum() * step_s) / 3600 if len(healthy_val) else 0
        chosen = None
        for t_warn in harness.THRESHOLD_GRID:
            fa = 0
            for _, r in healthy_val.iterrows():
                o = episode_outcome(parse_scores(r.scores), r.onset_w, -1,
                                    t_warn, harness.run_state_machine, step_s)
                fa += int(o["false_alarm"])
            rate = fa / healthy_hours_val if healthy_hours_val else np.inf
            if rate <= budget:
                chosen = float(t_warn)
                break

        if chosen is None:
            print("  NO OPERATING POINT MEETS THE FALSE-ALARM BUDGET.")
            print(f"  Even the highest threshold tested ({harness.THRESHOLD_GRID[-1]:.0f}) "
                  f"produced more than {budget}/h on healthy validation data.")
            summary[name] = {"gates": g, "operating_point": None}
            continue

        # ---------- test, read once ----------
        leads, fa_test, n_pos, n_det = [], 0, 0, 0
        per_mode: dict[str, list] = {}
        for _, r in test.iterrows():
            o = episode_outcome(parse_scores(r.scores), r.onset_w, r.crossing_w,
                                chosen, harness.run_state_machine, step_s)
            if r.crossed:
                n_pos += 1
                if o["detected"]:
                    n_det += 1
                    leads.append(o["lead_s"])
                    per_mode.setdefault(r["mode"], []).append(o["lead_s"])
            if o["false_alarm"]:
                fa_test += 1
        healthy_hours_test = (healthy_test.n_windows.sum() * step_s) / 3600
        far = fa_test / healthy_hours_test if healthy_hours_test else np.nan

        med_lead = float(np.median(leads)) if leads else np.nan
        if len(leads) >= 8:
            bs = [np.median(np.random.default_rng(i).choice(leads, len(leads)))
                  for i in range(2000)]
            lo, hi = np.percentile(bs, [2.5, 97.5])
        else:
            lo = hi = np.nan

        print(f"\n  Operating point (chosen on val): WARN at risk > {chosen:.2f}")
        print(f"  Healthy record in test: {healthy_hours_test:.2f} h\n")
        print(f"  {'lead time (median)':<28} {med_lead:>8.1f} s")
        print(f"  {'  95% CI':<28} {lo:>8.1f} .. {hi:.1f} s" if np.isfinite(lo)
              else f"  {'  95% CI':<28} {'n/a':>8}")
        print(f"  {'detection rate':<28} {n_det}/{n_pos}")
        print(f"  {'false alarms':<28} {fa_test} = {far:.3f}/h  "
              f"(budget {budget}/h)")

        if per_mode:
            print(f"\n  {'by fault mode':<24} {'n':>4} {'median lead':>12}")
            for m, v in sorted(per_mode.items()):
                print(f"  {m:<24} {len(v):>4} {np.median(v):>10.1f} s")

        print(f"\n  {'GATE':<22} {'result':>10}   detail")
        for gk, gv in g.items():
            det_bits = ", ".join(f"{k}={v}" for k, v in gv.items()
                                 if k not in ("pass", "note") and v is not None)
            print(f"  {gk:<22} {'PASS' if gv['pass'] else 'FAIL':>10}   {det_bits}")

        summary[name] = {
            "gates": g,
            "operating_point": chosen,
            "median_lead_s": None if not np.isfinite(med_lead) else round(med_lead, 1),
            "lead_ci95": None if not np.isfinite(lo) else [round(lo, 1), round(hi, 1)],
            "detection_rate": f"{n_det}/{n_pos}",
            "false_alarms_per_hour": round(float(far), 4) if np.isfinite(far) else None,
            "healthy_hours_test": round(float(healthy_hours_test), 2),
            "by_mode_median_lead_s": {m: round(float(np.median(v)), 1)
                                      for m, v in per_mode.items()},
        }
        print()

    # ---------- attribution, for detectors that name a cause ----------
    if "attribution" in df.columns:
        att = df[df.attribution.notna() & (df.split == "test")]
        if len(att):
            print("=" * 72)
            print("ATTRIBUTION -- when it warns, does it name the right cause?")
            print("=" * 72)
            guard = _load("guard", "22_decoder_guard.py")
            exp = guard.EXPECTED_ATTRIBUTION
            print("  Scored only on episodes that actually crossed the performance")
            print("  threshold. Naming a cause for a fault that did no damage is a")
            print("  different question, and a warning nobody should have raised.\n")

            conf: dict[tuple[str, str], int] = {}
            for _, r in att[att.crossed].iterrows():
                labels = r.attribution.split(",")
                cw = int(r.crossing_w)
                seg = labels[int(r.onset_w):cw + 1] or labels[int(r.onset_w):]
                if not seg:
                    continue
                got = max(set(seg), key=seg.count)
                conf[(r["mode"], got)] = conf.get((r["mode"], got), 0) + 1

            modes = sorted({m for m, _ in conf})
            comps = sorted({c for _, c in conf})
            print(f"  {'injected fault':<20}" + "".join(f"{c:>13}" for c in comps)
                  + f"{'expected':>14}{'correct':>9}")
            total = right = 0
            for m in modes:
                n = sum(conf.get((m, c), 0) for c in comps)
                cells = "".join(f"{conf.get((m,c),0):>13}" for c in comps)
                e = exp.get(m, "-")
                ok = conf.get((m, e), 0)
                total += n; right += ok
                pct = f"{100*ok/n:.0f}%" if n else "-"
                print(f"  {m:<20}{cells}{e:>14}{pct:>9}")
            if total:
                print(f"\n  overall {right}/{total} = {100*right/total:.0f}% "
                      f"(chance with {len(comps)} components = {100/len(comps):.0f}%)")
            print("\n  Mismatches are reported, not corrected. The expected mapping was")
            print("  written down in scripts/22 before this was run.")
            print()

    # ---------- G3, across detectors ----------
    print("=" * 72)
    print("G3 COMPARATOR -- does anything beat counting spikes?")
    print("=" * 72)
    base = summary.get("mean_activity", {})
    base_lead = base.get("median_lead_s")
    print(f"  mean_activity median lead: {base_lead} s "
          f"(FAR {base.get('false_alarms_per_hour')}/h)\n")
    for n, s in summary.items():
        if n == "mean_activity":
            continue
        lead = s.get("median_lead_s")
        beat = (lead is not None and base_lead is not None and lead > base_lead)
        s["gates"]["G3_comparator"] = {
            "median_lead_s": lead, "baseline_lead_s": base_lead, "pass": bool(beat)}
        print(f"  {n:<24} {lead} s   {'PASS' if beat else 'FAIL'}")

    (OUT / "harness_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nwrote {OUT/'harness_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
