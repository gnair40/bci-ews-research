# The more sensitive detector was worse, on both axes

**Preregistered:** `research/INVARIANT_DETECTOR_NOTE.md` — one candidate, numeric
criteria, and a prediction, all fixed before it was built
**Script:** `63_invariant_detector.py`

## What was tested

`reports/PERMUTATION_INVARIANT.md` showed that the information distinguishing
fault modes lives in the **shape of the per-channel change distribution**, and
that `decoder_guard`'s four scalar components discard it. The constructive
follow-up: build a one-class detector that scores that shape, and put it through
the same evaluation.

Structure deliberately mirrors `DecoderGuard` so the comparison is about features
and nothing else — global covariance of the twelve invariant summaries fitted on
healthy windows only, local centre and scale re-estimated per episode from its own
clean prefix. No fault ever touches the fit. The twelve features are imported
unchanged from the earlier probe: not re-chosen, not tuned.

## Both criteria failed, and the first prediction was wrong

| criterion | required | T11 | T5 |
|---|---|---|---|
| **Detection** — beat current AUC on **both** | > 0.672 / > 0.742 | **0.617** (−0.055) | **0.680** (−0.062) |
| **Specificity** — silence gate | ≤ 10% of healthy episodes trending | **98.5%** | **98.7%** |

I predicted detection would improve by 0.02–0.08 on both. **It got worse on
both.** I predicted the gate would still fail — it does, but at 98.5% against a
current best of 31%, roughly three times worse than anything in the 48-configuration
benchmark.

Per the preregistration: one candidate. **There is no tuned variant and there will
not be one.**

## The check that makes this trustworthy

Median Kendall τ on healthy episodes is **0.735** — the risk score rises almost
monotonically through nearly every healthy session. That is suspicious, because
`score()` clips at zero, which pins early windows to the floor and could
*manufacture* an upward trend.

So the same gate was run on the **unclipped** series:

| | clipped | unclipped |
|---|---|---|
| T11 — healthy episodes trending | 98.5% | **98.9%** |
| T11 — median τ | 0.735 | **0.716** |
| T5 — healthy episodes trending | 98.7% | **98.7%** |

**The trend survives.** The clipping did not cause it; the drift is real.

## What it means, and why this is the strongest result of its kind here

> **The shape of the per-channel distribution drifts monotonically through a
> healthy session — and that is the same shape that distinguishes faults.**

A detector sensitive enough to see the fault signature is, necessarily, sensitive
to ordinary within-session drift. It cannot separate them because they are the
same quantity.

This also explains the detection loss: healthy episodes' scores climb through the
session, inflating their medians and compressing the gap with faulted ones. Making
the detector sharper made the healthy baseline noisier faster than it made the
fault stand out.

Earlier work inferred this tension from a *class* of detectors sharing a failure
pattern (`reports/DAY_EFFECT_ACROSS_DETECTORS.md`). This demonstrates it
constructively: **I built the more sensitive detector the evidence pointed to,
committed the criteria in advance, and it was worse on both axes.** An inference
became a measurement.

## What this does and does not change about the earlier recommendation

`reports/PERMUTATION_INVARIANT.md` recommended building **attribution** on
permutation-invariant distributional summaries. **That recommendation stands** —
it was supported by a supervised probe of telling faults apart from one another,
and nothing here touches that.

**It must not be extended to detection.** The evidence supports invariant
summaries for one task and actively refutes them for the other. Those are
different problems, as the preregistration said before running, and the results
now say so with numbers.

## Limitations

- **One candidate, by design.** A different one-class scoring rule over the same
  features — a robust covariance, a per-feature one-sided rule, a rank-based
  distance — might behave differently. Not testing those was a deliberate
  constraint against searching until something works, not a claim that none could
  work.
- The comparison AUC values (0.672, 0.742) are the **episode-level** figures from
  `reports/PER_MODE_DETECTION.md`, not the window-level numbers registered in C02.
  Both arms here are episode-level, so the comparison is internally consistent.
- Two participants, as everywhere.
