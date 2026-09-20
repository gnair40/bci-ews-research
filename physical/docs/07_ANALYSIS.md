# Analysing the data

What to run, in order, what each output means, and — the part that matters most
— what each result would and would not license you to claim.

Assumes the recordings exist. If they do not, `dryrun.py` lets you rehearse all
of this today; see `05_SOFTWARE.md`.

---

## Run it in this order

```bash
cd ~/bci-ews-research
python3 physical/code/make_session_table.py
python3 physical/code/analyze_falsealarm.py
python3 physical/code/analyze_leadtime.py
python3 physical/code/analyze_leadtime.py --undesigned
python3 physical/code/analyze_correlation.py
python3 physical/code/analyze_decision_rate.py
```

Six commands. The first must come before the rest, and
`--undesigned` must come after the plain `analyze_leadtime.py`, because its
report compares against P-3's numbers. The others can be run in any order. Everything lands in `physical/data/results/` as a markdown report you
can read and a JSON file the reports are built from.

**Do not edit the reports by hand.** They say so at the top. If a number looks
wrong, fix the script and re-run, so the file on disk always matches the code
that produced it. A hand-edited report is a report nobody can reproduce,
including you.

---

## Step 1 — the session table

`make_session_table.py` reads every recording, decodes it, scores it, and writes
one row per session. Read its printout before anything else; it tells you
whether the campaign is sound.

### What to check in its output

**The split.** It prints `fit / val / test healthy / degraded`. If `test healthy`
is small, every false-alarm number downstream is weak, and no amount of analysis
fixes that — only more recording does.

**The margin.** It prints the median decoding error against the measured chance
level, and the margin between them, beside the neural target of 36.1°. If the
margin has drifted far from 36.1 since calibration, something about the
apparatus changed mid-campaign. Find out what, and write it down.

**The false-alarm arithmetic.** It prints how many hours of held-out healthy
recording you have and how many the budget needs. If it says you need more, you
need more.

**Anything that would not load.** It prints the name of any recording it could
not read. It does not skip them silently, because a dropped recording changes
every denominator downstream.

### Run it twice

```bash
python3 physical/code/make_session_table.py --decoder frozen
python3 physical/code/make_session_table.py --decoder per-session --tag _persession
```

A frozen decoder is calibrated once and used on later sessions, which is what
happens to a real implant. A per-session decoder is refitted each time, which
makes drift *between* sessions invisible.

If a result appears with a frozen decoder and vanishes with a per-session one,
the result is about **staleness**, and the write-up must say so rather than
calling it degradation.

---

## Step 2 — P-2, the false-alarm rate

`analyze_falsealarm.py` → `P2_FALSE_ALARM_RATE.md`

### The number, and the trap underneath it

If there were false alarms, there is a rate with an interval. **Read the top of
the interval, not the middle.** A rate that might be 0.4 per hour has not been
shown to be below 0.1.

If there were none, there is no rate — there is an **upper bound**. Zero events
in H hours bounds the true rate at about 3/H per hour, so four hours of
recording turns "zero false alarms" into "probably below 0.75 per hour", which
is seven times the budget.

> Writing "zero false alarms" and stopping there would be the most misleading
> thing this project could do. It reads as the strongest possible result and is,
> on a short campaign, almost no result at all.

### The silence gate

Separately from counting alarms: does the risk score **drift upward** during
healthy operation? A score that climbs steadily will cross any threshold
eventually. The gate allows at most 10% of healthy sessions to show a
significant trend — the same gate and the same bar the computational half used,
and **failed**, on fault-free neural data.

| Outcome | What it licenses you to say |
|---|---|
| Gate passes | On an apparatus with no biology in it, the monitor stays flat. That makes the computational failure a property of neural recordings rather than of the monitor — a stronger statement than either half gives alone. |
| Gate fails | The drift appears with no brain, no electrodes and nothing biological. That points at the monitoring approach itself, and it is the more interesting outcome. |
| Fails raw, passes detrended | The drift is close to linear. Worth reporting — but a deployed monitor must subtract it **causally**, from past windows only, which is harder than doing it afterwards with the whole session in hand. |

---

## Step 3 — P-3, lead time

`analyze_leadtime.py` → `P3_LEAD_TIME.md`

### Three numbers, not one

- **Detection delay** — how long after the fault began did it notice? *New
  here*: not computable on any archived human recording, because nobody wrote
  down when the electrodes started failing.
- **Lead time** — how much warning before decoding actually became unusable?
  Defined exactly as in the computational half, so the two compare.
- **Detection rate** — what share of faults did it catch at all?

### Two categories that are not detections

The report has a table for these, and it should be read carefully.

**Warned before the fault started.** The warning window ends before the onset,
so it contains no faulty data. It is a false alarm that happened to land inside
a degraded session. Counting these as detections is the easiest way to
manufacture a positive result here, which is exactly why they are separated.

**The fault never broke anything.** Mild faults are imposed and decoding carries
on. There is no failure to have led, so lead time is undefined — and from the
user's point of view a warning about something that turned out not to matter is
itself a false alarm.

### The pair rule

The report prints the false-alarm rate beside the lead time, at the same
threshold, always. Lead time can be made arbitrarily long by lowering the
threshold until the monitor warns constantly. **Neither number means anything
alone**, and reporting lead time by itself is the failure this project has been
most careful to avoid.

### Read the per-fault-type table

A difference between fault types is a more useful finding than a single average.
"Optical attenuation is catchable and geometric rotation is not" tells a
designer something. A pooled 62% tells them nothing, and hides it.

---

