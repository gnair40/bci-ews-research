# Research Plan 2025-26

*Aligned to the second page of ISEF Form 1A — Student Checklist.*

**Name:** Gayathri Nair
**School:** Central Bucks High School South
**Adult Sponsor:** Michelle Rhodes
**Submission date:** 15 September 2026
**Category:** Systems Software / Biomedical Engineering `[[RESEARCHER — confirm]]`

**Project Title:** *Seeing Failure Before It Shows: Building and Validating a
Decoder-Health Monitor for Neural Interfaces*

---

> ## Status, added 20 September 2026 — read before using this document
>
> **This is the September submission exactly as submitted. It has not been
> rewritten, and it will not be.** A submitted plan that quietly changes to
> match later decisions is not a record of anything.
>
> **The physical experiment described in Section C changed on 20 September
> 2026**, five days after this was submitted. The hypothesis was replaced, the
> experiments were rebuilt as P-1 to P-6, and the design now lives in
> `physical/` rather than in `research/`.
>
> What changed, in one line each:
>
> | | September plan (below) | Current design (`physical/`) |
> |---|---|---|
> | Physical question | Does the monitor's early-warning signal behave on a rig the way it does on neural data? | Does correlation with task performance — the way this field validates such monitors — support the conclusions drawn from it? |
> | Physical experiments | Phases 7–10 | P-1 to P-6 |
> | Healthy recording | 101 sessions | 101 is a floor; ~30 held-out hours to demonstrate the false-alarm budget |
> | Code | `rig/` | `physical/code/` |
>
> `research/RIG_PREREGISTRATION.md` §14 states what carried over and what did
> not. `physical/docs/00_WHY_THIS_PHASE_EXISTS.md` gives the reasoning.
>
> **The computational work in Sections A, B and D is unaffected**, as is the
> Risk and Safety subsection, which describes the same apparatus.
>
> **For the December final plan**, Section C's physical half has to be rebuilt
> from `physical/docs/01`, `02`, `03` and `06`. Nothing else needs to move.

> ## Note on scope and voice
>
> This is the September submission. It is written in the third person throughout,
> as a formal research report rather than a personal account.
>
> It is a summary, not the complete plan. The full methods, the preregistered
> predictions, the pass/fail criteria and the results so far are in the project
> repository, and all of it will be submitted with the December final plan once
> the experimental portion is running. Nothing here is inaccurate; detail has
> been left out, not altered. Where a section is short on purpose, it says so.
>
> Section C's Risk and Safety subsection is the exception. It is complete and
> unsummarised. A review committee cannot evaluate a project it cannot see, and
> being vague about safety is the one thing that would cause a plan to be
> rejected rather than protected.
>
> Step-by-step replication instructions for every computational stage are in
> `research/REPLICATION_GUIDE.md`. The physical build was detailed procedure by
> procedure in `research/EXPERIMENTAL_PROCEDURES.md`; **as of 20 September 2026
> that part is superseded by `physical/docs/`** — see the status note above.

---

## A. Rationale

Brain-computer interfaces let people with paralysis move a cursor by imagining
movement. A grid of small electrodes sits in the motor cortex and picks up
activity from nearby neurons, and software called a decoder turns that activity
into cursor motion. The hard part is not getting this to work on day one. It is
keeping it working. The recorded signal keeps changing: electrode impedance
shifts, individual neurons stop being picked up, and the link between brain
activity and intended movement moves. Long studies show how slow and steady this
is. Barrese et al. (2013) examined how 78 implanted arrays failed. Sponheim et
al. (2021) tracked more than six thousand recording sessions across nine years.
Hughes et al. (2021) followed one person's array for five years. Because the
change is gradual it is easy to miss, and a decoder can keep producing confident
output from a signal it no longer matches. Pun et al. (2024a) showed the change
is visible in the signal itself, not only in how well the person does the task.

