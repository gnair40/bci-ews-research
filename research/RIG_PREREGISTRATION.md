# Preregistration — the physical rig study

**Drafted:** 7 September 2026.
**Status: DRAFT — NOT YET FROZEN. Nothing has been built and nothing measured.**
**Frozen at commit:** `[[RESEARCHER — fill in after running the freeze in §10]]`

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
single number: a recording session contains roughly one independent measurement,
because the risk signal's lag-1 autocorrelation is 0.902–0.995 depending on
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

### P-R1 — Serial correlation is a property of drifting arrays, not of cortex

> With **no imposed drift**, the rig's lag-1 autocorrelation of the
> `decoder_guard` risk signal, measured on **non-overlapping** windows, will be
> **≥ 0.70**.

- **Derived from:** claim C18. Non-overlapping neural values are **0.902** (T11)
  and **0.784** (T5); `reports/WINDOW_SPACING.md`.
- **Why 0.70 and not 0.784:** 0.784 is the lower of two arrays, and a bar set at
  the minimum of an n = 2 sample is not a bar, it is a coin toss. 0.70 sits just
  below both, so the prediction fails only if the rig is clearly less
  autocorrelated than either real array. `[[RESEARCHER: accept or change]]`
- **Falsified if:** median non-overlap r < 0.70.
- **If confirmed:** the negative result generalises beyond cortex, to
  sensor-array health monitoring in general. This is the stronger outcome.
- **If falsified:** the failure is neural-specific, and the next BCI attempt
  needs neural-specific fixes rather than better statistics.
- **Measured by:** `scripts/66_window_spacing.py`, unchanged, at the every-6th
  spacing.

### P-R2 — Aggregation cannot rescue the rig either

> Effective independent samples per rig session, `n(1−r)/(1+r)`, will be **< 2**
> at **every** window spacing tested.

- **Derived from:** claim C18. Neural values never exceed **0.85**.
- **Honest caveat, stated rather than hidden:** *P-R2 is not independent of
  P-R1.* Effective sample size is a function of r and n, so a rig that satisfies
  P-R1 will very probably satisfy P-R2 automatically. It is listed separately
  because it is the quantity the project's conclusions actually rest on, **not
  because it is a second piece of evidence.** Two predictions that are one
  prediction wearing two hats would inflate apparent support, which is precisely
  the error class already logged as L09.
- **Falsified if:** n_eff ≥ 2 at any spacing.

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
