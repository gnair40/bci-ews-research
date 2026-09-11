# Trying to break the P5 result

**Predictions committed in advance:** `research/CEILING_CHALLENGE_NOTE.md` —
including that **I expected the confound to be real**.
**Script:** `50_ceiling_challenge.py`

## Summary

| | Outcome |
|---|---|
| Does the ceiling effect exist? | **Yes, and it is large.** Predicted, and confirmed. |
| Does it explain the P5 result? | **No.** Predicted it would; it does not. |
| Did anything else emerge? | **Yes** — a third variable that predicts equally well and cannot be told apart from P5. |
| Net effect on the headline | The **finding stands**; the **mechanism claim is withdrawn**. |

## 1. The ceiling effect is real

An episode counts as deteriorating when its smoothed decoder error exceeds **its
own pre-onset baseline + 10°**. On a day whose baseline already sits near the
90.7° chance level, there is almost no headroom left for a fault to do measurable
damage. Measured, as the median error increase actually achieved by injected
faults:

| T11 day | pre-onset baseline | damage the fault achieved |
|---|---|---|
| 665 | 44.9° | **+19.8°** |
| 658 | 49.9° | +19.6° |
| 758 | 58.3° | +27.4° |
| … | … | … |
| 770 | 83.4° | +1.7° |
| 672 | 83.1° | **−1.0°** |
| **783** | **87.5°** | **+0.4°** |

Baseline against achieved damage: **ρ = −0.747, p = 0.0033**. On the worst days
an injected fault moves the performance metric by less than half a degree.

**This is a genuine limitation of the fault-injection corpus and it is worth
recording on its own**, independently of what it does to P5: on high-baseline
sessions the ground truth is nearly degenerate, because a decoder already at
chance cannot be made much worse in a way this metric can see.

## 2. It does not explain P5

Both predictions about the consequences were wrong:

| Prediction | Result |
|---|---|
| damage ↔ decoder error: **negative** | ✓ ρ = −0.632, p = 0.021 |
| damage ↔ monitor AUC: **positive** | ✗ **ρ = +0.181, p = 0.55** |
| P5 weakens once damage is controlled | ✗ **strengthens: −0.720 → −0.794, p = 0.002** |

Weaker faults are *not* what makes the monitor fail on bad days. The middle row
is the one that matters: achieved damage barely relates to monitor accuracy at
all, so it cannot be the channel.

## 3. What did emerge, and why it forces a retraction

Measuring how often the ±10° threshold is cleared **in the pre-onset windows,
where no fault exists by construction**, gives a per-day noise level for the
decoder's performance trace. It rises from 0.3% on day 675 to **19.9% on day
783** — one pre-onset window in five clears the deterioration threshold with no
fault present at all.

That noise predicts the monitor's accuracy **exactly as well as decoder error
does**:

| T11 | ρ with monitor AUC | p |
|---|---|---|
| decoder error (P5) | **−0.720** | 0.0055 |
| trace noise | **−0.720** | 0.0055 |

And the two predictors correlate with each other at **ρ = +0.813**. The partial
correlations are the giveaway:

| | ρ | p |
|---|---|---|
| decoder error → AUC, controlling for trace noise | −0.333 | 0.29 |
| trace noise → AUC, controlling for decoder error | −0.333 | 0.29 |

**Identical, in both directions.** That is the signature of two collinear
predictors, not of one mediating the other. With 13 days and predictors
correlating at 0.81, this design cannot separate them — and I was one paragraph
from writing "trace noise is the real explanation", which the symmetry shows I
have no basis for.

## What stands and what is withdrawn

**Stands — the finding.** The monitor's per-day accuracy is strongly predicted by
how badly the decoder is doing that day (ρ = −0.720), and this survived the
early-warning-window challenge, the crossed/split challenge, and now the ceiling
challenge. Day 800: decoder error 42.5°, AUC 0.97. Day 783: 89.3°, AUC 0.32.
That is what a user of this system would experience, and it is unchanged.

**Withdrawn — the mechanism.** `reports/DAY_PREDICTORS.md` explained the result
as *"a day the decoder handles badly is atypical in ways that also hurt the
monitor."* I no longer have grounds to name which property of the day is
operative. "How badly the decoder is doing" and "how erratic the decoder's output
is" are the same variable at this sample size.

**Partly contaminated — the ground truth.** The spurious-crossing rate correlates
with monitor AUC at ρ = −0.665 (p = 0.013), so some of the day-to-day spread is
labels, not detection. It is not all of it: controlling P5 for the spurious rate
leaves **ρ = −0.613, p = 0.034**.

## A note on where this control came from

The ceiling and damage measures were fixed in the scope note before running. The
**trace-noise measure was added during the study**, once the damage result failed
to explain anything and the day-783 contradiction (median damage +0.4° yet 78% of
episodes "crossing") needed resolving.

It is a control variable rather than an outcome, and adding a control that
*weakens* my own finding is the conservative direction — but it was not
preregistered, and this paragraph exists so that is visible rather than implied.

## T5

Too small to arbitrate: 6 days. The ceiling effect does not appear there
(ρ = +0.029 baseline vs damage), decoder error and trace noise correlate only at
0.543, and nothing reaches significance once a control is added. It neither
supports nor contradicts.

## Limitations

- **13 days.** Two predictors correlating at 0.81 cannot be separated at this n.
  Separating them needs sessions where the decoder is bad but steady, or noisy
  but accurate — which this dataset may simply not contain.
- The ceiling effect means high-baseline sessions carry weak ground truth
  regardless of any of this, which limits what any analysis of those days can say.
