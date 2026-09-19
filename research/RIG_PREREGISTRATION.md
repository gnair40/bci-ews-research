# Preregistration — the physical rig study

**Drafted:** 7 September 2026.
**Status: DRAFT — NOT YET FROZEN. Nothing has been built and nothing measured.**
**Frozen at commit:** `[[RESEARCHER — fill in after running the freeze in §10]]`

> **AMENDED 19 September 2026 — P-R1 and P-R2 retargeted; no longer blocked.**
> Both took their thresholds from claim C18's pooled 0.902 and 0.784, which
> turned out to be raised by the sub-threshold fault ramp injected into those
> episodes rather than measured on fault-free recording
> (`reports/AUTOCORR_BY_SEVERITY.md`). The researcher chose option 1 of §11:
> retarget to the fault-free figures. The amendment is §12, the original wording
> is preserved there, and §11 is left standing as the record of why.

---

## 0. Read this before anything else

### 0.1 What this document is for

Everything in this project since Phase 3 has followed one rule: **write down what
you expect, and what would count as being wrong, before you look.** The reason is
not tidiness. If you test five things and report the one that worked, that looks
identical on paper to predicting one thing correctly. This document is what makes
those two look different, and it only works if its timestamp precedes the data.

Its force comes entirely from being committed to git before the first rig
recording exists. After that it must not be edited — only amended, in public, per
§9.

### 0.2 Who wrote this, and what that means

**This draft was written by an AI assistant from findings already in this
repository. It is not yet the researcher's preregistration, and it must not be
frozen until the researcher has read every prediction and either accepted or
changed it.**

The distinction that matters: the *derivations* below are mechanical — each
prediction follows from a measured number already in the repository, and the
source is cited on every line. The *thresholds* are judgement calls. A threshold
you accept without agreeing with is worse than no preregistration at all, because
it converts a genuine test into a formality.

**Change any threshold you disagree with. Now, not later.** After §10 is run,
changing one is an amendment with a public reason, and amendments that move a bar
toward a result are exactly the thing this mechanism exists to prevent.

### 0.3 Two decisions that must be answered before freezing

| # | Decision | Status |
|---|---|---|
| **D2** | **Build the hardware at all?** Declining leaves a defensible computational project and this document is discarded. | `[[RESEARCHER]]` |
| **D3** | **Channel count: 384, 192, or both.** Recommendation is 384, matching T11 — every day-effect finding (C07–C10, L03, P5) is a T11 finding, so matching it makes the comparison direct. 192 can be produced afterwards by pooling adjacent regions in software at no extra recording cost. | `[[RESEARCHER]]` |

**D1 (the deadline) is resolved and is no longer open.** Research plan draft due
15 September 2026; final plan December 2026; regional fair March 2027. Working
back from a mid-March fair: data collection must stop around **22 February 2027**;
the 10-week longitudinal arm must therefore start by **14 December 2026**; and
construction must begin by **23 November 2026**. That leaves roughly **9 weeks of
slack**. **The longitudinal arm (Arm B) is in.**

---

## 1. The question, in one paragraph

This project measured that no configuration of a decoder-health monitor passes
its five gates on real intracortical recordings, and located the cause in a
single number: a recording session **in which a fault is developing** contains
roughly one independent measurement, because the risk signal's lag-1
autocorrelation is 0.902–0.995 depending on
window spacing (claims C04, C18). **What the archived data cannot say is whether
that is a fact about cortex or about any multichannel sensor array that drifts
slowly** — there is no second kind of array in the dataset. It also cannot say
whether the 1,850 injected faults, every one of which is a mathematical operation
on a recorded matrix, resemble real physical degradation at all. This study
builds a physical array to answer both.

---

## 2. Predictions

Each prediction cites the archived number it is derived from, states the
threshold, states what would falsify it, and states what each outcome would mean.
**No prediction below has an outcome that is uninformative.** That is deliberate:
a study whose null result teaches nothing should not be run.

### P-R1 — The rig's quiet-state serial correlation looks like cortex's

