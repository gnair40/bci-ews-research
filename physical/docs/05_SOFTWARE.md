# The code: what each file does and when you run it

Sixteen files in `physical/code/`. This document says what each one is for, what
it needs, what it produces, and where it sits in the workflow. Each file also
carries a long explanation at the top of itself; open it and read it if you want
the reasoning rather than the summary.

Nothing here assumes you can read Python. You run these by typing one line.

---

## The workflow in one picture

```
      BEFORE                    RECORDING                  AFTER
      ------                    ---------                  -----

  monitor.py --selftest
  dryrun.py  ------------------------------------------>  (test the chain)

  bench.py darkframe
  bench.py frames|lag|dither|margin  <--- run_session.py --calibration
        |
        | apparatus is calibrated
        v
  draw_onset.py  ----------->  run_session.py  ------->  make_session_table.py
  (decide first,               (record)                         |
   lock with a checksum)             ^                          |
        |                            |                          v
        +----- run_campaign.py ------+              analyze_falsealarm.py   P-2
               (a hundred of them)                  analyze_leadtime.py     P-3
                                                    analyze_correlation.py  P-4
                                                    analyze_decision_rate.py P-6
```

The left-to-right order is not a suggestion. `run_session.py` refuses to record
a session that has no drawn plan, and the analysis scripts refuse to run before
the table exists. The scripts enforce the order because the order is the
argument.

---

## Before you have hardware

### `monitor.py --selftest`

**What:** builds a fake recording in memory, decodes it, degrades it, and checks
the monitor reacts. Needs no camera and no recordings.
**Run it:** `python3 physical/code/monitor.py --selftest`
**Produces:** PASS or FAIL on your screen.
**When:** first thing, on any computer, and again on the Pi after setting it up.

### `dryrun.py`

**What:** manufactures fake recordings in the exact format the apparatus
produces, so the whole analysis chain can be run before the box exists.
**Run it:** `python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8`
**Produces:** `physical/data/dryrun/` — a separate folder, with `SYNTHETIC`
written inside every session file.
**When:** once, before building, and again whenever you change an analysis
script and want to know it still runs.

> **No number from the dry run belongs in the write-up.** The fake recordings
> come from a formula written by the same person who wrote the analysis. A
> monitor tested only against its author's assumptions has been tested against
> nothing. That is exactly the criticism experiment P-5 exists to answer for the
> real apparatus.

---

## Setting the apparatus up

### `bench.py`

**What:** the checks that must pass before any session counts as data. Each one
catches a failure that produces plausible numbers rather than an obvious error.

| Subcommand | Asks | Needs |
|---|---|---|
| `darkframe` | Is the box light-tight? | the camera |
| `frames` | Did the recording arrive intact? | a recording |
| `lag` | How far behind the screen is the camera? | a recording |
| `dither` | Is the sub-brightness-level signal surviving? | a recording |
| `margin` | Is it as hard as the real thing? (experiment P-1) | a recording |
| `check` | all four of the above that need only a recording | a recording |

**Run it:** `python3 physical/code/bench.py check --session 0 --block 1`
**Produces:** PASS or FAIL for each, with what to do about a failure in order of
likelihood. `lag` also writes `physical/data/lag.json`, which every analysis
script then reads by itself.
**When:** Part 5 of `04_BUILD.md`, and again any time the apparatus is moved,
adjusted, or reassembled.

---

## Recording

### `draw_onset.py` — the most important script in the phase

**What:** decides, before the recording exists, whether a session is healthy
and, if not, when the degradation starts, what kind it is and how severe. Writes
that to a file and records the file's checksum.

**Run it:**
```bash
python3 physical/code/draw_onset.py --session 3 --block 7
python3 physical/code/draw_onset.py --session 3 --block 7 --healthy
```
**Produces:** `physical/data/onsets/s3_b7.json` and a line in
`physical/data/onsets/MANIFEST.csv`.
**When:** before **every** session. No exceptions.

