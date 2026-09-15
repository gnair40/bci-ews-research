# Combination study — result

**Frozen at** `72349644fd0a` before any arm was computed. Preregistration SHA-256 `7937a719d64f8dbd…`

**Faithfulness check** (the study was conditional on it): the generalised decomposition reproduces `decoder_guard` v1 on the original features at Spearman ρ = 1.0000 over 6,637 windows. Passed.

**Criterion:** ≥ +0.05 session-level AUC over `decoder_guard` v1 on **both** participants in the same direction. Recorded in advance: *a combined arm landing at +0.04 is not grounds for relaxing this.*

## Session-level AUC in the early-warning window

| Arm | T11 AUC | T11 95% CI | Δ | T5 AUC | T5 95% CI | Δ |
|---|---|---|---|---|---|---|
| `decoder_guard (incumbent)` | 0.673 | 0.632–0.714 | +0.000 | 0.742 | 0.706–0.778 | +0.000 |
| `C1_variability` | 0.639 | 0.599–0.679 | -0.034 | 0.762 | 0.728–0.795 | +0.020 |
| `C2_covariance` | 0.703 | 0.667–0.736 | +0.030 | 0.619 | 0.578–0.658 | -0.124 |
| `C3_both` | 0.626 | 0.587–0.666 | -0.047 | 0.760 | 0.725–0.793 | +0.017 |

## Verdict against the frozen criterion

| Arm | Cleared +0.05 on both? | |
|---|---|---|
| `C1_variability` | no | no improvement on either |
| `C2_covariance` | no | no improvement on either |
| `C3_both` | no | no improvement on either |

### Nothing clears the bar

Better features and a better decomposition were the two ingredients this project's own results identified, and combining them does not close the gap either. That closes the last direction the results themselves suggested.

The session-level target remains ≈ 0.93. n = 2 and the participants disagree - in Phase 1-2, on the joint-detector prediction, and in the F3 row of the feature study. A third dataset remains worth more than any arm here.
