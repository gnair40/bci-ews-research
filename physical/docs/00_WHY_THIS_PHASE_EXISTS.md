# Why the physical phase exists

**Read this first. It is the argument the whole phase rests on.**

This document assumes you know nothing about this project, about brain-computer
interfaces, or about the computational work that came before. Everything is
explained from the beginning.

---

## 1. The problem, in plain terms

Some people are paralysed so severely that they cannot move or speak. A
brain-computer interface, or BCI, is a device that lets them control a computer
cursor by imagining movement. A grid of tiny electrodes is implanted in the part
of the brain that plans movement. Software called a **decoder** reads the
electrical activity those electrodes pick up and turns it into cursor motion.

The hard part is not making this work on the first day. It is keeping it working.
The signals the electrodes pick up change slowly over months: individual brain
cells stop being detected, the electrodes' electrical properties shift, and the
relationship between brain activity and intended movement moves. The decoder was
built for how the signal used to look, so it slowly stops matching.

**The dangerous part is that this failure is invisible.** A pacemaker that stops
has an obvious signature. A decoder that has drifted keeps producing confident
output and is simply increasingly wrong. The person using it cannot tell whether
the device is degrading or whether they are tired, distracted, or having a bad
day.

The current fix is **recalibration**: the user stops what they are doing, works
through a guided block of practice movements, and the decoder is rebuilt from
that fresh data. It costs time, it needs supervision, and on many systems it
stops the person using the device at all. It happens **on a fixed schedule**
rather than when there is evidence it is needed.

---

## 2. What everybody wants, and what already exists

The obvious improvement is a **decoder-health monitor**: something that watches
the signal and says "this decoder has drifted, recalibrate it" — so
recalibration happens on evidence instead of on a calendar.

**That idea is not new, and it is important to say so clearly.**

- In general engineering, sensors that diagnose their own health are a
  thirty-year-old idea with a national standard behind them (the self-validating
  or "SEVA" sensor, Henry & Clarke 1993, British Standard BS7986:2001).
- In brain-computer interfaces specifically, the current state of the art is
  **MINDFUL** (Pun et al., 2024) — a method that measures instability in neural
  recordings without needing to know what the user intended. Its authors report
  that their instability score correlates with cursor performance at
  **r = 0.93 and r = 0.72**, and propose it as a way "to determine when
  recalibration should take place."

So: the monitor exists. **This project did not invent it and does not claim to.**

> **A fairness note, added 21 September 2026.** MINDFUL's authors report a
> correlation and propose the monitor for deciding when to recalibrate. They do
> **not** claim a lead time or a false-alarm rate. Criticising them for not
> reporting something they never claimed would be unfair, and a reviewer who
> knows the paper would notice.
>
> The accurate statement is about the **field**, not that paper: *no monitor of
> this class has a published lead time or false-alarm rate, because measuring
> either needs data nobody has.* That is uncontroversial, it is true, and it
> motivates everything here without putting words in anyone's mouth. See
> `research/REASSESSMENT_2026-09-21.md` §3.6.

---

## 3. The gap this project found

Here is the question nobody has answered.

**How early does such a monitor warn, and how often is it wrong?**

Those two numbers — **lead time** and **false-alarm rate** — are the only ones
that decide whether a warning system is worth having. A monitor that warns a
week early but cries wolf daily is useless. A monitor that never false-alarms
but warns ten minutes after the failure is also useless. **Neither number has
ever been reported for a decoder-health monitor.**

And there is a specific, unavoidable reason why not.

> **In a real recording, nobody wrote down when the degradation started.**

Without a recorded start time you cannot measure how early a warning came,
because "how early" is measured from a moment nobody recorded. Whoever analyses
the data has to pick that moment afterwards — and a different analyst picking a
different moment gets a different answer. The false-alarm rate is worse: it
cannot be computed at all, because you cannot count wrong alarms without knowing
which alarms were wrong.

**So the field validates these monitors a different way: by correlating the
monitor's output against performance.** That is where MINDFUL's r = 0.93 comes
from.

---

## 4. Why correlation is not enough — and this project has the evidence

This is the intellectual core of the project, so it is worth being careful.