> With **no imposed drift and no injected fault**, the rig's lag-1
> autocorrelation of the `decoder_guard` risk signal, measured on
> **non-overlapping** windows at a matched window count, will fall between
> **−0.12 and +0.54**.

- **Derived from:** the **fault-free** rows of `reports/AUTOCORR_BY_SEVERITY.md`.
  T11 gives **0.085** [−0.122, +0.453] on 17 episodes of 10 windows; T5 gives
  **0.435** [+0.271, +0.540] on 15 episodes of 7 windows. The band is the union
  of those two intervals.
- **Why a band and not a floor:** the two participants disagree by 0.35 and
  their intervals barely overlap, so there is no single value to predict. A band
  spanning both is the honest form. **This was previously a one-sided bar of
  ≥ 0.70, which the fault-free figures sit well below** — as written it would
  have failed for a reason having nothing to do with the rig.
- **Stated weakness, because it matters:** this band covers about a third of the
  possible range of a correlation, so confirming it is weak evidence. It rules
  out the two outcomes that would matter most — a rig pinned near zero, or one
  pinned near its ceiling — and little else. **P-R2 is the sharp prediction; this
  one is a sanity bound.** `[[RESEARCHER: accept or change]]`
- **Matched window count is part of the prediction, not a detail.** The lag-1
  estimator is biased low at short series and the bias depends on the length, so
  a rig block must yield 9–10 decimated windows to be comparable to T11 at all.
  Build manual step B-8.
- **Falsified if:** the median fault-free non-overlap r falls outside
  [−0.12, +0.54].
- **If confirmed:** the rig's quiet state is not distinguishable from cortex's,
  so it is a fair platform for the comparisons that follow.
- **If falsified:** the rig is not comparable to cortex in its quiet state, and
  every later comparison must be reported with that caveat attached rather than
  quietly ignored.
- **Measured by:** `scripts/66_window_spacing.py`, unchanged, at the every-6th
  spacing.

### P-R2 — A monotone fault raises serial correlation on hardware too

> On the rig, episodes carrying a **sub-threshold injected fault** will show a
> non-overlap lag-1 autocorrelation **at least 0.20 higher** than fault-free
> episodes from the same rig.

- **Derived from:** the severity split in `reports/AUTOCORR_BY_SEVERITY.md`. On
  cortex the rise from fault-free to sub-threshold is **+0.838** on T11
  (0.085 → 0.923) and **+0.390** on T5 (0.435 → 0.825). The bar of 0.20 sits
  below the smaller of the two, deliberately, so the prediction is not a
  restatement of the cortical numbers. `[[RESEARCHER: accept or change]]`
- **This replaces the original P-R2 entirely, and in the opposite direction.**
  The original predicted effective independent samples **below 2**, derived from
  C18's pooled figures. Fault-free cortex gives **8.44** (T11) and **2.75**
  (T5), so that bar was not merely mis-set, it was pointed the wrong way. The
  original text is preserved in §12.
- **Why this is now the sharp prediction:** it tests the mechanism rather than
  the number. Every fault in this project is a monotone ramp, and a ramp raises
  lag-1 autocorrelation on its own. If the same rise appears in a camera, the
  effect belongs to monotone degradation in any many-channel drifting sensor
  and not to neurons — which is precisely what Arm B exists to establish.
- **Falsified if:** the rise is under 0.20, absent, or negative.
- **If confirmed:** the mechanism behind C04 and C18 is general, and the
  project's central limit is a fact about this class of measurement problem
  rather than about cortex. **This is the stronger outcome.**
- **If falsified:** the ramp-driven correlation is neural-specific, which makes
  it a property of the brain worth studying in its own right and means the
  fault-injection benchmark does not transfer between domains.
- **Measured by:** `scripts/70_autocorr_by_severity.py`, unchanged, which splits
  by injected severity and now discovers any participant the harness has scored.
- **Not independent of P-R1**, and deliberately so: both read the same quantity.
  P-R1 bounds the quiet state, P-R2 tests what a fault does to it. They are
  reported as one finding with two parts, never counted as two pieces of
  evidence.

