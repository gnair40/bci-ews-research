#!/usr/bin/env python3
"""
Assemble every scored configuration into one table.

The point of reporting the whole matrix rather than a best row is that a
best row, selected after the fact from a grid, is not a result -- it is the
maximum of a set of noisy numbers. Every configuration that was run appears
here, including the ones that failed and the ones that could not even find an
operating point.

Usage: python3 scripts/24_benchmark_matrix.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

BASELINES = [("", "calibrate once"), ("_local", "recent normal")]
TRANSFORMS = [("", "none"), ("_detrend", "detrend"),
              ("_trailing", "trailing"), ("_prez", "pre-onset z")]
PARTICIPANTS = [("", "T11"), ("_T5", "T5")]
ORDER = ["decoder_guard", "mean_activity", "robust_dispersion", "distribution_shift"]
NICE = {"decoder_guard": "decoder-guard", "mean_activity": "mean activity",
        "robust_dispersion": "robust dispersion", "distribution_shift": "distribution shift"}

GATES = ["G1_silence", "G2_rate_invariance", "G3_comparator",
         "G4_elapsed_time", "G5_detrend"]


def main() -> int:
    rows = []
    for psfx, pname in PARTICIPANTS:
        for bsfx, bname in BASELINES:
            for tsfx, tname in TRANSFORMS:
                f = OUT / f"harness_summary{psfx}{bsfx}{tsfx}.json"
                if not f.exists():
                    continue
                data = json.loads(f.read_text())
                for det in ORDER:
                    if det not in data:
                        continue
                    s = data[det]
                    g = s.get("gates", {})
                    rows.append({
                        "participant": pname, "baseline": bname, "transform": tname,
                        "detector": det,
                        "lead": s.get("median_lead_s"),
                        "far": s.get("false_alarms_per_hour"),
                        "silence": (g.get("G1_silence") or {}).get("fraction_significant"),
                        "n_pass": sum(1 for k in GATES
                                      if (g.get(k) or {}).get("pass") is True),
                        "op": s.get("operating_point"),
                        "det_rate": s.get("detection_rate"),
                    })

    L = []
    A = L.append
    A("# Benchmark summary — every configuration\n")
    A("**Reproduce:** `python3 scripts/24_benchmark_matrix.py` after running "
      "`scripts/20_evaluation_harness.py` and `scripts/21_score_report.py` "
      "across the grid.\n")

    n_total = len(rows)
    n_op = sum(1 for r in rows if r["op"] is not None)
    n_pos = sum(1 for r in rows if (r["lead"] or -1) > 0)
    n_budget = sum(1 for r in rows if r["far"] is not None and r["far"] <= 0.1)
    n_silence = sum(1 for r in rows if r["silence"] is not None and r["silence"] <= 0.10)
    n_all = sum(1 for r in rows if r["n_pass"] == len(GATES))

    A("> **Correction, 28 Aug.** An earlier version of this table searched WARN "
      "thresholds only up to 59, while observed scores reach 300 "
      "(`decoder-guard`) and 3200 (`distribution_shift`). Configurations were "
      "therefore reported as having no operating point when the truth was that "
      "none existed *below an arbitrary bound*. The grid now spans the range the "
      "scores occupy and every row here is from the corrected search.\n")
    A("## The headline\n")
    A(f"| | count | of {n_total} |")
    A("|---|---|---|")
    A(f"| Configurations run | {n_total} | — |")
    A(f"| Found any operating point at all | {n_op} | {100*n_op/n_total:.0f}% |")
    A(f"| Achieved a **positive** median lead time | {n_pos} | {100*n_pos/n_total:.0f}% |")
    A(f"| Met the false-alarm budget (≤0.1/h) | {n_budget} | {100*n_budget/n_total:.0f}% |")
    A(f"| Passed the silence gate (≤10% of healthy episodes trend) | "
      f"**{n_silence}** | {100*n_silence/n_total:.0f}% |")
    A(f"| **Passed all five gates** | **{n_all}** | {100*n_all/n_total:.0f}% |")
    A("")
    A("> The binding constraint is not detection. Several configurations warn "
      "before performance falls. The constraint is **specificity**: the risk "
      "signal is never quiet during healthy operation, so any threshold low "
      "enough to catch a fault early also fires constantly on healthy record.\n")

    A("## Every configuration\n")
    A("| Participant | Baseline | Transform | Detector | Lead (s) | Detected | "
      "False alarms/h | Healthy episodes trending | Gates passed |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lead = "—" if r["op"] is None else f"{r['lead']}"
        far = "—" if r["far"] is None else f"{r['far']:.2f}"
        sil = "—" if r["silence"] is None else f"{r['silence']*100:.0f}%"
        note = " *(no operating point)*" if r["op"] is None else ""
        dr = r.get("det_rate") or "—"
        # Flag a lead time computed from almost nothing. A two-minute warning on
        # one episode out of 219 is not a fast detector, it is a silent one that
        # fired once, and without this marker the table would read as a success.
        if isinstance(dr, str) and "/" in dr:
            hit, tot = (int(v) for v in dr.split("/"))
            if tot and hit / tot < 0.05:
                dr = f"{dr} ⚠"
        A(f"| {r['participant']} | {r['baseline']} | {r['transform']} | "
          f"`{NICE.get(r['detector'], r['detector'])}` | {lead}{note} | {dr} | {far} | "
          f"{sil} | {r['n_pass']}/5 |")
    A("")

    A("⚠ marks a lead time computed from fewer than 5% of the fault episodes. "
      "A long lead measured on one or two detections is not a fast detector; it "
      "is a near-silent one that happened to fire early, and the two are easy to "
      "confuse in a table.\n")

    A("## The tradeoff, stated as a rule\n")
    usable = [r for r in rows if r["far"] is not None and r["far"] <= 0.1
              and r.get("det_rate")]
    A("Across the whole grid, a configuration either detects a meaningful share "
      "of faults and false-alarms far past budget, or meets budget and barely "
      "fires at all. The single configuration meeting the false-alarm budget "
      "with a positive lead time (T5, recent normal, trailing, robust "
      "dispersion: **+115 s**) detected **1 fault in 219**. There is no middle "
      "of this curve in the data as it stands.\n")

    best = min((r for r in rows if r["silence"] is not None),
               key=lambda r: r["silence"], default=None)
    if best:
        A("## Closest approach to the silence gate\n")
        A(f"`{NICE.get(best['detector'])}` — {best['participant']}, "
          f"{best['baseline']} baseline, {best['transform']} transform: "
          f"**{best['silence']*100:.0f}%** of healthy episodes still show a "
          f"significant trend, against a **10%** requirement.\n")
        A("A trailing reference is what moves this number, and it moves it by "
          "roughly half. It does not get close to passing.\n")

    out = REPORTS / "BENCHMARK_SUMMARY.md"
    out.write_text("\n".join(L))
    print(f"wrote {out}  ({n_total} configurations)")
    print(f"  passed all gates: {n_all}")
    print(f"  best silence-gate result: "
          f"{best['silence']*100:.0f}% (need <=10%)" if best else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
