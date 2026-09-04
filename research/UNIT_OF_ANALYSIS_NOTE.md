# Sweeping for statistics built on pooled windows — preregistered

**Written before running.**

## The error class, found by accident

`reports/PER_MODE_DETECTION.md` established that claim C02's headline is a
**window-level** AUC — every window from every episode concatenated and compared
individually. Claim C04 says windows within a session are not independent
(lag-1 r = 0.995), so pooling them inflates the apparent sample size by roughly
55× per session.

An AUC **point estimate** survives that: it is a descriptive statistic and does
not assume independence. An **inferential** statistic does not. And
`reports/ACHIEVABILITY.md` carries a column of them:

| detector | AUC | p as published |
|---|---|---|
| `decoder_guard`, recent-normal | 0.693 | **0** |
| `distribution_shift`, recent-normal | 0.666 | 1.2e-303 |
| `mean_activity`, recent-normal | 0.611 | 2e-137 |
| `decoder_guard`, **calibrate-once** | **0.491** | **0.046** |

The last row is the reductio. An AUC of 0.491 is chance to three decimals — the
table's own verdict column says *"at chance — no information"* — yet it carries a
nominally significant p-value, because n is enormous. A p of exactly `0` in the
first row is the same tell.

I found one instance of this by accident while decomposing the headline. That is
not a reason to fix one instance; it is a reason to sweep.

## What this study does

1. **Audit.** Classify every statistic in the registered claim set by its unit of
   analysis — window, episode, session, bin — and flag those pooling
   non-independent units.
2. **Recompute.** For each flagged *inferential* statistic, recompute it with the
   **episode** as the unit, by bootstrap over episodes, which is the standard this
   project already adopted elsewhere.
3. **Correct in place.** Any published p-value that does not survive is corrected
   inline in its report, not deleted.

## Predictions, committed

1. **The AUC point estimates barely move** — under 0.05 — because pooling affects
   the variance, not the location.
2. **The p-values become vastly less extreme.** Specifically, `p = 0` and
   `1.2e-303` should become ordinary numbers.
3. **At least one currently "significant" result becomes non-significant**, and
   the calibrate-once `decoder_guard` row (AUC 0.491, p = 0.046) is my candidate.

If the p-values survive roughly intact, then the effective sample size is larger
than lag-1 r = 0.995 suggests and the aggregation-limit analysis needs revisiting
instead.

## Fixed in advance

| | |
|---|---|
| Unit | the **episode** — one median score per episode, as every session-level analysis here uses |
| Interval | bootstrap over episodes, 2000 resamples, seed 20260902 |
| p-value | two-sided, from the bootstrap distribution of AUC − 0.5 |
| Reported | every flagged statistic, both participants, both baselines, whatever it shows |
| Not permitted | dropping a statistic because its corrected p is inconvenient |

## What this cannot change

The project's conclusions do not rest on these p-values. "0 of 48 configurations
pass the gates" is a count; the operating-point bound is arithmetic; the
aggregation limit is itself the reason this correction is needed. What is at stake
is whether the *supporting* statistics are stated honestly — which is worth a
study on its own.
