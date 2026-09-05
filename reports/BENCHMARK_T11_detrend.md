# Detector benchmark — T11

**Generated:** 2026-08-28 14:50 UTC  
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
| `decoder_guard` | -15.0 s | -20.0..-15.0 | 193/586 | 3.1601 | 32.71 |
| `distribution_shift` | -40.0 s | -55.0..-15.0 | 59/586 | 0.6419 | 127.23 |
| `mean_activity` | -20.0 s | -25.0..-5.0 | 147/586 | 2.4688 | 1.75 |
| `robust_dispersion` | -20.0 s | -37.5..30.1 | 18/586 | 0.1975 | 0.50 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | PASS | PASS | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | PASS | **FAIL** | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | **FAIL** | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -15.0 s |
| GAIN_DRIFT | -22.5 s |
| GEOMETRY_ROTATION | -15.0 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -45.0 s |
| GAIN_DRIFT | -20.0 s |
| GEOMETRY_ROTATION | -40.0 s |
| RATE_LOSS | -80.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -25.0 s |
| GAIN_DRIFT | -25.0 s |
| GEOMETRY_ROTATION | -42.5 s |
| NONE | 10.0 s |
| RATE_LOSS | -15.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 17.5 s |
| GAIN_DRIFT | -25.0 s |
| GEOMETRY_ROTATION | -42.5 s |
