# Research Plan — September 2026 submission

**Researcher:** Gayathri Nair
**School:** `[[RESEARCHER]]`
**Adult Sponsor:** `[[RESEARCHER]]`
**Submission date:** 15 September 2026
**Category:** Systems Software / Biomedical Engineering `[[RESEARCHER — confirm]]`

**Working title:** *Detecting Failure in Brain–Computer Interface Decoders*

---

> ## Note on scope — read this first
>
> **This is the September draft: a summary, not the full plan.** The complete
> methodology, the preregistered predictions, the validation criteria and the
> results to date are held in the project repository and will be submitted with
> the **December final plan**, once the experimental component is under way.
>
> **Nothing in this document is inaccurate.** Detail is omitted; nothing is
> misstated. Where a section is deliberately general, it says so.
>
> **One category of information is given in full and is not summarised:
> Section D, Risk and Safety.** A review committee cannot assess a project it
> cannot see, and vagueness about safety is the one kind that causes a plan to
> be rejected rather than protected.

---

## A. Rationale

People with paralysis can control a computer cursor through an implanted
electrode array and software called a **decoder**, which converts recorded neural
activity into intended movement. Over months and years the recording changes —
electrodes degrade, tissue responds, and the neural signal itself shifts — and
the decoder gradually produces the wrong output from a signal that no longer
matches what it was trained on.

The standard remedy is **recalibration**: the user stops what they are doing and
performs a supervised block so the decoder can be refitted. It is disruptive, and
it is currently scheduled by convention rather than by evidence that it is
needed.

A substantial body of work exists on *correcting* this drift. Considerably less
exists on *noticing it early enough to act*, and there is no standard way to test
whether a system that claims to notice it actually works. That gap — the absence
of an agreed test, rather than the absence of a detector — is what this project
addresses.

---

## B. Research question, engineering goal, and hypothesis

These are kept as three separate statements, so that an engineering objective is
not mistaken for a scientific claim.

**Research question.**
When a neural interface degrades, does the statistical structure of the recorded
signal change measurably *before* task performance changes — and if so, can that
change be distinguished from the change caused by the user simply doing something
different?

**Engineering goal.**
Build a monitor that converts such a change into a usable warning, and — more
importantly — build the test that determines whether any such monitor works.

**Primary hypothesis.**
For degradations whose onset is known and controlled, a monitor reading only the
input signal will produce a warning before task performance crosses a
degradation threshold, at a false-alarm rate low enough to be useful.

**Falsification, stated in advance.**
The hypothesis is false if the median warning arrives at or after the performance
crossing, or if the false-alarm requirement cannot be met at any operating point.
**A negative result here is a reportable outcome, not a failed project** — the
test battery is the deliverable either way.

**A methodological problem the project addresses directly.** In observational
recordings, nobody knows when deterioration actually began. "How early was the
warning?" therefore depends on how the analyst defines the event, which makes the
answer partly an artefact of that definition. This project's response is to build
data in which the onset is chosen and recorded in advance. *(Approach summarised;
detail in the December plan.)*

---

## C. Procedures

The project has three components. Methods are described at the level of what is
done, not how each step is implemented.

### C.1 Analysis of an existing public dataset — **complete**

A publicly archived dataset of chronic intracortical recordings (Pun et al.,
2024; Dryad, CC0 licence — see Bibliography) was downloaded programmatically with
checksum verification and analysed. The analysis was **preregistered**: the
design, the outcome measure and the success criteria were written to a
version-controlled file with a timestamp and data checksums *before* any analysis
was run, so that predictions cannot be adjusted after seeing results.

Raw data is held read-only and separately from all derived files; original files
are never modified.

### C.2 A benchmark with controlled onset — **complete**

Because observational data cannot establish when degradation began, a set of
degradation episodes was constructed in which **the onset time is chosen and
recorded in advance**, under a checksum, before any detector existed. A frozen
reference model grades the episodes. A battery of pass/fail criteria was defined
and committed before any detector was evaluated against it.

*Specific fault types, severity levels, and the composition of the criteria are
summarised here and detailed in the December plan.*

### C.3 An original physical experiment — **planned, not begun**