### P-R8 — A session-level monitor clears the archived shortfall

> On the rig, scoring **one decision per session**, the session-level AUC of
> `decoder_guard` will exceed **0.80** — above the 0.673 (T11) and 0.742 (T5)
> measured on the archived data, and below the 0.933 the design target requires.

- **Added 19 September 2026 as Amendment 2**, and it is now the centrepiece of
  Arm B. See `reports/SESSION_MONITOR_DESIGN.md` for why the drift sweep was
  demoted to make room.
- **Derived from:** `reports/OPERATING_POINT_BOUND.md`. Flagging 80% of
  degrading sessions while wrongly flagging 10% of healthy ones needs a
  session-level AUC of **0.933**. The archived monitor reaches 0.673 and 0.742.
- **Why 0.80, and why that is not a manufactured success:** 0.80 is a bar the
  archived data **fails**, so confirming it is a real result rather than a
  restatement. It is also well short of 0.933, so confirming it does **not**
  license claiming the monitor works. The interesting outcomes are all three:
  below 0.74 means the rig is worse than cortex and the analogy is in trouble;
  0.80 to 0.93 means the gap is narrowed but not closed; above 0.93 means a
  deployable monitor, which would be the strongest result this project could
  produce. `[[RESEARCHER: accept or change]]`
- **Falsified if:** session-level AUC is at or below 0.80.
- **Measured by:** `scripts/73_monitorability_certificate.py`, on 101 healthy
  and 101 constructed-degradation sessions — the schedule computed in
  `scripts/75_session_monitor_design.py`.

### P-R9 — The false-flag rate is finally measurable

> Over **101 healthy rig sessions**, the false-flag rate at the operating point
> chosen for P-R8 will be estimable with a relative standard error under 35%.

- **This is a prediction about the measurement, not about the system**, which is
  unusual and deliberate. The false-flag rate is half of what decides whether a
  monitor is worth deploying, and on the archived data it **cannot be estimated
  at all**: restricted to genuinely fault-free episodes there are 17 and 15 of
  them, about 1.4 hours, against a budget of 0.1 per hour.
- **Falsified if:** fewer than about 100 usable healthy sessions are obtained,
  or the estimate's relative standard error exceeds 35%.
- **If confirmed:** this is the first measured false-flag rate for decoder-health
  monitoring with constructed ground truth. That is the contribution that
  outlasts whatever P-R8 returns.
- **Measured by:** the same recordings as P-R8.

### P-R3 — The silence gate fails on the rig too

> More than **10%** of healthy rig episodes will show a significant trend in the
> risk signal — i.e. the rig **fails** the silence gate.

- **Derived from:** claim C03 and `reports/BENCHMARK_SUMMARY.md`. Across 48
  archived configurations, **0** passed the silence gate; the best was 31%
  trending and most sat at 80–100%.
- **Why 10%:** it is the gate's existing threshold, unchanged. No new number is
  introduced.
- **Falsified if:** ≤ 10% of healthy rig episodes trend.
- **If falsified:** that is a *large* result — it would mean a monitor can be
  silent on a real drifting array, and the archived failure is about cortex
  specifically. It would also make the rig the more useful test bed of the two.

### P-R4 — Ladder validity degrades with baseline error, on hardware too

> Spearman ρ between a session's baseline angular error and the fraction of
> session × mode cells in which the three severity levels are correctly ordered
> will be **< −0.4**.

- **Derived from:** limitation L01. Neural values are **−0.677** (T11) and
  **−0.926** (T5) — **the only relationship in this entire project that
  replicates significantly with the same sign on both participants**, which makes
  it the single best candidate for generalising to a third array.
- **Why −0.4:** comfortably weaker than both observed values, so the prediction
  is a real test rather than a restatement. `[[RESEARCHER: accept or change]]`
- **Falsified if:** ρ ≥ −0.4, or the sign reverses.
- **Measured by:** `scripts/53_severity_ladder.py`, unchanged.

