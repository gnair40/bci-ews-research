# Phases 1 and 2 — complete

**Project:** Anticipatory signatures of decoder failure in chronic intracortical BCIs
**Dataset:** Pun et al. (2024), *Communications Biology*. Dryad `doi:10.5061/dryad.n2z34tn5s`, version 6, **CC0-1.0**
**Status:** Phases 1 and 2 closed. Phase 3 not started.

> **Purpose of these phases.** To find out what this dataset can and cannot
> support, before committing to a full study. That is what they did. The answer
> is more useful than a positive result would have been.

---

## 1. The dataset

| | T11 | T5 |
|---|---|---|
| Sessions | 15 | 6 |
| Blocks | 29 | 21 |
| Trials | 1,839 | 1,200 |
| Neural features | 384 | 192 (no spike power) |
| Trial days | 658–800 (**142 days**) | 2121–2149 (**28 days**) |

Plus two extra T11 sessions on different tasks. 3,301 trials, 782,708 bins at
20 ms, 4.35 hours total. Downloaded programmatically with SHA-256 verification;
provenance in `data/raw/download_manifest.json`.

**Correction to the literature review:** it has the participants reversed. T11 is
the longitudinal one.

---

## 2. What was verified

| Claim | How | Result |
|---|---|---|
| The decoder is fixed | Paper's Methods **and** independently from the data | ✅ Confirmed twice |
| Performance genuinely degrades | Two independent measures | ✅ T11 steps at day 758; T5 dips and recovers |
| Task type is not a confound | Task name by session | ✅ One task per participant throughout |
| The pipeline is correct | Reproduced the published Fig. 1b | ✅ **r = 0.985 vs published 0.985** |
| The detector works | Synthetic positive/negative controls | ✅ Fires on bifurcation, silent on drift |
| The detector has adequate power | Power scaling with record length | ✅ 0.25 → 1.00 as records lengthen |

---

## 3. A discovery that supports the project's central framing

The abstract says "fixed decoders". The Methods say more: the weights are frozen,
but an **adaptive normalisation layer runs continuously** — a 3-minute rolling
z-score for T11, and for T5 a bias correction at adaptation rate 0.3 that updates
the decoder's intercept online.

The literature review's framing (C) — *"a monotonically degrading plant plus a
saturating compensator"* — was labelled speculation with no supporting paper. The
Methods describe exactly that architecture, with parameters attached. **The
compensator is real.**

It also carries a cost the write-up must state: those corrections remove slow
mean drift *before recording*, so the authors note that "performance drops
observed in this dataset were largely due to other types of model drift."

---

## 4. The preregistered analysis

Design frozen at commit `20db485` with data hashes and two timestamped
amendments, all before any indicator existed.

| Test | n | τ | p | |
|---|---|---|---|---|
| Primary — robust dispersion, pre-transition | 21 | +0.743 | 0.0002 | significant |
| Parallel — trial-to-trial dispersion | 21 | −0.419 | 0.0068 | significant, **opposite sign** |
| Sensitivity — session level | 11 | +0.745 | 0.0012 | significant |

**And the prespecified limitation check that overturns it:**

| Period | Performance there | τ | p |
|---|---|---|---|
| **Healthy baseline only** | 93–100% correct | **+0.857** | 0.0018 |
| All pre-transition *(the test)* | | +0.743 | 0.0002 |

The indicator rises *more steeply during healthy performance* than it does
overall. See `reports/figures/11_t11_why_negative.png`.

---

## 5. What the indicator actually measures

Three independent lines of evidence converge:

**Firing rate.** Falls **56.5%** across T11's record. A linear fit of the
indicator on it gives **R² = 0.707**. Controlling for firing rate, the
indicator's link to performance becomes non-significant (ρ 0.858 → 0.260, p =
0.17). Controlling for elapsed time, essentially nothing remains. And mean firing
rate predicts performance (ρ = −0.880) **as well as the full pipeline does**.

**Task invariance.** On the extra T11 sessions using completely different tasks —
including free web browsing — the indicator differs from the same-day cursor-task
value by only **5.9–8.4%**, against a **threefold range** across the record.

