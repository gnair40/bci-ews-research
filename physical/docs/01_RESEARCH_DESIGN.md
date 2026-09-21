# The research design, rebuilt

**What changed, why, and what is now being tested.**

Read `00_WHY_THIS_PHASE_EXISTS.md` first. This document assumes it.

---

## 1. A critical review of where the project stood

Before designing anything new, here is an honest audit of the original design and
what the evidence did to it.

### 1.1 The original research question

> *"When a neural interface starts degrading, does the statistical structure of
> the recorded signal change before task performance does? And if it does, can
> that change be told apart from the change you get when the user is just doing
> something different?"*

**Verdict: answered, and no longer the interesting question.**

The answer is *yes, partially, and not usably*. The signal does change — the
monitor reaches an AUC of 0.67–0.74, which is real information. But the change
is not specific: the risk score also rises during 76.5% to 100% of healthy
sessions. A question whose answer is known is not a research question any more.

### 1.2 The original hypothesis

> *"For degradations whose start times are controlled and recorded in advance, a
> monitor reading only the input signal will warn before task performance
> crosses a degradation threshold, at a false alarm rate low enough to be worth
> having."*

**Verdict: falsified, cleanly, and that is a real result.** Median lead time was
**−20 seconds** (the warning arrives after the failure) at **3.4 false alarms
per hour** against a budget of 0.1. Zero of 48 configurations passed all five
gates.

This hypothesis did its job. It was specific enough to be wrong.

### 1.3 The original engineering goal

> *"Build a monitor that converts such a change into a useful warning, and —
> more importantly — build the test that determines whether any monitor of that
> kind works."*

**Verdict: the first half failed, the second half succeeded, and the second half
is the contribution.** The benchmark works. The monitor does not. The goal was
written with the right emphasis before anyone knew which half would survive,
which is worth pointing out.

### 1.4 The original variables

| | Original | Problem found |
|---|---|---|
| Independent | fault mode, severity, onset time | Sound. The onset-locking was the good idea. |
| Dependent | lead time, false-alarm rate, gates passed | Sound, but **the false-alarm rate was not measurable** on the available data — 1.4 hours of genuinely fault-free recording. |
| Controlled | window geometry, decoder, budget | **The decision rate was never treated as a variable at all**, and it turned out to be the one that governs everything. |

That last row is the important one. The monitor was making **720 decisions an
hour** from a session containing roughly **one independent measurement's worth of
evidence**, and the false-alarm budget was being divided among all 720. Nobody
chose that; it fell out of an analysis window chosen for other reasons.

### 1.5 What was wrong with the first physical plan

The original physical plan asked: *is this failure specific to brains, or general
to any slowly drifting sensor?* Three findings made that the wrong thing to
spend the recording time on.

1. The failure is now **located and quantified** — it is a decision-rate problem
   with a stated target, not a mystery.
2. The negative result **does not need re-confirming**; it holds on genuinely
   fault-free data.
3. The false-alarm rate **still cannot be measured**, and that is the gap that
   actually blocks progress.

A rig that re-confirms a known negative is an expensive way to learn nothing.

---

## 2. The rebuilt research question

> **How early, and at what cost in false alarms, can a decoder-health monitor
> warn that a sensor array is degrading — and does the correlation-based
> validation the field currently relies on support the claims being made from
> it?**

Two halves, and the second is the novel one.

**Why this is worth asking.** The state of the art (MINDFUL, Pun et al. 2024)
validates a decoder-health monitor by correlating its score against performance,
reporting r = 0.93 and 0.72, and proposes it for deciding when to recalibrate.
Nobody has reported a lead time or a false-alarm rate for such a monitor,
because measuring either requires knowing when degradation began, and no
observational recording records that.

---

## 3. The hypothesis

> **A decoder-health monitor can show a strong correlation with task performance
> while simultaneously being unusable as a warning system — that is, a high
> correlation does not imply a usable lead time or an acceptable false-alarm
> rate.**

**Stated so it can be falsified.** On recordings with constructed, pre-recorded
degradation onsets, the monitor will achieve a correlation with performance of
**r > 0.7** (comparable to published values) while **either** its median lead
time is negative **or** its false-alarm rate exceeds 0.1 per hour at the
threshold needed for 80% detection.

**Falsified if** the monitor achieves r > 0.7 *and* positive median lead time
*and* a false-alarm rate within budget. That outcome would mean correlation-based
validation is adequate after all, which is equally worth knowing and would
substantially strengthen the case for the published approach.

**Why this is a real hypothesis and not a restatement of the computational
result.** The computational half measured lead time and false-alarm rate on
archived data, but could not measure the false-alarm rate properly (1.4 hours of
fault-free recording) and could not measure the correlation *on the same
recordings as the lead time* in a controlled way. The physical phase does both,
on the same sessions, with onsets known in advance.

---

## 4. Variables

### 4.1 Independent variables — what is deliberately changed

| # | Variable | Levels | Why it is here |
|---|---|---|---|
| **IV1** | **Degradation onset time** | drawn at random, recorded before the session | The variable that makes everything else measurable. Without it there is no lead time and no false-alarm rate. |
| **IV2** | **Degradation present or absent** | present / absent | Absent sessions are what a false-alarm rate is counted against. Roughly half of all sessions. |
| **IV3** | **Degradation type** | 4 modes: overall signal loss, channel dropout, per-channel gain drift, geometric rotation | Tests whether findings hold across kinds of failure or only one. |
| **IV4** | **Degradation severity** | 0, 0.25, 0.5, 1.0 | Gives a ladder. A monitor that responds to severity is behaving; one that does not is reacting to something else. |
| **IV5** | **Decision rate** | 720/hour down to 1 per session | **The variable the original design never varied.** Set in analysis, not in recording — see §5.2. |

