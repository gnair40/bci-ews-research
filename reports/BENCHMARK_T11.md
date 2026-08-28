# Detector benchmark — T11

**Generated:** 2026-08-28 02:15 UTC  
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
| `decoder_guard` | -5.0 s | -10.0..0.0 | 175/586 | 18.121 | 48.00 |
| `distribution_shift` | — | — | — | — | **none meets budget** |
| `mean_activity` | -10.0 s | -15.0..0.0 | 137/586 | 2.37 | 2.00 |
| `robust_dispersion` | -30.0 s | -50.0..40.0 | 11/586 | 0.1975 | 1.00 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | PASS | PASS | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | **FAIL** | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -2.5 s |
| GAIN_DRIFT | -2.5 s |
| GEOMETRY_ROTATION | -5.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -10.0 s |
| GEOMETRY_ROTATION | -45.0 s |
| RATE_LOSS | 0.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -30.0 s |
| GAIN_DRIFT | -7.5 s |
| GEOMETRY_ROTATION | -17.5 s |
