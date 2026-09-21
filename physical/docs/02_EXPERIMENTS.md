# The experiments

Six experiments, **P-1** to **P-6**. Each states what it tests, which variable it
moves, what is recorded, and what each outcome would mean.

Read `01_RESEARCH_DESIGN.md` first. Build instructions are in
`04_BUILD.md`; the code is in `physical/code/` and explained in
`05_SOFTWARE.md`.

**The numeric predictions live in `09_PREREGISTRATION.md`**, which must be
frozen before anything is recorded. This document says what each outcome would
*mean*; that one says what was *expected*, with thresholds attached, so that
"quiet enough" cannot be decided after seeing the graph.

---

## The apparatus in one paragraph

A screen displays a grid of grey patches. Each patch brightens and dims
according to a direction the computer chose, in the way a direction-tuned brain
cell fires faster for its preferred direction. A camera in a sealed dark box
watches that screen; each small region of the camera image acts as one
"channel", standing in for one electrode. A decoder learns to read the direction
back out of those channels. Then the system is degraded on purpose — a filter
over the lens, tape on part of the field, the stage rotated — at a moment chosen
and written down in advance.

**That last clause is the entire point.** It is the one property no human
recording has.

---

## P-1 — Does the apparatus work, and is it as hard as the real thing?

**Tests:** that there is anything to measure at all.
**Moves:** nothing. This is characterisation.
**Measures:** decoding error against the apparatus's own measured chance level.

### Why a "difficulty match" is required

An apparatus that decodes perfectly is useless here. If the direction can be read
off with no error, then degrading it barely changes anything and there is nothing
for a monitor to detect. Worse, comparing a system that decodes perfectly against
one that barely beats chance measures *difficulty*, not monitoring.

The real neural decoder sits at **54.6° of median angular error against a 90.7°
chance level** — a margin of **36.1°**. The apparatus must be tuned to roughly
that margin before anything else is run.

The tuning knob is **modulation depth**: how strongly each patch brightens with
direction. A simulation of this apparatus showed that at full modulation it
decodes to **0.0°**, which is useless, and that a depth of about **0.002** puts
it at the neural operating point.

### Protocol

1. Record 5 healthy sessions.
2. Run `bench.py margin` (see `05_SOFTWARE.md`).
3. If the margin is not within 6° of 36.1°, adjust modulation depth and repeat.
4. **Write the final depth down. Never change it again.** Every later session
   must use it or sessions are not comparable.

### Outcomes

| Result | Meaning |
|---|---|
| Margin within 6° of 36.1° | Proceed |
| Margin much larger | Apparatus too easy — lower the modulation depth |
| Margin much smaller | Too hard — raise depth or exposure |
| Cannot decode at all | Stop. Check the dither and timing first (`04_BUILD.md`, B-5 and B-6) |

---

## P-2 — The false-alarm rate *(the measurement nobody can currently make)*

**Tests:** how often the monitor warns when nothing at all is wrong.
**Moves:** IV2 (degradation absent).
**Measures:** DV2 false-alarm rate, DV4 silence-gate pass rate.

### Why this is the centre of the phase

On the archived data, genuinely fault-free recording amounts to **1.4 hours**.
A false-alarm budget of 0.1 events per hour cannot be estimated from that, by
anyone, ever. This experiment exists to fix exactly that.

### Protocol

1. Seal the box. Verify darkness with `bench.py darkframe`.
2. Record **101 healthy sessions minimum** — nothing touched, nothing degraded,
   nothing adjusted. 5 minutes each, about 8.4 hours, unattended overnight.
3. **Then record about four times more.** 101 is a floor, and the arithmetic
   below says how far above it the campaign needs to go.
4. **Change nothing during the campaign.** No cleaning, no refocusing, no
   re-seating cables. If something is changed anyway, write it in the log with
   the date — an undocumented mid-campaign intervention cannot be detected
   afterwards and would invalidate the arm.

### How much healthy recording is actually enough

*Added after the analysis code was written and the arithmetic was done
properly. The original figure of 101 sessions was chosen for the effort it
costs, not for what it can demonstrate, and those are different questions.*

