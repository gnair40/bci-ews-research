# Detector benchmark — T11

**Generated:** 2026-08-28 14:53 UTC  
**Reproduce:** `python3 scripts/20_evaluation_harness.py run --participant T11` then `python3 scripts/21_score_report.py --participant T11`

> Gates are reported before lead time, and that ordering is not cosmetic. A detector that fails the silence gate has not earned the right to have its lead time discussed.

## Setup

- Window 30 s, step 5 s
- Performance event: **+10°** above each episode's own pre-onset baseline, fixed before any detector existed
- False-alarm budget: **0.1/h**, threshold chosen on validation and frozen
- Episodes scored: 1073

## Results

| Detector | Median lead | 95% CI | Detected | False alarms/h | Operating point |
|---|---|---|---|---|---|
| `decoder_guard` | -25.0 s | -35.0..-5.0 | 121/586 | 2.0738 | 285.80 |
| `distribution_shift` | -45.0 s | -55.0..-20.0 | 97/586 | 1.6294 | 1361.10 |
| `mean_activity` | -30.0 s | -35.0..-15.0 | 105/586 | 2.2219 | 84.89 |
| `robust_dispersion` | 10.0 s | 5.0..17.5 | 284/586 | 20.3429 | 6.00 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | **FAIL** | PASS | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -30.0 s |
| GAIN_DRIFT | -20.0 s |
| GEOMETRY_ROTATION | -25.0 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -50.0 s |
| GAIN_DRIFT | -20.0 s |
| GEOMETRY_ROTATION | -52.5 s |
| RATE_LOSS | -35.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -30.0 s |
| GEOMETRY_ROTATION | -45.0 s |
| RATE_LOSS | -10.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 0.0 s |
| GAIN_DRIFT | 5.0 s |
| GEOMETRY_ROTATION | 5.0 s |
| NONE | 0.0 s |
| RATE_LOSS | 42.5 s |
