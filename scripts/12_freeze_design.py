#!/usr/bin/env python3
"""
12_freeze_design.py
===================
Write the frozen study design: the deterioration boundary, the exact blocks
that fall before and after it, and every parameter that must not change once
the early-warning analysis begins.

WHY FREEZING IS A SEPARATE, DELIBERATE STEP
-------------------------------------------
The value of a preregistration comes entirely from its being fixed BEFORE the
result is known. That only means something if freezing is a deliberate act with
a recorded time and a recorded commit -- not something that happens quietly as a
side effect of running an analysis.

So this script does nothing unless `--confirm` is passed. Without it, it prints
exactly what WOULD be frozen and exits. Read the preview, satisfy yourself that
it matches `research/deterioration_definition.md`, and only then confirm.

WHAT GETS RECORDED
------------------
  * the boundary (participant, trial day) and how it was located
  * the explicit list of block identifiers before and after it, so membership is
    a stored fact rather than something recomputed later from code that might
    have changed
  * the primary variable, analysis level, and the sensitivity variants
  * the reversibility test criteria, including what counts as FAILURE
  * the statistical procedure and the power statement
  * SHA-256 hashes of the input tables, so anyone can verify the freeze was
    computed from the data as it stood
  * the git commit at the moment of freezing

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not compute any early-warning indicator, and it does not decide
anything. The decision lives in the definition document; this only records it.

HOW TO RUN
----------
    python3 scripts/12_freeze_design.py              # preview only
    python3 scripts/12_freeze_design.py --confirm    # actually freeze
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = REPO_ROOT / "data" / "processed"
FREEZE_PATH = REPO_ROOT / "research" / "FROZEN_DESIGN.json"

# ---------------------------------------------------------------------------
# THE DESIGN, exactly as set out in research/deterioration_definition.md.
# Changing anything here after freezing invalidates the preregistration.
# ---------------------------------------------------------------------------
DESIGN = {
    "primary": {
        "participant": "T11",
        "cohort": "main",
        "variable": "angle_error_deg",
        "variable_summary": "median per session",
        "locating_level": "session",
        "analysis_level": "block",
        "method": "single change point, exhaustive least-squares split",
        "min_segment": 3,
        "significance": "5000-permutation test on within-segment SSE",
        "boundary_trial_day": 758,
        "boundary_p_value": 0.0018,
        "agreeing_methods": ["least-squares", "CUSUM", "rank scan"],
        "agreeing_variables": ["angle_error_deg", "percent_correct"],
    },
    "sensitivity": [
        {"name": "variable", "change": "locate the boundary on percent_correct "
                                       "instead of angle error",
         "expected_boundary_trial_day": 758},
        {"name": "level", "change": "run the primary analysis at session level "
                                    "(n=11) as well as block level (n=21)"},
    ],
    "reversibility_tests": [
        {"name": "T5 excursion", "participant": "T5",
         "baseline_days": [2121, 2126, 2128],
         "degraded_days": [2133, 2135],
         "recovered_days": [2149],
         "success_criterion": "indicator at day 2149 returns to within the range "
                              "spanned by days 2121-2128",
         "failure_criterion": "indicator at day 2149 remains at or above its "
                              "degraded-period level, indicating the measure "
                              "tracks elapsed time or accumulated drift rather "
                              "than system dynamics"},
        {"name": "T11 internal excursion", "participant": "T11",
         "baseline_days": [658, 665, 672, 675],
         "degraded_days": [727],
         "recovered_days": [751],
         "success_criterion": "indicator at day 751 returns to within the range "
                              "spanned by days 658-675",
         "failure_criterion": "indicator at day 751 remains elevated"},
    ],
    "secondary_outcome_neural_vs_behavioural": {
        "question": "does the neural indicator warn earlier than simply "
                    "watching performance?",
        "rationale": "predicting a collapse that was already visible in "
                     "behaviour is worth little; warning before behaviour "
                     "shows anything is worth a great deal",
        "baseline_blocks": "first 8 T11 blocks (trial days 658-675), which "
                           "precede every candidate destabilization date",
        "detection_rule": "first block exceeding baseline mean + k*SD and "
                          "staying beyond it for p consecutive blocks",
        "behavioural_signal": "median angle error per block",
        "neural_signal": "the early-warning indicator per block",
        "outcome": "detection_day(behaviour) - detection_day(neural), in trial "
                   "days; positive means the neural indicator warned first",
        "parameter_grid": {"k": [1.5, 2.0, 2.5, 3.0], "baseline_n": [4, 6, 8],
                           "persist": [2, 3]},
        "why_a_grid": "the rule is known to be parameter-sensitive (the "
                      "destabilization date moves 26 days across this grid), so "
                      "the full distribution is reported rather than one "
                      "setting; both signals use identical parameters at every "
                      "setting, which keeps the COMPARISON fair even though "
                      "either date alone is not well determined",
        "interpretation_fixed_in_advance": {
            "lead_positive_majority": "neural monitoring detects earlier than "
                                      "behavioural monitoring",
            "lead_near_zero": "no advantage over watching performance",
            "lead_negative": "behaviour detects first; the neural indicator "
                             "adds nothing and will be reported as such",
        },
    },
    "rejected_alternatives": {
        "destabilization_as_the_event": {
            "considered": True,
            "rejected_because": [
                "the destabilization IS the early-warning signal; making it the "
                "event would require a new warning before it, and the period "
                "before day 689 is flat and healthy",
                "its date is not determined: across 24 parameter combinations "
                "the onset lands on day 689 (12/24), day 715 (10/24) or day 709 "
                "(2/24) — a 26-day spread",
                "per-session tests sit exactly at the smallest p-value the "
                "sample size allows (0.0444), so they carry no information "
                "about effect size",
                "it costs most of the sample: 8 blocks before day 689 or 16 "
                "before day 715, against 21 before day 758",
            ],
            "retained_as": "a comparator in the secondary outcome above",
            "evidence": "data/processed/threshold_sensitivity.csv, "
                        "data/processed/session_vs_baseline.csv",
        },
    },
    "statistics": {
        "trend_statistic": "Kendall's tau",
        "null": "AR(1)-matched surrogates, two-sided",
        "alpha": 0.05,
        "two_sided_rationale": "a compressed basin can produce falling indicators "
                               "before a transition (Titus et al. 2019), so a "
                               "one-sided test would miss real signals",
    },
    "power_statement": {
        "n_before_blocks": 21,
        "smallest_detectable_tau": 0.305,
        "power_vs_2sd_rise": 0.74,
        "commitment": "a null result will be reported as a null, not reworked "
                      "until something appears",
    },
    "excluded_from_analysis": [
        "T11(additional) cohort (personal_use, random_targets) - different tasks",
    ],
    "still_open_after_freezing": [
        "which neural observable carries the indicator (raw 20 ms features are "
        "ruled out: near-white, 0.3-0.5 bins of memory)",
        "rolling-window length, which must be swept and reported as a surface",
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                   # noqa: BLE001
        return "unavailable"


def build_membership() -> dict:
    """List the exact blocks on each side of the boundary."""
    blocks = pd.read_csv(PROCESSED / "blocks.csv")
    p = DESIGN["primary"]
    b = blocks[(blocks.participant == p["participant"])
               & (blocks.cohort == p["cohort"])].sort_values(["trial_day", "block"])
    cut = p["boundary_trial_day"]
    before = b[b.trial_day < cut]
    after = b[b.trial_day >= cut]

    def rows(df):
        return [{"block_id": r.block_id, "trial_day": int(r.trial_day),
                 "block": int(r.block), "n_trials": int(r.n_trials),
                 "n_bins": int(r.n_bins)} for r in df.itertuples()]

    return {
        "before": {"n_blocks": len(before),
                   "n_sessions": int(before.trial_day.nunique()),
                   "n_trials": int(before.n_trials.sum()),
                   "trial_days": sorted(before.trial_day.unique().tolist()),
                   "blocks": rows(before)},
        "after": {"n_blocks": len(after),
                  "n_sessions": int(after.trial_day.nunique()),
                  "n_trials": int(after.n_trials.sum()),
                  "trial_days": sorted(after.trial_day.unique().tolist()),
                  "blocks": rows(after)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--confirm", action="store_true",
                    help="actually write the freeze file (without this, preview only)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing freeze (requires --confirm)")
    args = ap.parse_args()

    for f in ("blocks.csv", "trials.csv"):
        if not (PROCESSED / f).exists():
            print(f"Missing {f}. Run scripts/04_explore_dataset.py first.",
                  file=sys.stderr)
            return 1

    membership = build_membership()
    p = DESIGN["primary"]

    print("=" * 78)
    print("STUDY DESIGN FREEZE" + ("" if args.confirm else "  —  PREVIEW ONLY"))
    print("=" * 78)
    print(f"\nBoundary: {p['participant']} trial day {p['boundary_trial_day']}")
    print(f"  located on : {p['variable']} ({p['variable_summary']}), "
          f"{p['locating_level']} level")
    print(f"  method     : {p['method']}, min segment {p['min_segment']}")
    print(f"  p-value    : {p['boundary_p_value']}  "
          f"({', '.join(p['agreeing_methods'])} all agree, "
          f"on {' and '.join(p['agreeing_variables'])})")
    print(f"  analysed at: {p['analysis_level']} level")

    for side in ("before", "after"):
        m = membership[side]
        print(f"\n{side.upper()}  {m['n_blocks']} blocks · {m['n_sessions']} sessions "
              f"· {m['n_trials']:,} trials")
        print(f"  trial days: {m['trial_days']}")
        ids = [f"d{b['trial_day']}b{b['block']}" for b in m["blocks"]]
        for i in range(0, len(ids), 8):
            print("    " + "  ".join(ids[i:i + 8]))

    print("\nReversibility tests:")
    for t in DESIGN["reversibility_tests"]:
        print(f"  {t['name']} ({t['participant']}): "
              f"{t['baseline_days']} -> {t['degraded_days']} -> {t['recovered_days']}")
        print(f"     succeeds if : {t['success_criterion']}")
        print(f"     FAILS if    : {t['failure_criterion']}")

    ps = DESIGN["power_statement"]
    print(f"\nPower: n={ps['n_before_blocks']} blocks before the boundary; "
          f"detects |tau| >= {ps['smallest_detectable_tau']}; "
          f"power {ps['power_vs_2sd_rise']} vs a 2 sd rise.")
    print(f"  Commitment: {ps['commitment']}")

    sec = DESIGN["secondary_outcome_neural_vs_behavioural"]
    print("\nSecondary outcome (prespecified): neural vs behavioural lead time")
    print(f"  {sec['question']}")
    print(f"  outcome: {sec['outcome']}")
    print(f"  reported across {len(sec['parameter_grid']['k']) * len(sec['parameter_grid']['baseline_n']) * len(sec['parameter_grid']['persist'])} parameter settings, same for both signals")
    for k, v in sec["interpretation_fixed_in_advance"].items():
        print(f"    {k:<26} -> {v}")

    rej = DESIGN["rejected_alternatives"]["destabilization_as_the_event"]
    print("\nRejected alternative, recorded: destabilization as the event")
    for r in rej["rejected_because"]:
        print(f"  - {r}")

    print("\nStill open after freezing (independent of the event definition):")
    for s in DESIGN["still_open_after_freezing"]:
        print(f"  - {s}")

    if not args.confirm:
        print("\n" + "=" * 78)
        print("NOTHING WAS WRITTEN. This was a preview.")
        print("Check it against research/deterioration_definition.md, then run:")
        print("    python3 scripts/12_freeze_design.py --confirm")
        print("=" * 78)
        return 0

    if FREEZE_PATH.exists() and not args.force:
        print(f"\nERROR: {FREEZE_PATH.name} already exists.", file=sys.stderr)
        print("A design has already been frozen. Re-freezing after seeing any "
              "result destroys\nthe value of the preregistration. If this is a "
              "genuine correction made before any\nindicator was computed, pass "
              "--force and explain why in the commit message.",
              file=sys.stderr)
        return 1

    record = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_by_script": "scripts/12_freeze_design.py",
        "git_commit_at_freeze": git("rev-parse", "HEAD"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "definition_document": "research/deterioration_definition.md",
        "evidence": "data/processed/deterioration_candidates.csv",
        "input_hashes": {f: sha256(PROCESSED / f) for f in ("blocks.csv", "trials.csv")},
        "design": DESIGN,
        "membership": membership,
        "declaration": (
            "This design was fixed before any early-warning indicator was "
            "computed on the real data. The deterioration boundary was located "
            "from behavioural performance only. No EWS result was known at the "
            "time of freezing."
        ),
    }
    FREEZE_PATH.write_text(json.dumps(record, indent=2))
    print("\n" + "=" * 78)
    print(f"FROZEN. Written to {FREEZE_PATH.relative_to(REPO_ROOT)}")
    print(f"  commit at freeze: {record['git_commit_at_freeze'][:12]}")
    print("\nCommit this file now, before running any early-warning analysis.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
