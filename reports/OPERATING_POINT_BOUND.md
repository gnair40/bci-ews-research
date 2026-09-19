# Why the false-alarm budget is unreachable

**Reproduce:** `python3 scripts/28_operating_point_bound.py`

> This corrects an earlier conclusion. Having measured that the information is present (AUC 0.69-0.71), this project concluded the failure was in the machinery converting scores to warnings and would be fixable. Comparing decision rules by their full curve refuted that: threshold, CUSUM and CUSUM-with-a-specificity-gate all detect ~0% inside the budget. What follows is the reason.

## The multiple-comparisons burden

| | T11 | T5 |
|---|---|---|
| Healthy windows in test | 17,014 | 17,337 |
| Healthy hours | 23.6 | 24.1 |
| Alarms the budget permits | 2.4 | 2.4 |
| **Required per-window false-positive rate** | **1.4e-04** | **1.4e-04** |
| Observed per-window AUC | 0.693 | 0.707 |
| **Detection achievable there** | **0.18%** | **0.03%** |
| **AUC needed for 80% detection there** | **0.9992** | **0.9992** |

An AUC of 0.999 is not a detector that needs tuning. It is a different measurement problem. **The budget, as applied, demands near-perfect discrimination on every one of 720 decisions an hour.**

## The operating point was mis-specified

`0.1 false alarms per hour` was set as a usability requirement, and as a requirement on an *alarm* it is sensible — more than one spurious alert per ten hours would train a user to ignore it. The error was applying it to a system that re-decides every 5 seconds, which quietly converts a mild usability constraint into a demand for 0.9992 AUC.

A deployed monitor need not re-decide every 5 seconds. *"Should this session be flagged for a recalibration check?"* is a once-per-session question, and at that rate the false-positive budget per decision is four orders of magnitude looser.

### The same detector, judged once per session

| | T11 | T5 |
|---|---|---|
| Session-level AUC | 0.673 | 0.742 |
| Detection at 10% false-flag rate | 14.4% | 30.4% |
| Detection at 5% false-flag rate | 8.5% | 17.0% |
| AUC needed for 80% detection at 10% | 0.933 | 0.933 |

Aggregating to session level helps one participant and not the other (T5 0.707 → 0.742; T11 0.693 → 0.673), so it is **not** the rescue either — the disagreement between participants shows up here too. But it moves the problem from impossible to merely hard.

## The design target that follows

To flag 80% of degrading sessions while wrongly flagging 10% of healthy ones, a session-level AUC of about **0.93** is required. The current monitor achieves **0.67–0.74**.

That is a real gap and a specific one. It is the difference between *"this cannot work"* and *"this needs a measurement roughly this much better"*, and only the second is a research programme.

## What this does not license

Relaxing a target after failing to meet it is the classic way to manufacture a success, so the reasoning matters more than the number. The argument here is **not** that 0.1/h was too strict. It is that a per-hour alarm budget and a per-5-second decision rate are different quantities, and the design conflated them. The per-hour figure is unchanged; what changes is how many decisions it is divided among.

The honest headline stays as it was: **on this data, at the operating point the design specified, no configuration works.**
