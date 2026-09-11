# Benchmark summary — every configuration

**Reproduce:** `python3 scripts/24_benchmark_matrix.py` after running `scripts/20_evaluation_harness.py` and `scripts/21_score_report.py` across the grid.

> **Correction, 28 Aug.** An earlier version of this table searched WARN thresholds only up to 59, while observed scores reach 300 (`decoder-guard`) and 3200 (`distribution_shift`). Configurations were therefore reported as having no operating point when the truth was that none existed *below an arbitrary bound*. The grid now spans the range the scores occupy and every row here is from the corrected search.

## The headline

| | count | of 48 |
|---|---|---|
| Configurations run | 48 | — |
| Found any operating point at all | 47 | 98% |
| Achieved a **positive** median lead time | 10 | 21% |
| Met the false-alarm budget (≤0.1/h) | 3 | 6% |
| Passed the silence gate (≤10% of healthy episodes trend) | **0** | 0% |
| **Passed all five gates** | **0** | 0% |

> The binding constraint is not detection. Several configurations warn before performance falls. The constraint is **specificity**: the risk signal is never quiet during healthy operation, so any threshold low enough to catch a fault early also fires constantly on healthy record.

## Every configuration

| Participant | Baseline | Transform | Detector | Lead (s) | Detected | False alarms/h | Healthy episodes trending | Gates passed |
|---|---|---|---|---|---|---|---|---|
| T11 | calibrate once | none | `decoder-guard` | 0.0 | 174/586 | 18.27 | 87% | 3/5 |
| T11 | calibrate once | none | `mean activity` | -10.0 | 137/586 | 2.37 | 80% | 1/5 |
| T11 | calibrate once | none | `robust dispersion` | -30.0 | 16/586 ⚠ | 0.20 | 85% | 1/5 |
| T11 | calibrate once | none | `distribution shift` | -25.0 | 144/586 | 1.78 | 91% | 1/5 |
| T11 | calibrate once | detrend | `decoder-guard` | -15.0 | 193/586 | 3.16 | 89% | 3/5 |
| T11 | calibrate once | detrend | `mean activity` | -20.0 | 147/586 | 2.47 | 86% | 1/5 |
| T11 | calibrate once | detrend | `robust dispersion` | -20.0 | 18/586 ⚠ | 0.20 | 86% | 1/5 |
| T11 | calibrate once | detrend | `distribution shift` | -40.0 | 59/586 | 0.64 | 89% | 2/5 |
| T11 | calibrate once | trailing | `decoder-guard` | -5.0 | 54/586 | 3.80 | 31% | 2/5 |
| T11 | calibrate once | trailing | `mean activity` | 0.0 | 83/586 | 6.07 | 34% | 2/5 |
| T11 | calibrate once | trailing | `robust dispersion` | 5.0 | 96/586 | 6.96 | 42% | 3/5 |
| T11 | calibrate once | trailing | `distribution shift` | -5.0 | 81/586 | 5.88 | 32% | 2/5 |
| T11 | calibrate once | pre-onset z | `decoder-guard` | -25.0 | 130/586 | 1.98 | 86% | 2/5 |
| T11 | calibrate once | pre-onset z | `mean activity` | -20.0 | 71/586 | 1.38 | 76% | 1/5 |
| T11 | calibrate once | pre-onset z | `robust dispersion` | 5.0 | 273/586 | 15.65 | 92% | 2/5 |
| T11 | calibrate once | pre-onset z | `distribution shift` | -27.5 | 78/586 | 1.38 | 91% | 2/5 |
| T11 | recent normal | none | `decoder-guard` | -20.0 | 143/586 | 3.41 | 98% | 2/5 |
| T11 | recent normal | none | `mean activity` | -35.0 | 90/586 | 2.17 | 80% | 1/5 |
| T11 | recent normal | none | `robust dispersion` | 5.0 | 275/586 | 15.60 | 92% | 1/5 |
| T11 | recent normal | none | `distribution shift` | -35.0 | 161/586 | 2.67 | 94% | 0/5 |
| T11 | recent normal | detrend | `decoder-guard` | -15.0 | 145/586 | 3.11 | 88% | 2/5 |
| T11 | recent normal | detrend | `mean activity` | -35.0 | 79/586 | 1.83 | 81% | 1/5 |
| T11 | recent normal | detrend | `robust dispersion` | -5.0 | 230/586 | 5.28 | 89% | 2/5 |
| T11 | recent normal | detrend | `distribution shift` | -35.0 | 149/586 | 2.47 | 92% | 0/5 |
| T11 | recent normal | trailing | `decoder-guard` | 0.0 | 38/586 | 4.89 | 34% | 2/5 |
| T11 | recent normal | trailing | `mean activity` | 15.0 | 33/586 | 4.05 | 50% | 2/5 |
| T11 | recent normal | trailing | `robust dispersion` | 0.0 | 73/586 | 4.69 | 48% | 2/5 |
| T11 | recent normal | trailing | `distribution shift` | 0.0 | 177/586 | 5.58 | 55% | 2/5 |
| T11 | recent normal | pre-onset z | `decoder-guard` | -25.0 | 121/586 | 2.07 | 98% | 2/5 |
| T11 | recent normal | pre-onset z | `mean activity` | -30.0 | 105/586 | 2.22 | 82% | 1/5 |
| T11 | recent normal | pre-onset z | `robust dispersion` | 10.0 | 284/586 | 20.34 | 91% | 1/5 |
| T11 | recent normal | pre-onset z | `distribution shift` | -45.0 | 97/586 | 1.63 | 96% | 0/5 |
| T5 | recent normal | none | `decoder-guard` | -35.0 | 6/219 ⚠ | 0.23 | 100% | 2/5 |
| T5 | recent normal | none | `mean activity` | -55.0 | 4/219 ⚠ | 0.23 | 77% | 1/5 |
| T5 | recent normal | none | `robust dispersion` | 57.5 | 12/219 | 0.90 | 63% | 4/5 |
| T5 | recent normal | none | `distribution shift` | -10.0 | 2/219 ⚠ | 0.23 | 95% | 2/5 |
| T5 | recent normal | detrend | `decoder-guard` | None | 0/219 ⚠ | 0.08 | 93% | 1/5 |
| T5 | recent normal | detrend | `mean activity` | -20.0 | 5/219 ⚠ | 0.30 | 81% | 1/5 |
| T5 | recent normal | detrend | `robust dispersion` | 55.0 | 11/219 | 0.60 | 81% | 3/5 |
| T5 | recent normal | detrend | `distribution shift` | -10.0 | 2/219 ⚠ | 0.15 | 91% | 2/5 |
| T5 | recent normal | trailing | `decoder-guard` | — *(no operating point)* | — | — | 50% | 2/5 |
| T5 | recent normal | trailing | `mean activity` | None | 0/219 ⚠ | 0.00 | 45% | 2/5 |
| T5 | recent normal | trailing | `robust dispersion` | 115.0 | 1/219 ⚠ | 0.08 | 62% | 2/5 |
| T5 | recent normal | trailing | `distribution shift` | 80.0 | 3/219 ⚠ | 0.23 | 66% | 2/5 |
| T5 | recent normal | pre-onset z | `decoder-guard` | -35.0 | 5/219 ⚠ | 0.30 | 100% | 1/5 |
| T5 | recent normal | pre-onset z | `mean activity` | -10.0 | 3/219 ⚠ | 0.23 | 76% | 1/5 |
| T5 | recent normal | pre-onset z | `robust dispersion` | 55.0 | 12/219 | 0.90 | 63% | 3/5 |
| T5 | recent normal | pre-onset z | `distribution shift` | -10.0 | 2/219 ⚠ | 0.30 | 96% | 1/5 |

⚠ marks a lead time computed from fewer than 5% of the fault episodes. A long lead measured on one or two detections is not a fast detector; it is a near-silent one that happened to fire early, and the two are easy to confuse in a table.

## The tradeoff, stated as a rule

Across the whole grid, a configuration either detects a meaningful share of faults and false-alarms far past budget, or meets budget and barely fires at all. The single configuration meeting the false-alarm budget with a positive lead time (T5, recent normal, trailing, robust dispersion: **+115 s**) detected **1 fault in 219**. There is no middle of this curve in the data as it stands.

## Closest approach to the silence gate

`decoder-guard` — T11, calibrate once baseline, trailing transform: **31%** of healthy episodes still show a significant trend, against a **10%** requirement.

A trailing reference is what moves this number, and it moves it by roughly half. It does not get close to passing.
