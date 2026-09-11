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
| `decoder_guard` | — | — | — | — | **none meets budget** |
| `distribution_shift` | 80.0 s | — | 3/219 | 0.2254 | 311.69 |
| `mean_activity` | None s | — | 0/219 | 0.0 | 67.37 |
| `robust_dispersion` | 115.0 s | — | 1/219 | 0.0751 | 320.83 |

## Gates

| Detector | silence | rate_invariance | comparator | elapsed_time | detrend |
|---|---|---|---|---|---|
| `decoder_guard` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |
| `distribution_shift` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |
| `mean_activity` | **FAIL** | PASS | — | PASS | **FAIL** |
| `robust_dispersion` | **FAIL** | PASS | **FAIL** | PASS | **FAIL** |

Gate meanings: **silence** — no trend in risk while healthy. **rate invariance** — risk is not a restatement of total activity. **comparator** — beats counting spikes at a matched false-alarm rate. **elapsed time** — not merely tracking time. **detrend** — silence still holds after removing a linear trend.

### `distribution_shift` by fault mode

| Fault | Median lead |
|---|---|
| GAIN_DRIFT | 80.0 s |

### `robust_dispersion` by fault mode

| Fault | Median lead |
|---|---|
| CHANNEL_DROPOUT | 115.0 s |
