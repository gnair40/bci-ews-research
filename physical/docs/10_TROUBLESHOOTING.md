# When something goes wrong

Organised by **when** it happens, because that is how you will meet it. Each
entry: what you see, what it actually means, and what to do — with the command.

**The rule underneath all of it.** Almost nothing here announces itself. A
screen that sleeps, a room that warms, a disk that fills, a filter applied four
seconds late — every one of them produces recordings that look completely
normal and analyse into nonsense. That is why there is a daily check and why it
takes a second:

```bash
python3 physical/code/health_check.py
```

**Run it every recording day before you start.** Finding out on day four that
day two was junk costs two days.

---

## Part A — setting up

### The camera is not detected

`rpicam-hello --list-cameras` shows nothing.

Nine times out of ten the ribbon cable is in backwards or not seated. Power the
Pi **off**, lift the connector tab straight up, insert with the **silver
contacts facing the HDMI ports**, push fully home, press the tab down. Tug very
gently — it should not move.

If it still fails: the Pi 4 uses the older, wider camera connector. A cable
bought separately may be the narrower Pi 5 kind and will not fit. Use the cable
the camera shipped with.

### The stimulus window does not appear when I connect over SSH

An SSH session has no screen attached to it. Either run the stimulus from the
Pi's own desktop, or tell it which display to use:

```bash
export DISPLAY=:0
python3 physical/code/run_session.py --session 0 --block 1 --calibration
```

Put that `export` line in `~/.bashrc` on the Pi and you will not meet this again.

### `ModuleNotFoundError: picamera2` (or pygame)

```bash
sudo apt install -y python3-picamera2 python3-pygame
```

**Not `pip`.** On Raspberry Pi OS the camera library is built against the
system and the `pip` version usually does not work.

If `picamera2` is missing on your laptop rather than the Pi, that is correct —
capture only runs on the Pi. Everything else, including every analysis script
and `monitor.py --selftest`, runs anywhere.

### The box will not go dark enough

`bench.py darkframe` fails. Tape in this order: the cable hole, the lid seam,
the screen bezel. Check with the room lights **on** — that is the worst case.

If you cannot get below the threshold, the check tells you to record a dark
frame each session and subtract it. **Write that down as a deviation.** A
subtracted offset is not the same as no offset when the thing being measured is
drift, and the write-up has to say which one you had.

---

## Part B — calibration (P-1)

### The margin is far too large — the apparatus decodes too well

Expected, on the first try. Lower `--depth`; halving it roughly doubles the
error.

```bash
python3 physical/code/run_session.py --session 0 --block 2 --calibration --depth 0.001
python3 physical/code/bench.py margin --session 0 --block 2
```

**Change one thing at a time.** Depth, exposure, and capture size all move the
margin, and moving two at once means you learn nothing from the result.

### The margin is far too small — it cannot decode

Raise `--depth`, or raise `--exposure`, or average more pixels per channel by
raising the capture size toward 96×64. Same rule: one at a time.

If it cannot decode **at all** (error at chance), stop adjusting depth and check
the dither and timing first — those are upstream, and no amount of depth fixes a
signal the screen is destroying or a label that is shifted.

### The dither check fails

The screen is processing the image. In order of likelihood:

1. Turn **off** dynamic contrast, every "enhancement" or "vivid" mode, all
   ambient-light adjustment, and every power-saving dimmer.
2. `--exposure 16000` — a longer exposure averages more of the dither.
3. Try a different screen. Some panels are really 6-bit with their own
   dithering, which fights yours.

Only if all three fail, raise `--depth` fourfold **and re-run `bench.py
margin`**, because the apparatus will no longer be matched to cortex and every
comparison has to say so.

### The lag is different every time I measure it

A varying delay is the one thing a fixed correction cannot fix. Either drop to
25 frames per second, or hold each direction for five seconds (`--hold 250`) and
analyse only the middle three. Both cost resolution and both are better than a
label that is wrong by an unknown amount.

### The Pi cannot hold 50 frames a second

Measure it rather than guess:

```bash
python3 physical/code/stimulus.py --benchmark 300
```

**This is the one assumption a slow computer can break silently.** Late frames
mean every camera frame's direction label is wrong by an unknown amount, and
nothing in the recording says so — `bench.py frames` catches it afterwards, this
catches it before a campaign is planned around a rate the machine cannot hold.

