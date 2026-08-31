# Preregistration — the feature study

**Status:** DRAFT, not yet frozen. Freeze with `scripts/12_freeze_design.py`
before running anything in §4.
**Written:** 28 August 2026, after Phase 3 and **before any candidate feature has
been computed on the corpus.**

---

## 1. Why this document exists

Phase 3 ruled out better decision rules, longer windows, and better aggregators —
each on measurement, not preference. The one remaining direction is a **better
feature**.

That direction is dangerous in a specific way, and the danger is worth naming
plainly:

> There are two participants and they **disagree**. T5 and T11 disagreed in sign
> in Phase 1–2, and disagreed again on the joint-detector prediction. With n = 2,
> **any feature that helps one participant can be found by trying enough
> features.** A feature search run opportunistically will produce a winner
> whether or not any real signal exists.

Phase 1–2 already demonstrated what protects against this: writing the analysis
down, with a checksum, before running it. That is what this document is for.

---

## 2. What is already known, and must not be re-litigated

Fixed by Phase 3 and **not** open for adjustment during this study:

| Fixed | Value |
|---|---|
| Performance event | +10° above an episode's own pre-onset baseline |
| Injection plan | The locked plans, with their recorded amendments |
| Reference decoder | Frozen; not refitted |
| Baseline strategy | Recent-normal (calibrate-once carries no information: AUC 0.491) |
| Primary metric | Session-level AUC in the early-warning window |
| Comparator to beat | Counting activity, and `decoder-guard` v1 |

**Session-level AUC is the primary metric, not lead time or false-alarm rate.**
Phase 3 established that at any usable operating point detection is ~1%, so
operating-point metrics have no resolution to distinguish features. AUC has.

---

## 3. The hypothesis, and what would falsify it

**H:** At least one candidate feature family raises session-level AUC by ≥ 0.05
over `decoder-guard` v1 **on both participants in the same direction.**

**Falsified if:** no family clears +0.05 on both, or every family that clears it
on one participant fails or reverses on the other.

The both-participants requirement is the whole point. **A feature that helps only
T11, or only T5, is recorded as a null result**, not as a partial success — that
rule is stated here so it cannot be softened later.

### The target, for context

To flag 80% of degrading sessions at a 10% false-flag rate needs session-level
AUC ≈ **0.93**. Current: **0.673 (T11) / 0.742 (T5)**. A +0.05 improvement does
not reach the target and is not claimed to. It is the smallest effect worth
pursuing further.

---

## 4. The candidate features — all of them, named now

Four families. **This list is closed.** Anything not on it is a new study
requiring its own preregistration.

| # | Family | What it measures | Why it is a candidate |
|---|---|---|---|
| **F1** | Per-channel **variability** (Fano factor: variance ÷ mean, per channel per window) | how *steadily* each channel fires, independent of how much | Current features use only the mean. A failing electrode may become erratic before it becomes quiet. |
| **F2** | **Cross-channel covariance structure** (off-diagonal correlation, summarised by top eigenvalue share) | whether channels move *together* differently | Electrode loss changes which channels co-vary. This is closest to what the published MINDFUL measure captures and is the family with the strongest prior. |
| **F3** | **Spectral content** of each channel's binned activity (power in slow vs fast bands) | the *timescale* of fluctuation | Drift and fault plausibly live at different timescales; every current feature is timescale-blind. |
| **F4** | **Channel-count statistics** (number of channels above/below fixed multiples of their own healthy median) | the *shape of the distribution across channels* rather than its moments | Robust to the heavy tails that defeated earlier scale-based measures. |

Each is computed on the same 30-second windows, fitted on healthy data only,
scored through the unchanged harness, and reported for **both** participants.

---

## 5. Analysis plan, fixed in advance

1. Compute all four families on both participants.
2. Report **all four**, in the table of §4's order, whatever the outcome.
3. Primary comparison: session-level AUC in the early-warning window, versus
   `decoder-guard` v1 and versus counting activity.
4. Confidence intervals by bootstrap over **episodes**, not windows — Phase 3
   measured lag-1 autocorrelation at 0.995, so windows are not independent and
   bootstrapping them would produce intervals roughly √55 too narrow.
5. Any family clearing +0.05 on both participants then goes through the **full
   five gates**, silence first.
6. No family is dropped, merged, or reparameterised after seeing its result.

### Multiple comparisons

Four families × two participants = eight tests. The both-participants requirement
already imposes most of the correction; in addition, the +0.05 threshold applies
to the **point estimate**, and any family clearing it must also have a bootstrap
interval excluding zero on both participants.

---

## 6. What will be reported regardless of outcome

- All four families, with their AUCs on both participants.
- Every family that helped one participant and not the other, **named as such**.
- The gap remaining to the 0.93 target.
- If nothing clears +0.05: that is the result, and it converts "a better feature
  is the remaining direction" into "the obvious better features were tried and
  do not work", which is a stronger and more useful statement than the current
  open question.

---

## 7. What this study cannot settle

Even a success here leaves the **binding limitation untouched**: two
participants, who disagree. A feature clearing +0.05 on both is encouraging and
is still n = 2.

**A third participant remains worth more than any feature.** This study is the
right thing to do while that is blocked, not a substitute for it.

---

## 8. Freeze procedure

    python3 scripts/12_freeze_design.py --confirm     # records commit + checksums

Freeze before computing any feature in §4. If the plan changes after freezing,
amend with a recorded reason rather than editing — the same discipline that made
the Phase 1–2 negative result trustworthy.