**Why it matters.** In a real brain-implant recording, nobody wrote down when
the electrodes started going bad. So "how early did the monitor warn?" depends
on which moment the analyst picks, and two analysts get two answers. Fixing the
answer first, under a checksum, removes that — and makes the claim checkable by
somebody who does not trust you.

The script **refuses to overwrite an existing plan.** That refusal is the point:
re-drawing a plan after seeing a recording is precisely the tampering the
checksum exists to prevent.

### `note_onset.py` — the P-5 counterpart to `draw_onset.py`

**What:** records when a fault you caused *by hand* actually started, after the
fact, from a stopwatch.
**Run it:**
```bash
python3 physical/code/run_session.py --session 30 --block 1 --undesigned "fingerprint on the lens edge"
python3 physical/code/note_onset.py  --session 30 --block 1 --at-clock 21:47:12
```
**Produces:** `physical/data/raw/s30_b1/observed_onset.json`.
**When:** experiment P-5 only, immediately after each recording.

**Why this is not `draw_onset.py`.** P-5's faults are ones nobody designed — a
half-unseated ribbon cable, a fingerprint, a warm afternoon. They cannot be
drawn in advance, because the onset is the moment your hand moves. So the onset
is your word rather than a checksum, which is weaker evidence, and the analysis
keeps those sessions in **a separate table that is never pooled with P-3**.

What P-5 keeps is the part that matters most: nobody designed what the fault
would look like.

It refuses to overwrite an existing note. If the first was wrong, `--replace`
exists and the research log gets a line saying what was wrong — a silently
corrected onset is indistinguishable from an onset adjusted to improve a result.

### `stimulus.py`

**What:** draws the moving pattern the camera watches, and writes down the true
direction on every frame. Applies the software degradations automatically at the
drawn moment, and prints a countdown for the ones you impose by hand.
**Produces:** `stim.csv` — one row per frame.
**When:** started for you by `run_session.py`. You rarely run it directly.

Two settings in it are calibration, not preference: `--depth` (how strongly
direction shows, set by B-7 and then never changed) and the spatial dithering
(how a fraction of a brightness level reaches a screen that can only show whole
ones). Both are explained at the top of the file.

### `capture.py`

**What:** records what the camera sees, reduced to one number per channel per
frame — not photographs.
**Produces:** `capture.npy`, `capture_t.npy`, `capture_meta.json`.
**When:** started for you by `run_session.py`.

Automatic exposure and automatic white balance are **forced off**. A modern
camera constantly adjusts itself to keep the picture looking good, which here
means quietly cancelling out the degradation the experiment is imposing. The
recording would then show a healthy system while the system was being degraded,
and nothing in the data would say so.

### `run_session.py`

**What:** records one complete session — starts the stimulus, starts the
capture, waits for both, and writes down every setting used.
**Run it:** `python3 physical/code/run_session.py --session 3 --block 7`
**Produces:** `physical/data/raw/s3_b7/` and a row in
`physical/data/raw/SESSION_LOG.csv`.
**When:** once per session.

It **refuses** to record unless a plan has been drawn, with two marked
exceptions: `--calibration` (apparatus setup, kept out of every result) and
`--undesigned "what you are about to do"` (experiment P-5, where the onset is
written down afterwards with `note_onset.py`). It also refuses to overwrite a
folder that already has a recording in it.

### `run_campaign.py`

**What:** a hundred sessions without sitting next to it.
**Run it:**
```bash
python3 physical/code/run_campaign.py plan   --session 10 --healthy 101
python3 physical/code/run_campaign.py status --session 10
python3 physical/code/run_campaign.py record --session 10
```
**Produces:** nothing of its own — it calls the two scripts above.
**When:** the P-2 healthy campaign and the P-3 degraded campaign.

It can be stopped and restarted: `record` skips any block already recorded, so
if the power fails at block 60 the same command carries on at 60 in the morning.
It stops after two failures in a row, because two in a row almost always means
the camera has gone, the screen has slept, or the disk is full, and grinding
through ninety-nine more failures wastes the night.

---

## Analysis

### `make_session_table.py` — run this before any analysis

