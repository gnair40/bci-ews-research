# Calibration-efficiency study — scope fixed before running

**Written:** 2 September 2026, after the transfer analysis and before any curve
is computed.

## Why this question, and why now

The transfer analysis found **0 of 7 candidates improved both participants**, and
concluded that what helps a decoder-health monitor appears to be
participant-specific. If that holds, the useful question stops being *"which
feature generalises?"* and becomes:

> **How much healthy recording does a monitor need before it is as good as it
> is going to get for that person?**

That question is answerable with the data already downloaded. It is
**within-participant by construction**, so the disagreement that has blocked
everything else does not apply to it.

## Why this is a lighter-weight note rather than a full freeze

The two previous studies compared candidates against a threshold, so there was a
favourable direction to select toward and a freeze was necessary. This produces a
**descriptive curve** — how performance varies with the amount of fitting data.
There is no "better" outcome to steer toward: a monitor needing 5 minutes and one
needing 5 hours are both just facts.

That said, a descriptive study still has choices that could be tuned after the
fact, so the ones that matter are fixed here:

| Fixed in advance | |
|---|---|
| Metric | session-level AUC in the early-warning window, as throughout |
| What varies | number of healthy windows used for the **global fit** |
| What does not | local re-baselining on each episode's pre-onset windows, unchanged |
| Grid | 5, 10, 20, 40, 80, 160, all available |
| Repeats | 5 random healthy subsets per grid point, reported with spread |
| Episodes | a fixed random 300 per participant, drawn once with a stated seed |
| Reported | both participants, whatever the curves look like |

**Saturation is not defined in advance**, because defining it before seeing the
curve shape would be guessing. The curve is reported and read; no threshold for
"enough" is set retrospectively and presented as though it were prior.

## What this can and cannot say

**Can:** how much healthy data this monitor needs on these two arrays.

**Cannot:** that the same amount suffices for a new participant. That is the
transfer question, and it is the one that needs a third dataset.