The benchmark prints the options in order of preference:

1. **Run the stimulus on a faster computer** with the screen attached, and
   capture on the Pi. Then **re-measure the lag** — two machines means two
   clocks, and `bench.py lag` is what tells you whether that matters.
2. **Lower `--patch`.** 40 now; 24 costs about a third as much. This shrinks the
   pattern on screen and changes how many camera pixels see each patch, so it is
   an **apparatus change**: re-run `bench.py margin` afterwards and record it.
3. **Drop to `--fps 25`** and record twice as long per session. The analysis
   window is 30 s either way; you halve the resolution of every lead-time claim,
   so the write-up has to say so.

For reference, the drawing arithmetic measured **1.83 ms per frame** on a
laptop against a 20 ms budget. An earlier version of the loop measured 6.9 ms,
which would not have fitted on a Pi — it expanded every patch to pixels twice
per frame instead of broadcasting.

### Lots of dead channels

The screen does not fill the camera's view, or part of it is in shadow. Move the
camera or the screen until the grid fills the frame with a small margin, and
re-record. `bench.py frames` tells you the count.

### Channels clipped at 255

Too bright, or the exposure is too long. Lower `--brightness` or `--exposure`. A
clipped channel physically cannot show an increase, so it is blind to half the
faults.

---

## Part C — during a campaign

### The screen went to sleep partway through the night

Every session after that point is a dark frame. `health_check.py` catches it as
a brightness shift; `bench.py frames` catches it as dead channels.

Exclude the affected sessions — **do not delete them** — and re-record:

```
physical/data/EXCLUSIONS.csv
folder,reason,excluded_at
s10_b34,screen slept; dark frames from 40 s onward,2026-10-04
```

Then stop it recurring: disable the screensaver, disable screen blanking, and
set the power profile to never sleep. On the Pi:
`sudo raspi-config` → Display Options → Screen Blanking → Off.

### The Pi rebooted / the power cut mid-campaign

Nothing is lost except the session in progress, which will be short and is
caught as a truncated recording. `run_campaign.py record` skips anything already
recorded, so just run the same command again:

```bash
python3 physical/code/run_campaign.py record --session 10
```

Exclude the truncated one with its reason.

### "No space left on device"

Recordings are about 25 MB each; a hundred is 2.5 GB. Move completed recordings
to the USB drive, or record to it directly. `health_check.py` tells you how many
more sessions will fit **before** you start a campaign that would not fit.

A disk that fills overnight truncates sessions rather than stopping cleanly,
which is why this is worth checking rather than discovering.

### I applied a hand-imposed fault late

Say so, in the session note and in the research log:

```bash
python3 physical/code/run_session.py --session 20 --block 7 --note "filter applied ~4 s late"
```

**A late fault is not a ruined session.** The onset is what was drawn, and four
seconds is smaller than one analysis window. A *silently* late fault is a
corrupted measurement. The difference is entirely whether you wrote it down.

If you missed it by much more than a window — say twenty seconds — exclude the
session and record that block again under a new number.

### I recorded a session without drawing a plan first

`run_session.py` refuses, so this can only happen with `--calibration` or
`--undesigned`. If it was meant to be an experimental session, it cannot be used
for lead time or false alarms: nothing fixed its onset in advance. Record it
again properly. The stray recording can stay where it is, marked `calibration`,
and the analysis will ignore it.

### The temperature sensor is not wired up

Not fatal — `run_session.py` logs an empty temperature and carries on. But
temperature is why the log exists: a camera's dark current rises with it, and if
the risk score climbs over an evening and so did the room, you cannot separate
them afterwards. Wire it up if you can; note in the log that you did not, if you
cannot.

### A plan file no longer matches its checksum

`health_check.py` reports `CHANGED`. **Do not "fix" the manifest.** The onset in
that plan is no longer provably the one drawn before the recording existed,
which is the entire basis of the lead-time measurement.

Exclude the session, with the reason, and write what happened in the log. If you
know what touched the file — an editor, a sync tool, a copy — say that too.

### The room got much hotter or colder than usual

Record it in the log with the date and the reading. It does not invalidate
anything by itself, but it is the first thing to check if the risk score does
something odd on that night, and it is not recoverable afterwards if you did not
write it down.

---

## Part D — analysis

### "No healthy sessions in the test group"