Most of the field treats this as something to correct rather than something to
notice. Karpowicz et al. (2025), for example, hold performance steady by
realigning the underlying patterns so a fixed decoder keeps working. The usual
fallback is recalibration: the user stops, does a guided block, and the decoder
gets refit. That costs the person time, needs supervised data, and on many
systems stops them using the device at all. At present it happens on a schedule
instead of when there is evidence it is needed. The standard way to predict a
change like this comes from dynamical systems theory. As a system nears a tipping
point it recovers more slowly from small disturbances, so its variance and
autocorrelation rise (Scheffer et al., 2009), and Maturana et al. (2020) applied
that idea to human brain recordings to predict seizure risk. But the idea is
disputed, and the criticism matters here. Wilkat et al. (2019) found no sign of it
before human seizures. Helmich et al. (2024) argue the clinical evidence is
thinner than commonly assumed and say the assumptions should be checked first.
van der Bolt et al. (2021) showed that the slower a system responds, the longer a
recording is needed before the signal is visible at all, which is a problem for
something that changes over months. This project tests whether those assumptions
hold in this setting rather than assuming they do.

There is therefore a substantial body of work on fixing drift, much less on
catching it early, and no agreed way to check whether something that claims to
catch it actually works. That last gap is the target of this project, and it
exists for a specific reason. In recordings that were only observed, nobody wrote
down when the decline started. Whoever analyzes the data picks the start point
afterward. Any claim about how early a warning arrived therefore depends partly
on that choice instead of on what actually happened, and the false alarm rate
cannot be worked out at all. Those two numbers — how early the warning comes and
how often it is wrong — are the only ones that decide whether a warning system is
worth having, and both become measurable only when the experimenter controls when
the degradation starts and records it in advance.

The recordings used here are the ones Pun et al. (2024a) released alongside their
instability study, archived publicly on Dryad under a CC0 public-domain
dedication (Pun et al., 2024b). They cover two BrainGate participants, designated
T11 and T5, across 21 trial days and 3,301 cursor trials, with T11 recorded
roughly two years after implant and T5 closer to six. That is real chronic human
data from arrays that had already been drifting for years, which is the setting
the problem actually occupies rather than a simulation of it, and because the
files are public, any other group can run the same test on the same signal and
obtain the same answer. What the recordings do not carry is an onset, so this
project supplies one: degradations are applied to the recorded neural features
with start times drawn and locked to disk before any detector exists. The
implication is that lead time and false alarm rate stop being estimates that
depend on an analyst's judgment and become quantities on which two methods can be
compared directly. That is what converts decoder-health monitoring from a claim
into a measurement, and it is why the benchmark matters more than any single
detector that might pass it. It also means a negative answer is worth having: if
a warning cannot be delivered early enough to be useful, or cannot be delivered
without excessive false alarms, that is a limit the field should know before a
monitor is deployed on the assumption that it works.

This matters because implanted brain-computer interfaces are leaving the research
laboratory (Hughes et al., 2021; Karpowicz et al., 2025; Pun et al., 2024a), and
the population they are aimed at is not small. About 5.4 million Americans,
roughly one in fifty, live with paralysis; 41.8% of them are unable to work, and
stroke and spinal cord injury together account for 61% of cases (Armour et al.,
2016). In more than twenty years of the BrainGate trials, fewer than two dozen
people have received an implant, and the bottleneck is not only surgical. Across
14 participants and 20 arrays, the share of electrodes recording usable activity
fell from 41% in the first three months to 34% in the last, and 3 of the 20
arrays stopped producing consistent decoding signals altogether (Hahn et al.,
2025). Keeping a decoder working through that requires recalibration, and a 2026
systematic review of 58 studies found that it still generally requires a
specialist research team (Swanson et al., 2026). Today recalibration happens on a
schedule, which means users sit through sessions they did not need while
continuing to rely on a decoder that has already drifted between them. A warning
that fired on evidence instead of on a calendar would return that time and catch
the failures a calendar misses. Underneath this is a question every regulated
medical device must answer before it can become one: how does anyone know it is
still working? For decoders there is no accepted answer, and no accepted way to
check whether a proposed answer is any good. A field cannot certify what it
cannot measure, so this is a prerequisite for these devices reaching the people
who need them rather than a refinement to be added afterward.

### Real-world impact, in more detail

*On the official form this folds into the Rationale. It is kept separate here
because it answers a different question, and because some forms request it on its
own.*

