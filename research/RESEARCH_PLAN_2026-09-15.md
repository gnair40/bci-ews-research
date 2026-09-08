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

Written so that somebody who has never seen this project, and has never used a
command line, can reproduce every step. Procedures are numbered for citation.
Each gives the exact command, what it does, and what you should see if it worked.

**Terms used below, defined once.** A **terminal** is a window where you type
commands instead of clicking. A **command** is a line of text you type and then
press Enter. A **script** is a saved file of instructions the computer runs. A
**repository** (or "repo") is the folder holding all the project's files and its
complete history of changes. **Git** is the program that records that history.
**Python** is the programming language everything here is written in.

Text shown like `this` is typed exactly as written. `~` means your home folder.

**One distinction that will otherwise waste your time.** Some files in `scripts/`
are **programs** you run; others are **libraries** — files of definitions that
other programs import and use, which do nothing if you run them on their own.
Four are libraries: `19_detectors.py`, `22_decoder_guard.py`,
`32_feature_families.py` and `35_general_guard.py`. They are written, not
executed, and each is flagged where it appears below.

---

### STAGE 0 — Prepare a computer (Procedures 1–6)

**Procedure 1. Open a terminal.**
On macOS press ⌘+Space, type `Terminal`, press Enter. On Windows install *Windows
Subsystem for Linux* first (`wsl --install` in PowerShell as administrator,
then restart), then open the *Ubuntu* app. On Linux press Ctrl+Alt+T.

**Procedure 2. Check whether Python is installed.** Type:
```
python3 --version
```
*Expect:* `Python 3.11.15` or any 3.11 or newer. If you get "command not found",
install Python from python.org (macOS/Windows) or run
`sudo apt install python3 python3-pip` (Linux/WSL).
*Why 3.11:* every result in this project was produced on 3.11.15. Older versions
may behave differently in ways that are hard to notice.

**Procedure 3. Check whether Git is installed.**
```
git --version
```
If missing: `sudo apt install git` (Linux/WSL) or install from git-scm.com.

**Procedure 4. Download the project.**
```
cd ~
git clone https://github.com/gnair40/bci-ews-research.git
cd bci-ews-research
```
`cd ~` moves you to your home folder. `git clone` copies the whole project,
including its history. `cd bci-ews-research` moves you into it.
*Expect:* a message ending "done." and a new folder.

**Procedure 5. Install the libraries the code needs.**
```
pip install -r requirements.txt
```
A **library** is pre-written code the project relies on. This installs six:
`numpy` (fast number arrays), `pandas` (tables with named columns), `scipy`
(scientific computing and statistics), `h5py` (reads MATLAB files), `matplotlib`
(graphs), and `requests` (downloads over the internet).
*Expect:* "Successfully installed" or "Requirement already satisfied".
*Why a file instead of typing names:* it pins the toolchain, so the same software
runs everywhere. A result that changes because a library quietly updated is a
real and common source of irreproducible research.

**Procedure 6. Confirm you are in the right place.**
```
ls
```
`ls` lists files. *Expect to see:* `data`, `reports`, `research`, `scripts`,
`tools`, `README.md`, `requirements.txt`.

---

### STAGE 1 — Obtain the archived dataset (Procedures 7–12)

**Procedure 7. Understand what is being downloaded and why it is legal.**
The dataset is *MINDFUL* (Pun et al.), deposited on Dryad under DOI
`10.5061/dryad.n2z34tn5s`, released under a **CC0** licence, which places it in
the public domain with no restriction on reuse. It was collected years earlier by
other researchers under their own institutional approvals and is de-identified.
**This project recruits nobody.**

**Procedure 8. Obtain Dryad API credentials.**
Dryad's public download route is protected by an anti-bot challenge that returns
a web page rather than data to any script. **That protection is not
circumvented.** Instead, use the repository's own supported route: create a Dryad
API account (authenticated with an ORCID iD, free at orcid.org), which issues
OAuth 2.0 client credentials.

**Procedure 9. Supply the credentials without ever writing them to a file.**
```
export DRYAD_CLIENT_ID="your-id-here"
export DRYAD_CLIENT_SECRET="your-secret-here"
```
`export` puts a value into the terminal's memory for this session only. It is
never saved to disk and never committed. Delete the API account after use.

