# Why averaging does not rescue the detector

**Reproduce:** `python3 scripts/29_aggregation_limit.py`

> Per-window AUC is ~0.70 and a session holds ~55 windows. If those were independent, aggregation would raise discriminability by roughly sqrt(55). It does not. This measures why, because the answer decides which direction is worth pursuing.

## Serial correlation and effective sample size

| Participant | Windows per session | Lag-1 autocorrelation | Effective independent samples |
|---|---|---|---|
| T11 | 55 | **0.995** | **0.1** |
| T5 | 42 | **0.980** | **0.4** |

## Session-level aggregators

| Aggregator | T11 | T5 |
|---|---|---|
| median | 0.684 | 0.736 |
| mean | 0.589 | 0.670 |
| 90th percentile | 0.469 | 0.510 |
| max | 0.457 | 0.487 |
| top-decile mean | 0.465 | 0.506 |
| fraction above own median | 0.436 | 0.322 |

Per-window AUC for comparison: **0.693** (T11), **0.707** (T5).
