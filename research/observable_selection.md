# Choosing the observable — and a constraint the data impose

**Status: DECIDED 26 August 2026 and recorded as amendment 1 to `research/FROZEN_DESIGN.json`**, before any early-warning indicator was computed on the real data. Option A adopted as primary, Option B in parallel, Option D as part of the write-up regardless of outcome.
**Written:** 26 August 2026, after the deterioration definition was frozen, before
any early-warning indicator has been computed on the real data.
**Reproduce:** `python3 scripts/13_select_observable.py`

> The frozen design (`research/FROZEN_DESIGN.json`) deliberately left one thing
> open: *which neural quantity the indicator is computed on*. This document
> reports what the data allow, using **baseline blocks only** (T11 trial days
> 658–675). No trend information was used, because lag-1 autocorrelation is
> itself an early-warning indicator and choosing an observable by its trend
> would be circular.

---

## 1. The trap that had to be avoided first

Critical slowing down is a claim about a **recovery rate**. Measuring it needs an
observable that remembers its recent past. The obvious way to give a noisy signal
memory is to smooth it — and that is exactly wrong.

Starting from **pure white noise, which has no memory at all**:

| Treatment | lag-1 correlation |
|---|---|
| untouched | −0.002 |
| smoothed, 5-sample window | **+0.799** |
| smoothed, 25-sample window | **+0.962** |
| smoothed, 50-sample window | **+0.982** |
| rebinned, 5-sample bins | +0.003 |
| rebinned, 25-sample bins | +0.038 |
| rebinned, 50-sample bins | +0.011 |

Smoothing **manufactures** memory — the correlation belongs to the filter, not the
system. An indicator built on smoothed data measures the smoothing window.
Non-overlapping rebinning cannot do this: rebinned white noise stays white.

Every candidate below therefore uses rebinning, never smoothing.

---

## 2. What the baseline data show

Memory of each candidate, measured on the 8 baseline blocks:

| Observable | Memory (samples) | = seconds | Usable? |
|---|---|---|---|
| **decoder output (cursorVel), 20 ms** | **54.89** | **1.10 s** | see §3 |
| decoder output, rebinned 1 s | 1.35 | 1.34 s | borderline |
| population mean, 20 ms | 0.78 | 0.02 s | no |
| neural PC1, rebinned 5 s | 0.69 | 3.46 s | no |
| population mean, rebinned 1 s | 0.61 | 0.61 s | no |
| population mean, rebinned 5 s | 0.60 | 2.99 s | no |
| neural PC1, rebinned 1 s | 0.56 | 0.56 s | no |
| neural PC1, rebinned 500 ms | 0.44 | 0.22 s | no |
| neural PC1, 20 ms | 0.33 | 0.01 s | no |

**Every purely neural observable is essentially white, at every timescale from
20 ms to 5 s.** Rebinning improves the signal-to-noise ratio, so if slow structure
were present it should have emerged — it did not.

---

## 3. The decoder output does not rescue this

`cursorVel` is the one candidate with real memory (1.10 s). But the paper's
Methods state that the decoded velocity is **exponentially smoothed**:

> *"The raw decoded velocity vₜ was exponentially smoothed with the running
> velocity average X̂ₜ via X̂ₜ = α X̂ₜ₋₁ + (1−α)β vₜ"*

That is precisely the filter shown in §1 to invent memory. If `cursorVel` were an
exponential moving average of a memoryless input, its autocorrelation would decay
exactly as `r₁ᵏ`. Measured against that prediction:

| Lag (bins) | Observed | Pure-filter prediction | Difference |
|---|---|---|---|
| 1 | 0.9817 | 0.9817 | 0.0000 |
| 5 | 0.9179 | 0.9118 | +0.0062 |
| 10 | 0.8268 | 0.8313 | −0.0045 |
| 20 | 0.6438 | 0.6911 | **−0.0473** |
| 40 | 0.4229 | 0.4776 | **−0.0547** |
| 60 | 0.2435 | 0.3301 | **−0.0866** |

