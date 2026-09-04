# Is the detection headline carried by one easy fault mode? — preregistered

**Written before computing anything.**

## Why this follows

`reports/MODE_SEPARABILITY.md` found `GEOMETRY_ROTATION` to be the most
distinctive fault in the set, and `reports/ATTRIBUTION_ACCURACY.md` measured its
`dispersion` component at **z = 16.5** during the early-warning window — nine
times `profile`, and far above anything the other modes produce.

A fault that shifts a component by sixteen standard deviations is not a subtle
one. So the headline detection result — **session-level AUC 0.69 (T11) and 0.71
(T5)**, quoted throughout this project and registered as claim C02 — may be a
mixture of *one mode that is trivially detectable* and *three that are not*.

If so, the honest headline is not "the monitor detects faults counting spikes
cannot see" but "the monitor detects **rotation**, and struggles with the rest".
That is a materially different claim and it is registered as ESTABLISHED, so it
needs checking.

## What is measured

The headline AUC decomposed by injected fault mode, using **exactly** the stored
scores it was computed from — same episodes, same early-warning windows, same
healthy comparison group. Nothing is recomputed, so any difference is genuinely a
decomposition of the published number rather than a different analysis.

| | |
|---|---|
| Faulted group | per mode, median score over `[onset, crossing)` |
| Healthy group | unchanged and shared across modes — the non-crossing episodes |
| Metric | AUC, as in C02 |
| Reported | all four modes, both participants, plus the headline recomputed with rotation removed |

## Prediction, committed

1. **`GEOMETRY_ROTATION` will have the highest per-mode AUC**, above 0.8.
2. **Removing it will lower the headline materially** — I expect the remaining
   three modes to land near 0.60–0.65 against the published 0.69/0.71.

If instead rotation sits in line with the others, the headline is robust and the
z = 16.5 dispersion shift is not translating into easier detection — which would
itself be worth understanding.

## What follows

**Prediction confirmed** → claim C02 is amended in the register to state the
per-mode breakdown, and the README headline is qualified. A claim that is true
only because of one fault mode should say so.

**Prediction wrong** → C02 stands as written, now with a decomposition behind it.

Either way the numbers go into the register, because "is our headline carried by
one easy case?" is the sort of question that only gets asked if it is written
down first.

---

## Correction, appended after running — the note mislabelled its own target

**This note said "session-level AUC 0.69 (T11) and 0.71 (T5)". That is wrong.**

Those registered numbers are **window-level**: `31_verify_claims.py` concatenates
every window from every episode and compares them individually. Every session-level
analysis elsewhere in this project takes one median per episode instead.

The preregistration is left as written and this correction appended, rather than
edited in place, because silently fixing a preregistration after seeing results
destroys the only thing it is for.

The consequence for this study is small — both levels are now computed and
reported side by side, and the window-level figure reproduces the register
exactly (0.693 and 0.708). The consequence for the project is not: **claim C02's
headline is a window-level statistic**, and claim C04 says windows within a
session are not independent. The point estimate is sound; any p-value or interval
built on it would not be. Recorded in the register.

## Predictions scored

| | predicted | outcome |
|---|---|---|
| rotation is the highest mode, above 0.8 | yes | **wrong** — highest on T11 but 0.789, and only *third* on T5 |
| headline without rotation falls to 0.60–0.65 | yes | **wrong** — 0.636 on T11 (drop 0.037), 0.740 on T5 (drop 0.002) |

Both wrong, and the study is the more useful for it: the headline is **not**
carried by one easy fault mode, so C02 stands as registered.
