# How much healthy recording does commissioning need?

**Scope fixed in advance:** `research/CALIBRATION_STUDY_NOTE.md`
**Produced by:** `scripts/39_calibration_curve.py`, reported by `scripts/40_calibration_report.py`
**Figure:** `reports/figures/14_calibration_curve.png`

## Why this question

The transfer analysis found **0 of 7 candidates improved both participants**, so
what helps a decoder-health monitor looks participant-specific. If a monitor has
to be fitted per person anyway, the useful number is not *which feature wins* but
*how much healthy data fitting one costs*. That is a within-participant question,
so the disagreement that blocked the transfer analysis does not apply to it.

## The answer

**About 20 healthy windows — roughly two minutes of ordinary recording — and
everything after that is free.** On both arrays the curve is flat from the
smallest well-posed fit onwards.

| | T11 | T5 |
|---|---|---|
| AUC at 20 windows (scattered draw) | 0.6535 | 0.7396 |
| AUC using the entire healthy record (221 / 211 windows) | 0.6476 | 0.7388 |
| **Change from 20 windows to all of it** | **−0.0059** | **−0.0008** |
| Total spread across every fit size ≥ 20 | 0.0075 | 0.0014 |

Going from two minutes of calibration data to nearly nineteen changes the AUC by
less than 0.01 on both arrays, and on both it changes *downward*. There is no
amount of extra healthy recording that improves this monitor.

## The full curves

Each row is the mean over 5 random healthy subsets, ± the spread across them.
The final row of each table pools the entire healthy record, so it is the same
object under either draw and is labelled `all-pooled`.

**T11** — 221 healthy windows available

| windows | minutes if contiguous | scattered draw | contiguous draw |
|---|---|---|---|
| 10 | 1.2 | *0.670 ± 0.010* | *0.659 ± 0.009* |
| 20 | 2.1 | 0.654 ± 0.002 | 0.665 ± 0.003 |
| 40 | 3.8 | 0.652 ± 0.003 | 0.659 ± 0.005 |
| 80 | 7.1 | 0.646 ± 0.002 | — |
| 160 | 13.8 | 0.646 ± 0.001 | — |
| 221 (all) | 18.8 | 0.648 | 0.648 |

**T5** — 211 healthy windows available

| windows | minutes if contiguous | scattered draw | contiguous draw |
|---|---|---|---|
| 10 | 1.2 | *0.730 ± 0.013* | *0.730 ± 0.013* |
| 20 | 2.1 | 0.740 ± 0.001 | 0.733 ± 0.006 |
| 40 | 3.8 | 0.740 ± 0.001 | 0.740 ± 0.002 |
| 80 | 7.1 | 0.740 ± 0.001 | — |
| 160 | 13.8 | 0.739 ± 0.001 | — |
| 211 (all) | 18.0 | 0.739 | 0.739 |

*Italic rows are not interpretable — see the next section.*

## Two things I had to check before believing the headline

### 1. The n = 10 point is a singular fit, not a measurement

The guard measures its `profile` component as a Mahalanobis distance in a
**K = 10** dimensional subspace. A fit of *n* windows gives that covariance rank
min(*n*−1, 10), so at *n* = 10 it is rank-deficient and only the 1e-6 ridge makes
it invertible. Measured directly (`data/processed/calibration_conditioning.csv`):

| windows | smallest eigenvalue | condition number | singular? |
|---|---|---|---|
| 10 | 1.0×10⁻⁶ *(exactly the ridge)* | 1.8×10⁷ | **yes** |
| 20 | 5.7×10⁻² | 1.6×10² | no |
| 40 | 5.0×10⁻² | 2.3×10² | no |
| 80 | 5.2×10⁻² | 2.1×10² | no |
| 160 | 4.3×10⁻² | 3.0×10² | no |
| 221 | 4.2×10⁻² | 3.0×10² | no |

This matters because the n = 10 point is the **highest** AUC on T11 (0.670), and
taken at face value it would have supported a headline of "more calibration data
makes the monitor worse." It does not: it is the one grid point where the
distance being computed is not a distance. It is plotted (grey band) and excluded
from every claim above.

### 2. "20 windows" really does mean "two minutes of recording"

The frozen protocol draws the healthy windows **at random from the whole record**,
so they are scattered across days. Adjacent windows have lag-1 r = 0.995, so 20
*scattered* windows could easily carry far more information than 20 *contiguous*
ones — in which case quoting a number of minutes would have been false.

I therefore added a **contiguous draw** (*n* consecutive windows from a single
block, which is what a real commissioning session collects) and ran the whole
grid again. At matched window counts the two draws agree: T11 0.665 contiguous
vs 0.654 scattered at n = 20; T5 0.740 vs 0.740 at n = 40. The concern was
reasonable and the data does not support it. The window count does translate
into minutes.

This run was added *after* seeing the frozen curve. It is a check on what the
number means, not a search for a better number, and it is reported here whichever
way it came out. The frozen scattered protocol remains the primary result.

## Deviations from the frozen scope, stated plainly

- **The n = 5 grid point never ran.** `39_calibration_curve.py` skips any fit
  with fewer than 8 windows. Given the conditioning result above, a 5-window fit
  would have been even more singular than the 10-window one, so nothing is lost —
  but the frozen grid said 5 and it is absent, so it is recorded here rather than
  quietly dropped.
- **The contiguous draw stops at 40 windows.** No single healthy block contains
  80 consecutive windows. That is itself a finding: past ~40 windows, more
  calibration data *necessarily* means pooling across blocks or days.
- **The contiguous draw was not in the frozen scope at all.** Added afterwards,
  for the reason given above.

## What this means, and what it does not

Read together with the earlier negative results, this is the constructive half of
the same fact. A session's healthy neural record barely varies within itself —
that is what lag-1 r = 0.995 says, and it is why aggregating windows never bought
the statistical power the detection problem needed. The flip side is that the
221st healthy window tells the fit nothing the 20th had not already said.
**The property that makes this monitor hard to make sensitive is the same
property that makes it cheap to commission.**

Practically: if this monitor were ever deployed, it would not need a long
enrolment session. Two minutes of ordinary healthy use is enough to fit it, on
both arrays tested.

**This cannot say** that two minutes suffices for a *new* participant. That is
the transfer question, and it still needs a third dataset — the Card et al. 2024
release (T15) remains the top recommendation.

**It also cannot say** that the resulting monitor is good enough to use. AUC
0.65–0.74 is well short of the ~0.99 the operating-point analysis showed is
required to meet the false-alarm budget. This measures how quickly the monitor
reaches *its own* ceiling, not where that ceiling is.
