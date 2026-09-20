# December final plan — Sections B and C, rebuilt for the physical design

**Drafted:** 20 September 2026.
**Status: DRAFT.** Not submitted. The September submission,
`research/RESEARCH_PLAN_2026-09-15.md`, remains the document of record until
this replaces it.

---

## What this document is, and what it is not

The September submission described a physical experiment that was redesigned on
20 September. This draft rebuilds the two sections that changed, from
`physical/docs/01_RESEARCH_DESIGN.md`, `02_EXPERIMENTS.md`,
`03_MATERIALS_AND_SAFETY.md` and `06_DATA_COLLECTION.md`.

**Written in the third person throughout**, as a formal research report, to
match the September submission's voice.

| Section | Status |
|---|---|
| A. Rationale | **Unchanged.** The computational work and the problem it addresses are unaffected. |
| B. Question, goal, hypothesis | **Rebuilt below.** The September hypothesis was tested and falsified; that is reported as a result, and a new hypothesis governs the physical phase. |
| C. Materials | **Unchanged.** The apparatus is the same one; the redesign changed the experiments run on it, not the parts list. Confirmed item by item against `physical/docs/03`. |
| C. Procedures | **Rebuilt below.** Stages 1–8 (computational) unchanged; Stages 9–11 replaced by six experiments, P-1 to P-6. |
| C. Risk and Safety | **Unchanged.** Same apparatus, same assessment, same absence of human participants. |
| C. Data Analysis | **Physical half rebuilt below.** The computational half is unchanged. |
| C. Artificial Intelligence | **Open.** Requires checking against the 2026-27 form and with the SRC. |
| D. Bibliography | **Open.** September used first authors only; December may require full author lists. |

Four items remain for the researcher to decide and are marked
`[[RESEARCHER]]` where they occur.

---

## B. Research Question, Engineering Goal, Hypothesis, and Expected Outcomes

These are stated separately so that an engineering target is not mistaken for a
scientific claim.

### B.1 What the September hypothesis produced

The September submission tested this hypothesis:

> For degradations whose start times are controlled and recorded in advance, a
> monitor reading only the input signal will warn before task performance
> crosses a degradation threshold, at a false alarm rate low enough to be worth
> having.

**It was falsified, cleanly, and the result stands.** For the monitor this
project built, on the participant with the longer record, median lead time was
**−20 seconds** — the warning arrives after the failure — at **3.4 false alarms
per hour** against a budget of 0.1; on the second participant, **−35 seconds**.
Ten of 48 configurations achieved a positive median lead time, and **none passed
all five gates**. The hypothesis was specific enough to be wrong, which is what it was for,
and the negative result is reported rather than repaired.

That answer closes the question it was asked about. It also exposes the question
that is actually open, which the physical phase addresses.

### B.2 The research question for the physical phase

> **How early, and at what cost in false alarms, can a decoder-health monitor
> warn that a sensor array is degrading — and does the correlation-based
> validation on which the field currently relies support the claims being made
> from it?**

The second half is the novel one. The current state of the art (Pun et al.,
2024) validates a decoder-health monitor by correlating its score against task
performance, reports correlations of r = 0.93 and r = 0.72, and proposes the
monitor as a means of deciding when recalibration should occur. No lead time and
no false-alarm rate has been reported for any monitor of this class, because
measuring either requires knowing when degradation began, and no observational
recording records that.

### B.3 Engineering goal

Build the apparatus and the benchmark on which those two numbers can be measured
at all: a multichannel sensor system whose failures begin at times drawn at
random and committed under checksum before each recording exists, and which can
be run unattended for long enough to bound a false-alarm rate.

**The deliverable is the measurement and the apparatus that makes it possible,
not a warning device.** A device issuing warnings at the currently measured lead
time would be a device that does not do what its label claims. What is built
afterward is decided by the results, and the conditions are set out in advance in
`physical/docs/08_WHAT_COMES_AFTER.md`.

### B.4 Hypothesis

> **A decoder-health monitor can show a strong correlation with task performance
> while simultaneously being unusable as a warning system — that is, a high
> correlation does not imply a usable lead time or an acceptable false-alarm
> rate.**

**Stated so that it can be falsified.** On recordings with constructed,
pre-committed degradation onsets, the monitor will achieve a correlation with
performance of **r > 0.7**, comparable to published values, while **either** its
median lead time is negative **or** its false-alarm rate exceeds 0.1 per hour at
the threshold required for 80% detection.

**Conditions for rejection, fixed in advance.** The hypothesis is rejected if the
monitor achieves r > 0.7 *and* a positive median lead time *and* a false-alarm
rate within budget. That outcome would mean correlation-based validation is
adequate after all — equally worth knowing, and a substantial strengthening of
the published approach.

