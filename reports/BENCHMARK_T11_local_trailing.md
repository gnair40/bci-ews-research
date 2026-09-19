# Detector benchmark — T11

**Generated:** 2026-08-28 14:51 UTC  
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
| `decoder_guard` | 0.0 s | 0.0..10.0 | 38/586 | 4.8882 | 113.34 |
| `distribution_shift` | 0.0 s | 0.0..5.0 | 177/586 | 5.5795 | 110.11 |
| `mean_activity` | 15.0 s | 0.0..35.1 | 33/586 | 4.0488 | 40.04 |
| `robust_dispersion` | 0.0 s | -5.0..0.0 | 73/586 | 4.6907 | 31.78 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |
| `distribution_shift` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |
| `mean_activity` | **FAIL** | PASS | — | PASS | **FAIL** |
| `robust_dispersion` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -7.5 s |
| GAIN_DRIFT | 5.0 s |
| GEOMETRY_ROTATION | 0.0 s |
| RATE_LOSS | 35.0 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 0.0 s |
| GAIN_DRIFT | 5.0 s |
| GEOMETRY_ROTATION | 0.0 s |
| NONE | -30.0 s |
| RATE_LOSS | 30.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 0.0 s |
| GAIN_DRIFT | -115.0 s |
| GEOMETRY_ROTATION | 17.5 s |
| NONE | -5.0 s |
| RATE_LOSS | 55.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 0.0 s |
| GAIN_DRIFT | -2.5 s |
| GEOMETRY_ROTATION | 0.0 s |
| NONE | -50.0 s |
| RATE_LOSS | 7.5 s |
