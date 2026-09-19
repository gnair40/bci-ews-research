# Label-free attribution on invariant features — preregistered

**Written before the rule is built or run.** The mode→feature mapping is fixed
below and is not adjustable afterwards.

## Why this has to be tested

`reports/PERMUTATION_INVARIANT.md` recommended building **attribution** on
permutation-invariant distributional summaries. That recommendation rests
entirely on a **supervised** probe — one that fitted a discriminant per pair of
faults using the injected labels.

Yesterday I took the analogous step for **detection**: built it unsupervised, with
criteria fixed in advance, and it failed badly on both axes
(`reports/INVARIANT_DETECTOR.md`). A supervised probe showing information exists
did **not** mean an unsupervised rule could use it.

The surviving half of that recommendation is exposed to exactly the same risk and
is currently untested. Leaving it standing, immediately after demonstrating the
pattern, would be inconsistent.

## What "label-free" means here, precisely

The rule uses **no episode labels at run time**: nothing is fitted to which fault
occurred. Calibration is from each episode's own clean prefix, as everywhere.

It does use knowledge of **how the faults are injected** to assign each mode a
feature, below. That is the same standing as `EXPECTED_ATTRIBUTION` in
`22_decoder_guard.py`, which is what makes this a fair comparison to the guard's
current 56%. It is *not* the standing of a monitor facing an unknown fault, and
that limit is stated rather than glossed.

## The mapping, committed now

Each fault mode is assigned the one invariant summary its injection mechanism
should move most. Derived from the injector's own construction, not from any
result.

| fault | assigned feature | mechanism |
|---|---|---|
| `CHANNEL_DROPOUT` | **`frac_severely_down`** | silences a random subset — most channels untouched, a few driven far down. Nothing else produces that. |
| `RATE_LOSS` | **`mean`** | scales every channel down together, so the whole distribution shifts. |
| `GAIN_DRIFT` | **`sd`** | independent per-channel gains, centred so the mean is preserved by construction — spread with no shift. |
| `GEOMETRY_ROTATION` | **`skew`** | channels exchange activity. In log space a channel losing most of its activity falls far, while the receiving channel rises less — an asymmetric, negatively skewed spread. |

**Stated uncertainty, in advance:** the rotation assignment is the one I am least
sure of. `kurtosis` is the plausible alternative — exchange produces heavy tails
as well as asymmetry. I am committing to `skew` on the mechanism above. If
rotation fails and `kurtosis` would have succeeded, that is a **wrong prediction**,
recorded as such, and not a licence to swap the mapping.

## The rule

For each window, the four assigned features are calibrated to robust z-scores
against the episode's own clean prefix, exactly as `DecoderGuard` calibrates its
components. The attributed cause is the mode whose assigned feature has the
largest calibrated |z|, taken as a majority vote across the early-warning window.

No specificity ordering. The guard needs one because a generic residual component
swamps specific ones; here all four features are equally specific by construction,
so adding an ordering would be an untested extra mechanism.

## Success criteria, fixed in advance

| | Criterion | Current |
|---|---|---|
| **Overall** | accuracy must exceed the current value on **both** participants | 56.3% (T11), 52.5% (T5) |
| **Rotation** | must exceed chance on **both** | **0%** on both |

Chance is 25% over four modes. Beating one participant only is not a success.

## Prediction, committed

1. **Overall accuracy improves to 0.70–0.85 on both participants.**
2. **`GEOMETRY_ROTATION` rises above 0.50 on both**, from its current 0%.

Tempered deliberately by yesterday's result: a supervised probe showing 0.93–1.00
separability does not entitle me to expect near-perfect label-free attribution.
The rule is cruder than a fitted discriminant and has to work per window.

## What follows

**Both criteria met** → the surviving recommendation is confirmed under the
harder, label-free condition, and the attribution failure is not just diagnosed
but fixed.

**Not met** → the recommendation is corrected to say what the evidence actually
supports: that the information is present, *not* that a simple label-free rule can
reach it. Same correction the detection half already received.

One candidate. No tuned variant follows a failure.
