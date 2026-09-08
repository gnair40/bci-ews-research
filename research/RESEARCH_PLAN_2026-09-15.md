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

Intracortical brain–computer interfaces (iBCIs) allow people with paralysis to
control computers and communication devices directly from recorded neural
activity (Hughes et al.; Pun et al.). An implanted electrode array records
signals from motor cortex, and software called a decoder converts that activity
into intended movement. Their central unsolved engineering problem is not
accuracy on the first day but reliability over months and years, because the
recorded signal is not stationary: electrode impedance changes, individual
recorded units are lost, and the relationship between neural activity and
intended movement drifts. This is established across long observation periods and
many implants — Barrese et al. analysed failure modes across seventy-eight
arrays, Sponheim et al. characterised longevity and reliability across more than
six thousand datasets spanning nine years, and Hughes et al. documented five
years of array performance in a single human participant. The process is slow and
gradual, which is exactly what makes it hard to notice, and the consequence is
that a decoder can go on producing confident output from a signal that no longer
matches what it was trained on. That the degradation is measurable in the signal
itself, and not only in the user's task outcomes, was shown by Pun et al., who
found that a statistical measure of neural instability tracks closed-loop
performance in chronic human recordings.

The field's response has been almost entirely corrective rather than diagnostic,
treating drift as a nuisance to be removed: Karpowicz et al., for instance,
stabilise performance by realigning the underlying latent dynamics so that a
fixed decoder keeps working as the recording changes. The alternative in routine
use is recalibration, in which the user stops, performs a supervised block, and
the decoder is refitted — a procedure that costs the user time, requires
supervised data, interrupts use entirely on many systems, and is at present
scheduled by convention rather than by evidence that it is needed. The
established framework for anticipating a transition of this kind comes from
dynamical systems theory, where a system's recovery from small perturbations
slows near a tipping point and its variance and autocorrelation rise accordingly
(Scheffer et al.), a framework Maturana et al. applied to human neural data as a
biomarker for seizure susceptibility. That framework is genuinely contested, and
the disagreement bears directly on the present question: Wilkat et al. found no
evidence of critical slowing down before human epileptic seizures, Helmich et al.
argue that the clinical evidence base is thinner than it is usually presented to
be and caution against applying the framework without first checking that its
assumptions hold, and van der Bolt et al. show that the length of record required
to detect such a signal scales with how slowly the system responds — a serious
constraint for a process that unfolds over months. Taking that criticism
seriously, rather than assuming the framework applies, is a design commitment of
this project.

A substantial body of work therefore exists on correcting drift (Karpowicz et
al.; Pun et al.), considerably less on noticing it early enough to act, and —
more importantly — there is no agreed way to test whether a system that claims to
notice it actually works. That second gap is what this project targets, and it
has a specific technical cause: in observational recordings nobody knows when
deterioration actually began, because the onset is identified by the analyst
after the fact. Any claim about how early a warning arrived therefore depends
partly on that definition rather than on the world, and the rate of false alarms
cannot be estimated at all, yet lead time and false-alarm rate are the only two
quantities that determine whether a warning system is worth deploying. Both
become measurable only in a system where the experimenter controls, and records
in advance, when the degradation begins; building such a system, and the test
procedure that goes with it, is the substance of this project. The practical case
is direct, since iBCIs are moving from research demonstrations toward clinical
use (Hughes et al.; Karpowicz et al.; Pun et al.): a device whose reliability
cannot be monitored is a device its user cannot fully trust, and knowing when a
neural interface needs attention — and being told why — is a prerequisite for one
that somebody can depend on daily.

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

Formatted in MLA style and listed alphabetically by author. Author first names
appear as initials where the source list carries initials; these should be
expanded from the published papers before final submission.

Barrese, J. C., et al. "Failure Mode Analysis of Silicon-Based Intracortical
Microelectrode Arrays in Non-Human Primates." *Journal of Neural Engineering*,
vol. 10, no. 6, 2013, p. 066014, https://doi.org/10.1088/1741-2560/10/6/066014.

Helmich, M. A., et al. "Slow Down and Be Critical before Using Early Warning
Signals in Psychopathology." *Nature Reviews Psychology*, vol. 3, 2024, pp.
767–80, https://doi.org/10.1038/s44159-024-00369-y.

Hughes, C. L., et al. "Long-Term Intracortical Microelectrode Array Performance
in a Human: A 5 Year Retrospective Analysis." *Journal of Neural Engineering*,
vol. 18, no. 4, 2021, https://doi.org/10.1088/1741-2552/ac1add.

Karpowicz, B. M., et al. "Stabilizing Brain-Computer Interfaces through Alignment
of Latent Dynamics." *Nature Communications*, vol. 16, 2025,
https://doi.org/10.1038/s41467-025-59652-y.

Maturana, M. I., et al. "Critical Slowing Down as a Biomarker for Seizure
Susceptibility." *Nature Communications*, vol. 11, 2020, article 2172,
https://doi.org/10.1038/s41467-020-15908-3.

Pun, T. K., et al. "Measuring Instability in Chronic Human Intracortical Neural
Recordings towards Stable, Long-Term Brain-Computer Interfaces." *Communications
Biology*, vol. 7, 2024, https://doi.org/10.1038/s42003-024-06784-4. Dataset:
Dryad, CC0, https://doi.org/10.5061/dryad.n2z34tn5s.

Scheffer, M., et al. "Early-Warning Signals for Critical Transitions." *Nature*,
vol. 461, 2009, pp. 53–59, https://doi.org/10.1038/nature08227.

Sponheim, C., et al. "Longevity and Reliability of Chronic Unit Recordings Using
the Utah, Intracortical Multi-Electrode Arrays." *Journal of Neural Engineering*,
vol. 18, no. 6, 2021, p. 066044, https://doi.org/10.1088/1741-2552/ac3eaf.

van der Bolt, B., et al. "No Warning for Slow Transitions." *Journal of the Royal
Society Interface*, vol. 18, no. 174, 2021, article 20200935,
https://doi.org/10.1098/rsif.2020.0935.

Wilkat, T., et al. "No Evidence for Critical Slowing Down prior to Human
Epileptic Seizures." *Chaos*, vol. 29, no. 9, 2019, p. 091104,
https://doi.org/10.1063/1.5122759.

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