**Procedure 10. Download, with automatic integrity checking.**
```
python3 scripts/01_download_dataset.py
```
This asks Dryad's API which files the deposit contains, downloads each one, and
computes a **SHA-256 checksum** of every file — a long fingerprint that changes
completely if even one byte differs — then compares it against the checksum Dryad
publishes.
*Expect:* two files. `MINDFUL_Data.zip` (411,951,588 bytes) and `README.md`
(3,348 bytes), both reported as verified. Roughly 400 MB; allow several minutes.
*If a checksum does not match, stop.* The download is corrupt and nothing built
on it can be trusted.

**Procedure 11. Unpack and inspect the archive without opening it by hand.**
```
python3 scripts/02_inspect_dataset.py --extract
```
*Expect:* 166 files extracted, 825,449,877 bytes, and a summary written to
`reports/inventory.json`.
*Why a script rather than double-clicking:* the inspection is recorded, so what
was in the archive on the day it was opened is a fact in the repository rather
than a memory.

**Procedure 12. Convert the data into tables, and look at it.**
```
python3 scripts/03_load_dataset.py --save
python3 scripts/04_explore_dataset.py
```
The first walks the folder tree of MATLAB `.mat` files and produces two flat
tables — one row per trial, one row per recording block — plus the neural arrays.
The second produces a descriptive report.
*Expect:* 54 blocks, 3,301 trials, and a written report at
`reports/DATASET_EXPLORATION.md`.
*Note on a trap this handles for you:* MATLAB numbers the first item in a list
`1`; Python numbers it `0`. Getting that wrong shifts every trial by one time
step and silently corrupts everything downstream. The loader converts and keeps
**both** versions so the conversion can be checked.
*Also deliberate:* the loader does **not** smooth, z-score, or remove outliers.
Those are not "loading" — each is a scientific decision that changes what the
results mean, so they are made later and visibly.

---

### STAGE 2 — Prove the tools work before trusting them (Procedures 13–18)

*This whole stage exists because a detector that has never been tested on a
system with a known answer cannot be trusted on a system without one.*

**Procedure 13. Confirm the published decoder really was fixed.**
```
python3 scripts/05_check_decoder_stability.py
```
The analysis assumes the original researchers' decoder was not being retrained
during the recordings. This tests that assumption against the data itself rather
than taking the paper's word for it.

**Procedure 14. Test the detector on systems whose answer is already known.**
```
python3 scripts/06_ews_controls.py
```
This builds two simulated systems: one that genuinely approaches a tipping point
(the detector **should** fire) and one that merely drifts steadily (it **should
not**). *Expect:* fires on the first, silent on the second. If it fails either,
the detector is broken and no result from real data would mean anything.

**Procedure 15. Find out how much data the detector needs.**
```
python3 scripts/07_ews_power_sweep.py
python3 scripts/08_record_length_check.py
```
The first measures how reliably the detector finds a real effect at different
record lengths; the second checks whether the actual recordings are long enough.
*Expect:* detection power rising from about 0.25 to 1.00 as records lengthen.

**Procedure 16. Reproduce somebody else's published result.**
```
python3 scripts/09_reproduce_mindful.py
```
This recomputes a figure from the original paper using this project's own code.
*Expect:* **r = 0.985**, matching the published 0.985.
*Why this matters more than any other check in Stage 2:* it is the only test that
compares this pipeline against an answer produced independently, by other people.
Passing it means the data is being read correctly.

**Procedure 17. Work out how large an effect could even be detected.**
```
python3 scripts/10_design_power_analysis.py
```

**Procedure 18. Record everything so far.**
```
git add -A
git commit -m "Stage 2 complete: tools validated"
```
`git add -A` marks all changes to be saved; `git commit` saves them with a note.
*Why now:* the record of what was done must be built as you go. Reconstructed
afterwards, it is no longer evidence.

---

### STAGE 3 — Preregister the analysis (Procedures 19–22)

*This is the stage that makes everything after it credible.*

**Procedure 19. Understand what preregistration is.** You write down what you are
going to measure, and what would count as success, **before you look at the
data**, and save it with a timestamp you cannot fake. Without it, testing five
things and reporting the one that worked looks identical on paper to correctly
predicting one thing.

**Procedure 20. Choose the definition of "deterioration" using performance data
only.**
```
python3 scripts/11_define_deterioration.py
```
This compares six candidate definitions using **only task-performance data** —
never the neural signal that will later be used to predict it. Six are compared
and **one is chosen and frozen**. Choosing after seeing which gives the best
result is exactly the error this prevents.
*Expect:* a change-point at trial day 758, agreed by three independent methods
and two different outcome variables, p = 0.0018.

