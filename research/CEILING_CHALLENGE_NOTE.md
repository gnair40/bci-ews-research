# Ceiling challenge to the P5 result — scope and predictions fixed before running

**Written:** 3 September 2026, before computing anything. This is a deliberate
attempt to break my own headline finding.

## The finding under challenge

P5: the monitor's per-day accuracy is predicted by that day's decoder error
(ρ = −0.720, p = 0.0055, preregistered). I called this a structural objection to
the design — the monitor fails on the days it exists for.

I already tested one artifact channel (whether high-error days produce shorter
early-warning windows or a shifted crossed/not-crossed split) and it did not hold.
**I missed a second one, and it is more dangerous.**

## The channel I missed

An episode "crosses" when smoothed decoder error exceeds **its own pre-onset
baseline plus 10°** (`crossing_window` in `20_evaluation_harness.py`). That is a
sound definition — it is relative, not absolute — but it interacts badly with a
day whose baseline is already near chance:

- Measured chance on T11 is **90.7°**. Day 783's baseline is **89.3°**.
- A fault on that day has roughly **1.4° of headroom** before the error metric
  saturates. It cannot get much worse because it is already as bad as random.

If injected faults do **less measurable damage** on high-error days, then the
ground truth on those days is weaker, the faulted and healthy episodes are
genuinely less separable, and **every** detector would score lower — for reasons
that have nothing to do with the monitor being unreliable when it matters.

That would not make P5 false. It would change what it means, from *"the monitor
fails when the decoder fails"* to *"faults are harder to measure when the decoder
is already near chance"* — a statement about the measuring instrument, not about
the monitor.

## Predictions, committed in advance

**I think the confound is real and I expect to find it.** I am not setting up a
straw man to knock down. Specifically:

| | Predicted |
|---|---|
| achieved fault damage vs that day's decoder error | **negative** — less headroom on bad days |
| achieved fault damage vs monitor AUC | **positive** — weaker faults are harder to see |
| P5 after controlling for achieved damage | **weakens substantially** |

If instead damage is flat across days, the ceiling channel is closed and P5 stands
as originally stated.

## Fixed in advance

| | |
|---|---|
| Achieved damage | median decoder error over the post-onset windows **minus** the episode's own pre-onset baseline, in degrees — the same baseline the crossing rule uses |
| Episodes | the faulted episodes already in `episode_scores*.csv`, unchanged |
| Aggregation | per day, median across that day's faulted episodes |
| Decisive test | partial Spearman of decoder error vs monitor AUC, **controlling for achieved damage** |
| Reported | both participants, whatever it shows, including if it destroys the headline |

## What I will do with each outcome

- **Confound confirmed** → `reports/DAY_PREDICTORS.md` and the README headline are
  rewritten to the narrower claim, and the log records that I published a stronger
  claim than the data supported for one day before catching it.
- **Confound absent** → P5 stands, and it now stands against two named challenges
  instead of one.

Either way the result goes in. This note exists so that the second outcome cannot
be presented as though the first had never been a live possibility.

---

# Addendum, 3 September 2026 — unambiguous episodes only

**Written before running.**

## The question this leaves open

The ceiling challenge established that the spurious-crossing rate — how often the
+10° threshold is cleared by noise alone — reaches 19.9% on the worst day and
correlates with monitor accuracy at ρ = −0.665. So **some** of the day-to-day
spread is contaminated labels rather than failed detection. Controlling for it
leaves ρ = −0.613 (p = 0.034), so not all of it.

"Some but not all" is unsatisfying. There is a sharper test.

## The test

Keep only the faulted episodes where the fault **demonstrably did real damage** —
achieved damage ≥ 10°, the same threshold the crossing rule uses, but measured as
a median over all post-onset windows rather than a single smoothed excursion. On
those episodes the ground truth is unambiguous whatever the day's noise level.
Then recompute the per-day accuracy and re-run the decoder-error correlation.

- **Day effect persists among unambiguous episodes** → it is the monitor failing,
  not the labels. The finding hardens.
- **Day effect vanishes** → it was contaminated ground truth, and the whole
  bad-day result needs restating as a fact about the corpus.

## Predictions, committed

**I expect it to weaken substantially but not vanish** — consistent with the
partial correlation already measured (−0.720 → −0.613 controlling for spurious
crossings).

**I also expect the worst days to lose most of their episodes**, because day 783's
median achieved damage is +0.4°. If a day retains too few unambiguous episodes to
score at all, **that is the result for that day and it is reported as such**, not
worked around by lowering the threshold.

## Fixed in advance

| | |
|---|---|
| Filter | faulted episodes with achieved damage ≥ 10°; comparison group unchanged (non-crossing episodes) |
| Minimum | a day needs ≥ 5 in each group to be scored, same as everywhere else |
| Not permitted | lowering the 10° threshold after seeing how many days survive |
| Reported | both participants, the retained counts per day, and the correlation on whatever days remain |
