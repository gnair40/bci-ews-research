# The runbook — every step, in order, from parts to results

**This is the "just tell me what to do" document.** Every other document
explains *why*. This one is the order, the command, and what success looks
like. Tick the boxes as you go.

Where a step needs more explanation than fits here, it names the document.

> **The one rule that overrides everything:** if a step's check fails, **stop
> and fix it before moving on.** Every check in this list catches a failure
> that otherwise produces recordings that look completely normal and analyse
> into nonsense. Skipping one does not save time; it moves the cost to the end,
> where it is much larger.

---

## Stage 0 — before you spend any money *(20 minutes, laptop)*

- [ ] **0.1** Get the project onto your computer.
  ```bash
  git clone https://github.com/gnair40/bci-ews-research.git
  cd bci-ews-research
  pip install -r requirements.txt
  ```
- [ ] **0.2** Check the software works.
  ```bash
  python3 physical/code/monitor.py --selftest
  ```
  **Success:** `PASS — the pipeline is wired up correctly`.
- [ ] **0.3** Check this computer can draw the pattern fast enough.
  ```bash
  python3 physical/code/stimulus.py --benchmark 300
  ```
  **Success:** `PASS`. If it fails here, it will certainly fail on the Pi —
  read `10_TROUBLESHOOTING.md`.
- [ ] **0.4** Rehearse the whole analysis on fake recordings.
  ```bash
  python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8 --undesigned 4 --orphans 2
  python3 physical/code/make_session_table.py --raw physical/data/dryrun/raw --tag _dryrun
  python3 physical/code/analyze_falsealarm.py --tag _dryrun
  python3 physical/code/analyze_leadtime.py --tag _dryrun
  python3 physical/code/analyze_decision_rate.py --tag _dryrun
  python3 physical/code/figures.py all --tag _dryrun
  ```
  **Success:** **six** figures in `physical/data/figures/`, the last of them
  `decision_rate_dryrun.png`. Look at them.
  **None of those numbers are results** — the fakes come from a formula.

  *(Until 24 September 2026 this list omitted `analyze_decision_rate.py`, so
  following it exactly produced five figures while this line promised six.
  P-6 is co-primary with P-2, so the missing step was not just a missing
  picture — the rehearsal skipped half of what it is meant to rehearse.)*
- [ ] **0.5** Delete the fakes.
  ```bash
  rm -rf physical/data/dryrun
  ```
- [ ] **0.6** Confirm the repository still agrees with itself.
  ```bash
  python3 tools/check_all.py
  ```
  **Success:** `PASS — every gate is green` (about two minutes). This runs all
  eleven checks, including `79_preregistration_freeze.py`, which confirms the
  frozen preregistration has not drifted since its timestamp. Run it again
  before every commit you make from here on.

**If Stage 0 passes, the money is safe to spend.**

---

## Stage 1 — buy the parts *(10 minutes, then wait)*

- [ ] **1.1** Order the four critical items (~$110): Raspberry Pi 4 4GB,
      Camera Module 3, 64GB A2 microSD, official USB-C power supply.
- [ ] **1.2** Order or gather the rest: box, matte black paper, tape, tripod,
      screen, ND filter, USB drive. Full list with search terms in
      `11_SHOPPING_LIST.md`.

**While you wait:** read `00_WHY_THIS_PHASE_EXISTS.md` and
`01_RESEARCH_DESIGN.md`. They are the argument the whole phase rests on, and
understanding them is what lets you answer a judge's questions.

---

## Stage 2 — set up the Pi *(1–2 hours)*

Full detail: `04_BUILD.md` Part 2.

- [ ] **2.1** Write Raspberry Pi OS to the card with Raspberry Pi Imager.
      **In the settings, enable SSH and enter your wifi** before writing.
- [ ] **2.2** Boot the Pi, connect from your laptop: `ssh yourname@bci-rig.local`
- [ ] **2.3** Install the software.
  ```bash
  sudo apt update
  sudo apt install -y python3-picamera2 python3-pygame python3-numpy python3-scipy python3-pandas git
  ```
- [ ] **2.4** Get the project onto the Pi and check it.
  ```bash
  git clone https://github.com/gnair40/bci-ews-research.git
  cd bci-ews-research
  python3 physical/code/monitor.py --selftest
  ```
