# It was the model's fault, not the features'

**Preregistered:** `research/PERMUTATION_INVARIANT_NOTE.md`, prediction included
**Script:** `62_permutation_invariant.py`
**Status: EXPLORATORY** — a supervised upper bound using labels a deployed
monitor never has.

## What this corrects

`reports/MODE_SEPARABILITY.md` concluded, and claim **E05** recorded:

> rotation — the guard's fault, fixable
> dropout / gain / rate — **the features' fault, not fixable this way**

**That second line was wrong.** All four fault modes are near-perfectly separable.
The limitation was the model I probed with, not the information available.

## Why the first probe could not have worked

It fitted a **linear discriminant** on the per-channel change vector — one fixed
direction in 384-dimensional channel space. But **which channels a fault touches
is drawn at random for each episode**: `CHANNEL_DROPOUT` silences a random subset,
`GAIN_DRIFT` scales each channel by an independent random factor. No fixed
direction identifies either one, so the model was structurally incapable of seeing
them and its failure said nothing about the information.

The three confusable modes differ in the **shape** of the per-channel change
distribution, which does not depend on channel identity at all:

| fault | signature across channels |
|---|---|
| `CHANNEL_DROPOUT` | sparse and extreme — most untouched, a few at zero |
| `RATE_LOSS` | uniform shift — everything down together |
| `GAIN_DRIFT` | spread, mean intact — scattered both ways |

## The result

Twelve permutation-invariant summaries, everything else held identical — same
episodes, same leave-one-session-out, same fixed λ, same pairwise AUC.

**T11**

| pair | per-channel (384-d) | **invariant (12-d)** | change |
|---|---|---|---|
| CHANNEL_DROPOUT vs RATE_LOSS | 0.575 | **0.999** | **+0.424** |
| CHANNEL_DROPOUT vs GAIN_DRIFT | 0.599 | **0.997** | **+0.399** |
| GAIN_DRIFT vs RATE_LOSS | 0.777 | **0.965** | +0.188 |
| CHANNEL_DROPOUT vs GEOMETRY_ROTATION | 0.858 | 0.997 | +0.140 |
| GAIN_DRIFT vs GEOMETRY_ROTATION | 0.919 | 0.929 | +0.009 |
| GEOMETRY_ROTATION vs RATE_LOSS | 0.977 | 0.978 | +0.001 |

The confusable trio's mean rises from **0.650 to 0.987**; the worst pair anywhere
from **0.574 to 0.929**. T5 shows the same pattern (trio 0.623 → **0.998**).

The preregistered prediction — worst pair above 0.75 — is met at 0.929, and its
second half holds too: **rotation's pairs barely moved** (+0.009, +0.001), because
they were already near ceiling and rotation genuinely does have a fixed-direction
component.

## The control that makes the claim honest

Twelve features beating 384 has an obvious alternative explanation: a 384-feature
discriminant on ~400 episodes is heavily regularised and may simply have underfit.
The gain could be **dimensionality**, not invariance.

So the same pipeline was run on **12 randomly chosen raw channels** — dimension
count held fixed, invariance destroyed, 20 draws:

| | confusable trio, mean AUC |
|---|---|
| 384 raw channels | 0.650 |
| **12 random raw channels** | **0.702** |
| **12 invariant features** | **0.987** |

*(T5: 0.623 / 0.756 / 0.998.)*

Cutting to 12 dimensions does help a little — which confirms the 384-d model was
handicapped — but it gets nowhere near. **The gain is the representation.**

## What this changes

**Claim E05 is withdrawn.** The corrected reading of the attribution failure:

> **The information to identify all four fault modes is present and strong. The
> guard's four scalar components are the entire limitation.**

That makes the attribution result an unambiguous design problem rather than a
mixture of a design problem and an information ceiling — a cleaner and more
useful conclusion than the one it replaces, and one I only reached by doubting a
line I had already published.

## The design recommendation this produces

> ### ⚠️ Correction, 5 September 2026 — this recommendation is narrowed
>
> The recommendation below has now been tested in both halves, label-free, and
> **both fail**:
>
> - **Detection** (`reports/INVARIANT_DETECTOR.md`): AUC fell to 0.617/0.680 from
>   0.672/0.742, and 98.5% of healthy episodes trend against a 31% best.
> - **Attribution** (`reports/INVARIANT_ATTRIBUTION.md`): 51.1%/39.7% against the
>   guard's 56.3%/52.5%, with rotation at 2.1%/6.1% against 25% chance.
>
> Corrected to what the evidence supports: **invariant summaries are evidence
> that the information exists. They are not a demonstrated design for a
> monitor.** The paragraph below should be read as describing where the
> information lives, not as a recipe.

An attribution scheme for these faults should be built on **permutation-invariant
distributional summaries** of the per-channel change — sparsity, spread, tail
shape — not on projections onto fixed channel directions, and not on scalar
magnitudes like `dispersion` that discard the distribution's shape.

That is the third concrete design change this line of work has produced,
alongside a performance metric with range at the bad end, and per-session
severity calibration.

## Limitations

- **Supervised, and an upper bound.** It uses the injected labels. A monitor has
  none, so it could not reach these numbers even with perfect components. This
  says the information exists, not that it is reachable one-class.
- **T5 has 3 sessions** after filtering; its near-1.0 values mean "clearly
  separable", not precise. T11's 12 sessions carry the result.
- The twelve features were fixed in advance and none was added or removed after
  seeing a result — but they were chosen *knowing* how the faults are injected,
  which is knowledge a real monitor would not have.
