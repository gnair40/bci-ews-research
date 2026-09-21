# Preregistration — the physical-validation phase

**Drafted:** 20 September 2026.
**Status: DRAFT — NOT FROZEN. Nothing has been built and nothing measured.**
**Frozen at commit:** `[[RESEARCHER — fill in after running the freeze in §10]]`

---

## 0. Read this before anything else

### 0.1 What this document is for

Everything in this project since Phase 3 has followed one rule: **write down
what you expect, and what would count as being wrong, before you look.**

The reason is not tidiness. If you test five things and report the one that
worked, that looks identical on paper to predicting one thing correctly. This
document is what makes those two look different, and **it only works if its
timestamp precedes the data.**

`02_EXPERIMENTS.md` already states what each outcome would mean. This document
does the harder part: it attaches **numbers** to those outcomes, so that "the
monitor was quiet enough" cannot be decided after the fact by whoever is looking
at the graph.

After the freeze in §10 this file must not be edited — only amended, in public,
per §9.

### 0.2 Who wrote this draft, and what that means

**This draft was written by an AI assistant from findings already in this
repository. It is not yet the researcher's preregistration, and it must not be
frozen until the researcher has read every prediction and either accepted it or
changed it.**

The distinction that matters:

- The **derivations** are mechanical. Each prediction follows from a measured
  number already in this repository, and the source is cited on every line.
- The **thresholds** are judgement calls. A threshold is a statement about what
  would count as interesting, and that is the researcher's to make.

Every judgement call is collected in §11 so none of them can be accepted by
inattention.

### 0.3 One thing that is different from the earlier preregistration

`research/RIG_PREREGISTRATION.md` governed a study that has been superseded
(its §14). **Its predictions P-R1 to P-R10 are not carried forward**, and no
result from this phase may be reported as confirming or refuting them. This
document replaces it completely.

---

## 1. The hypothesis, and how it will be judged

> **Reframed 21 September 2026 from an existence claim to a measurement claim.**
> "A monitor *can* correlate strongly and be unusable" is close to a statistical
> truism. What this phase does is **measure two quantities nobody has
> measured**. See `01_RESEARCH_DESIGN.md` §3 and
> `research/REASSESSMENT_2026-09-21.md` §3.1. The judging rule below is
> unchanged — it was always a measurement rule.

> **Primary:** for a monitor of the class proposed for deciding when to
> recalibrate, the lead time and false-alarm rate, measured against onsets fixed
> in advance with enough fault-free recording to bound the rate, fall outside
> what a deployed system could use.

> **Secondary:** that monitor reaches the correlation the field reports as
> evidence, while those two measured quantities say it is unusable.

Judged by a rule fixed here, computed by
`physical/code/analyze_correlation.py`, with no discretion left at the end:

| | Condition | Measured by |
|---|---|---|
| **Strong correlation** | any of \|raw\|, \|partial\|, \|differences\| ≥ **0.70** | DV5 |
| **Unusable** | median lead time ≤ 0 **or** false-alarm rate above budget | DV1, DV2 |
| **Supported** | strong **and** unusable | both |
| **Falsified** | strong **and** usable on both counts | both |
| **Inconclusive** | no measure reaches 0.70 | DV5 |

**"Inconclusive" is a real outcome and will be reported as one.** A weakly
correlated monitor says nothing about whether correlation-based validation is
sufficient, and claiming otherwise would be the easiest available way to turn a
null result into an apparent finding.

---

## 2. The predictions

Each states what is expected, where the expectation comes from, what would
falsify it, and what either outcome would mean. **None is a success criterion
for the project.** A phase in which every prediction fails is a phase that has
measured something.

---

### PP-1 — The false-alarm rate will exceed the budget

> On fault-free sessions held out from both fitting and threshold selection, the
> monitor will produce **more than 0.1 false alarms per hour**.

**Derivation.** The same monitor on archived neural recordings produces
**3.41 per hour** (T11) and **0.225 per hour** (T5), both above the 0.1 budget
(`data/processed/monitorability_certificate_T11.json`, `_T5.json`).

**Falsified if** the 95% upper bound on the rate is **at or below 0.1 per hour**.
With zero observed false alarms that requires roughly **30 hours of held-out
fault-free recording** (rule of three; see `02_EXPERIMENTS.md` P-2). **With less
recording than that, this prediction cannot be falsified**, only left untested —
which is itself a result about the campaign rather than about the monitor, and
will be reported in those words.

