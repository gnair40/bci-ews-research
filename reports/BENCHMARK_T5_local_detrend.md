# Detector benchmark — T5

**Generated:** 2026-08-28 14:50 UTC  
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
| `decoder_guard` | None s | — | 0/219 | 0.0751 | 61.77 |
| `distribution_shift` | -10.0 s | — | 2/219 | 0.1503 | 660.82 |
| `mean_activity` | -20.0 s | — | 5/219 | 0.3005 | 23.12 |
| `robust_dispersion` | 55.0 s | -5.0..85.0 | 11/219 | 0.601 | 56.64 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | PASS | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | PASS | **FAIL** | PASS |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| GAIN_DRIFT | -10.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -15.0 s |
| RATE_LOSS | -95.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 55.0 s |
| GAIN_DRIFT | 80.0 s |
| GEOMETRY_ROTATION | -20.0 s |
| RATE_LOSS | 70.0 s |