**Participant disagreement.** In T5 the indicator *falls* during degradation, so
its reversibility test passes vacuously.

> **Conclusion: the indicator tracks the state of the recording, not the state of
> the coupled human–decoder system.** In this dataset, "neural instability" and
> "the electrodes are wearing out" are not separable by scale-based measures.

---

## 6. Constraints established, and why they matter

| Finding | Consequence |
|---|---|
| No observable has measurable memory (0.3–0.7 samples, 20 ms–5 s) | The **autocorrelation half of critical slowing down cannot be tested** here |
| The decoder output's memory is its own smoothing filter | It cannot serve as the observable |
| Smoothing raises white-noise lag-1 correlation to +0.962 | Never smooth to create memory; rebin instead |
| Rolling z-scoring fixes block variance at ≈1 | Incompatible with scale-based indicators |
| Raw variance swings ~100× between healthy blocks | Robust estimators are required |
| T5 has 3 pre-transition sessions | **No test at α = 0.05 exists** at n = 3 |
| Block level gives 21 observations vs 11 | Detects \|τ\| ≥ 0.305 rather than ≥ 0.455 |

---

## 7. The design flaw, stated plainly

The frozen design **did not require the block-level indicator series to be
de-trended** before testing its trend. The synthetic controls had already
established that de-trending is necessary — that is why the detector correctly
stayed silent on monotonic drift in simulation. Its omission is why recording
drift produced p = 0.0002.

**This was not corrected retrospectively.** Doing so after seeing the outcome
would destroy the preregistration. It defines Phase 3.

---

## 8. What Phase 3 must do

1. **De-trend** the block-level indicator series before testing its trend.
2. **A within-baseline silence gate, prespecified.** Require no significant trend
   during healthy performance before the pre-transition trend may be interpreted
   at all. *A real early-warning indicator must be silent when the system is
   healthy.*
3. **Demonstrate invariance to mean firing rate** on the baseline — don't assert it.
4. **Beat mean firing rate**, not only MINDFUL.
5. **Control for elapsed time.**

Candidates not yet attempted, all requiring preregistration: the residual after
removing firing rate (which is what framing (C) actually predicts), covariance
*geometry* rather than scale, and **flickering** — visible in T11 as day 727
degraded → day 751 fully recovered → day 758 collapsed.

**And one possibility to hold open:** this dataset may not be able to answer the
question, because the array's signal decline is large enough and entangled enough
with performance that no measure separates the two. Establishing that with honest
gates would itself be a publishable methodological result.

---

## 9. Why this counts as a result

The design was frozen before any indicator was computed, with data hashes and a
git commit. Both amendments predate the analysis. The limitation that overturned
the headline was recorded *in advance*. No test was repeated with different
settings. A specification slip in the code — implementing "clear majority" as
merely >50% — was reported rather than quietly resolved in the favourable
direction.

A negative result obtained this way is informative. The same numbers without a
preregistration would not have been.

---

## 10. Repository

**16 scripts** (download → inspect → load → explore → verify → controls → power →
record length → reproduce baseline → design power → define deterioration → freeze
→ select observable → analyse → diagnose → synthesise), **11 figures**, the frozen
design with both amendments, and dated logs throughout.

| Document | Contents |
|---|---|
| `DATASET_README.md` | Provenance, structure, variable dictionary; all open questions now closed |
| `reports/DATASET_EXPLORATION.md` | Descriptive characterisation, all sections complete |
| `reports/EWS_RESULTS.md` | The preregistered result and why it is negative |
| `research/deterioration_definition.md` | Six methods compared; the frozen definition |
| `research/design_decisions.md` | Analysis level, power, sample sizes |
| `research/observable_selection.md` | Why autocorrelation was excluded |
| `research/phase3_design_implications.md` | What the next study must do |
| `research/procedures.md` | 40 numbered procedures, methods-section ready |
| `research/FROZEN_DESIGN.json` | The preregistration, with hashes and amendments |