**What does not currently exist.** Three things, stated specifically because
"novel" means nothing on its own. First, there is no public dataset of decoder
degradation in which the moment of onset is known, because in real recordings
nobody recorded it. Without that, the two numbers that decide whether a warning
system is worth deploying cannot be computed at all, by anyone. This project
builds that corpus. Second, there is no agreed battery that a decoder-health
monitor has to pass, so any group can report whichever measure flatters its own
system. This project builds that battery, and its first requirement is the one
most often skipped: the monitor must be silent when nothing is wrong. Third, a
monitor that reports only "something is wrong" is close to useless in practice,
because the correct response to a failing electrode is not the correct response to
a user simply doing something different. The monitor built here is designed to
distinguish the two, treating a change of task as an explicit category rather
than as a false alarm.

**The failure mode is invisible, which is what makes it dangerous.** A pacemaker
that stops has an obvious signature. A decoder that has drifted keeps producing
confident output and is merely increasingly wrong, so the person using it cannot
tell whether the interface is degrading or whether they are tired, distracted, or
having a bad day. That ambiguity does more damage than a clean failure would.
Someone unable to distinguish the two either stops trusting the device on days it
is fine or keeps trusting it on days it is not, and for a device used to move a
cursor or to speak, both outcomes are serious.

**Benchmarks are how fields progress.** The monitor is the smaller half of this
work. The larger half is that once a shared standard exists, competing systems
can be measured against it rather than against their own best cases, and the next
group's improvement becomes provable rather than asserted. That is also the part
that survives whatever this project's own monitor turns out to do, which is
precisely why the grading system was built before the thing being graded.

**The question may not be about brains at all.** The underlying issue is what
happens to any sensor array with many channels that drifts slowly, which is why
part of this experiment runs on physical hardware rather than on neural
recordings. If the answer generalises, it applies to health monitoring of
implanted and embedded sensor systems well beyond this one, and the same battery
transfers with it.

**The limits, stated plainly.** Nothing here is a medical device, nothing is
tested on a person, and no clinical benefit is claimed or demonstrated. This is a
measurement and evaluation project. Within those limits the claim is still
substantial: a safety-relevant question that any of these devices will eventually
have to answer is currently unanswerable, not because it is hard but because the
data needed to answer it does not exist. This project builds that data, and the
standard that goes with it.

---

## B. Research Question, Engineering Goal, Hypothesis, and Expected Outcomes

These are stated separately so that an engineering target is not mistaken for a
scientific claim.

**Research question.** When a neural interface begins to degrade, does the
statistical structure of the recorded signal change before task performance does?
And if it does, can that change be distinguished from the change produced when
the user is simply doing something different?

**Engineering goal.** Build a monitor that converts such a change into a useful
warning, and — more importantly — build the test that determines whether any
monitor of that kind works.

**Hypothesis.** For degradations whose start times are controlled and recorded in
advance, a monitor reading only the input signal will warn before task
performance crosses a degradation threshold, at a false alarm rate low enough to
be worth having.

**Conditions for rejection, fixed in advance.** The hypothesis is rejected if the
warning usually arrives at or after the performance drop, or if the false alarm
requirement cannot be met at any operating point.

**Expected outcomes.** Two are informative, which is the test of whether this is
an experiment rather than a demonstration. If the monitor warns early enough at
an acceptable false alarm rate, the result is a method for triggering
recalibration on evidence instead of on a schedule. If it does not, the result is
a measured limit on how early this class of failure can be detected at all,
together with the reason — and that limit is worth publishing, because it would
otherwise be discovered by whoever deploys such a monitor first. The benchmark is
the deliverable in either case. Reporting that the idea does not work is
preferred to tuning it until it appears to.

**A prerequisite problem.** In observational recordings nobody knows when
deterioration actually began, so "how early was the warning" depends on how the
analyst defines the event. This project's answer is to construct data in which
the onset is chosen and written down ahead of time.

---

## C. Research Methods / Project Summary

### Materials and Equipment

**Computational (Arm A)**

1. Standard personal computer running macOS, Linux, or Windows with WSL
2. Python 3.11 or newer
3. Git version control software
4. Open-source Python libraries: NumPy, pandas, SciPy, h5py, Matplotlib, and
   requests
5. MINDFUL dataset (Pun et al., 2024b), Dryad DOI 10.5061/dryad.n2z34tn5s,
   released under a CC0 public-domain dedication, approximately 393 MB

