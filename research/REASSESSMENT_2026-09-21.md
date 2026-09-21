# Ground-up reassessment of the project

**Written:** 21 September 2026, on instruction to assume nothing in the
repository is correct merely because it is already there.

**Method.** I re-derived the load-bearing claims from the stored data rather
than reading the documents that assert them, looked for the objections a
hostile reviewer would raise, and checked which of the project's own
justifications survive being tested. Two did not survive unchanged. One of my
own re-analyses was wrong and is reported below with the others.

This document is the audit. The design changes it justifies are in
`physical/docs/`, and §7 lists them.

---

## 1. What the project currently is

**Computational half (complete).** Public intracortical BCI recordings from two
participants. Four kinds of degradation injected into them at onsets drawn and
checksummed before any detector existed, producing ~1,850 episodes. A monitor
and a five-gate test battery. Result: the monitor detects what counting spikes
cannot (AUC 0.71–0.79 against 0.40–0.52) but **cannot be deployed** — median
lead time −20 s, 3.4 false alarms an hour against a 0.1 budget, 0 of 48
configurations passing all gates. The cause is located: a per-hour alarm budget
divided among 720 decisions an hour.

**Physical half (designed, not built).** A camera in a sealed box watching a
screen, standing in for a multichannel sensor array, with failures beginning at
moments drawn and checksummed in advance. Six experiments. Preregistered.

**Claimed contribution.** That a decoder-health monitor can correlate strongly
with performance while being unusable as a warning, and therefore that the
field's validation standard is insufficient.

---

## 2. What survives scrutiny

I tested the claims the project most depends on. These held.

### 2.1 The hardware is genuinely necessary — I checked, expecting it not to be

The stated justification is that only **1.4 hours** of genuinely fault-free
recording exists, so a 0.1-per-hour false-alarm rate cannot be bounded. My first
suspicion was that this is a **design choice** — that faults were injected into
almost everything and more episodes could simply have been held clean.

It is not. A block of real recording can contribute **at most one** fault-free
episode, because injecting into it makes it not fault-free. The ceiling is
therefore set by how many blocks were recorded in 2016–17:

| | Blocks | Fault-free ceiling | Held out |
|---|---|---|---|
| T11 | 29 | 2.2 h | ~17 episodes |
| T5 | 21 | 1.2 h | ~13 episodes |
| **Total** | **50** | **3.4 h** | **~1.4 h** |

Reaching the ~30 fault-free hours needed to bound 0.1/hour would take roughly
**400 blocks**. No public intracortical dataset is close, and a third dataset
(T15) would add hours, not hundreds of hours.

**So the apparatus is not a physical component added for the sake of having
one.** It is the only way to get the one quantity the archived data structurally
cannot supply. That is the strongest thing in this project's favour and it
survived being attacked.

### 2.2 The negative result and the discipline

102 claims recompute from stored data. The onsets were checksummed before
detectors existed. Five gates applied in a fixed order with silence first. Five
claims withdrawn on evidence, every correction kept in place. This is the part
that would survive a hostile review unchanged.

---

## 3. What does not survive

### 3.1 The hypothesis is an existence claim, and existence claims are weak

> *"A decoder-health monitor **can** show a strong correlation with task
> performance while simultaneously being unusable as a warning system."*

Of course it can. Correlation measures association across a range; deployability
is a single operating point under an alarm budget. That these can come apart is
close to a **statistical truism**, and a reviewer with statistical training will
say so — probably in the first two minutes.

Demonstrating that something is *possible* is the weakest form of empirical
claim. The project is not actually doing the weak thing — it is **measuring two
quantities nobody has measured** — but it is *describing* itself as doing the
weak thing, and it will be judged on the description.

**This is the single most important problem in the project**, and it is a
framing problem rather than a scientific one.

### 3.2 The external validity of the apparatus is under-defended

