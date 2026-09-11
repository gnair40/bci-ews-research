# Can the monitor know when not to be trusted?

**Scope fixed in advance:** `research/ABSTENTION_NOTE.md`
**Script:** `48_label_free_signals.py`

## Why this was asked

P5 found that the monitor's per-day AUC is predicted by that day's decoder error
(ρ = −0.720, p = 0.0055). I initially wrote that this makes abstention
straightforward, because decoder error is measurable online. **That was wrong,
and the correction is recorded in `reports/DAY_PREDICTORS.md`:** angular error is
measured against the user's *intended* direction, which exists here only because
these are task blocks with logged targets. In free use there is no target.

So abstention depends on a prior question: is there a signal computable from the
**decoder's output alone** that stands in for decoder error?

## The answer: no

Four candidates, all computed from the decoded velocity stream with no target, no
intent, and no label used at any point. Two stages, each Bonferroni-corrected at
0.0125.

**T11 (13 days)**

| candidate | vs decoder error | vs monitor AUC | verdict |
|---|---|---|---|
| L1 speed variability | −0.264 (p = 0.38) | −0.214 (p = 0.48) | no |
| L2 direction reversal rate | −0.401 (p = 0.17) | −0.165 (p = 0.59) | no |
| L3 output autocorrelation | +0.396 (p = 0.18) | +0.187 (p = 0.54) | no |
| L4 mean output speed | **+0.681 (p = 0.0103)** | −0.137 (p = 0.65) | stage 1 only |

**T5 (6 days)**

| candidate | vs decoder error | vs monitor AUC | verdict |
|---|---|---|---|
| L1 speed variability | −0.200 (p = 0.70) | −0.200 (p = 0.70) | no |
| L2 direction reversal rate | +0.771 (p = 0.07) | −0.714 (p = 0.11) | no |
| L3 output autocorrelation | −0.771 (p = 0.07) | +0.714 (p = 0.11) | no |
| L4 mean output speed | **−0.943 (p = 0.0048)** | +0.771 (p = 0.07) | stage 1 only |

**Nothing passes stage 2 on either participant.** No label-free signal predicts
whether the monitor will work on a given day, which is the only thing an
abstention rule needs to predict.

## The one thing that did pass stage 1, and why it is unusable anyway

L4 — mean output speed — tracks decoder error on **both** participants and clears
the corrected threshold on both. It is the strongest cross-participant agreement
in this entire project.

**And the signs are opposite.**

| | ρ (L4 vs decoder error) | reading |
|---|---|---|
| T11 | **+0.681** | faster output ⇒ *worse* decoding |
| T5 | **−0.943** | faster output ⇒ *better* decoding |

A relationship that reverses between two arrays cannot be made into a rule: any
threshold that abstains correctly on T11 abstains backwards on T5. This is the
participant-specificity the transfer analysis found, now visible in a single
statistic rather than inferred from seven failures.

It is also exactly why the scope note refused to predict signs for L1–L4. Had a
sign been guessed, one of these two participants would have "confirmed" it.

## Conclusion

**Abstention is an untested proposal, not a capability of this system.** The
scope note said in advance that this is what a null would mean, and it is
reported as such rather than reframed.

What survives is narrower and still worth stating: *the monitor's reliability
varies enormously by session and is predicted by decoder error* (P5), which is
measurable during the periodic assessment blocks a clinical BCI already runs —
just not continuously. An abstention rule built on assessment-block error is
therefore not ruled out by this result; it is simply not something this data can
test, because it would need the monitor and the assessment to be evaluated on
different sessions than the ones used to find the relationship.

## Limitations

- **13 days and 6 days.** Still |ρ| ≈ 0.68 to detect anything at n = 13. The
  stage-2 nulls mean underpowered, not disproved.
- **Four candidates, chosen by mechanism but not exhaustive.** A better
  label-free signal may exist; this shows that four reasonable ones do not work.
- **No signs were predicted**, as the scope note recorded, so the L4 stage-1
  result carries less evidential weight than P5's did — it was not risked in
  advance.
