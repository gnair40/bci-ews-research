# What makes a day good or bad for the monitor — preregistered

**Written:** 2 September 2026, after the day-variance result and **before any
predictor is computed**.

## The question

Same-day AUC ranges 0.32 to 0.97 across 13 sessions on T11, and only 26% of that
is sampling noise. Something about a session decides whether the monitor works on
it. This asks what.

## Why this needs a preregistration when the last two studies needed only a note

The calibration curve was descriptive — there was no favourable direction to
steer toward. This is not. There are dozens of session properties I could
correlate against 13 numbers, and with that many chances something will clear
p < 0.05 by luck alone. Without a fixed list written down first, this study is a
fishing expedition wearing a lab coat.

## The power limit, stated before looking

**With 13 days, this study can only detect a very large effect.** At n = 13 and
a Bonferroni threshold of 0.05/5 = 0.01, a Spearman correlation must reach
**|ρ| ≈ 0.68** to be called significant. Anything smaller than that is
undetectable here no matter how real it is.

This is written down so that a null result is read as *"underpowered"* and not as
*"no relationship exists"*, and so that a hit at ρ = 0.7 is read as *"the only
size of effect this design could have found"* rather than as a strong discovery.

## The five predictors, and the direction predicted for each

Chosen because each has a mechanism, not because it is available. **The direction
is committed in advance**, so a correlation with the opposite sign counts against
the mechanism rather than being reinterpreted as support.

| # | Predictor | Mechanism | Predicted sign |
|---|---|---|---|
| **P1** | **Healthy dispersion** — robust spread of that day's healthy window features | The monitor scores departures from a healthy reference. A wide reference makes a departure of any given size less visible. This is the most direct mechanism and my primary hypothesis. | **negative** |
| **P2** | **Mean firing rate** across the day's healthy windows | More spikes means more signal per window and less counting noise | positive |
| **P3** | **Active channel count** — channels above the silence floor | A fault expressed on dead channels cannot be seen; more live channels means more places to see it | positive |
| **P4** | **Within-day drift** — how far the healthy features move from the start of the day to the end | A day that is drifting is already moving in the direction a fault would move it, masking faults | negative |
| **P5** | **Decoder error on that day's healthy data** | A day the decoder already handles badly may be atypical in ways that also hurt the monitor | negative |

## Fixed in advance

| | |
|---|---|
| Outcome | the same-day AUC per day already in `data/processed/day_variance*.csv`, unchanged |
| Test | Spearman rank correlation, two-sided |
| Threshold | Bonferroni, 0.05 / 5 = **0.01** |
| Reported | **all five, both participants, with sign and p, whatever they show** |
| Not permitted | adding a sixth predictor after seeing these five; dropping a day; switching to a one-sided test after seeing a sign |

If a later predictor is added, it will be added **in a new section labelled
exploratory**, with its own reasoning, and will never be presented alongside
these five as though it had been preregistered.

## What a positive result would and would not mean

**Would:** identify a measurable session property that predicts whether the
monitor works — which is directly actionable, since it means a deployed monitor
could tell the user *"today is a day I cannot be trusted"* rather than failing
silently. That is a genuinely useful capability and it is the reason this study
is worth doing.

**Would not:** establish causation, or generalise beyond these two arrays. And
with T5's day effect already confounded with fault mix, T5 can at best offer weak
support here.