A correlation below 0.7 by every measure renders the test inconclusive rather
than supporting either side, and is reported as such. A weakly correlated monitor
says nothing about whether correlation-based validation is sufficient.

### B.5 Variables

**Independent.**

| | Variable | Levels |
|---|---|---|
| IV1 | Degradation onset time | drawn at random and committed under checksum before each session |
| IV2 | Degradation present or absent | present / absent; roughly half of sessions are fault-free |
| IV3 | Degradation type | overall signal loss, channel dropout, per-channel gain drift, geometric rotation |
| IV4 | Degradation severity | 0, 0.25, 0.5, 1.0 |
| IV5 | Decision rate | 720 per hour down to one per session; set in analysis, at no recording cost |

**Dependent.**

| | Variable | Definition |
|---|---|---|
| DV1 | Lead time | seconds between the first warning and performance crossing its failure threshold; positive means the warning came first |
| DV2 | False-alarm rate | warnings per hour of recording in which no degradation was applied |
| DV3 | Detection rate | proportion of degraded sessions warned about, at a stated false-alarm rate |
| DV4 | Silence-gate pass rate | proportion of fault-free sessions in which the risk score shows no significant trend |
| DV5 | Correlation with performance | correlation between monitor score and task performance, computed raw, with the time trend removed, and on first differences |

A sixth quantity is recorded alongside DV1 and must not be confused with it.
**Detection delay** is the interval between the drawn onset and the first
warning — how long the monitor took to notice. Lead time asks whether the warning
was useful; detection delay asks whether the monitor was quick. A monitor can be
slow to notice and still give useful warning, if the decoder continues to work
for a period after the fault begins. **Detection delay cannot be computed on any
archived human recording**, and is the measurement this apparatus exists to make.

### B.6 Expected outcomes

All three are informative, which is the test of whether this is an experiment
rather than a demonstration.

| Outcome | What it would mean |
|---|---|
| Strong correlation, unusable lead time or false-alarm rate | **Hypothesis supported.** Correlation-based validation does not support the conclusions drawn from it. Since that is the standard method of validating this class of monitor, the evidence base for drift-triggered recalibration is weaker than it appears. |
| Strong correlation, usable warning | **Hypothesis falsified.** Correlation-based validation is adequate, strengthening the published approach. |
| Correlation collapses once the time trend is removed | Published correlations of this kind may be inflated by shared drift, and the control is necessary. |

This project cannot predict which will occur. Reporting that the idea does not
work is preferred to adjusting it until it appears to.

---

## C. Research Methods / Project Summary

### C.1 Materials and Equipment

**Unchanged from the September submission**, items 1 to 19, and confirmed item by
item against `physical/docs/03_MATERIALS_AND_SAFETY.md`. The redesign altered
which experiments are run on the apparatus, not what the apparatus is made of.
Approximate total for the physical items: $150.

No item on the list is hazardous. The design requires no mains wiring, no
soldering, no chemicals, and no heating element.

### C.2 Procedures

Stages 1 to 8 are computational and are unchanged from the September submission.
They are complete: the dataset is acquired and characterised, the reference
decoder established, the original hypothesis tested under a frozen design, ground
truth constructed by fault injection, the evaluation preregistered before the
monitor was built, the monitor built and graded, the result interrogated against
its own weakest points, and the project audited against itself.

What follows replaces Stages 9 to 11.

**Stage 9 — Build and calibrate the apparatus.** A camera is mounted inside a
light-sealed matte-black enclosure facing a display. The display presents a grid
of grey patches whose brightness encodes a direction, in the manner of a
direction-tuned cortical neuron firing faster for its preferred direction. Each
region of the camera image serves as one channel, standing for one electrode, and
the same decoder architecture used on the neural data predicts direction from
those channels.

Four bench checks must pass before any session is treated as data, each of which
catches a failure that would otherwise produce plausible numbers rather than an
obvious error: that the enclosure is light-tight, that recordings arrive intact
with no dropped frames or dead channels, that the delay between display and
camera is measured and stable, and that the sub-brightness-level signal survives
to the sensor.

**Stage 10 — Match the apparatus to the difficulty of the neural recordings
(experiment P-1).** An apparatus that decodes perfectly is useless for this work:
degrading it changes little, so there is nothing for a monitor to detect, and
comparing a system that decodes perfectly against one that barely exceeds chance
measures difficulty rather than monitoring. The neural decoder operates at 54.6°
of median angular error against a 90.7° measured chance level, a margin of 36.1°.
The apparatus is tuned, by adjusting the depth of brightness modulation, until its
own margin falls within 6° of that figure. Chance is established empirically by
shuffling the pairing between image data and intended direction, not assumed from
theory. The final modulation depth is recorded and not altered afterward; a change
mid-campaign would make sessions before and after it incomparable, and nothing in
the data would reveal that it had occurred.

