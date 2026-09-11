# Early-warning analysis — results

**Run:** 26 August 2026, against the design frozen at commit `20db485` with 2
amendments, all recorded before any indicator was computed.
**Reproduce:** `python3 scripts/14_run_ews_analysis.py`

> **Headline: the preregistered primary test is statistically significant, and it
> cannot be interpreted as an early warning.** A limitation recorded in advance
> turns out to explain it. The overall result is negative, and it is reported as
> such because the design was fixed beforehand.

---

## 1. What the preregistered tests returned

| Test | n | Kendall τ | p | |
|---|---|---|---|---|
| **Primary** — within-block robust dispersion, pre-transition | 21 | **+0.743** | **0.0002** | significant |
| **Parallel** — trial-to-trial robust dispersion | 21 | **−0.419** | 0.0068 | significant, **opposite sign** |
| Sensitivity — primary, session level | 11 | +0.745 | 0.0012 | significant |
| Sensitivity — parallel, session level | 11 | −0.491 | 0.0408 | significant, opposite sign |

The primary indicator rises steeply and consistently before the transition, at
both block and session level. Taken alone this looks like a clear positive.

**It is not, for the reason in §2.**

---

## 2. The prespecified limitation check that overturns it

Amendment 2 recorded, in advance, that the indicator was **not flat across the
healthy baseline blocks**, and that this must be reported whatever the outcome.
Testing it directly:

| Period | Performance there | n | τ | p |
|---|---|---|---|---|
| **Healthy baseline only** (days 658–675) | 93–100% correct, AE 17.9–24.5° | 8 | **+0.857** | 0.0018 |
| Rest of pre-transition (689–751) | mixed | 13 | +0.667 | 0.0014 |
| All pre-transition *(the preregistered test)* | | 21 | +0.743 | 0.0002 |

Indicator values across the healthy baseline: **23.6, 21.7, 28.2, 27.6, 36.7,
36.8, 43.3, 50.4** — more than doubling across eight blocks in which the
participant was performing at 93–100% correct.

> **The trend is *steeper* inside the healthy baseline than it is overall.** An
> indicator that rises just as fast during stable, excellent performance is not
> detecting an approach to deterioration. It is tracking something that drifts
> monotonically regardless of performance — most plausibly the recording itself
> (electrode drift, impedance change, gain drift) rather than the state of the
> coupled human–decoder system.

This is precisely the failure mode the synthetic **negative control** was built
to catch: monotonic drift with no bifurcation. On synthetic data the detector
correctly stayed silent, because indicators there were computed on a *de-trended*
series. The frozen design did not specify de-trending of the block-level
indicator series — **an omission in the preregistration, not a property of the
data.** See §5.

---

## 3. The two participants disagree in sign

| | T5 baseline | T5 degraded | T5 recovered |
|---|---|---|---|
| primary indicator | 7.81 → 10.67 (rising) | **7.49** | 7.91 |

In T5 the indicator **falls** during the degradation, to below its baseline
range, and the baseline itself rises monotonically (7.81, 8.11, 7.53, 7.95, 8.46,
9.94, 10.38, 10.60, 10.67) while performance is 95–99% correct.

**The T5 reversibility test passes its prespecified criterion vacuously.** The
criterion was "the indicator at recovery returns to within the baseline range" —
7.91 does. But the indicator never rose during the degradation in the first
place, so the criterion is satisfied without the test having demonstrated
anything. Recorded as a pass, interpreted as uninformative.

The T11 internal excursion test (day 727 → 751) is a genuine pass: baseline range
21.74–50.40, degraded 56.78 (above the range), recovered 48.73 (back inside it).
But given §2, that too is consistent with monotonic drift plus noise.

---

## 4. Secondary outcome — neural vs behavioural detection time

| | |
|---|---|
| Settings evaluated | 23 of 24 |
| Neural detects first | 13 |
| Behaviour detects first | 8 |
| Tied | 2 |
| Median lead | **+7.0 days** (range −74 to +43) |

The preregistration required a **"clear majority"** for the conclusion that
neural monitoring detects earlier. 13 of 23 is 57%, and the spread runs from 74
days behind to 43 days ahead. **This does not meet the prespecified bar and is
reported as equivocal**, not as a positive.

*Note on a specification slip:* the analysis code implemented "clear majority" as
simply >50%, and on that reading printed "neural monitoring detects earlier". The
document's wording is the binding one. The result is equivocal.

---

## 5. Conclusion

**Negative.** The evidence does not support the claim that these early-warning
indicators detect impending deterioration in this dataset:

1. The primary indicator's significant rise is **not specific to the approach to
   deterioration** — it rises at least as steeply during healthy baseline.
2. The parallel indicator moves in the **opposite direction**, significantly.
3. The two participants **disagree in sign**: the indicator rises in T11 and
   falls during T5's degradation.
4. The secondary lead-time comparison is **equivocal** against its own bar.
5. The one clean reversibility pass (T11 727→751) is equally consistent with
   monotonic drift.

Combined with the earlier finding that **no observable in this dataset has a
measurable recovery rate**, so the autocorrelation half of critical slowing down
could not be tested at all, the overall answer is that **this dataset does not
support a classic critical-slowing-down early-warning analysis.**

### What was learned, and what a corrected study would need

- **A design flaw, stated plainly.** The frozen design did not require the
  block-level indicator series to be de-trended before testing its trend. The
  synthetic controls (`scripts/06`) established that de-trending is necessary,
  and its omission here is exactly why a monotonic recording drift produced a
  significant result. **This is not corrected retrospectively** — doing so after
  seeing the outcome would destroy the preregistration. It defines the next study.
- **The baseline period is not a stable reference** in either participant, which
  undermines any indicator anchored to it.
- **A future preregistration should** de-trend the indicator series before the
  trend test, and should include a *within-baseline* negative control as a
  prespecified gate — i.e. require the indicator to show no significant trend
  during healthy performance before its pre-transition trend is interpreted.

That last point is the most transferable lesson: **a real early-warning
indicator must be silent when the system is healthy.** Testing that should be a
precondition, not a post-hoc check.

---

## 6. What makes this result reportable

The design was frozen before any indicator was computed, with data hashes and a
git commit. Both amendments predate the analysis and are timestamped. The
limitation that overturned the headline was recorded *in advance*, not discovered
afterwards. No test was repeated with different settings, and the losing
interpretations were written down before the result was known.

A negative result obtained this way is informative. The same numbers obtained
without a preregistration would not have been.
