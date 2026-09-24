# Replication guide — every computational step, in order

**What this is.** The command-by-command walkthrough of the computational half of
this project, written so somebody who has never seen it, and has never used a
command line, can redo every step and get the same numbers.

**Why it lives here and not in the research plan.** It used to be Section C of
`RESEARCH_PLAN_2026-09-15.md`. The ISEF form asks Section C for the experimental
design and the methods of data collection, at the level a reviewer reads, not a
645-line tutorial. Moving it out kept the plan readable without losing a single
step. The plan's Section C now describes the design and points here.

**Voice.** This is written in the first person, unlike the research plan. That is
deliberate: it is a working document for whoever is at the keyboard, and the
research plan is the formal one.

**Companion documents.**
- `research/EXPERIMENTAL_PROCEDURES.md` — the same material organised by phase,
  plus the full detail for the physical rig, which is the part that still has to
  be built.
- `research/RESEARCH_PLAN_2026-09-15.md` — the formal plan, third person.

---

## The steps

I wrote this so somebody who has never seen my project, and has never used a
command line, can redo every step. The procedures are numbered so they can be
referred to. Each one gives the command to type, what it does, and what you
should see if it worked.

**Some words I use, defined once.** A **terminal** is a window where you type
commands instead of clicking. A **command** is a line of text you type and then
press Enter. A **script** is a saved file of instructions the computer runs. A
**repository**, or repo, is the folder with all the project files and the full
history of changes to them. **Git** is the program that keeps that history.
**Python** is the language everything here is written in.

Text shown like `this` is typed exactly as written. `~` means your home folder.

