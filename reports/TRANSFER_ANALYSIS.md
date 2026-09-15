# Does anything transfer between participants?

**Reproduce:** `python3 scripts/38_transfer_analysis.py`

> Every study here ended with something helping one participant and hurting the other. Recorded four separate times, that stops being a limitation and becomes a result worth measuring. Every candidate evaluated on both participants is pooled below.

## Every candidate, both participants

| Candidate | T11 Δ | T5 Δ | Same direction? |
|---|---|---|---|
| F1 variability | +0.004 | -0.075 | **no** |
| F2 covariance | -0.043 | -0.137 | yes |
| F3 spectral | +0.078 | -0.186 | **no** |
| F4 counts | +0.003 | -0.212 | **no** |
| C1 decomp / F1 | -0.034 | +0.020 | **no** |
| C2 decomp / F2 | +0.030 | -0.124 | **no** |
| C3 decomp / both | -0.047 | +0.017 | **no** |

## The result

- **0 of 7 candidates improved *both* participants.**
- 1 of 7 moved in the same direction at all — and that one moved *down* on both.
- Correlation between the two columns: Pearson r = **-0.630** (p = 0.130), Spearman ρ = -0.429 (p = 0.337).
- The best candidate on T11 (F3 spectral, +0.078) is the **worst** on T5 (-0.186).
- The best on T5 (C1 decomp / F1, +0.020) is negative on T11 (-0.034).

## What can and cannot be claimed

**Can:** across seven candidates spanning four feature families and three decomposition arms, **none improved both participants.** That count needs no model and no assumption.

**Cannot:** that the correlation is genuinely negative. r = -0.630 looks striking but p = 0.130 at n = 7, and the candidates are not fully independent — C1 and C3 share a feature family. The honest reading is *no evidence of positive transfer*, not *evidence of negative transfer*.

## Why this matters more than any single null

Each study on its own said "this candidate did not work". Together they say something about **the problem** rather than about any candidate: **what improves decoder-health monitoring appears to be participant-specific.** Every attempt to find a measurement that helps one array and transfers to another has failed, in seven attempts, by construction independent of each other's outcome.

If that holds, it changes the target. A monitor would be **fitted per participant and per array**, and the question stops being *"which feature is best?"* and becomes *"how quickly can a monitor be calibrated for a new user?"* — a different and more tractable problem.

It also explains, in one sentence, why the two-participant limitation has been so binding: **there was never a shared effect for the second participant to confirm.**

## The obvious objection

Two participants cannot establish that generalisation fails in general; they can only fail to demonstrate it. A third dataset could show that T5 and T11 are unusually dissimilar and that transfer is ordinary. **That is exactly why a third dataset has been the top recommendation throughout, and this analysis strengthens rather than replaces that.**