### P-R5 — The invariant-feature route fails again

> A one-class detector built on permutation-invariant features will have **lower**
> episode-level detection AUC than `decoder_guard` on the rig.

- **Derived from:** claims C16 and C17. On both participants it was worse:
  0.617/0.680 against 0.672/0.742, with 98.5% of healthy episodes trending.
- **Falsified if:** the invariant detector's AUC exceeds `decoder_guard`'s.
- **Note:** this prediction has already been made twice in this project and was
  **wrong both times in the same direction** — I predicted improvement, and got
  degradation. Here I am predicting degradation. If it improves on hardware, that
  is a genuine and surprising positive, and the third failed prediction in a row.
- **Measured by:** `scripts/63_invariant_detector.py`, unchanged.

### P-R6 — Undesigned faults are harder than designed ones

> Median episode-level detection AUC on the **undesigned** faults (Stage 9: loosened
> connector, thermal drift, EMI, lens contamination, physical rotation, ND filter)
> will be **lower** than on the four **designed** faults, by **≥ 0.03 AUC**.

- **Derived from:** no archived number — there is none, because no undesigned
  fault has ever been observed in this project. That absence is the point.
  `PROJECT_DEFINITION.md` §5.4 names this as the principal remaining risk: *"if
  the monitor only ever meets degradations the researcher wrote, then passing the
  test partly measures the researcher's imagination rather than the monitor's
  generality."*
- **Why ≥ 0.03:** smaller than the 0.05 bar the feature study used, because this
  is a difference between conditions rather than an improvement claim, and the
  designed/undesigned comparison has fewer episodes on the undesigned side.
  `[[RESEARCHER: accept or change]]`
- **Falsified if:** undesigned AUC is equal to or higher than designed AUC.
- **If falsified:** **the most valuable single outcome available in this study.**
  It would mean the monitor's components generalise past the four modes they were
  designed for, which is the direct answer to "your faults are made up."
- **Reporting rule, fixed now:** designed and undesigned results go in
  **separate tables**, never merged. Generalisation from one to the other is a
  testable claim, and merging the tables destroys the only place this study tests
  it.

### P-R7 — Natural drift resembles at least one designed mode

> Over 6–10 weeks with nothing injected (Arm B), the drift's feature-level
> signature will be closest to at least one of the four designed modes at a rate
> **above chance (25%)**, by nearest-mode assignment on the four `decoder_guard`
> component z-scores.

- **Derived from:** no archived number; this is the external-validity question
  `ORIGINAL_DATA_COLLECTION_DESIGN.md` §3 Idea B exists to ask.
- **Falsified if:** natural drift matches no designed mode above chance.
- **If falsified:** **a significant finding about how fault benchmarks are built
  — including this project's own.** It would mean 1,850 episodes of carefully
  constructed ground truth do not resemble what actually goes wrong. That belongs
  in the write-up as a headline, not a limitation.

---

## 3. The go/no-go gate — Stage 6

**No fault may be injected, and no prediction above may be evaluated, until all
five criteria below are met on healthy rig data.** If they cannot be met, the
study stops and reports the rig as a failed analogue (§7).

| # | Criterion | Archived reference | Rig must reach |
|---|---|---|---|
| **G1** | Decoder skill: (measured chance) − (held-out error) | T11: 90.7 − 54.6 = **36.1°** | **25°–47°** |
| **G2** | Held-out angular error | T11: **54.6°** | **45°–65°** |
| **G3** | Channel count | 384 | **exactly** the value chosen in D3 |
| **G4** | Samples per window | 1500 | **exactly 1500** |
| **G5** | Dead channels outside the dark margin | — | **< 5%** |

**Criteria deliberately excluded from this gate, and why.** Lag-1
autocorrelation, effective sample size, detection AUC and silence-gate pass rate
are **not** matching criteria. They are the dependent variables. Requiring the
rig to match them at baseline would guarantee every prediction in §2 and make the
study circular — the same error as choosing a deterioration definition after
seeing which one performs best, which this project refused once already
(`research/deterioration_definition.md`).