**One thing that will waste your time if I do not say it now.** Some files in
`scripts/` are programs you run. Others are libraries, meaning files of
definitions that other programs load and use. A library does nothing if you run
it by itself. Four of mine are libraries: `19_detectors.py`,
`22_decoder_guard.py`, `32_feature_families.py` and `35_general_guard.py`. You
write those, you do not run them, and I flag each one where it comes up.

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
I used 3.11.15 for every result in this project. Older versions can behave a
little differently in ways that are easy to miss.

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
git checkout claude/isef-research-pipeline-9zt4uq
```
`cd ~` moves you to your home folder. `git clone` copies the whole project,
including its history. `cd bci-ews-research` moves you into it. `git checkout` picks the branch the work is on.
**The `git checkout` line is not optional.** A plain clone lands on `main`, which as of 24 September 2026 is the repository as it stood on 16 August — four files, no `physical/`. Every command after this one would fail. See `physical/docs/12_RUNBOOK.md` step 0.1.

*Expect:* a message ending "done." and a new folder.

**Procedure 5. Install the libraries the code needs.**
```
pip install -r requirements.txt
```
A library is pre-written code my project uses. This installs six of them:
`numpy` for fast number arrays, `pandas` for tables with named columns, `scipy`
for the statistics, `h5py` to read MATLAB files, `matplotlib` for graphs, and
`requests` to download over the internet.
You should see "Successfully installed" or "Requirement already satisfied".
I keep them in a file instead of typing the names each time so everyone runs the
same versions. A result that changes because a library quietly updated itself is
a common way research stops being reproducible.

**Procedure 6. Confirm you are in the right place.**
```
ls
```
`ls` lists files. *Expect to see:* `data`, `reports`, `research`, `scripts`,
`tools`, `README.md`, `requirements.txt`.

---

### STAGE 1 — Obtain the archived dataset (Procedures 7–12)

**Procedure 7. Know what you are downloading and why it is allowed.**
The dataset is MINDFUL (Pun et al.), on Dryad under DOI
`10.5061/dryad.n2z34tn5s`. It is released under CC0, which puts it in the public
domain with no restrictions on reuse. Other researchers collected it years ago
under their own institutional approvals, and it is de-identified. I recruit
nobody.

**Procedure 8. Obtain Dryad API credentials.**
Dryad's public download page is protected by an anti-bot check that hands any
script a web page instead of data. I did not get around that protection. I used
the route Dryad supports instead: make a Dryad API account, which you log into
with an ORCID iD (free at orcid.org), and it gives you API credentials.

**Procedure 9. Supply the credentials without ever writing them to a file.**
```
export DRYAD_CLIENT_ID="your-id-here"
export DRYAD_CLIENT_SECRET="your-secret-here"
```
`export` puts a value in the terminal's memory for that session only. It never
gets saved to a file and never goes into the repository. Delete the API account
when you are done with it.

**Procedure 10. Download, with automatic integrity checking.**
```
python3 scripts/01_download_dataset.py
```
This asks Dryad which files are in the deposit, downloads each one, and computes
a SHA-256 checksum for it. A checksum is a long fingerprint that changes
completely if even one byte of the file is different. It then compares that
against the checksum Dryad publishes.
You should get two files: `MINDFUL_Data.zip` at 411,951,588 bytes and `README.md`
at 3,348 bytes, both reported as verified. It is about 400 MB, so give it a few
minutes.
If a checksum does not match, stop there. The download is corrupt and nothing you
build on it can be trusted.

**Procedure 11. Unpack and inspect the archive without opening it by hand.**
```
python3 scripts/02_inspect_dataset.py --extract
```
You should see 166 files extracted, 825,449,877 bytes, and a summary written to
`reports/inventory.json`.
I do this with a script instead of double-clicking the zip so the inspection gets
recorded. That way what was in the archive on the day I opened it is written down
in the repository instead of being something I remember.

**Procedure 12. Convert the data into tables, and look at it.**
```
python3 scripts/03_load_dataset.py --save
python3 scripts/04_explore_dataset.py
```
The first walks the folder tree of MATLAB `.mat` files and produces two flat
tables, one row per trial and one row per recording block, plus the neural
arrays.
The second produces a descriptive report.
You should get 54 blocks, 3,301 trials, and a report at
`reports/DATASET_EXPLORATION.md`.
There is a trap here that the loader handles for you. MATLAB numbers the first
item in a list 1, and Python numbers it 0. Get that wrong and every trial shifts
by one time step, which quietly ruins everything after it. My loader converts and
keeps both versions so the conversion can be checked.
The loader also does no smoothing, no z-scoring, and no outlier removal, on
purpose. Those are not loading. Each one is a decision that changes what the
results mean, so I make them later where they are visible.

---

### STAGE 2 — Prove the tools work before trusting them (Procedures 13–18)

This whole stage is here for one reason. A detector that has never been tried on
a system where you already know the answer cannot be trusted on a system where
you do not.

**Procedure 13. Confirm the published decoder really was fixed.**
```
python3 scripts/05_check_decoder_stability.py
```
My analysis assumes the original researchers' decoder was not being retrained
during the recordings. This checks that against the data instead of taking the
paper's word for it.

**Procedure 14. Test the detector on systems whose answer is already known.**
```
python3 scripts/06_ews_controls.py
```
This builds two fake systems. One really does approach a tipping point, so the
detector should fire on it. The other only drifts steadily, so the detector
should stay quiet. You want it firing on the first and silent on the second. If
it gets either one wrong, the detector is broken and nothing it says about real
data would mean anything.

**Procedure 15. Find out how much data the detector needs.**
```
python3 scripts/07_ews_power_sweep.py --windows 800 1600 3000 5000 --sigmas 400 1000 2000
python3 scripts/08_record_length_check.py
```
Those `--windows` and `--sigmas` values are not the script's defaults, and the
committed `data/processed/ews_power_sweep.csv` was made with them. Running the
command bare uses the defaults (`400 800 1600 3000` and `100 400 1000`) and
produces a different grid, so the committed file would not come back. The six
settings the two grids share agree exactly, so nothing here is in doubt except
which grid to keep. **`[[RESEARCHER — decide which grid the project keeps.]]`**
The committed one reaches a longer window (5000) and a heavier smoothing (2000);
the defaults reach a shorter window (400) and a lighter one (100).
The first one measures how reliably the detector finds a real effect at
different recording lengths. The second checks whether the actual recordings are
long enough. You should see detection go from about 0.25 up to 1.00 as the
records get longer.

**Procedure 16. Reproduce somebody else's published result.**
```
python3 scripts/09_reproduce_mindful.py
```
This recalculates a figure from the original paper using my code.
You should get r = 0.985, which matches their published 0.985.
This is the check I trust most in this stage. It is the only one that compares my
pipeline against an answer someone else produced independently. If it passes, I
am reading the data correctly.

**Procedure 17. Work out how large an effect could even be detected.**
```
python3 scripts/10_design_power_analysis.py
```

**Procedure 18. Record everything so far.**
```
git add -A
git commit -m "Stage 2 complete: tools validated"
```
`git add -A` marks all the changes to be saved and `git commit` saves them with a
note. I commit at this point rather than later because the record has to be built
as you go. If you reconstruct it afterward it stops being evidence.

---

### STAGE 3 — Preregister the analysis (Procedures 19–22)

This is the stage that makes everything after it worth believing.

**Procedure 19. What preregistration is.** You write down what you are going to
measure and what would count as success before you look at the data, then save it
with a timestamp you cannot fake. Without it, testing five things and reporting
the one that worked looks exactly the same on paper as predicting one thing
correctly.

**Procedure 20. Choose the definition of "deterioration" using performance data
only.**
```
python3 scripts/11_define_deterioration.py
```
This compares six possible definitions using only task performance data. It
never touches the neural signal that will later be used to predict it. Six get
compared, one gets picked, and then it is locked. Picking after you have seen
which one gives the nicest result is the mistake this is meant to stop.
You should get a change point at trial day 758, agreed on by three separate
methods and two different outcome measures, p = 0.0018.

**Procedure 21. Freeze the design.**
```
python3 scripts/12_freeze_design.py
python3 scripts/12_freeze_design.py --confirm
```
Run it without `--confirm` first. That shows you what is about to be locked and
changes nothing. Then run it again with `--confirm` to actually freeze it.
It writes `research/FROZEN_DESIGN.json`, which holds the participant, the outcome
measure, the analysis level, the statistical method, the success criteria, the
git commit ID at the moment of freezing, and SHA-256 checksums of the input data
files so nobody can say later that the data was different.
I made it a two-step confirm on purpose. Freezing should not be something you can
do by accident.

**Procedure 22. Choose the neural observable, and record what was ruled out.**
```
python3 scripts/13_select_observable.py
```
What comes out is that nothing measurable in this data has any "memory," which
means half the theory I wanted to test cannot be tested here at all. I measured
that and wrote it down before running the analysis, rather than finding it later
and using it as an excuse.

---

### STAGE 4 — Run the preregistered analysis (Procedures 23–25)

**Procedure 23. Run it exactly as frozen.**
```
python3 scripts/14_run_ews_analysis.py
```
I do not change any settings and I do not re-run it with different options.
Results go to `reports/EWS_RESULTS.md`, including the limitation check I
specified in advance.

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

Here is why this whole stage exists. In recordings that were only observed,
nobody knows when the deterioration started, so "how early did the warning
arrive" has no answer. The fix is to build degradations where I pick the start
time and write it down first.

**Procedure 26. Draw the degradation schedule and lock it.**
```
python3 scripts/17_fault_injector.py plan
```
For every episode this picks the degradation type, how fast it comes on, how bad
it gets, and the exact moment it starts. Then it writes all of that to a file
along with a checksum of the list and the git commit it was made at.
You should get 1,073 episodes for one participant and 777 for the other.
The script will not redraw those start times unless you give it a reason it can
record. That refusal is the whole point. Ground truth you can quietly adjust is
not ground truth.
The original data files never get modified. Only the plan is saved, and the
change gets applied in memory when an episode is scored.

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
activity, then freezes it. Its only job is grading episodes. It never detects
anything.
You should get about 54.6 degrees of error on held-out healthy data, against a
measured chance level of 90.7 degrees.
I say measured because I get chance by shuffling which neural data goes with
which movement, instead of assuming it is 90 degrees. Measured per day it runs
from 47.7 to 102.7 degrees, so assuming would have been wrong.

**Procedure 29. Build the graders before building the thing being graded.**
First write `scripts/19_detectors.py`. You do not run this one. It is a library,
meaning a file of definitions that other scripts load and use, and running it by
itself does nothing. Then run the two that do execute:
```
python3 scripts/20_evaluation_harness.py run
python3 scripts/21_score_report.py
```
The harness imports the detector definitions, applies each one to every episode,
and writes the scores; the report turns those scores into a readable document.
Run these and commit them before you write any monitor. At this point the only
detectors that exist are three simple baselines I did not invent, so I cannot
have shaped the grading system to flatter a monitor that does not exist yet.
Every detector follows the same rule. It sees only the neural feature stream. Not
the model's output, not the task, not the performance score, and not any label
saying a fault happened. It is fitted on healthy data only.

**Procedure 30. Build the monitor.**
Write `scripts/22_decoder_guard.py`. This is also a library, so again you do not
run it. The harness loads it the same way it loads the baseline detectors, which
means my monitor gets graded by the same code, on the same terms, as the
detectors it is competing against. Then re-run the harness from Procedure 29 so
it gets scored, and draw the figures:
```
python3 scripts/23_benchmark_figures.py
```
The monitor has four named parts. Each one is compared against healthy data, and
it reports the largest as its risk score along with which part produced it. That
way the answer to "why is it warning" is a sentence and not just a number.

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
You get 48 configurations: four detectors by four data transformations by two
baseline strategies on one participant, and a smaller grid on the other. I report
all of them. I do not drop any.

**Procedure 33. Test whether the monitor confuses "different" with "broken".**
```
python3 scripts/25_task_change_test.py
```
This uses real days where the same person did something totally different
through the same electrodes with nothing wrong with the hardware.

**Procedure 34–38. Measure the limits.**
```
python3 scripts/26_achievability.py
python3 scripts/27_decision_rules.py
python3 scripts/28_operating_point_bound.py
python3 scripts/29_aggregation_limit.py
python3 scripts/30_export_demo.py
```
In order, these ask: is the information there at all, would a better decision
rule help, what accuracy would the stated requirement actually demand, does
averaging more measurements help, and finally a demo you can look at.

---

### STAGE 7 — Follow-up studies (Procedures 39–52)

Every study in this stage gets preregistered before I run it. The pattern is the
same each time: write the prediction and the success criterion into a file,
commit it, then run the script.

| # | Command | Question |
|---|---|---|
| 39 | Write `scripts/32_feature_families.py` (a library, not run directly), then `python3 scripts/33_run_feature_study.py --participant T11`, again with `--participant T5`, then `python3 scripts/34_feature_report.py` | Would different input measurements help? Four families named in advance, list closed, criterion frozen with a checksum |
| 40 | Write `scripts/35_general_guard.py` (a library), then `python3 scripts/36_run_combination_study.py --participant T11` (and `T5`), then `python3 scripts/37_combination_report.py` | Does the monitor's structure generalize to new inputs? |
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

Every check here was written after the work it checks, and several of them found
real mistakes in my own work. Four of the checks were themselves buggy before
they were any use, which is why I now test each new one against a problem I
already know is there.

**Procedure 53. Check every headline number against the data files.**
```
python3 scripts/31_verify_claims.py
```
This recalculates every number quoted anywhere in my project straight from the
stored data files. You should see `All 97 headline claims match the data
files.`

**Procedure 54. Check the project can actually be reproduced.**
```
python3 scripts/55_reproducibility_audit.py
```
This checks four things. Every library I use is declared. Every intermediate
file a script reads is written by some script. No script reads a file that gets
made later in the order. And every script named in a document actually exists.

**Procedure 55. Build the register of every claim and its status.**
```
python3 scripts/56_claims_register.py
```
This sorts every claim into ESTABLISHED, LIMITATION, WITHDRAWN, UNANSWERABLE or
EXPLORATORY. Claims I withdrew stay in the repository marked "do not quote"
instead of being deleted.

**Procedure 56. Check for known classes of statistical mistake.**
```
python3 scripts/61_statistical_hygiene.py
```
Scans every script for three error patterns this project actually made.

**Procedure 57. Check the written log accounts for every day of work.**
```
python3 scripts/65_log_coverage.py
```
This compares the dates in my research log against the dates in the project
history. If there is a day with work on it and no log entry, I have to explain
it. What I am not allowed to do is re-date an existing entry to make it line up,
because that would falsify the record.

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
If you run them afterward you end up with regenerated files that are unsaved and
no longer agree with the code that made them. I have made this mistake once
already.

---

### STAGE 9 — Build the physical instrument (Procedures 61–75)

> **SUPERSEDED 20 September 2026.** The physical experiment was redesigned. Do
> not follow the procedures below; follow **`physical/README.md`** and
> `physical/docs/04_BUILD.md` through `07_ANALYSIS.md` instead.
>
> The order there is the same in spirit — decide what the session will be before
> recording it, build, check, then record — but the code is in `physical/code/`
> rather than `rig/`, and the experiments are P-1 to P-6 rather than Procedures
> 61–75. `research/RIG_PREREGISTRATION.md` §14 says what carried over.
>
> Procedures 61–75 are kept below unchanged, as the record of what the physical
> stage was going to be.

The full detail, including wiring and safety, was in
`research/RIG_PROCEDURE.md`. Nothing got built until Procedure 61 was done.

**Procedure 61. Preregister the physical experiment, and freeze it.**
Fill in `research/RIG_PREREGISTRATION.md`: predictions with actual numbers in
them, the pass/fail gate, how many sessions I will record, when I stop, and what
would show each prediction was wrong. Then:
```
git add research/RIG_PREREGISTRATION.md
git commit -m "Freeze the rig preregistration before building anything"
git rev-parse HEAD
```
Paste the ID that last command prints back into the file and commit again. I do
not start building until this exists.

**Procedure 62. Assemble the parts.** A Raspberry Pi 4 single-board computer, a
camera module, a display, a light-excluding enclosure with a matte black interior,
a camera mount, and black tape. Roughly $115.

**Procedure 63. Install the operating system.** Use *Raspberry Pi Imager*
(raspberrypi.com/software) to write *Raspberry Pi OS 64-bit* to a memory card.
In its settings, set a hostname, turn on SSH, and put in your Wi-Fi details. SSH
is what lets you control the computer over the network, so the box can stay
closed while it runs.

**Procedure 64. Connect to it and install the software.**
```
ssh yourusername@rig.local
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 python3-numpy python3-pandas python3-pygame git
```

**Procedure 65. Attach the camera, with the power off, and test it.**
With the power off, lift the black tab on the connector, slide the ribbon in
with the blue side facing the ethernet port, and press the tab back down. Then
power on and run:
```
rpicam-hello --timeout 5000
```
If this fails, stop and fix it before doing anything else. Everything after it
depends on the camera working.

**Procedure 66. Measure the frame rate you can actually sustain.**
```
rpicam-vid --width 480 --height 320 --framerate 50 --timeout 10000 --codec yuv420 -o /dev/null --info-text "%fps"
```
Write down the number you actually get, not the one you asked for, and use that
everywhere.

**Procedure 67. Build the enclosure.** Line the inside with matte black paper or
paint, including the lid. Cut one hole for cables and one panel for the
display. Tape every remaining gap.
Room light changes with the time of day and the weather. Over a six-week
recording that would look exactly like the degradation I am trying to measure.

**Procedure 68. Mount the display and camera rigidly.** The display faces into the box and the camera faces it, square and level, far
enough back that the pattern fills about 80% of the frame width. I leave the dark
margin on purpose. Those regions see no signal, so they give me a free reference
for background noise.

**Procedure 69. Strain-relieve every cable.** Tape each cable to the wall about 5 cm from its connector. If a cable half
works itself loose partway through a recording, I get a fault I did not log at a
time I do not know. That is the one thing this design cannot survive.

**Procedure 70. Write the stimulus program.** The display shows a grid of patches.
Each patch is assigned one fixed preferred direction, drawn once at random. On
every frame, given the current heading, each patch's brightness is set to
`0.5 × (1 + cos(heading − preferred direction))`.
I use this instead of a moving dot for a specific reason. A moving dot would
make each region respond to where the dot is, which is position information. Real
neural channels respond to which direction the person means to move. Doing it
this way makes each patch behave like a direction-tuned channel, so the problem I
am solving is the same shape as the real one.
The program writes the true heading for every frame to a log file, so the correct
answer is recorded instead of reconstructed later.

**Procedure 71. Write the capture program.** It reads frames, cuts each one into a fixed grid of regions, and averages the
brightness in each region. Each region average is one channel, the same way each
electrode's activity count is one channel in the archived data.
Lock the exposure and white balance. The automatic settings are compensators.
Leave them on and the camera will quietly cancel out the exact degradations I am
trying to measure.

**Procedure 72. Measure the delay between display and camera.** Show one black frame every hundred frames, record it, find where the total
brightness dips, and compare that against the logged time. Subtract that delay
from every recording after this. Measure it again if you change the display, the
exposure or the frame rate.
If you leave a delay uncorrected it rotates every channel's apparent tuning, and
the result looks exactly like a mediocre model rather than a timing bug.

**Procedure 73. Confirm the file format works before recording anything real.**
```
python3 scripts/67_rig_format_check.py
```
This builds a fake test block, loads it with the unmodified archived loader, and
checks the required fields are there. You should see `PASS`.
The test data it makes is not data. No result of mine cites it. It exists only to
prove the file format is right before I record anything real.

**Procedure 74. Record the healthy baseline and fit the model.**
```
for i in $(seq 1 20); do
  python3 rig/run_block.py --session 1 --blocknum $i
