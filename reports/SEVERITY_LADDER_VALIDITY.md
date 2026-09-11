# Does "severity" mean the same thing on every session?

**Prediction committed in advance:** addendum 2 of
`research/CEILING_CHALLENGE_NOTE.md`
**Script:** `53_severity_ladder.py`

## Why this is a question about the corpus

Every benchmark in this project treats fault severity as a **controlled
variable** with three ordered levels — `benign`, `sub`, `crossing` — calibrated
once, globally, in `17_fault_injector.py`. The ceiling result showed achieved
damage ranging from +19.8° on one session to +0.4° on another, which raises the
obvious question: do those three labels still describe three ordered things on
each individual session?

A cell is one (session × fault mode). It is **monotone** when median achieved
damage strictly increases benign → sub → crossing. All 60 T11 cells and all 24
T5 cells had enough episodes to measure; none were dropped.

## The answer: about half the time

| | T11 | T5 |
|---|---|---|
| Cells measured | 60 | 24 |
| Monotone | 34 | 16 |
| **Not monotone** | **26** | **8** |
| **Monotone fraction** | **0.567** | **0.667** |

And it degrades with the session's baseline error, **on both participants,
significantly, with the same sign** — the first time in this project that has
happened:

| | ρ (baseline error vs monotone fraction) | p |
|---|---|---|
| T11 | **−0.677** | **0.0055** |
| T5 | **−0.926** | **0.0080** |

Three T11 sessions (665, 658, 692 — the three lowest-baseline days) are monotone
in all four fault modes. Two (689, 758) are monotone in **none**.

## What the prediction got right and wrong

**Right:** the ladder holds on low-baseline sessions and collapses on
high-baseline ones. That was the substantive prediction and it is confirmed
twice.

**Wrong in the specifics:** I named days 783 and 672 as the likely worst. Day 783
is in the worst tier (0.25) but **day 672 is fine at 0.75**, and the two total
failures are days **689 and 758**.

Day 758 is the informative one: its baseline is only 58.2°, mid-range, so a pure
headroom story does not explain it. It has by far the **highest directional
concentration of any session (0.679)** — the task that day was the least
directionally varied of all fifteen.

On T11 concentration predicts the monotone fraction nearly as well as baseline
does (ρ = −0.641, p = 0.010 against −0.677, p = 0.006). On T5 it does not
(−0.463, p = 0.36). **These are the same two entangled variables from
`WHAT_DECODER_ERROR_MEANS.md`, and this study cannot separate them either.** The
robust statement is the baseline one, which replicates.

## The fault modes disagree between participants

| monotone fraction | T11 | T5 |
|---|---|---|
| CHANNEL_DROPOUT | **0.467** (worst) | **1.000** (perfect) |
| GAIN_DRIFT | 0.533 | 0.667 |
| GEOMETRY_ROTATION | 0.600 | 0.500 |
| RATE_LOSS | **0.667** (best) | **0.500** (worst) |

The worst mode on one array is the best on the other. No claim about which fault
type is hardest to calibrate survives both participants, and none is made.

## What this does and does not invalidate

**Does not:** the headline benchmark results. "0 of 48 configurations pass the
gates", the AUC figures, and the operating-point bound all pool across sessions
and severities, and the global calibration does hold *on average* — that is what
it was calibrated to do.

**Does:** any claim that stratifies by severity **within** a session, and any
reading of a per-session result that assumes the three levels were comparably
spaced there. On 43% of T11 cells they were not.

This is an internal-validity limitation of the corpus that had been assumed away
throughout, and it is now measured.

## What follows for a future corpus

Severity should be calibrated **per session**, against that session's own
achievable damage range, rather than once globally. A fault labelled "crossing"
should be one that crosses the threshold *on the session it is injected into* —
which requires measuring each session's headroom before choosing severities for
it, instead of after.

That is the second concrete design change this line of work has produced, and it
is independent of the first (a performance metric with range at the bad end and
robustness to task geometry).

## Limitations

- **Monotonicity is a coarse test.** Three ordered medians either increase or
  they do not; a cell that fails by 0.1° counts the same as one that fails by 10°.
  A graded measure would be more sensitive but needs a threshold choice this
  study deliberately avoided.
- 15 and 6 sessions. The *replication* of the baseline relationship across two
  arrays is what carries this, not either number alone.
- Baseline error and directional concentration remain entangled, as everywhere
  else in this dataset.
