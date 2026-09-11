# Phase 3 — Building and testing a decoder-health monitor

**Status:** complete. Every result below is reproducible from this repository.
**Reproduce the whole chain:** `scripts/17` → `18` → `20` → `21` → `24` → `26` →
`27` → `28` → `29`.

---

> **Terminology note.** Throughout this project, "participant" means **whose
> published recording a data file contains** — the convention used by the
> researchers who collected it, who label their de-identified subjects T5, T11,
> T15. It does **NOT** mean a person this project recruits.
>
> **This project has no human participants in the ISEF sense.** Nobody is
> recruited, nobody wears anything, no consent forms are collected, and Form 4
> is not required. "Adding a third participant" means **downloading one more
> public data file** that somebody else collected years ago under their own
> ethics approval. See Amendment 1 in `research/PROJECT_DEFINITION.md`.

---

## 1. What Phase 3 set out to do

Phases 1–2 tested the original early-warning-signal idea on public intracortical
BCI data under a frozen design and returned a **negative** result. More
importantly, they exposed a problem that no amount of analysis could fix:
**observational data cannot say when deterioration began**, so lead time is
partly an artefact of the analyst's own definition and the false-alarm rate is
not estimable at all.

Phase 3 therefore built the ground truth rather than looking for it, and then
built a monitor and an honest test for it.

---

## 2. What was built

| Component | What it is |
|---|---|
| **Fault injector** (`scripts/17`) | 1,073 episodes on T11 and 777 on T5. Four fault types, three rates, three severities. Onsets drawn and locked to disk under a git hash and SHA-256 **before** any detector existed; re-drawing is refused without a recorded reason. Original files never modified. |
| **Reference decoder** (`scripts/18`) | Grades only. Ridge regression to intended movement direction, frozen after fitting. 54.6° median angular error on held-out healthy T11 against 90.7° chance; 52.8° vs 84.9° on T5. |
| **Detector contract** (`scripts/19`) | A detector sees only the feature stream — never the decoder output, the task, the performance number, or any fault label — and is fitted on healthy windows alone. Three baselines to the same standard. |
| **Evaluation harness** (`scripts/20`, `21`) | 30 s windows stepped every 5 s. Lead time and false-alarm rate reported as a pair, never one number. Five gates, silence first. Splits by block; one free parameter chosen on validation; test read once. |
| **`decoder-guard`** (`scripts/22`) | Four named components — level, silence, dispersion, profile — each calibrated against healthy data, the largest reported as risk *with its cause named*. Works in log space so a uniform gain change becomes an additive shift and can be separated from a change in the shape across channels. |

**The grading system was built and committed before the monitor existed.** When
`scripts/20` and `21` were committed, the only detectors they could score were
three baselines this project did not invent.

---

## 3. Results

### 3.1 The benchmark: 48 configurations, none passes

Four detectors × two baseline strategies × four transforms × two participants.

| Of 48 configurations | Count |
|---|---|
| Found an operating point | 47 |
| Achieved positive median lead time | 10 |
| Met the false-alarm budget (≤0.1/h) | 3 |
| **Passed the silence gate** | **0** |
| **Passed all five gates** | **0** |

### 3.2 But the information is present

Stripping away every threshold and state machine, and asking only whether one
window's raw score separates the early-warning interval from healthy recording:

| Condition | `decoder_guard` AUC |
|---|---|
| Calibrated once, applied months later | **0.491** — chance |
| Re-baselined on recent healthy data, T11 | **0.693** |
| Re-baselined on recent healthy data, T5 | **0.707** |

**Calibrate-once carries no information at all** — that failure is a bound, not a
shortfall of effort. With a recent baseline the information is real.

### 3.3 The monitor beats the trivial comparator, and exactly where designed

Phase 1–2 found that counting activity matched a five-dimensional pipeline, so
this is the comparison that decides whether any of the work was worth doing.

| Fault | `decoder-guard` (T11 / T5) | counting activity |
|---|---|---|
| overall signal loss | 0.61 / 0.64 | **0.80 / 0.78** |
| electrodes dying | 0.65 / 0.75 | **0.73 / 0.77** |
| **channels drifting apart** | **0.79 / 0.73** | 0.41 / 0.40 |
| **signal shape rotating** | **0.76 / 0.71** | 0.52 / 0.51 |

