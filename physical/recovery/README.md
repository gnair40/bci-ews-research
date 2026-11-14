# The recovery subphase: what a failure point is for

**Status on 14 November 2026: a draft. Nothing here is preregistered, built
or measured.**

The researcher asked for a subphase of the physical validation that takes the
failure point, once it has been found, and asks whether it can be used to make
decoding better. This folder holds that subphase as a proposal: the research
behind it, a design, a draft of the amendment that would add it to the plan,
and working code.

The frozen preregistration, `physical/docs/09_PREREGISTRATION.md`, has not
been edited.

## Why the folder is called "recovery"

Three different outcomes are possible, and the experiment measures which one
occurs.

- **Recovery**: better than doing nothing. The likeliest, and a real
  improvement.
- **Restoration**: back to where decoding was before the fault.
- **Enhancement**: better than before the fault. The strongest claim and the
  least likely, because a fault usually removes information.

Naming the folder after the strongest of the three would have named it after
a result it may not show.

## What is in it

| File | What it is |
|---|---|
| [`01_RESEARCH.md`](01_RESEARCH.md) | The published ways a decoder is repaired after a failure, what each needs, which the bench can test, and what was and was not confirmed about each source |
| [`02_DESIGN.md`](02_DESIGN.md) | Experiment P-8: the question, four repairs, five failure points, what is measured, the analysis plan, what it cannot show |
| [`03_PREREGISTRATION_DRAFT.md`](03_PREREGISTRATION_DRAFT.md) | Seven draft predictions, a draft judging rule, and the nine choices that are the researcher's. **Not frozen** |
| [`code/repairs.py`](code/repairs.py) | The four repairs and the scoring rule, with a built-in check |
| [`code/analyze_recovery.py`](code/analyze_recovery.py) | The analysis: reads the session table, applies every repair at every failure point, writes the report |

## The short version

- **It adds no recording.** P-8 re-analyses the sessions of P-2, P-3 and P-5,
  as P-4 and P-6 already do. No parts, no bench time, no delay to the build.
- **Four repairs**, from cheapest to most costly: renormalise each channel;
  drop the channels that went dark and refit; both together; recalibrate with
  the true direction. The first three need no calibration task.
- **Five failure points**: the sealed onset (the most any monitor could buy),
  the moment decoding failed, the moment the monitor warned, and on fault-free
  sessions a matched moment and any real false alarm (what a repair nobody
  needed costs).
- **The draft predicts recovery for three fault types, none for the fourth,
  and no enhancement.** The last is the prediction the researcher's idea needs
  to see fail.

## Checking the code

```bash
python3 physical/recovery/code/repairs.py --selftest
```

needs no recordings and takes a few seconds. It uses recordings made from a
formula, with faults built to suit each repair, to confirm that the repairs
and the scoring are wired up correctly. It is not evidence about anything.

The analysis was also rehearsed once, end to end, on the fake recordings that
`physical/code/dryrun.py` makes, and every file from that rehearsal was then
deleted with `dryrun.py --cleanup`.

**The self-test is not part of `tools/check_all.py`.** That suite has 13
gates, a number the paper and other documents cite. Adding a fourteenth for a
subphase that has not been approved would change those documents for a draft.

## What happens next is the researcher's decision

`03_PREREGISTRATION_DRAFT.md`, section 5, lists nine choices. The first is
whether P-8 is added at all. If it is, the amendment should be appended
before the bench records anything, so that it counts as preregistered.
