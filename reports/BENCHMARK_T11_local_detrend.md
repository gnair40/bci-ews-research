# Detector benchmark — T11

**Generated:** 2026-08-28 02:25 UTC  
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
| `decoder_guard` | -15.0 s | -20.1..-10.0 | 145/586 | 3.1107 | 45.00 |
| `distribution_shift` | — | — | — | — | **none meets budget** |
| `mean_activity` | -35.0 s | -45.0..-30.0 | 79/586 | 1.8269 | 55.00 |
| `robust_dispersion` | -5.0 s | -10.0..0.0 | 227/586 | 5.1845 | 14.00 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | PASS | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -30.0 s |
| GAIN_DRIFT | -15.0 s |
| GEOMETRY_ROTATION | -10.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -32.5 s |
| GEOMETRY_ROTATION | -47.5 s |
| RATE_LOSS | -15.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -5.0 s |
| GAIN_DRIFT | 0.0 s |
| GEOMETRY_ROTATION | -10.0 s |
| NONE | -45.0 s |
| RATE_LOSS | 0.0 s |
