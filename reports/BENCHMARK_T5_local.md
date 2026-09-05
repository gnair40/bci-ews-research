# Detector benchmark — T5

**Generated:** 2026-08-28 15:24 UTC  
**Reproduce:** `python3 scripts/20_evaluation_harness.py run --participant T5` then `python3 scripts/21_score_report.py --participant T5`

> Gates are reported before lead time, and that ordering is not cosmetic. A detector that fails the silence gate has not earned the right to have its lead time discussed.

## Setup

- Window 30 s, step 5 s
- Performance event: **+10°** above each episode's own pre-onset baseline, fixed before any detector existed
- False-alarm budget: **0.1/h**, threshold chosen on validation and frozen
- Episodes scored: 777

## Results

| Detector | Median lead | 95% CI | Detected | False alarms/h | Operating point |
|---|---|---|---|---|---|
| `decoder_guard` | -35.0 s | — | 6/219 | 0.2254 | 60.01 |
| `decoder_guard_joint` | -15.0 s | — | 6/219 | 0.3756 | 339.92 |
| `distribution_shift` | -10.0 s | — | 2/219 | 0.2254 | 660.82 |
| `mean_activity` | -55.0 s | — | 4/219 | 0.2254 | 32.71 |
| `robust_dispersion` | 57.5 s | 2.5..82.5 | 12/219 | 0.9015 | 53.46 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `decoder_guard_joint` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | PASS | PASS | PASS |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -60.0 s |
| GAIN_DRIFT | -30.0 s |
| GEOMETRY_ROTATION | 37.5 s |

### `decoder_guard_joint` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -15.0 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| GAIN_DRIFT | -10.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -30.0 s |
| RATE_LOSS | -105.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 57.5 s |
| GAIN_DRIFT | 40.0 s |
| GEOMETRY_ROTATION | 20.0 s |
| RATE_LOSS | 80.0 s |