- [ ] **2.5** **Check the Pi can draw at 50 fps.** This is the one that can
      change your plan.
  ```bash
  python3 physical/code/stimulus.py --benchmark 300
  ```
  **If it fails**, it prints three options and what each costs. Decide now,
  before building — two of the three change the apparatus.
- [ ] **2.6** Power off. Attach the camera ribbon: **silver contacts toward the
      HDMI ports.** Power on and check:
  ```bash
  rpicam-hello --list-cameras
  ```
  **Success:** a camera is listed. If not, the cable is backwards or not
  seated — this is the most common problem in the whole build.
- [ ] **2.7** Stop the screen sleeping: `sudo raspi-config` → Display Options →
      Screen Blanking → **Off**. Also disable any screensaver on the display
      itself.

---

## Stage 3 — build the box *(an afternoon)*

Full detail: `04_BUILD.md` Part 3.

- [ ] **3.1** Line the whole inside, lid included, with **matte** black.
- [ ] **3.2** Mount the screen at one end, facing in.
- [ ] **3.3** On the screen: fixed middle brightness, and turn **off** automatic
      brightness, ambient-light sensing, dynamic contrast, every "enhancement"
      mode, and all power-saving dimmers. **Write the brightness number in your
      log.**
- [ ] **3.4** Mount the camera at the other end, rigidly. Aim so the grid fills
      the view with a small margin.
- [ ] **3.5** Bring cables out through **one** hole. Tape the hole, the lid
      seams, and any seam that shows light.
- [ ] **3.6** Cut the ND filter to cover the lens, and cut tape pieces for 25%,
      50% and 100% of the field. Keep them where you can reach them in the dark.

---

## Stage 4 — the bench checks *(an hour)*

Full detail: `04_BUILD.md` Part 5. **Do not skip any of these.**

- [ ] **4.1** Darkness. Screen **off**, lid shut, on the Pi:
  ```bash
  python3 physical/code/bench.py darkframe
  ```
- [ ] **4.2** Record your first calibration session.
  ```bash
  python3 physical/code/run_session.py --session 0 --block 1 --calibration --frames 3000
  ```
  If the stimulus window does not appear over SSH: `export DISPLAY=:0` first.
- [ ] **4.3** Did it arrive intact?
  ```bash
  python3 physical/code/bench.py frames --session 0 --block 1
  ```
- [ ] **4.4** Timing, dither and difficulty, all three at once:
  ```bash
  python3 physical/code/bench.py check --session 0 --block 1
  ```
- [ ] **4.5** Repeat **4.2** and the `lag` check on two more recordings. If the
      three lag measurements agree, you are fine. If they disagree, read
      `10_TROUBLESHOOTING.md`.

---

## Stage 5 — calibrate the difficulty *(this is experiment P-1)*

- [ ] **5.1** Read the margin:
  ```bash
  python3 physical/code/bench.py margin --session 0 --block 1
  ```
- [ ] **5.2** If it is not within **6° of 36.1°**, change **one** setting
      (`--depth` first), record another calibration session, and check again.
- [ ] **5.3** Repeat until it passes. Record **five** calibration sessions at
      the final setting — they build the decoder, and more is strictly better.
- [ ] **5.4** **Write the final `--depth` in your research log and never change
      it again.** If it changes mid-campaign, sessions before and after are not
      comparable and nothing in the data will reveal it.

---

## Stage 6 — freeze the preregistration — **DONE, 24 September 2026**

**Frozen at commit `f4dda04`.**
Nothing in this stage is outstanding. It is kept here in sequence so the
runbook still reads as the order things happened in.

- [x] **6.1** The ten predictions (PP-1 to PP-10) and the ten judgement calls
      were read.
- [x] **6.2** They were accepted as the researcher's own — see
      `09_PREREGISTRATION.md` §10.1, which records the instruction verbatim.
- [x] **6.3** Campaign length fixed at **101 fault-free sessions**: one
      unattended night. The alternative, ~480 sessions over four nights, was
      what PP-1 needed to be falsifiable and was declined against the fair
      date. `02_EXPERIMENTS.md` P-2 has the arithmetic.
- [x] **6.4 / 6.5** Frozen and the hash written into the header.

> **Recording may now begin — once the apparatus exists and passes the §3
> gate.** The freeze is what makes every "we predicted this beforehand"
> checkable rather than asserted; it is not a substitute for the gate.

