# Defining Deterioration — comparison and proposed preregistration

**Status: PROPOSED. Not frozen. Awaiting your approval.**
**Written:** 25 August 2026, before any early-warning indicator has been computed.
**Evidence:** `scripts/11_define_deterioration.py` → `data/processed/deterioration_candidates.csv`

> **What has and has not been done.** Every number in this document comes from
> *behavioural performance only* — angle error and success rate. No neural
> feature has been read for this purpose and **no early-warning indicator has
> been computed on the real data.** Nothing here was chosen because it makes an
> early-warning result look better; that result does not exist yet.

---

## 1. The evidence: where each method lands

`scripts/11_define_deterioration.py` applies every candidate to both
participants, at block and session level, on both performance variables.

### T11

| Level | Variable | Least-squares | CUSUM | Rank scan | Baseline+persist | Change exists? |
|---|---|---|---|---|---|---|
| Session | angle error | **day 758** | **day 758** | **day 758** | day 715 | p = 0.0018 |
| Session | success | **day 758** | **day 758** | **day 758** | day 702 | p = 0.0014 |
| Block | angle error | day 758 | day 758 | day 715 | day 689 | p = 0.0002 |
| Block | success | day 758 | day 727 | day 758 | day 702 | p = 0.0002 |

### T5

| Level | Variable | Least-squares | CUSUM | Rank scan | Baseline+persist | Change exists? |
|---|---|---|---|---|---|---|
| Session | angle error | day 2133 | day 2133 | day 2133 | none | p = 0.071 |
| Session | success | day 2133 | day 2133 | day 2133 | none | p = 0.071 |
| Block | angle error | day 2133 | day 2133 | day 2133 | day 2133 | p = 0.059 |
| Block | success | day 2133 | day 2133 | day 2133 | day 2133 | p = 0.046 |

**At T11 session level, three independent data-driven methods agree on day 758 on
both performance variables — four independent convergences on the same
boundary.** That agreement is the central result of this document: the change
point is a property of the data, not a choice.

---

## 2. Two structural facts the series revealed

### 2.1 T11's "before" period is not a flat healthy baseline

| Trial day | 658 | 665 | 672 | 675 | 689 | 692 | 702 | 709 | 715 | 727 | **751** | 758 | 770 | 783 | 800 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| angle error | 22.6 | 19.1 | 22.9 | 18.5 | 33.6 | 22.6 | 25.5 | 24.0 | 36.2 | **64.7** | **21.8** | 121.4 | 101.9 | 111.5 | 95.7 |
| success % | 94.7 | 100 | 100 | 96.2 | 98.1 | 100 | 85.8 | 92.2 | 87.5 | **56.5** | **100** | 25.5 | 41.4 | 31.9 | 31.9 |

Performance wobbles upward from about day 689, spikes badly at **day 727**
(56.5% correct), **returns completely to baseline at day 751 (100% correct)**,
and only then collapses permanently at day 758.

> This matters for interpretation, and it is why the baseline+persistence rule
> fires early (day 689–715): it is detecting the onset of *instability*, which is
> a different event from the *transition*. Both are real. They are not the same
> thing, and a study must say which one it is testing.

**A note for later, flagged and deliberately not acted on:** alternating between
a good and a bad state before a permanent shift is called **flickering**, and it
is itself a recognised early-warning phenomenon in this literature. If you ever
want to use it, it must be preregistered as an indicator *in advance* — it cannot
be adopted after seeing that it happens to work here.

### 2.2 T5 is not a single change point

Model comparison on T5 (block level, angle error, BIC — lower is better):

| Model | SSE | BIC |
|---|---|---|
| No change point | 9398.3 | 134.27 |
| One change point (day 2133) | 6170.9 | 131.52 |
| **Two change points (2133 and 2149)** | **3342.8** | **124.74** |