**What:** reads every recording, runs the decoder and the monitor over each one,
and writes one row per session plus a per-window record.
**Run it:** `python3 physical/code/make_session_table.py`
**Produces:** `physical/data/sessions.csv`,
`physical/data/processed/windows/*.npz`, `physical/data/processed/table_meta.json`.

It does three things that decide whether anything downstream means anything.

**It splits the sessions into three groups.** `fit` builds the decoder and the
monitor; `val` chooses the warning threshold; `test` is where the false-alarm
rate and the lead time are reported from. A threshold chosen on the same
sessions it is then measured on will always look good, because it was chosen to
look good on exactly those recordings.

**It never modifies `physical/data/raw/`.** Raw recordings are written once and
read forever.

**It honours `physical/data/EXCLUSIONS.csv`**, which is how a session is set
aside without deleting raw data. The file wants `folder,reason,excluded_at`, and
a row with no reason is **refused outright** — an unexplained exclusion cannot
be told apart from dropping a session because of how it turned out.

**It refuses to score a P-5 session whose onset was never written down**, and
names it. Such a session has nothing on record saying a fault happened, so every
other piece of code would read it as healthy and put it in the fault-free arm —
quietly corrupting the one measurement this phase exists to make.

**It prints how much healthy recording you would need.** See below.

### `analyze_falsealarm.py` — experiment P-2

**What:** how often the monitor warns when nothing is wrong, plus the silence
gate.
**Run it:** `python3 physical/code/analyze_falsealarm.py`
**Produces:** `physical/data/results/P2_FALSE_ALARM_RATE.md` and a JSON file.

### `analyze_leadtime.py --undesigned` — experiment P-5

**What:** the same analysis, on the sessions whose faults nobody designed,
reported in its own file with a direct comparison against P-3.
**Run it:** `python3 physical/code/analyze_leadtime.py --undesigned`
**Produces:** `physical/data/results/P5_UNDESIGNED_FAULTS.md`.
**When:** after P-3, because the comparison needs P-3's numbers to exist.

If undesigned faults turn out to be meaningfully harder to detect, that is a
finding about how fault benchmarks are built — **including this project's own** —
and it belongs in the write-up as a headline rather than a limitation.

### `analyze_leadtime.py` — experiment P-3

**What:** how long the monitor takes to notice, and how much warning it gives
before decoding actually fails. Always printed beside the false-alarm rate at
the same threshold.
**Run it:** `python3 physical/code/analyze_leadtime.py`
**Produces:** `physical/data/results/P3_LEAD_TIME.md` and a JSON file.

### `analyze_correlation.py` — experiment P-4

**What:** the experiment that tests the hypothesis. Computes the correlation the
field would report *and* the lead time and false-alarm rate, **on the same
recordings**.
**Run it:** `python3 physical/code/analyze_correlation.py`
**Produces:** `physical/data/results/P4_CORRELATION_VS_USABILITY.md`.

### `analyze_decision_rate.py` — experiment P-6

**What:** re-scores the recordings at every decision rate from one per window to
one per session. No extra recording needed.
**Run it:** `python3 physical/code/analyze_decision_rate.py`
**Produces:** `physical/data/results/P6_DECISION_RATE.md`.

### `figures.py` — every picture, from the stored data

**What:** six figures, regenerated from `physical/data/` by one command.
**Run it:** `python3 physical/code/figures.py all`
**Produces:** `physical/data/figures/*.png` at 200 dpi.
**When:** after the analysis scripts, and again any time a number changes.

| Figure | What it is for |
|---|---|
| `session_detail` | One session with the fault onset, the failure, and the warning all marked. **The figure that explains the project.** |
| `false_alarm_evidence` | Fault-free hours accumulating against the rule-of-three bound, with the 30-hour mark drawn. Makes the campaign-length argument visual. |
| `lead_time` | The distribution, with zero marked. Everything left of it arrived too late. |
| `decision_rate` | Detection against decision rate, with the intervals — because overlapping intervals *are* the result. |
| `severity_response` | The manipulation check as a picture. |
| `correlation_vs_usability` | What the field publishes on the left, the two numbers that decide usability on the right, same recordings. |