**Procedure 21. Freeze the design.**
```
python3 scripts/12_freeze_design.py
python3 scripts/12_freeze_design.py --confirm
```
Run it **without** `--confirm` first: that previews what will be locked and
changes nothing. Then run it with `--confirm` to actually freeze.
This writes `research/FROZEN_DESIGN.json`, containing the participant, the
outcome measure, the analysis level, the statistical method, the success
criteria, the **git commit identifier at the moment of freezing**, and
**SHA-256 checksums of the input data files** — so nobody can later claim the
data was different.
*The two-step confirm is deliberate:* freezing must be an act you cannot perform
by accident.

**Procedure 22. Choose the neural observable, and record what was ruled out.**
```
python3 scripts/13_select_observable.py
```
*Expect:* a recorded finding that no observable in this data has measurable
"memory", which means **one half of the intended theory cannot be tested at
all** — established by measurement, and written down before the analysis rather
than discovered as an excuse afterwards.

---

### STAGE 4 — Run the preregistered analysis (Procedures 23–25)

**Procedure 23. Run it exactly as frozen.**
```
python3 scripts/14_run_ews_analysis.py
```
No settings are changed, and the analysis is not re-run with different options.
*Expect:* results written to `reports/EWS_RESULTS.md`, including the
prespecified limitation check.

**Procedure 24. Diagnose what the indicator was actually measuring.**
```
python3 scripts/15_diagnose_drift.py
```

**Procedure 25. Write up the phase, whatever it says.**
```
python3 scripts/16_phase12_synthesis.py
git add -A && git commit -m "Phase 1-2 complete"
```

---

### STAGE 5 — Build ground truth (Procedures 26–31)

*Rationale for this entire stage: in observational recordings nobody knows when
deterioration began, so "how early did the warning arrive?" cannot be answered.
The remedy is to construct degradations whose onset you choose and record in
advance.*

**Procedure 26. Draw the degradation schedule and lock it.**
```
python3 scripts/17_fault_injector.py plan
```
This draws, for every episode, which degradation type, how fast, how severe, and
**at exactly which moment it begins** — then writes all of it to a file together
with a checksum of the list and the git commit it was created at.
*Expect:* 1,073 episodes for one participant, 777 for the other.
**The script refuses to redraw these onsets without a recorded reason.** That
refusal is the point: ground truth that can be quietly adjusted is not ground
truth.
*Note:* the original data files are **never modified**. Only the plan is stored;
the change is applied in memory when an episode is scored.

**Procedure 27. Verify the plan is internally consistent.**
```
python3 scripts/17_fault_injector.py verify
```

**Procedure 28. Fit and freeze the grading model.**
```
python3 scripts/18_reference_decoder.py fit
python3 scripts/18_reference_decoder.py check
```
This fits a simple model that predicts intended movement direction from neural
activity, then **freezes it**. It exists only to grade episodes, never to detect
anything.
*Expect:* about 54.6° of error on held-out healthy data, against a **measured**
chance level of 90.7°.
*Why "measured":* chance is established by shuffling the pairing between neural
data and movements, not assumed to be 90°. When measured per day it ranges from
47.7° to 102.7°, so assuming would have been wrong.

**Procedure 29. Build the graders before building the thing being graded.**
First write `scripts/19_detectors.py`. **This one is not run directly** — it is a
*library*, a file of definitions that other scripts import and use. Running it on
its own does nothing. Then run the two that do execute:
```
python3 scripts/20_evaluation_harness.py run
python3 scripts/21_score_report.py
```
The harness imports the detector definitions, applies each one to every episode,
and writes the scores; the report turns those scores into a readable document.
**Run these, and commit them, before writing any monitor.** At this point the
only detectors that exist are three simple baselines this project did not invent,
so the grading system cannot have been shaped to flatter a monitor that does not
exist yet.
*The rule every detector obeys:* it sees **only** the neural feature stream —
never the model's output, never the task, never the performance score, never any
label saying a fault occurred — and is fitted only on healthy data.

