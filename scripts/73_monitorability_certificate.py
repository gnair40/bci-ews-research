#!/usr/bin/env python3
"""
73_monitorability_certificate.py
================================
The instrument's output: can this sensor array be health-monitored, and at what
cost in false alarms?

WHAT THIS IS FOR
----------------
This project spent its computational half finding out that a decoder-health
monitor could not be made to work on chronic intracortical recordings: across 48
configurations, none passed all five gates, and the binding constraint was
specificity rather than detection (reports/BENCHMARK_SUMMARY.md). A negative
result of that kind is a measured limit, and a measured limit is what an
instrument exists to report.

So this is the readout. Point it at any system that has been through the
standard pipeline -- the archived neural recordings, or the physical rig -- and
it answers the same four questions in the same way, so the two can be compared
directly for the first time:

  * how much genuinely independent evidence one recording session holds,
  * how early a warning arrives,
  * what that warning costs when nothing is wrong,
  * and whether the pair is good enough to be worth deploying.

WHY A CERTIFICATE AND NOT A SCORE
---------------------------------
A single score would hide the thing that matters. Lead time and false-alarm rate
trade against each other: either can be made to look excellent by sacrificing
the other, so neither is interpretable alone. Every row below is reported with
the operating point that produced it, and the verdict is explicitly conditional
on a stated false-alarm budget rather than absolute.

The certificate also prints the estimator's ceiling at the series length
actually available. A lag-1 autocorrelation measured on ten windows cannot
exceed about 0.60 however strongly correlated the signal really is
(reports/AUTOCORR_BY_SEVERITY.md), and a reader who does not know that will read
a number near the ceiling as a finding rather than as a limit.

Usage:
    python3 scripts/73_monitorability_certificate.py
    python3 scripts/73_monitorability_certificate.py --participant T5
    python3 scripts/73_monitorability_certificate.py --budget 0.05
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"

GATES = ["G1_silence", "G2_rate_invariance", "G3_comparator",
         "G4_elapsed_time", "G5_detrend"]
GATE_LABEL = {
    "G1_silence": "Silence — quiet when nothing is wrong",
    "G2_rate_invariance": "Rate invariance — not just total activity",
    "G3_comparator": "Comparator — beats counting spikes",
    "G4_elapsed_time": "Elapsed time — not just tracking the clock",
    "G5_detrend": "Detrend — silence survives removing a linear trend",
}
DEFAULT_BUDGET = 0.1            # false alarms per hour


def summary_path(participant: str) -> Path:
    """The harness summary for a participant, preferring the local-baseline run."""
    sfx = "" if participant.upper().startswith("T11") else f"_{participant}"
    for cand in (f"harness_summary{sfx}_local.json", f"harness_summary{sfx}.json"):
        p = OUT / cand
        if p.exists():
            return p
    raise SystemExit(
        f"no harness summary for {participant}. Run:\n"
        f"  python3 scripts/20_evaluation_harness.py run --local\n"
        f"  python3 scripts/21_score_report.py --local")


def estimator_ceiling(n: int, reps: int = 8000, seed: int = 4) -> float:
    """Highest lag-1 value an n-point series typically reports, as rho -> 1."""
    if n < 3:
        return float("nan")
    rng = np.random.default_rng(seed)
    rho = 0.999
    eps = rng.normal(0, np.sqrt(1 - rho * rho), (reps, n))
    x = np.empty((reps, n))
    x[:, 0] = rng.normal(size=reps)
    for i in range(1, n):
        x[:, i] = rho * x[:, i - 1] + eps[:, i]
    a, b = x[:, :-1], x[:, 1:]
    am = a - a.mean(1, keepdims=True)
    bm = b - b.mean(1, keepdims=True)
    den = np.sqrt((am * am).sum(1) * (bm * bm).sum(1))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(den > 1e-12, (am * bm).sum(1) / den, np.nan)
    return float(np.nanmedian(r))


def independence(participant: str) -> dict | None:
    """Serial dependence at the non-overlapping spacing, fault-free if available."""
    sev = OUT / "autocorr_by_severity.json"
    if sev.exists():
        d = json.loads(sev.read_text())
        pres = d.get("participants", {}).get(participant)
        if pres:
            row = pres.get("by_severity", {}).get("6", {}).get("none")
            if row:
                return {"source": "fault-free episodes (scripts/70)",
                        "lag1": row["lag1_r_median"], "ci95": row["ci95"],
                        "n_windows": row["n_windows_median"],
                        "n_eff": row["n_eff"], "n_episodes": row["n_episodes"]}
    ws = OUT / "window_spacing.json"
    if ws.exists():
        d = json.loads(ws.read_text())
        row = d.get(participant, {}).get("spacings", {}).get("6")
        if row:
            return {"source": "all not-crossed episodes (scripts/66) — POOLED, "
                              "includes injected faults",
                    "lag1": row["lag1_r_median"], "ci95": None,
                    "n_windows": row["n_windows_median"],
                    "n_eff": row["n_eff"], "n_episodes": row["n_episodes"]}
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--participant", default="T11",
                    help="T11, T5, or a rig label such as RIG1")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET,
                    help="false alarms per hour the deployment can tolerate")
    ap.add_argument("--detector", default="decoder_guard")
    args = ap.parse_args()

    summary = json.loads(summary_path(args.participant).read_text())
    if args.detector not in summary:
        raise SystemExit(f"detector {args.detector} not in summary; "
                         f"have {', '.join(summary)}")
    s = summary[args.detector]
    gates = s.get("gates", {})
    passed = [g for g in GATES if gates.get(g, {}).get("pass")]

    ind = independence(args.participant)
    ceiling = estimator_ceiling(int(round(ind["n_windows"]))) if ind else float("nan")

    lead = s.get("median_lead_s")
    far = s.get("false_alarms_per_hour")
    within = far is not None and far <= args.budget
    warns_early = lead is not None and lead > 0
    verdict = bool(len(passed) == len(GATES) and within and warns_early)

    cert = {
        "participant": args.participant, "detector": args.detector,
        "false_alarm_budget_per_hour": args.budget,
        "independence": ind, "estimator_ceiling": ceiling,
        "median_lead_s": lead, "lead_ci95": s.get("lead_ci95"),
        "false_alarms_per_hour": far, "detection_rate": s.get("detection_rate"),
        "operating_point": s.get("operating_point"),
        "gates_passed": len(passed), "gates_total": len(GATES),
        "gate_detail": {g: bool(gates.get(g, {}).get("pass")) for g in GATES},
        "monitorable": verdict,
    }
    (OUT / f"monitorability_certificate_{args.participant}.json").write_text(
        json.dumps(cert, indent=2))

    # ------------------------------------------------------------------ report
    L = [f"# Monitorability certificate — {args.participant}\n",
         "**Generated by `scripts/73_monitorability_certificate.py` — "
         "do not edit by hand.**\n",
         f"Detector `{args.detector}`, judged against a budget of "
         f"**{args.budget} false alarms per hour**. The verdict is conditional "
         f"on that budget and is not meaningful without it.\n"]
    A = L.append

    A("## Verdict\n")
    A(f"## {'MONITORABLE' if verdict else 'NOT MONITORABLE'} at "
      f"{args.budget} false alarms/hour\n")

    A("## How much independent evidence is in one session?\n")
    if ind:
        A(f"- Windows per session at non-overlapping spacing: "
          f"**{ind['n_windows']:.0f}**")
        A(f"- Lag-1 autocorrelation: **{ind['lag1']:.3f}**"
          + (f" (95% CI {ind['ci95'][0]:.3f} to {ind['ci95'][1]:.3f})"
             if ind.get("ci95") else ""))
        A(f"- Effective independent samples: **{ind['n_eff']:.2f}**")
        A(f"- Episodes measured: {ind['n_episodes']}")
        A(f"- Source: {ind['source']}")
        A("")
        A(f"**The estimator's ceiling at {ind['n_windows']:.0f} windows is "
          f"{ceiling:.2f}.** Feed it a series whose true correlation is 0.999 "
          f"and that is what it reports, so any measured value near the ceiling "
          f"is a limit of the measurement rather than a property of the signal. "
          f"This is stated here because it is easy to misread and because this "
          f"project misread it once.")
    else:
        A("*Not available — run `scripts/70_autocorr_by_severity.py` and "
          "`scripts/66_window_spacing.py` first.*")

    A("")
    A("## What a warning costs\n")
    A("| Quantity | Value |")
    A("|---|---|")
    A(f"| Median lead time | **{lead if lead is not None else 'none found'}"
      f"{' s' if lead is not None else ''}** |")
    if s.get("lead_ci95"):
        A(f"| Lead time 95% CI | {s['lead_ci95'][0]} s to {s['lead_ci95'][1]} s |")
    A(f"| False alarms per hour | **{far if far is not None else 'n/a'}** |")
    A(f"| Within the {args.budget}/hour budget | "
      f"{'yes' if within else '**no**'} |")
    A(f"| Faults detected | {s.get('detection_rate', 'n/a')} |")
    A(f"| Warning threshold used | {s.get('operating_point', 'n/a')} |")
    A("")
    A("Lead time and false-alarm rate are reported together, always. Either can "
      "be made to look excellent by sacrificing the other, so a single figure "
      "is not interpretable. The threshold that produced this pair was chosen "
      "on the validation split and applied unchanged to the test split.\n")

    A("## Gates\n")
    A(f"**{len(passed)} of {len(GATES)} passed.** They are applied in order and "
      f"a detector that fails the first is not carried forward: a monitor that "
      f"alarms during healthy operation is disqualified however well it detects "
      f"faults.\n")
    A("| Gate | Result |")
    A("|---|---|")
    for g in GATES:
        ok = gates.get(g, {}).get("pass")
        A(f"| {GATE_LABEL[g]} | {'pass' if ok else '**FAIL**'} |")

    A("")
    A("## Reading this honestly\n")
    if verdict:
        A("Every gate passed, the warning arrives before the failure, and it "
          "does so inside the budget. That is the outcome this project did not "
          "obtain on cortex, so if this certificate is for a rig recording it "
          "is the more interesting of the two possible answers: it would mean "
          "the limit found on neural data is neural-specific rather than "
          "general to slowly drifting arrays.")
    else:
        reasons = []
        if len(passed) < len(GATES):
            reasons.append(f"{len(GATES) - len(passed)} of five gates failed")
        if not warns_early:
            reasons.append("the warning does not arrive before the failure")
        if not within:
            reasons.append("the false-alarm rate exceeds the budget")
        A(f"**Not monitorable at this budget because " + "; ".join(reasons) + ".**")
        A("")
        A("This is a measurement, not a defeat. It says what this array's "
          "monitoring costs, in numbers somebody else can check and compare "
          "against their own hardware. Nobody could state that before, because "
          "in observational recordings the onset of degradation is never "
          "written down, so lead time depends on the analyst's definition and "
          "the false-alarm rate is not estimable at all.")
    A("")
    A("**What this certificate cannot tell you:** whether a different detector "
      "would do better, whether a longer session would help, or whether the "
      "result transfers to a different array. Those are separate measurements, "
      "and this instrument is built to make each of them runnable.")

    (REPORTS / f"MONITORABILITY_CERTIFICATE_{args.participant}.md").write_text(
        "\n".join(L))
    print("\n".join(L[2:]).replace("**", ""))
    print(f"\nwrote {REPORTS / f'MONITORABILITY_CERTIFICATE_{args.participant}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