done
python3 scripts/18_reference_decoder.py fit --participant RIG --raw-root data/raw_rig
```

**Procedure 75. Apply the pass/fail gate, and stop if it fails.**
Before I introduce any degradation, the rig's healthy behavior has to match the
archived data's healthy behavior within a range I state in advance.
I leave the quantities the experiment is testing out of this gate on purpose. If
I made the rig match those too, I would be guaranteeing my own result and the
whole study would be circular.
If the gate cannot be passed, I stop here and report that. That is a real finding
about where the comparison breaks down, and it beats introducing faults into a
system I never showed was comparable in the first place.

---

### STAGE 10 — Run the physical experiment (Procedures 76–80)

**Procedure 76. Lock the degradation schedule, before recording.**
```
python3 scripts/17_fault_injector.py plan --participant RIG --raw-root data/raw_rig
git add -A && git commit -m "Lock the rig injection plan before any fault is recorded"
```

**Procedure 77. Record the designed degradations.** Follow the plan exactly and
do not look at a single result until every session in it is recorded.

**Procedure 78. Record the undesigned degradations.** These are physical things I do where I control and log the timing, but where
what it looks like in the data comes from physics rather than from anything I
designed: loosening a connector, sliding in an optical filter, warming a
component, adding interference, smudging the lens, rotating the camera. Log each
one the moment you do it, not afterward.
I report designed and undesigned results in separate tables. Whether the findings
carry over from one to the other is a claim that has to be tested, not
assumed.

**Procedure 79. Run the parallel long-duration arm.** One identical recording a day for six to ten weeks with nothing introduced,
logging temperature and humidity alongside. Change nothing. If you do touch the
rig, write down what you did and when. An intervention you did not log is
impossible to tell apart from a finding.

**Procedure 80. Analyse with the same code, unchanged.**
```
python3 scripts/20_evaluation_harness.py run --participant RIG --raw-root data/raw_rig
python3 scripts/21_score_report.py --participant RIG
python3 scripts/24_benchmark_matrix.py
python3 scripts/29_aggregation_limit.py
python3 scripts/66_window_spacing.py
```
I do not write or change any analysis code after seeing the new data. That is my
best answer to anyone who says the result was shaped to fit: the analysis was
written, frozen and checked by 97 automated tests before the rig existed.

---

