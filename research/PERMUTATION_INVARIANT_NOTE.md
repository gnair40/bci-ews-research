# Was "the features' fault" actually the model's fault? — preregistered

**Written before computing anything.**

## The conclusion I am challenging

`reports/MODE_SEPARABILITY.md` (claims **E04/E05**) found that
`GEOMETRY_ROTATION` separates from everything at 0.86–1.00, while
`CHANNEL_DROPOUT`, `GAIN_DRIFT` and `RATE_LOSS` separate from **each other** at
only 0.57–0.78. I wrote:

> rotation — the guard's fault, fixable
> dropout / gain / rate — **the features' fault, not fixable this way**

Re-reading my own method, that second line may be wrong, and for a structural
reason rather than a subtle one.

## Why the model, not the features

The probe fitted a **linear discriminant** on the per-channel signed log-ratio
vector — it searches for one fixed direction in 384-dimensional channel space.

But **which channels a fault affects is drawn at random for each episode.**
`CHANNEL_DROPOUT` silences a random subset; `GAIN_DRIFT` scales each channel by
an independent random factor. There is therefore *no fixed direction* that
identifies either one: the informative pattern lands on different coordinates
every time.

A linear discriminant is structurally incapable of detecting that. It is the
wrong tool, and its failure says nothing about whether the information exists.

Meanwhile the three modes should differ sharply in the **shape of the
distribution** of per-channel changes, which does not depend on channel identity
at all:

| fault | signature across channels |
|---|---|
| `CHANNEL_DROPOUT` | **sparse and extreme** — most channels untouched, a few driven to zero |
| `RATE_LOSS` | **uniform shift** — every channel down by a similar amount |
| `GAIN_DRIFT` | **spread with no mean change** — channels scattered either way |

Those are different distributions with the same *support*, and permutation-
invariant summaries see them while a fixed direction cannot.

## What is measured

The identical probe — same episodes, same leave-one-session-out, same fixed
λ = 0.1·trace/p, same pairwise AUC — with only the **feature representation**
changed, from the raw 384-channel vector to twelve permutation-invariant
summaries of it:

mean, sd, skew, kurtosis, the 5/25/50/75/95th percentiles, the fraction of
channels essentially unchanged (|v| < 0.05), the fraction severely reduced
(v < −1.0), and the participation ratio ‖v‖₁/‖v‖₂ (a sparsity measure).

Fixed in advance, and **not tuned**: no feature is added or removed after seeing
a result.

## Prediction, committed

**The three confusable modes will separate substantially better** — I expect the
worst pair to rise from **0.574** to above **0.75**, on T11.

I do **not** expect rotation's numbers to improve much; they are already near
ceiling and rotation has a genuine fixed-direction component.

If the permutation-invariant features do **no better**, then my original
conclusion stands and the information really is absent — and I will have tested
it properly instead of asserting it.

## Status and limits

Still **EXPLORATORY** and still an **upper bound**: it uses the injected fault
labels a deployed monitor never has. Nothing here is a proposed component. If it
succeeds it means an attribution scheme *could* work on these faults, not that
this monitor does.

## What follows either way

**Separates better** → claims E05 and the "not fixable this way" line in
`MODE_SEPARABILITY.md` are corrected, and the honest split becomes *all four
modes are separable in principle; the guard's four scalar components are the
limitation*.

**Does not** → E05 stands, now with a real test behind it rather than an
inference from one model class.