**Physical validation rig (Arm B), approximately $150 total**

6. Raspberry Pi 4 Model B single-board computer, 4 GB RAM — quantity 1
7. microSD memory card, 32 GB, A2 or U3 speed class — quantity 1
8. Official Raspberry Pi USB-C power supply, 5 V 3 A — quantity 1
9. Raspberry Pi Camera Module 3, with the 15-pin ribbon cable supplied —
   quantity 1
10. Display: monitor, tablet, or laptop screen, minimum resolution 1280 × 720,
    with adjustable brightness — quantity 1
11. Cardboard enclosure, at least 40 × 30 × 30 cm — quantity 1
12. Matte black paper or matte black paint, sufficient to line the enclosure
    interior including the lid — quantity 1
13. Camera mount: small tripod or rigid bracket — quantity 1
14. Black gaffer or electrical tape — 1 roll
15. Stepper motor and driver: 28BYJ-48 5 V motor with ULN2003 driver board —
    quantity 1
16. Jumper wires, female-to-female, 20 cm — quantity 6
17. Neutral density filter: photographic ND 0.6 gel sheet — quantity 1
18. Temperature and humidity sensor: DHT22 or AM2302, on a breakout board with
    the pull-up resistor fitted — quantity 1
19. External storage: 128 GB USB flash drive — quantity 1

No item on this list is hazardous. The design requires no mains wiring, no
soldering, no chemicals, and no heating element.

### Procedures

The work proceeds in two arms. Arm A is computational and uses the archived
dataset. Arm B is a physical validation rig, built to test whether Arm A's
conclusions are specific to neural tissue or general to any slowly drifting
multichannel sensor. Command-by-command instructions for every computational
stage are in `research/REPLICATION_GUIDE.md`; the physical build is detailed
procedure by procedure in `research/EXPERIMENTAL_PROCEDURES.md`.

**Stage 1 — Acquire and characterise the dataset.** The MINDFUL archive is
downloaded through the Dryad API using a scripted, checksummed procedure. Raw
files are stored read-only and are never modified; all derived data is written to
a separate location. A loader is written for the nested MATLAB file structure and
verified against the depositors' own published analysis code. Dataset structure
is then characterised and reported: two participants, 21 trial days, 54 blocks,
3,301 trials, with per-participant feature counts and inter-session gaps
recorded.

**Stage 2 — Establish a reference decoder and a measured chance level.** A
ridge-regression velocity decoder is fit on held-out training blocks to convert
neural features into cursor velocity, reproducing the published baseline as a
correctness check. Chance performance is established empirically, by shuffling
the pairing between neural data and intended direction, rather than assumed from
theory.

**Stage 3 — Test the original idea, under a design fixed in advance.** The
early-warning-signal hypothesis from dynamical systems theory is tested directly:
whether variance and autocorrelation of the neural signal rise ahead of a decline
in task performance. The deterioration definition, the observable, and the
success criteria are frozen and committed before the analysis is run, so the
result cannot be produced by choosing a favourable definition afterward.
Synthetic positive and negative controls with known answers are built first, to
confirm the analysis can detect an effect that is genuinely present and does not
report one that is absent.

**Stage 4 — Construct ground truth by fault injection.** Four degradation modes
are applied to the recorded neural features: firing-rate loss, channel dropout,
gain drift, and geometry rotation. Each is applied as a monotone ramp at one of
several severity levels, producing approximately 1,850 episodes. Every onset time
is drawn pseudo-randomly, written to disk, and locked under a SHA-256 checksum
before any detector is written, so no onset can be adjusted after detector
behaviour is seen. The injection code is verified to leave all pre-onset data
bit-identical to the original recording, so that no detector can respond to a
leak rather than to the fault. Severity levels are verified to form a true
ladder, so that a larger severity is always a worse fault.

**Stage 5 — Preregister the evaluation before building the monitor.** Outcome
measures, success thresholds, and directional predictions are written to a
timestamped file and committed to version control, together with the commit hash
and the checksums of the input data, before the corresponding data are examined.
Amendments are permitted but must be recorded with a stated reason and a date.