**Either way.** Above budget quantifies by how much, which nobody currently
knows for any monitor of this class. Within budget would be the first
demonstration that such a monitor can be quiet enough to deploy.

---

### PP-2 — The silence gate will fail

> **More than 10%** of fault-free sessions will show a statistically significant
> monotonic trend in the risk score.

**Derivation.** On genuinely fault-free neural episodes the gate fails at
**76.5%** (T11) and **100%** (T5) against the same 10% bar
(`reports/AUTOCORR_BY_SEVERITY.md`; `data/processed/harness_summary*_local.json`).

**Falsified if** 10% or fewer of fault-free sessions trend significantly.

**This is the most informative prediction in the document, and the one most
likely to be wrong.** A failure here, on an apparatus containing no biological
material, no electrodes and no brain, would make the computational failure very
hard to attribute to neural recordings and would point at the monitoring
approach itself. A pass would mean the opposite: that the computational failure
is specific to neural data, which is a stronger and more surprising claim than
this project currently makes anywhere.

**Reported twice**, on the risk score as measured and after removing a linear
trend, and the two are never merged. If silence survives only after detrending,
that says the drift is close to linear — but a deployed monitor must subtract it
causally, from past windows only, which is harder than doing it afterward with
the whole session in hand.

---

### PP-3 — The median lead time will not be positive

> The median lead time across degraded sessions will be **at or below zero
> seconds** — the warning arrives at or after decoding performance fails.

**Derivation.** Median lead time on archived recordings is **−20 s** (T11, 95%
CI −25 to −10) and **−35 s** (T5), at the threshold meeting each participant's
false-alarm budget (monitorability certificates, as above).

**Falsified if** the median is positive and its 95% bootstrap interval excludes
zero.

**Either way.** A negative lead time confirmed on an independent physical system
says the limitation is not a property of neural tissue. A positive one, at a
false-alarm rate within budget, would be the first usable warning anyone has
measured for this class of monitor — and would have to be reported together with
that rate, never alone.

---

### PP-4 — The correlation will be strong by at least one measure

> At least one of the raw, partial or first-difference correlations between the
> monitor's score and task performance will have magnitude **≥ 0.70**.

**Derivation.** At session level on archived recordings, T11 gives raw
**−0.818**, partial **−0.500**, differences **−0.679**; T5 gives partial
**−0.852** (`data/processed/session_level_monitor.json`). The published state of
the art reports **0.93** and **0.72** (Pun et al., 2024).

**Falsified if** all three measures fall below 0.70 in magnitude, in which case
the hypothesis test is **inconclusive**, not supported and not refuted.

**Why any of three rather than the raw one.** An earlier version of this
project's analysis tested only the raw figure and described a monitor as "not
strongly correlated" at raw 0.698 while its partial correlation was 0.915. That
is not a defensible reading, and the rule is fixed here so it cannot recur.

---

### PP-5 — The raw correlation will exceed the partial correlation

> The magnitude of the raw correlation will be **greater** than the magnitude of
> the correlation with the time trend removed from both series.

**Derivation.** T11 raw **−0.818** against partial **−0.500**; the monitor's
score and task performance both trend with time (day vs drift **−0.939**, day vs
error **+0.750**), and any two drifting series correlate
(`data/processed/session_level_monitor.json`).

**Falsified if** the partial correlation is at least as large as the raw one.

**Why this is worth predicting separately.** It is the mechanism behind the
headline. If raw exceeds partial here as it does on neural data, then published
correlations of this kind may be partly measuring the passage of time, and the
control is necessary rather than fastidious. If it does not, the shared-trend
explanation is weaker than this project has assumed and that should be said.

---

### PP-6 — Detection will rise with severity

> Detection rate at severity **1.0** will exceed detection rate at severity
> **0.25**.

**Derivation.** Not from a number but from a requirement: a monitor that
responds to how bad the fault is, is responding to the fault. One that does not
is responding to something else, and every other result in the phase becomes
hard to interpret.

**Falsified if** detection is flat or falls across the severity ladder.

**If falsified, PP-1 to PP-5 are reported but not interpreted as being about
degradation**, because it would no longer be established that the monitor is
tracking degradation at all. This is the closest thing in this document to a
manipulation check.

---

### PP-7 — Deciding less often will help

> Detection at one decision per session will exceed detection at 720 decisions
> per hour by **at least 10 percentage points**, at equal false-alarm cost.