**Procedure 30. Build the monitor.**
Write `scripts/22_decoder_guard.py`. **Also a library, also not run directly** —
the harness imports it exactly as it imports the baseline detectors, so the
monitor is graded by the same code, on the same terms, as detectors it is
competing against. Then re-run the harness (Procedure 29) so it is scored, and
draw the figures:
```
python3 scripts/23_benchmark_figures.py
```
The monitor has four named parts, each compared against healthy data, and it
reports the largest as its risk score **together with which part produced it** —
so the answer to "why is it warning?" is a sentence, not just a number.

**Procedure 31. Commit before looking at any score.**
```
git add -A && git commit -m "Monitor written before baseline scores were read"
```

---

### STAGE 6 — Run the benchmark (Procedures 32–38)

**Procedure 32. Score every configuration.**
```
python3 scripts/24_benchmark_matrix.py
```
*Expect:* 48 configurations — four detectors × four data transformations × two
baseline strategies on one participant, and a reduced grid on the other. Every
one is reported; none is dropped.

**Procedure 33. Test whether the monitor confuses "different" with "broken".**
```
python3 scripts/25_task_change_test.py
```
Uses real days on which the same person did something completely different
through the same electrodes with nothing wrong.

**Procedure 34–38. Measure the limits.**
```
python3 scripts/26_achievability.py
python3 scripts/27_decision_rules.py
python3 scripts/28_operating_point_bound.py
python3 scripts/29_aggregation_limit.py
python3 scripts/30_export_demo.py
```
In order: whether the information is present at all; whether a better
decision rule would help; what performance the stated requirement would demand;
whether averaging more measurements helps; and a viewable demonstration.

---

### STAGE 7 — Follow-up studies (Procedures 39–52)

**Every study in this stage is preregistered before it is run.** The pattern is
always: write the prediction and the success criterion to a file, commit it, then
run the script.

| # | Command | Question |
|---|---|---|
| 39 | Write `scripts/32_feature_families.py` (a library, not run directly), then `python3 scripts/33_run_feature_study.py --participant T11`, again with `--participant T5`, then `python3 scripts/34_feature_report.py` | Would different input measurements help? Four families named in advance, list closed, criterion frozen with a checksum |
| 40 | Write `scripts/35_general_guard.py` (a library), then `python3 scripts/36_run_combination_study.py --participant T11` (and `T5`), then `python3 scripts/37_combination_report.py` | Does the monitor's structure generalise to new inputs? |
| 41 | `python3 scripts/38_transfer_analysis.py` | Does it transfer between participants? |
| 42 | `python3 scripts/39_calibration_curve.py --participant T11` (and `T5`), then `40_calibration_report.py` | How much healthy data does commissioning need? |
| 43 | `python3 scripts/41_staleness_curve.py --participant T11` (and `T5`), `42_staleness_report.py`, `43_staleness_permutation.py` | Does the fit go stale over time? |
| 44 | `python3 scripts/44_day_variance.py --participant T11` (and `T5`) | How much does accuracy vary between sessions? |
| 45 | `python3 scripts/45_pooling_loss.py --participant T11` (and `T5`) | Does combining sessions dilute the signal? |
| 46 | `python3 scripts/46_day_predictors.py`, then `47_p5_mediation.py` | What predicts a good session? Five predictors, directions committed in advance, corrected for testing five things at once |
| 47 | `python3 scripts/48_label_free_signals.py` | Could the monitor know when not to trust itself? |
| 48 | `python3 scripts/49_day_effect_across_detectors.py --participant T11` (and `T5`) | Is the session effect specific to this monitor or shared? |
| 49 | `python3 scripts/50_ceiling_challenge.py --participant T11` (and `T5`) | An attempt to break this project's own headline finding |
| 50 | `python3 scripts/51_unambiguous_episodes.py --participant T11` (and `T5`), `52_per_day_chance.py --participant T11` | Are the labels themselves weaker on bad sessions? |
| 51 | `python3 scripts/53_severity_ladder.py --participant T11` (and `T5`) | Does "more severe" always mean more damage? |
| 52 | `python3 scripts/54_window_overlap.py --participant T11` (and `T5`) | How much does the overlap between measurement windows bias the results? |

---

### STAGE 8 — Audit the project against itself (Procedures 53–60)

*Every check here was written after the work it checks, and several found real
errors. Four of them were themselves buggy before they were useful, which is why
each is tested against a defect already known to exist.*

**Procedure 53. Check every headline number against the data files.**
```
python3 scripts/31_verify_claims.py
```
Recomputes every figure quoted anywhere in the project from the stored data.
*Expect:* `All 97 headline claims match the data files.`

