# Does deciding less often help? The comparison, done paired

**Reproduce:** `python3 scripts/78_decision_rate_paired.py`

> `scripts/76` reports each decision rate's detection with its own interval, and the published reading was that the intervals overlap so nothing can be settled. **Overlap of two marginal intervals is not a test of a difference**, and here both rates are scored on the same episodes against the same fault-free set, so most of the uncertainty is shared and cancels in the difference.

## Each participant's full range

| | Decision rate | Degraded | Fault-free | Change | Paired 95% CI | Established? |
|---|---|---|---|---|---|---|
| **T11** | 720 → 13/h | 764 | 29 | **+11.5%** | -0.3% to +27.6% | no |
| **T5** | 720 → 27/h | 369 | 21 | **-18.2%** | -42.3% to -4.9% | **yes** |

## Matched range — both to 27 decisions an hour

The two participants' episodes are different lengths, so their own ranges end at different decision rates. This row compares like with like.

| | Change | Paired 95% CI | Established? |
|---|---|---|---|
| **T11** | +11.3% | +0.0% to +27.1% | no |
| **T5** | -18.2% | -41.5% to -5.1% | **yes** |

## What this changes

**The archived data is not silent on this question.** On T5 the change is established at the 95% level. The earlier reading — that nothing can be said — came from comparing intervals instead of testing the difference.

**And the established result points the wrong way for the hypothesis.** On T5 deciding less often makes detection **worse**, not better. The physical phase's prediction PP-7 expects the opposite.

That is a better reason to run the experiment than "we cannot tell", and a worse position to start from than this project had assumed. A preregistered prediction that contradicts the only established evidence available is still a legitimate prediction — but it has to be made knowing that, and PP-7 now says so.

## What this does not change

- **n = 2, and they still disagree.** A paired test tightens each participant's own interval; it cannot reconcile two participants who point in opposite directions.
- The threshold still rests on 29 and 21 fault-free episodes. Pairing cancels that uncertainty **in the difference**, not in the levels, so the absolute detection rates remain as uncertain as `scripts/76` says.
- Nothing here is about the physical apparatus. It is a re-reading of the archived analysis.