### 4.2 Dependent variables — what is measured

| # | Variable | Definition | Why it matters |
|---|---|---|---|
| **DV1** | **Lead time** | seconds between the first warning and the moment performance crosses its failure threshold; positive means the warning came first | Half of what decides whether a warning is worth having |
| **DV2** | **False-alarm rate** | warnings per hour of recording in which no degradation was applied | The other half, and the number nobody can currently measure |
| **DV3** | **Detection rate** | fraction of degraded sessions warned about, at a stated false-alarm rate | Standard, and needed to make DV1 and DV2 interpretable |
| **DV4** | **Silence-gate pass rate** | fraction of healthy sessions in which the risk score shows no significant trend | The gate that failed computationally; does it fail here too? |
| **DV5** | **Correlation with performance** | correlation between the monitor's score and task performance, with and without controlling for time | **The comparison variable.** This is what the field reports. Measuring it beside DV1 and DV2 on the same recordings is the experiment. |

**DV5 is the point.** Everything else has been measured before, in some form.
Measuring the field's validation metric *and* the metrics that actually matter,
on the same sessions, is what tests the hypothesis.

### 4.3 Controlled variables — held fixed, and why

| Variable | Held at | Why it must not vary |
|---|---|---|
| Analysis window | 30 s, stepping 5 s | Shared with the computational half; changing it breaks comparability |
| Decoder | ridge regression, fit once on healthy data | A decoder that adapts would hide the drift being measured |
| Camera exposure and gain | fixed, automatic modes **off** | Automatic exposure compensates for dimming — it cancels the degradation being measured |
| Screen brightness setting | fixed, all "enhancement" off | Same reason |
| Modulation depth | fixed after calibration | Sets the difficulty; changing it makes sessions incomparable |
| Room light | enclosure sealed; darkness verified | Ambient light varies with the time of day and would masquerade as drift |
| Physical geometry | camera position taped and photographed | Moving the camera is itself a geometric fault |

---

## 5. Why this needs physical apparatus

Three reasons, each of which independently rules out doing this in software or on
archived data.

### 5.1 The false-alarm rate needs hundreds of healthy hours

To measure a false-alarm rate of roughly 10% to within a third of itself takes
about **101 healthy sessions**. To measure 2% takes about **545**. The archived
data contains **1.4 hours** of genuinely fault-free recording.

No person can sit through that. An apparatus can run unattended overnight.

### 5.2 One recording campaign yields every decision rate

**The decision rate (IV5) is an analysis choice, not a recording choice.** A
session recorded once can afterwards be scored at 720 decisions an hour, or 1 per
session, or anything between. So IV5 costs nothing extra in recording time — the
whole curve falls out of the same sessions.

This is what makes the design affordable, and it is worth understanding before
reading the procedures.

### 5.3 A simulation cannot test this

A simulated sensor degrades exactly the way it was told to. The question here is
partly whether a monitor tuned on *invented* faults handles *real* ones — a
loosened connector, a smudged lens, a warm circuit board. Those cannot be
simulated, because if you could write down what they look like you would not
need to test them.

---

## 6. The engineering goal, restated

> **Build the measurement apparatus and the benchmark that make lead time and
> false-alarm rate measurable for decoder-health monitors — and use them to test
> whether the correlation-based validation the field relies on is sufficient.**

**What success looks like:** a reproducible apparatus, a dataset with recorded
onsets, and the first published lead-time and false-alarm numbers for this class
of monitor — whatever those numbers turn out to be.

**What it does not include:** a claim that the monitor works. The evidence so far
says it does not, and the apparatus is built to measure that honestly rather than
to rescue it.

---

## 7. Limitations, stated in advance

Written now, before any data exists, so they cannot be quietly adjusted later.

1. **A camera is not a brain.** The claim under test is about a *class of
   measurement problem* — many channels, drifting slowly, monitored by a
   statistic — and not about biology. Results transfer to the extent the class
   is the right abstraction, which is itself uncertain.
2. **One apparatus.** Everything rests on one physical system, exactly the "n of
   2" limitation that constrains the computational half.
3. **Constructed degradation is still constructed.** The undesigned-fault arm
   (§Procedures) exists because of this, but it is a partial answer.
4. **The monitor is one family of detector.** A different detector might behave
   differently, and nothing here bounds what is possible in general.
5. **The correlation comparison cannot be run against MINDFUL directly**,
   because that would require their analysis pipeline on this data. The claim is
   about *correlation-based validation as a method*, not about their specific
   number.

---

## 8. How this connects back

| Research-question component | Which experiment answers it | Which DV |
|---|---|---|
| How early does it warn? | P-1, P-3 | DV1 |
| At what cost in false alarms? | P-2 | DV2, DV3 |
| Does it stay quiet when nothing is wrong? | P-2 | DV4 |
| Does correlation-based validation support the claims? | **P-4** | **DV5 vs DV1, DV2** |
| Does any of it hold for faults nobody designed? | P-5 | all |
| How often should a monitor decide? | P-6 | DV1, DV2 vs IV5 |

The experiments are specified in `02_EXPERIMENTS.md`.
