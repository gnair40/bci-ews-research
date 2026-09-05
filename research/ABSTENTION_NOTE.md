# Label-free abstention — scope fixed before running

**Written:** 2 September 2026, immediately after correcting the overclaim in
`reports/DAY_PREDICTORS.md`.

## The question, stated correctly this time

P5 showed that the monitor's per-day AUC is predicted by that day's decoder error
(ρ = −0.720, p = 0.0055 on T11). I first wrote that this makes abstention easy,
because decoder error is measurable online. **It is not.** Angular error is
measured against the user's *intended* direction, which exists in this dataset
only because these are task blocks with logged targets. In free use there is no
target.

So the real question is:

> **Is there a signal computable from the decoder's OUTPUT ALONE — no targets, no
> labels — that stands in for decoder error well enough to decide when the
> monitor should abstain?**

## The candidates, and why each might work

All are computed from the decoded velocity stream produced by the frozen decoder
on that day's real recording. **No target, no intent, no label is used.**

| | Signal | Reasoning |
|---|---|---|
| **L1** | **Output speed variability** — robust spread of decoded speed | A decoder reading a signal it no longer matches produces erratic output magnitude |
| **L2** | **Direction reversal rate** — how often decoded direction flips by more than 90° between consecutive bins | Real reaching is smooth. Rapid flipping is the signature of a decoder tracking noise |
| **L3** | **Output autocorrelation** — lag-1 correlation of the decoded velocity vector | A healthy decode is temporally smooth; a degraded one is closer to white noise |
| **L4** | **Mean output speed** | A decoder that has lost its signal may produce systematically smaller commands |

## Fixed in advance

| | |
|---|---|
| Stage 1 | each candidate vs **decoder error** across days — does it stand in for P5 at all? |
| Stage 2 | each candidate vs **monitor AUC** — does it predict the thing abstention needs to predict? |
| Test | Spearman, two-sided; Bonferroni 0.05/4 = **0.0125** within each stage |
| Reported | **all four, both stages, both participants**, whatever they show |
| Power | unchanged and still binding: n = 13 days, so \|ρ\| ≈ 0.68 is the detection limit |

**No direction is predicted for L1–L4** — unlike the P1–P5 preregistration, I
genuinely do not have a mechanism confident enough to commit a sign for each, and
inventing one to look rigorous would be worse than saying so. The consequence is
recorded: **a sign that emerges here carries less weight than P5's did**, because
it was not risked in advance.

## The decision rule this is for, specified before any number is seen

If a candidate passes both stages, abstention is: **the monitor stays silent on
sessions whose label-free signal falls in the region associated with high decoder
error.** The threshold would be set on the fit days and reported with the
resulting coverage (how many sessions are refused) alongside the accuracy on
those retained. **Coverage and accuracy are reported as a pair**, exactly as lead
time and false-alarm rate have been throughout — an abstaining monitor can always
look perfect by refusing almost everything.

## What a null would mean

That the abstention idea is not supported by anything measurable here, and it
should be described as an untested proposal rather than a capability. That is an
acceptable outcome and it will be reported as such.
