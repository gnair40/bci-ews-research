# How long does a commissioned monitor stay valid — and what actually moves it?

**Scope fixed in advance:** `research/STALENESS_STUDY_NOTE.md`
**Scripts:** `41_staleness_curve.py`, `42_staleness_report.py`,
`43_staleness_permutation.py`, `44_day_variance.py`, `45_pooling_loss.py`
**Figure:** `reports/figures/15_staleness_curve.png`

## The three answers

| Question | Answer |
|---|---|
| Does a monitor's fit go stale as it ages? | **No measurable effect** over 142 days. Point estimate −0.012 AUC per 100 days; permutation p = 0.128. |
| Does it matter which day you test on? | **Enormously.** AUC 0.32 to 0.97 across 13 sessions on T11. I² = 0.86. |
| Is the loss caused by mixing days together? | **No.** Pooling across days costs 0.003 AUC. That hypothesis is refuted. |

The headline is the middle row, and it was not the question I set out to ask.
**The age of a monitor's calibration is irrelevant; the identity of the day it is
used on decides almost everything.**

---

## 1. Staleness: no measurable ageing

Fit the guard on 40 healthy windows from one day, score episodes from another,
and measure AUC(A→B) − AUC(B→B) — each cross-day fit against the same-day fit on
the *same target day*, so that differences in how hard a day's episodes are
cannot be mistaken for staleness. T11 gives 95 forward day pairs spanning 3 to
142 days.

| | T11 | T5 |
|---|---|---|
| Forward pairs | 95 | 15 |
| Gap range | 3–142 days | 2–28 days |
| Mean AUC lost vs a same-day fit | −0.0088 | −0.0019 |
| Slope | −0.012 AUC / 100 days | −0.022 AUC / 100 days |
| **Permutation p** | **0.128** | **0.080** |

Both participants point the same way — the first time in this project that they
have agreed on the direction of anything — but neither reaches significance, and
the size is negligible: after **142 days**, the estimated cost of never refitting
is about **0.017 AUC**.

### The statistic that would have been wrong

The obvious test gives Spearman ρ = −0.301, **p = 0.003** on T11, which reads as
a clear result. It is not one. The 95 forward pairs come from only 15 sessions,
so every pair shares a source or a target day with many others; Spearman's
p-value assumes independent observations and that assumption fails badly here.

The right test permutes **which calendar date belongs to which session**, keeping
the measured AUC matrix exactly as it is. That destroys only the link between
elapsed time and performance while preserving the entire dependency structure —
which is precisely the null hypothesis of interest.

| | naive Spearman p | permutation p | understated by |
|---|---|---|---|
| T11 | 0.003 | **0.128** | 43× |
| T5 | 0.004 | **0.080** | 22× |

This is the same failure mode that has shaped the whole project. Within a session,
adjacent windows have lag-1 r = 0.995, and treating them as independent
*overstated* the power available for detection. Here, treating day pairs as
independent *understates* a p-value by more than fortyfold. **Same root cause,
opposite direction, and both would have produced a false claim.**

---

## 2. Day variance: the finding I did not go looking for

The same-day AUC — the monitor at its best, fitted and used on the same session —
varies enormously by session:

| T11 day | 658 | 672 | 675 | 689 | 692 | 702 | 709 | 715 | 751 | 758 | 770 | 783 | 800 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUC | 0.88 | 0.72 | 0.91 | 0.56 | 0.89 | 0.46 | 0.71 | 0.55 | 0.65 | 0.69 | 0.48 | **0.32** | **0.97** |

On day 800 the monitor is nearly perfect. On day 783 it is **worse than chance** —
its risk score is systematically *lower* during faults than during healthy
operation. Three of thirteen days sit below 0.5.

### It survives sampling noise

Each day's AUC rests on ~20 faulted and ~10 healthy episodes, so it carries a
bootstrap standard error near 0.10 on its own. That is not enough to explain the
spread:

| | T11 | T5 |
|---|---|---|
| Observed sd across days | 0.198 | 0.136 |
| Mean within-day sampling se | 0.100 | 0.071 |
| **Share of variance that is sampling** | **26%** | **27%** |
| Cochran's Q | 83.1 (df 12) | 23.0 (df 5) |
| I² | **0.86** | **0.78** |

Both participants agree, and by a wide margin.

### It does not survive equally on both participants

The 40 episodes drawn per day differ in fault mix, and a day that happened to
draw more performance-crossing faults is easier for reasons that have nothing to
do with the day. Controlling for that splits the two arrays:

| | Spearman(fraction of crossing-severity faults, AUC) | |
|---|---|---|
| T11 | ρ = **0.05**, p = 0.87 | mix explains nothing — the day effect stands |
| T5 | ρ = **0.886**, p = 0.019 | mix explains most of it — T5 cannot corroborate |

So the honest statement is: **on T11 the day-to-day swing is real and unexplained.
On T5 an ordinary confound accounts for it.** One array shows the effect; the
other cannot confirm it. That is where this stops until a third dataset exists.

---

## 3. Two hypotheses I tested and had to abandon

### Pooling across days is *not* what costs performance

The per-day analysis looked far better than every pooled number in this project,
which suggested that mixing days together dilutes the signal — an attractive idea
with an obvious fix. It is wrong. Holding the fit source and episode set
identical and varying only whether the comparison is made within or across days:

| | T11 | T5 |
|---|---|---|
| Mean within-day AUC | 0.675 | 0.798 |
| Pooled across all days | 0.672 | 0.782 |
| **Cost of pooling** | **0.003** | **0.016** |
| Pooled after per-day normalisation | 0.681 | 0.775 |

Pooling costs essentially nothing, and normalising per session recovers nothing
because there was nothing to recover. Reported because it was tested.

### The number that made it look otherwise was my own error

The apparent gap came from a statistic in `44_day_variance.py`: an
inverse-variance pooled AUC of **0.836** on T11, against an unweighted mean of
0.675. I nearly wrote that up as "the monitor is substantially better than every
earlier report said."

It is an artefact. **AUC is bounded in [0, 1], so its sampling variance shrinks
toward the bounds** — which means 1/se² weighting systematically over-weights
exactly the days with the most extreme AUCs. Measured:

| | Spearman(&#124;AUC − 0.5&#124;, se) | weight ratio max/min |
|---|---|---|
| T11 | **−0.913** | 31× |
| T5 | **−0.943** | 12× |

Day 800 (AUC 0.974, se 0.030) received 31 times the weight of day 702 (AUC 0.456,
se 0.170) purely because near-perfect AUCs have small standard errors. The
statistic is now labelled `..._BIASED_DO_NOT_QUOTE` in the output with the
reasoning attached, and the unweighted mean is the performance figure.

Cochran's Q is built from the same weights, so **its p-value is approximate for
the same reason**. The conclusion does not rest on it: the model-free comparison
(observed sd 0.198 vs mean within-day se 0.100) uses no weighting and agrees.

---

## What this changes

For most of this project the question has been *which detector, which feature,
which combination* — and the answer has been a null every time. The day-variance
result says those searches may have been aimed at the wrong axis. The spread
across sessions on one participant (0.32 to 0.97) is **larger than the entire
range any feature or combination ever moved the pooled number**, and it was
invisible in the pooled analyses because pooling averages it away.

The next question is therefore not "which feature is best" but **"what makes day
800 different from day 783?"** — a question this dataset can be asked directly,
and one nobody has asked because the pooled framing hid it.

## Limitations, stated flatly

- **13 days on one participant.** Individual days carry wide confidence
  intervals (day 783: [0.13, 0.55]). The *spread* is well supported; any single
  day's value is not.
- **T5 cannot corroborate** — its day effect is confounded with fault mix, and it
  has only 6 sessions over 28 days.
- **40 episodes per day**, a fixed random draw. A different draw would move
  individual days.
- **None of this makes the monitor deployable.** The gates still fail, and the
  ~0.99 AUC the false-alarm budget demands is still out of reach on most days.
  What changed is where the remaining variance lives.
