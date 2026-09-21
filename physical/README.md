# The physical-validation phase

Everything in this folder builds and runs an apparatus that can measure
something the archived human recordings cannot: **how early a decoder-health
monitor warns, and how often it warns when nothing is wrong.**

Both numbers need failures whose start times were fixed before the recording
existed, and many hours of genuinely fault-free recording. Human brain-implant
recordings have neither. A sealed box with a screen and a camera has both.

---

## If you just want to know what to do next

**[`docs/12_RUNBOOK.md`](docs/12_RUNBOOK.md)** — every step, in order, from
"nothing bought yet" to "results in hand". Numbered, with the command for each
step and what success looks like. Tick the boxes as you go.

Everything else in this folder explains *why*. That one is the order.

## Read in this order

| | Document | What it is for |
|---|---|---|
| 00 | [`docs/00_WHY_THIS_PHASE_EXISTS.md`](docs/00_WHY_THIS_PHASE_EXISTS.md) | The argument. What is new, what is not, and an honest account of what already exists. **Start here.** |
| 01 | [`docs/01_RESEARCH_DESIGN.md`](docs/01_RESEARCH_DESIGN.md) | An audit of the old design, the new hypothesis, the variables, and the limitations written in advance |
| 02 | [`docs/02_EXPERIMENTS.md`](docs/02_EXPERIMENTS.md) | The six experiments P-1 to P-6, what each tests, and what every outcome would mean |
| 03 | [`docs/03_MATERIALS_AND_SAFETY.md`](docs/03_MATERIALS_AND_SAFETY.md) | What to buy, why each item, and the safety assessment |
| 04 | [`docs/04_BUILD.md`](docs/04_BUILD.md) | From an empty box to a calibrated apparatus, assuming no prior knowledge |
| 05 | [`docs/05_SOFTWARE.md`](docs/05_SOFTWARE.md) | Every script: what it does, what it needs, what it produces |
| 06 | [`docs/06_DATA_COLLECTION.md`](docs/06_DATA_COLLECTION.md) | What to do on each recording day |
| 07 | [`docs/07_ANALYSIS.md`](docs/07_ANALYSIS.md) | What to run, and what each result would and would not license you to claim |
| 08 | [`docs/08_WHAT_COMES_AFTER.md`](docs/08_WHAT_COMES_AFTER.md) | What, if anything, gets built afterwards — decided by result, written before the results exist |
| 09 | [`docs/09_PREREGISTRATION.md`](docs/09_PREREGISTRATION.md) | **The predictions, with numbers attached, and the freeze procedure.** Draft — must be read, edited and frozen by the researcher before anything is built |
| 10 | [`docs/10_TROUBLESHOOTING.md`](docs/10_TROUBLESHOOTING.md) | **When something goes wrong** — every situation, by when it happens, with the command that fixes it |
| 11 | [`docs/11_SHOPPING_LIST.md`](docs/11_SHOPPING_LIST.md) | **What to buy, in the order to buy it** — search terms, costs, and what can be substituted or skipped |
| 12 | [`docs/12_RUNBOOK.md`](docs/12_RUNBOOK.md) | **The checklist.** Every step from parts to results, in order, with the command for each |

`data/_FOLDER_NOTES.md` explains what lives where and what is committed.

---

## The apparatus, in one paragraph

A screen shows a grid of grey patches. Each patch brightens and dims with a
direction the computer chose, the way a direction-tuned brain cell fires faster
for its preferred direction. A camera in a sealed dark box watches the screen,
and each small region of its image is one "channel", standing in for one
electrode. A decoder learns to read the direction back out. Then the system is
degraded on purpose — a filter over the lens, tape across part of the field, the
stage rotated — **at a moment drawn at random and locked under a checksum before
the recording existed.**

That last clause is the whole point. It is the one property no human recording
has, and without it neither lead time nor false-alarm rate has a fixed value.

---

## Try the whole thing today, with no hardware

```bash
python3 physical/code/monitor.py --selftest
python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8 --undesigned 4 --orphans 2
python3 physical/code/make_session_table.py --raw physical/data/dryrun/raw --tag _dryrun
python3 physical/code/analyze_falsealarm.py --tag _dryrun
python3 physical/code/analyze_leadtime.py --tag _dryrun
python3 physical/code/analyze_leadtime.py --tag _dryrun --undesigned
rm -rf physical/data/dryrun
```

That manufactures fake recordings and runs the entire analysis chain on them.
**No number it produces is a result** — the fakes come from a formula, not from
an apparatus. It answers one question: does the chain run?

`--orphans 2` deliberately makes two broken sessions: undesigned faults whose
onset was never written down. The table builder should name them and throw them
out. If it ever stops doing that, a session containing a fault would land in the
fault-free arm and corrupt the false-alarm rate, so it is worth checking that
the check still works.

---

## Every recording day, before you start

```bash
python3 physical/code/health_check.py
```

One second. It checks that every drawn plan still matches its checksum, that
every recording is complete, that the apparatus has not drifted since
calibration, and that the disk will hold the rest of the campaign. **Almost
everything that can go wrong with a campaign produces recordings that look
fine**, which is why this is a daily habit rather than a thing you run when
suspicious.

## Once the apparatus exists

```bash
# calibrate
python3 physical/code/run_session.py --session 0 --block 1 --calibration
python3 physical/code/bench.py check --session 0 --block 1

# record
python3 physical/code/run_campaign.py plan   --session 10 --healthy 101
python3 physical/code/run_campaign.py record --session 10

# analyse
python3 physical/code/make_session_table.py
python3 physical/code/analyze_falsealarm.py
python3 physical/code/analyze_leadtime.py
python3 physical/code/analyze_leadtime.py --undesigned
python3 physical/code/analyze_correlation.py
python3 physical/code/analyze_decision_rate.py

# draw everything
python3 physical/code/figures.py all
```

---

## Five things not to do, four of which the code enforces

**Record a session without deciding its outcome first.** `run_session.py`
refuses unless `draw_onset.py` has already drawn and checksummed a plan. An
onset chosen after the fact is an onset the analyst can adjust, and then lead
time is a matter of opinion.

**Re-draw a plan.** `draw_onset.py` refuses to overwrite one. Re-drawing after
seeing a recording is exactly the tampering the checksum exists to prevent.

**Start recording data before the predictions are frozen.** Not enforced by
code — this one is on you. `docs/09_PREREGISTRATION.md` §10 is the procedure,
and the commit timestamp on the freeze is what makes every "we predicted this
beforehand" checkable rather than asserted. Calibration sessions are fine
before the freeze; nothing that counts as data is.

**Overwrite raw data.** `run_session.py` refuses to record into a folder that
already holds a recording, and nothing in the analysis writes to
`physical/data/raw/` at all.

**Score a hand-caused fault whose onset was never written down.**
`make_session_table.py` names it and excludes it. Nothing on record would say a
fault happened, so every other piece of code would read it as healthy and put it
in the fault-free arm — which would quietly corrupt the one measurement this
phase exists to make.

---

## No human participants

Nobody is a subject of this research at any stage, including the researcher.
Nobody is recruited, surveyed, interviewed, photographed, recorded or measured.
The camera is inside a closed box pointing at a screen; no person is ever in its
field of view or a source of data. See `docs/03_MATERIALS_AND_SAFETY.md` §3.1.