The best-supported description of T5 is **down at day 2133, back up at day
2149** — a reversible excursion, not a transition. A single-change-point model
mischaracterises it, and that is precisely why T5's change point is only
marginally significant (p = 0.046–0.071).

---

## 3. Candidate methods compared

### Method 1 — Change-point detection on angle error

**What it means.** Try every possible place to cut the series in two. For each
cut, measure how much the values scatter around their own segment's average. The
best cut is the one leaving the least leftover scatter — the point at which the
series separates most cleanly into "before" and "after".

**How it would be applied.** Median angle error per session for T11 (15 values).
Exhaustive search over all valid split points, requiring at least 3 observations
on each side. Significance by shuffling the values 5,000 times and re-finding the
best cut each time.

**Assumptions.** One change, in the mean; roughly constant scatter within each
segment; observations ordered in time.

**Strengths.** No tuning parameters — nothing to adjust toward a preferred
answer. Standard and recognisable. Gives an exact, reportable date. Comes with a
significance test for whether a change exists at all.

**Weaknesses.** Assumes a single change, which we now know understates T11's
structure (there is an earlier destabilisation). Uses the whole series, including
data after the event.

**Circularity risk: none.** The event is located from behaviour; the indicator
will be computed from neural features. Different data, different signals.

**Noise/outliers.** Moderately vulnerable — squared error gives a wild point
extra influence. Here the change is so large (SSE falls 88%, from 39,908 to
4,580) that no single point could move it.

**Clear "before"?** Yes — the defining strength. 11 sessions / 21 blocks.

**Small-n appropriate?** Yes at n = 15. The permutation test is exact-in-spirit
and does not rely on large-sample approximations.

**ISEF-defensible?** Yes, and strongly so *because three methods agree*.

---

### Method 2 — Change-point detection on success rate

**What it means.** Identical machinery, applied to percent-correct instead.

**How it would be applied.** Mean `percent_correct` per session. Same procedure.

**Assumptions.** Same, plus that a proportion behaves enough like a continuous
measure — reasonable here, since values span 25–100% and avoid the extremes
where that breaks down.

**Strengths.** Success rate is recorded independently by the dataset authors and
is not derived from angle error, so agreement between the two is genuine
corroboration rather than restatement.

**Weaknesses.** One value per block only — no within-block variation to draw on.

**Circularity risk: none.** Same reasoning as Method 1.

**Noise/outliers.** Slightly more robust in practice, being bounded 0–100.

**Clear "before"?** Yes, and it lands in the same place.

**Small-n appropriate?** Yes.

**ISEF-defensible?** Yes — best used as the confirmation, not the primary.

---

### Method 3 — A predefined performance threshold