**Stage 6 — Build the monitor and the grading battery.** Candidate detectors are
fit on healthy data only, using one-class methods, and produce a continuous risk
score for each 30-second analysis window. A five-part gate battery is applied,
described under Data Analysis below. The full configuration grid — combinations
of detector, baseline policy, and preprocessing transform, across both
participants — is run in its entirety, and every configuration is reported
including those that perform poorly.

**Stage 7 — Interrogate the result rather than report it.** Follow-up analyses
test the result against its own weakest points: whether a change of task is
mistaken for a fault, whether performance depends on how stale the calibration
is, whether the apparent effect is a property of the signal or of the window
geometry, whether any decision rule does better than a simple threshold, and how
much independent information a recording session actually contains. Where a claim
cannot be supported, it is withdrawn and the withdrawal is recorded.

**Stage 8 — Audit the project against itself.** Automated checks verify that
every number in every report can be regenerated from the stored data, that no
script reads a file produced by a later stage, that every documented command is
accepted by the script it names, and that every statistical claim has a recorded
justification. The analysis code is covered by unit tests, and the tests are
themselves validated by reintroducing known bugs and confirming the tests catch
them.

**Stage 9 — Construct the physical rig.** A Raspberry Pi camera is mounted inside
a light-sealed matte-black enclosure facing a display. The display presents a
pattern encoding a known direction; each region of the camera image serves as one
channel; the same decoder architecture predicts direction from those channels.
Calibration establishes that the rig produces a working decoder above its own
measured chance level before any degradation is introduced.

**Stage 10 — Degrade the rig under two conditions.** *Designed* faults mirror the
four injected modes and are imposed through software and controlled hardware.
*Undesigned* faults come from real physical interventions — loosening the camera
ribbon, applying the neutral density filter, smudging the lens, rotating the
stage with the stepper motor, warming the board — where the start time is known
because it was caused, but the resulting signature was not designed in advance.
The two classes are recorded and reported separately.

**Stage 11 — Sweep imposed drift speed.** A brightness drift with a controlled
time constant is imposed and swept across log-spaced levels, with repeated
healthy blocks recorded at each level. This produces a calibration curve of
monitorability against drift speed, on which the neural measurement can be placed
as a single point. A separate set of recordings runs over several weeks with
nothing injected at all, capturing whatever drift the rig produces on its own.

**Data collection.** All recording is automated by scripted capture. Block
length, sampling rate, and window geometry are fixed in advance and matched to
the neural analysis. Ambient temperature and humidity are logged alongside every
block. Every reported figure is regenerated from stored data files by a script.

### Risk and Safety

**This subsection is complete and unsummarised.**

**Human participants: none.** No person is recruited, surveyed, interviewed,
photographed, recorded, or measured at any stage, including the researcher. The
camera operates inside a closed enclosure facing a display; no person is ever in
its field of view or serves as a source of data. The archived dataset was
collected years earlier by other researchers under their own institutional
approvals, is de-identified, and is released under a CC0 public-domain
dedication. Where project documents use the word "participant," it refers to the
label attached to a de-identified published recording, following the depositors'
own convention. It never refers to a person recruited for this project. Form 4
and SRC human-participants approval are not expected to be required; this will be
confirmed with the SRC rather than assumed.

**Vertebrate animals: none.** No animal work of any kind.

**Potentially hazardous biological agents: none.** No biological material of any
kind.

**Hazardous chemicals, activities, and devices:**

| Item | Assessment |
|---|---|
| Electrical supply | 5 V DC from a regulated USB supply. No mains wiring, no exposed conductors, no capacitors above logic level, no batteries beyond a sealed USB power bank. |
| Stepper motor | 5 V low-torque hobby motor with driver board. Operated only with the enclosure closed; hands kept clear while powered. |
| Display | Standard consumer monitor or tablet, operated inside a closed enclosure. Not viewed at close range at high brightness. |
| Thermal intervention | Household hair dryer on its lowest setting, at no less than 30 cm, in bursts of no more than 60 seconds, with component temperature not exceeding 50 °C. No heat gun, hotplate, open flame, or oven is used at any point. |
| Optical filter | Photographic neutral-density gel sheet. Inert plastic; no hazard. |
| Chemicals | None. No solvents or consumables; adhesives limited to hot glue. |
| Sharps and tools | Scissors and craft knife for cardboard, used with a cutting mat. Soldering is not required by the design; if it becomes necessary it will be performed under adult supervision with eye protection and ventilation. |