**Procedure 54. Check the project can actually be reproduced.**
```
python3 scripts/55_reproducibility_audit.py
```
Checks four things: every library used is declared; every intermediate file read
by a script is written by some script; no script reads a file produced later in
the sequence; and every script named in a document exists.

**Procedure 55. Build the register of every claim and its status.**
```
python3 scripts/56_claims_register.py
```
*Expect:* claims sorted into ESTABLISHED, LIMITATION, **WITHDRAWN**,
UNANSWERABLE and EXPLORATORY. Withdrawn claims stay in the repository, marked
"do not quote", rather than being deleted.

**Procedure 56. Check for known classes of statistical mistake.**
```
python3 scripts/61_statistical_hygiene.py
```
Scans every script for three error patterns this project actually made.

**Procedure 57. Check the written log accounts for every day of work.**
```
python3 scripts/65_log_coverage.py
```
Compares dates in the research log against dates in the project history. A date
with work but no entry must be explained — **never by re-dating an entry**, which
would falsify the record.

**Procedures 58–60. The remaining analyses.**
```
python3 scripts/57_attribution_accuracy.py
python3 scripts/58_mode_separability.py --participant T11
python3 scripts/59_per_mode_detection.py
python3 scripts/60_unit_of_analysis.py
python3 scripts/62_permutation_invariant.py --participant T11
python3 scripts/63_invariant_detector.py --participant T11
python3 scripts/64_invariant_attribution.py --participant T11
python3 scripts/66_window_spacing.py
```

**Procedure 60b. Always run the checks before saving, never after.**
```
python3 scripts/31_verify_claims.py && \
python3 scripts/55_reproducibility_audit.py && \
python3 scripts/56_claims_register.py && \
python3 scripts/61_statistical_hygiene.py && \
python3 scripts/65_log_coverage.py
git add -A && git commit -m "..."
```
Running them afterwards leaves regenerated files unsaved and disagreeing with the
code that made them.

---

### STAGE 9 — Build the physical instrument (Procedures 61–75)

*Full detail, including wiring and safety, is in `research/RIG_PROCEDURE.md`.
Nothing here is built until Procedure 61 is complete.*

**Procedure 61. Preregister the physical experiment, and freeze it.**
Complete `research/RIG_PREREGISTRATION.md` — predictions with numeric thresholds,
the pass/fail gate, sample sizes, stopping rules, and what would prove each
prediction wrong. Then:
```
git add research/RIG_PREREGISTRATION.md
git commit -m "Freeze the rig preregistration before building anything"
git rev-parse HEAD
```
Paste the identifier that last command prints back into the file, and commit
again. **Construction begins only after this exists.**

**Procedure 62. Assemble the parts.** A Raspberry Pi 4 single-board computer, a
camera module, a display, a light-excluding enclosure with a matte black interior,
a camera mount, and black tape. Roughly $115.

**Procedure 63. Install the operating system.** Use *Raspberry Pi Imager*
(raspberrypi.com/software) to write *Raspberry Pi OS 64-bit* to a memory card.
In its settings, set a hostname, enable **SSH** (which lets you control the
computer over the network so the enclosure can stay closed), and enter Wi-Fi
details.

**Procedure 64. Connect to it and install the software.**
```
ssh yourusername@rig.local
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 python3-numpy python3-pandas python3-pygame git
```

**Procedure 65. Attach the camera — with the power off — and test it.**
Lift the black tab on the connector, insert the ribbon with the blue side facing
the ethernet port, press the tab down. Then power on and run:
```
rpicam-hello --timeout 5000
```
*If this fails, stop and fix it.* Everything downstream depends on it.

**Procedure 66. Measure the frame rate you can actually sustain.**
```
rpicam-vid --width 480 --height 320 --framerate 50 --timeout 10000 --codec yuv420 -o /dev/null --info-text "%fps"
```
**Write down the number you actually get** and use it everywhere.

**Procedure 67. Build the enclosure.** Line the inside — including the lid — with
matte black paper or paint. Cut one hole for cables and one panel for the
display. Tape every remaining gap.
*Why:* ambient light varies with time of day and weather, and over a six-week
recording it would be indistinguishable from the degradation being measured.