**Permitted adjustments to reach G1/G2**, in this order, one variable at a time,
recorded each time: screen brightness, exposure time, analogue gain, slight
defocus. Once the gate passes these are **frozen for the entire study**.

---

## 4. Sample sizes and stopping rules — fixed now

Decided in advance so that "collect until it works" is not available.

| Stage | What | Blocks | Stopping rule |
|---|---|---|---|
| 6 | Healthy baseline | 20 | Fixed count |
| 7 | Designed faults | per injection plan (~200) | The plan, once locked, is followed exactly |
| 8A | Natural autocorrelation | 50, across ≥ 5 separate days, powering down between | Fixed count |
| 8B | Imposed-drift sweep | 8 τ levels × 10 = 80 | Fixed count |
| 9 | Undesigned faults | 6 fault types × 5 repetitions = 30 | Fixed count |
| 10 | SNR and geometry sweeps | ~280 | Fixed grid |
| 11 | Longitudinal | 1/day for 6–10 weeks | Stop at the data cutoff (22 Feb 2027) or 10 weeks, whichever is first |

**≈ 660 blocks ≈ 55 hours of recording**, almost all unattended.

**No interim analysis of Stages 7–10 will be performed before collection for that
stage is complete.** Looking at results and then deciding whether to collect more
is how a stopping rule becomes a free parameter.

---

## 5. Analysis plan — fixed now

- **Every analysis uses the existing scripts unchanged.** 17 (injector), 18
  (decoder), 20 (harness), 21 (scoring), 24 (benchmark matrix), 29 (aggregation),
  53 (severity ladder), 63 (invariant detector), 66 (window spacing). No analysis
  code is written after seeing rig data.
- **Unit of analysis: the episode.** Bootstrap over episodes, 2,000 resamples,
  never over windows. Windows within a block are not independent — that is the
  hypothesis under test, so treating them as independent while testing it would
  be self-contradictory. This project already inflated a sample size 26.6× that
  way and published four p-values as exactly zero, three of which were not real
  (limitation L09).
- **A bootstrap p of 0.0010 is the floor** (2/2000) and will be reported as
  *p < 0.001 at this resolution*, never as zero.
- **Lead time and false-alarm rate are reported as a pair**, never singly.
- **Window-level and episode-level figures are labelled as such**, always.
- **Designed and undesigned faults are reported in separate tables** (P-R6).
- **Splits are by block, never by episode.** The test set is read once.

---

## 6. What this study does **not** test

Stated so that the write-up cannot quietly widen later.

- It does **not** test whether an optical sensor resembles a neuron. The claim
  under test is stated at the level of *multichannel arrays with slow drift*, and
  no claim about biological similarity is made anywhere.
- It does **not** produce closed-loop results. Nothing adapts to the fault; the
  archived study's open-loop limitation carries over.
- It does **not** resolve the archived n = 2 problem. A third array is not a
  third participant, and no cross-participant generality claim is licensed by it.
- It does **not** test the monitor in deployment. There is no user, no task, and
  no consequence to a false alarm.

---

## 7. If the gate fails

If G1–G5 cannot be met in either direction, the study **stops before Stage 7**
and reports: *an optical array could not be tuned to cortical decoding
difficulty; the analogy has a limit and here is where it sits.*

**That is a legitimate result and it will be reported as one**, not buried. It is
strictly better than injecting faults into a system never shown to be comparable
and then reporting a difference nobody can interpret.

---

## 8. Human participants, safety, and rules

**No human participants at any stage, including the researcher.** The camera is
enclosed and points at a screen. No person is measured, recorded, imaged or
surveyed. This preserves Amendment 1 (`PROJECT_DEFINITION.md`, 26 August 2026).
Form 4 is not expected to apply — **to be confirmed with the SRC, not assumed.**

All electronics run from a 5 V USB supply; no mains wiring, no battery beyond a
phone power bank, no heating element. No Form 3 expected — **again, confirm.**