**Waste and environmental impact.** No hazardous waste is generated. Electronic
components are retained for reuse; cardboard is recycled.

**Supervision.** All construction is performed at `[[RESEARCHER — home / school
lab]]` under the supervision of the Adult Sponsor named above.

Form 3 is not expected to be required for low-voltage bench electronics not
connected to any person. This will be confirmed with the SRC rather than assumed,
and the Rules Wizard will be re-run once the build decision is final.

### Data Analysis

**What is being analyzed.** Each recording block is divided into overlapping
analysis windows, 30 seconds long and advancing 5 seconds at a time. For each
window, a detector produces one number, called a risk score. An episode
therefore becomes a series of risk scores over time. The analysis asks two things
of that series: whether it rises before task performance falls, and whether it
stays flat when nothing is wrong.

**Splitting the data.** Blocks are divided into three sets before any analysis
begins: one for fitting, one for validation, and one for testing. Detectors are
fit only on healthy data from the fitting set, so no detector sees a fault while
it is being built. The validation set is used to choose the one adjustable
setting. The test set is looked at once, at the end.

**Preregistration.** The outcome measures, the success thresholds, and the
predictions are written into a timestamped file and committed to version control
before the matching data are collected or examined. The file records the commit
hash and the checksums of the input data, so the timing can be verified
afterward. Changes are allowed, but each one is recorded with a date and a
reason. Predictions that turn out wrong are reported as wrong.

**The one adjustable setting.** A monitor has one knob: the warning threshold.
Setting it low produces early warnings but many false ones; setting it high
produces few false alarms but late warnings. Because that knob alone can produce
almost any result, it is not set by hand. It is chosen automatically on the
validation set as the lowest threshold whose false alarm rate stays within a
budget of 0.1 false alarms per hour. Lower is preferred because, within the
budget, an earlier warning is more useful. The chosen value is then fixed and
applied unchanged to the test set.

**The two main measures.** Lead time is the gap between the first warning and the
point where task performance crosses the degradation threshold, with positive
values meaning the warning came first. False alarm rate is the number of warnings
per hour of healthy recording. These are always reported together, along with the
threshold that produced them, because either one on its own can be made to look
good by giving up the other.

**The five gates.** Before lead time is discussed for any detector, that detector
has to pass five checks. They are applied in order, and a detector that fails the
first is not carried forward.

1. **Silence.** The risk score should not drift while nothing is wrong. Kendall's
   rank correlation is computed between risk and window index for each healthy
   episode in the test set. The gate passes if fewer than 10% of those episodes
   show a significant trend at p < 0.05.
2. **Rate invariance.** The risk score should be measuring something other than
   how much total activity is present. Spearman correlation is computed between
   the detector's healthy risk series and a simple mean-activity series, and the
   median absolute correlation has to be below 0.6.
3. **Comparator.** The detector has to produce a longer median lead time than the
   simple approach of counting spikes, at the same false alarm budget.
4. **Elapsed time.** The risk score should not be tracking how long the block has
   been running. Spearman correlation against window index is computed on healthy
   episodes, and the median absolute value has to be below 0.5.
5. **Detrend.** The silence check is run again after removing a linear trend from
   each series, to confirm the first result was not an artifact of how the trend
   test works.

The full grid of configurations, covering combinations of detector, baseline
policy, and preprocessing transform for both participants, comes to 48. All 48
are run and reported, including the ones that do poorly.

**Statistics.** Non-parametric methods are used throughout, because the samples
are small and the distributions are not normal. Confidence intervals come from
bootstrap resampling at the level of the episode rather than the individual
window. Windows within an episode overlap and are recorded seconds apart, so they
are not independent measurements, and resampling them as if they were would make
the data look larger than it is. Rather than assume this away, serial correlation
is measured: lag-1 autocorrelation is computed on the risk series, effective
sample size is calculated from it as n(1−r)/(1+r), and that number is reported
next to any confidence interval so a reader can see how much independent evidence
is behind it. Wherever autocorrelation is quoted, the window spacing used to
compute it is stated as well, since overlapping windows raise it on their own.

