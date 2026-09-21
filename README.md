# Decoder-Guard — monitoring brain-computer interface reliability

A high-school research project (ISEF) on whether the failure of an intracortical
brain-computer interface can be **detected before it costs the user
performance**, and on building an honest test for any system that claims to do
so.

> **No human participants.** Every number here comes from **public,
> de-identified datasets** collected years ago by other researchers under their
> own ethics approval. Nobody is recruited, nobody wears a device, no consent
> forms are collected. Where the documents say "participant" they mean *whose
> published recording a data file contains* — the source researchers' convention,
> labelling their subjects T5, T11, T15.

---

## The problem

People with paralysis can control a computer cursor through an implanted
electrode array and software called a **decoder**. Over months the recording
degrades — electrodes drift, neurons drop out — and the decoder keeps confidently
producing output from a signal that no longer matches what it was trained on.
Eventually it must be retrained, which is slow and disruptive.

The field has spent a decade learning to *correct* that drift and almost no
effort on *noticing it early enough to act*. There is not even a standard way to
test whether such a warning system works.

## Where this is, as of 21 September 2026

**The computational half is complete** and its result is below. **The physical
half is specified, coded and preregistered, and waiting on parts.** It exists
because two numbers that decide whether this class of monitor can be deployed —
how early it warns, and how often it warns when nothing is wrong — cannot be
measured on archived human recordings by anyone. Start at
[`physical/README.md`](physical/README.md).

## The result, in one line

**On this data, at the operating point the design specified, no configuration
works — and the reason is now measured rather than guessed.**

| Finding | |
|---|---|
| The monitor detects faults **counting spikes cannot see** | AUC 0.71–0.79 where the trivial baseline sits at 0.40–0.52. Replicated on two participants. Not carried by one easy fault mode: removing the most distinctive one moves it by 0.037 and 0.002. |
| It does **not** mistake a task change for a fault | 15× and 70× separation |
| It **cannot** be deployed at the specified false-alarm rate | 0 of 48 configurations pass the gates |
| Why: **one measurement per session** | Lag-1 autocorrelation 0.995. Effective independent samples per session: 0.1 |
| The target a future attempt must beat | Session-level AUC ≈ **0.99**; achieved **0.67–0.74** |
| Commissioning is **cheap** | ~20 healthy windows — about **two minutes** of recording. More data adds nothing. |
| A fit does **not** go stale | −0.012 AUC per 100 days over a 142-day span; permutation p = 0.128 |
| But **which day** you use it on decides almost everything | Same-day AUC ranges **0.32 to 0.97** across 13 sessions; I² = 0.86 |
| It tracks the day's **absolute** decoder error | ρ = −0.720, p = 0.0055, preregistered; survives three challenges |
| But **not** the decoder having lost signal | Margin over that day's own chance: ρ = +0.264, p = 0.38. Five entangled day-variables, 13 days — which one matters is not identifiable here. |
| It **cannot tell** when it is having a bad day | No label-free signal predicts its own reliability |
| The failure belongs to a **class**, not this build | Shared with `distribution_shift` (ρ = 0.835), absent from `mean_activity` (ρ = −0.06) |

## Start here