**Derivation, and the evidence against it.** Two mechanisms argue for it: a
looser budget per decision, and more evidence behind each decision.

**The archived evidence does not support it, and on one participant actively
contradicts it.** The published reading was that the intervals overlap so
nothing can be settled — but overlap of marginal intervals is not a test of a
difference, and both rates are scored on the same episodes. Re-done as a paired
test (`scripts/78_decision_rate_paired.py`, 21 September 2026):

| | Change, 720 → slowest | Paired 95% CI | Established? |
|---|---|---|---|
| T11 | +11.5% | −0.3% to +27.6% | no |
| **T5** | **−18.2%** | **−42.3% to −4.9%** | **yes** |

So the **one established result** in the archived data says deciding less often
makes detection **worse** — the opposite of this prediction.

**This prediction is therefore made against the weight of the available
evidence, deliberately and on the record.** That is legitimate: the mechanisms
are real, the archived thresholds rest on 29 and 21 fault-free episodes, and
the apparatus removes exactly that limitation. But it has to be stated, because
"we predicted the direction that the only significant evidence contradicted" is
a very different thing to report afterwards than "we predicted the obvious".

**If PP-7 fails** — if detection falls on the apparatus too — that is the more
likely outcome on current evidence and is **not a disappointment**. It would
mean pooling destroys more than the looser budget buys, which is the opposite
of the intuition this whole direction rests on, and it is the result that would
most change what a designer does.

**Falsified if** detection falls, or rises by less than 10 points, at one
decision per session.

**A correction that bears on this.** Deciding less often loosens the
per-decision budget by exactly the pooling factor and no more. At 720 decisions
an hour the budget permits a per-decision false-positive rate of 0.00014,
needing an AUC near 0.9992; at one decision per five-minute session it permits
0.0083, needing about **0.990**. Both are far above the 0.673 and 0.742 measured
on neural recordings. **The looser budget alone is therefore not a rescue**, and
what PP-7 actually tests is whether the second mechanism contributes anything
beyond it. (This project quoted 0.933 for the once-per-session target until
20 September 2026; that figure is the target at a 10% false-flag rate, roughly
thirteen times the budget. See `reports/OPERATING_POINT_BOUND.md`.)

---

### PP-8 — Undesigned faults: a comparison, with no direction predicted

> The detection rate on faults imposed by hand and not designed in advance will
> be compared against the detection rate on designed faults. **A difference of
> 20 percentage points or more** will be treated as meaningful.

**No direction is predicted, and that is deliberate.** There is no measured
number anywhere in this repository from which to derive one: every degradation
this project has ever tested was an equation someone wrote. Inventing a
direction here would be guessing dressed as a prediction.

**What each outcome would mean.** Undesigned faults meaningfully harder to
detect is a finding about how fault benchmarks are built — **including this
project's own** — and belongs in the write-up as a headline rather than a
limitation. Meaningfully easier suggests a real physical fault disturbs more of
the signal at once than a clean equation applied to one property of it, which
would make the designed benchmark the more conservative test. No meaningful
difference is the result the designed benchmark needs in order to be trusted.

**With approximately ten undesigned sessions only a large difference is
detectable.** A gap below 20 points will be reported as **not measured**, never
as *no difference*.

---

### PP-9 — The decision-rate direction will hold across apparatus configurations

> The sign of the decision-rate change will be **the same in all four**
> apparatus configurations of P-7.

**Derivation.** None from measurement — no one has run this. It follows from
the *claim* P-6 makes: if the decision-rate effect is a property of monitoring
drifting many-channel sensors, it should not depend on the exposure, the patch
size or the channel count, all of which are held at the same decoding
difficulty.

**Falsified if** any configuration reverses the sign.

**Either way.** Holding across four configurations is what would let the result
be stated as a design rule rather than an observation about one box. Reversing
is equally informative and more surprising: it would say the effect depends on
something the design has not identified, and name which configuration differs.

---

### PP-10 — The single-apparatus numbers will move across configurations

> The median lead time will differ by **more than 10 seconds**, or the
> false-alarm rate by **more than a factor of two**, between the four
> configurations.

**Derivation.** Also none — this is the self-applied version of the criticism
this project makes of two-participant conclusions. If four configurations of the
same box give materially different numbers, then a single-apparatus figure is
apparatus-specific and must be reported with its spread.

**Falsified if** all four agree closely, which would mean the numbers are more
robust to apparatus detail than expected — a genuinely useful thing to know and
the outcome that would most strengthen every other result here.

