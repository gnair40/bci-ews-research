# Detector benchmark — T5

**Generated:** 2026-08-28 14:53 UTC  
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
| `decoder_guard` | -35.0 s | — | 5/219 | 0.3005 | 110.11 |
| `distribution_shift` | -10.0 s | — | 2/219 | 0.3005 | 1080.12 |
| `mean_activity` | -10.0 s | — | 3/219 | 0.2254 | 47.62 |
| `robust_dispersion` | 55.0 s | 5.0..95.0 | 12/219 | 0.9015 | 116.67 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | PASS | PASS | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -42.5 s |
| GAIN_DRIFT | 5.0 s |

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| GAIN_DRIFT | -10.0 s |

### `mean_activity` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -10.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 55.0 s |
| GAIN_DRIFT | 50.0 s |
| GEOMETRY_ROTATION | 0.0 s |
| RATE_LOSS | 120.0 s |
