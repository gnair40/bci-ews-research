# On the days that matter most, the corpus cannot answer the question

**Predictions committed in advance:** the addendum to
`research/CEILING_CHALLENGE_NOTE.md`
**Script:** `51_unambiguous_episodes.py`

## The test

Keep only faulted episodes where the fault **demonstrably did real damage** —
achieved damage ≥ 10°, the crossing rule's own threshold, measured as a median
over post-onset windows rather than a single smoothed excursion. On those the
ground truth is unambiguous whatever the day's noise level. Then re-run the
decoder-error correlation on whatever days still have enough episodes to score.

The threshold was fixed in advance and **not** lowered when it turned out to
disqualify half the dataset.

## The result is not a yes or a no

**6 of 13 T11 days, and 5 of 6 T5 days, cannot be scored at all.**

| T11 day | unambiguous / faulted | AUC (all) | AUC (unambiguous only) |
|---|---|---|---|
| 658 | 13 / 19 | 0.879 | 0.888 |
| 675 | 7 / 24 | 0.906 | 0.893 |
| 692 | 12 / 25 | 0.887 | 0.917 |
| 702 | 12 / 18 | 0.456 | **0.467** |
| 715 | 8 / 24 | 0.554 | 0.643 |
| 758 | 5 / 8 | 0.685 | 0.776 |
| 800 | 5 / 23 | 0.974 | **1.000** |
| 665 | 20 / 29 | — | *unscoreable* |
| 672 | **0** / 22 | 0.722 | *unscoreable* |
| 689 | 1 / 10 | 0.564 | *unscoreable* |
| 709 | 4 / 21 | 0.706 | *unscoreable* |
| 751 | 1 / 15 | 0.648 | *unscoreable* |
| 770 | 4 / 15 | 0.482 | *unscoreable* |
| **783** | **1 / 20** | **0.319** | *unscoreable* |

And how many episodes a day retains is predicted by how badly the decoder is
doing on it: **ρ = −0.604, p = 0.029.**

> On day 783 — the worst day the monitor had, and therefore the single most
> important day to understand — exactly **one** of twenty injected faults did
> damage the performance metric could unambiguously see. On day 672, **none** did.

## What this means

**The question "does the monitor really fail on bad days, or do the labels just
get noisy there?" is not answerable with this corpus.** Not "answered no" —
*unanswerable*, because the days where it matters are precisely the days where
injected faults cannot produce measurable ground truth.

That is a limitation of the experimental design, not of the analysis, and it is
the most consequential thing in this report.

## What the surviving days do and do not show

Among the 7 scoreable T11 days the correlation drops to **ρ = −0.536, p = 0.215**.
That is *not* a refutation: at n = 7, |ρ| would have to reach about 0.79 to clear
p < 0.05, so this test has almost no power left after the filtering. It is
inconclusive in the strict sense.

What is suggestive, and no more than suggestive: **day 702 stays bad on clean
episodes** — 0.456 across all episodes, 0.467 on its 12 unambiguous ones. If the
day effect were purely contaminated labels, filtering to unambiguous faults should
have rescued it. It did not. Day 715 improves (0.554 → 0.643) and day 800 goes to
a perfect 1.000, so the picture is mixed.

My two predictions, scored honestly:

| Predicted | Outcome |
|---|---|
| the effect weakens substantially but does not vanish | **partly right** — it weakened to −0.536 and lost significance, but at n = 7 "lost significance" is not the same as "weakened" |
| the worst days lose most of their episodes | **right**, and strongly: ρ = −0.604, p = 0.029 |

## What a future attempt should change

This points at a concrete design fix rather than a vaguer "get more data".

The performance metric is **angular error against the intended direction**, which
saturates: chance is 90.7°, and a decoder already at 87.5° has nowhere left to go.
Every fault injected onto such a session is invisible to the ground truth by
construction.

A corpus meant to study monitoring on *bad* days needs a performance measure with
dynamic range at the bad end — something that still separates "poor" from
"catastrophic" once angular error has flattened out. Time-to-target, path
efficiency, or a directly decoded-trajectory measure would all keep resolving
where angle stops.

Without that, any study of this kind is structurally blind on exactly the sessions
it most needs to see.

## Limitations

- **7 days on T11, 1 on T5.** T5 retains a single scoreable day and can say
  nothing at all here.
- The 10° threshold is one choice. It is the crossing rule's own threshold, fixed
  before running, and deliberately not tuned — but a different corpus design, not
  a different threshold, is what this calls for.
- The retained episodes are not a random subset: they are the faults that
  happened to bite. Comparing their AUC to the full set mixes "cleaner labels"
  with "easier faults", and at this n the two cannot be separated either.
