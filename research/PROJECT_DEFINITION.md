# What this project actually is

**Written:** 26 August 2026, after Phases 1–2 completed and before any ISEF
section was drafted.
**Purpose:** work *backward* from the final product, so that every later choice
(question, hypothesis, experiment, analysis) is derived rather than assumed.
**Status:** proposal for the researcher to accept, reject, or amend. Nothing here
is frozen. `research/FROZEN_DESIGN.json` governs the *Phase 1–2* analysis only
and is unaffected by anything in this document.

---

## 0. Read this first: the honest starting position

Phases 1–2 tested the original idea — early-warning signals of decoder failure,
via critical slowing down — on the best public data that exists for it. **The
result was negative, and the reasons it was negative are the most valuable thing
this project owns.** Specifically:

| What was found | Why it constrains the project |
|---|---|
| No observable in the data has a measurable recovery rate (0.3–0.7 samples of memory) | The **autocorrelation half of critical slowing down cannot be tested at all** on session-level iBCI data |
| The variance indicator is 71% mean firing rate (R²=0.707) | "Neural instability" and "the electrodes are dying" are **not separable** by that measure |
| Mean firing rate alone predicts performance as well as the whole pipeline (ρ=−0.880 vs +0.858) | A one-line comparator matches a five-dimensional one. **Sophistication was not the bottleneck** |
| The indicator rose *faster* during healthy performance than overall (τ=+0.857, p=0.0018) | The detector **was not silent when the system was healthy** — the disqualifying failure |
| The indicator is task-invariant (8.4% difference between cursor task and free web browsing on the same day) | It measures **the recording**, not the human–decoder system |
| T5 and T11 disagree in sign | No cross-participant generality was demonstrated |
| **We never knew when deterioration actually began** | Every "how early is the warning?" claim in Phase 1–2 was **unverifiable in principle** |

That last row is the hinge of this entire document. Everything below follows
from it.

---

## 1. The problem with the original project, stated plainly

The original plan was: *find early-warning signals in a public dataset that
precede decoder performance decline.*

The fatal issue is not that the result came out negative. It is that **the
question as posed cannot be answered by that dataset, or by any observational
dataset, in a way that could be checked.**

Here is why. To claim "the warning arrived 12 days early," you need to know when
the thing being warned about *started*. In the public data we do not know that.
We only see performance drop at some point and then define, retrospectively, that
the drop was "the event." So the lead time is a function of our own definition,
not of the world. Change the definition and the lead time changes. That is
circular, and no amount of statistical care fixes it — Phase 1–2 spent a great
deal of care on exactly this (`research/deterioration_definition.md` compares six
definitions and freezes one in advance) and the circularity survived the care.

> **You cannot validate an early-warning system without a system in which you
> control, and therefore know, when the warning should have fired.**

This single sentence is what makes an original experiment *logically necessary*
rather than a science-fair add-on. It is not "I should also collect some data of
my own." It is: **the central claim is unverifiable without it.**

---

## 2. Critical evaluation of four possible projects

The instruction was not to assume the current idea is the best one. So here are
four, evaluated against what Phases 1–2 established.

### A. Early-warning detector for decoder deterioration (the original)

**Mechanism assumed:** the human–decoder system approaches a bifurcation, and
critical slowing down (rising variance, rising autocorrelation) precedes it.

**Verdict: weakest of the four. Do not build the project on this.**

- Autocorrelation is unmeasurable here — established empirically, not assumed.
- The bifurcation premise is itself doubtful. Phase 1–2 found a monotonic 56.5%
  decline in firing rate over 142 days, with an adaptive-normalisation
  compensator in the decoder masking it until it saturated. That is a *ramp into
  a saturating compensator*, which is not a fold bifurcation and does not
  generically produce critical slowing down.
- Committing a year to a mechanism the pilot data argues against is bad research
  strategy, regardless of how elegant the theory is.
- It is also the framing most vulnerable to the "you found a correlation and
  called it a detector" criticism that was explicitly to be avoided.

### B. Broader failure-prediction framework (predict time-to-recalibration)

**Verdict: better, but generic and underpowered as stated.**

