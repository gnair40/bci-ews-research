# Feature study — result

**Frozen at** `0950c0415736` (2026-09-01T21:08:25+00:00), before any feature was computed. Preregistration SHA-256 `a5e5bde03c0a3266…`

**Criterion, fixed in advance:** a family must raise session-level AUC by ≥ 0.05 over `decoder_guard` v1 **on both participants in the same direction**. A family helping only one is a null result, not a partial success.

> `F0_control_mean` is **not a fifth family**. It is the *current* feature — per-channel mean activity — pushed through the identical one-class scorer every family uses. Without it, a family beating `decoder_guard` could be winning on the shared scorer rather than on its features.

## Session-level AUC in the early-warning window

| | T11 AUC | T11 95% CI | Δ vs v1 | T5 AUC | T5 95% CI | Δ vs v1 |
|---|---|---|---|---|---|---|
| `decoder_guard (incumbent)` | 0.673 | 0.632–0.714 | +0.000 | 0.742 | 0.706–0.778 | +0.000 |
| `F0_control_mean` | 0.570 | 0.537–0.605 | -0.102 | 0.510 | 0.471–0.548 | -0.233 |
| `F1_variability` | 0.676 | 0.640–0.714 | +0.004 | 0.668 | 0.630–0.705 | -0.075 |
| `F2_covariance` | 0.629 | 0.591–0.665 | -0.043 | 0.605 | 0.564–0.644 | -0.137 |
| `F3_spectral` | 0.750 | 0.717–0.781 | +0.078 | 0.556 | 0.512–0.596 | -0.186 |
| `F4_counts` | 0.675 | 0.643–0.708 | +0.003 | 0.530 | 0.489–0.572 | -0.212 |

## Verdict against the frozen criterion

| Family | Cleared +0.05 on **both**? | |
|---|---|---|
| `F1_variability` | no | no improvement on either |
| `F2_covariance` | no | no improvement on either |
| `F3_spectral` | no | null result — helped T11 only |
| `F4_counts` | no | no improvement on either |

### No family clears the bar

That converts *"a better feature is the remaining direction"* into *"the four obvious better features were specified in advance, tried, and do not work"* — a stronger and more useful statement than the open question it replaces.

It does **not** show that no feature could work. It shows that the four families a careful reading of the problem suggested do not, on these two datasets.

## Secondary comparison — against the matched control

> **This is post-hoc and is not the frozen criterion.** It was computed after seeing that nothing passed. It is reported because it changes what the null result *means*, not because it rescues it.

The frozen criterion compares each family against `decoder_guard` v1, which uses its own four-component scorer. The families use the generic one. So a family losing to `decoder_guard` may be losing to the **scorer** rather than to the features. `F0_control_mean` — the current features through the generic scorer — is what settles that.

| Family | T11 vs F0 | T5 vs F0 | Both ≥ +0.05? |
|---|---|---|---|
| `F1_variability` | +0.106 | +0.158 | **yes** |
| `F2_covariance` | +0.059 | +0.095 | **yes** |
| `F3_spectral` | +0.180 | +0.047 | no |
| `F4_counts` | +0.105 | +0.021 | no |

**And the scorer is worth more than the features.** `decoder_guard` beats its own features under the generic scorer by +0.102 and +0.233. Its advantage is largely in the four-component decomposition, not in the per-channel means it consumes.

So the honest reading is: **two families are better features than the current ones, and that is not enough**, because the gain does not cover what the purpose-built scorer contributes. Combining better features with that decomposition is a new study, and would need its own preregistration.

## What this cannot settle

n = 2, and the two participants disagree. A family clearing +0.05 on both is encouraging and is still n = 2. A third dataset remains worth more.
