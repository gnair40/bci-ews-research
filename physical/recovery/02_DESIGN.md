# Experiment P-8: recovery from the failure point

**Status on 14 November 2026: a draft design. Not approved, not preregistered,
not run.** No bench exists, so no result exists. The frozen preregistration in
`physical/docs/09_PREREGISTRATION.md` does not mention this experiment and has
not been touched.

---

## 1. The question

The rest of the physical phase asks whether a monitor can warn that decoding
is about to fail. This experiment asks what the warning is for.

> Once a failure point is known, how much decoding performance does a repair
> that starts there recover; how does that depend on which failure point is
> used; and what does a repair cost when nothing was wrong.

It tests the researcher's idea of 14 November directly: that the moment of
failure can be used to make the system better than it would otherwise have
been.

## 2. Why it needs no new recordings

A repair to a decoder is arithmetic on the recording. It can be applied
afterward to a session that has already been recorded, exactly as experiments
P-4 and P-6 re-analyse the sessions of P-2 and P-3. P-8 does the same. It adds
**no sessions, no parts and no bench time** to the plan. It adds one program
and a few minutes of analysis.

That matters for the schedule. Nothing has been built, and this experiment
cannot delay the build.

## 3. What a session looks like to this experiment

Each session is cut into three stretches that never overlap.

```
start ............ onset ..... failure point ..... + 30 s ............ end
|  the decoder as it was   |                |  the repair   |  every repair  |
|  while healthy           |                |  watches      |  is scored     |
|  ("error before")        |                |  ("adapt")    |  ("evaluate")  |
```

A repair is never scored on the stretch it was built from. If fewer than 30
seconds remain after the adaptation period, the session is not scored for that
failure point, and the report counts how many were left out and why.

## 4. The four repairs

All four are always applied and all four are always reported. None is chosen
afterward as "the" repair.

| Code | Repair | What it does | What it may look at | Needs the true direction |
|---|---|---|---|---|
| R0 | None | The frozen decoder carries on | Nothing | No |
| R1 | Renormalise | Replaces each channel's stored average and spread with the values measured during the adaptation period | 30 s of camera signal | No |
| R2 | Mask and refit | Finds the channels that have gone dark and solves the decoder's weights again without them, from the stored calibration summary | 30 s of camera signal; the calibration summary | No |
| R3 | Mask and renormalise | R1 and R2 together | The same | No |
| R4 | Recalibrate | Fits a new decoder from the adaptation period alone | 30 s of camera signal **and the true direction** | **Yes** |

R4 stands for stopping the user to perform a set calibration task. On the
bench that costs nothing. In a real device it costs the user's time, which is
the cost a warning system exists to reduce. R1 to R3 could run while the
device is in use.

**"Gone dark" has a fixed rule.** A channel is called lost if its brightness,
as a fraction of its brightness at calibration, is less than half the value
that the 75th-percentile channel kept. A filter that dims everything equally
therefore marks nothing as lost. Tape over part of the field marks the covered
channels.

### What each repair is expected to fix, and why

| Fault | R1 renormalise | R2 mask and refit | R3 both | R4 recalibrate |
|---|---|---|---|---|
| RATE_LOSS (filter: everything dims) | Should help: the scale is restored. What remains is a noisier signal | Nothing to mask | As R1 | Could help; limited by 30 s of data |
| GAIN_DRIFT (channels drift apart) | Should help: each channel is rescaled separately | Nothing to mask unless a channel falls very far | As R1 | Could help |
| CHANNEL_DROPOUT (tape: channels go dark) | **May make things worse:** dividing a dark channel by its tiny spread amplifies noise | Should help | Should help most | Could help |
| GEOMETRY_ROTATION (the field shifts) | Should not help: every channel's average and spread are unchanged | Should not help | Should not help | The only one that could |

The rotation row is a control. If R1 to R3 appear to repair a fault they have
no means of repairing, something is wrong with the analysis.

## 5. The five failure points

The same repairs are started at different moments, because the moments answer
different questions.

| Sessions | Failure point | What it shows |
|---|---|---|
| Sealed faults (P-3) | **Onset**, as sealed in advance | The most that any monitor could buy. Nobody could know this moment in real use |
| Sealed faults (P-3) | **Failure**: decoding has measurably failed | A monitor with a lead time of exactly zero |
| Sealed faults (P-3) | **Warning**: this monitor warned | What this monitor buys, late warnings and missed faults included |
| Fault-free (P-2) | **Matched moment**, placed by the same rule that places onsets | The cost of a repair nobody needed |
| Fault-free (P-2) | **False alarm**, if the monitor raised one | The same cost, at the moments it would actually be paid |

The fourth and fifth rows are what keep this honest. A repair that helps after
a real fault and harms after a false alarm is only worth having if false
alarms are rare, which is the question P-2 measures.

