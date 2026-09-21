# What comes after the experiments

**Written before the experiments run, so that what gets built afterwards is
decided by the results rather than by what would look good on a table.**

---

## 1. There is no device in the plan, and that is deliberate

An earlier version of this project ended with "a sensor array that monitors its
own health and says when it needs recalibrating". That is a good-sounding
deliverable and it was the wrong one, for a reason worth stating plainly:

**the evidence says that device does not work yet.** The computational half
measured a median lead time of **−20 seconds** — the warning arrives after the
failure — at **3.4 false alarms per hour** against a budget of 0.1, with zero of
48 configurations passing all five gates. Building a box that issues those
warnings and calling it the deliverable would be building a thing that is known
not to do what its label says.

So the deliverable of this phase is **a measurement and the apparatus that makes
it possible**, not a warning device. Whether anything gets built on top of that
depends on what the measurement says.

---

## 2. What the phase delivers regardless of the result

These exist whichever way the experiments go, and they are the contribution.

**A benchmark with known onsets.** Two hundred-odd recordings from a system that
degrades in known ways at moments drawn at random and locked under a checksum
before each recording existed. No human recording has this property, and without
it neither lead time nor false-alarm rate has a fixed value.

**The first false-alarm rate for a decoder-health monitor with enough
fault-free recording behind it to mean something.** Genuinely fault-free
recording in the archived human data amounts to 1.4 hours. This phase can record
thirty.

**A direct test of how this field validates its monitors.** P-4 computes the
correlation the field reports *and* the lead time and false-alarm rate that
decide usability, on the same recordings. That comparison has not been made,
because nowhere else can both sides come from the same data.

**Working, documented code and a protocol somebody else can follow.** Including
the parts that failed.

---

## 3. What gets built afterwards, and on what condition

Each row is decided by results that do not exist yet. None of it is started
before the experiments finish.

| If the experiments show | Then the sensible thing to build | Why |
|---|---|---|
| A usable lead time **within** the false-alarm budget | A demonstration monitor: the box, running live, showing the risk score and issuing warnings at the threshold P-2 established | The warning has been shown to be worth having, so showing it is honest |
| **P-6's curve rises** and the intervals separate | A *decision-rate calculator*: given a false-alarm budget and how fast the failure develops, it returns how often to check | This is the generalisable output — it applies to any drifting many-channel sensor, not just a brain implant |
| A high correlation with **unusable** lead time or false-alarm rate | **No device.** A validation protocol instead: the checklist and the code that any future monitor should be put through before it is proposed for clinical use | The finding is that the standard validation is insufficient. The useful artefact is a better test, not another monitor |
| The silence gate fails on an apparatus with no biology in it | **No device.** A written account of why this class of monitor drifts, and what would have to change | A monitor that alarms during healthy operation should not be packaged up |
| Results are inconclusive — intervals overlap, no measure settles | **No device.** The benchmark, the data, and a statement of exactly how much more recording would settle it | "We do not know yet, and here is what it would take" is a real result and a common one |

**Three of the five rows say "no device".** That is not pessimism; it is what
follows from the current evidence, and writing it down now is what stops a
disappointing result from quietly turning into a demonstration of something that
was not shown.

---

## 4. What the ISEF deliverable actually is

If somebody at the fair asks "what did you build?", the answer is:

> A test rig and a benchmark that can measure something nobody has been able to
> measure: how early a brain-implant health monitor warns, and how often it
> warns when nothing is wrong — because the failures were scheduled in advance
> and locked with a checksum before each recording existed.
>
> Using it, I measured [the result]. That matters because decoder-health
> monitors are currently validated by correlating them with task performance,
> and my measurements show whether that validation supports the conclusions
> drawn from it.

The physical thing on the table is the apparatus. The result is the contribution.
Those are not the same, and conflating them is how a project ends up with an
impressive-looking box and nothing to say.

---

## 5. The impact, stated without inflation

**What this does not do.** It does not improve anybody's brain implant. It does
not make a decoder more accurate. Nobody's device works better because of it.

**What it does do.** Drift-triggered recalibration is being proposed as the way
to decide when a decoder needs rebuilding. The evidence offered for it is
correlation with task performance. Nobody has reported how early such a monitor
warns or how often it warns wrongly — the two numbers that decide whether it can
be used on a person — because measuring them needs recordings with known failure
times and many fault-free hours, and human implant recordings have neither.

This phase builds a system that has both, and reports those two numbers. If they
are good, that is the first real evidence for an approach that is currently
proposed on weaker grounds. If they are bad, that is a warning delivered before
the approach reaches somebody who depends on the device rather than after.

**The method generalises further than the apparatus does.** Fixing failure
times before the recording exists, reporting lead time and false-alarm rate as a
pair, and recording enough fault-free hours to bound the rate are not facts about
brain implants. They apply to any many-channel sensor that drifts — an
industrial array, an environmental network, a prosthetic limb. The decision-rate
result, if P-6 settles, is a design rule for all of them.

---

## 6. What would have to be true before any of this touched a person

Stated so the limits are on the record, not because it is close.

1. It works on neural recordings, not only on this apparatus.
2. It works on more than one participant, and more than two.
3. The false-alarm rate holds over months, not over hours.
4. Somebody has established what a wrong warning actually costs a user — a
   question this project does not touch and cannot answer from a cardboard box.

None of those is within reach of a science-fair project, and the write-up should
not imply otherwise.
