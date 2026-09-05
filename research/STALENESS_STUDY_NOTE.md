# Recalibration-cadence study — scope fixed before running

**Written:** 2 September 2026, after the calibration curve and before any
staleness number is computed.

## The question

The calibration curve answered *how much* healthy recording commissioning costs:
about 20 windows, two minutes. The companion question, and the one that finishes
a deployable story, is:

> **How long does that calibration stay valid?**

A monitor fitted on day A and used on day B is working from a stale picture of
the array. Neural recordings drift across months — that drift is the entire
reason decoders need recalibrating, and it is the premise of this project. If the
monitor's own fit goes stale as fast as the decoder's does, then a monitor is not
a way out of the recalibration problem, it is a second instance of it.

This is **within-participant**, so the two-participant limitation that blocked the
transfer analysis does not apply.

## What the data allows

| | T11 | T5 |
|---|---|---|
| Sessions | 15 | 6 |
| Span | day 658 → 800 = **142 days** | day 2121 → 2149 = **28 days** |
| Forward ordered day pairs | 105 | 15 |

T11 carries this study. T5 can only speak to gaps under a month and is reported
as a consistency check, not as a replication.

## Fixed in advance

| | |
|---|---|
| Metric | session-level AUC in the early-warning window, as throughout |
| What varies | the **gap in days** between the day the global fit came from and the day the episodes come from |
| Fit size | **exactly 40 healthy windows**, from one source day. Fixed so fit size cannot confound the gap — 40 is above the singular regime (n ≤ K = 10) and on the flat part of the calibration curve |
| Repeats | 5 random 40-window draws per (source day, target day) pair |
| Test episodes | up to 40 per target day, fixed random draw, seed 20260902 |
| Local re-baselining | unchanged, exactly as everywhere else |
| Primary analysis | **AUC(A→B) − AUC(B→B)**, i.e. each cross-day fit scored against the *same-day* fit on the same target day |
| Reported | both participants, forward gaps primary, whatever the curves look like |

### Why the primary analysis is a difference

Different days contain different episodes and are not equally easy. Comparing raw
AUC across target days would confound "the fit is stale" with "that day was
harder". Subtracting the same-day fit on the *same target day* removes that: what
is left is what the gap costs, holding the test set fixed.

The same-day reference is mildly optimistic — the healthy windows and the
episodes come from the same session, though from different blocks where possible.
That optimism inflates the *difference*, so it biases toward finding staleness.
That is the safe direction and it is stated rather than corrected.

## Prediction, recorded before running

**I expect the staleness effect to be small.** Local re-baselining already
re-centres every episode on its own pre-onset windows, so day-to-day offset drift
is largely absorbed before the global fit is consulted. What the global fit still
supplies is the subspace and scale the profile component is measured in, and the
calibration curve showed that is estimable from 20 windows — which suggests it is
a coarse, stable property rather than a finely-tuned one.

This is written down so that a small effect counts as a **result** rather than
being reframed after the fact as a failed study, and so that a large effect
counts as my prediction being **wrong** rather than as something I anticipated.

## What this can and cannot say

**Can:** how fast this monitor's global fit goes stale on these two arrays, over
142 days on T11.

**Cannot:** anything about a new participant — still the transfer question, still
needing a third dataset. And nothing about whether the monitor is good enough to
deploy: AUC 0.65–0.74 is far below the ~0.99 the false-alarm budget demands. This
measures the *shelf life* of a fit, not its quality.
