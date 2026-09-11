# Closing an open item: what window-overlap contamination actually cost

**Prediction committed in advance:** `research/WINDOW_OVERLAP_NOTE.md`
**Script:** `54_window_overlap.py`

## The defect

Windows are 1500 bins (30 s) long, stepped every 250 bins (5 s). Local
re-baselining took an episode's "pre-onset" windows as `F[:ow]`, where `ow` is
the first window whose *start* falls at or after fault onset. But a window that
starts before onset still extends 1500 bins past its start — so any window with
`start + 1500 > onset_bin` **contains faulted data while being counted as
healthy**.

Measured: **5.99 contaminated windows per episode on T11, 6.00 on T5** — exactly
the 1500 / 250 = 6 the geometry predicts.

This was found during the benchmark work, recorded as a limitation on the grounds
that the bias is *conservative*, and never measured. It was one of two open items
left explicitly unresolved.

## The prediction, and how it scored

| Predicted | Outcome |
|---|---|
| Removing the contaminated windows **raises** AUC | ✓ on both participants |
| Effect is small | ✓ though larger than the "few thousandths" I guessed |
| ~6 contaminated windows per episode | ✓ 5.99 and 6.00 |

## What it cost

| | T11 | T5 |
|---|---|---|
| Days measured | 13 | 6 |
| Mean AUC gain from the strict reference | **+0.0072** | **+0.0123** |
| Median gain | +0.0037 | +0.0096 |
| Largest single-day gain | +0.0316 | +0.0310 |
| Days improved / worsened / tied | 7 / 2 / 4 | 4 / 0 / 2 |

Six of nineteen days tie *exactly*, which is why the per-participant Wilcoxon
tests are weak (p = 0.13 and 0.125) — most of their power goes to ties. The
direction was committed before running, so the appropriate test is a **one-sided
sign test across both arrays**:

> **11 of 13 non-tied days improved. p = 0.011.**

## What this means for every earlier number

**The bias was conservative, as argued — and now it is measured rather than
asserted.** Every AUC reported in this project understates the monitor's
performance by roughly **0.7 % to 1.2 %**, with a worst case of about 3 %.

That is small enough that no conclusion changes. In particular it does not
approach the gap between the 0.65–0.74 achieved and the ~0.99 the false-alarm
budget requires, so the headline negative result stands untouched. But
"conservative" is no longer an argument in this repository; it is a number.

## Why the earlier results were not recomputed

Fixing this would shift every AUC in the project up by under 0.01 and change no
conclusion, at the cost of invalidating the frozen records that every
preregistration points at. The frozen numbers are the ones that were committed to
in advance, and replacing them for a sub-1% correction would trade a real
methodological guarantee for a cosmetic one.

The correction factor is documented here and in the README instead. A future
benchmark run should use the strict reference from the start —
`start + WINDOW_BINS <= onset_bin` — and `54_window_overlap.py` implements it.

## Limitations

- 19 sessions across two participants, using the same 40-episodes-per-day
  subsample as the other session-level analyses.
- The paired design excludes episodes without at least 3 strictly-clean windows
  from **both** arms, so the comparison is honest but drops short episodes near
  the start of a block.
- The correction is measured on `decoder_guard` only. The other detectors use the
  same re-baselining and should be affected similarly, but that is an expectation,
  not a measurement.