Full safety procedures are in `research/RIG_PROCEDURE.md` §2.

---

## 9. Amendments

If something below must change after freezing, it is amended, never edited:

1. Append to §11 with the date, what changed, and **why**.
2. State whether any rig data had already been collected at that point.
3. Commit separately, with the reason in the commit message.
4. **Never delete or reword the original text.**

This is the same mechanism `FROZEN_DESIGN.json` used for its two amendments and
`PER_MODE_DETECTION_NOTE.md` used for its correction. An amendment that moves a
threshold toward a result must say so in those words.

---

## 10. Freeze procedure

Run this only after D2 and D3 are answered and every threshold has been read and
accepted or changed:

```
cd ~/bci-ews-research
git add research/RIG_PREREGISTRATION.md
git commit -m "Freeze the rig preregistration before building anything"
git push -u origin claude/isef-research-pipeline-9zt4uq
git rev-parse HEAD
```

Paste the hash `git rev-parse HEAD` prints into the **Frozen at commit** field at
the top of this file, then commit once more. The timestamp on that commit is what
makes every "before" in this document checkable rather than asserted.

**After that commit exists, building may begin. Not before.**

---

## 11. Amendment log

*(empty)*

---

## 11. Open item — the C18 derivation behind P-R1 and P-R2

**Raised:** 15 September 2026, before anything was built or measured.

### What happened

While working out the numbers for Procedure 78, a design calculation asked which
imposed drift speed would reproduce cortex's no-overlap autocorrelation of 0.902.
It returned no answer. Chasing that produced two separate findings, both in
`reports/AUTOCORR_BY_SEVERITY.md` and `reports/DRIFT_SWEEP_DESIGN.md`.

**First: 0.902 is not a fault-free number.** `scripts/66_window_spacing.py`
computes it over episodes where the injected fault never crossed threshold, and
calls those "healthy". They are not fault-free — the set also contains episodes
with no fault at all, outnumbered roughly 18 to 1 by episodes carrying a
sub-threshold ramp. Every fault in this project is a monotone ramp, and a ramp
raises lag-1 autocorrelation on its own. Split by what was actually injected, the
no-overlap value runs 0.085 (no fault) → 0.887 (benign ramp) → 0.923 (sub
ramp) on T11, and 0.435 → 0.656 → 0.825 on T5. The ordering is monotone in
injected severity, which is what it would look like if the ramp were supplying
the correlation.

**Second: the estimator saturates.** At the no-overlap spacing an episode keeps
10 windows on T11 and 7 on T5. The sample lag-1 correlation is heavily biased
downward at that length — feed it a series whose true correlation is 0.999 and
at 10 points it reports about 0.60. So every no-overlap figure in this project,
C18's included, understates whatever correlation is really there. That direction
makes the project's negative results look *weaker* than they are, so nothing
already written becomes over-claimed by it.

### What this does and does not change

- **It does not overturn C04's use.** C04 governs how detector performance is
  aggregated, and detector performance is measured on episodes that contain
  faults. Within those episodes the windows really are dependent. Bootstrapping
  over episodes rather than windows remains right.
- **It does change the false-alarm side**, which is a fault-free question, and
  the fault-free rows give more independent samples than the pooled figure
  implies, not fewer.
- **It changes what the rig must be compared against.** Arm B injects nothing.

### The decision to make — `[[RESEARCHER]]`

Three options, and this document should not be frozen until one is chosen and
written into P-R1 and P-R2:

1. **Retarget to the fault-free figures.** Honest, but the fault-free estimate
   rests on 17 episodes (T11) and 15 (T5) with intervals wide enough to cover
   almost anything. A threshold set from them is a threshold set from very
   little.
2. **Keep the pooled figures and restate what P-R1 compares.** Defensible only
   if the rig's comparison arm also carries an injected ramp — which would mean
   comparing the imposed-drift arm, not Arm B, and P-R1's wording has to change
   to say so.
3. **Drop P-R1 and P-R2 from the preregistration** and record the autocorrelation
   as a measurement rather than a prediction, on the grounds that no honest
   threshold can be set from an n of 2 arrays with intervals this wide.