**Never edit a figure by hand**, for the same reason as the reports: a
hand-edited figure is one nobody can trace back to data. Each one burns its
date, session count and source into the image, so a figure that escapes into a
slide deck still says what it rests on.

Deliberately absent: any dual-axis chart pairing lead time against false-alarm
rate, and any single combined "score". They have opposite signs of "good", and
the trade-off *is* the finding.

### `health_check.py` — run this every recording day

**What:** asks whether the campaign is still sound. Takes about a second.
**Run it:** `python3 physical/code/health_check.py`
**Produces:** PASS or FAIL for six checks, on your screen.
**When:** every recording day, before starting.

It checks the plan checksums, completeness, dropped and truncated frames,
whether the apparatus itself has drifted since calibration, disk headroom, and
that every excluded session carries a reason.

**It deliberately cannot see any result.** A check you run daily that could see
results is a check that would slowly teach you to stop the campaign when the
numbers look good. It only asks whether the recordings are what they claim.

### `monitor.py` — the shared core

Not run directly, except for `--selftest`. Every analysis script imports it, so
that the decoding, the windowing, the risk score and the warning logic are
defined **once**. Four scripts each working it out for themselves would drift
apart, and two scripts reporting different numbers from the same recording is
the kind of bug that survives to a poster.

It imports the detector, the warning state machine and the 10-degree failure
threshold from the computational half (`scripts/19`, `scripts/20`, `scripts/22`)
rather than reimplementing them. **The apparatus changes; the thing being tested
does not.** If the physical phase used a differently-tuned monitor, a difference
in the result could just as easily be a difference in the monitor.

---

## Three decisions in the code that are scientific, not technical

These are choices someone could reasonably disagree with. They are listed here
rather than buried, and each is adjustable from the command line.

### 1. The decoder is frozen, not refitted each session

`--decoder frozen` (the default) fits the decoder once, on the earliest healthy
sessions, and never refits. That is what happens to a real implant: it is
calibrated on one day and used on later ones, and the drift between those days
is the problem. `--decoder per-session` refits every session, which makes
between-session drift invisible.

Run both. If a result only appears with a frozen decoder, it is a result about
**staleness**, and it should be described that way.

### 2. A warning is timestamped at the END of the window that produced it

A window covers 30 seconds, and its risk score cannot exist until the last of
those seconds has happened. Timestamping the warning at the window's start would
credit the monitor with knowing something up to half a minute before the data
existed, and would inflate every lead time by that much.

### 3. Lead time and detection delay are different things

- **Lead time** = when decoding actually failed − when the monitor warned.
  Defined exactly as in the computational half, so the two compare.
- **Detection delay** = when the monitor warned − the drawn onset.
  **New here.** Not computable on any archived human recording.

A monitor can be slow to notice and still give useful warning, if the decoder
keeps working for a while after the fault starts. Both are reported.

---

## The thing the code will tell you that the experiment plan does not

`make_session_table.py` and `analyze_falsealarm.py` both print this, and it is
worth knowing before the campaign rather than after.

Suppose the monitor is perfect and produces **zero** false alarms. Zero is not a
rate — it is an upper bound. Seeing no events in H hours puts a 95% upper bound
of about **3/H per hour** on the true rate (the "rule of three"). To push that
bound down to the 0.1 per hour budget, H must be about **30 hours of held-out
healthy recording**.

The experiment plan calls for 101 healthy sessions. After the fit and validation
groups are taken out, that leaves roughly **four test hours**, which supports an
upper bound of about 0.75 per hour — seven times the budget.

**101 healthy sessions is enough to catch a monitor that is noisy. It is not
enough to show that a quiet monitor meets the budget.** Both scripts print the
arithmetic for whatever has actually been recorded, so the claim in the write-up
can be the one the data supports. If the honest answer is an upper bound rather
than a rate, the write-up should say "upper bound" — the difference is the whole
argument.

Recording more is cheap: the healthy campaign is unattended and runs overnight.
Thirty hours is about four nights.
