# A one-class detector on invariant features — preregistered

**Written before any of it is built or run.**

## Where this comes from

`reports/PERMUTATION_INVARIANT.md` showed that twelve permutation-invariant
summaries of the per-channel change separate all four fault modes at 0.93–1.00,
where the guard's four scalar components leave three of them confusable. The
information lives in the **shape of the distribution across channels**, and
`decoder_guard` throws that shape away.

The constructive question follows: **does a monitor built on that shape do better
than the one built on scalars?**

## Why this is a test and not a search

The instruction I am working under forbids trying variants until one works. So
this is bound tightly, in advance:

- **One candidate only.** If it fails, that is the result. I will not build a
  second, a third, or a tuned version of the same idea.
- **The features are not new and not tuned.** The same twelve summaries fixed in
  `62_permutation_invariant.py`, unchanged. Nothing added or removed.
- **The evaluation is the existing frozen one.** Same episodes, same
  early-warning windows, same silence-gate definition, same healthy comparison
  group. Only the detector changes.
- **Success criteria are numeric and fixed below**, before running.

## What is built

`InvariantGuard`: per window, the per-channel deviation from that episode's own
local healthy reference, reduced to the twelve invariant summaries, scored as a
robust Mahalanobis distance in that 12-dimensional space with covariance fitted
on **healthy windows only**. One-class throughout — no fault ever touches the fit.

This differs from the separability probe in the way that matters: **that probe was
supervised and told faults apart from each other; this is unsupervised and must
tell a fault from healthy recording.** Those are different problems, and the
second is harder.

## Success criteria, fixed in advance

| | Criterion | Current best |
|---|---|---|
| **Detection** | session-level AUC must exceed the current value on **both** participants | 0.672 (T11), 0.742 (T5) |
| **Specificity** | fraction of healthy episodes whose risk signal trends must be **≤ 10%** — the silence gate | 31% (best of 48 configurations) |

Beating detection on one participant only is **not** a success; that is the
pattern that has produced every false positive in this project.

## Prediction, committed

1. **Detection will improve modestly** — I expect AUC up by 0.02–0.08 on both,
   because the shape information is real and demonstrably present.
2. **The silence gate will still fail.** I do not expect it below 10%.

Reason for the second: the gate fails because the risk signal is never quiet
during healthy operation, and that is driven by within-session drift and by
lag-1 r = 0.995 — properties of the recording, not of the feature set. A better
representation should sharpen the fault signal without making healthy recording
any quieter.

If the gate *does* pass, my account of why everything failed is wrong in an
important way, and that would be the most significant result of the project.

## What follows

**Both criteria met** → a genuine improvement, and the first configuration in this
project that is deployable at the specified budget. It would need confirmation on
a third participant before being called that.

**Detection improves, gate still fails** → confirms the structural objection: the
limitation is the recording's statistics, not the monitor's features. This is what
I expect.

**Neither improves** → the shape information does not transfer from
telling-faults-apart to telling-fault-from-healthy, and the separability result
stays a statement about attribution only.

All three outcomes are reportable and none is a reason to build a second
candidate.