**This prediction expects the project's own headline numbers to be unstable.**
It is here because the alternative is discovering it after publication.

---

## 3. The gate: what must pass before any prediction is interpreted

Applied in this order. **A prediction evaluated on an apparatus that has not
cleared the gate is not evidence about anything.**

| | Condition | Where |
|---|---|---|
| G-a | The enclosure is light-tight: mean pixel < 2, max < 5, of 255 | `bench.py darkframe` |
| G-b | Recordings arrive intact: under 1% late frames, under 5% dead channels, under 1% clipped | `bench.py frames` |
| G-c | Display-to-camera delay is measured and agrees across three recordings | `bench.py lag` |
| G-d | The sub-brightness-level signal survives: median agreement > 0.02, positive on > 80% of channels | `bench.py dither` |
| G-e | **Difficulty matches the neural recordings: margin within 6° of 36.1°** | `bench.py margin` |

**G-e is the one that can stop the phase.** An apparatus decoding far better
than cortex has little to lose when degraded, and comparing it against one that
barely beats chance measures difficulty rather than monitoring. If the margin
cannot be brought within tolerance, §7 applies.

---

## 4. Sample sizes and stopping rules — fixed now

| Arm | Sessions | Fixed in advance because |
|---|---|---|
| Calibration (P-1) | 5 minimum, more permitted | These also build the decoder; more is strictly better and costs nothing later |
| Fault-free (P-2) | **`[[RESEARCHER — 101 floor, or ~360 to make PP-1 falsifiable]]`** | See PP-1 |
| Degraded (P-3) | **101**, spread across 4 types and 3 severities | Gives ~8 sessions per type-severity cell |
| Undesigned (P-5) | **10** | See PP-8 |
| Apparatus variation (P-7) | **3 × 40** (20 fault-free + 20 degraded each) | Enough to see a sign reversal (PP-9) or a large shift (PP-10); not enough to estimate either precisely, and the report says so |

**Stopping rules.**

1. **Recording stops at the planned count, not when a result appears.** The
   analysis scripts are not run against the accumulating campaign to decide
   whether to continue.
2. **A session is never discarded because of its result.** Sessions are
   discarded only for recorded mechanical reasons — dropped frames, a mistimed
   hand-imposed fault, an interrupted recording — and every discard is written
   in the research log with its reason at the time.
3. **No re-drawing.** `draw_onset.py` refuses to overwrite a plan, and
   `note_onset.py` refuses to overwrite a noted onset without `--replace` and a
   log entry.
4. **If the campaign is cut short**, the achieved count is reported and PP-1 is
   reported as untested rather than as failed.

---

## 5. The analysis plan, fixed now

Everything here is already implemented; this section fixes it so that it cannot
be adjusted after the data exist.

1. **Windows** of 30 s stepping 5 s, matching the neural analysis exactly.
2. **The decoder is frozen**, fitted once on the earliest fault-free sessions.
   The per-session refit is run as a stated sensitivity check, not as the
   primary analysis.
3. **Three disjoint groups**: fit, threshold-selection, and reporting. The
   false-alarm rate and lead time are reported only from the third.
4. **One free parameter**, the warning threshold, chosen on the
   threshold-selection group to meet the 0.1/hour budget, then applied unchanged.
5. **Warnings are timestamped at the end** of the window that produced them.
6. **A warning whose window ends before the onset is a false alarm**, not a
   detection, and is excluded from every timing figure.
7. **Lead time** is measured against performance crossing its own pre-onset
   baseline by 10°, the threshold fixed in `scripts/17_fault_injector.py` before
   any detector existed. **Detection delay** is measured against the drawn onset
   and reported separately.
8. **P-5 is never pooled with P-3.**
9. **Medians, not means**, throughout, with bootstrap intervals where n ≥ 3 and
   no interval quoted below that.
10. **Results are reported per fault type**, not only pooled.
11. **Zero events is reported as an upper bound**, never as a rate.

---

## 6. What this phase does not test

Stated now so that it cannot be quietly widened later.

- **It does not test MINDFUL or any other named published method.** It tests
  correlation-based validation *as a method*, using a monitor of the same family.
- **It does not test anything about brain tissue.** A camera in a box is not
  cortex. The claim under test concerns a class of measurement problem — many
  channels, drifting slowly, watched by a statistic.
- **It does not establish what a false alarm costs a user.** That question needs
  people, and this project has none.