A bench instrument will be built to test whether the findings from C.1–C.2 are
specific to neural recordings or general to any multichannel sensor array that
drifts slowly. It consists of a small single-board computer, a camera module, a
display presenting a controlled visual pattern, and a light-excluding enclosure.
The camera's image is divided into fixed regions; each region's average intensity
is treated as one channel, giving a multichannel array structurally comparable to
the archived data.

Degradations of known onset are then introduced, in two classes:

- **Designed** — controlled changes to the emitted pattern.
- **Undesigned** — real physical interventions (loosening a connector, inserting
  an optical filter, thermal change, electromagnetic interference, lens
  contamination, physical rotation of the camera), where the experimenter knows
  *when* the fault began but did not design what its signature would look like.

A parallel arm records one identical session per day for 6–10 weeks with **no**
intervention, to observe natural degradation.

**A go/no-go criterion is applied before any fault is introduced:** the
instrument's healthy behaviour must fall within a specified range of the archived
data's healthy behaviour. If it cannot, the comparison is not made and that
limitation is reported. *Criteria are specified in the preregistration and will
appear in the December plan.*

**Nothing will be built until the experimental preregistration is committed.**

---

## D. Risk and Safety

**This section is complete and is not summarised.**

### D.1 Human participants — **none**

**No human participants are involved at any stage, including the researcher.**
Nobody is recruited, surveyed, interviewed, imaged, recorded, or measured. The
camera is enclosed and points at a display; no person is ever in its field of
view or is a source of data.

The archived dataset was collected years earlier by other researchers under their
own institutional approvals, is de-identified, and is released under a CC0 public
domain licence. Where project documents use the word "participant," it refers to
**whose published recording a data file contains** — the depositing authors'
own convention for labelling their de-identified subjects — and never to a person
this project recruits.

*Form 4 and SRC human-participants approval are not expected to be required.*
**To be confirmed with the SRC rather than assumed.**

### D.2 Vertebrate animals — **none.** No animal work of any kind.

### D.3 Potentially hazardous biological agents — **none.** No biological
material of any kind.

### D.4 Hazardous chemicals, activities and devices

| Item | Assessment |
|---|---|
| Electrical supply | 5 V DC from a regulated USB power supply. **No mains wiring, no exposed conductors, no capacitors above logic level, no batteries beyond a sealed USB power bank.** |
| Stepper motor | 5 V, low-torque hobby motor with driver board. Operated only with the enclosure closed. Pinch hazard mitigated by keeping hands clear while powered. |
| Display | Standard consumer monitor or tablet. Operated inside a closed enclosure; the researcher does not view it at close range at high brightness. |
| Thermal intervention | A household hair dryer on its lowest setting, at a distance of no less than 30 cm, in bursts of no more than 60 seconds, with the component temperature not exceeding 50 °C. **No heat gun, hotplate, open flame or oven is used at any point.** |
| Optical filter | Photographic neutral-density gel sheet. Inert plastic; no hazard. |
| Chemicals | **None.** No solvents, adhesives beyond hot glue, or consumables. |
| Sharps / tools | Scissors and a craft knife for cardboard, used with a cutting mat. Soldering is **not** required by the design; if it becomes necessary it will be performed under adult supervision with eye protection and ventilation. |

**Waste disposal.** No hazardous waste is generated. Electronic components are
retained; cardboard is recycled.

**Supervision.** All construction is performed at `[[RESEARCHER — home / school
lab]]` under the supervision of the Adult Sponsor named above.

*Form 3 is not expected to be required for low-voltage bench electronics
connected to no person.* **To be confirmed with the SRC rather than assumed, and
the Rules Wizard will be re-run once the build decision is final.**

---

## E. Data Analysis

- **Analysis is preregistered.** Outcome measures, success thresholds and
  predictions are committed to a timestamped, version-controlled file before the
  corresponding data is collected or examined. Predictions that turn out wrong
  are reported as wrong.
- **Data is split before analysis**, with a held-out portion examined only once.
- **Non-parametric statistics** are used throughout, given small samples and
  non-normal distributions.
