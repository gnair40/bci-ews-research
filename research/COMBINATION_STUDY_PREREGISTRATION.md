# Preregistration — the combination study

**Status:** DRAFT. **Not frozen. Not run.**
**Written:** 1 September 2026, immediately after the feature study returned.

> **No human participants.** As throughout this project, "participant" means
> whose published de-identified recording a data file contains. Nobody is
> recruited. See the README.

---

## 1. Why this exists, and why it is not simply run

The feature study returned a null against its frozen criterion. Its **post-hoc**
secondary comparison found something worth following:

| Against the matched control | T11 | T5 |
|---|---|---|
| F1 variability | +0.106 | +0.158 |
| F2 covariance | +0.059 | +0.095 |
| `decoder_guard`'s scorer, over its own features | **+0.102** | **+0.233** |

Two families are better *features*. The current system's advantage is mostly its
four-component *decomposition*. **Neither alone closes the gap; nobody has tried
both.**

That is an obvious next move, and obvious next moves derived from a post-hoc
table are exactly what the freeze discipline exists to slow down. The feature
study's own F3 row is the cautionary case: it cleared the bar on one participant
and failed on the other, and would have been declared a success by anyone who
looked at one participant before writing the rule.

**So this is written before anything is computed, and is not run until frozen.**

---

## 2. What is already fixed and not open to adjustment

| Fixed | Value |
|---|---|
| Injection plans, performance event (+10°), reference decoders | unchanged |
| Baseline strategy | recent-normal |
| Primary metric | session-level AUC in the early-warning window |
| Confidence intervals | bootstrap over **episodes** (lag-1 r = 0.995) |
| **Both-participants rule** | unchanged, and it is the whole point |

**One change from the feature study, stated as a change:** the comparator is
`decoder_guard` v1 *only*. The matched control F0 was needed there to interpret a
null; here the question is directly "does this beat the deployed system", so a
matched control is not required and adding one would only multiply comparisons.

---

## 3. What gets built

`decoder_guard` computes four named components from per-channel **mean activity**:
level, silence, dispersion, profile. The change is to compute the same kind of
named decomposition over the **better feature sets**:

| Arm | Components computed from |
|---|---|
| **C1** | F1 variability (per-channel Fano factor) |
| **C2** | F2 covariance structure |
| **C3** | F1 and F2 together, components concatenated |

Each keeps `decoder_guard`'s calibration, specificity-ordered attribution, and
state machine unchanged. **Only the input to the decomposition changes.**


### 3a. How the decomposition generalises — specified before it is built

`decoder_guard`'s four components are defined for *activity* features
specifically: total activity, channels at zero, spread of per-channel gains,
residual shape. Fano factors and eigenvalue shares are not activity, so the
components must be stated in their **structural** form, which is what actually
carries over. That statement belongs here, before implementation, not in a
commit message afterwards.

| Component | Structural definition, for any non-negative feature vector |
|---|---|
| `level` | overall magnitude — the sum across feature dimensions |
| `extremes` | fraction of dimensions in the far lower tail of their own healthy reference (the generalisation of "channels gone silent") |
| `spread` | robust dispersion across dimensions of the log-profile, after the common mode is removed |
| `profile` | Mahalanobis residual in that common-mode-removed subspace |

Calibration, specificity-ordered attribution, and the state machine are unchanged.
Working in logs and removing the common mode is retained, because that is what
makes `spread` and `profile` invariant to a uniform change in scale — the
property the original decomposition was built around.

**Faithfulness check, run before the arms and reported with them:** the same
generalised decomposition applied to the *original* features (per-channel mean
activity) must approximately reproduce `decoder_guard` v1. If it does not, the
generalisation is not a generalisation, and the arms cannot be interpreted as
"the same decomposition over better features". This check can fail, and if it
fails the study stops rather than continuing with a mislabelled comparison.

**Three arms. The list is closed.**

---

## 4. Hypothesis and falsification

**H:** At least one arm raises session-level AUC by **≥ 0.05 over
`decoder_guard` v1 on both participants in the same direction.**

**Falsified if** no arm clears +0.05 on both, or every arm clearing it on one
reverses on the other.

**Stated in advance, because it is the tempting exception:** C3 combining two
families that each helped is **not** grounds for relaxing the threshold if it
lands at, say, +0.04. The bar is +0.05 on both, set before the numbers exist.

---

## 5. What will be reported regardless

- All three arms, both participants, with episode-bootstrap intervals.
- Any arm helping one participant and not the other, **named as such**.
- The gap remaining to the session-level target of ≈ 0.93.
- If nothing clears: that the two most promising known ingredients do not combine
  productively, which closes the last direction this project's own results
  suggested.

---

## 6. What this cannot settle

Unchanged, and still binding: **n = 2, and the participants disagree.** They
disagreed in Phase 1–2, on the joint-detector prediction, and in the F3 row of
the feature study. An arm clearing +0.05 on both is encouraging and is still
n = 2.

**A third dataset remains worth more than any of this.** It is blocked only on
Dryad credentials.

---

## 7. Freeze procedure

    python3 scripts/12_freeze_design.py --confirm

Freeze before computing any arm. Amend with a recorded reason rather than
editing — the discipline that made the F3 null trustworthy.