- **One apparatus, one room.** The same caution that applies to two participants
  applies here with more force.
- **A different monitor might behave differently.** Nothing here bounds what is
  possible in general.

---

## 7. If the apparatus fails its calibration gate

If G-e cannot be met after adjusting modulation depth, exposure, and pixels per
channel:

1. Record the achieved margin and everything tried, in the research log.
2. **Report the phase as an apparatus that could not be matched to the neural
   operating point**, and say so plainly.
3. Do not proceed to PP-1 to PP-8 on an unmatched apparatus and describe the
   results as though the match had held.

A phase that stops here has still produced the benchmark design, the code, and a
measured reason it did not work — which is worth more than results from an
apparatus known to be too easy.

---

## 8. Human participants, safety, and rules

**No person is a subject of this research at any stage, including the
researcher.** Nobody is recruited, surveyed, interviewed, photographed, recorded
or measured. The camera is sealed inside a closed box pointing at a screen; no
person is ever in its field of view or a source of data.

Safety is covered in full in `03_MATERIALS_AND_SAFETY.md`. Nothing on the
materials list is hazardous; there is no mains wiring, no soldering, no
chemicals and no heating element beyond the bounded thermal intervention
described there.

---

## 9. Amendments

This document may be amended after freezing. It may not be edited.

1. Every amendment is a **new numbered section appended at the end**.
2. The original wording is **preserved inside the amendment**, quoted.
3. Each amendment states **what changed, why, and on what date**, and whether
   the data it governs had been seen.
4. An amendment made **after** the relevant data were seen is marked as such, in
   bold, at its head. It is not forbidden; it is disclosed.
5. The amendment log in §12 is updated in the same commit. *(The earlier
   preregistration's log said "(empty)" while three amendments existed. A log
   filled in afterward is not a log.)*

---

## 10. Freeze procedure

1. The researcher reads every prediction in §2 and every judgement call in §11,
   and edits anything they do not accept **as their own**.
2. Fill in the two `[[RESEARCHER]]` fields: the fault-free campaign length in §4
   and, after the commit below, the freeze hash at the top.
3. Commit:

```bash
git add physical/docs/09_PREREGISTRATION.md
git commit -m "Freeze the physical-phase preregistration before building anything"
git rev-parse HEAD
```

4. Paste the printed commit ID into the header and commit once more. **The
   timestamp on that commit is what makes every "before" in this document
   checkable rather than asserted.**

**After that commit exists, building may begin. Not before.**

Calibration sessions may be recorded before the freeze — they set the apparatus
up and are excluded from every result — but no session that counts as data.

---

## 11. Judgement calls requiring the researcher's decision

None of these follows from a measurement. Each is a statement about what would
count as interesting, and each is the researcher's to make.

| # | Call | Drafted at | Why that value |
|---|---|---|---|
| 1 | Fault-free campaign length | **undecided** | 101 is a floor; ~360 makes PP-1 falsifiable. This is the only one that changes what gets recorded. |
| 2 | "Strong" correlation threshold | **0.70** | Just below the weaker of the two published MINDFUL values (0.72), so clearing it puts the monitor in the same range as the state of the art |
| 3 | False-alarm budget | **0.1/hour** | Inherited unchanged from the computational design. Never relaxed. |
| 4 | Silence-gate bar | **10%** | Inherited unchanged, so the two phases are comparable |
| 5 | Decision-rate margin (PP-7) | **10 points** | Chosen to exceed T11's observed +11.5% only marginally, so the prediction is not trivially satisfied by noise |
| 6 | Undesigned-fault margin (PP-8) | **20 points** | Chosen for what ~10 sessions can actually resolve, not for what would be interesting |
| 7 | Severity check (PP-6) | **1.0 vs 0.25** | The ends of the ladder, where any response should be largest |
| 8 | Difficulty tolerance | **±6° of 36.1°** | Inherited from the rig design |
| 9 | Apparatus-shift margin (PP-10) | **10 s / 2×** | Chosen for what four configurations can resolve, not for what would be interesting |
| 10 | Number of P-7 configurations | **4** | Three extra is ~10 unattended hours; a fifth adds 3.5 h for little extra discrimination |

**Values 3, 4 and 8 are inherited and changing them would break comparability
with the computational half.** Values 2, 5, 6 and 7 are genuinely open. Value 1
is the scheduling decision.

---

## 12. Amendment log

*(No amendments. This document has not yet been frozen.)*
