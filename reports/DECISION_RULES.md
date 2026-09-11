# Decision rules compared by curve

**Reproduce:** `python3 scripts/27_decision_rules.py`

> Comparing one operating point per rule is how you get fooled: CUSUM detects 221 faults to the threshold rule's 143 but shows a *later* median lead, purely because the extra 78 are the hard cases the other rule missed entirely. Curves cannot hide behind a favourable threshold.


## Detection achievable within the false-alarm budget

| Participant | Rule | Faults detected at ≤0.1/h |
|---|---|---|
| T11 | `threshold` | **0.0%** |
| T11 | `cusum` | **0.0%** |
| T11 | `cusum+spec` | **0.0%** |
| T5 | `threshold` | **0.8%** |
| T5 | `cusum` | **0.3%** |
| T5 | `cusum+spec` | **0.3%** |

Every rule is at or near zero useful detection inside the budget. The rule is not the bottleneck.