Counting activity is **at or below chance** on both faults that conserve total
activity — as those faults were constructed to be — while the monitor reaches
0.71–0.79. It loses on the fault that *is* nothing but overall activity, which is
correct behaviour. **The pattern replicates on both participants**, who disagreed
in Phase 1–2.

### 3.4 The clean positive: task changes are not mistaken for faults

The dataset contains days on which the same participant used the cursor task and
also did something entirely different, through the same electrodes, with nothing
wrong.

| Day 658 | Same task | Different task | Real fault | |
|---|---|---|---|---|
| **decoder-guard** | 11.16 | **8.67** | 135.35 | **15.6× separation** |
| robust dispersion | 0.14 | **0.46** | 0.29 | **would false-alarm** |

Day 665 gives **70× separation**. A monitor that alarms when someone switches
application trains its user to ignore it; this one does not. Robust dispersion
fails in the worst direction — a healthy task change scored *higher* than a real
fault.

### 3.5 Why nothing passes: the arithmetic

The budget is 0.1 false alarms per hour; the monitor decides every 5 seconds.
Treating healthy episodes as the independent unit (see §3.6):

| | T11 | T5 |
|---|---|---|
| Budget permits | 2.4 flags | 2.4 flags |
| Required per-session false-flag rate | 0.76% | 0.59% |
| Session AUC | 0.673 | 0.742 |
| **Detection achievable there** | **0.9%** | **1.8%** |
| **AUC needed for 80% detection** | **0.990** | **0.991** |

Three decision rules were compared by their **full curve**, not one operating
point: threshold, CUSUM, and CUSUM with a specificity gate. Detection inside the
budget: **0.0%** on T11 for all three. **The decision rule is not the bottleneck.**

### 3.6 Why nothing *can* pass by averaging: one measurement per session

| | T11 | T5 |
|---|---|---|
| Windows per session | 55 | 42 |
| **Lag-1 autocorrelation** | **0.995** | **0.980** |
| **Effective independent samples** | **0.1** | **0.4** |

**A session does not contain 55 measurements. It contains one measurement taken
55 times.** Six aggregators were tried; none beats a plain median, and the ones
leaning on the tail are near chance.

This single fact explains every negative result:

- CUSUM cannot help — accumulating 55 copies of one measurement adds nothing.
- Longer or more windows cannot help — there is no √N to collect.
- The silence gate always fails — a series with r = 0.995 *is* a trend, so
  testing it for one will nearly always find one.

### 3.7 The feature study: four families named in advance, none sufficient

Phase 3 ruled out better decision rules, longer windows and better aggregators,
leaving a better *measurement* as the only direction — and the direction most
exposed to fishing, since with two disagreeing participants a family that helps
one can be found by trying enough. So four families were named, the list closed,
and the criterion frozen at commit `0950c04` with a checksum before anything was
computed: **+0.05 session-level AUC over `decoder_guard` v1, on both
participants in the same direction.**

| Family | T11 Δ | T5 Δ | Verdict |
|---|---|---|---|
| F1 variability | +0.004 | −0.075 | no improvement on either |
| F2 covariance | −0.043 | −0.137 | no improvement on either |
| **F3 spectral** | **+0.078** | **−0.186** | **null — helped T11 only** |
| F4 counts | +0.003 | −0.212 | no improvement on either |

**F3 is the case the rule was written for.** It cleared the bar on T11 and failed
badly on T5. With one participant, or with the rule written after seeing the
table, it would have been the feature that worked.

**The null has structure** (post-hoc, and labelled as such in
`reports/FEATURE_STUDY_RESULT.md`). Against the matched control — the current
features through the *same* generic scorer — F1 (+0.106, +0.158) and F2 (+0.059,
+0.095) both clear +0.05 on both participants. They are better features. Nothing
passes anyway because `decoder_guard` beats its own features under that scorer by
+0.102 and +0.233: **its advantage is mostly the four-component decomposition,
not the per-channel means it consumes.** Better features are not enough to cover
that.

---

## 4. Corrections made during Phase 3

Recorded because the corrections are part of the result.