Undesigned faults (P-5) are scored from their noted onset and reported in a
separate table, as everywhere else in the phase.

## 6. What is measured

For each session, failure point and repair:

- **Error before**: median decoding error before the onset, frozen decoder.
- **Unrepaired error**: median error over the evaluation stretch with R0.
- **Error after repair**: the same stretch, with the repaired decoder.

From those:

```
degrees recovered  =  unrepaired error  -  error after repair

                          degrees recovered
recovery fraction  =  ---------------------------------
                       unrepaired error - error before
```

| Recovery fraction | Meaning |
|---|---|
| below 0 | The repair made decoding worse |
| 0 | Nothing recovered |
| between 0 and 1 | **Partial recovery.** An improvement over doing nothing |
| 1 | **Restoration.** Back to where it was before the fault |
| above 1 | **Enhancement.** Better than before the fault |

The fraction is computed only for sessions that the fault damaged by at least
10 degrees, the same 10 degrees that defines failure in the rest of the
project. Without that limit it would be one small number divided by another.

## 7. Variables

| Kind | Variable | Values |
|---|---|---|
| Independent | Repair | R0, R1, R2, R3, R4 |
| Independent | Failure point | onset, failure, warning; matched moment, false alarm |
| Independent | Fault type and severity | As drawn and sealed for P-3 |
| Independent | Adaptation period | 30 s (primary); 10 s and 60 s reported as a curve |
| Dependent | Degrees recovered | degrees; negative means harm |
| Dependent | Recovery fraction | none; defined for damaged sessions only |
| Dependent | Sessions better than before | count out of damaged sessions |
| Dependent | Cost of a needless repair | degrees, on fault-free sessions |
| Controlled | Decoder, monitor, threshold, window, session groups | Exactly as in the session table of the main phase |

## 8. Analysis plan

1. **The session is the unit.** Every comparison is paired within a session:
   the same stretch of the same recording, with and without the repair.
2. **Medians with bootstrap intervals** over sessions, 5,000 resamples, the
   same function the lead-time analysis uses. No interval with fewer than
   three sessions.
3. **Counts with Wilson intervals**, the same function the decision-rate
   analysis uses.
4. **By fault type.** An average over fault types is shown but no claim is
   made from it.
5. **Reporting group only.** The calibration summary comes from the fitting
   group. Results come from the reporting group. Nothing in this experiment is
   tuned on data, so the threshold-selection group is not used at all.
6. **All repairs, all failure points, every time.** Including the ones that
   fail.
7. **Sealed and undesigned faults are never pooled.**
8. **The report is not edited by hand.**

## 9. How it is run

After `make_session_table.py`, as one more analysis:

```bash
python3 physical/recovery/code/repairs.py --selftest      # any time; needs no recordings
python3 physical/recovery/code/analyze_recovery.py
```

It writes `P8_RECOVERY.md`, `recovery.json` and `recovery_sessions.json` to
`physical/data/results/`.

## 10. What it cannot show

- **It is not a person controlling a cursor.** The error is decoding error on
  recorded frames. A user adapts to a decoder, and a recording cannot.
- **R4 is given the truth.** A real device has it only during a calibration
  task.
- **The onset is an upper bound.** No deployed system knows it.
- **Five-minute sessions.** A repair is scored over one to four minutes. A
  repair that helps at first and drifts later would look better than it is.
- **The faults are still mostly designed.** P-5 has ten sessions.
- **One apparatus in one room.** A recovery measured here is not an estimate
  of recovery in an implanted array.
- **It cannot show enhancement from the fault itself.** If any repair leaves
  decoding better than before, the likeliest reason is that the frozen decoder
  had gone stale, and the report should say so.

## 11. What "building" would mean, and what is not designed

Everything above is analysis after the fact. A version in which the bench
repairs itself during a session would be a further experiment. Two forms are
conceivable: the recording program renormalises the live signal when the
monitor warns, or the hardware compensates, for example by raising the camera
exposure when the whole field has dimmed. Neither is designed here. Either
would need a monitor running inside the recording loop, which the present
software does not have, and new sessions.

The reason to do P-8 first is that it shows which repairs are worth building.
There is no point building a live repair that the recordings already show
does not help.

## 12. How this attaches to the frozen plan

The preregistration was frozen on 24 September 2026 with seven experiments.
Its own section 9 says how to add to it: a new numbered section appended at
the end, dated, stating whether the data it governs had been seen.

**That has not been done.** `03_PREREGISTRATION_DRAFT.md` holds the text that
would be appended. It becomes part of the plan only when the researcher
approves the design and gives the instruction to append it. If that happens
before the bench records anything, P-8 is preregistered in the full sense. If
it happens after, the amendment must say so at its head, and P-8 is reported
as exploratory.
