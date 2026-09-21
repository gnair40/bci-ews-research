# The mode the monitor never identifies is the easiest one to identify

**Preregistered:** `research/MODE_SEPARABILITY_NOTE.md`, including the prediction
**Script:** `58_mode_separability.py`
**Status: EXPLORATORY** — an information probe using fault labels a deployed
monitor never has. No number here is monitor performance.

## Why it was run

Attribution names `GEOMETRY_ROTATION` correctly **0%** of the time on both arrays.
Two very different explanations were live: the guard's four components throw the
information away, or the modes genuinely leave indistinguishable traces. Those
imply opposite conclusions — a fixable design problem, or a capability that should
be dropped rather than improved.

## The answer

**Rotation is the most separable fault mode there is.**

| pair | T11 AUC | T5 AUC |
|---|---|---|
| GEOMETRY_ROTATION vs RATE_LOSS | **0.977** | **0.999** |
| **GAIN_DRIFT vs GEOMETRY_ROTATION** | **0.920** | **0.998** |
| CHANNEL_DROPOUT vs GEOMETRY_ROTATION | **0.857** | **1.000** |
| GAIN_DRIFT vs RATE_LOSS | 0.777 | 0.586 |
| CHANNEL_DROPOUT vs GAIN_DRIFT | 0.598 | 0.624 |
| CHANNEL_DROPOUT vs RATE_LOSS | 0.574 | 0.657 |

Every pair involving rotation is at the top of the table on both participants.
Every pair not involving it is near the bottom.

The preregistered prediction — GAIN_DRIFT vs GEOMETRY_ROTATION above 0.8 — is met
at **0.920** and **0.998**, with the mechanism that was stated in advance: gain
drift scales each channel independently, giving a random per-channel pattern;
rotation exchanges activity between specific pairs, giving a structured one. A
signed per-channel vector sees that. The `dispersion` component, which discards
both the signs and the pairing, cannot.

## So the attribution failure is a design problem, definitively

**The mode the monitor gets wrong 100% of the time is the mode most easily
identified from the very features the monitor is looking at.** The information is
not merely present, it is the strongest signal in the set, and four scalar
components summarise it away.

This resolves the open question from `reports/ATTRIBUTION_ACCURACY.md`: attribution
is fixable in principle, and `GEOMETRY_ROTATION → profile` failed because
`dispersion` and norm-preserving rotation are the same signature *as those
components are defined*, not because rotation is invisible.

## The other half of the table is the real ceiling

> ### ⚠️ Correction, 4 September 2026 — this section is withdrawn
>
> **The conclusion below is wrong.** It attributes the confusability of
> `CHANNEL_DROPOUT`, `GAIN_DRIFT` and `RATE_LOSS` to the features. It is the
> **model** that could not separate them: this probe fitted a *linear
> discriminant*, which searches for one fixed direction, while the channels each
> fault touches are drawn at random per episode — so no fixed direction exists to
> find.
>
> With twelve **permutation-invariant** summaries of the same per-channel vector,
> the confusable trio's mean AUC rises from **0.650 to 0.987** on T11 and from
> 0.623 to 0.998 on T5. A control using 12 *random raw channels* reaches only
> 0.702, so the gain is the representation, not the smaller dimension count.
>
> The corrected reading: **all four modes are separable in principle, and the
> guard's four scalar components are the entire limitation.** See
> `reports/PERMUTATION_INVARIANT.md`. Claim E05 is withdrawn.

`CHANNEL_DROPOUT`, `GAIN_DRIFT` and `RATE_LOSS` separate from one another at
0.57–0.78 — barely above chance for two of the three pairs, on both participants.
That is not a component-design problem. Those three faults genuinely leave similar
traces in per-channel activity, which they should: each of them reduces or rescales
what channels report, differing mainly in *which* channels and *how much*.

So the guard's 56% attribution accuracy is **not** all mechanism failure. There is
a real information ceiling for three of the four modes, and no attribution scheme
built on these features will separate them cleanly. The honest split is:

- **rotation** — the guard's fault, fixable
- **dropout / gain / rate** — the features' fault, not fixable this way

## Limitations

- **An upper bound, and a supervised one.** It fits a discriminant per pair using
  the injected labels. A monitor has no labels, so it could not achieve these
  numbers even with perfect components.
- **T5 has only 3 sessions** after filtering to the test split, so leave-one-out
  there trains on two sessions. Its near-1.0 values should be read as "clearly
  separable", not as precise. T11's 12 sessions carry the result.
- λ was fixed at 0.1·trace/p in advance and not tuned; a tuned value would give
  a higher and less honest number.
- 384 features against ~400 episodes. The regularisation is doing real work, and
  leave-one-session-out is what keeps that from becoming leakage.
