# What "the decoder is failing" actually meant

**Status: EXPLORATORY.** Unlike P1–P5, the ceiling challenge and the
unambiguous-episode test, nothing here was preregistered. It began as a check on
a recommendation I had already published, found that check to be broken, and
ended somewhere I did not anticipate. Read every number as hypothesis-generating.

**Script:** `52_per_day_chance.py`

## Why I ran it

`reports/UNAMBIGUOUS_EPISODES.md` recommended that a future corpus use a
performance measure with more dynamic range at the bad end, because angular error
saturates near the 90.7° chance level. **That recommendation is only right if the
decoder still holds usable signal on those days.** If it is already
indistinguishable from chance, there is nothing left for a fault to destroy and no
change of metric recovers anything.

So I measured each day's decoder against **its own** chance level, using the same
shuffled-pairing procedure the reference decoder used.

## Two things wrong with my own check

**1. A statistic stored under a name that inverted it.** `mannwhitneyu` returns
U₁, the count of pairs where x exceeds y — so U₁/(nm) is P(error **exceeds**
chance). I stored it as `prob_better_than_chance`. A decoder 55° better than
chance was recorded as **0.273** and would have been read as its probability of
beating chance. Both directions are now written out.

**2. A per-day chance level that is not what it looks like.** Shuffled chance came
out between **47.7° and 102.7°** across days, where a chance level ought to sit
near 90°. The cause is task geometry: if a day's intended movements all point in
similar directions, shuffling the pairing barely changes anything, because
pointing the popular way already scores well.

Measured directly — the resultant length of each day's intended directions, 0 for
isotropic and 1 for all-one-way:

| T11 day | 675 | 658 | 672 | 692 | 751 | 689 | 702 | 709 | 715 | 727 | 800 | 770 | 783 | 758 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| concentration | 0.01 | 0.03 | 0.07 | 0.07 | 0.11 | 0.18 | 0.25 | 0.26 | 0.30 | 0.48 | 0.52 | 0.56 | 0.59 | **0.68** |

**Sessions differ by a factor of fifty in how directionally varied the task was.**
That was not known before and it affects every absolute error number in this
project.

## The finding that came out of fixing it

Absolute angular error predicts the monitor's accuracy strongly. **Error relative
to that day's own chance level does not.**

| T11 | ρ with monitor AUC | p |
|---|---|---|
| absolute decoder error (P5) | **−0.720** | **0.0055** |
| margin over that day's own chance | +0.264 | 0.38 |
| directional concentration | −0.516 | 0.071 |

The clearest single case:

| | decoder error | beats its own chance by | monitor AUC |
|---|---|---|---|
| **day 800** | 42.5° (looks excellent) | P(better) = **0.531** — barely | **0.974** |
| **day 658** | 33.6° | P(better) = 0.727 — comfortably | 0.878 |
| **day 783** | 89.3° (looks terrible) | P(better) = 0.533 — barely | 0.319 |

Days 800 and 783 beat their own chance by almost identical margins, and their
monitor accuracies are 0.974 and 0.319. Whatever separates them, it is not how
much real signal the decoder retains.

## What this does to the headline

The finding has been stated as *"the monitor fails when the decoder is already
failing."* In the sense that phrase naturally carries — **the decoder having lost
its signal — it is not supported.** Relative-to-chance decoder quality does not
predict monitor accuracy at all (+0.264, p = 0.38).

What is supported is narrower and less quotable: *the monitor's accuracy is
strongly associated with the day's absolute angular error*, a quantity that mixes
decoder quality with how directionally varied the task happened to be.

## Where this line of work terminates

Counting from the start of these session-level analyses, there are now **five**
day-level variables that correlate with monitor accuracy to varying degrees:

| variable | ρ with monitor AUC | p |
|---|---|---|
| absolute decoder error | −0.720 | 0.0055 |
| trace noise | −0.720 | 0.0055 |
| spurious-crossing rate | −0.665 | 0.013 |
| directional concentration | −0.516 | 0.071 |
| margin over own chance | +0.264 | 0.38 |

They are mutually entangled — decoder error and trace noise alone correlate at
0.813 — and there are thirteen days. **This design can establish that sessions
differ enormously and that the differences track "how well things were going that
day". It cannot identify which property is responsible, and no further
re-slicing of thirteen numbers will change that.**

That is the honest terminal statement, and continuing to test variables against
the same 13 points would be generating explanations rather than testing them.

## What would actually settle it

Sessions that break the entanglement — a decoder that is inaccurate but steady, or
noisy but accurate, or a task held at constant directional difficulty across
sessions. None of those exist in this data. A prospective recording could hold the
task fixed by design, which would separate task geometry from decoder health at
the source instead of trying to unpick them afterwards.

## Correction to the earlier recommendation

`reports/UNAMBIGUOUS_EPISODES.md` recommends a performance measure with dynamic
range at the bad end. That still holds — angular error genuinely does compress
near chance — but it was stated as though saturation were the whole problem. It is
not: **the saturation point itself moves between sessions**, because each day's
chance level depends on its task geometry. A better metric must be robust to that
too, or it will simply relocate the confound. The README limitation has been
amended.
