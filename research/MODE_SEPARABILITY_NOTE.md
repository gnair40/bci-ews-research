# Is the information to tell fault modes apart even there? — preregistered

**Written before running.**

## The question this follows from

`reports/ATTRIBUTION_ACCURACY.md` found `GEOMETRY_ROTATION` attributed correctly
**0%** of the time on both arrays, and diagnosed the cause as the components
rather than the ranking rule: `dispersion` is *defined* as channels spreading with
the total conserved, and rotation is injected as norm-preserving, so they are the
same signature by definition.

That diagnosis has a testable consequence, and it is the difference between two
very different conclusions:

- **The information is present** and the guard's four components throw it away →
  attribution is a fixable design problem.
- **The information is absent** — the modes genuinely leave indistinguishable
  traces in these features → no attribution scheme could work, and the capability
  should be dropped rather than improved.

This is the same shape as the earlier finding that detection information *was*
present (AUC 0.69) even though nothing passed the gates. Separating "the mechanism
fails" from "the information isn't there" has been the useful move each time.

## What this is, and what it is emphatically not

**An information probe and an upper bound.** It uses the injected fault labels,
which a deployed monitor never has, and it fits a discriminant per pair of modes.
Nothing here is a proposed component, and no number from it may be quoted as
monitor performance.

Reported as EXPLORATORY in the claims register regardless of outcome, because a
supervised probe is a departure from the one-class discipline the rest of the
project holds to.

## Method, fixed in advance

| | |
|---|---|
| Episodes | test-split faulted episodes that crossed, as everywhere else |
| Feature | per-channel signed log-ratio between the early-warning window and the episode's own **strictly clean** pre-onset baseline (`start + window <= onset`) |
| Model | regularised linear discriminant, `w = (Σ + λI)⁻¹(μ₁ − μ₂)`, with **λ = 0.1 · trace(Σ)/p fixed in advance and not tuned** |
| Validation | **leave-one-session-out** — no block may appear in both train and test, because episodes from one block are not independent |
| Metric | pairwise AUC over the pooled held-out projections, all 6 mode pairs |
| Reported | all 6 pairs, both participants, whatever they show |

## Prediction, committed

**I expect the information to be present**, and specifically that
`GEOMETRY_ROTATION` vs `GAIN_DRIFT` separates at **AUC > 0.8**.

The mechanism: gain drift scales each channel independently, so its signature is a
*random* per-channel pattern; rotation exchanges activity between specific pairs
of channels, so its signature is *structured* — some channels up, their partners
down. A signed per-channel vector should see that even though a scalar dispersion
measure, which discards the signs and the pairing, cannot.

If that pair comes out near chance, my diagnosis of the attribution failure is
incomplete: it would mean the two faults really are indistinguishable in these
features, not merely conflated by one badly-chosen component.

## What follows either way

**Separable** → the attribution failure is a component-design problem, and the
report should say the capability is fixable in principle.

**Not separable** → attribution for those modes is impossible with these features,
and claiming it as a capability at all would be unsupportable.