Every fault-free session was used to build the monitor or choose its threshold.
Record more. There is no analysis fix: the false-alarm rate has to come from
sessions the monitor never saw.

Recording more **calibration** sessions also helps, because calibration sessions
build the decoder and free up experimental fault-free sessions for the test
group.

### No threshold could be chosen

The monitor's scores on the validation sessions never fall inside the budget at
any threshold in the grid. Usually this means the validation set is too small —
with two sessions, the budget permits 0.007 alarms, so any alarm at all fails.
Record more fault-free sessions.

### The monitor warns on everything, or on nothing

Both usually mean the decoder or the detector was fitted on the wrong data.
Check `make_session_table.py`'s printout: how many sessions went into `fit`, and
is the median decoding margin still near 36.1°? A margin that has drifted far
from calibration means the apparatus changed, and the monitor is reacting to
that rather than to the faults.

### The margin has drifted since calibration

Something about the apparatus changed mid-campaign. Find out what, write it in
the log with the date, and say so in the write-up. Sessions before and after are
not comparable, and **nothing in the data will reveal this afterwards** — which
is exactly why it is checked daily.

### Detection does not rise with severity

This is preregistered prediction **PP-6**, and it is a manipulation check rather
than a finding. If it fails, the monitor is not tracking the fault, and PP-1 to
PP-5 get reported but **not interpreted as being about degradation**. Say that
plainly; do not quietly reinterpret them.

### No correlation measure reaches 0.70

The hypothesis test is **inconclusive** — not supported, not refuted. A weakly
correlated monitor says nothing about whether correlation-based validation is
sufficient. Report it as inconclusive. This is written into the preregistration
precisely so it cannot be talked into a finding afterwards.

### The analysis runs out of memory, or the machine freezes

It should not — `make_session_table.py` loads one recording at a time and peak
memory is a couple of sessions whatever the campaign size. If it happens
anyway, the likely cause is an unusually large fit set combined with a machine
that has very little RAM.

Check the printout: how many sessions went into `fit`? Those are loaded twice
(once for the decoder's normalisation, once for its weights), one at a time,
and their *windows* are accumulated — which is small, but not nothing at fifty
sessions.

If you are running the analysis on the Pi itself, run it on a laptop instead.
Only recording needs the Pi; every analysis script runs anywhere.

### A recording will not load

`make_session_table.py` names it rather than skipping silently. Usually it is
truncated — check `capture_meta.json` for how many frames it actually got.
Exclude it with the reason.

### Two reports disagree about the same number

Run the gates:

```bash
python3 scripts/31_verify_claims.py
python3 scripts/55_reproducibility_audit.py
```

If both pass and the documents still disagree, one of them holds a
**hand-copied constant** rather than reading it from a file. That has happened
in this project — twice — and the fix is to make the number a claim in
`31_verify_claims.py` so the disagreement cannot recur silently.

---

## Part E — if something goes wrong that is not on this list

1. **Write down what you saw, before you change anything.** In the research log,
   with the date and time. The state you are about to destroy by fixing it is
   sometimes the only evidence of what happened.
2. **Change one thing.**
3. **Re-run the relevant check**, not the whole campaign.
4. **Write down what fixed it**, including the things that did not.

The research log is not paperwork. Three weeks from now it is the only thing
that will explain an odd result, and a log that records only successes is not a
record of the research.

---

## The commands, in one place

```bash
python3 physical/code/monitor.py --selftest          # does the software work?
python3 physical/code/health_check.py                # is the campaign sound?
python3 physical/code/bench.py check --session 0 --block 1   # is the box right?
python3 physical/code/bench.py darkframe             # is it dark? (Pi only)
python3 physical/code/run_campaign.py status --session 10    # what is left?
python3 tools/check_all.py                           # every gate, one command
python3 scripts/31_verify_claims.py                  # do the numbers still hold?
```

And to rehearse the whole analysis chain with no hardware at all:

```bash
python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8 --undesigned 4 --orphans 2
python3 physical/code/make_session_table.py --raw physical/data/dryrun/raw --tag _dryrun
python3 physical/code/analyze_falsealarm.py --tag _dryrun
python3 physical/code/analyze_leadtime.py --tag _dryrun
python3 physical/code/analyze_decision_rate.py --tag _dryrun
python3 physical/code/figures.py all --tag _dryrun
python3 physical/code/dryrun.py --cleanup
```