A false-alarm rate measured on a camera in a cardboard box is **not an estimate
of the false-alarm rate of an implanted array**, and nothing in the project
claims it is — but the framing invites the question and then does not answer it
crisply. "We matched the decoding difficulty to 36.1°" is not an answer:
matching median angular error does not make the noise structure, the drift
mechanism, or the failure modes comparable.

The defensible answer exists and needs saying plainly: the apparatus measures
**whether the measurement is possible, and whether the monitor's behaviour is
intrinsic to the method or specific to neural recordings.** It is an instrument
for testing a *method*, not a model of a brain.

### 3.3 P-6 is ranked last and is probably the best experiment in the phase

The decision-rate curve is currently the second thing to cut, and its prediction
is labelled the weakest. That ranking is wrong, for a reason the project has not
noticed:

**The decision-rate law is a claim about the statistics of monitoring any
drifting many-channel sensor. It is not a claim about biology.** A camera array
is therefore a *legitimate instance of the class*, not a proxy for something
else — and the "your box is not a brain" objection, which is fatal to a
generalisation from P-2, **does not apply to P-6 at all.**

It is also the only result that reaches beyond brain-computer interfaces:
*given an alarm budget and how fast your failures develop, here is how often to
check.* Nobody has that curve for any system.

### 3.4 I found new evidence that changes P-6's standing — by getting it wrong first

`scripts/76` reports a detection rate at each decision rate with its own
bootstrap interval, and the published reading is that the intervals overlap, so
nothing can be settled. **Overlap of marginal intervals is not a test of a
difference**, and here both rates are scored on the same episodes against the
same fault-free set, so most of the uncertainty is shared and cancels.

Re-done as a paired test (`scripts/78_decision_rate_paired.py`):

| | Change, 720 → slowest | Paired 95% CI | Established? |
|---|---|---|---|
| T11 | +11.5% | −0.3% to +27.6% | no |
| **T5** | **−18.2%** | **−42.3% to −4.9%** | **yes** |

**The archived data is not silent. It contains one established result, and that
result says deciding less often makes detection _worse_** — the opposite of what
the physical phase's PP-7 predicts.

That is a better reason to run the experiment than "we cannot tell", and a
worse starting position than the project assumed. A preregistered prediction
that contradicts the only established evidence is still legitimate, but it has
to be made knowing that.

**My first attempt at this analysis was wrong.** I selected negatives as "all
not-crossed episodes" and got T5 *rising* +52% — a confident, publishable-looking
number that was an artifact of re-introducing the sub-threshold-ramp mislabel
this project had already identified and corrected in `AUTOCORR_BY_SEVERITY.md`.
I caught it only because it disagreed with the published figure. Recorded here
because a reassessment that reports only its successful checks is not an audit.

### 3.5 The project applies a standard to others it does not apply to itself

It criticises conclusions drawn from **two participants** — correctly, and
repeatedly. It then plans to draw conclusions from **one apparatus**, in one
room, with one screen, one camera and one set of optics.

That is the same defect. And unlike the participant problem, it is **cheap to
fix**: vary the apparatus.

### 3.6 The comparison target is slightly a straw man

MINDFUL's authors report a correlation and propose the monitor for deciding when
to recalibrate. They do **not** claim a lead time. Criticising them for not
reporting something they never claimed is unfair, and a reviewer who knows the
paper will notice.

The fair statement is about the **field**, not the paper: *no monitor of this
class has a published lead time or false-alarm rate, because measuring them
requires data nobody has.* That is true, uncontroversial, and still motivates
everything.

---

## 4. Alternatives I considered and rejected

| Alternative | Why not |
|---|---|
| **Drop the hardware; add a third dataset (T15)** | Does not fix the binding constraint. Fault-free hours are capped by block count; T15 adds hours, not the hundreds needed. Worth doing **as well**, not instead. |
| **Pure methodology: propose a benchmark standard, no new data** | Defensible as a paper, weak as a science-fair project, and it forfeits the one measurement only this project can make. |
| **Keep the apparatus but aim it at "does the neural result generalise?"** | This was the original design and was already superseded. It is the framing most exposed to "your box is not a brain". |
| **Build a warning device as the deliverable** | The evidence says the warning does not work. Building it anyway is building something known not to do what its label says. |