- Drops the CSD commitment, which is correct.
- But "extract many features, fit a model, predict a label" is a very common
  project shape, and with 2 participants and ~40 sessions it is severely
  underpowered and highly exposed to leakage. Phase 1–2 already showed that
  *nothing survived controlling for elapsed time* — a time-to-event model on this
  data would mostly be learning "later = worse."
- Its real weakness: it still has no ground truth for onset, so it inherits the
  circularity of A.

### C. Multimodal signal-quality detector (combine several indicators)

**Verdict: adds cost, and the pilot predicts it adds little.**

- The empirical finding that mean firing rate alone matches the full pipeline is
  direct evidence that the marginal value of *more* indicators on this data is
  small. Combining several confounded measures does not decontaminate them.
- Multimodality is worth having as a *component*, not as the project's identity.

### D. A validated decoder-health monitor, with the ground truth built rather than assumed

**Verdict: strongest. This is the recommendation.**

Reframe the deliverable from *"a signal that predicts failure"* to *"a monitor
that reports decoder health, plus the experimental system that proves whether any
such monitor works."*

Why this dominates A–C:

1. **It is mechanism-agnostic.** It does not need critical slowing down to be
   true. Whatever measure passes the gates, passes.
2. **It converts the pilot's failure into the contribution.** The five gates from
   `research/phase3_design_implications.md` — silence during health, invariance
   to firing rate, beat the trivial comparator, survive time control, de-trend
   before trend-testing — become the *validation standard*, which is a real and
   currently-missing methodological product.
3. **It makes the original experiment logically necessary** (§1), not decorative.
4. **Its output is actionable, not just significant**: a state and an attribution,
   which map onto different real responses.
5. **Its impact is measurable rather than asserted**: you can run the closed loop
   with and without the monitor and count recalibrations.