**If you ever need to change a frozen value**, do not edit
`09_PREREGISTRATION.md`. Append an amendment under its §9: a new numbered
section quoting the original wording, saying what changed, why, on what date,
and **whether the data had been seen**. An amendment made after seeing the data
is allowed and is disclosed in bold. That disclosure is the price of changing
your mind afterwards, and paying it is much better than quietly editing.

---

## Stage 7 — the fault-free campaign *(experiment P-2, nights)*

- [ ] **7.1** Draw the plans — one command draws and checksums all of them.
  ```bash
  python3 physical/code/run_campaign.py plan --session 10 --healthy 101
  ```
- [ ] **7.2** Start it in the evening.
  ```bash
  python3 physical/code/run_campaign.py record --session 10
  ```
- [ ] **7.3** **Every morning, before anything else:**
  ```bash
  python3 physical/code/health_check.py
  python3 physical/code/run_campaign.py status --session 10
  ```
- [ ] **7.4** If you decided on the longer campaign, draw and record more.
      Nothing else in this project buys as much for as little effort.
- [ ] **7.5** **Change nothing during the campaign.** No cleaning, no
      refocusing, no re-seating cables. If something changes anyway, write it
      in the log with the date.

---

## Stage 8 — the degraded sessions *(experiment P-3, ~8 hours, partly attended)*

- [ ] **8.1** Draw them all first, then see which need you in the room.
  ```bash
  python3 physical/code/run_campaign.py plan   --session 20 --degraded 101
  python3 physical/code/run_campaign.py status --session 20
  ```
- [ ] **8.2** Record the automatic ones unattended.
  ```bash
  python3 physical/code/run_campaign.py record --session 20 --software-only
  ```
- [ ] **8.3** Record the by-hand ones with you present. Have the filter or tape
      in hand **before** you start; the stimulus counts down 60, 30, 10, 5, 0.
  ```bash
  python3 physical/code/run_session.py --session 20 --block 7
  ```
- [ ] **8.4** If you mistime one, say so — in the note and in your log.
  ```bash
  python3 physical/code/run_session.py --session 20 --block 7 --note "filter applied ~4 s late"
  ```
      A late fault is not a ruined session. A **silently** late one is.
- [ ] **8.5** Come back and finish every by-hand block. Reporting only the
      software faults would be reporting a benchmark missing its harder half.

---

## Stage 9 — faults nobody designed *(experiment P-5, ~1 hour, attended)*

For each of the five interventions in `06_DATA_COLLECTION.md`:

- [ ] **9.1** Start it, saying what you are about to do.
  ```bash
  python3 physical/code/run_session.py --session 30 --block 1 --undesigned "half-unseated the camera ribbon and re-seated it"
  ```
- [ ] **9.2** **Watch the clock and write down the second you act.**
- [ ] **9.3** Record that onset immediately afterwards.
  ```bash
  python3 physical/code/note_onset.py --session 30 --block 1 --at-clock 21:47:12 --fault CONNECTOR
  ```
      **A session without this cannot be analysed at all.**

---

## Stage 9b — the same questions on a different apparatus *(P-7, ~10 hours, mostly unattended)*

**Why:** this project criticises conclusions drawn from two participants. It
would be drawing conclusions from one box. This narrows that.

Three extra configurations, each **re-calibrated to 36.1° first** so that only
the apparatus changes and not the difficulty.

| Config | What to change |
|---|---|
| B | `--exposure 16000`, and halve `--depth` to compensate |
| C | `--patch 24` |
| D | `--cols 12 --rows 8` (96 channels instead of 384) |

For each one:

- [ ] **9b.1** Re-calibrate. Record a calibration session with the new settings
      and check the margin:
  ```bash
  python3 physical/code/run_session.py --session 40 --block 1 --calibration --exposure 16000
  python3 physical/code/bench.py margin --session 40 --block 1
  ```
      Adjust `--depth` until the margin is back within 6° of 36.1°.
      **Write the settings in the log.**
- [ ] **9b.2** Draw and record a reduced campaign — 20 fault-free, 20 degraded:
  ```bash
  python3 physical/code/run_campaign.py plan   --session 41 --healthy 20
  python3 physical/code/run_campaign.py plan   --session 41 --degraded 20
  python3 physical/code/run_campaign.py record --session 41
  ```