**What it means.** Declare a fixed cutoff in advance ("deterioration = angle
error above 90°" or "success below 50%") and take the first crossing.

**How it would be applied.** Fix the number before looking, then find the first
session that crosses it.

**Assumptions.** That a universally meaningful cutoff exists.

**Strengths.** Maximally transparent and trivially preregisterable. No
data-driven fitting whatsoever.

**Weaknesses.** The number is arbitrary, and a reviewer will say so. Worse, it is
not comparable across participants: T11 and T5 operate at different baselines
(T11 ≈ 20° when healthy, T5 ≈ 30°), so one cutoff cannot mean the same thing for
both. It also ignores persistence entirely — T11's day-727 spike would trigger a
90° rule under some choices, even though performance fully recovers at day 751.

**Circularity risk: none**, provided the number is genuinely fixed in advance.

**Noise/outliers.** Highly vulnerable — a single bad session triggers it.

**Clear "before"?** Yes, but possibly the wrong "before" if a transient trips it.

**Small-n appropriate?** Yes, though it wastes information.

**ISEF-defensible?** Only weakly on its own. The obvious question — "why 90?" —
has no good answer.

---

### Method 4 — A sustained decline over multiple blocks/sessions

**What it means.** Require performance to get worse and *stay* worse for a stated
number of consecutive observations, ignoring one-off bad sessions.

**How it would be applied.** Fix a run length (say 2 or 3), then find the first
run of that many consecutive degraded observations.

**Assumptions.** That "degraded" can be defined, which pushes the problem back to
Method 3 or Method 5.

**Strengths.** Directly encodes the idea that a real transition persists, which
is scientifically the right instinct. Immune to isolated spikes.

**Weaknesses.** Not a complete method on its own — "declining" still needs
defining. Run length is another free parameter.

**Circularity risk: none.**

**Noise/outliers.** Robust, by construction.

**Clear "before"?** Yes.

**Small-n appropriate?** Yes, but each observation consumed by the persistence
requirement shortens the usable "before".

**ISEF-defensible?** Yes as a component. Incomplete alone.

---

### Method 5 — Magnitude + persistence, anchored to the participant's own baseline

**What it means.** Define "normal" from that participant's own early sessions,
then call it deterioration when performance is worse than normal by a stated
margin *and* stays worse.

**How it would be applied.** Baseline = the first 6 observations. Limit = baseline
mean + 2 standard deviations (for angle error). Onset = first observation past the
limit with the next one also past it.

**Assumptions.** The early period is genuinely representative of "healthy"; the
margin and run length are chosen sensibly.

**Strengths.** *The rule can be written down having seen only the early data.*
This is its outstanding property: it cannot possibly be tuned to a collapse that
has not been looked at. It is participant-relative, so it means the same thing
for T11 and T5. It combines magnitude with persistence, which is the right shape
for the concept.

**Weaknesses.** Three free parameters (baseline length, margin, run length).
Empirically here it fires at **day 689–715 for T11** — much earlier than the
change-point methods — because it detects the *onset of instability* rather than
the transition. That is not a malfunction; it is a different definition of the
event, and it produces a shorter and more ambiguous "before" (the period it marks
as deteriorated includes day 751, at 100% correct).

**Circularity risk: none**, and the lowest hindsight risk of any method here.

**Noise/outliers.** Robust via the persistence requirement.

**Clear "before"?** Yes but short, and the "after" is not homogeneous.

**Small-n appropriate?** Yes.

**ISEF-defensible?** Yes — genuinely strong. Its weakness is that it answers a
slightly different question than the one this project asks.

---

### Method 6 — Two-segment vs three-segment model comparison *(additional)*

**What it means.** Rather than assuming one change, ask the data how many changes
are best supported, penalising extra changes so the model cannot simply add them
to fit noise (this is what BIC does).

**How it would be applied.** Compare no-change, one-change and two-change models
by BIC on each participant.

**Strengths.** Tests an assumption every other method makes silently. It is what
revealed that T5 is down-then-up and that T11 has an earlier destabilisation.

**Weaknesses.** Not a definition of deterioration by itself — a diagnostic.

**Circularity risk: none.**

**ISEF-defensible?** Yes, and it demonstrates exactly the kind of assumption-
checking that distinguishes careful work.

---

## 3b. Why the *destabilization* is not the event — considered and rejected

A natural objection: *this project is about early warning, so shouldn't the event
be the moment things start destabilising (≈ day 689–715) rather than the collapse
(day 758)?* It was considered seriously and rejected, for three reasons.

### Reason 1 — the destabilization IS the early-warning signal

Rising variance, wobbling, and flickering between good and bad states are exactly
what critical slowing down predicts as the **precursor**. Making them the event
promotes the warning into the thing needing warning, and then a *new* warning is
required before it — and the period before day 689 is flat and healthy, so there
is nothing there to find.

```
warning : destabilization  (~day 689–751)
event   : collapse          (day 758)
lead    : the quantity being measured
```

### Reason 2 — its date is not determined

The threshold rule has three parameters someone must choose. Running all 24
combinations (`scripts/11_define_deterioration.py --sensitivity`):

| Onset | Frequency |
|---|---|
| day 689 | 12 / 24 |
| day 715 | 10 / 24 |
| day 709 | 2 / 24 |

**The date swings 26 days depending on whether 2 or 3 consecutive degraded blocks
are required.** A date that moves that much with its own parameters is a property
of the choice, not of the data — and a study should not be built on it.

The per-session tests look stronger than they are:

| Trial day | mean AE | p | smallest p possible at this n |
|---|---|---|---|
| 689 | 34.1 | 0.0444 | **0.0444** |
| 715 | 36.2 | 0.0444 | **0.0444** |
| 727 | 59.4 | 0.0444 | **0.0444** |
| 758 | 121.4 | 0.0444 | **0.0444** |

Every "significant" session sits exactly at the floor. With 8 baseline blocks
against 2, 0.0444 is the smallest value the test can return — it means "completely
separated", which is easy at n = 2, and carries no information about how large the
effect is. Identical p-values across very different effect sizes are the signature
of that floor.

By contrast the day-758 boundary is agreed by three independent methods on two
independent variables at **p = 0.0018**, with no parameters to choose.

### Reason 3 — it costs most of the sample

| Event | Blocks before it | Smallest detectable \|τ\| | Verdict |
|---|---|---|---|
| day 689 | 8 | ≈ 0.57 | unusable |
| day 715 | 16 | ≈ 0.36 | marginal |
| **day 758** | **21** | **0.305** | **usable** |

### But the objection contains a real point, and it is now tested — see §6, C2

The sharp form of the worry is not about which date to pick. It is: *if the
destabilization was already visible in behaviour, what does the neural signal
add?* A clinician watching performance would notice trouble around day 689–715.
An indicator that only fires at day 750 predicts a collapse that was already
obvious.

That deserves its own test, and it is added to the preregistration as a
prespecified secondary outcome (§6, C2). The destabilization becomes a
**comparator**, not the target.


## 4. Hindsight bias — the honest treatment

**The circularity that would matter is absent.** The event is defined from
behavioural performance; the early-warning indicator will be computed from neural
features. Different measurements. MINDFUL established that the two are correlated
*contemporaneously* — that is precisely why the interesting question is whether
the neural indicator moves **earlier**, and defining the event behaviourally is
the correct way to ask it.

**Data-driven location is unavoidable, and that is acceptable if handled openly.**
Any purely a-priori threshold is arbitrary; any data-driven method uses the data.
The way to make data-driven location defensible is:

1. **Fix the procedure before running it.** Done — the method, level, variable,
   minimum segment size and significance test were specified before execution.
2. **Use a method with no tuning knobs.** Least-squares single change point has
   none. There is nothing to adjust toward a preferred answer.
3. **Require independent methods to agree.** Three do, on two variables. A single
   researcher choice cannot produce fourfold convergence.
4. **Freeze the result in the repository before any indicator is computed**, with
   the commit recorded, so the ordering is verifiable rather than asserted.
5. **Report every method's answer, including the disagreements** — the block-level
   disagreements and the earlier threshold firings are in §1 and §2, not hidden.

**The residual risk, stated plainly.** I have now seen the performance series;
that was unavoidable, because characterising the dataset required plotting
performance. What protects the analysis is that the boundary was set by an
algorithm rather than by judgement, that the algorithm was specified in advance,
and that **no early-warning indicator has been computed, so there is nothing yet
to tune toward.** This is the point at which freezing has maximum value, and it
is why it should happen now.

---

## 5. T11 primary, T5 secondary — is it justified?

**Yes, and on four independent grounds, none of which is "it works better".**

| Criterion | T11 | T5 |
|---|---|---|
| Change point statistically established | **p = 0.0014–0.0018** | p = 0.046–0.071 (marginal / n.s.) |
| Pre-transition observations | **21 blocks / 11 sessions** | 9 blocks / **3 sessions** |
| Valid trend test at session level | yes (n = 11) | **no** — at n = 3 no test can reach α = 0.05 |
| Single-transition model appropriate | yes (dominant, SSE −88%) | **no** — BIC favours down-then-up |

T5 fails the primary role on the merits: its transition is not statistically
established, it has too few pre-transition observations to support a trend test,
and it is not a transition at all but a reversible excursion.

**But it is exactly that last failure that makes T5 valuable.** Performance falls
to 37% and returns to 93%, with no change to the decoder. A genuine
critical-slowing-down indicator should rise into the dip **and fall again** with
the recovery; an indicator responding merely to elapsed time or accumulated drift
will keep climbing. That is a discriminating test no simulation can provide.

**One addition to your proposal.** T11 *also* contains a reversible excursion —
day 727 degrades to 56.5% and day 751 returns to 100% — so the reversibility test
can be run **within T11 as well**, on the same participant that carries the
primary analysis. That is stronger than relying on T5 alone, and it costs nothing.

---

## 6. Proposed preregistration — the exact procedure to freeze

### A. PRIMARY deterioration definition

| Item | Fixed value |
|---|---|
| **Participant** | T11 |
| **Variable** | Median angle error per session (`angle_error_deg`, median over trials) |
| **Level for LOCATING the change point** | **Session** (15 observations) |
| **Level for the ANALYSIS** | **Block** (all blocks before the boundary) |
| **Method** | Single change point, exhaustive least-squares split |
| **Minimum segment size** | 3 observations each side |
| **Excluded data** | `T11(additional)` cohort; trials flagged `excluded` are retained in the median but reported both ways |
| **Significance test** | 5,000-permutation test; the change point is only used if p < 0.05 |
| **Result** | **Boundary at trial day 758.** Deterioration onset = first block on day 758. |
| **"Before" period** | All 21 T11 blocks on trial days 658–751 |
| **"After" period** | All 8 T11 blocks on trial days 758–800 |

**Why session level to locate but block level to analyse.** Locating wants
robustness, and session level is where all three methods agree on both variables.
Analysis wants observations, and block level provides 21 rather than 11. These are
different jobs; the change point is a *date*, so once located at session
resolution it applies unambiguously to blocks.

### B. SENSITIVITY definition

Repeat the entire primary analysis with the boundary located by **change-point on
success rate** instead of angle error, at session level. This lands on day 758
as well, so the sensitivity analysis tests whether conclusions survive the choice
of performance variable. Report both regardless of agreement.

Additionally report the primary analysis at **session level** (n = 11) alongside
block level, as a second sensitivity axis.

### C. T5 REVERSIBILITY / VALIDATION TEST

Not a lead-time test — a directional prediction:

> The indicator should **rise** from days 2121–2128 into the degraded period
> (2133–2135) **and fall again** at day 2149, when performance recovers to 92.8%.

Prespecified success criterion: the indicator at day 2149 returns to within the
range spanned by days 2121–2128. Prespecified failure criterion: the indicator at
day 2149 remains at or above its degraded-period level, which would indicate the
measure is tracking elapsed time or accumulated drift rather than system dynamics.

**Run the same test within T11** across days 727 → 751, where performance
degrades to 56.5% and returns to 100%.

### C2. PRESPECIFIED SECONDARY OUTCOME — neural versus behavioural lead time

*Answers: does the neural indicator warn earlier than simply watching performance?*

This is the clinically meaningful comparison. Predicting a collapse that was
already visible in behaviour is worth little; warning before behaviour shows
anything is worth a great deal.

**One detection rule, applied identically to both signals.**

| Element | Fixed value |
|---|---|
| Baseline | the first 8 T11 blocks (trial days 658–675) — these precede every candidate destabilization date, so the baseline cannot be contaminated by it |
| Limit | baseline mean + *k* × baseline SD |
| Detection | first block exceeding the limit and staying beyond it for *p* consecutive blocks |
| Behavioural signal | median angle error per block |
| Neural signal | the early-warning indicator per block |
| Outcome | `detection_day(behaviour) − detection_day(neural)`, in trial days. **Positive means the neural indicator warned first.** |

**Reported across the parameter grid, not at one setting.** We now know this rule
is parameter-sensitive (§3b), so *k* ∈ {1.5, 2.0, 2.5, 3.0}, baseline ∈ {4, 6, 8}
and *p* ∈ {2, 3} are all run — the same 24 combinations. Because both signals use
identical parameters at every setting, the *comparison* is fair even though either
date alone is not well determined. Report the full distribution of lead times plus
its median.

**Prespecified interpretation, fixed in advance:**

| Result | Conclusion |
|---|---|
| Lead > 0 in a clear majority of settings | Neural monitoring detects earlier than behavioural monitoring |
| Lead ≈ 0 | No advantage over watching performance |
| Lead < 0 | Behaviour detects first — **the neural indicator adds nothing**, and this must be reported as such |

That third row is the point of prespecifying it. It is a result the project can
lose, which is what makes winning it meaningful.

### D. What must be frozen before any indicator is computed

1. This document, committed, with its commit hash recorded.
2. The boundary — **T11 trial day 758** — and the resulting block membership of
   the "before" and "after" sets, written to a data file, not recomputed later.
3. The analysis level (block), the performance variable (angle error), and the
   sensitivity variants (success rate; session level).
4. The T5 and T11-internal reversibility criteria above, including what counts as
   failure.
5. The trend statistic (Kendall's τ), the significance procedure (two-sided
   against AR(1)-matched surrogates), and α = 0.05 — already fixed in
   `scripts/06_ews_controls.py`.
6. The power statement: at n = 21 the test detects |τ| ≥ 0.305, with power 0.74
   against a 2-standard-deviation rise. **A null result will be reported as a
   null.**
7. The secondary outcome of §6.4 — the detection rule, its baseline blocks, the
   parameter grid it is reported across, and the three prespecified
   interpretations, **including that a negative lead means the neural indicator
   adds nothing and will be reported that way.**

### E. What may still be decided afterwards

Nothing about the event definition. Genuinely open, and independent of it: which
neural observable carries the indicator (raw features are ruled out — they are
near-white at 20 ms), and the rolling-window length, which must be swept and
reported as a surface rather than chosen.

---

## 7. Concise recommendation

**PRIMARY** — Change point on median angle error per session for T11, located by
exhaustive least-squares single-change-point search with 3-observation minimum
segments and a 5,000-permutation significance test. Boundary: **trial day 758**
(p = 0.0018). Analysis at block level: 21 blocks before, 8 after.

**SENSITIVITY** — The same procedure on success rate (also day 758), plus the
primary analysis repeated at session level (n = 11). Both reported regardless of
whether they agree.

**T5 VALIDATION** — Reversibility: the indicator must rise into T5's degraded
period (days 2133–2135) **and fall back** at day 2149 when performance recovers
to 92.8%. Repeat within T11 across days 727 → 751. Failure criterion prespecified.

**WHY** — Three independent change-point methods agree on day 758 across two
independent performance variables, so the boundary is a property of the data
rather than a researcher's choice; the change is strongly significant for T11
(p ≈ 0.0015) and only marginal for T5 (p = 0.046–0.071); T11 has 21
pre-transition blocks against T5's 9; and BIC shows T5 is a reversible excursion
rather than a transition, which disqualifies it as the primary event and makes it
ideal as a reversibility control.

**WHAT WE MUST FREEZE BEFORE EWS ANALYSIS** — This document and its commit hash;
the day-758 boundary and the explicit block membership of the before/after sets
written to a file; the analysis level, primary variable and sensitivity variants;
the reversibility criteria including what counts as failure; the trend statistic,
surrogate procedure and α; and the power statement, with an advance commitment to
report a null as a null.