The observed decay tracks the filter closely at short lags and falls **faster**
than it at long lags. There is no excess memory beyond the filter — the implied
time constant, 1.08 s, is a smoothing constant, not a neural one.

**Using `cursorVel` as the CSD observable would measure the decoder's smoothing
filter.** It is not an acceptable choice.

---

## 4. What this means for the project

> **The strict critical-slowing-down prediction — rising lag-1 autocorrelation,
> i.e. a slowing recovery rate — cannot be tested within blocks on this dataset.**
> Not because the method is inadequate (it was validated in `scripts/06`–`07`),
> but because no recorded observable has a recovery rate to measure.

This is a real finding and should be reported as one, not worked around.

**What survives.** Critical slowing down predicts **two** signatures, and they
have different requirements:

| Signature | Needs memory in the observable? | Available here |
|---|---|---|
| Rising lag-1 autocorrelation | **Yes** | ✗ |
| **Rising variance** | **No** | **✓** |

Variance is computable on a memoryless signal. The variance of the neural state,
and the trial-to-trial variability within a block, are both measurable and both
are recognised early-warning indicators.

**What the data structure actually is.** Within a block (~5 minutes) the neural
signal has no slow dynamics. The drift that matters happens **across days**. So
this is not the classic CSD setup of a long continuous record with a rolling
window — it is **21 sparse samples of a slowly drifting system**, one per
pre-transition block.

*Caveat on how far this was tested:* bin widths up to 5 s were examined within
blocks of about 5 minutes. Structure slower than that is not resolvable within a
block — there would be too few samples — so this rules out memory at
sub-10-second scales, not at all scales.

---

## 5. Options

None of these is chosen here.

### Option A — variance-based indicators only *(most defensible)*
Compute the variance of the neural state per block and test whether it rises
across the 21 pre-transition blocks. Report explicitly that lag-1 autocorrelation
was **excluded in advance**, with the evidence in §2–3 as the reason.

*Strength:* honest, and the exclusion is itself a reportable methodological
finding. *Cost:* tests one half of the CSD signature rather than both.

### Option B — trial-to-trial variability
Use the spread of neural features **across trials** within a block rather than
across time. Trials are separate events, so this sidesteps the memory problem
entirely.

*Strength:* a classic early-warning indicator; makes use of the trial structure.
*Cost:* a different quantity from the temporal variance in the CSD literature,
and needs its own justification.

### Option C — non-overlapping window distances
Follow MINDFUL, but with **non-overlapping** 60 s windows so no autocorrelation is
manufactured, and treat the resulting distance series as the observable.

*Strength:* directly comparable to the published baseline. *Cost:* a distance from
a reference is not a state variable, so "recovery rate" is not well defined for it.

### Option D — report the constraint as the result
Publish the finding that no observable in this dataset supports an autocorrelation-
based early-warning analysis, alongside variance results.

*Strength:* a genuine methodological contribution — it tells the field something
about what these recordings can and cannot support. *Cost:* a narrower claim than
originally intended.

---

## 6. Recommendation — ADOPTED

**Option A as primary, Option B as a parallel indicator, and Option D as part of
the write-up regardless of what A and B produce.**

The exclusion of lag-1 autocorrelation should be **added to the frozen design
before the analysis runs**, with §2–3 as its justification — so that it is on
record as a decision made in advance, not an omission noticed afterwards.

**Adopted.** Recorded as amendment 1 to the frozen design, which now fixes:

| | |
|---|---|
| Primary indicator | within-block temporal variance (trace of the covariance of the 5-D projected neural series) |
| Parallel indicator | trial-to-trial variance (across trials, of per-trial means) |
| **Excluded in advance** | **lag-1 autocorrelation**, with §2–3 as the reason |
| Null | 5,000-permutation test on block order, two-sided |
| Reported regardless | that no observable here supports an autocorrelation-based analysis |

The null changed from AR(1)-matched surrogates because those suit a long
continuous autocorrelated series; a 21-point block-level series with no temporal
memory calls for permuting the block order instead. That is the same null already
used in the power analysis, so the quoted figures (|τ| ≥ 0.305, power 0.74
against a 2 sd rise) apply unchanged.