**Reporting by category.** Results are reported separately for each fault mode
rather than averaged together, because a monitor that handles one mode well and
three poorly would otherwise look the same as one that handles all four
moderately. Faults created by software injection and faults created by physical
intervention on the rig are also reported in separate tables. Whether a result
carries from one to the other is treated as something to test rather than assume.

**Analysis of the physical rig data.** The point of the rig is to find out
whether the result from the neural data is specific to brain tissue or general to
any slowly drifting multichannel sensor. That comparison only means something if
the rig data is analyzed the same way, so the same scripts are run on it without
modification. The window length, the step size, the detectors, the gates, and the
false alarm budget all stay as they were. Any change made to accommodate the rig
would have to be made to the neural analysis as well, and would be recorded as an
amendment.

**Checking the rig works before degrading it.** Before any fault is introduced,
the rig has to clear a calibration step: its decoder must predict direction from
the camera channels better than its own measured chance level, where chance is
established by shuffling the pairing between image data and intended direction
rather than assumed from theory. A rig that cannot decode above chance has
nothing to degrade, and no result from it would mean anything.

**The main comparison.** The quantity compared across the two systems is how much
independent information a session contains: the lag-1 autocorrelation of the risk
series and the effective sample size derived from it. Two conditions have to hold
for that comparison to be fair. First, the autocorrelation is computed on
non-overlapping windows, because overlapping windows raise it for reasons that
have nothing to do with the system being measured. Second, the rig blocks are
recorded at a length that gives the same number of windows as the neural
episodes, because this statistic is biased downward when the series is short, and
the size of that bias depends on the length. Comparing a long rig recording
against a short neural one would produce a difference that came from the
recording length rather than from the systems.

**The drift sweep.** Rather than asking only whether the rig resembles cortex,
the rig is used to impose a drift whose speed is set deliberately, and that speed
is swept across levels spanning roughly two orders of magnitude. At each level,
repeated healthy blocks are recorded and the same autocorrelation and effective
sample size are computed. This produces a curve of how monitorable an array is as
a function of how fast it drifts, on which the neural measurement can be placed
as a single point. The number of levels and the number of blocks per level are
set in advance by a power calculation rather than chosen by eye, since too few
blocks would produce a curve too noisy to read.

**The uninstructed arm.** A separate set of recordings runs over several weeks
with nothing injected at all, capturing whatever drift the rig produces on its
own. These are compared against the four designed modes by nearest-match
assignment, to see whether naturally occurring degradation resembles any of the
faults that were invented. A negative answer here would say something about how
fault benchmarks are built in general, including this project's own, so it is
reported either way.

**Predictions fixed in advance.** Numerical thresholds for each of these
comparisons are written into a separate rig preregistration, committed before the
rig is built, and each prediction states what result would falsify it and what
either outcome would mean. No comparison in this arm is left to be defined after
the data are seen.

**Checking the numbers.** Every figure that appears in a report is recalculated
from the stored data files by a script, so a number that stops matching its
source is caught rather than trusted. The analysis code has unit tests, and those
tests are checked by deliberately putting known bugs back into the code and
confirming the tests catch them.

### Artificial Intelligence (AI)

> `[[RESEARCHER — read, verify, and edit before submission. This records what
> occurred and must be checked against the current year's ISEF wording. An AI
> disclosure has to be the researcher's own statement.]]`

