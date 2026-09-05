#!/usr/bin/env python3
"""
One register of every claim this project makes, and what state it is in.

Nineteen reports and a long log, with claims in genuinely different conditions --
some survived three attacks, some were retracted, one is unanswerable with this
data. Scattered across documents those distinctions blur, and the blurring always
runs one way: a withdrawn mechanism gets quoted as though it still stood.

So the register is the single source of truth, and it is CHECKED rather than
written:

  1. every claim marked ESTABLISHED cites at least one verifier claim
  2. every verifier claim it cites actually exists in 31_verify_claims.py
  3. every report it cites exists on disk
  4. verifier claims cited by NOTHING are reported as a coverage gap

Check 4 is the interesting one: it asks whether the evidence base and the story
have drifted apart.

Usage: python3 scripts/56_claims_register.py
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "reports"

ESTABLISHED = "ESTABLISHED"
WITHDRAWN = "WITHDRAWN"
UNANSWERABLE = "UNANSWERABLE"
EXPLORATORY = "EXPLORATORY"
LIMITATION = "LIMITATION"

ORDER = [ESTABLISHED, LIMITATION, WITHDRAWN, UNANSWERABLE, EXPLORATORY]

# id, status, statement, report, verifier labels, note
CLAIMS = [
    # ---------------------------------------------------------- established
    ("C01", ESTABLISHED,
     "The reference decoder works: 54.6° held-out error against a measured "
     "90.7° chance level on T11, 52.8° on T5.",
     "PHASE3_REPORT.md",
     ["Reference decoder, T11 held-out healthy error (deg)",
      "Reference decoder, T11 measured chance (deg)",
      "Reference decoder, T5 held-out healthy error (deg)"],
     "Chance measured by shuffled pairing, not assumed to be 90°."),

    ("C02", ESTABLISHED,
     "The monitor detects faults that counting spikes cannot see, on both "
     "participants: AUC 0.69–0.71 with a local baseline where a calibrate-once "
     "baseline sits at chance.",
     "EWS_RESULTS.md",
     ["Early-warning AUC, T11 recent-normal", "Early-warning AUC, T5 recent-normal",
      "Early-warning AUC, T11 calibrate-once (should be chance)"],
     "Replicated. The calibrate-once arm is the control and lands at 0.491. "
     "NOTE: this number is WINDOW-level -- the verifier pools every window. The "
     "episode-level equivalent is 0.672 (T11) and 0.742 (T5). Claim C04 says "
     "windows within a session are not independent, so the point estimate stands "
     "but no interval or p-value may be built on it. See PER_MODE_DETECTION.md."),

    ("C15", ESTABLISHED,
     "The detection headline is not carried by one easy fault mode: removing "
     "GEOMETRY_ROTATION moves it by 0.037 on T11 and 0.002 on T5.",
     "PER_MODE_DETECTION.md",
     ["headline without GEOMETRY_ROTATION, T11",
      "headline without GEOMETRY_ROTATION, T5",
      "episode-level headline, T11 (register C02 is window-level)",
      "window-level headline reproduces the register, T11"],
     "Predicted the opposite -- that rotation carried it and removal would drop "
     "the headline to 0.60-0.65. Wrong on both counts."),

    ("C03", ESTABLISHED,
     "No configuration is deployable at the specified false-alarm budget: "
     "0 of 48 pass all five gates.",
     "BENCHMARK_SUMMARY.md",
     ["Configurations passing all five gates"],
     "The binding gate is silence, not detection."),

    ("C04", ESTABLISHED,
     "A session contains roughly one independent measurement: lag-1 "
     "autocorrelation of the risk signal is 0.995 (T11) and 0.980 (T5).",
     "AGGREGATION_LIMIT.md",
     ["Lag-1 autocorrelation of risk, T11 healthy",
      "Lag-1 autocorrelation of risk, T5 healthy"],
     "This single fact explains most of the negative results."),

    ("C05", ESTABLISHED,
     "A task change is separated from a real fault by 15× on T11.",
     "EWS_RESULTS.md",
     ["Task change vs real fault separation, day 658"],
     "The comparator gate does its job."),

    ("C06", ESTABLISHED,
     "Commissioning is cheap: ~20 healthy windows (about two minutes) reaches "
     "the accuracy the entire healthy record reaches, on both participants.",
     "CALIBRATION_CURVE.md",
     ["calibration T11, 20 windows (scattered)", "calibration T11, entire healthy record",
      "calibration T5, 20 windows (scattered)", "calibration T5, entire healthy record",
      "calibration T5, 40 windows CONTIGUOUS", "calibration T11, 20 windows CONTIGUOUS"],
     "Contiguous draw confirms the count translates into real minutes."),

    ("C07", ESTABLISHED,
     "A monitor's fit does not measurably go stale over 142 days.",
     "STALENESS_AND_DAY_VARIANCE.md",
     ["staleness permutation p, T11 (naive said 0.003)", "staleness permutation p, T5"],
     "The naive test said p = 0.003; permuting day labels gives 0.128."),

    ("C08", ESTABLISHED,
     "Monitor accuracy varies enormously by session — 0.32 to 0.97 on T11 — and "
     "only about a quarter of that is sampling noise.",
     "STALENESS_AND_DAY_VARIANCE.md",
     ["day-to-day AUC spread, T11 (min)", "day-to-day AUC spread, T11 (max)",
      "I-squared across days, T11", "share of day variance that is sampling, T11"],
     "Invisible to every pooled analysis, because pooling averages it away."),

    ("C09", ESTABLISHED,
     "Session accuracy is strongly associated with that session's absolute "
     "decoder error (ρ = −0.720, p = 0.0055), preregistered with the direction "
     "committed in advance.",
     "DAY_PREDICTORS.md",
     ["P5 decoder error vs monitor AUC, T11 (rho)",
      "P5 p-value, T11 (Bonferroni threshold 0.01)",
      "P5 partial rho controlling window length, T11",
      "P5 controlling for achieved damage, T11 (strengthens)"],
     "Survived three challenges: early-warning window length, crossed/split "
     "shift, and the achievable-damage ceiling."),

    ("C10", ESTABLISHED,
     "The bad-session pattern is shared by distribution-based detectors and "
     "absent from scalar ones — it belongs to a class of monitor, not to this "
     "implementation.",
     "DAY_EFFECT_ACROSS_DETECTORS.md",
     ["guard vs distribution_shift per-day AUC, T11",
      "guard vs mean_activity per-day AUC, T11",
      "distribution_shift vs decoder error, T11"],
     "My prediction was that all four detectors would share it. They do not."),

    ("C11", ESTABLISHED,
     "No label-free signal predicts whether the monitor will work that day, so "
     "abstention is an untested proposal rather than a capability.",
     "ABSTENTION.md",
     ["L4 vs monitor AUC, T11 (stage 2 null)"],
     "Four candidates, two stages, nothing passes stage 2."),

    ("C12", ESTABLISHED,
     "Mean output speed tracks decoder error on both participants and clears "
     "the threshold on both — with OPPOSITE signs (+0.681 vs −0.943).",
     "ABSTENTION.md",
     ["L4 vs decoder error, T11 (sign reverses)",
      "L4 vs decoder error, T5 (opposite sign)"],
     "Strongest cross-participant agreement in the project, and a contradiction: "
     "any rule tuned on one array runs backwards on the other."),

    ("C13", ESTABLISHED,
     "Pooling episodes across sessions costs essentially nothing (0.003 AUC), "
     "refuting the hypothesis that pooling was diluting the signal.",
     "STALENESS_AND_DAY_VARIANCE.md",
     ["cost of pooling episodes across days, T11"],
     "Tested because it was attractive; reported because it was tested."),

    # ------------------------------------------------------------ limitations
    ("L01", LIMITATION,
     "Severity is only valid in aggregate: the three fault levels are correctly "
     "ordered in 57% of session × mode cells on T11 and 67% on T5, degrading "
     "with the session's baseline error on both arrays.",
     "SEVERITY_LADDER_VALIDITY.md",
     ["severity ladder monotone fraction, T11", "severity ladder monotone fraction, T5",
      "baseline vs ladder validity, T11 (rho)", "baseline vs ladder validity, T5 (rho)"],
     "The only relationship in this project that replicates significantly with "
     "the same sign on both participants."),

    ("L02", LIMITATION,
     "Every AUC reported here understates performance by about 0.7–1.2%, "
     "because six 'pre-onset' windows per episode contain faulted data.",
     "WINDOW_OVERLAP.md",
     ["contaminated windows per episode, T11 (1500/250 = 6)",
      "AUC understated by the overlap, T11", "AUC understated by the overlap, T5",
      "sign test across both arrays, p (one-sided)"],
     "The bias is conservative, as was argued when found — now a number rather "
     "than an argument. No conclusion changes."),

    ("L03", LIMITATION,
     "On sessions near chance an injected fault does almost no measurable "
     "damage, so their ground truth is nearly degenerate: 6 of 13 T11 sessions "
     "cannot be scored on unambiguous faults at all.",
     "UNAMBIGUOUS_EPISODES.md",
     ["T11 days scoreable on unambiguous faults (of 13)",
      "bad days retain fewer unambiguous faults, T11 (rho)",
      "ceiling: baseline vs achieved fault damage, T11"],
     "Day 783: 1 of 20 faults measurable. Day 672: none."),

    ("L04", LIMITATION,
     "The profile covariance is singular below n = K + 1 windows, so the n = 10 "
     "calibration point is not a measurement.",
     "CALIBRATION_CURVE.md",
     ["n=10 profile covariance is singular (min eigenvalue)",
      "n=20 profile covariance is well posed (min eigenvalue)"],
     "It is also the highest AUC on T11, and would have supported a false "
     "headline that more calibration data makes the monitor worse."),

    ("L05", LIMITATION,
     "Inverse-variance weighting is biased for a bounded statistic: it inflated "
     "a pooled AUC from 0.675 to 0.836 by over-weighting the most extreme days.",
     "STALENESS_AND_DAY_VARIANCE.md",
     ["inverse-variance weighting bias, T11 (rho)"],
     "The field is named ..._BIASED_DO_NOT_QUOTE in the output."),

    ("L06", LIMITATION,
     "The two participants disagree on why sessions differ: on T5 the spread "
     "tracks the fault mix each session drew, on T11 it does not.",
     "STALENESS_AND_DAY_VARIANCE.md",
     ["fault-mix confound, T5 (rho) — why T5 cannot corroborate",
      "fault-mix confound, T11 (rho) — day effect stands"],
     "So T5 cannot corroborate the T11 day effect."),

    ("L07", LIMITATION,
     "A candidate feature can clear the bar on one participant and fail badly "
     "on the other (F3 spectral: 0.750 vs 0.556).",
     "FEATURE_STUDY_RESULT.md",
     ["F3 spectral, T11 (cleared the bar here)", "F3 spectral, T5 (failed badly here)",
      "F0 control, T11 (current features, generic scorer)"],
     "The both-participants rule in action; this is why it exists."),

    ("C14", ESTABLISHED,
     "Attribution is better than chance but not usable: 56% on T11 (chance 25%) "
     "and 52% on T5 (chance 33%), with GAIN_DRIFT named correctly 99% of the time.",
     "ATTRIBUTION_ACCURACY.md",
     ["attribution accuracy overall, T11 (chance 0.25)",
      "attribution accuracy overall, T5 (chance 0.33)",
      "GAIN_DRIFT named correctly, T11"],
     "Implemented and scored since the guard was written, printed to stdout and "
     "captured nowhere until now."),

    ("L09", LIMITATION,
     "Every p-value in ACHIEVABILITY.md was computed by pooling windows, "
     "inflating the apparent sample size 26.6×. Four were published as p = 0; "
     "three results significant as published are not significant at the episode "
     "level, including one published at p = 3.4e-15 that is actually p = 0.144.",
     "UNIT_OF_ANALYSIS.md",
     ["sample-size inflation from pooling windows",
      "published statistics that were p = 0 exactly",
      "results significant as published, null when corrected",
      "largest AUC shift from the correction"],
     "The AUC point estimates and verdicts stand -- median shift 0.020. The p "
     "column does not. Corrected inline in ACHIEVABILITY.md rather than deleted."),

    ("L10", LIMITATION,
     "Three statistical error classes were found in this project, all by "
     "accident, all by checks written after the work they caught. They are now "
     "encoded as a linter over all 61 scripts, which passes with 0 unreviewed "
     "sites and 8 deliberate ones documented.",
     "STATISTICAL_HYGIENE.md",
     ["sample-size inflation from pooling windows",
      "results significant as published, null when corrected"],
     "The linter missed its own motivating example on the first run, because "
     "the test was wrapped in a local helper. Fixed before its output was "
     "trusted -- the fourth time a checking tool here was wrong before it was "
     "useful."),

    ("C16", ESTABLISHED,
     "A one-class detector built on the shape information — the thing the "
     "evidence pointed to — is WORSE on both axes: AUC 0.617/0.680 against "
     "0.672/0.742, and 98.5% of healthy episodes trending against a 31% best. "
     "The shape that distinguishes faults also drifts through healthy sessions.",
     "INVARIANT_DETECTOR.md",
     ["invariant one-class detector AUC, T11 (worse)",
      "invariant one-class detector AUC, T5 (worse)",
      "healthy episodes trending, invariant detector T11",
      "same trend unclipped, T11 (not an artefact)"],
     "Preregistered with numeric criteria and a prediction that detection would "
     "improve; it fell on both participants. One candidate by design, no tuned "
     "variant. The trend survives unclipping, so it is not the scoring "
     "convention. Turns an inference about detector classes into a measurement."),

    ("C17", ESTABLISHED,
     "The invariant-feature recommendation fails label-free in BOTH halves: "
     "detection (0.617/0.680 vs 0.672/0.742) and attribution (51.1%/39.7% vs "
     "56.3%/52.5%, rotation 2.1%/6.1% against 25% chance). A supervised "
     "demonstration that information exists has twice failed to translate into "
     "a label-free rule that uses it.",
     "INVARIANT_ATTRIBUTION.md",
     ["label-free invariant attribution, T11 (worse)",
      "label-free invariant attribution, T5 (worse)",
      "rotation under the invariant rule, T11 (below chance)"],
     "Both preregistered with criteria and predictions fixed first; both "
     "predictions wrong. The attribution failure is diagnostic -- `sd` is a "
     "generic spread measure every fault elevates, so it swamps the specific "
     "features. That is the `profile` residual problem again, and my "
     "preregistration explicitly declined a specificity ordering on reasoning "
     "that was wrong."),

    # ------------------------------------------------------------- withdrawn
    ("W01", WITHDRAWN,
     "WITHDRAWN: that the monitor fails because the decoder has lost its "
     "signal. Margin over a session's own chance level does NOT predict monitor "
     "accuracy (+0.264, p = 0.38).",
     "WHAT_DECODER_ERROR_MEANS.md",
     ["margin over own chance vs monitor AUC, T11",
      "day 800 barely beats its own chance, P(better)"],
     "Days 800 and 783 beat their own chance by near-identical margins with "
     "accuracies of 0.97 and 0.32."),

    ("W02", WITHDRAWN,
     "WITHDRAWN: any claim about WHICH property of a session causes the "
     "accuracy swing. Trace noise predicts identically (−0.720) and correlates "
     "with decoder error at 0.813; the partials are identical in both "
     "directions (−0.333).",
     "CEILING_CHALLENGE.md",
     ["trace noise vs monitor AUC, T11 (ties P5 exactly)",
      "P5 controlling for trace noise, T11 (collapses)"],
     "Identical partials both ways is collinearity, not mediation."),

    ("L08", LIMITATION,
     "GEOMETRY_ROTATION is attributed correctly 0% of the time, on both "
     "participants — and the cause is the components, not the ranking rule.",
     "ATTRIBUTION_ACCURACY.md",
     ["GEOMETRY_ROTATION named correctly, T11", "GEOMETRY_ROTATION named correctly, T5",
      "during rotation, dispersion z (vs profile 1.92)",
      "during rotation, profile IS lit (fraction)"],
     "`profile` is lit in 80% of rotation episodes but `dispersion` sits at "
     "z = 16.5 against its 1.9; largest-wins would still pick dispersion 98% of "
     "the time."),

    ("W04", WITHDRAWN,
     "WITHDRAWN: the preregistered mapping GEOMETRY_ROTATION -> `profile`. "
     "Rotation is injected with norm-preserving Givens rotations, and "
     "`dispersion` is defined as channels spreading apart with the total "
     "conserved — the same signature by definition.",
     "ATTRIBUTION_ACCURACY.md",
     ["GEOMETRY_ROTATION named correctly, T11"],
     "The mapping was wrong from the start. Re-ordering or re-weighting the rule "
     "cannot fix it; the components would have to be redefined to be separable."),

    ("W03", WITHDRAWN,
     "WITHDRAWN: that weaker faults on bad sessions explain the accuracy swing. "
     "Achieved damage barely relates to monitor accuracy (+0.181, p = 0.55).",
     "CEILING_CHALLENGE.md",
     ["ceiling: damage vs monitor AUC, T11 (predicted +, got ~0)"],
     "I predicted this confound would hold. It did not."),

    # ---------------------------------------------------------- unanswerable
    ("U01", UNANSWERABLE,
     "Whether the session effect is failed detection or degraded labels cannot "
     "be decided with this corpus: filtering to unambiguous faults leaves 7 "
     "sessions and ρ = −0.536, p = 0.215.",
     "UNAMBIGUOUS_EPISODES.md",
     ["P5 on unambiguous episodes only, T11 (underpowered)",
      "spurious crossings vs monitor AUC, T11"],
     "Not answered no — unanswerable. At n = 7, |ρ| must reach ~0.79 to clear "
     "p < 0.05, so the filtering removed the power along with the ambiguity."),

    # ----------------------------------------------------------- exploratory
    ("E01", EXPLORATORY,
     "Sessions differ by a factor of fifty in how directionally varied the task "
     "was (0.013 to 0.679), which is why each session's own chance level ranges "
     "47.7°–102.7° instead of sitting near 90°.",
     "WHAT_DECODER_ERROR_MEANS.md",
     ["directional concentration vs monitor AUC, T11"],
     "Not preregistered. Found while checking a recommendation I had already "
     "published, and it affects every absolute error number in the project."),

    ("E02", EXPLORATORY,
     "Preregistered predictor P4 (within-day drift) came out with the wrong "
     "sign (+0.582 against a predicted negative) and P1 was null.",
     "DAY_PREDICTORS.md",
     ["P4 drift came out with the WRONG sign, T11", "P1 healthy dispersion, T11 (null)"],
     "Reported because the signs were committed in advance; nothing is claimed "
     "from either."),

    ("E04", EXPLORATORY,
     "[NARROWED — see C17: this is evidence the information exists, NOT a "
     "design for a monitor; both label-free halves fail] "
     "The information to identify GEOMETRY_ROTATION is the strongest signal in "
     "the feature set (pairwise AUC 0.86–0.98 on T11, 1.00 on T5) — so the "
     "attribution failure is a component-design problem, not missing information.",
     "MODE_SEPARABILITY.md",
     ["gain-drift vs rotation separability, T11",
      "gain-drift vs rotation separability, T5"],
     "A supervised probe using labels a monitor never has: an upper bound, not "
     "monitor performance. The mode the guard always gets wrong is the easiest "
     "one to identify."),

    ("W05", WITHDRAWN,
     "WITHDRAWN: that dropout, gain drift and rate loss face an information "
     "ceiling. That was the LINEAR MODEL's limit, not the features'. With "
     "permutation-invariant summaries the confusable trio rises from 0.650 to "
     "0.987 on T11 and 0.623 to 0.998 on T5.",
     "PERMUTATION_INVARIANT.md",
     ["confusable trio, invariant features, T11",
      "confusable trio, per-channel features, T11",
      "control: 12 RANDOM raw channels, T11"],
     "A linear discriminant seeks one fixed direction, but the channels each "
     "fault touches are random per episode. A 12-random-channel control reaches "
     "only 0.702, so the gain is representation, not dimension count."),

    ("E06", EXPLORATORY,
     "All four fault modes are near-perfectly separable from one another, so "
     "the guard's attribution failure is entirely a design problem and not "
     "partly an information ceiling.",
     "PERMUTATION_INVARIANT.md",
     ["confusable trio, invariant features, T11",
      "rotation pairs barely moved, T11 (as predicted)"],
     "Supervised upper bound: it says the information exists, not that a "
     "one-class monitor could reach it."),

    ("E03", EXPLORATORY,
     "The decoder-guard operating point on T11 is 50.46, giving 3.41 false "
     "alarms per hour against a 0.1/h budget.",
     "BENCHMARK_T11_local.md",
     ["decoder-guard operating point, T11 recent-normal",
      "decoder-guard false alarms per hour, T11"],
     "Quoted in the demo; the budget is missed by 34×."),
]


def verifier_labels() -> set[str]:
    tree = ast.parse((REPO / "scripts" / "31_verify_claims.py").read_text())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and getattr(d.func, "id", "") == "claim":
                    out.add(d.args[0].value)
    return out


def main() -> int:
    have = verifier_labels()
    problems: list[str] = []
    cited: set[str] = set()

    for cid, status, _stmt, report, labels, _note in CLAIMS:
        for lb in labels:
            cited.add(lb)
            if lb not in have:
                problems.append(f"{cid} cites verifier claim '{lb}' which does not exist")
        if not (REPORTS / report).exists():
            problems.append(f"{cid} cites report '{report}' which does not exist")
        if status == ESTABLISHED and not labels:
            problems.append(f"{cid} is marked ESTABLISHED but cites no verifier claim")

    uncited = sorted(have - cited)
    print(f"register: {len(CLAIMS)} claims, verifier: {len(have)} checks\n")
    for st in ORDER:
        n = sum(1 for c in CLAIMS if c[1] == st)
        print(f"  {st:<14} {n}")

    print(f"\ncoverage: {len(cited)}/{len(have)} verifier claims cited by the register")
    if uncited:
        print("  not cited by any register entry:")
        for lb in uncited:
            print(f"    - {lb}")

    # ---- emit the register ------------------------------------------------
    lines = ["# Claims register",
             "",
             "**Generated by `scripts/56_claims_register.py` — do not edit by hand.**",
             "",
             "Every claim this project makes, in one place, with its current status.",
             "Scattered across nineteen reports these distinctions blur, and the",
             "blurring always runs one way: a withdrawn mechanism gets quoted as though",
             "it still stood.",
             "",
             "The register is checked, not written. Every claim marked ESTABLISHED must",
             "cite a check in `31_verify_claims.py` that exists, every cited report must",
             "exist, and any verifier check cited by nothing is reported as a coverage",
             "gap — which asks whether the evidence base and the story have drifted",
             "apart.",
             "",
             "| status | meaning |",
             "|---|---|",
             "| **ESTABLISHED** | survived its challenges; backed by a recomputed check |",
             "| **LIMITATION** | a measured property of the corpus or method, not a result |",
             "| **WITHDRAWN** | asserted earlier, retracted on evidence; do not quote |",
             "| **UNANSWERABLE** | this data cannot decide it — not the same as 'no' |",
             "| **EXPLORATORY** | not preregistered; hypothesis-generating only |",
             ""]
    for st in ORDER:
        rows = [c for c in CLAIMS if c[1] == st]
        if not rows:
            continue
        lines += [f"## {st} ({len(rows)})", ""]
        for cid, _s, stmt, report, labels, note in rows:
            lines += [f"### {cid}", "",
                      stmt, "",
                      f"- **Report:** [`{report}`](../reports/{report})",
                      f"- **Checks:** {len(labels)} — "
                      + "; ".join(f"`{l}`" for l in labels),
                      f"- **Note:** {note}", ""]
    lines += ["---", "",
              f"**Coverage:** {len(cited)} of {len(have)} verifier checks are cited "
              f"by a register entry."]
    if uncited:
        lines += ["", "Not cited by any entry:", ""]
        lines += [f"- `{l}`" for l in uncited]
    (REPORTS / "CLAIMS_REGISTER.md").write_text("\n".join(lines) + "\n")

    print(f"\nwrote {REPORTS / 'CLAIMS_REGISTER.md'}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS — every cited check and report exists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