Suppose the monitor is perfect and produces **zero** false alarms. Zero is not
a rate; it is an upper bound. Seeing no events in H hours puts a 95% upper
bound of about **3/H per hour** on the true rate — the standard "rule of
three". For that bound to reach the 0.1/hour budget, H must be about **30
hours of held-out healthy recording.**

101 sessions is 8.4 hours in total, and the fit and validation groups take
their share, leaving roughly **4 test hours**. Zero false alarms in 4 hours
supports an upper bound of about **0.75/hour** — seven times the budget.

**101 sessions is enough to catch a monitor that is noisy. It is not enough to
show that a quiet monitor meets the budget.** The two are different claims and
the write-up must make whichever one the data supports.

Thirty hours is about four unattended nights rather than one.
`make_session_table.py` and `analyze_falsealarm.py` both print the arithmetic
for whatever has actually been recorded; use their number, not this paragraph.

### Outcomes

| Result | Meaning |
|---|---|
| False-alarm rate within 0.1/hour | The monitor is quiet enough to deploy — the first time anyone has been able to say so with evidence |
| Above budget | Quantifies exactly how far off it is, which nobody currently knows |
| Silence gate fails, as it did computationally | Confirms the limit generalises beyond neural recordings |
| Silence gate passes | **The most surprising outcome available**, and it would mean the computational failure is specific to neural data |

---

## P-3 — Lead time from a known onset

**Tests:** how early the monitor warns, measured from a start time recorded
before the session began.
**Moves:** IV1 (onset), IV3 (type), IV4 (severity).
**Measures:** DV1 lead time, DV3 detection rate.

### Protocol

1. **Before each session**, run `draw_onset.py`. It picks the onset time, the
   fault type and the severity, writes them to a file, and **locks that file
   with a checksum.** Do this before the recording starts, every time.
2. Record the session. The degradation begins at the drawn time — imposed in
   software for gain and rotation faults, by hand for optical ones (a timer and
   a filter).
3. **101 degraded sessions**, spread across the four types and four severities.
4. Analyse with `analyze_leadtime.py`.

### Why the onset is drawn before rather than chosen after

If the onset is picked afterwards, the lead time depends on the person picking
it. Two analysts get two answers from the same recording. Locking it with a
checksum beforehand makes that impossible, and makes the claim checkable by
someone who does not trust you.

### Outcomes

| Result | Meaning |
|---|---|
| Positive lead time within the false-alarm budget | A usable warning, measured properly for the first time |
| Negative lead time, as computationally | The warning arrives after the failure — confirmed on an independent system |
| Lead time varies by fault type | Some failures are catchable and others are not; a more useful finding than a single number |

---

## P-4 — Correlation against usability *(the novel experiment)*

**Tests the hypothesis directly.**
**Moves:** nothing new — this is an analysis of P-2 and P-3 recordings.
**Measures:** DV5 correlation, compared against DV1 and DV2 **on the same sessions**.

### What is being tested

The field validates decoder-health monitors by correlating the monitor's score
against task performance. MINDFUL reports **r = 0.93 and 0.72** this way and
proposes the monitor for deciding when to recalibrate.

This experiment asks whether that validation supports the conclusion drawn from
it, by computing **both** on the same recordings:

- the correlation the field would report, and
- the lead time and false-alarm rate that decide whether the monitor is usable.

### Protocol

1. From every session in P-2 and P-3, compute the monitor's score and the task
   performance.
2. Compute the correlation between them — the number the field reports.
3. **Then compute it again with the time trend removed**, and again on changes
   rather than levels. Both series drift, and any two drifting series correlate.
4. Place those beside the lead time and false-alarm rate from the same sessions.

### Why this needs the physical apparatus

It cannot be done on archived data, because the lead time there depends on an
onset nobody recorded and the false-alarm rate is not estimable from 1.4 hours.
**Both sides of the comparison have to come from the same recordings**, or the
comparison means nothing.

### Outcomes

| Result | Meaning |
|---|---|
| **High correlation, unusable lead time or false-alarm rate** | **Hypothesis supported.** Correlation-based validation does not support the claims made from it — a direct, checkable methodological finding about how this field validates its monitors |
| High correlation, usable warning | Hypothesis falsified. Correlation-based validation is adequate, which strengthens the published approach and is equally worth reporting |
| Correlation collapses when the time trend is removed | Shows the published correlations may be inflated, and that the control is necessary |

