# The other half of the recommendation fails too

**Preregistered:** `research/INVARIANT_ATTRIBUTION_NOTE.md` — mapping, rule,
criteria and prediction all committed before the code existed
**Script:** `64_invariant_attribution.py`

## Why it was tested

`reports/PERMUTATION_INVARIANT.md` recommended invariant summaries for
**attribution**, on the strength of a **supervised** probe. The analogous step for
**detection** was then built unsupervised and failed on both axes
(`reports/INVARIANT_DETECTOR.md`). The attribution half was exposed to the same
risk and untested.

## Both criteria failed, and both predictions were wrong

| | required | T11 | T5 |
|---|---|---|---|
| **Overall accuracy** — beat the guard on both | > 56.3% / > 52.5% | **51.1%** (−5.2 pts) | **39.7%** (−12.8 pts) |
| **Rotation** — beat chance on both | > 25% | **2.1%** | **6.1%** |

I predicted 70–85% overall and rotation above 50%. Overall got **worse** on both
participants, and rotation, while no longer literally zero, is nowhere near
chance.

Per the preregistration: **one candidate, and no tuned variant follows a failure.**

## The failure is diagnostic

**`sd` — the feature assigned to `GAIN_DRIFT` — wins almost everything.**

| T11, injected | named `GAIN_DRIFT` | out of |
|---|---|---|
| `CHANNEL_DROPOUT` | 60 | 89 |
| `GEOMETRY_ROTATION` | 73 | 95 |
| `RATE_LOSS` | 14 | 109 |

Every fault raises the spread of the per-channel change distribution, so a
generic spread measure is elevated by all of them and swamps the specific ones.

**This is the `profile` residual problem in a new costume.** `decoder_guard`
carries a specificity ordering precisely because a generic component beats
specific ones on magnitude, and my preregistration explicitly declined to use one:

> *"No specificity ordering… all four features are equally specific by
> construction, so adding an ordering would be an untested extra mechanism."*

**That assumption was wrong.** `sd` is not specific to gain drift; it is a
generic spread measure. I reasoned from how the *faults* differ and forgot to ask
how the *features* overlap.

A second, separate failure: on T5, `frac_severely_down` **never wins once** —
`named_CHANNEL_DROPOUT` is 0 across the entire table, and dropout scores 0%.

## What I am deliberately not doing

The obvious fix is a specificity ordering over these four features. **I am not
building it.** The preregistration committed to one candidate, and a failure is
not a licence to keep going until something works — that constraint exists exactly
for moments like this, when the fix looks obvious and the temptation is strongest.

A future attempt should test an ordered version. It is an untested hypothesis
here, not a result.

## The stated uncertainty turned out to be moot

The preregistration flagged `GEOMETRY_ROTATION → skew` as the assignment I was
least sure of, with `kurtosis` as the alternative. **Neither would have helped**:
rotation is named `GAIN_DRIFT` in 73 of 95 episodes, so the binding failure is
`sd` dominating, not the choice between skew and kurtosis.

Flagging that uncertainty in advance still paid — it means I can rule it out as
the cause instead of speculating.

## What this corrects, and the pattern it completes

The recommendation in `PERMUTATION_INVARIANT.md` is corrected to what the
evidence supports:

> Invariant summaries are evidence that **the information distinguishing fault
> modes exists**. They are **not** a demonstrated design for a monitor — neither
> for detection nor for attribution.

Both halves have now been tested label-free and both fail. That produces the
sharpest methodological finding of this line of work:

> **A supervised demonstration that information exists has, twice, failed to
> translate into a label-free rule that uses it.**

Twice is not a law, but it is a pattern worth stating: separability under a
fitted discriminant is a weak guarantee about what an unsupervised monitor can
do, and this project now has two independent measurements of that gap rather
than an argument about it.

## Limitations

- One candidate per task, by design. A specificity-ordered rule, a different
  calibration, or a per-feature one-sided test might behave differently. Not
  testing them was a constraint against searching, not evidence that none works.
- The mapping uses knowledge of how faults are injected — the same standing as
  the guard's `EXPECTED_ATTRIBUTION`, which is what makes the comparison fair, and
  still not the standing of a monitor facing an unknown fault.
- Two participants, as everywhere. Here they agree: both criteria fail on both.