The computational half of this project built a monitor of the same family and
tested it against constructed ground truth. Two things came out.

**First: a strong correlation can coexist with a useless monitor.** The monitor
built here reaches an AUC of 0.67–0.74 at the session level — real, measurable
signal. And yet:

| Measure | Result |
|---|---|
| Healthy sessions in which the risk score still trends upward | **76.5% (T11), 100% (T5)** against a 10% bar |
| Median lead time | **−20 seconds** — the warning arrives *after* the failure |
| False alarms per hour | **3.4**, against a budget of 0.1 |

A monitor that rises during 76.5% of perfectly healthy sessions correlates with
performance and is still not something you would deploy.

**Second: that kind of correlation is systematically inflated.** When this
project measured its own session-level drift measure against performance, it got
ρ = −0.818, which looks decisive. But both quantities decline over months, and
**any two quantities that both trend over time will correlate whether or not one
tells you anything about the other.** Controlling for time:

| | Participant T11 | Participant T5 |
|---|---|---|
| Raw correlation | −0.818 | −0.943 |
| Controlling for the time trend | −0.500 (p = 0.058) | −0.852 (p = 0.031) |
| On changes rather than levels | −0.679 (p = 0.008) | **+0.100** (p = 0.873) |

Neither participant survives both checks, and on one of them the correlation
**changes sign**. That is what a correlation between two drifting series looks
like when you interrogate it.

**MINDFUL's r = 0.93 is a correlation of exactly this kind** — an instability
score against a performance measure, both changing across sessions over months.
This project cannot say whether it survives the same controls, because that
analysis has not been published. **What this project can say is that the check
is necessary and is not currently being done.**

---

## 5. What the physical phase is for

Everything above is an argument made on somebody else's recordings — Pun et
al.'s, downloaded from a public archive. It has two limits that no amount of
further analysis can fix:

**Limit 1 — the false-alarm rate cannot be measured on that data.** Once you
restrict to sessions that genuinely contain no injected fault, there are **17 and
15 of them, about 1.4 hours total.** You cannot estimate a rate of 0.1 events per
hour from 1.4 hours of recording. Nobody can.

**Limit 2 — two arrays, and they disagree.** Every finding here rests on two
people's implants, and on several key questions those two disagree with each
other, including the direction of an effect.

**The physical phase exists to remove both limits**, and this is the only reason
it exists. It is not there to demonstrate that a device can be built.

A physical sensor array that can be degraded on purpose gives you the one thing
no human recording can:

> **A recording where the experimenter knows when the degradation started,
> because the experimenter caused it and wrote it down first — and hundreds of
> hours of healthy recording to count false alarms against.**

No BCI participant can sit through two hundred sessions so that somebody can
estimate a false-alarm rate. A sensor array on a bench can run unattended for a
fortnight.

---

## 6. What this phase contributes that does not exist

Stated precisely, so it can be checked and so it cannot be overclaimed:

| | Already exists | This project |
|---|---|---|
| A decoder-health monitor | **Yes** — MINDFUL, and others | Not claimed as new |
| Self-monitoring sensors in general | **Yes** — standardised since 1993 | Not claimed as new |
| Correlating a health score against performance | **Yes** — r = 0.93 reported | Not claimed as new |
| **A benchmark with known degradation onsets** | **No** | **Built** |
| **A measured lead time for such a monitor** | **No** | **Measured** |
| **A measured false-alarm rate** | **No** — and not measurable on archived data | **The physical phase** |
| **Evidence that correlation-based validation is inflated** | **No** | **Shown, on this project's own analysis** |

The contribution is **not a device**. It is a **validation method and the
measurements it produces** — and the finding that the way the field currently
validates these monitors does not support the claims being made from it.

---

## 7. What comes next, and in what order

1. **Physical experiments** (`01` onward in this folder). Build the apparatus,
   validate it, run the experiments, analyse the results.
2. **Then, and only then, the prototype.** What to build depends on what the
   experiments find. Building first and measuring afterwards is how you end up
   with a device that demonstrates nothing.

If you are starting from zero, read the documents in this folder in numerical
order. Each one assumes only the ones before it.