**Stage 11 — Record the fault-free campaign (experiment P-2).** Sessions are
recorded with nothing touched, nothing degraded and nothing adjusted, unattended
and overnight. Each session's status is drawn and committed under checksum before
it is recorded, exactly as degraded sessions are, so that the two classes are
produced by the same procedure.

The quantity of recording required is set by the arithmetic rather than by
convenience, and is larger than the September plan assumed. A monitor producing
no false alarms in H hours supports a 95% upper bound of approximately 3/H per
hour on the true rate. For that bound to reach the stated budget of 0.1 per hour,
H must be approximately **30 hours of held-out fault-free recording**. One
hundred and one sessions of five minutes provides roughly four such hours once
the sessions used to build the monitor and to set its threshold are excluded,
supporting a bound of about 0.75 per hour — seven times the budget.

One hundred and one sessions is therefore sufficient to detect a monitor that is
noisy, and insufficient to demonstrate that a quiet one meets the budget. These
are different claims, and the write-up will make whichever the data supports.
`[[RESEARCHER — confirm the campaign length. Approximately four unattended
nights rather than one.]]`

**Stage 12 — Record the degraded sessions (experiment P-3).** Before each
session, a script draws the onset time, the degradation type and the severity,
writes them to a file, and records that file's SHA-256 checksum in an append-only
manifest. Because the checksum is written before the recording exists, the onset
cannot subsequently be adjusted to improve a result, and a reader who does not
trust the experimenter can verify that the files still match their checksums.

Two of the four degradation types are imposed automatically in software at the
drawn moment. The other two are physical — a neutral density filter slid in front
of the lens, tape applied over part of the field — and are imposed by hand at a
countdown the software prints. Where a hand-imposed fault is mistimed, the
discrepancy is recorded in the session note and the research log rather than
corrected silently.

**Stage 13 — Impose faults that were not designed (experiment P-5).** Every
degradation in Stage 12, and every degradation in the computational work, is an
equation someone wrote. Whether real degradation resembles them has not been
tested. Real faults are therefore caused deliberately — a camera ribbon cable
half-unseated and re-seated, a fingerprint on the edge of the lens, the stage
rotated by stepper motor, the board warmed within the limits set out in the Risk
and Safety subsection — and the time of each is written down immediately
afterward.

**These sessions are analysed in a separate table and are never pooled with
Stage 12's.** Their onsets come from a stopwatch rather than from a checksummed
file, which is weaker provenance. What they retain is the property that matters:
the signature of the fault was not designed in advance. A session of this kind
whose onset was not recorded cannot be analysed at all, and the analysis software
refuses to score it rather than treating it as fault-free.

**Stage 14 — Analyse (experiments P-4 and P-6).** Neither requires additional
recording. P-4 computes, on the sessions from Stages 11 and 12, both the
correlation the field reports and the lead time and false-alarm rate that decide
usability. P-6 re-scores those same sessions at every decision rate from one per
analysis window to one per session. The decision rate is an analysis choice
rather than a recording choice, so a single campaign yields the entire curve.

**Data collection.** All recording is automated. Session length, frame rate,
analysis window and step are fixed in advance and matched to the neural analysis:
a 30-second window stepping every 5 seconds, against neural data binned at 20
milliseconds and an apparatus running at 50 frames per second, so that one camera
frame corresponds to one neural bin. Ambient temperature is logged alongside every
session, because a camera sensor's dark current rises with temperature and would
otherwise be indistinguishable afterward from the drift being measured. Raw
recordings are written once and never modified; every reported figure is
regenerated from them by a script.

Approximately 217 sessions and 18 hours of recording at the floor, or
approximately 480 sessions and 40 hours to demonstrate the false-alarm budget,
the majority unattended.

### C.3 Data Analysis — physical phase

The computational analysis is unchanged. What follows replaces the passages
describing the rig.

**The same monitor, not a reimplementation.** The detector, the warning state
machine and the performance-failure threshold are imported from the computational
analysis rather than rewritten for the apparatus. If the physical phase used a
differently tuned monitor, any difference in result could equally be a difference
in the monitor. The apparatus changes; the object of study does not. Any change
made to accommodate the apparatus would have to be made to the neural analysis as
well and would be recorded as an amendment.

**Three groups, and a session belongs to exactly one.** The decoder and the
monitor are built from one set of fault-free sessions; the single adjustable
parameter, the warning threshold, is chosen on a second, held-out set; and the
false-alarm rate and lead time are reported from a third. A threshold chosen on
the sessions its performance is then measured on will always appear favourable,
because it was chosen to. Sessions are assigned in recording order rather than at
random, so that the group used to build the decoder is genuinely the earliest
data.

