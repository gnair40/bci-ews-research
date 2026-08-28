# Benchmark summary — every configuration

**Reproduce:** `python3 scripts/24_benchmark_matrix.py` after running `scripts/20_evaluation_harness.py` and `scripts/21_score_report.py` across the grid.

## The headline

| | count | of 36 |
|---|---|---|
| Configurations run | 36 | — |
| Found any operating point at all | 21 | 58% |
| Achieved a **positive** median lead time | 5 | 14% |
| Met the false-alarm budget (≤0.1/h) | 1 | 3% |
| Passed the silence gate (≤10% of healthy episodes trend) | **0** | 0% |
| **Passed all five gates** | **0** | 0% |

> The binding constraint is not detection. Several configurations warn before performance falls. The constraint is **specificity**: the risk signal is never quiet during healthy operation, so any threshold low enough to catch a fault early also fires constantly on healthy record.

## Every configuration

| Participant | Baseline | Transform | Detector | Lead (s) | False alarms/h | Healthy episodes trending | Gates passed |
|---|---|---|---|---|---|---|---|
| T11 | calibrate once | none | `decoder-guard` | -5.0 | 18.12 | 87% | 3/5 |
| T11 | calibrate once | none | `mean activity` | -10.0 | 2.37 | 80% | 1/5 |
| T11 | calibrate once | none | `robust dispersion` | -30.0 | 0.20 | 85% | 1/5 |
| T11 | calibrate once | none | `distribution shift` | — *(no operating point)* | — | 91% | 1/5 |
| T11 | calibrate once | detrend | `decoder-guard` | -20.0 | 3.01 | 89% | 2/5 |
| T11 | calibrate once | detrend | `mean activity` | -20.0 | 2.47 | 86% | 1/5 |
| T11 | calibrate once | detrend | `robust dispersion` | -30.0 | 0.05 | 86% | 1/5 |
| T11 | calibrate once | detrend | `distribution shift` | — *(no operating point)* | — | 89% | 2/5 |
| T11 | calibrate once | trailing | `decoder-guard` | -5.0 | 3.75 | 31% | 2/5 |
| T11 | calibrate once | trailing | `mean activity` | 0.0 | 6.02 | 34% | 2/5 |
| T11 | calibrate once | trailing | `robust dispersion` | 5.0 | 6.96 | 42% | 3/5 |
| T11 | calibrate once | trailing | `distribution shift` | -5.0 | 5.88 | 32% | 2/5 |
| T11 | recent normal | none | `decoder-guard` | -20.0 | 3.36 | 98% | 1/5 |
| T11 | recent normal | none | `mean activity` | — *(no operating point)* | — | 80% | 1/5 |
| T11 | recent normal | none | `robust dispersion` | 5.0 | 15.60 | 92% | 0/5 |
| T11 | recent normal | none | `distribution shift` | — *(no operating point)* | — | 94% | 0/5 |
| T11 | recent normal | detrend | `decoder-guard` | -15.0 | 3.11 | 88% | 2/5 |
| T11 | recent normal | detrend | `mean activity` | -35.0 | 1.83 | 81% | 1/5 |
| T11 | recent normal | detrend | `robust dispersion` | -5.0 | 5.18 | 89% | 2/5 |
| T11 | recent normal | detrend | `distribution shift` | — *(no operating point)* | — | 92% | 0/5 |
| T11 | recent normal | trailing | `decoder-guard` | — *(no operating point)* | — | 34% | 2/5 |
| T11 | recent normal | trailing | `mean activity` | 15.0 | 4.05 | 50% | 2/5 |
| T11 | recent normal | trailing | `robust dispersion` | 0.0 | 4.39 | 48% | 2/5 |
| T11 | recent normal | trailing | `distribution shift` | — *(no operating point)* | — | 55% | 2/5 |
| T5 | recent normal | none | `decoder-guard` | — *(no operating point)* | — | 100% | 1/5 |
| T5 | recent normal | none | `mean activity` | -52.5 | 0.23 | 77% | 1/5 |
| T5 | recent normal | none | `robust dispersion` | 57.5 | 0.90 | 63% | 4/5 |
| T5 | recent normal | none | `distribution shift` | — *(no operating point)* | — | 95% | 1/5 |
| T5 | recent normal | detrend | `decoder-guard` | — *(no operating point)* | — | 93% | 1/5 |
| T5 | recent normal | detrend | `mean activity` | -20.0 | 0.30 | 81% | 1/5 |
| T5 | recent normal | detrend | `robust dispersion` | 55.0 | 0.53 | 81% | 3/5 |
| T5 | recent normal | detrend | `distribution shift` | — *(no operating point)* | — | 91% | 1/5 |
| T5 | recent normal | trailing | `decoder-guard` | — *(no operating point)* | — | 50% | 2/5 |
| T5 | recent normal | trailing | `mean activity` | — *(no operating point)* | — | 45% | 2/5 |
| T5 | recent normal | trailing | `robust dispersion` | — *(no operating point)* | — | 62% | 2/5 |
| T5 | recent normal | trailing | `distribution shift` | — *(no operating point)* | — | 66% | 2/5 |

## Closest approach to the silence gate

`decoder-guard` — T11, calibrate once baseline, trailing transform: **31%** of healthy episodes still show a significant trend, against a **10%** requirement.

A trailing reference is what moves this number, and it moves it by roughly half. It does not get close to passing.
