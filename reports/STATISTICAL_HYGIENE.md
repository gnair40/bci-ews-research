# A linter for the mistakes this project actually made

**Script:** `61_statistical_hygiene.py` (runs last, with the other gates)

## Why it exists

Three statistical error classes have been found in this project. **All three were
found by accident**, and all three were caught by checks written *after* the work
they caught:

| found | how | consequence |
|---|---|---|
| Inference on pooled, non-independent units | noticed while decomposing a headline | 4 p-values published as exactly `0`; sample size inflated **26.6×**; **3 "significant" results were not real** |
| A comparison that can never be true | noticed because every day reported precisely `0.00` | a fault-mix control measured nothing while looking exactly like a control that passed |
| An estimator biased by its own weights | noticed because the number was implausibly good | a pooled AUC inflated from 0.675 to **0.836** |

Waiting to trip over a fourth is not a strategy. This encodes the three as static
checks and runs them over every script.

## Status: **PASS** — 61 scripts, 0 unreviewed sites

| check | unreviewed | reviewed and kept |
|---|---|---|
| pooled inference | 0 | 6 |
| impossible comparison | 0 | 0 |
| inverse-variance weighting | 0 | 2 |

A finding is a **prompt, not a verdict** — each pattern was wrong at least once
here, and each site needs a human decision. Sites inspected and deliberately kept
are listed in `REVIEWED` with the reason, so the check stays a clean gate rather
than a wall of noise. **Anything not on that list is a real finding.**

## The linter missed its own motivating example, at first

The first version flagged one site and **did not flag `26_achievability.py`** —
the very code the check was written for. That file wraps `mannwhitneyu` inside a
local `auc(pos, neg)` helper, so the pooled variable never appears in the
statistical test's arguments.

A linter that cannot catch the case it was written for is worse than no linter,
because it converts "unchecked" into "checked and clean". Fixed by identifying
local functions that contain a test call and treating a call to one of those as a
test call. That took the count from 1 site to 9 — including all three of the
known-bad lines in `26_achievability.py`.

**This is the fourth time in this project that a checking tool was itself wrong
before it was useful.** The reproducibility audit reported 27 problems of which 1
was real; this one reported 1 of which the important 3 were missing. Both patterns
are the same mistake in opposite directions, and both were caught only by asking
"does it find the thing I already know is there?"

## What was changed in response

- `23_benchmark_figures.py` — its bar chart pools windows for a descriptive AUC
  with no inference attached, which is legitimate. The y-axis now says
  **"(window-level AUC)"** so the quantity is not mistaken for the episode-level
  one after the corrections in `reports/UNIT_OF_ANALYSIS.md`.

Nothing else needed changing: the remaining eight sites are the deliberate ones —
the pooled statistics computed on purpose so the register can record what claim
C02's number is, and the inverse-variance weights that Cochran's Q requires and
that are already labelled `..._BIASED_DO_NOT_QUOTE`.

## What it cannot do

- **Static only.** It finds shapes, not wrong answers. A test on genuinely
  independent units that is nonetheless the wrong test will pass.
- **Three patterns.** These are the three this project made. A fourth error class
  will not be caught until it is found some other way and added — which is the
  honest limit of learning from your own mistakes.
- The `impossible_comparison` check is a heuristic (an attribute compared to a
  string here and used numerically there). It catches the bug that motivated it;
  it would miss a numeric field never used arithmetically in the same file.