**Honest weaknesses of D, stated now rather than discovered later:** it is a
larger build; it requires human participants and therefore ISEF Forms; and its
transfer claim (from the student's recorded signals to intracortical data) is a
claim that must be *tested*, not assumed. §8 addresses each.

---

## 3. The final product

Three things, all of which exist as artefacts a judge can inspect and run.

### 3.1 `decoder-guard` — a real-time decoder-health monitor

A software system that sits alongside a decoder, reads **the same feature stream
the decoder reads** (channels × binned activity), and never sees the decoder's
output or the task labels. It emits, once per update:

| Output | Type | Meaning |
|---|---|---|
| **Risk score** | continuous, 0–1 | calibrated deviation of the current feature distribution from the fitted-healthy reference |
| **Warning state** | `NOMINAL` / `WATCH` / `WARN` / `FAIL-LIKELY` | thresholded risk, with hysteresis and dwell requirements so it cannot chatter |
| **Attribution** | one of a fixed, small set | *which* failure mode dominates the risk: `RATE-LOSS`, `CHANNEL-DROPOUT`, `GEOMETRY-ROTATION`, `GAIN-DRIFT`, `TASK-CHANGE` |
| **Confidence** | continuous | how well-supported the attribution is; low confidence is reported, not hidden |

Two design commitments that follow directly from Phase 1–2:

- **It is fitted on healthy data only** (one-class). It never sees a degradation
  label during fitting. This is what prevents the leakage that a supervised
  failure-predictor invites.
- **`TASK-CHANGE` is an explicit output class.** Phase 1–2 found the old
  indicator gave nearly the same value during a structured cursor task and during
  free web browsing. A monitor that cannot say "the neural statistics changed
  because the person is doing something different" will generate false alarms in
  real use, and that is the difference between a lab result and a usable device.

Interpretability is a requirement, not a nice-to-have: every risk score
decomposes into named, unit-carrying contributions, so the answer to "why is it
warning?" is a sentence, not a number.

### 3.2 The degradation-controlled corpus — original data with known onset

A recorded dataset from a closed-loop control system built for this project, in
which degradations are **injected at times the experimenter chose and logged
before the session**, at controlled types and rates. This is the ground truth that
does not exist anywhere publicly. See §5.

### 3.3 The validation protocol and benchmark

A published, runnable evaluation that any decoder-health monitor can be put
through — the five gates plus the lead-time/false-alarm operating curve, with
reference implementations of three baselines (mean firing rate; the Phase 1–2
robust-dispersion indicator; MINDFUL's KL divergence, already reproduced exactly
in `scripts/09_reproduce_mindful.py` at r = 0.985).

> If the monitor itself fails the gates, **the benchmark is still the
> contribution**, and the project still concludes with a real finding. This is
> deliberate: the project is designed so that a negative result is publishable.
> Phase 1–2 is the proof that this is not a rhetorical safety net.

---

## 4. The scientific question, the engineering problem, the hypothesis

These are three different things and the project has all three. Keeping them
separate is what stops "engineering goal" from quietly becoming "hypothesis."

**Scientific question.**
> When a neural control interface degrades, does the *statistical structure* of
> the input signal change measurably *before* closed-loop task performance
> changes — and if so, is that change distinguishable from the change caused by
> the user simply doing something different?

The second clause is the part the literature and Phase 1–2 both skate over, and
it is where the science is. The reason a warning can arrive before performance
drops at all is the **compensation gap**: the human adapts, and the decoder's own
adaptive normalisation adapts, so performance is held flat while the underlying
signal is already degrading. Phase 1–2 documented that compensator in the
published system. The gap between "signal is degrading" and "performance has
dropped" is not noise — it is the quantity being detected.

**Engineering problem.**
> Build a monitor that converts that statistical change into a warning state
> early enough to act on, at a false-alarm rate low enough to be worth having,
> and with an attribution specific enough to choose the right action.

**Primary hypothesis (H1).**
> For injected degradations of known onset, `decoder-guard` reaches `WARN` before
> closed-loop task performance crosses its degradation threshold, with a median
> lead time greater than zero, at a false-alarm rate ≤ 1 per 10 hours of matched
> healthy operation.

**H2 (specificity).**
> Attribution accuracy across the four injected failure modes exceeds chance, and
> genuine task changes are classified `TASK-CHANGE` rather than as failures.

**H3 (transfer).**
> The identical monitor, with no refitting of its structure, produces risk scores
> on the public intracortical dataset that pass the five gates — in particular,
> that it is **silent during T11's healthy baseline**, which the Phase 1–2
> indicator was not.

**H4 (impact — the reason any of this matters).**
> A recalibration policy driven by the monitor's `WARN` state achieves task
> performance no worse than fixed-schedule recalibration while performing
> significantly fewer recalibrations.

H4 is the one that turns a detector into a benefit. It is also the one most at
risk of being cut for time, so it is staged explicitly in §9.

**Null / falsification, stated in advance.** H1 is false if median lead time is
≤ 0, or if the false-alarm constraint cannot be met at any operating point. H3 is
false if the monitor trends during healthy baseline. **Any of these being false
is a reportable result, not a failure of the project.**

---

## 5. The original experimental system, and why it is logically necessary

### 5.1 The necessity argument in one paragraph

Lead time = (time performance crossed threshold) − (time the monitor warned). In
observational data the first term is defined by the analyst, so lead time is
partly an artefact of that definition, and the false-alarm rate cannot be
estimated at all because there is no known-healthy period of controlled length
with no impending event. Both terms become measurable the moment the experimenter
controls onset. **Therefore an experimental system with injected, pre-logged
degradation is not an addition to the study; it is the only configuration in
which the study's primary claim is checkable.**

### 5.2 What is actually built

A closed-loop continuous-control testbed:

```
 biological signal  →  feature extraction  →  decoder  →  cursor  →  screen
        source           (channels × bins)                              ↓
                                │                                    human
                                ├──→  decoder-guard  →  risk / state / attribution
                                │
                        degradation injector  (type, onset, rate — logged in advance)
```

Every element is real hardware and real software the student builds or
configures. The human is in the loop, which matters enormously: **the
compensation the project is trying to see through only exists when a real person
is adapting.**

### 5.3 The signal source — the one genuinely open decision

The abstraction the monitor consumes is *multichannel, non-stationary, binned
activity*. Three sources fit it, and they trade off realism against feasibility:

| Source | Realism of degradation | Feasibility | Human subjects? |
|---|---|---|---|
| **Surface EMG**, multichannel, cursor control | **High** — electrode lift-off, gel drying, sweat, fatigue, posture shift are *real* physical degradations with the same character as electrode failure | Moderate — needs an isolated, battery-powered, commercially-made amplifier | Yes → Form 4 |
| **Hardware-in-the-loop replay rig** — recorded spike trains played through a real analog front end with switchable channel loss / attenuation | Moderate — real analog path, synthetic source | High | No |
| **Consumer EEG** | Low for this purpose — poor channel count, dominated by artefact | High | Yes → Form 4 |

**Recommendation: EMG as primary, replay rig as the controlled ladder.** The rig
gives a clean severity ladder (dropout of 1, 2, 4, 8, 16 channels; gain drift of
−5%, −10%, −20% per hour) with perfect repeatability and no ethics burden; EMG
gives the human-in-the-loop compensation that the rig cannot fake. Together they
cover both halves of the argument. **This decision is the researcher's to make
and is deliberately left open here.**

### 5.4 What may be simulated, and what may not

A single rule, which is worth stating in the plan verbatim because it is the
methodological line the project must not cross:

> **The perturbation may be simulated. The response to it may not.**

| Legitimately simulated | Must be real |
|---|---|
| The degradation schedule (which mode, when, how fast) | The signal's own non-stationarity — simulating it assumes the answer |
| Surrogate and permutation null distributions | The human's adaptive compensation |
| Power analysis and the severity ladder | The decoder's adaptive normalisation |
| Sensor-failure *mechanism* on the replay rig (switched attenuation) | The analog front end it passes through |

Simulating the thing you are trying to detect is circular: you would be
measuring your own generative assumptions. That is the same error, in a different
costume, as choosing a deterioration definition after seeing which one gives the
best result — which this project already refused to do once.

---

## 6. Variables

**Independent (manipulated, in the original experiment):**

1. Failure mode — `RATE-LOSS`, `CHANNEL-DROPOUT`, `GEOMETRY-ROTATION`,
   `GAIN-DRIFT`, plus `TASK-CHANGE` and `NONE` as controls (6 levels).
2. Degradation rate — fast / medium / slow (3 levels), spanning at least a
   tenfold range in time constant.
3. Severity at endpoint — sub-threshold / threshold-crossing (2 levels).
4. Onset time — randomised within the session and **logged before the session
   runs**, so it cannot be adjusted after seeing the data.

**Dependent (measured):**

- **Primary:** lead time (seconds), signed, from `WARN` to performance-threshold
  crossing.
- **Primary constraint:** false `WARN` rate per hour on matched `NONE` sessions.
- Attribution accuracy (confusion matrix over the 6 levels).
- Risk-score calibration (does risk 0.8 mean 80%?).
- **H4:** recalibration count and task performance under three policies —
  monitor-triggered, fixed-schedule, never.

**Controlled / held constant:** participant, electrode montage, task, decoder
architecture and its hyperparameters, session time of day, and the monitor's
operating point (frozen before the test set is touched).

**Confounds identified in advance, from Phase 1–2:** elapsed time within session;
overall signal amplitude (the firing-rate confound in its EMG form); task
difficulty; participant learning across sessions. Each is either randomised
(onset time), counterbalanced (mode order), or measured and regressed (amplitude,
elapsed time).

---

## 7. Failure defined objectively, and leakage prevented

**The event, non-retrospectively.** In the original corpus the degradation onset
is *defined by the injection log written before the session*. It is not inferred
from the data at all. This is the property no public dataset has. The
performance-threshold crossing is defined by a rule fixed in advance (a
prespecified drop in the same performance metric used throughout Phase 1–2,
relative to that session's own pre-onset baseline).

**Leakage controls, all decided before data collection:**

1. **One-class fitting.** The monitor's reference is fitted on healthy segments
   only. It never sees a degradation label.
2. **Split by session and by participant**, never by time window within a
   session — adjacent windows are correlated and splitting within a session
   would leak.
3. **Three-way split with a frozen operating point.** Develop on the public iBCI
   data (T11) → freeze thresholds and all hyperparameters → evaluate once on the
   original corpus → evaluate once on the held-out participant and on T5.
4. **Preregistration before the test set is opened**, using the same mechanism
   already built and used once: `scripts/12_freeze_design.py`, which records a
   git commit hash and file checksums so the ordering is verifiable by a third
   party rather than asserted.
5. **The public dataset serves discovery; the original corpus serves
   confirmation.** This is exactly the division the two datasets can honestly
   support, and it is why having both is worth more than having either.

---

## 8. The three honest risks, and what is done about each

**Risk 1 — transfer.** EMG is not cortex. A judge will ask, correctly, whether
anything here says something about iBCIs.

*Response:* the monitor consumes an abstraction (channels × binned activity) that
both satisfy, and **the same code, unmodified, is run on the public
intracortical dataset** — that is H3, and it either passes the gates or it does
not. The claim is tested, not argued. Notably the pilot already establishes the
bar it must clear: it must be silent across T11's healthy baseline, where the
previous indicator rose from 23.6 to 50.4.

**Risk 2 — scope.** Four failure modes, attribution, real-time operation, a
benchmark, and a closed-loop impact demonstration is a lot for one year.

*Response:* §9 stages it so that each stage is independently reportable, and the
project has a defensible result even if it stops at Stage 2.

**Risk 3 — the monitor may simply fail the gates.**

*Response:* that is a real possibility and it is planned for. Phase 1–2 already
demonstrates the project's willingness to report a negative result from a frozen
design. If nothing passes, the deliverable is the benchmark plus the evidence
that a class of methods does not work on this problem, with the mechanism
(rate-confounding and compensator-masking) identified. That is a genuine
contribution and it is a more useful one than a fragile positive.

---

## 9. Staging, so that every stage is a reportable result

| Stage | Deliverable | Standalone result if the project stops here |
|---|---|---|
| **1. Benchmark** | The five gates + three baselines, run on the public data | *"Published iBCI instability measures fail the silence gate; here is why and here is the test"* — already 80% complete |
| **2. Rig** | Replay rig + injector + `decoder-guard` v1 (risk + state) | *"Lead time and false-alarm rate measured against known onset for the first time"* |
| **3. Human loop** | EMG closed-loop corpus with human compensation | *"Compensation masks degradation by N seconds; the monitor sees through it"* |
| **4. Attribution** | Failure-mode classification incl. `TASK-CHANGE` | *"Warnings are actionable, not just present"* |
| **5. Impact** | Monitor-triggered vs fixed-schedule recalibration (H4) | *"K% fewer recalibrations at equal performance"* — the headline |

Stage 1 uses work that already exists in this repository. Stages 2 and 4 require
no human participants. Stage 3 is the one gated on ISEF approval, so its
paperwork starts first even though it runs third.

---

## 10. Success criteria, measurable and set now

| # | Criterion | Threshold |
|---|---|---|
| S1 | Median lead time on injected degradations | > 0 s, with a 95% CI excluding 0 |
| S2 | False `WARN` rate on matched healthy sessions | ≤ 1 per 10 h |
| S3 | **Silence gate** — monitor's trend during healthy baseline | not significant at α = 0.05, on *every* healthy segment tested |
| S4 | Beats the trivial comparator | outperforms mean-amplitude/mean-rate alone on S1 at matched S2 |
| S5 | Survives elapsed-time control | S1 holds with elapsed time regressed out |
| S6 | Attribution accuracy | > chance (1/6), with `TASK-CHANGE` recall > 0.8 |
| S7 | Transfer | passes S3 unchanged on public T11 data |
| S8 | Impact | fewer recalibrations than fixed schedule at non-inferior performance |

S3 is non-negotiable and comes first in reporting order: **an indicator that is
not silent when the system is healthy is not a detector, whatever its p-value.**
That sentence is the thing Phase 1–2 bought, and it is the spine of the project.

---

## 11. What is decided, and what is still the researcher's call

**Decided by evidence** (Phases 1–2, reproducible in this repository):

- Critical slowing down via autocorrelation is not testable on session-level iBCI
  data — measured, not assumed.
- Any indicator must be demonstrated invariant to overall signal level, and must
  beat mean rate as a comparator.
- The silence gate is mandatory and comes before any trend test.
- Ground truth for onset requires an experiment; observational data cannot
  supply it.

**Open, and deliberately left to the researcher:**

1. **Signal source** — EMG primary, or rig only, or both (§5.3). This is the
   single biggest decision and it drives the ISEF forms, the timeline, and the
   equipment budget.
2. **How many failure modes** — four is proposed; two (rate-loss and dropout)
   would be defensible and much faster.
3. **Whether Stage 5 (impact) is in scope this year** or is stated as the next
   step.
4. **The performance threshold rule** for the original corpus — must be fixed
   before data collection, not after.

Nothing in §11 should be answered by asking which choice would produce the
better-looking result.
