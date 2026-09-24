# Collecting the data

What to do, in order, on each day of recording. Assumes the apparatus has passed
every check in `04_BUILD.md` Part 6.

About **28 hours of recording** across **337 sessions** (217 for P-1 to P-5,
plus 120 for the P-7 apparatus arm), most of it unattended overnight. The
calendar matters more than the clock.

**The fault-free campaign is one night**, not four: 101 sessions at five
minutes each is 8.4 hours, and that count is frozen
(`09_PREREGISTRATION.md` §4, commit `f4dda04`). The P-7 arm is three more
unattended nights on top.

---

## What a campaign costs, measured

Not estimated — these are from full-length 15000-frame sessions.

| | Per session | **101 (the frozen P-2 arm)** | 337 (the whole plan) | 480 (what PP-1 would have needed) |
|---|---|---|---|---|
| Raw data on disk | **23.7 MB** | 2.4 GB | 5.2 GB | **11.4 GB** |
| Recording time | 5 min | 8.4 h | 18 h | 40 h |
| Analysis, start to finish | 0.58 s | 1 min | 2 min | **5 min** |

A session is `capture.npy` (23.0 MB), `stim.csv` (0.6 MB), `capture_t.npy`
(0.1 MB) and `session.json`.

**11 GB fits on a 32 GB card beside the operating system, but not comfortably.**
Move completed recordings to the USB drive as you go, and let
`health_check.py` tell you how many more will fit before you start a night that
would not finish. A disk that fills overnight truncates sessions rather than
stopping cleanly.

**The analysis is fast and runs anywhere.** Only recording needs the Pi; run
everything else on a laptop, where it takes minutes rather than tens of minutes.

## The four rules

**1. Draw before you record.** Every session's plan — healthy or degraded, and
if degraded, when and what and how badly — is decided and checksummed before the
recording exists. `run_session.py` refuses otherwise.

**2. Change nothing mid-campaign.** No cleaning the lens, no refocusing, no
re-seating cables, no adjusting the screen. If something is changed anyway,
**write it in the log with the date and time.** An undocumented mid-campaign
change cannot be detected afterwards and would invalidate the arm it happened
in. Writing it down costs a sentence; not writing it down can cost the campaign.

**3. Never edit a recording.** Nothing modifies `physical/data/raw/`. If a
session went wrong, record another one under a new block number and note why.

**4. Log the mistakes too.** A research log that only records what went well is
not a record of the research. If you drop the filter, sneeze on the lens, or
realise at block 40 that the screen went to sleep at block 12 — that goes in.

---

## Every recording day, before you start

Five minutes. Do not skip it, because every one of these has a failure mode that
produces recordings that look fine.

```bash
cd ~/bci-ews-research
git pull
python3 physical/code/monitor.py --selftest
```

Then, by hand:

- [ ] The box is closed and taped.
- [ ] The screen is on, at the brightness written in the log, with every
      automatic adjustment still off.
- [ ] The camera has not moved.
- [ ] `df -h` shows free space. Recordings are about 25 MB each; a hundred
      sessions is 2.5 GB.
- [ ] The temperature sensor reading is noted in the log.

Every two or three days, or after anything is touched:

```bash
python3 physical/code/bench.py check --session 0 --block 1
```

Record a fresh calibration session first if the last one is old:

```bash
python3 physical/code/run_session.py --session 0 --block <next> --calibration
```

---

## P-1 — calibration (about 25 minutes, attended)

Already done as part of `04_BUILD.md` Part 5, B-7. It is listed here because it
is formally an experiment and its result — the final modulation depth — belongs
in the log.

1. Record five calibration sessions.
2. Run `bench.py margin` on each.
3. If the margin is not within 6° of 36.1°, adjust `--depth`, record again,
   repeat.
4. **Write the final depth in the log. Never change it again.**

Those five sessions also become the `fit` group: the decoder and the monitor are
built from them. That is why they are worth recording properly even though they
are "only" calibration — and why recording more of them is good, since every
calibration session is one fewer healthy experimental session spent on fitting
instead of on measuring false alarms.

---

## P-2 — the healthy campaign (four nights, unattended)

This is the measurement that does not exist anywhere else. Genuinely fault-free
recording in the archived human data amounts to **1.4 hours**; a budget of one
false alarm per ten hours cannot be checked against that by anyone.

### Draw the plans

```bash
python3 physical/code/run_campaign.py plan --session 10 --healthy 101
```

One command draws all 101 and checksums every one.

### Record

```bash
python3 physical/code/run_campaign.py record --session 10
```

Leave it. 101 sessions at five minutes each is about 8.4 hours, so start it in
the evening. In the morning:

```bash
python3 physical/code/run_campaign.py status --session 10
```

If it stopped early it says so, and running `record` again carries on where it
left off.

### Do not record more

**101 is the frozen count, not a floor to beat.** `09_PREREGISTRATION.md` §4
fixed it on 24 September 2026, and §9 of that document makes any extension an
appended, dated amendment stating whether the data had been seen. The reason
for that formality is specific: recording extra fault-free hours *after*
seeing that the monitor was noisy, until the rate comes down, is the exact
shape of the thing preregistration exists to prevent. Deciding to extend
before running any analysis is fine — write the amendment first.

**What 101 costs you, stated plainly.** After the fit and threshold groups are
taken out, 101 leaves about four held-out test hours. Even with zero false
alarms that supports an upper bound of only about 0.75 per hour, seven times
the budget. Demonstrating the 0.1 per hour budget would need roughly **30
hours of held-out** recording — about **480 sessions, four unattended nights**.