An AI assistant (Anthropic's Claude, accessed through Claude Code) was used as a
programming and drafting tool throughout this project. Specifically, it was used
to help write and debug the Python analysis scripts, to help build the
verification and reproducibility-checking tools, to assist in drafting written
documentation including portions of this plan, and as a discussion partner for
study design.

The following were determined by the researcher and not delegated: the research
question, the choice of dataset, the decision to construct ground truth by fault
injection, the selection of degradation modes and severity levels, the contents
of each preregistration, the thresholds for every gate, and the interpretation
and reporting of results. All AI-generated code was reviewed, executed, and
validated against the project's own verification gates, unit tests, and mutation
tests before any result derived from it was accepted. No data were generated or
fabricated by AI; all analyzed data originate either from the public MINDFUL
archive or from instrumented recordings made on the physical rig. A complete,
timestamped record of the development process, including errors made and
corrected, is maintained in the project's research log and version-control
history.

---

## D. Bibliography

Formatted in APA 7th edition style. **Author lists are abbreviated to the first
author pending expansion; APA requires every author up to twenty in the reference
list, so each entry must be completed from the published paper before
submission.**

Armour, B. S., et al. (2016). Prevalence and causes of paralysis—United States,
2013. *American Journal of Public Health*, *106*(10), 1855–1857.
https://doi.org/10.2105/AJPH.2016.303270

Barrese, J. C., et al. (2013). Failure mode analysis of silicon-based
intracortical microelectrode arrays in non-human primates. *Journal of Neural
Engineering*, *10*(6), 066014. https://doi.org/10.1088/1741-2560/10/6/066014

Hahn, N. V., et al. (2025). *Long-term performance of intracortical microelectrode
arrays in 14 BrainGate clinical trial participants* [Preprint]. medRxiv.
https://doi.org/10.1101/2025.07.02.25330310

Helmich, M. A., et al. (2024). Slow down and be critical before using early
warning signals in psychopathology. *Nature Reviews Psychology*, *3*, 767–780.
https://doi.org/10.1038/s44159-024-00369-y

Hughes, C. L., et al. (2021). Long-term intracortical microelectrode array
performance in a human: A 5 year retrospective analysis. *Journal of Neural
Engineering*, *18*(4). https://doi.org/10.1088/1741-2552/ac1add

Karpowicz, B. M., et al. (2025). Stabilizing brain-computer interfaces through
alignment of latent dynamics. *Nature Communications*, *16*.
https://doi.org/10.1038/s41467-025-59652-y

Maturana, M. I., et al. (2020). Critical slowing down as a biomarker for seizure
susceptibility. *Nature Communications*, *11*, 2172.
https://doi.org/10.1038/s41467-020-15908-3

Pun, T. K., et al. (2024a). Measuring instability in chronic human intracortical
neural recordings toward stable, long-term brain-computer interfaces.
*Communications Biology*, *7*. https://doi.org/10.1038/s42003-024-06784-4

Pun, T. K., et al. (2024b). *Data from: Measuring instability in chronic human
intracortical neural recordings toward stable, long-term brain-computer
interfaces* [Data set]. Dryad. https://doi.org/10.5061/dryad.n2z34tn5s

Scheffer, M., et al. (2009). Early-warning signals for critical transitions.
*Nature*, *461*, 53–59. https://doi.org/10.1038/nature08227

Sponheim, C., et al. (2021). Longevity and reliability of chronic unit recordings
using the Utah intracortical multi-electrode arrays. *Journal of Neural
Engineering*, *18*(6), 066044. https://doi.org/10.1088/1741-2552/ac3eaf

Swanson, E., et al. (2026). Recalibration of implantable brain-computer
interfaces to enable long-term independent use: A systematic review. *Journal of
Neural Engineering*, *23*(3). https://doi.org/10.1088/1741-2552/ae7694

van der Bolt, B., et al. (2021). No warning for slow transitions. *Journal of the
Royal Society Interface*, *18*(174), 20200935.
https://doi.org/10.1098/rsif.2020.0935

Wilkat, T., et al. (2019). No evidence for critical slowing down prior to human
epileptic seizures. *Chaos*, *29*(9), 091104. https://doi.org/10.1063/1.5122759

---

## Sections after D — all four are to be deleted before printing

Per the form's instructions, **Human Participants Research**, **Vertebrate Animal
Research**, **Potentially Hazardous Biological Agents**, and **Hazardous
Chemicals, Activities, and Devices** are all to be deleted. None applies, and
each is addressed in the Risk and Safety subsection of Section C.

---

## Checklist before submission

- [ ] Adult Sponsor has reviewed and signed
- [ ] Rules Wizard run for the current year
- [ ] Category confirmed
- [ ] AI subsection read, verified and edited by the researcher
- [ ] Supervision location filled in (Risk and Safety)
- [ ] Bibliography author lists expanded to full APA form
- [ ] Article numbers checked against each paper, or omitted
- [ ] SRC asked to confirm the Form 3 and Form 4 assessments
- [ ] The four inapplicable sections after D deleted