**The decoder is frozen.** It is fitted once, on the earliest fault-free
sessions, and never refitted — as a real implant is calibrated on one day and used
on later ones. The analysis is also run with the decoder refitted each session,
which makes between-session drift invisible. A result appearing under one and not
the other is a result about staleness, and is described that way.

**Reporting a rate against reporting a bound.** Where false alarms occur, a rate
is reported with an exact Poisson interval, and the upper end of that interval is
what the verdict rests on. Where none occur, no rate exists: an upper bound is
reported instead, together with the hours of recording behind it. Reporting "zero
false alarms" without that bound would read as the strongest available result
while being, on a short campaign, almost none.

**Warnings are timestamped at the end of the window that produced them**, since a
window's risk score cannot exist until its final second has elapsed. Timestamping
at the window's start would credit the monitor with knowledge up to thirty seconds
before the data existed and would inflate every lead time accordingly.

**A warning preceding the onset is a false alarm, not an early detection.** Where
the warning window ends before the fault began it contains no faulty data, and is
counted as a false alarm occurring within a degraded session. Counting such
warnings as detections is the most direct available means of manufacturing a
positive result, and they are excluded from every timing figure.

**Reporting by category.** Results are reported per degradation type rather than
averaged, because a monitor handling one type well and three poorly would
otherwise resemble one handling all four moderately. Designed and undesigned
faults are reported in separate tables. With approximately ten undesigned
sessions only a large difference is detectable, and a small difference is
reported as not measured rather than as no difference.

**Lead time and false-alarm rate are reported together, always.** Either can be
made to appear excellent by sacrificing the other: a monitor warning constantly
has unlimited lead time, and one never warning has a perfect false-alarm rate.
The pair is the result; neither figure alone is interpretable, and the verdict is
conditional on a stated budget.

**The silence gate.** Separately from counting alarms, each fault-free session is
tested for a monotonic trend in the risk score, and no more than 10% may show a
significant one. A score climbing steadily through every fault-free session will
cross any threshold eventually, whether or not it has yet. This is the same gate,
at the same threshold, that the computational analysis applied and failed on
fault-free neural recordings. Whether it fails on an apparatus containing no
biological material is among the more informative outcomes available.

**The correlation, computed three ways.** Both the monitor's score and task
performance drift with time, and any two drifting quantities correlate. The
correlation is therefore reported raw, with the time trend removed from both, and
on changes rather than levels. The hypothesis treats the correlation as strong if
any of the three exceeds 0.7, not the raw figure alone.

**The decision-rate curve.** Sessions are re-scored at each decision rate with a
fresh threshold chosen on the held-out fault-free sessions, so that rates are
compared at equal false-alarm cost rather than at a fixed threshold. Windows are
pooled by mean rather than maximum: the maximum of a block is a rescaled
threshold and delivers none of the evidence-pooling the question concerns.

Deciding less often loosens the per-decision budget by exactly the pooling
factor. At 720 decisions per hour a budget of 0.1 per hour permits a
per-decision false-positive rate of 0.00014, requiring an AUC of approximately
0.9992; at one decision per five-minute session it permits 0.0083, requiring
approximately 0.990. Against the 0.673 and 0.742 achieved on the neural
recordings, both remain distant. The looser budget alone is therefore not a
remedy, and what this experiment measures is whether the second mechanism —
more evidence behind each decision — contributes anything beyond it.

**Predictions fixed in advance.** What each outcome of each experiment would mean
is written into `physical/docs/02_EXPERIMENTS.md` and committed before any
recording exists. No comparison is left to be defined after the data are seen.
The superseded rig preregistration is retained as a record; its predictions P-R1
to P-R10 are not carried forward, and no result from this phase will be reported
as confirming or refuting them.

**Checking the numbers.** Every figure appearing in a report is regenerated from
stored data by a script, and reports are not edited by hand. Automated gates
verify that every headline number can be recomputed, that no script reads a file
produced by a later stage, that every documented command is accepted by the
script it names, and that every statistical claim has a recorded justification.

---

## Open items

| | Item | Needed for |
|---|---|---|
| 1 | Campaign length: 101 fault-free sessions, or approximately 360 | Stage 11, and the calendar |
| 2 | AI disclosure wording, checked against the 2026-27 form and with the SRC | Section C |
| 3 | Bibliography: first authors only, or full author lists | Section D |
| 4 | Supervision location for the build | Risk and Safety |
| 5 | Category confirmation (currently Systems Software / Biomedical Engineering) | Cover page |
| 6 | Whether `research/ISEF_RESEARCH_PLAN.md` is retired or becomes the base document | Assembly |

Item 1 is the only one that changes what is recorded. The remainder are
administrative and do not block the build.