**The structure is right. The framing, the ranking, and the self-applied
standard are what need changing.**

---

## 5. What a hostile reviewer will attack, and the answer

| Attack | Answer |
|---|---|
| *"Isn't 'correlation doesn't imply usability' obvious?"* | The statistical point is. The **numbers are not** — no monitor of this class has a published lead time or false-alarm rate. This is a measurement, not a demonstration. |
| *"Your box isn't a brain."* | Correct, and no estimate for implants is claimed. The apparatus tests whether the measurement is possible and whether the behaviour is intrinsic to the method. For P-6 the objection does not apply at all: that claim is about drifting many-channel sensors, and the box is one. |
| *"You injected the faults, so you designed what you detect."* | P-5 imposes faults nobody designed, reported in a separate table because its onsets come from a stopwatch rather than a checksum. |
| *"n = 2 participants, n = 1 apparatus."* | The participant limit is stated everywhere. The apparatus limit is now addressed by varying it — see §7. |
| *"Why should I believe the monitor is any good?"* | You should not, and the project does not claim it is. It reports a negative result with the cause located. |
| *"What did you actually build?"* | A benchmark and the instrument that makes two unmeasurable quantities measurable. Four of six outcomes produce no device, decided in advance. |

---

## 6. Feasibility, honestly

71 days to the December plan. The schedule finishes 27 October with 35 days of
slack, absorbing about one major setback. The changes in §7 add **about four
recording hours and no new equipment**.

The binding risk is not the science. It is that this is a school year, the
campaign is 40 hours of recording, and the slack absorbs one failure, not three.
`13_SCHEDULE.md` costs each risk in days, and the cut order is fixed in advance.

---

## 7. What changes, concretely

Each of these is a change to a document in `physical/docs/`, not a suggestion.

1. **Reframe the hypothesis from an existence claim to a measurement claim.**
   The question becomes *what are the lead time and false-alarm rate of a
   monitor of this class, measured properly?* — with the correlation comparison
   as one result among several rather than the headline. (`01`, `02`, `09`)

2. **Promote P-6 to co-primary with P-2**, and say why the "not a brain"
   objection does not apply to it. It moves out of the cut list. (`02`, `13`)

3. **Rewrite PP-7** to state that it predicts *against* the only established
   evidence, citing the paired re-analysis. (`09`)

4. **Add an apparatus-variation arm.** Repeat a reduced campaign under three or
   four deliberately different apparatus configurations — different exposure,
   patch size, channel count, screen. Turns n = 1 apparatus into a family, and
   turns the decision-rate result from a point into a curve with a spread.
   Cost: about four hours of extra recording, no new parts. (`02`, `09`, `13`)

5. **State the external-validity position explicitly** wherever a result from
   the apparatus is reported — what it is and is not an estimate of. (`01`, `07`)

6. **Retarget the comparison from MINDFUL to the field.** (`00`, `01`)

7. **Keep everything else.** The ground-truth discipline, the gates, the
   preregistration, the negative result, the code and the schedule are sound and
   are not touched.

---

## 8. The honest one-paragraph version

*Two quantities decide whether a brain-implant health monitor can be used on a
person: how early it warns, and how often it warns when nothing is wrong.
Neither has ever been reported for any monitor of this class, because measuring
them needs failures with known start times and tens of hours of recording in
which nothing goes wrong — and human implant recordings have neither. This
project measured both on archived recordings as far as they allow, found the
monitor warns 20 seconds too late at 34 times its alarm budget, and located the
cause in how often it is asked. It then built an apparatus where both quantities
are measurable without limit, to find out how often such a monitor should be
asked — a question that is about drifting sensor arrays in general, not about
brains, and that the archived data cannot settle because its two participants
disagree.*

That is a measurement, a diagnosis, and a design question. It is not a
demonstration that a method works.