**Procedure 68. Mount the display and camera rigidly.** The display faces into
the enclosure; the camera faces it, square and level, positioned so the pattern
fills about 80% of the frame width. **The dark margin is deliberate** — those
regions see no signal and provide a free background-noise reference.

**Procedure 69. Strain-relieve every cable.** Tape each cable to the wall about
5 cm from its connector. A cable that half-unseats itself mid-recording produces
an unlogged fault at an unknown time — the one failure this design cannot
tolerate.

**Procedure 70. Write the stimulus program.** The display shows a grid of patches.
Each patch is assigned one fixed preferred direction, drawn once at random. On
every frame, given the current heading, each patch's brightness is set to
`0.5 × (1 + cos(heading − preferred direction))`.
*Why this and not a moving dot:* a moving dot would make each image region
respond to *where* the dot is, which is position information. Real neural channels
respond to *which direction* is intended. This construction makes each patch
behave like a direction-tuned channel, so the problem is the same in form.
The program writes the true heading for every frame to a log file, so the correct
answer is recorded rather than reconstructed.

**Procedure 71. Write the capture program.** It reads frames, divides each into a
fixed grid of regions, and averages the brightness of each region. **Each region
average is one channel** — exactly as each electrode's activity count is one
channel in the archived data.
**Fix the exposure and white balance.** Automatic settings are adaptive
compensators; leave them on and the camera will quietly cancel the very
degradations being measured.

**Procedure 72. Measure the delay between display and camera.** Show a single
black frame every hundred frames, record, find where total brightness dips, and
compare against the logged time. Subtract that delay from every recording
afterwards. **Re-measure if the display, exposure or frame rate changes.**
*Why:* an uncorrected delay rotates every channel's apparent tuning and would
look exactly like a mediocre model.

**Procedure 73. Confirm the file format works before recording anything real.**
```
python3 scripts/67_rig_format_check.py
```
This builds a synthetic test block, loads it with the **unmodified** archived
loader, and confirms the required fields are present. *Expect:* `PASS`.
**The test data it builds is not data** and no result may cite it; it exists only
to prove the file format is right.

**Procedure 74. Record the healthy baseline and fit the model.**
```
for i in $(seq 1 20); do
  python3 rig/capture.py 15000 data/raw_rig/session_001/block_$i.npy
done
python3 scripts/18_reference_decoder.py fit --participant RIG
```

**Procedure 75. Apply the pass/fail gate — and stop if it fails.**
The instrument's *healthy* behaviour must match the archived data's healthy
behaviour within a stated range before any degradation is introduced.
**Deliberately excluded from this gate** are the quantities the experiment is
testing. Requiring the instrument to match those would guarantee the result and
make the study circular.
**If the gate cannot be passed, the study stops here and reports that** — a real
finding about the limits of the comparison, and far better than introducing
faults into a system never shown to be comparable.

---

### STAGE 10 — Run the physical experiment (Procedures 76–80)

**Procedure 76. Lock the degradation schedule, before recording.**
```
python3 scripts/17_fault_injector.py plan --participant RIG
git add -A && git commit -m "Lock the rig injection plan before any fault is recorded"
```

**Procedure 77. Record the designed degradations**, following the plan exactly,
and **look at no result until every session in it is recorded.**

**Procedure 78. Record the undesigned degradations.** Physical interventions
whose *timing* you control and log, but whose *signature* emerges from physics
rather than from anything you designed: loosening a connector, inserting an
optical filter, warming a component, introducing interference, contaminating the
lens, rotating the camera. **Log each intervention at the moment you perform it.**
Designed and undesigned results are reported in **separate tables**, because
whether findings generalise from one to the other is a claim to be tested.

**Procedure 79. Run the parallel long-duration arm.** One identical recording per
day for six to ten weeks with **nothing introduced**, logging temperature and
humidity. **Change nothing** — and if you do touch the instrument, log what and
when. An unlogged intervention is indistinguishable from a finding.

**Procedure 80. Analyse with the same code, unchanged.**
```
python3 scripts/20_evaluation_harness.py run --participant RIG
python3 scripts/21_score_report.py --participant RIG
python3 scripts/24_benchmark_matrix.py
python3 scripts/29_aggregation_limit.py
python3 scripts/66_window_spacing.py
```
**No analysis code is written or modified after seeing the new data.** That is the
strongest available defence against the charge that the result was shaped to fit:
the analysis was written, frozen, and checked by 97 automated tests before the
instrument existed.

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
