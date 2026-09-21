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

A deployed monitor need not re-decide every 5 seconds. *"Should this session be flagged for a recalibration check?"* is a once-per-session question, and at that rate the per-decision budget is looser by exactly the pooling factor — the number of windows in an episode, **55** on T11 — which is about 1.7 orders of magnitude.

> **Corrected 20 September 2026.** This paragraph used to say "four orders of magnitude looser". It is not: the looseness is the pooling factor and nothing else, and four orders would need one decision per fourteen hours. The figure is now computed from the data rather than asserted.

### The same detector, judged once per session

| | T11 | T5 |
|---|---|---|
| Session-level AUC | 0.673 | 0.742 |
| Detection at 10% false-flag rate | 14.4% | 30.4% |
| Detection at 5% false-flag rate | 8.5% | 17.0% |
| Episode length (minutes) | 4.6 | 3.5 |
| Decisions per hour at that rate | 13.1 | 17.1 |
| AUC needed for 80% detection at 10% | 0.933 | 0.933 |
| **False alarms/hour that 10% implies** | **1.31** | **1.71** |
| **Per-decision FPR the 0.1/h budget allows** | **0.0076** | **0.0058** |
| **AUC needed for 80% detection at the budget** | **0.990** | **0.991** |

Aggregating to session level helps one participant and not the other (T5 0.707 → 0.742; T11 0.693 → 0.673), so it is **not** the rescue either — the disagreement between participants shows up here too.

### Two targets, and which one the budget actually implies

> **Corrected 20 September 2026.** Earlier versions of this report gave **0.933** as *the* session-level design target. That number answers "what AUC gives 80% detection at a **10%** false-flag rate?" — and the 10% was a round figure that appears nowhere in the design. It is not the budget.

At one decision per 4.6-minute episode, flagging 10% of healthy episodes is **1.31 false alarms an hour** — about 13 times the 0.1/hour budget this project set and never relaxed.

| Question | Target AUC | What it costs in false alarms |
|---|---|---|
| 80% detection at a 10% false-flag rate | 0.933 | 1.31/hour |
| 80% detection **inside the 0.1/hour budget** | **0.990** | 0.1/hour |

So the honest statement is: deciding once per episode moves the requirement from **0.9992 to 0.990**, not from 0.9992 to 0.933. That is a real reduction and the direction of the argument survives — but against an observed **0.673 and 0.742** the gap stays very large, and describing it as "merely hard" was premature.

## The design target that follows

To flag 80% of degrading sessions **while staying inside the 0.1/hour budget**, a session-level AUC of about **0.990** is required. The current monitor achieves **0.67–0.74**.

That is a real gap and a specific one, and it is larger than this report previously said. It is still the difference between *"this cannot work"* and *"this needs a measurement roughly this much better"* — but the second is now a harder programme than the 0.933 figure implied.

The 10% figure is kept in the table above rather than deleted, because it is a legitimate answer to a different question and because removing it would hide the mistake instead of correcting it.

`reports/SESSION_MONITOR_DESIGN.md` and `reports/COMBINATION_STUDY_RESULT.md` were regenerated against the corrected target on the same day, and both now read it from this script's output rather than holding it as a hand-copied literal. `research/RIG_PREREGISTRATION.md`, `research/BUILD_MANUAL.md` and `research/EXPERIMENTAL_PROCEDURES.md` still quote 0.933; they are superseded documents, kept unchanged as the record, and each carries a banner saying so.

## What this does not license

Relaxing a target after failing to meet it is the classic way to manufacture a success, so the reasoning matters more than the number. The argument here is **not** that 0.1/h was too strict. It is that a per-hour alarm budget and a per-5-second decision rate are different quantities, and the design conflated them. The per-hour figure is unchanged; what changes is how many decisions it is divided among.

The honest headline stays as it was: **on this data, at the operating point the design specified, no configuration works.**