## Step 3b — P-5, faults nobody designed

`analyze_leadtime.py --undesigned` → `P5_UNDESIGNED_FAULTS.md`

Same monitor, same threshold, same code — different sessions and **different
provenance**. P-3's onsets were drawn and checksummed before the recording
existed; P-5's were written down afterwards from a stopwatch, because the fault
was the moment your hand moved.

The report puts the two side by side and says which way the gap went.

| Outcome | What it licenses |
|---|---|
| Undesigned faults **harder** to catch | A finding about how fault benchmarks are built, **including this project's own**. A monitor evaluated only on invented faults is being graded on a paper its author wrote. Headline, not limitation. |
| Undesigned faults **easier** to catch | A real physical fault disturbs more of the signal at once than a clean equation applied to one property of it — so the designed benchmark is the harder, more conservative test. |
| The two are **close** | The result the designed benchmark needs in order to be trusted. Worth stating plainly, because it could easily have gone the other way. |

With ten P-5 sessions only a large difference is detectable. **Read a small gap
as "not measured", not as "no difference".** The two are not the same claim and
the write-up must not blur them.

Never quote a P-5 number as if it were a P-3 number. The separation is the
reason the drawn onsets mean anything.

## Step 4 — P-4, the experiment that tests the hypothesis

`analyze_correlation.py` → `P4_CORRELATION_VS_USABILITY.md`

The hypothesis:

> A decoder-health monitor can show a strong correlation with task performance
> while simultaneously being unusable as a warning system.

The field validates this class of monitor by correlating its score against task
performance. MINDFUL reports r = 0.93 and 0.72 that way and proposes the monitor
for deciding when to recalibrate. This experiment computes **both** on the same
recordings: the correlation the field would report, and the lead time and
false-alarm rate that decide usability.

### Why three correlations and not one

Both the risk score and the performance drift with time, and **any two drifting
quantities correlate**. So the report gives the raw correlation, the correlation
with the time trend removed from both, and the correlation on changes rather
than levels. If the raw figure is large and the other two are not, the published
style of number may be measuring the passage of time.

The hypothesis counts the correlation as "strong" if **any** of the three clears
0.70 — not just the raw one. An earlier version tested only the raw figure and
called a monitor "not strongly correlated" at raw 0.698 while its partial
correlation was 0.915, which is not a defensible reading.

### All three outcomes are worth reporting

| Outcome | What it means |
|---|---|
| Strong correlation, unusable warning | **Hypothesis supported.** Correlation-based validation does not support the claims made from it. Since that is the standard way this class of monitor is validated, and since neither lead time nor false-alarm rate has been reported for any of them, the evidence base for drift-triggered recalibration is weaker than it appears. |
| Strong correlation, usable warning | **Hypothesis falsified.** Correlation-based validation is adequate — which strengthens the published approach and is equally worth reporting. |
| Correlation collapses when the trend is removed | Published correlations of this kind may be inflated, and the control is necessary. |
| No measure reaches 0.70 | Inconclusive. A weakly correlated monitor says nothing about whether correlation-based validation is sufficient. Report it as inconclusive, not as evidence either way. |

**This project cannot predict which it will get.** That is what makes it an
experiment rather than a demonstration.

---

## Step 5 — P-6, the decision rate

`analyze_decision_rate.py` → `P6_DECISION_RATE.md`

The computational monitor failed for a reason that had little to do with the
detector: it was deciding 720 times an hour, so a budget of 0.1 false alarms per
hour left each decision a false-positive rate of 0.00014 — needing an AUC of
about 0.9992.

This re-scores the same recordings at every rate from one decision per window to
one per session, choosing a fresh threshold at each rate so the comparison is at
equal false-alarm cost.

| Curve | What it licenses |
|---|---|
| **Rises**, intervals separated | Deciding less often genuinely helps. A design rule for any drifting many-channel sensor: check on the timescale the failure develops over, and no faster. |
| **Falls**, intervals separated | Pooling destroys more than the looser budget buys. The correct design move is the opposite of the obvious one — the limitation is in what the statistic can see, not how often it is consulted. |
| Intervals overlap | **Not settled.** The same position the computational half was left in. Say so; more degraded sessions would narrow it, nothing else will. |

---

## What none of this can show

Write these into the limitations section before the results tempt you out of
them.

- **One apparatus, in one room.** A false-alarm rate measured here does not
  transfer to an implanted array, and no claim is made that it does. What
  transfers is the *method*: onsets fixed in advance, lead time and false-alarm
  rate reported as a pair, enough fault-free recording to bound the rate.
- **Cardboard is not cortex.** The apparatus was tuned to match the neural
  decoder's difficulty, which makes the comparison fair. It does not make it a
  brain.
- **The faults are still mostly designed.** P-5 exists precisely because the
  other faults are equations someone wrote. If P-5's undesigned faults behave
  differently, that is a finding about this project's own benchmark. P-5 is
  itself only ten sessions, and its onsets rest on a stopwatch, so it is a
  partial answer rather than a complete one.
- **Sessions are five minutes.** A monitor that only misbehaves after an hour of
  continuous running would not be caught.
- **Every number depends on the threshold**, which depends on the budget. The
  verdict is conditional on a stated budget and is meaningless without it.

---

## The rule about re-running

If you change an analysis script, re-run **every** report it affects and commit
the regenerated files together. A repository where `P2_FALSE_ALARM_RATE.md` was
produced by an older version of the script than `P3_LEAD_TIME.md` is a
repository whose numbers do not agree with each other, and finding out which is
stale is much harder than re-running five commands.
