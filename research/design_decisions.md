# Study Design Decisions

**Status:** Open. Nothing here has been decided.
**Written:** 25 August 2026, after Phase 1 (dataset characterisation) and
Phase 2 (detector validation) completed.
**Reproduce the numbers:** `python3 scripts/10_design_power_analysis.py`
**Companion page:** [Designing the Analysis](https://claude.ai/code/artifact/095081a8-01f7-47b9-a101-b69963e7ad7c)

---

## ⚠️ Correction to an earlier claim in this repository

An earlier analysis (`scripts/08_record_length_check.py`, and the "fast framing"
row it printed) concluded that treating the record as concatenated within-session
dynamics gives **16,144 correlation times** of data and therefore ample power.

**That number is real but answers the wrong question.** It compares the record
length against the correlation time of a *fast* observable (cursor velocity,
≈0.55 s). An early-warning test asks whether an indicator **trends upward across
time**, and the sample size for a trend test is the number of independent
observations of the **slow** variable — the thing drifting toward the transition.

Sampling more finely inside a block gives a more *precise* estimate at each point.
It does not give more *points*. `scripts/10_design_power_analysis.py` computes the
right quantity.

---

## 1. What actually limits the study

Kendall's τ is the trend statistic this literature uses (−1 = always falling,
0 = no trend, +1 = always rising). At small n it takes a large τ to reach
significance at all.

### Real sample sizes in this dataset

| Level | T11 | T5 |
|---|---|---|
| session (all) | 15 | 6 |
| session (pre-transition) | 11 | 3 |
| block (all) | 29 | 21 |
| **block (pre-transition)** | **21** | 9 |

"Pre-transition" uses the paper's own early/late boundaries: trial day 758 for
T11, 2133 for T5.

### Smallest detectable |τ|

| n | What it is | Smallest \|τ\| | Verdict |
|---|---|---|---|
| 3 | T5 sessions pre-transition | 1.000 | **no valid test** — α = 0.05 is unreachable with 3 points |
| 6 | T5 sessions, all | 0.733 | unusable |
| 9 | T5 blocks pre-transition | 0.500 | marginal |
| 11 | T11 sessions pre-transition | 0.455 | marginal |
| 15 | T11 sessions, all | 0.371 | marginal |
| **21** | **T11 blocks pre-transition** | **0.305** | **usable** |
| 29 | T11 blocks, all | 0.256 | usable |

### Power to detect a real trend

Effect = total rise across the record, in units of the indicator's own noise
standard deviation.

| n | 0.5 sd | 1 sd | 2 sd | 4 sd | 8 sd |
|---|---|---|---|---|---|
| 6 | 0.07 | 0.11 | 0.25 | 0.64 | 0.98 |
| 9 | 0.07 | 0.14 | 0.41 | 0.91 | 1.00 |
| 11 | 0.08 | 0.16 | 0.47 | 0.95 | 1.00 |
| 15 | 0.10 | 0.20 | 0.61 | 0.99 | 1.00 |
| **21** | 0.10 | 0.26 | **0.74** | 1.00 | 1.00 |
| 29 | 0.12 | 0.32 | 0.86 | 1.00 | 1.00 |

> **The most consequential fact on this page.** Moving from sessions to blocks
> takes T11's pre-transition sample from **11 to 21**, and moves the study from
> marginal to usable. Blocks are already separate recordings of a few minutes,
> and each still holds a median of 15,161 bins — so the indicator at each point
> stays precisely estimated. This is close to a free improvement.

---

## 2. Decision A — the analysis level

*What counts as one observation in the trend test.*

| Option | n (T11 pre-transition) | Assessment |
|---|---|---|
| Session | 11 | **Marginal.** Matches the intuition that degradation unfolds over months. Detects only \|τ\| ≥ 0.455. A null here could not be interpreted. |
| **Block** | **21** | **Recommended.** Nearly doubles the sample at no real cost. Caveat: blocks within a session are not fully independent — acknowledge it, and test it by comparing within-session against between-session variability. |
| Sliding window | 725 | **Misleading.** MINDFUL's 60 s / 10 s resolution. Adjacent windows overlap and come from the same block, so the *effective* sample stays near the block count. Fine for estimating the indicator smoothly; not a valid n for the trend test. |

---

## 3. Decision B — what "performance" means

Lower stakes than it appears, because the candidates already agree on the timing
and direction of the decline.

| Variable | Grain | Missing | For | Against |
|---|---|---|---|---|
| `angle_error_deg` | trial | 2.4% | What the paper uses — makes the benchmark direct | Already a median within each trial |
| `percent_correct` | block | 0% | Cleanest meaning; independent of angle error | One value per block only |
| `time_to_target` | trial | 2.4% | Direct measure of difficulty | Censored near 10 s — ceiling effect |
| `path_efficiency` | trial | 14.3% | Sensitive to control quality | Most missing data |

**Suggested:** angle error as primary, success rate as confirmation. They already
agree, so reporting both converts a single measurement into a robustness check at
no cost.

---

## 4. Decision C — what "deterioration" means

*The decision that determines whether this is a new result or a restatement.*

