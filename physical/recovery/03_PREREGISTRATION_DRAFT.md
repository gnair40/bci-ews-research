# Draft amendment: experiment P-8, recovery from the failure point

> **THIS IS A DRAFT. IT IS NOT FROZEN AND IT IS NOT PART OF THE
> PREREGISTRATION.**
>
> It was written on 14 November 2026 by the AI assistant at the researcher's
> request. Every prediction and every threshold below is a proposal. The
> researcher has not approved any of them. Section 5 lists the choices that
> are hers.
>
> `physical/docs/09_PREREGISTRATION.md` has not been edited. This text would
> be appended to it as a new numbered section, under the rule in its own
> section 9, only on her instruction.

---

## 1. What would be added

One experiment, **P-8**, analysed from the sessions of P-2, P-3 and P-5. No
session is added. The design is in `physical/recovery/02_DESIGN.md`, the code
in `physical/recovery/code/`.

**Data seen when this was drafted: none.** No bench exists. The only numbers
the code has produced came from formula-made rehearsal recordings, which were
deleted and are not evidence.

## 2. Hypothesis (draft)

> For at least one kind of fault, a repair that needs no knowledge of the true
> direction and starts at the failure point recovers decoding performance that
> would otherwise be lost, at a cost on fault-free recording smaller than the
> gain.

This is a claim about **recovery**. It is not a claim that decoding ends up
better than before the fault. That stronger claim is prediction PR-7, and the
draft predicts against it.

## 3. Predictions (draft)

Each names one repair for one fault in advance, so that a result cannot be
found by searching among the combinations. All read the reporting group, with
the repair started at the sealed onset and a 30-second adaptation period,
unless stated.

| Code | Prediction | Falsified if | Confidence when drafted |
|---|---|---|---|
| PR-1 | **RATE_LOSS, R1.** Renormalising recovers at least half the damage: median recovery fraction 0.5 or more | The median is below 0.5 and the upper end of its interval is below 0.5 | Moderate. A filter also makes the signal noisier, which renormalising cannot undo |
| PR-2 | **GAIN_DRIFT, R1.** The same: median recovery fraction 0.5 or more | As PR-1 | Moderate to high |
| PR-3 | **CHANNEL_DROPOUT, R3.** Masking and renormalising recovers a positive number of degrees: the interval for degrees recovered lies above 0 | The interval includes 0 or lies below it | Moderate |
| PR-4 | **CHANNEL_DROPOUT, R1 alone.** Renormalising without masking does not help: degrees recovered is 0 or negative | The interval lies above 0 | Low. It depends on how dark the covered channels are |
| PR-5 | **GEOMETRY_ROTATION, R1 to R3 (control).** None recovers anything: each interval for degrees recovered includes 0 | Any of the three lies above 0. That would point to an error in the analysis before it pointed to a finding | High |
| PR-6 | **Cost of a needless repair.** On fault-free sessions at the matched moment, no repair among R1 to R3 costs 10 degrees or more: the lower end of the interval for degrees recovered is above -10 | Any of the three has an interval reaching -10 or below | Moderate |
| PR-7 | **No enhancement.** For no repair and no fault type are most damaged sessions left better than before the fault: every Wilson interval for that share has its lower end below 0.5 | Any lower end is at or above 0.5. **This is the prediction the researcher's idea needs to see fail** | Moderate to high |

Reported without a prediction, because the draft has no honest basis for one:
how R4, with only 30 seconds of labelled data, compares with R1 to R3; how
recovery from the monitor's own warning compares with recovery from the
onset; the curve over adaptation periods of 10, 30 and 60 seconds; undesigned
faults.

## 4. Judging rule (draft)

For each fault type separately:

| Outcome | Condition |
|---|---|
| **Recovery shown** | The repair named for that fault in PR-1 to PR-3 recovers degrees with an interval above 0, **and** PR-6 holds for that repair |
| **Recovery not shown** | The interval includes 0 |
| **Repair harmful** | The interval lies below 0, or PR-6 fails for that repair |
| **Enhancement shown** | PR-7 is falsified for that fault type |

No single verdict is given for the experiment as a whole. Four fault types can
give four different answers, and that is the result.

## 5. Choices that are the researcher's

None of these has a right answer that the assistant can supply. Each was given
a default so that the code could be written and tested.

| # | Choice | Default in the draft | The alternative |
|---|---|---|---|
| 1 | Whether to add P-8 at all | Not added until she says so | Leave the frozen plan at seven experiments |
| 2 | Whether to freeze before the bench records | Assumed yes | Run it as exploratory and say so |
| 3 | The adaptation period | 30 s, one analysis window | 10 s or 60 s as primary |
| 4 | The rule for a lost channel | Below half of what the 75th-percentile channel kept | A different fraction or reference |
| 5 | The thresholds in PR-1, PR-2 and PR-6 | 0.5 of the damage; 10 degrees | Any others, set before data exist |
| 6 | Which repair is named for which fault | R1, R1, R3 | Other pairings |
| 7 | Whether to add an alignment repair for rotation | Not included | Add it as R5, with its own settings fixed in advance (see `01_RESEARCH.md`, row 5) |
| 8 | Whether PR-7 predicts for or against enhancement | Against | For. A prediction made against the evidence is allowed, and PP-7 of the frozen plan is one |
| 9 | Whether a live, self-repairing version is wanted later | Not designed | Design it after P-8 reports |

## 6. What the amendment would change in the frozen document

Under section 9 of the preregistration an amendment quotes the wording it
changes. The frozen document describes seven experiments and ten
predictions. The amendment would quote the lines that say so
and state that P-8 and PR-1 to PR-7 are added, that no session is added, that
nothing in P-1 to P-7 or PP-1 to PP-10 changes, and that the amendment was
made before any bench data existed. The amendment log in its section 12 would
be updated in the same commit, and `scripts/79_preregistration_freeze.py`
would be run to confirm that the log and the history agree.

## 7. If this is never frozen

Then P-8 may still be run, and its report already says at its head that the
analysis is exploratory and must be labelled so wherever it is quoted.