- **Confidence intervals are obtained by resampling at the level of the
  independent unit**, not at the level of individual measurements, because
  measurements taken close together in time are not independent of one another.
- **Results are verified automatically.** Every figure quoted in project
  documents is recomputed from the stored data files by a script, so a number
  that stops matching its source is caught rather than trusted.
- **Both classes of physical fault (designed and undesigned) are reported
  separately**, since whether findings generalise from one to the other is a
  claim to be tested rather than assumed.

*Specific statistical tests, thresholds and the verification battery are detailed
in the December plan.*

---

## F. Bibliography

1. Barrese, J. C., Rao, N., Paroo, K., Triebwasser, C., Vargas-Irwin, C.,
   Franquemont, L., & Donoghue, J. P. (2013). Failure mode analysis of
   silicon-based intracortical microelectrode arrays in non-human primates.
   *Journal of Neural Engineering, 10*(6), 066014.
   https://doi.org/10.1088/1741-2560/10/6/066014
2. Helmich, M. A., Olthof, M., Oldehinkel, A. J., Wichers, M., Bringmann, L. F.,
   & Smit, A. C. (2024). Slow down and be critical before using early warning
   signals in psychopathology. *Nature Reviews Psychology, 3*, 767–780.
   https://doi.org/10.1038/s44159-024-00369-y
3. Hughes, C. L., Flesher, S. N., Weiss, J. M., Downey, J. E., Collinger, J. L.,
   & Gaunt, R. A. (2021). Long-term intracortical microelectrode array
   performance in a human: A 5 year retrospective analysis. *Journal of Neural
   Engineering, 18*(4). https://doi.org/10.1088/1741-2552/ac1add
4. Karpowicz, B. M., et al. (2025). Stabilizing brain-computer interfaces through
   alignment of latent dynamics. *Nature Communications, 16*.
   https://doi.org/10.1038/s41467-025-59652-y
5. Maturana, M. I., et al. (2020). Critical slowing down as a biomarker for
   seizure susceptibility. *Nature Communications, 11*, 2172.
   https://doi.org/10.1038/s41467-020-15908-3
6. Pun, T. K., Khoshnevis, M., Hosman, T., et al. (2024). Measuring instability in
   chronic human intracortical neural recordings towards stable, long-term
   brain-computer interfaces. *Communications Biology, 7*.
   https://doi.org/10.1038/s42003-024-06784-4
   [Dataset: Dryad, CC0, https://doi.org/10.5061/dryad.n2z34tn5s]
7. Scheffer, M., et al. (2009). Early-warning signals for critical transitions.
   *Nature, 461*, 53–59. https://doi.org/10.1038/nature08227
8. Sponheim, C., et al. (2021). Longevity and reliability of chronic unit
   recordings using the Utah, intracortical multi-electrode arrays. *Journal of
   Neural Engineering, 18*(6), 066044. https://doi.org/10.1088/1741-2552/ac3eaf
9. van der Bolt, B., van Nes, E. H., & Scheffer, M. (2021). No warning for slow
   transitions. *Journal of the Royal Society Interface, 18*(174), 20200935.
   https://doi.org/10.1098/rsif.2020.0935
10. Wilkat, T., Rings, T., & Lehnertz, K. (2019). No evidence for critical slowing
    down prior to human epileptic seizures. *Chaos, 29*(9), 091104.
    https://doi.org/10.1063/1.5122759

---

## G. Use of artificial intelligence

`[[RESEARCHER — to be written by the researcher. Not drafted here.]]`

> Reminder of what this section has to cover, so nothing is missed: whether AI
> tools were used, which ones, for what (e.g. code, analysis, writing, literature
> search), and what the researcher did independently. The form's wording changes
> year to year and AI use is listed among the grounds for disqualification, so
> check the current year's wording and confirm with the SRC.

---

## H. Checklist before submission

- [ ] Adult Sponsor has reviewed and signed
- [ ] Rules Wizard run for the current year
- [ ] Category confirmed
- [ ] Section G written
- [ ] School and Sponsor fields filled
- [ ] SRC asked to confirm the Form 3 / Form 4 assessments in Section D
- [ ] Supervision location stated in D.4
