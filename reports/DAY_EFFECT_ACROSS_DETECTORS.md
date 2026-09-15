# Whose fault is the day effect?

**Prediction committed in advance:** the addendum to
`research/DAY_PREDICTOR_PREREGISTRATION.md`
**Script:** `49_day_effect_across_detectors.py`

## My prediction was wrong

I predicted the day effect would be **shared by all four detectors** at ρ > 0.7,
on the reasoning that "an atypical recording" is not a property of any one
detector. I also stated the alternative: if decoder-guard were uncorrelated with
the baselines, the problem would be a design flaw.

Neither happened. The answer is a third thing I did not anticipate.

| T11: per-day AUC correlation with decoder-guard | ρ | p | met the predicted 0.7? |
|---|---|---|---|
| `distribution_shift` | **+0.835** | 0.0004 | **yes** |
| `robust_dispersion` | +0.247 | 0.42 | no |
| `mean_activity` | −0.060 | 0.84 | no |

And the P5 relationship — failing on days the decoder is already failing —
follows exactly the same split:

| T11: per-day AUC vs that day's decoder error | ρ | p |
|---|---|---|
| `decoder_guard` | **−0.720** | 0.0055 |
| `distribution_shift` | **−0.670** | 0.0122 |
| `robust_dispersion` | −0.368 | 0.22 |
| `mean_activity` | +0.220 | 0.47 |

T5 shows the same ordering (guard vs `distribution_shift` ρ = 0.829, vs
`robust_dispersion` 0.714, vs `mean_activity` 0.486), though with 6 days it
confirms nothing on its own.

## What it actually means

The day effect is **neither universal to the data nor specific to decoder-guard.
It belongs to a family of detectors.**

The two detectors that share it — `decoder_guard` and `distribution_shift` — are
the two that model the **multivariate distribution** of neural activity against a
healthy reference. The two that do not share it, `mean_activity` and
`robust_dispersion`, reduce a window to a scalar and have no distributional
reference to lose.

That gives the P5 result a mechanism it did not have before. On a day the decoder
handles badly, the *structure* of the activity is atypical — which is exactly
what a decoder is sensitive to, and exactly what a distribution-based monitor
depends on being stable. **A monitor built on the same kind of information the
decoder uses inherits the decoder's bad days.** Counting spikes does not, because
it never depended on that structure in the first place — but counting spikes is
also the detector that cannot see most faults, which is where this project
started.

That is a real tension and it is not resolved: **the property that makes a
detector sensitive enough to be useful is the same property that makes it fail
when the decoder fails.**

## The alternative reading I cannot exclude

`mean_activity` and `robust_dispersion` are also the *weaker* detectors, hovering
near chance on many days. A detector whose per-day AUC is mostly noise will
correlate weakly with everything, so their low correlations may reflect their
noisiness rather than a genuinely different mechanism.

Against that: their per-day AUCs are not flat — `mean_activity` ranges 0.35 to
0.74 across days, which is real spread, not a constant. But with 13 days I cannot
separate "different mechanism" from "too noisy to correlate", and I am not going
to claim I can.

## Why this changes the headline

`reports/DAY_PREDICTORS.md` concluded that the monitor's failures line up with
the hazard it exists to detect, and called that a structural objection to the
design. That conclusion **stands but should be read more narrowly**: it is an
objection to *distribution-based* decoder-health monitoring, which is a class of
approach rather than one implementation. A future attempt cannot escape it by
rebuilding decoder-guard differently while keeping the same kind of reference.

## Limitations

- **13 days on one participant**, and the weak-detector confound above.
- The detectors are not matched on overall performance, which is what makes that
  confound possible. Matching them would mean handicapping the good ones, which
  would test something else.
- Everything else — days, episodes, fits, windows — is identical across
  detectors by construction, so nothing but the detector varies.
