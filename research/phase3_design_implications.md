# What Phase 1–2 established, and what Phase 3 must do differently

**Status:** Exploratory characterisation, run after the confirmatory analysis was
completed and reported. Nothing here revises `reports/EWS_RESULTS.md`.
**Reproduce:** `python3 scripts/15_diagnose_drift.py`

> The purpose of this phase was to understand how this dataset behaves before
> committing to a full study. It did that, and the answer is more useful than a
> positive result would have been.

---

## 1. The single most important number

**Mean firing rate falls 56.5% across T11's record** — from 26.5 to 11.5.

That is not a subtle drift. Over 142 days, more than half the recorded neural
activity disappears. Everything else follows from it.

---

## 2. The indicator adds nothing beyond firing rate

| Comparison | Spearman ρ | p |
|---|---|---|
| indicator vs angle error, raw | **+0.858** | <0.0001 |
| … controlling for mean firing rate | **+0.260** | 0.17 (n.s.) |
| … controlling for elapsed time | **+0.105** | 0.59 (n.s.) |
| **mean firing rate vs angle error** | **−0.880** | <0.0001 |

- A linear fit of the indicator on mean firing rate gives **R² = 0.707**. Seventy
  percent of the indicator *is* firing rate.
- Once firing rate is controlled for, the indicator's relationship to performance
  **is no longer significant**.
- Once elapsed time is controlled for, essentially nothing remains.

> **And the sting: mean firing rate predicts performance (ρ = −0.880) at least as
> well as the entire dispersion pipeline does (ρ = +0.858).** A one-line
> calculation matches a five-dimensional projection with robust statistics.

Any future indicator has to beat that, and "beating MINDFUL" is not the only bar
— **mean firing rate is a simple, strong comparator that must be beaten too.**

---

## 3. But the diagnosis is only partial — stated honestly

Firing rate does **not** explain the within-baseline rise that overturned the
headline result:

| Period | firing-rate trend | indicator trend |
|---|---|---|
| Healthy baseline (658–675) | τ = −0.286, p = 0.40 **(n.s.)** | τ = **+0.857**, p = 0.0018 |
| All pre-transition | τ = −0.524, p = 0.0006 | τ = +0.743, p = 0.0002 |

Across the healthy baseline the indicator climbs steeply while firing rate barely
moves. **Something else drives that rise and it has not been identified.**
Candidate recording properties tested and rejected: `avgOutliers` (ρ = −0.23),
silent channels (ρ = +0.29), low-variance channels (ρ = +0.31).

This matters: it means the confound is not fully characterised, and a design that
only regresses out firing rate would still be exposed.

---

## 4. What this phase established

| Finding | Consequence |
|---|---|
| No observable has a measurable recovery rate (0.3–0.7 samples of memory, 20 ms–5 s) | The autocorrelation half of critical slowing down **cannot be tested** on this data |
| The decoder output's apparent memory is its own exponential smoothing filter | It cannot serve as the observable |
| Raw variance swings ~100× between healthy blocks | Scale-based indicators need robust estimators |
| Rolling z-scoring fixes block variance at ≈1 | It is incompatible with a variance indicator |
| The indicator rises during healthy baseline | Trend alone is not evidence of approach to a transition |
| Mean firing rate falls 56.5% and explains 71% of the indicator | Signal decline and "neural instability" are **not separable** by this measure |
| Mean firing rate predicts performance as well as the indicator | A trivial comparator matches the sophisticated one |

---

## 5. What Phase 3 must do differently

### Five requirements, all testable before any outcome is computed

1. **De-trend the block-level indicator series** before testing its trend. The
   synthetic controls established this is necessary; the frozen design omitted it,
   and that omission is why monotonic drift produced p = 0.0002.

2. **A within-baseline silence gate, prespecified.** Require the indicator to show
   **no significant trend during healthy performance** before its pre-transition
   trend may be interpreted at all. This is the single most transferable lesson:
   *a real early-warning indicator must be silent when the system is healthy.*
   Had this been a gate rather than a footnote, the headline would never have been
   reported as positive.

3. **Demonstrate invariance to mean firing rate.** Either regress it out before
   testing, or construct an indicator that is invariant to overall rate by design
   — and demonstrate that invariance on the baseline, not assert it.

4. **Add mean firing rate as a comparator.** The claim to beat is no longer only
   MINDFUL. It is also "does this do better than counting spikes?"

5. **Control for elapsed time.** Nothing in this dataset survived controlling for
   time. Any future claim must show it does.

### And one honest possibility to hold open

It may be that **this dataset cannot answer the early-warning question**, because
the array's signal decline is so large (−56.5%) and so entangled with performance
that no measure can separate "the system is approaching a transition" from "the
electrodes are failing".

If Phase 3's gates are applied honestly and nothing passes them, that is a
publishable methodological result: *long-term iBCI recordings with substantial
signal decline may not support critical-slowing-down analysis, and here is the
evidence and the set of tests that establish it.*

That is a real contribution, and it is available regardless of which way the
numbers fall.

---

## 6. Where a positive result could still come from

Not exhausted by this phase:

- **The residual after regressing out firing rate**, which is what the literature
  review's framing (C) actually predicts — the widening gap between neural
  degradation and behavioural compensation, not either series alone.
- **T5 as a genuine second case**, with an indicator that does track its
  degradation (this one did not — it fell).
- **Higher-order structure**: the covariance geometry rather than its overall
  scale, which is closer to what MINDFUL measures and is less rate-dependent.
- **Flickering**, which is visible in T11 (day 727 degraded, 751 fully recovered,
  758 collapsed) and is a recognised early-warning phenomenon distinct from both
  variance and autocorrelation. It would have to be preregistered in advance.
