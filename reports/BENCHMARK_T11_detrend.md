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
| `decoder_guard` | -20.0 s | -20.0..-15.0 | 192/586 | 3.0119 | 33.00 |
| `distribution_shift` | — | — | — | — | **none meets budget** |
| `mean_activity` | -20.0 s | -25.0..-5.0 | 147/586 | 2.4688 | 1.75 |
| `robust_dispersion` | -30.0 s | -52.5..2.5 | 12/586 | 0.0494 | 1.00 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | PASS | **FAIL** | **FAIL** | PASS |
| `distribution_shift` | **FAIL** | PASS | **FAIL** | **FAIL** | PASS |
| `mean_activity` | **FAIL** | **FAIL** | — | **FAIL** | PASS |
| `robust_dispersion` | **FAIL** | PASS | **FAIL** | **FAIL** | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `decoder_guard` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | -15.0 s |
| GAIN_DRIFT | -22.5 s |
| GEOMETRY_ROTATION | -17.5 s |

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
| CHANNEL_DROPOUT | -40.0 s |
| GAIN_DRIFT | -25.0 s |
| GEOMETRY_ROTATION | -20.0 s |