- [ ] **9b.3** Label every session with its configuration as you record it:
  ```bash
  python3 physical/code/run_session.py --session 41 --block 1 --config B
  ```
      Sessions with no label count as configuration **A**, the baseline.

---

## Stage 10 — the analysis *(20 minutes, laptop)*

- [ ] **10.1** Copy the recordings to your laptop. Only recording needs the Pi.
- [ ] **10.2** Build the table. Read its printout before anything else.
  ```bash
  python3 physical/code/make_session_table.py
  ```
- [ ] **10.3** Run the five analyses, in this order.
  ```bash
  python3 physical/code/analyze_falsealarm.py
  python3 physical/code/analyze_leadtime.py
  python3 physical/code/analyze_leadtime.py --undesigned
  python3 physical/code/analyze_correlation.py
  python3 physical/code/analyze_decision_rate.py
  ```
- [ ] **10.4** Draw the figures.
  ```bash
  python3 physical/code/figures.py all
  ```
- [ ] **10.5** Analyse each apparatus configuration **separately** — each is a
      different apparatus and gets its own decoder and threshold. Pooling them
      would average over the thing being varied.
  ```bash
  python3 physical/code/make_session_table.py --config B --tag _B
  python3 physical/code/analyze_decision_rate.py --tag _B
  python3 physical/code/analyze_leadtime.py --tag _B
  ```
      Repeat for C and D. Then compare the four:
  ```bash
  python3 physical/code/analyze_apparatus.py --configs A,B,C,D
  ```
      It answers **PP-9** (does the decision-rate curve keep its direction?) and
      **PP-10** (do the lead time and false-alarm rate move?), and it is allowed
      to say *not testable* — which is a real answer, not a failure.
- [ ] **10.6** Run it again with the other decoder, as a stated check.
  ```bash
  python3 physical/code/make_session_table.py --decoder per-session --tag _persession
  ```
- [ ] **10.7** Read `07_ANALYSIS.md` alongside the reports. It says what each
      result does and does **not** license you to claim.

---

## Stage 11 — whatever the results are, you are covered

**Every outcome has a write-up.** `08_WHAT_COMES_AFTER.md` decided this before
any data existed, which is what stops a disappointing result being quietly
reframed as a success.

| What you find | What you report | Do you build anything more? |
|---|---|---|
| Strong correlation, **unusable** warning | **Hypothesis supported.** Correlation-based validation does not support the claims made from it | No device — a validation protocol instead |
| Strong correlation, **usable** warning | **Hypothesis falsified.** The published approach is adequate, and now has evidence | Yes — a live demonstration monitor |
| Correlation collapses once the time trend is removed | Published correlations of this kind may be inflated | No device |
| P-6's curve rises, intervals separate | A decision-rate design rule for any drifting sensor array | Yes — a decision-rate calculator |
| Silence gate fails with no biology present | The limitation is in the approach, not in neural recordings | No device |
| Everything inconclusive | The benchmark, the data, and exactly how much more recording would settle it | No device |

**Four of the six say "no device", and that is the plan, not a disappointment.**
The deliverable is the apparatus and the measurement — see
`08_WHAT_COMES_AFTER.md` §4 for the answer to "what did you build?"

- [ ] **11.1** Write the results into your research log, including anything
      that surprised you.
- [ ] **11.2** Check every preregistered prediction in `09_PREREGISTRATION.md`
      §2 and record whether it held. **Report the ones that failed.**
- [ ] **11.3** Rebuild Section C of the December plan from
      `research/RESEARCH_PLAN_DECEMBER_DRAFT.md`, with the real numbers in it.

---

## When something goes wrong

`10_TROUBLESHOOTING.md`, organised by when it happens. If it is not in there:

1. **Write down what you saw before you change anything.** Fixing it destroys
   the evidence.
2. Change one thing.
3. Re-run the relevant check, not the whole campaign.
4. Write down what fixed it — including what did not.

---

## The whole thing, in six commands

If you remember nothing else:

```bash
python3 physical/code/monitor.py --selftest          # does the software work?
python3 physical/code/stimulus.py --benchmark 300    # can this machine draw it?
python3 physical/code/bench.py check --session 0 --block 1   # is the box right?
python3 physical/code/health_check.py                # is the campaign sound?
python3 physical/code/make_session_table.py          # turn recordings into rows
python3 physical/code/figures.py all                 # draw everything
```