**All three outcomes are publishable, and this project cannot predict which it
will get.** That is what makes it an experiment.

---

## P-5 — Faults nobody designed

**Tests:** whether a monitor tuned on invented faults handles real ones.
**Moves:** IV3, extended to physical interventions.
**Measures:** DV1, DV2, DV3, reported in a **separate table**.

Every degradation in the computational half was an equation applied to recorded
numbers. Nobody has checked whether real degradation resembles them.

### Protocol

Cause a real fault by hand, note the exact time, let the recording run through.

| Intervention | How |
|---|---|
| Connector loosening | Half-unseat the camera ribbon, then re-seat it |
| Optical attenuation | Slide a neutral-density filter in front of the lens |
| Contamination | A fingerprint on the lens edge |
| Mechanical rotation | Turn the stage with the stepper motor, recording the angle |
| Thermal | Hair dryer, lowest setting, at least 30 cm, no more than 60 s, component below 50 °C |

You know *when* it started because you caused it. You did **not** design what it
would look like — that is the whole point.

Recorded with `run_session.py --undesigned`, and the onset written down
immediately afterwards with `note_onset.py`. Analysed by
`analyze_leadtime.py --undesigned`, which reports them in their own table beside
P-3's and never pools the two: a stopwatch is weaker evidence than a checksum,
and pretending otherwise would hand back the argument the rest of the phase
rests on.

### Outcome

If undesigned faults are meaningfully harder to detect, that is a finding about
how fault benchmarks are built **including this project's own**, and it belongs
in the write-up as a headline rather than a limitation.

---

## P-6 — How often should a monitor decide?

**Tests:** whether deciding less often makes monitoring easier.
**Moves:** IV5, decision rate — **set in analysis, costing no extra recording**.
**Measures:** DV3 detection at a fixed false-alarm rate, across decision rates.

### Why this is worth asking

The computational monitor failed for a reason unrelated to the detector: a
false-alarm budget of 0.1 per hour was applied to a system deciding **720 times
an hour**, which demands a per-decision false-positive rate of 0.00014.

Deciding less often should help twice over — a looser per-decision budget, and
more evidence behind each decision. If that holds there is a **decision-rate
law** for monitoring any drifting many-channel sensor.

On the archived data the two participants **disagree about which way the curve
goes** (rising +11.5% on one, falling −18.2% on the other) with confidence
intervals spanning 62% to 99%, because the threshold rests on 29 and 21
fault-free sessions. It cannot be settled there.

### Protocol

Re-score the P-2 and P-3 recordings at every decision rate from 720 per hour
down to one per session. **No extra recording is required.**

### Outcomes

| Curve | Meaning |
|---|---|
| **Rises** | Deciding less often genuinely helps. A design rule for any drifting sensor array: *check this often, and no more.* |
| **Falls** | Pooling destroys more than it buys, and the correct design move is the opposite of what the analysis suggests |
| **Flat** | The failure is in the detector, not the sampling — sending the next attempt somewhere completely different |

---

## Summary: what each experiment costs

| Experiment | Sessions | Time | Attended? |
|---|---|---|---|
| P-1 calibration | 5 | 25 min | yes |
| P-2 healthy campaign | 101 floor, ~360 to demonstrate the budget | 8.4 h floor, ~30 h to demonstrate the budget | **no — overnight** |
| P-3 degraded sessions | 101 | 8.4 h | partly |
| P-4 correlation analysis | 0 | minutes | analysis only |
| P-5 undesigned faults | 10 | 50 min | yes, by hand |
| P-6 decision-rate curve | 0 | minutes | analysis only |
| **Total recording** | **~217 at the floor, ~480 to demonstrate the budget** | **~18 h at the floor, ~40 h to demonstrate the budget** | mostly unattended |

Two of the six experiments need no recording at all, because the decision rate
and the correlation are analysis choices. That is what makes this affordable.

**If time runs short, cut P-5 and P-6 before P-2.** P-2 is the measurement that
does not exist anywhere else, it is the one that runs while you sleep, and
every other result in the phase is reported against the threshold it produces.

The extra P-2 hours are the cheapest thing in the project: the box records by
itself, and nobody has to be present. They are also the only thing that buys
precision on the false-alarm rate — no analysis choice can substitute for
fault-free hours.