| Correction | Effect |
|---|---|
| **Threshold search stopped at 59** while scores reach 3,200. 15 of 36 configurations were reported as "no operating point exists" when none existed *below an arbitrary bound*. | Corrected to 1 of 48. Headline unchanged. |
| **Bound computed treating 5-second windows as independent**, which r = 0.995 refutes. | Recomputed with episodes as the unit: 0.9% detection and AUC 0.990 needed, against 0.18% and 0.9992. Rigorously different, practically identical. |
| **"The failure is in the machinery, a fixable engineering problem."** | Refuted by the decision-rule curves. The bottleneck is the measurement. |
| **`GAIN_DRIFT` was not mean-preserving**, twice — log-centring preserves the geometric mean (+116% at crossing severity), and pre-onset rescaling still left +20.8%. | Now conserved per bin: −2.4%. |
| **`CHANNEL_DROPOUT`'s severity ladder ran backwards** because levels drew independent channel sets rather than nested ones. | Nested; now monotone. |
| **Pre-onset guarantee held only by floating-point luck.** A leak would let a detector "warn" off the leak itself. | Enforced by construction. |
| **T5 ran with an empty test set.** | The harness now refuses rather than reporting nothing. |

A prediction was also recorded in advance (`research/DETECTOR_V2_RECORD.json`,
committed while the results files were untouched) and **split**: satisfied on
T11, falsified on T5. The change was **not adopted**.

---

## 5. Limitations

- **Two participants, and they disagree.** T5 and T11 disagreed in sign in
  Phase 1–2 and disagreed again on the joint detector. With n = 2 an improvement
  cannot be distinguished from noise. **This is the binding limitation.**
- **Open-loop evaluation.** Injected episodes cannot include a human adapting, so
  performance is decoder output error rather than task success.
- **`GEOMETRY_ROTATION` at crossing severity** clips 17% of entries and loses 18%
  of mean activity, so it stops being a clean test of the trivial-comparator gate.
- **Attribution names only 3 of 4 components**, meaning it partly collapses onto
  whatever is chronically lit.
- **Window overlap contaminates the healthy reference.** Windows are 30 s and
  step 5 s, so six windows that *start* before an onset still *span* it. With a
  typical 25 pre-onset windows, about **24% of the re-baselining reference
  contains post-fault data**. The bias is conservative — it pulls the reference
  toward the fault and so reduces sensitivity — and lead time, being a
  difference on the same windowing, largely cancels it. Fix for the next full
  run: require `start + window <= onset_bin`.
- **The task-change result rests on two days and four blocks.** A demonstration,
  not an estimate; no confidence interval is quoted because none would be
  meaningful.

---

## 6. What is ruled out, and what remains

**Ruled out on evidence, not preference:**

- Better decision rules — measured, all at 0% inside the budget
- Longer or more windows — no independent information to average
- Better session-level aggregators — six tried, none beats a median
- Calibrate-once deployment — carries literally no information (AUC 0.491)

**Ruled in as the only remaining direction:** a fundamentally better
**measurement** — different features, not more processing of these ones. The
current features are per-channel mean activity in a 30-second window. Untried:
per-channel variability, cross-channel covariance structure, spectral content.

---

## 7. Next steps, in priority order

1. **A third participant.** With two who disagree, this is worth more than any
   detector improvement. Card et al. 2024 (T15, 256 electrodes, different task,
   11.6 GB) is identified and costed; blocked only on Dryad credentials.
   *Even without a decoder for it, the silence gate needs only healthy
   recordings* — and would establish whether the failure belongs to these two
   arrays or to the approach.
2. ~~**A preregistered feature study.**~~ **Done** (§3.7). Four families named
   in advance, none sufficient. It newly indicates combining the better features
   (F1, F2) *with* the four-component decomposition rather than substituting for
   it — which is a new study needing its own preregistration, not a change to
   make on the strength of a post-hoc table.
3. **Re-run with adaptive normalisation.** The reference decoder deliberately
   froze its normalisation to isolate degradation from the compensator Phase 1–2
   identified. Running the other condition is a separate, stated experiment.

---

## 8. The honest summary

The project set out to build an early-warning system for BCI decoder failure.
It did not succeed, and it now knows why to three decimal places.

What it produced instead: **a benchmark that did not previously exist** (1,850
fault episodes with known onset), **a test battery** whose first gate would have
caught the Phase 1–2 error, **a replicated demonstration that the monitor
detects what counting spikes cannot**, **one clean deployment-relevant positive**,
and **a quantified bound** — AUC 0.99 required, 0.67–0.74 achieved, with a
measured explanation of why no amount of averaging closes the gap.

That is a more useful contribution than a fragile positive would have been, and
every step of it is reproducible.