So if this arm comes back quiet, the sentence in the write-up is *"the rate is
bounded at 0.75/hour; this campaign cannot distinguish a quiet monitor from a
noisy one"* — **not** *"the monitor met the budget"*. That wording is fixed in
advance in PP-1 precisely so it cannot be softened later.

```bash
python3 physical/code/run_campaign.py plan   --session 10 --healthy 200
python3 physical/code/run_campaign.py record --session 10
```

`make_session_table.py` prints exactly how many more hours are needed, for
whatever you have recorded so far. Use that number rather than this paragraph.

### During the campaign

Nothing. That is the protocol. Do not look inside, do not adjust, do not clean.

---

## P-3 — the degraded sessions (about 8.4 hours, partly attended)

101 sessions with a degradation whose onset was drawn and locked in advance.

### Draw them all first

```bash
python3 physical/code/run_campaign.py plan   --session 20 --degraded 101
python3 physical/code/run_campaign.py status --session 20
```

`status` lists every block, what fault it drew, how severe, when it starts, and
**which ones need somebody in the room**. Two of the four fault types are
imposed by hand.

| Fault | How it is imposed |
|---|---|
| `GAIN_DRIFT` | software, automatic |
| `GEOMETRY_ROTATION` | software, automatic |
| `RATE_LOSS` | **by hand** — slide the neutral density filter in front of the lens |
| `CHANNEL_DROPOUT` | **by hand** — place tape over part of the field |

### Recording an attended block

```bash
python3 physical/code/run_session.py --session 20 --block 7
```

The stimulus prints a countdown — 60, 30, 10, 5 seconds, then **APPLY THE FAULT
NOW**. Have the filter or the tape in your hand before you start. The movement
should take under a second and must not knock the camera.

If you mistime it, **say so in the log and in `--note`**, and record that block
again under a new number:

```bash
python3 physical/code/run_session.py --session 20 --block 7 --note "applied filter ~4 s late"
```

A late fault is not a ruined session — the onset is what was drawn, and a
four-second error is smaller than one analysis window. A *silently* late fault
is a corrupted measurement.

### Leaving the by-hand ones for later

```bash
python3 physical/code/run_campaign.py record --session 20 --software-only
```

records only the automatic ones, unattended. **Come back and do the by-hand
blocks.** Reporting results from only the software faults, without saying so,
would be reporting a benchmark that quietly excludes the harder half of itself.

---

## P-5 — faults nobody designed (about 50 minutes, attended)

Every degradation in P-3, and every one in the computational half, was an
equation someone wrote. Nobody has checked whether *real* degradation looks like
them.

For each intervention: start the recording with `--undesigned`, note the
**exact clock time** you act, cause the fault, and let the recording run to the
end. Then write the onset down straight away.

```bash
python3 physical/code/run_session.py --session 30 --block 1 \
    --undesigned "half-unseated the camera ribbon and re-seated it"
python3 physical/code/note_onset.py --session 30 --block 1 \
    --at-clock 21:47:12 --fault CONNECTOR
```

`run_session.py` prints the clock time the recording started, so keep that
window visible and **write down the time you act while it is happening.** Do not
reconstruct it afterwards from memory.

| Intervention | How | Care |
|---|---|---|
| Connector loosening | half-unseat the camera ribbon, then re-seat it | gently; the connector is fragile |
| Optical attenuation | slide the ND filter in front of the lens | — |
| Contamination | a fingerprint on the **edge** of the lens | clean it afterwards with a lens cloth |
| Mechanical rotation | turn the stage with the stepper motor, recording the angle | hands clear while powered |
| Thermal | hair dryer, **lowest setting, at least 30 cm, no more than 60 s** | component below 50 °C, adult present |

These sessions are analysed in a **separate table** from P-3, by
`analyze_leadtime.py --undesigned`. The onset came from your stopwatch rather
than from a checksummed file, and that is weaker provenance which must not be
silently mixed in. Everything else is identical: the same monitor, the same
threshold, the same code.

**A P-5 session with no noted onset cannot be analysed at all.**
`make_session_table.py` refuses to score it and says so by name — because a
session containing a fault, with nothing on record saying so, would otherwise
land in the fault-free arm and quietly corrupt the false-alarm rate. That is the
single worst thing that could happen to this phase's main measurement, so the
code checks for it rather than trusting the protocol.

If you get an onset wrong, `note_onset.py` refuses to overwrite it. Use
`--replace` **and write in the research log what was wrong and why** — a
silently corrected onset is indistinguishable from an onset adjusted to improve
a result.

If undesigned faults turn out to be meaningfully harder to detect, that is a
finding about how fault benchmarks are built — **including this project's own** —
and it belongs in the write-up as a headline rather than a limitation.

---

## P-4 and P-6 — no recording at all

Both are analyses of the sessions above. P-4 compares the correlation the field
reports against the lead time and false-alarm rate on the same recordings; P-6
re-scores everything at different decision rates. Neither needs the apparatus.

That is what makes this affordable: two of the seven experiments cost minutes.

---

## The research log

One file, appended to, never edited. For each session or run, record:

- date and time
- session and block numbers
- what was drawn (the script prints it)
- the temperature
- anything at all that was unusual — including mistakes

The session log (`physical/data/raw/SESSION_LOG.csv`) is written automatically
and records every setting. It does **not** record that you sneezed on the lens
at block 43. That is what the written log is for, and three weeks later it is
the only thing that will explain an odd result.

---

## If time runs short

Cut in this order: **P-5, then P-6, then P-3 severities.**

Do not cut P-2. It is the measurement that does not exist anywhere else, it is
the one that runs while you sleep, and every other result in the phase is
reported against the threshold it produces.