There is no option in which the numbers stay as drafted and the wording stays as
drafted. Whichever is chosen, the reason goes in `research/research_log.md` and
the change is an amendment under §9, dated, with this section left standing.

---

## 12. Amendment 1 — P-R1 and P-R2 retargeted to the fault-free figures

**Decided:** 19 September 2026, by the researcher, before anything was built or
measured.
**Option taken:** §11 option 1, retarget to the fault-free figures.

### What the original predictions said

> **P-R1 (original).** With no imposed drift, the rig's lag-1 autocorrelation of
> the `decoder_guard` risk signal, measured on non-overlapping windows, will be
> **≥ 0.70**. *Derived from claim C18: non-overlapping neural values are 0.902
> (T11) and 0.784 (T5). Chosen as 0.70 because it "sits just below both".*

> **P-R2 (original).** Effective independent samples per rig session,
> `n(1−r)/(1+r)`, will be **< 2** at every window spacing tested. *Derived from
> claim C18: neural values never exceed 0.85.*

### Why they had to change

Both derive from figures computed over episodes where the injected fault never
crossed threshold — a set that `scripts/66` calls "healthy" but which is roughly
18 to 1 sub-threshold fault ramps to genuinely fault-free episodes. Every fault
in this project is a monotone ramp, and a ramp raises lag-1 autocorrelation by
itself. Split by what was actually injected:

| | no fault | benign ramp | sub ramp | pooled (C18) |
|---|---|---|---|---|
| T11 | **0.085** | 0.887 | 0.923 | 0.902 |
| T5 | **0.435** | 0.656 | 0.825 | 0.784 |

The rig's natural-drift arm injects nothing, so the fault-free column is what it
must be compared against. A bar of 0.70 meant to sit "just below both" sits
**above** both. P-R2 was worse: fault-free effective samples are 8.44 and 2.75,
so a bar of "below 2" was pointing the wrong way.

### What the option costs, stated rather than buried

The fault-free estimates rest on **17 episodes on T11 and 15 on T5**, with
intervals wide enough that T11's covers almost the whole plausible range. A
threshold set from them is a threshold set from very little, and P-R1 is
correspondingly weak — it is a sanity bound, not a test.

That cost is why P-R2 was rewritten to test the *mechanism* instead of the
level. The rise from fault-free to faulted is large on both participants
(+0.838 and +0.390), in the same direction, and measured on hundreds of episodes
rather than seventeen. It is the part of this amendment that carries the
evidential weight.

### What did not change

P-R3 through P-R7 are untouched. None of them derives from C18, and §11's
analysis found no problem with any of them.

---

## 13. Amendment 2 — the session-level study replaces the drift sweep

**Decided:** 19 September 2026, before anything was built or measured.

Arm B was designed to ask whether this project's negative result is specific to
cortex or general to any slowly drifting sensor array. Three findings from the
September audit made that the wrong question to spend twenty-two hours of
recording on:

1. **The failure was located.** `reports/OPERATING_POINT_BOUND.md` shows a
   per-hour alarm budget divided among 720 decisions an hour demands a per-window
   AUC of 0.9992. Asked once per session the same detector needs 0.933, and
   reaches 0.673 and 0.742. That is a gap to close, not a wall.
2. **The false-flag rate cannot be measured on archived data at all** — 17 and
   15 fault-free episodes, about 1.4 hours.
3. **The negative result is real without the rig.** The silence gate fails on
   fault-free episodes too, 76.5% and 100% against a 10% bar, so a camera
   failing the same way would confirm something already established.

P-R1 through P-R7 are unchanged and still run; the drift sweep survives as an
optional arm (B-15). What changes is which measurement the recording time is
spent on first, and P-R8 and P-R9 are the predictions for it.

**What this amendment does not do.** It does not relax the 0.1-per-hour budget.
That figure is unchanged. What changes is how many decisions it is divided
among, which is a different quantity that the original design conflated with it.