| Read | For |
|---|---|
| [`reports/CLAIMS_REGISTER.md`](reports/CLAIMS_REGISTER.md) | **Start here** — every claim, its status, and what checks it |
| [`reports/PHASE3_REPORT.md`](reports/PHASE3_REPORT.md) | **The whole project**, from the ground-truth problem to the bound |
| [`reports/monitor_demo.html`](reports/monitor_demo.html) | The monitor **running** — one fault caught, one missed, one false alarm |
| [`reports/project_guide.html`](reports/project_guide.html) | Plain-language explanation, no background assumed |
| [`reports/bad_day_problem.html`](reports/bad_day_problem.html) | **The bad-day problem** — the five September studies and what they changed ([published](https://claude.ai/code/artifact/3626899e-5714-4a29-861a-5fab36eacf82)) |
| [`research/research_log.md`](research/research_log.md) | Dated record of every step, every mistake, every correction |
| [`reports/PHASE1_2_REPORT.md`](reports/PHASE1_2_REPORT.md) | The earlier phase and its negative result |
| [`reports/CALIBRATION_CURVE.md`](reports/CALIBRATION_CURVE.md) | How much healthy data commissioning costs |
| [`reports/STALENESS_AND_DAY_VARIANCE.md`](reports/STALENESS_AND_DAY_VARIANCE.md) | Ageing, day-to-day swing, and three near-misses |
| [`reports/DAY_PREDICTORS.md`](reports/DAY_PREDICTORS.md) | The preregistered result, and why it is bad news |
| [`reports/ABSTENTION.md`](reports/ABSTENTION.md) | Whether the monitor can know when not to be trusted (it cannot) |
| [`reports/DAY_EFFECT_ACROSS_DETECTORS.md`](reports/DAY_EFFECT_ACROSS_DETECTORS.md) | Whose fault the day effect is — a failed prediction that paid off |
| [`reports/CEILING_CHALLENGE.md`](reports/CEILING_CHALLENGE.md) | Trying to break the headline — what survived, and the mechanism I retracted |
| [`reports/UNAMBIGUOUS_EPISODES.md`](reports/UNAMBIGUOUS_EPISODES.md) | **The corpus is blind where it matters** — and the design fix that follows |
| [`reports/WHAT_DECODER_ERROR_MEANS.md`](reports/WHAT_DECODER_ERROR_MEANS.md) | What "the decoder is failing" actually meant — and where this line of work stops |
| [`reports/SEVERITY_LADDER_VALIDITY.md`](reports/SEVERITY_LADDER_VALIDITY.md) | Whether "severity" means the same thing on every session (it does not) |
| [`reports/WINDOW_OVERLAP.md`](reports/WINDOW_OVERLAP.md) | An open limitation, closed with a number |
| [`reports/REPRODUCIBILITY_AUDIT.md`](reports/REPRODUCIBILITY_AUDIT.md) | Whether any of this actually reproduces — and the claim that did not |
| [`reports/ATTRIBUTION_ACCURACY.md`](reports/ATTRIBUTION_ACCURACY.md) | When it warns, does it name the right cause? One mode: never |
| [`reports/MODE_SEPARABILITY.md`](reports/MODE_SEPARABILITY.md) | The mode it never identifies is the easiest one to identify |
| [`reports/PER_MODE_DETECTION.md`](reports/PER_MODE_DETECTION.md) | Is the headline carried by one easy fault mode? No — and the AUC level it is quoted at |
| [`reports/UNIT_OF_ANALYSIS.md`](reports/UNIT_OF_ANALYSIS.md) | **Every published p-value recomputed** — three were significant and are not |
| [`reports/STATISTICAL_HYGIENE.md`](reports/STATISTICAL_HYGIENE.md) | A linter for the three statistical mistakes this project actually made |
| [`reports/PERMUTATION_INVARIANT.md`](reports/PERMUTATION_INVARIANT.md) | It was the model's fault, not the features' — a published conclusion withdrawn |
| [`reports/INVARIANT_DETECTOR.md`](reports/INVARIANT_DETECTOR.md) | Building the sharper detector the evidence pointed to — it was worse on both axes |
| [`reports/INVARIANT_ATTRIBUTION.md`](reports/INVARIANT_ATTRIBUTION.md) | The other half fails too — and what that says about supervised probes |
| [`research/ORIGINAL_DATA_COLLECTION_DESIGN.md`](research/ORIGINAL_DATA_COLLECTION_DESIGN.md) | Why archived data cannot close certain gaps, and the options rejected. **Its recommendation is superseded** by the physical phase, which asks a different question |
| [`physical/README.md`](physical/README.md) | **The physical-validation phase** — an apparatus whose failures are scheduled in advance, so lead time and false-alarm rate have a fixed value for the first time |

## Checking the work

Seven gates plus a test suite. Run all of them before committing anything, never
after, or you end up with regenerated files that disagree with the code.

```
python3 -m unittest discover -s tests   # 45 unit tests
python3 tools/mutation_check.py         # do those tests catch anything?
python3 scripts/31_verify_claims.py     # every headline number, recomputed
python3 scripts/55_reproducibility_audit.py
python3 scripts/56_claims_register.py
python3 scripts/61_statistical_hygiene.py
python3 scripts/65_log_coverage.py
python3 scripts/69_command_check.py     # would a reader's first command work?
python3 scripts/77_cross_reference.py   # do the documents agree with the code?
python3 physical/code/monitor.py --selftest   # the physical phase's pipeline
```

`69_command_check.py` was missing from this list until 20 September 2026, which
is exactly the way a gate stops being run. `77_cross_reference.py` was added on
21 September after two documents were found disagreeing about the same number
for two weeks — every other gate checks a figure against the data file it came
from, and nothing was checking that two documents agree.

`tools/mutation_check.py` is the unusual one. A test suite that passes on its
first run has demonstrated nothing, so it reintroduces eleven bugs this project
actually had, one at a time, and confirms the matching test fails against each.
Every test in `tests/` is derived from a real mistake rather than written for
coverage.

## How the argument runs

1. **The original idea was tested and failed.** Early-warning-signal theory,
   under a design frozen in advance. The indicator rose *faster* during healthy
   performance than overall. Reported as negative.
2. **Observational data cannot answer the question.** Nobody recorded when
   deterioration began, so lead time is an artefact of the analyst's own
   definition and the false-alarm rate is not estimable at all.
3. **So the ground truth was built.** 1,850 fault episodes with onsets drawn and
   locked to disk under a checksum *before* any detector existed.
4. **A grading system was built before the monitor**, so the metric could not be
   chosen to flatter it.
5. **The monitor works in the ways that were measurable and fails in the ways
   that were measured**, with the cause identified to three decimal places.
6. **The cause was not the detector.** A false-alarm budget of 0.1 per hour was
   being divided among 720 decisions an hour, demanding a per-decision
   false-positive rate of 0.00014. Deciding once per session loosens that by the
   pooling factor — to 0.0083, needing AUC 0.990 against 0.673–0.742 observed.
   Better, but not a rescue.
7. **Two numbers were still missing, and could not be measured here at all.**
   Lead time depends on an onset nobody recorded, and 1.4 hours of genuinely
   fault-free recording cannot bound a rate of 0.1 per hour. **No published
   decoder-health monitor has either number attached.**
8. **So a physical apparatus was designed to supply both** — failures beginning
   at moments drawn at random and checksummed before each recording exists, and
   campaigns that run unattended for the tens of hours a false-alarm bound
   needs. That phase is specified, coded, and preregistered; see
   [`physical/`](physical/README.md).

## Reproducing it

```bash
pip install -r requirements.txt
python3 scripts/01_download_dataset.py      # needs DRYAD_CLIENT_ID / _SECRET
python3 scripts/17_fault_injector.py verify
python3 scripts/18_reference_decoder.py fit
python3 scripts/20_evaluation_harness.py run --local
python3 scripts/21_score_report.py --local
python3 scripts/24_benchmark_matrix.py
```

Raw data (~9 GB) is not committed; the download script verifies SHA-256
checksums against a manifest. Scripts are numbered in dependency order, with
**two exceptions that run last**: `31_verify_claims.py` and
`55_reproducibility_audit.py` both consume the output of most other scripts, so
their numbers record when they were written rather than where they run. That is
checked, not assumed — see below.

To check that the numbers quoted in these documents still match the data they
came from:

```bash
python3 scripts/31_verify_claims.py
```

It recomputes every headline figure from `data/processed/` and compares each
against the value written in the reports — **102** of them as of 21 September
2026, and the script prints the count, so this sentence cannot drift out of date
without the script saying so. Run it before quoting any figure.

```bash
python3 scripts/55_reproducibility_audit.py
```

```bash
python3 scripts/56_claims_register.py
```

```bash
python3 scripts/61_statistical_hygiene.py
```

```bash
python3 scripts/65_log_coverage.py
```

It fails if any date with commits has no research-log entry and no explicit
reconciliation — so a day's work cannot vanish from the record silently.

The hygiene linter scans every script for the three statistical error classes this project has
actually made — inference on pooled non-independent units, a comparison that can
never be true, and inverse-variance weighting of a bounded statistic — and fails
on any site not explicitly reviewed.

The register regenerates and fails if anything marked ESTABLISHED
cites a check that does not exist, or if a verifier check is cited by no claim.
Currently 38 claims covering 93 of 93 checks.

The audit checks that the reproduction path itself holds: every import declared, every
consumed file produced by some script, no ordering inversions, and every script
named in a document present. It found a headline figure that no committed script
regenerated — see [`reports/REPRODUCIBILITY_AUDIT.md`](reports/REPRODUCIBILITY_AUDIT.md).

## Layout

```
scripts/     01-76; 31, 55, 56, 61 and 65 run last, everything else in order
research/    design decisions, preregistrations, the dated log
reports/     results, figures, the demo
data/        raw (gitignored) and processed outputs
rig/         the first version of the bench apparatus
physical/    the physical-validation phase: docs 00-08, code, and its own data
```

The two halves answer different questions. `scripts/` asks what a
decoder-health monitor does on archived human recordings, where nobody wrote
down when the electrodes started failing. `physical/` builds a system where
that moment **is** written down — drawn at random and checksummed before each
recording exists — so that lead time and false-alarm rate stop depending on
which moment an analyst picks.

## Honest limitations

- **Two participants, and they disagree.** They disagreed in Phase 1–2 and again
  on a later prediction. With n = 2 an improvement cannot be told from noise.
  **This is the binding limitation.**
- **Open-loop evaluation.** Injected faults are replayed, so no live person
  adapts. Performance is decoder output error, not task success.
- One fault type stops being a clean test at high severity.
- **Attribution names the wrong cause for one fault type, always.** Overall 56%
  (T11) and 52% (T5) against chance of 25% and 33%, but `GEOMETRY_ROTATION` is
  named correctly **0%** of the time on both arrays. The cause is not the ranking
  rule — `profile` is lit in 80% of those episodes, yet `dispersion` reads z = 16.5
  against its 1.9. Rotation is injected as norm-preserving, and `dispersion` is
  *defined* as channels spreading with the total conserved: the same signature.
- **The p-values in `ACHIEVABILITY.md` were invalid and are corrected.** They
  pooled windows, inflating the apparent sample size **26.6×**; four were
  published as `p = 0`. The AUC values and verdicts stand (median shift 0.020),
  but three results significant as published are not significant at the episode
  level — including one published at `p = 3.4e-15` that is actually `p = 0.144`.
- **Every AUC here is understated by about 1%.** 30 s windows stepped every 5 s
  mean six "pre-onset" windows per episode actually contain faulted data, so the
  healthy reference is contaminated toward the fault. Measured cost: +0.0072 (T11)
  and +0.0123 (T5) AUC recovered by a strict reference; 11 of 13 non-tied sessions
  improved, sign test p = 0.011. The bias is conservative, as was argued when it
  was found — it is now a number rather than an argument. No conclusion changes.
- **Severity is only valid in aggregate.** The three fault levels were
  calibrated once, globally, and produce correctly ordered damage in just **57%**
  of session × fault-mode cells on T11 and 67% on T5 — degrading with the
  session's baseline error on both arrays (ρ = −0.677 and −0.926). Pooled results
  are unaffected; any severity-stratified claim *within* a session is not.
- **The performance metric saturates, and its saturation point moves.** Angular
  error against intended direction has chance near 90°, so on a session already
  there an injected fault is invisible to the ground truth by construction — on
  the worst session 1 of 20 faults did measurable damage, on another none did.
  Worse, each session's *own* chance level ranges 47.7°–102.7° because sessions
  differ ~50× in how directionally varied the task was. A replacement metric needs
  range at the bad end **and** robustness to task geometry.

## Attribution

Primary dataset: Pun, Khoshnevis, Hosman et al. (2024), *Communications Biology*,
[doi:10.5061/dryad.n2z34tn5s](https://doi.org/10.5061/dryad.n2z34tn5s). Their
published instability result is reproduced exactly (r = 0.985) in
`scripts/09_reproduce_mindful.py` as a check that this pipeline reads their data
correctly.