| Option | Assessment |
|---|---|
| **Discrete transition, located by change-point** | **Recommended.** T11 has a clean one: flat through day 751, then a step to ~120° error and ~25% correct at day 758, sustained. This gives a defined "before", which a lead-time claim requires. Locate it with a method, not by eye, and fix it *before* computing the indicator. |
| Crossing a fixed threshold | Workable. Simple and pre-registerable, and yields two events (T11 day 758, T5 day 2133). But the threshold is arbitrary and a critic will say so. |
| No event — continuous correlation | **Abandons the contribution.** Highest power, will almost certainly "work", and is structurally MINDFUL: a measure of current neural state correlating with current performance. The literature review names this threat explicitly — *"It's just MINDFUL with different statistics."* Without a defined "before" there is no lead time. |

---

## 5. Decision D — what T5 is for

T5 has 6 sessions and cannot carry a trend test of its own. The temptation is to
treat it as a weak replication. But consider what T5 actually does:

| Trial day | 2121 | 2126 | 2128 | 2133 | 2135 | 2149 |
|---|---|---|---|---|---|---|
| percent correct | 97.8 | 98.7 | 95.5 | 60.9 | **37.0** | **92.8** |

Performance falls to 37% and **returns to 93%** — and `scripts/05` showed that
recovery involved no change to the decoder (cosine similarity 0.621 at day 2149
against 0.620 at day 2135).

> **T5 is a built-in reversibility control on real data.** A genuine
> critical-slowing-down indicator should rise into the dip **and fall again** with
> the recovery. A detector responding merely to elapsed time, accumulated drift or
> nonstationarity will keep climbing through day 2149.
>
> This is a discriminating test no simulation can provide, and it costs nothing.

---

## 6. Combinations

### Design 1 — fine estimate, coarse test *(recommended primary)*

> block level (n = 21) · angle error + success rate · change-point event · T5 as reversibility control

Compute the indicator *within* each block, where thousands of bins make it
precise. Test whether it trends upward across the 21 blocks preceding T11's
day-758 transition. Then check whether it falls again across T5's recovery.

Separates the two roles cleanly: fine resolution buys precision, block count
provides the sample.

- Detects |τ| ≥ 0.305 · power 0.74 against a 2 sd rise
- Beats MINDFUL if the indicator rises *before* performance falls
- Main risk: blocks within a session are correlated

### Design 2 — the purist *(recommended as sensitivity check)*

> session level (n = 11) · angle error · change-point event

Most defensible conceptually, least powerful. Detects only |τ| ≥ 0.455.
Run alongside Design 1: agreement means the finding is robust to the choice;
disagreement is itself worth reporting.

### Design 3 — the one already published *(avoid as the primary claim)*

> window level (n = 725) · angle error · continuous correlation, no event

Enormous apparent sample, will produce a strong significant correlation, and is
structurally MINDFUL. Correct as the way to *reproduce the baseline* — already
done in `scripts/09` — but it is not the contribution.

### Design 4 — the pre-registered null *(recommended reporting stance)*

> Design 1, with the power analysis stated in advance and a null accepted as a result

Not a separate analysis; a decision about reporting. State beforehand that the
test has power 0.74 against a 2 sd rise at n = 21, and that a null will be
reported as a null rather than reworked until something appears.

This is what converts "we found nothing" into a bounded negative result against a
published comparator. The literature review's own words: a clean negative result
against a real comparator is *"far better than a mushy positive."*

---

## 7. Recommendation

**Design 1 as primary, Design 2 as sensitivity check, Design 4 as reporting
stance**, with the T5 reversibility test as the sharpest single piece of evidence.

Reasoning, in order of how much it matters:

1. **Block level is nearly free.** 11 → 21 pre-transition observations; |τ| ≥ 0.455 → ≥ 0.305. No other choice here buys as much.
2. **A defined event is non-negotiable.** No "before" means no lead time, and lead time is the entire contribution.
3. **The T5 test discriminates in a way simulation cannot.** Rising-then-falling with a real recovery is hard for a spurious nonstationarity detector to fake.
4. **Pre-registering power costs nothing now and is worth a lot later.** It is the difference between a null that ends the project and a null that *is* the result.

### Still to decide

- Whether angle error or success rate is the **declared** primary. Close to arbitrary; pick one and say so.
- **Where exactly the change point sits.** Must be located by a method, not by eye, and fixed before the indicator is computed.

> Nothing here is irreversible — the pipeline is validated and the data are local,
> so any of these designs runs in an afternoon. What *is* irreversible is looking
> at the answer first and choosing the design afterwards.

---

## 8. Provenance of these numbers

- Sample sizes read from `data/processed/blocks.csv` (main cohort only).
- Detection thresholds: exact Kendall τ null distributions for n ≤ 8, 20,000-permutation nulls above that.
- Power: 4,000 simulations per cell, α = 0.05, two-sided.
- At n = 3 the exact test cannot reach α = 0.05 at all (smallest attainable two-sided p is 1/3); the script flags this rather than reporting a meaningless power figure.
- Regenerate everything with `python3 scripts/10_design_power_analysis.py`.
