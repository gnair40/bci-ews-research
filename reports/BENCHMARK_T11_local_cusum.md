# Detector benchmark — T11

**Generated:** 2026-08-28 19:43 UTC  
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
| `decoder_guard` | -55.0 s | -65.0..-50.0 | 221/586 | 3.3576 | 1019.46 |
| `decoder_guard_joint` | -55.0 s | -65.0..-50.0 | 211/586 | 3.6044 | 3432.14 |
| `distribution_shift` | -50.0 s | -60.0..-45.0 | 255/586 | 4.6907 | 4201.76 |
| `mean_activity` | -80.0 s | -90.0..-70.0 | 101/586 | 2.0244 | 1284.66 |
| `robust_dispersion` | -5.0 s | -5.0..0.0 | 385/586 | 13.7759 | 44.95 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `decoder_guard_joint` | **FAIL** | **FAIL** | PASS | **FAIL** | **FAIL** |
| `distribution_shift` | **FAIL** | **FAIL** | PASS | **FAIL** | **FAIL** |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | **FAIL** | PASS | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -45.0 s |
| GAIN_DRIFT | -65.0 s |
| GEOMETRY_ROTATION | -57.5 s |

### `decoder_guard_joint` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -45.0 s |
| GAIN_DRIFT | -85.0 s |
| GEOMETRY_ROTATION | -62.5 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -50.0 s |
| GAIN_DRIFT | -52.5 s |
| GEOMETRY_ROTATION | -55.0 s |
| RATE_LOSS | -47.5 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -80.0 s |
| GEOMETRY_ROTATION | -110.0 s |
| RATE_LOSS | -57.5 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -5.0 s |
| GAIN_DRIFT | 0.0 s |
| GEOMETRY_ROTATION | -10.0 s |
| NONE | -45.0 s |
| RATE_LOSS | 15.0 s |
