# What makes a day good or bad for the monitor?

**Preregistered:** `research/DAY_PREDICTOR_PREREGISTRATION.md` — five predictors,
five predicted signs, Bonferroni threshold 0.01, all committed before anything
was computed.
**Scripts:** `46_day_predictors.py`, `47_p5_mediation.py`

## The result

**The monitor works on days when the decoder is working, and fails on days when
the decoder is already struggling.**

| # | Predictor | predicted sign | T11 ρ | p | verdict |
|---|---|---|---|---|---|
| P1 | Healthy dispersion | − | +0.203 | 0.51 | not significant |
| P2 | Mean firing rate | + | −0.319 | 0.29 | not significant |
| P3 | Active channels | + | +0.459 | 0.11 | not significant |
| P4 | Within-day drift | − | **+0.582** | 0.037 | **wrong sign**, not significant |
| **P5** | **Decoder error that day** | **−** | **−0.720** | **0.0055** | **supports the mechanism** |

*(Bonferroni threshold p < 0.01. All five reported, as the preregistration
requires.)*

T5 agrees in direction and size on P5 (ρ = −0.829) but at 6 days cannot clear the
threshold (p = 0.042). Every other predictor is null on T5 too, and P3 was not
computable there — all 6 sessions have the same active-channel count.

The relationship is stark at the extremes:

| T11 day | decoder error | monitor AUC |
|---|---|---|
| 800 | 42.5° | **0.97** |
| 658 | 33.6° | 0.88 |
| … | … | … |
| 770 | 80.1° | 0.48 |
| **783** | **89.3°** (chance is 90.7°) | **0.32** |

## The challenge it had to survive

The outcome is **itself defined by decoder performance**: the AUC compares
faulted episodes scored from fault onset until decoder error crosses the
deterioration threshold, against healthy episodes. On a day whose baseline error
is already near chance, episodes might cross almost immediately — leaving a
short early-warning window with few points — or the crossed/not-crossed split
might shift. Either would depress AUC on high-error days for reasons having
nothing to do with whether the monitor can see faults.

That challenge fails on T11:

| relationship | ρ | p |
|---|---|---|
| decoder error → fraction of episodes crossing | −0.300 | 0.32 |
| decoder error → mean early-warning window length | +0.148 | 0.63 |
| fraction crossing → AUC | +0.234 | 0.44 |
| early-warning window length → AUC | +0.198 | 0.52 |
| **decoder error → AUC, controlling for window length** | **−0.773** | **0.0032** |

None of the mediating links exist, and the partial correlation is *stronger* than
the raw one. The result is not an artefact of how the outcome is built.

On T5 the partial correlation points the same way (−0.698) but with 3 degrees of
freedom it means little (p = 0.19).

## What it means, and it is not good news

> **Partial retraction, 3 September.** The mechanism claim in this section is
> **withdrawn**. A later challenge (`reports/CEILING_CHALLENGE.md`) found a second
> variable — how *erratic* the decoder's output is that day — that predicts the
> monitor's accuracy exactly as well (ρ = −0.720, identical), correlates with
> decoder error at ρ = +0.813, and produces **identical** partial correlations in
> both directions (−0.333, p = 0.29). That symmetry means the two are collinear,
> not that one mediates the other: at 13 days this design **cannot say which
> property of the day is operative**.
>
> The *finding* below survives — the monitor's accuracy is strongly predicted by
> how badly the decoder is doing, and that has now withstood three separate
> challenges. What is withdrawn is the explanation of *why*. Read every
> "because" in this section as unestablished.
>
> One further caveat from the same challenge: the spurious-crossing rate — how
> often the deterioration threshold is cleared by noise alone, with no fault
> present — reaches 19.9% on day 783 and correlates with monitor AUC at
> ρ = −0.665. So part of the day-to-day spread is contaminated ground truth
> rather than detection. Not all of it: controlling for it leaves ρ = −0.613,
> p = 0.034.

The mechanism written down in advance was that a day the decoder handles badly is
atypical in ways that also hurt the monitor. That is consistent with the data but
is **not** established by it, for the reason above. The consequence is
uncomfortable either way:

> **The monitor is least reliable exactly when it would be most needed.**

A decoder-health monitor exists to warn during the periods when the decoder is
degrading. This one is near-perfect on good days (AUC 0.97) and *worse than
chance* on the worst day measured (0.32) — meaning its risk score ran backwards,
reading lower during faults than during healthy operation.

This is a more serious limitation than any of the earlier negative results,
because the earlier ones said "not sensitive enough yet". This one says the
failure is **correlated with the condition it is meant to detect**. A monitor
whose errors are independent of the hazard can be improved by making it more
sensitive; a monitor whose errors track the hazard cannot.

## What follows

It also points at something concrete this system could do: **abstain**. If a
session's difficulty can be recognised at the time, the monitor can report
"today is a day I cannot be trusted" instead of failing silently. A monitor that
knows when to stay quiet is a substantially more defensible object than one that
does not.

> **Correction, 2 September.** The first version of this section said decoder
> error is "measurable online, without labels, from the decoder's own output
> statistics." **That is wrong.** The angular error used as P5 is measured
> against the *intended* movement direction, which is known here only because
> these are recorded task blocks with logged targets. During free use there is no
> target and no intended direction, so this quantity cannot be computed. It is
> available during the assessment blocks a clinical BCI runs periodically, not
> continuously.
>
> Whether abstention is possible therefore depends on a question the first
> version skipped: **is there a label-free signal that stands in for decoder
> error?** That is tested in `reports/ABSTENTION.md` rather than assumed here.

## The predictor that came out backwards

P4 (within-day drift) was predicted negative — a day already drifting should mask
faults — and came out **+0.582**. It does not clear the corrected threshold, so
nothing is claimed from it either way, but the sign was committed in advance and
is reported as it fell. If anything it hints at the opposite mechanism: days with
more internal movement may simply be days with more happening to detect.

## Limitations

- **13 days, one participant.** The preregistration fixed the power limit before
  looking: at n = 13, |ρ| must reach ~0.68 to clear Bonferroni. P5 at −0.720 is
  the *only size of effect this design could have found*, and the four nulls mean
  "underpowered", not "no relationship".
- **T5 supports but cannot confirm** — 6 days, and its day-to-day variation is
  separately confounded with fault mix.
- **Correlational.** Nothing here shows that poor decoder performance *causes*
  poor monitor performance; a common cause — a session whose recording is simply
  messier — is at least as likely, and is in fact the mechanism that was
  predicted.
