# The Build Manual

> ## SUPERSEDED 20 September 2026
>
> **This is no longer the build manual** for the physical phase. Read **`physical/docs/04_BUILD.md`** instead.
>
> This file is kept because it carries more depth on some hardware steps — the Raspberry Pi setup and the enclosure in particular — and because the apparatus it builds is the same one. What changed is the experiments run on it, not the box.
>
> **Do not mix the two.** The programs in `rig/` and the programs in
> `physical/code/` each keep their own `preferred_directions.npy` — the file
> that decides which patch on the screen is which channel. Recordings made with
> one set cannot be compared with recordings made with the other, and nothing in
> the data would reveal that they had been mixed. Pick one and stay in it; for
> anything recorded from 20 September 2026 onward, that is `physical/code/`.

---

**Everything needed to finish this project without further help.**

This assumes you have never soldered anything, never used a Raspberry Pi, and
have forgotten what every script in this repository does. It starts from
nothing. Where a step depends on something already established computationally,
it names the file so the connection can be checked rather than taken on trust.

Read Part 0 and Part 1 before buying anything.

---

# PART 0 — What is being built, and why it matters

## 0.1 The device, in one sentence

**A session-level decoder-health monitor, and the benchtop instrument that
measures how good it is.**

The monitor answers one question, once per session: *should this session be
flagged for a recalibration check?* The instrument measures the two numbers about
that monitor which cannot currently be measured anywhere — how often it catches a
degrading session, and how often it wrongly flags a healthy one.

Feed it a recording from any many-channel sensor. It returns three numbers and a
verdict:

| Output | Meaning |
|---|---|
| Effective independent samples per session | How much genuinely independent evidence one recording session contains |
| Lead time at the chosen false-alarm budget | How far ahead of a failure a warning can arrive |
| False alarms per hour at that lead time | What that warning costs when nothing is wrong |
| **Verdict** | **Monitorable / not monitorable at this budget** |

It is a measuring instrument, not a monitor. That distinction is the whole
project and it is worth being precise about at the fair.

## 0.2 Why this is the honest deliverable

The computational half of this project asked whether a decoder-health monitor
can warn before a brain-computer interface fails. Across 48 configurations, none
passed all five gates (`reports/BENCHMARK_SUMMARY.md`). The binding constraint
was not detection — several configurations warn before performance falls — it
was **specificity**: the risk signal is never quiet during healthy operation, so
any threshold low enough to catch a fault early also fires constantly when
nothing is wrong.

**Then the arithmetic behind that failure was worked out, and it changed the
problem.** A budget of 0.1 false alarms per hour, divided among **720 decisions
an hour**, demands a per-decision false-positive rate of 0.00014 — needing a
per-window AUC of **0.9992** against an observed 0.693. Put that beside the
finding that a faulted session holds roughly **one independent measurement**: the
monitor was making 720 decisions an hour out of one measurement's worth of
evidence.

That is a sampling-rate problem, not a detector problem, and it was
self-inflicted. Asked **once per session** instead, the same detector needs an
AUC of **0.933** to flag 80% of degrading sessions while wrongly flagging 10% of
healthy ones. It currently reaches **0.673** (T11) and **0.742** (T5).

> **0.933 is superseded.** It is the AUC needed at a 10% false-flag rate, which at one decision per episode is about thirteen times this project's 0.1/hour budget. Derived from the budget the target is **0.990**. Corrected 20 September 2026; see `reports/OPERATING_POINT_BOUND.md`. This document is kept unchanged as the record.

**That is the difference between "this cannot work" and "this needs to be about
this much better", and only the second is something to build.**

### The number nobody can currently measure

The false-flag rate is half of what decides whether such a monitor is worth
deploying, and **it cannot be estimated from the archived data at all.**
Restricted to genuinely fault-free episodes that data offers **17 and 15
episodes — about 1.4 hours.** Measuring a 10% false-flag rate to within a third
of itself takes about **101 healthy sessions, 8.4 hours**; measuring 2% takes
45 hours.

No BCI participant can sit through two hundred sessions so somebody can estimate
a false-alarm rate. **A box with a camera in it can run unattended for a
fortnight.** That is the argument for building this, and it is a far better one
than the argument it was originally built on.

This matters for the engineering category specifically. The deliverable is a
working physical device with a specification, a calibration procedure, a
validation protocol and measured performance — which is what an engineering
project is. It is not a demonstration of a principle, and it is not a model.

## 0.3 Why anyone outside this project should care

**The question nobody can currently answer.** Every implanted medical device has
to answer one question before it can be a regulated product: *how do you know it
is still working?* A pacemaker that stops has an obvious signature. A neural
decoder that has drifted keeps producing confident output and is merely
increasingly wrong. There is no accepted way to detect that, and — more
importantly — **no accepted way to test whether a proposed way works.** A field
cannot certify what it cannot measure.

**The scale.** About 5.4 million Americans, roughly one in fifty, live with
paralysis; 41.8% are unable to work, and stroke and spinal cord injury account
for 61% of cases (Armour et al., 2016). Implanted brain-computer interfaces are
aimed at the most severely affected of that group.

**The bottleneck is not surgery.** Across 14 BrainGate participants and 20
implanted arrays, the share of electrodes recording usable activity fell from
41% in the first three months to 34% in the last, and 3 of the 20 arrays stopped
producing consistent decoding signals altogether (Hahn et al., 2025). Keeping a
decoder working through that requires recalibration, and a 2026 systematic
review of 58 studies found it still generally requires a specialist research
team (Swanson et al., 2026).

**Where the money is.** Recalibration currently runs on a calendar, not on
evidence. Every scheduled session that was not needed is specialist time spent
for nothing, and every drift that happens between sessions is a person using a
device that has quietly stopped matching their brain.

A transparent model of that cost, with every assumption stated so it can be
argued with:

| Assumption | Value | Where it comes from |
|---|---|---|
| Recalibration sessions per user per year | 24 (roughly fortnightly) | An assumption. Vary it. |
| Staff time per session | 2 hours, 2 people | An assumption from the supervised-session descriptions in Swanson et al. |
| Fraction that evidence-based triggering could avoid | 50% | **An assumption, and the one this project cannot yet support.** It is what the instrument would let somebody measure. |
| Sessions avoided per user per year | 12 | 24 × 50% |
| Specialist hours returned per user per year | 48 | 12 × 2 × 2 |

The point of the table is not the total. It is that **every cell except the
third is a known quantity, and the third is exactly what has no measurement
behind it.** That missing number is the gap this instrument is built to make
measurable. Present it that way and it is honest; present it as a dollar saving
and a judge will rightly ask where the 50% came from.

**The part that outlasts the project.** Once a shared way to measure
monitorability exists, every competing system can be measured against it instead
of against its own best case, and the next group's improvement becomes provable
rather than asserted. That is how a research area turns into an engineering
discipline.

## 0.4 What is explicitly not claimed

- This is not a medical device. It is a bench instrument.
- Nothing is tested on a person. There are no human participants at any stage.
- No clinical benefit is demonstrated.
- The camera is not a brain. The claim under test is about a *class of
  measurement problem* — many channels, drifting slowly — not about biology.

---

# PART 1 — How the computational work connects to the physical work

Nothing in Part 4 onward is a new idea. Every physical test exists because a
specific computational result raised a specific question that software could not
settle. This table is the spine of the project; if a judge asks "why are you
building this?", the answer is a row of it.

| # | What was found computationally | Where it lives | The question it leaves open | The physical test |
|---|---|---|---|---|
| 1 | A **faulted** session contains roughly one independent measurement; lag-1 autocorrelation 0.995. **Fault-free it is 0.893, for 3.12 effective samples** | claim C04 (amended 19 Sep), `reports/AUTOCORR_BY_SEVERITY.md` | Is either figure a fact about brains, or about any slowly drifting many-channel sensor? | **B-9**: measure the same quantity on the rig, against the fault-free figure |
| 2 | That autocorrelation survives removing all window overlap (0.902 / 0.784) | claim C18, `reports/WINDOW_SPACING.md` | — | — |
| 3 | **But those figures are pooled over episodes carrying an injected fault ramp. Fault-free, it is 0.085 (T11) and 0.435 (T5)** | `reports/AUTOCORR_BY_SEVERITY.md` | The rig's natural-drift arm injects nothing, so which number is it compared against? | **Resolved 19 Sep**: the fault-free figures. `RIG_PREREGISTRATION.md` §12 |
| 4 | The lag-1 estimator saturates near 0.60 at 10 windows, so 0.902 cannot be inverted to a drift speed | `reports/AUTOCORR_BY_SEVERITY.md`, `reports/DRIFT_SWEEP_DESIGN.md` | How long must a rig block be for its number to be comparable? | **B-8**: match block length to window count, not to duration |
| 5 | 0 of 48 configurations passed all five gates; the binding gate is silence, not detection | `reports/BENCHMARK_SUMMARY.md` | Does the same gate bind on hardware? | **B-11**: run the identical gate battery on rig recordings |
| 6 | Injected faults are equations applied to recorded numbers; nobody checked whether real degradation resembles them | `research/RIG_PREREGISTRATION.md` P-R6 | Do faults I cause but did not design look like the ones I invented? | **B-12**: undesigned physical faults, reported in a separate table |
| 7 | Decoder error, trace noise and task geometry all move together in the archive; a claim had to be withdrawn because they could not be separated | claim register, WITHDRAWN entry | Can they be separated when one is held fixed by hand? | **B-13**: cross one variable against another on the rig |
| 8 | Monitorability depends on drift speed, and the sweep needs 5 levels × 53 blocks ≈ 22 h | `reports/DRIFT_SWEEP_DESIGN.md` | What does the curve actually look like? | **B-14**: the drift sweep |
| 9 | **The rig as originally specified decodes perfectly (0.0° vs 89° chance) and no fault can move it** | `reports/RIG_DIGITAL_TWIN.md` | — | **Fixed before building.** Calibration is now B-7 |
| 10 | **The calibrated stimulus asks for half a brightness level, which a screen cannot emit** | `reports/RIG_DIGITAL_TWIN.md`, `rig/stimulus.py` | Does spatial dithering deliver it on real hardware? | **B-6**: measure the dither with the camera |
| 11 | **The budget was applied at 720 decisions/hour, demanding AUC 0.9992. Once per session it needs 0.933; the monitor reaches 0.673–0.742** | `reports/OPERATING_POINT_BOUND.md` | Can a session-level monitor close that gap? | **B-14**: the session-level monitor study — now the centrepiece |


> **0.933 is superseded.** It is the AUC needed at a 10% false-flag rate, which at one decision per episode is about thirteen times this project's 0.1/hour budget. Derived from the budget the target is **0.990**. Corrected 20 September 2026; see `reports/OPERATING_POINT_BOUND.md`. This document is kept unchanged as the record.

| 12 | **The false-flag rate cannot be estimated from archived data: 17 and 15 fault-free episodes, ~1.4 hours** | `reports/AUTOCORR_BY_SEVERITY.md` | What is it actually? | **B-14**: 101 healthy sessions, which no participant could sit through |

Rows 9 and 10 are the two that would have wasted the most time. Both were caught
by simulating the rig in `scripts/72_rig_digital_twin.py` instead of building
it, which is the reason Part 2 exists.

## 1.1 The same analysis runs on both halves — that is the point

The rig is only a comparison if it is analysed identically. **No script is
modified to accommodate it.** The rig's recordings are converted into the same
file format the neural loader already reads (`rig/to_mat.py`), given a
participant label of the `RIG` form, and handed to the same pipeline:

```
scripts/17_fault_injector.py    →  same four fault modes, same onset locking
scripts/18_reference_decoder.py →  same ridge decoder, same measured chance
scripts/20_evaluation_harness.py→  same 30 s windows stepping 5 s
scripts/21_score_report.py      →  same five gates, same 0.1/hour budget
```

This was rehearsed end-to-end on a synthetic fixture in
`scripts/68_rig_pipeline_dryrun.py`, which found three real pipeline bugs and
four malformed documented commands before any hardware existed. Run it again
before the first real recording:

```
python3 scripts/68_rig_pipeline_dryrun.py
```

If it does not print PASS, stop and fix that before recording anything.

## 1.2 You do not have to write any code

Every program the physical work needs is already written and in the repository.
`research/RIG_CODE.md` is the index: what each one is for, the exact commands for
a typical session, a fallback table for when something misbehaves, and the full
source of every file inline in case one is ever lost.

The one command you will type most:

```
python3 rig/run_block.py --session 1 --blocknum 1
```

That records one block end to end — stimulus, camera, conversion — and appends
every setting used to `rig/blocklog.csv`. Add `--dry-run` to see what it would
do without any hardware attached.

---

# PART 2 — Gates to clear before spending any money

Do these in order. Each is a stop-or-go. They cost nothing and they exist
because two of them have already caught design faults that would have been
expensive to find on the bench.

### GATE 1 — The pipeline runs end to end on fake data

```
python3 scripts/68_rig_pipeline_dryrun.py
```
**Expect:** `PASS`. It builds a synthetic six-day fake participant, runs the
real loader, injector, decoder, harness and scorer over it, then deletes
everything it made.
**If it fails:** the failure is in the shared pipeline, not the rig. Fix it
before going further — every later result depends on this working.

### GATE 2 — The rig design is not too easy

```
python3 scripts/72_rig_digital_twin.py
```
**Expect:** section 1b reports `Matched`, and all four faults show `yes` under
"Ladder rises".
**Why it matters:** the original design decoded to 0.0° of error where cortex
sits at 54.6°. A rig that good measures difficulty, not neurons, and no fault
can move it. If this stops saying `Matched` after any change to `rig/`, the
change broke the comparison.

### GATE 3 — The two calibration settings are actually in the rig code

```
grep -n "depth" rig/stimulus.py | head -3
grep -n "default=48" rig/capture.py
```
**Expect:** `--depth` defaulting to about `0.00211`, and a capture width of 48.
**If either is missing:** the built rig will not match the simulated one and
Gate 2's result does not apply to it.

### GATE 4 — The preregistration is settled (**DONE — 19 September 2026**)

This gate was blocking the build. It is now closed, and this is what it closed
with, so it can be explained at the fair without re-deriving it.

P-R1 and P-R2 both took their thresholds from claim C18's pooled 0.902 and
0.784. Those turned out to be raised by the sub-threshold fault ramp injected
into those episodes, not measured on fault-free recording. Fault-free, the same
measurement gives **0.085** on T11 and **0.435** on T5. So the old P-R1 bar of
"≥ 0.70, just below both" sat *above* both, and P-R2's "fewer than 2 effective
samples" pointed the wrong way — fault-free gives 8.44 and 2.75.

**Both were retargeted to the fault-free figures** (`RIG_PREREGISTRATION.md`
Amendment 1, §12; the original wording is preserved there):

| | Now predicts | Falsified if |
|---|---|---|
| **P-R1** | fault-free non-overlap r between **−0.12 and +0.54** | outside that band |
| **P-R2** | faulted r exceeds fault-free r by **≥ 0.20** | the rise is under 0.20, absent, or negative |

**What to say if a judge presses on this.** P-R1 is a wide band and therefore
weak — it rests on 17 episodes on T11 and 15 on T5, with intervals wide enough
to cover most of the plausible range. It rules out a rig pinned at zero or at
its ceiling and little else. That weakness is exactly why P-R2 was rewritten to
test the *mechanism* rather than the level: the rise from fault-free to faulted
is large (+0.838 on T11, +0.390 on T5), in the same direction on both
participants, and measured on hundreds of episodes rather than seventeen. **P-R2
is the prediction that carries the weight.**

Verify it is in place before building:
```
grep -n "between \*\*−0.12 and +0.54\*\*" research/RIG_PREREGISTRATION.md
```

### GATE 5 — Every claim still verifies

```
python3 scripts/31_verify_claims.py
python3 scripts/55_reproducibility_audit.py
python3 -m pytest tests/ -q
python3 tools/mutation_check.py
```
**Expect:** all four pass. This is the project's standing rule before any
commit, and it applies here too.

**Only after all five gates pass, order parts.**

---

# PART 3 — Buying the parts

The full list with specifications is in `research/RESEARCH_PLAN_2026-09-15.md`
under Materials and Equipment, items 6–19. About $150, or about $110 if a spare
screen already exists.

Three notes that are easy to get wrong:

1. **Raspberry Pi 4 Model B, 4 GB.** Not a Pi Zero (too slow for 50 fps
   capture), not a Pi 5 unless you are willing to debug camera-stack
   differences. The 4 GB version, specifically.
2. **Camera Module 3, with the ribbon it ships with.** The Pi 4's camera
   connector is the older wider type; Camera Module 3 ships with the right
   cable, but a cable bought separately may be the narrower Pi-5/Zero kind and
   will not fit.
3. **A screen whose brightness can be set and left alone.** Anything with
   automatic brightness, ambient-light adjustment or a power-saving dimmer will
   silently cancel the degradation being measured. A cheap monitor with manual
   controls beats a modern laptop here.

---

# PART 4 — Building it, step by step

Nothing here requires soldering. If a step mentions a tool you do not have, stop
and get it rather than improvising — several steps depend on the enclosure being
genuinely light-tight, and improvised versions usually are not.

## 4.1 Prepare the Raspberry Pi

**Step 1.** Download the Raspberry Pi Imager from `raspberrypi.com/software` on
your normal computer and install it.

**Step 2.** Put the microSD card into your computer. Most laptops need a USB SD
adapter; if yours does not have a slot, that adapter is the one part not on the
list.

**Step 3.** Open the Imager. Choose:
- *Raspberry Pi Device*: Raspberry Pi 4
- *Operating System*: Raspberry Pi OS (64-bit)
- *Storage*: your SD card

**Step 4.** Before clicking Write, click the gear icon for advanced options and
set: a hostname (`bcirig` is fine), enable SSH, set a username and password, and
enter your wifi name and password. Writing these now saves needing a keyboard
and monitor attached to the Pi later.

**Step 5.** Click Write and wait. It takes a few minutes. When it finishes,
remove the card.

**Step 6.** Put the card into the Pi. The slot is on the underside of the board
at the end opposite the USB ports. It only goes in one way.

**Step 7.** Plug in the official USB-C power supply. A red light comes on and a
green light flickers. Wait two minutes for the first boot.

**Step 8.** From your normal computer, open a terminal and connect:
```
ssh bcirig@bcirig.local
```
Type the password you set. If `bcirig.local` does not resolve, find the Pi's IP
address in your router's device list and use that instead.
*Expect:* a prompt ending in `$`. You are now typing commands on the Pi.

**Step 9.** Update it and install what the rig needs:
```
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 python3-pygame python3-numpy python3-scipy git
```
This takes 10–20 minutes. `picamera2` is the camera library, `pygame` draws the
stimulus, the other two do the maths.

**Step 10.** Get this project onto the Pi:
```
cd ~
git clone https://github.com/gnair40/bci-ews-research.git
cd bci-ews-research
git checkout claude/isef-research-pipeline-9zt4uq
```

**The `git checkout` line is not optional.** A plain clone lands on `main`, which as of 24 September 2026 is the repository as it stood on 16 August — four files, no `physical/`. Every command after this one would fail. See `physical/docs/12_RUNBOOK.md` step 0.1.

## 4.2 Attach the camera

**Step 11.** Shut the Pi down completely before touching the camera connector:
```
sudo shutdown -h now
```
Wait until the green light stops flickering, then unplug the power. **Do not
connect the camera with power applied.**

**Step 12.** Find the camera connector: a thin black slot between the HDMI ports
and the headphone jack, labelled CAMERA.

**Step 13.** Lift the connector's tab. Grip the black plastic tab at both ends
and pull gently upward about 2 mm. It stays attached and moves only a little.

**Step 14.** Insert the ribbon cable with the **silver contacts facing the HDMI
ports** and the blue plastic stiffener facing the USB ports. Push it in until it
is square and no silver shows.

**Step 15.** Press the tab back down until it clicks. Tug the cable very gently;
it should not move.

**Step 16.** Power the Pi back up and confirm the camera is seen:
```
rpicam-hello --list-cameras
```
*Expect:* a line naming an `imx708` sensor.
*If nothing is listed:* power down, reseat the ribbon at both ends, and try
again. A cable inserted backwards or not fully seated is by far the most common
cause.

## 4.3 Build the enclosure

The enclosure's only job is to make the camera see the screen and nothing else.
Stray light is not a nuisance here — it is a signal that varies with the room
and swamps a modulation of half a brightness level.

**Step 17.** Take the cardboard box (at least 40 × 30 × 30 cm) and cut off any
flaps that do not form the lid.

**Step 18.** Line every interior surface, including the inside of the lid, with
matte black paper or paint. Matte, not glossy: glossy black reflects, which is
the problem you are solving.

**Step 19.** Cut a window in one end just large enough for the screen's display
area. The screen sits outside the box facing in, with the box's edge overlapping
the bezel.

**Step 20.** Tape the screen to the box around all four edges with black tape.
Press along every edge. Any gap is a light leak.

**Step 21.** Mount the camera on the tripod or bracket at the opposite end,
pointing at the screen, centred, as square to it as you can manage.

**Step 22.** Set the distance so the whole patch grid fills the camera's view
with a small margin. You will check this properly in B-1.

**Step 23.** Cut a small hole for the camera ribbon and the power cable, then
tape around them. Cables are the light leak people forget.

**Step 24.** Mount the temperature and humidity sensor inside, away from the
screen. Wire it to the Pi's GPIO pins with three jumper wires: VCC to pin 1
(3.3 V), GND to pin 6, DATA to pin 7. The breakout board is labelled.

**Step 25.** Close the lid and tape it. Work in the dimmest room you have and
look for light leaking out — if light escapes, light gets in.

---

# PART 5 — Bench validation, with a fallback for every failure

Run these in order. **Each has a pass condition and a written fallback**, because
the most likely way this project fails is not that a test comes out negative —
that would be a result — but that a test comes out ambiguous and there is no
plan, at 11pm, a week before the fair.

Record every run in `research/research_log.md`, including the ones that fail.

---

## B-1 — Can the camera see the screen at all?

```
cd ~/bci-ews-research
rpicam-still -o /tmp/check.jpg --width 640 --height 480 --timeout 2000
```
Copy it to your own computer to look at it:
```
scp bcirig@bcirig.local:/tmp/check.jpg .
```

**Pass:** the patch grid fills most of the frame, is in focus, and is not cut
off at any edge.

**If it is out of focus:** Camera Module 3 autofocuses. Lock it to the screen
distance with `rpicam-still --autofocus-mode manual --lens-position N`, trying
N from 0 upward; larger N is nearer.

**If it is cut off or crooked:** move and re-aim the camera, then repeat. Do not
correct it in software later — a rotation you did not intend is
`GEOMETRY_ROTATION` and it would contaminate the fault you inject deliberately.

**If the image is black:** the screen is off, asleep, or the box is on the wrong
way round. Check the screen is showing something before blaming the camera.

---

## B-2 — Is the box actually light-tight?

With the screen **off** and the lid closed:

```
python3 rig/bench.py darkframe
```

**Pass:** it prints PASS — mean below about 2 counts and max below about 5.

**If it fails** it tells you what to do. In short: re-tape the cable hole, then
the lid, then the screen bezel, in that order of likelihood. Turn the room
lights on and off while re-running; if the mean changes, light is getting in.

**Fallback if you cannot seal it:** the command saves `rig/darkframe.npy`.
Subtract it from every recording, and **write that down as a deviation** — a
subtracted offset is not the same as no offset when you are measuring drift.

---

## B-3 — Does the stimulus program run?

```
cd ~/bci-ews-research
python3 rig/stimulus.py --frames 500 --out /tmp/stim_test.csv
```

**Pass:** a grey field appears on the screen, runs for about 10 seconds, and
`/tmp/stim_test.csv` has 500 rows.

**It will look like a uniform grey rectangle, and that is correct.** The
modulation is about half a brightness level out of 255. If you can see the
individual patches by eye, the depth is wrong — check Gate 3.

**If pygame complains about no display:** you are connected over SSH with no
screen attached to the Pi. Either attach the screen to the Pi's HDMI and run
from a keyboard, or set `export DISPLAY=:0` first. The screen must be driven by
the Pi itself.

**If it runs slower than 50 fps:** lower `--patch` to 30 and re-run. Frame rate
matters because the camera and stimulus must agree; B-5 checks this.

---

## B-4 — Does the capture program run?

Run the stimulus in one SSH window and this in a second:
```
cd ~/bci-ews-research
python3 rig/capture.py --frames 500 --out /tmp/cap_test.npy
```

**Pass:** it prints a shape of `(500, 384)`.

**If it is slower than the stimulus:** reduce `--fps` on both to 30 and record
that you did. The number only has to match between the two programs and stay
fixed for the whole study.

---

## B-5 — Do the stimulus and the camera agree about time?

This is the test most likely to be skipped and most likely to matter. If the
camera lags the screen, every frame is labelled with the wrong heading and the
decoder will look broken for a reason that has nothing to do with the rig.

Record one block, then:

```
python3 rig/bench.py lag --cap rig/cap_s1_b1.npy --stim rig/stim_s1_b1.csv
```

It prints a table of agreement against shift and names the best lag. It finds
the answer from the signal itself — the predicted tuning of every channel is
known from the logged heading, so the lag is whichever shift makes prediction
and measurement agree best. No clocks involved.

**Pass:** the best lag is within 3 frames.

**If it is larger but stable:** repeat on two more blocks. If they agree, pass
it to every future recording as `--lag <seconds>` and record it in the log. A
fixed, measured, documented offset is fine. An unmeasured one is fatal.

**If it is not stable between blocks:** drop both programs to 25 fps and repeat.

**B-5b, the robust alternative:** abandon frame-level alignment entirely. Hold
each heading for 5 seconds instead of 2 (`--hold 250`) and analyse only the
middle 3 seconds of each hold. It costs trials and removes the timing problem
completely.

---

## B-6 — Does the dither actually deliver a fraction of a brightness level?

The calibrated stimulus asks each patch to swing by about half of one brightness
level. A screen emits whole levels only. `rig/stimulus.py` solves this by
spatial dithering — mixing two adjacent levels within a patch — and this test
checks the camera can actually see the result. **If this fails, nothing after it
means anything.**

Record one block, then:

```
python3 rig/bench.py dither --cap rig/cap_s1_b1.npy --stim rig/stim_s1_b1.csv
```

**Pass:** the median per-channel correlation with the predicted tuning is
clearly positive, and it is positive for nearly every channel. The number will
be **small** — that is the point of the calibration — but it must be consistent.

**If it fails**, the command lists the fixes in order of likelihood. In short:
the screen is applying its own processing (turn off dynamic contrast, every
"enhancement", and every power-saving dimmer); then try `--exposure 16000`;
then try a different screen, since many cheap panels are really 6-bit with
their own internal dithering.

**Last-resort fallback:** raise `--depth` fourfold and **re-run
`python3 scripts/72_rig_digital_twin.py` at the new value** to find out what
operating point you are now at. You will no longer be matched to cortex, and
every comparison must say so. Try the three fixes above first.

---

## B-7 — Calibrate the rig to cortex's difficulty

**This is the most important step in the build, and it did not exist in the
original plan.** It was added after `scripts/72_rig_digital_twin.py` showed that
the rig as specified decodes perfectly (0.0° against 89° chance) where cortex
manages 54.6° against 90.7°. A rig that good measures difficulty, not neurons.

Record one full 5-minute block, convert it, fit the decoder, and read off the
error and the measured chance level:

```
python3 rig/run_block.py --session 1 --blocknum 1
python3 rig/bench.py margin --cap rig/cap_s1_b1.npy --stim rig/stim_s1_b1.csv
```

**Pass:** the margin (chance minus error) is within about 6° of **36.1°**, which
is T11's margin (54.6° error against 90.7° chance, from
`data/processed/reference_decoder.json`).

**If the margin is much larger — the rig is too easy:** lower `--depth`. Halving
it roughly doubles the error. Re-run and re-measure.

**If the margin is much smaller — the rig is too hard:** raise `--depth`, or
raise `--exposure`, or average more pixels per channel by raising the capture
size back toward 96 × 64.

**Why match the margin and not the error:** the two systems have different
chance levels (90.7° on T11, whatever the rig measures). Equal error against
unequal chance would not be equal difficulty.

**Record the final `--depth` in the log and never change it again.** Every later
recording must use the same value, or the blocks are not comparable to each
other.

---

## B-8 — Fix the block length by window count, not by minutes

The lag-1 estimator is badly biased at short series: fed a signal whose true
correlation is 0.999, it reports about 0.60 at ten windows
(`reports/AUTOCORR_BY_SEVERITY.md`). The size of that bias depends on how many
windows there are, so a rig block and a neural episode are only comparable if
they yield the **same number of windows**.

T11 episodes keep **10** windows at the non-overlapping spacing; T5 keep **7**.
A 15000-frame block at 50 fps gives 55 windows, or 9 after decimation — close to
T11.

**Pass:** your recorded block yields 9 or 10 decimated windows.

**If it yields a different number:** change the frame count, not the window
geometry. The window geometry is shared with the neural analysis and changing it
would break the comparison in a way that is much harder to see.

---

## B-9 — The main comparison: how much independent evidence is in a session?

Gate 4 settled what this is judged against: **P-R1**, a fault-free non-overlap r
between −0.12 and +0.54, and **P-R2**, a faulted-minus-fault-free rise of at
least 0.20.

Record 10 healthy blocks with nothing injected. Then:
```
python3 scripts/66_window_spacing.py
```
**Read the non-overlap row**, not the overlapping one. Compare against the
**fault-free** neural figures (0.085 on T11, 0.435 on T5) from
`reports/AUTOCORR_BY_SEVERITY.md`, never against the pooled 0.902 and 0.784.

**Both outcomes are publishable, which is why this is worth doing:**
- Rig looks like cortex → the limit generalises beyond brains, to sensor health
  monitoring in general. The stronger result.
- Rig does not → the failure is neural-specific, and the next attempt at a
  neural monitor needs a neural-specific fix rather than better statistics.

---

## B-10 — Does the rig produce a severity ladder?

For each of the four fault modes, record blocks at severities 0, 0.25, 0.5 and
1.0. Check that decoding error rises monotonically with severity.

**Pass:** all four rise. The twin predicts rises of +12.6° (`RATE_LOSS`), +14.5°
(`CHANNEL_DROPOUT`), +35.0° (`GAIN_DRIFT`) and +36.0° (`GEOMETRY_ROTATION`).

**If a mode does not rise:** that mode is unusable and **must be reported as
unusable rather than quietly dropped.** A ladder that does not rise is a bug
this project has already had once, in `scripts/17_fault_injector.py`, where
`CHANNEL_DROPOUT` drew independent channel sets per severity and ran backwards.

**If `GEOMETRY_ROTATION` is the one that fails:** the likely cause is that a
whole-grid roll is not what a physical rotation does — a real rotation also
blurs and crops the edges. Use the stepper motor to rotate the stage physically
instead of rolling the channel indices, and record the angle you turned.

---

## B-11 — Run the five gates on rig data

```
python3 scripts/20_evaluation_harness.py run --participant RIG1
python3 scripts/21_score_report.py --participant RIG1
```

**Pass:** the report is produced. **There is no "good" answer here** — the whole
point is to find out whether the silence gate binds on hardware the way it binds
on cortex, where 0 of 48 configurations passed.

**If the rig passes gates that cortex failed**, that is the most interesting
result the project could produce, and it means the failure is neural-specific.
Do not treat it as a bug. Check it, then report it.

---

## B-12 — Faults you cause but did not design

Cause a real fault by hand, note the exact time, and let the recording run
through it:

| Intervention | How |
|---|---|
| Connector loosening | Half-unseat the camera ribbon, re-seat it |
| Optical attenuation | Slide the ND gel in front of the lens |
| Contamination | A fingerprint on the lens edge |
| Mechanical rotation | Turn the stage with the stepper motor |
| Thermal | Hair dryer, lowest setting, ≥30 cm, ≤60 s, component below 50 °C |

You know *when* it started because you caused it. You did **not** design what it
would look like — which is the point.

**Report these in a table separate from the designed faults.** Prediction P-R6
says undesigned faults will be at least 0.03 AUC harder. Whether the result
transfers is the question, not the assumption.

---

## B-13 — Separate the variables the archive could not

In the archived data, decoder error, trace noise and task geometry all move
together, and a claim had to be withdrawn because they could not be told apart.
On the rig you can hold one fixed and vary the other: sweep `--brightness` with
`--concentration` fixed, then the reverse, then both crossed.

This is the manipulation recorded data cannot offer, and it is the cleanest
argument for why the rig had to be built rather than simulated.

---

## B-14 — The decision-rate curve *(the centrepiece)*

**What this produces: a curve that does not exist for any system, measured
entirely on data this project collects.**

### The question

`reports/OPERATING_POINT_BOUND.md` found that the monitor failed for a reason
unrelated to the detector: a budget of 0.1 false alarms per hour was applied to a
system deciding **720 times an hour**, demanding a per-decision false-positive
rate of 0.00014.

That implies something more general than a fix. **Deciding less often should make
monitoring easier for two compounding reasons** — a looser per-decision budget,
and more evidence behind each decision. If that holds, there is a *decision-rate
law* for health monitoring of any drifting many-channel sensor: **detection
achievable at a fixed false-flag rate, as a function of how often you decide.**

### Why the archived data raised this and cannot answer it

`reports/DECISION_RATE_CURVE.md` measures the curve on Pun et al.'s recordings.
Two things stop it settling anything:

| | T11 | T5 |
|---|---|---|
| Direction of the curve | **rises** (+11.5%) | **falls** (−18.2%) |
| Detection at 720 decisions/hour | 85.1% (CI 62.6–98.7%) | 86.4% (CI 66.9–93.8%) |
| Fault-free episodes behind the threshold | **29** | **21** |

A law that points one way in one array and the other way in the next is not a
law. And at a 10% false-flag rate the threshold is the 90th percentile of 29
episodes — **two or three episodes in the tail.** The intervals show what that
costs.

**This is the specification for a measurement, not a dead end.**

### One campaign gives the whole curve

**The decision rate is an analysis choice, not a recording choice.** A session
recorded once can be scored at every decision rate afterwards. So this does not
need an arm per rate. It needs enough fault-free sessions to put a trustworthy
threshold on the tail, and the entire curve falls out of the same recordings.

### The schedule

| | Value |
|---|---|
| Healthy sessions | **101 minimum** — this is a floor, not a target |
| Sessions with a constructed degradation | **101** |
| Total | **202, about 17 hours** |
| Scored at | every decision rate from 720/hour down to 1 per session |

**Record more healthy sessions than 101 if time allows**, and record them first.
The binding constraint is the tail of the fault-free distribution, so healthy
recording is what buys precision. 200 healthy sessions costs another 8 hours
unattended and roughly halves the width of the threshold's interval.

```
python3 rig/run_batch.py --make-sweep-plan rig/plans/healthy.txt --levels 0 --blocks 101
python3 rig/run_batch.py --plan rig/plans/healthy.txt
```

Degrading sessions impose a drift whose **onset is drawn and written down before
the session starts.** That is what the archived data does not have and cannot be
given retrospectively.

Then score the same recordings at every decision rate:

```
python3 scripts/76_decision_rate_curve.py
```

### What each outcome means

| If the rig's curve… | Then |
|---|---|
| **Rises**, as T11's does | Deciding less often genuinely helps. The curve is a design rule: *check this often, and no more.* Applies to any drifting many-channel sensor, not just implants. |
| **Falls**, as T5's does | Pooling windows destroys more than it buys, and the right move is the opposite of what this analysis suggests. |
| **Is flat** | The failure is in the detector, not the sampling — which sends the next attempt somewhere completely different from where this project would have sent it. |

**All three are publishable, and the project cannot currently predict which one
it will get.** That is the test of whether this is an experiment rather than a
demonstration.

### Why this is your data and not a re-analysis

| | Archived data | This campaign |
|---|---|---|
| Fault-free sessions | 29 / 21 | **101+** |
| Onsets | never recorded; chosen afterwards | **drawn before each session** |
| Who collected it | Pun et al., 2024 | **this project** |
| Can it settle the curve? | **no** | yes |

The archived data asked the question. **The answer comes from recordings made
here**, and it is a design curve for a whole class of sensor, not a fact about
two people's implants.

---

## B-15 — The drift sweep *(optional, only if time allows)*

The old centrepiece, kept because it is still a good question: 5 levels
log-spaced between 4 s and 811 s, 53 blocks each, about 22 hours
(`reports/DRIFT_SWEEP_DESIGN.md`). Run it only after B-14 is complete. **If time
is short, cut this and not B-14.**

---

# PART 6 — The finished instrument

## 6.1 What sits on the table at the fair

A closed black box, about 40 cm long, with a screen at one end and a Raspberry
Pi camera at the other. A laptop beside it showing the output. Inside, a
temperature sensor and a small stepper motor. Total cost about $150.

**What it does:** given a recording from any many-channel sensor, it reports
whether that sensor can be health-monitored, and at what cost.

**How to demonstrate it in two minutes at the table:**
1. Show the live view — a grey rectangle. Explain that the direction signal is
   half a brightness level deep, which is why it looks like nothing, and that
   matching cortex's difficulty is why it has to be that small.
2. Run a short healthy block. Show the monitor staying quiet.
3. Slide the ND filter in front of the lens. Show the risk score rising.
4. Show the certificate: the verdict, the lead time, and the false-alarm rate
   that lead time costs.

Step 4 is the one that distinguishes this from a science-fair demonstration. Any
project can make a number go up when something breaks. This one reports **what
that warning costs when nothing is breaking**, which is the number the field
does not currently have.

## 6.2 The certificate

```
python3 scripts/73_monitorability_certificate.py --participant RIG1
```

It reads recordings already processed by the standard pipeline and emits
`reports/MONITORABILITY_CERTIFICATE_RIG1.md` — the participant name is part
of the filename, so a rig certificate never overwrites a neural one —
containing:

| Field | Meaning |
|---|---|
| Windows per session, and independent samples | How much genuinely independent evidence one session holds |
| Lag-1 autocorrelation at non-overlapping spacing | The measured serial dependence, with the spacing stated |
| Estimator ceiling at this series length | The highest value the statistic can report here, so a number near it is not mistaken for a real one |
| Lead time at the false-alarm budget | How early a warning arrives |
| False alarms per hour | What that costs |
| Gates passed, out of five | Silence first |
| **Verdict** | Monitorable / not monitorable at this budget |

The same command run with `--participant T11` produces the certificate for the
neural data. **That is the demonstration**: one instrument, one procedure, two
very different systems, directly comparable for the first time.

## 6.3 Why this is an engineering deliverable and not a demo

- It has a **specification**: 384 channels, 50 fps, 30 s windows stepping 5 s,
  0.1 false alarms per hour.
- It has a **calibration procedure** with a pass condition (B-7, margin within
  6° of 36.1°).
- It has a **validation protocol** that can fail (B-1 through B-14, each with a
  written fallback).
- It has **measured performance**, reported with its limits.
- It is **reproducible**: $150 of parts and a public repository.

---

# PART 7 — When something comes out wrong

Work down this list. Every branch has an action, because "the result was
unexpected" must never end in a stop.

### The rig will not decode above chance at all (B-7 fails badly)
1. Check B-6 first — if the dither is not getting through, nothing downstream
   can work.
2. Raise `--depth` by 10× temporarily. If it decodes now, the problem is signal
   level, and the fix is exposure or pixels per channel, not depth.
3. Check the stimulus and capture are seeing the same frames (B-5).
4. If it still fails: **report it.** "A camera-and-screen array could not be
   made to decode at cortex's operating point" is a genuine finding about the
   limits of the analogy, and the computational half of the project stands
   without it.

### The rig decodes far too well
Lower `--depth`, then reduce pixels per channel. Both are in Gate 3. Do not
proceed with a rig that decodes better than about 40° of error — it is not
comparable to cortex and the comparison will be about difficulty.

### One fault mode has no severity ladder
Report that mode as unusable and carry on with the other three. Do not
substitute a different severity definition to make the ladder appear — that is
exactly the "try several definitions and keep the best" pattern this project
refuses elsewhere.

### The autocorrelation comes out nowhere near either neural figure
This is a result, not a failure. Report the number with its interval, state the
window spacing and the number of windows, and note the estimator's ceiling at
that length. Then say plainly which of the two systems it resembles, if either.

### Recording takes longer than the time available
Cut in this order, and record what you cut:
1. B-13 (variable separation) — interesting, not load-bearing.
2. B-14 levels: 4 levels instead of 5, which costs resolution but is honest if
   stated.
3. B-12 undesigned faults down to two interventions instead of five.
**Never cut:** B-2 (light-tightness), B-6 (dither), B-7 (calibration), B-9 (the
main comparison). Those four are the experiment.

### The Pi dies, the card corrupts, or the box gets knocked
Keep a second SD card imaged and a photograph of the camera geometry. Re-aiming
the camera changes the channel mapping, so a knocked box means re-running B-7
and starting the affected arm again. Record the date it happened.

### A number disagrees with one already in the repository
Run `python3 scripts/31_verify_claims.py`. If a committed number no longer
matches its source, that is a finding about the repository, and it goes in the
log before anything else is changed.

---

# PART 8 — Working without further help

## 8.1 The rule that has caught the most mistakes

**Before every commit:**
```
python3 scripts/31_verify_claims.py
python3 scripts/55_reproducibility_audit.py
python3 scripts/56_claims_register.py
python3 scripts/61_statistical_hygiene.py
python3 scripts/65_log_coverage.py
python3 scripts/69_command_check.py
python3 -m pytest tests/ -q
python3 tools/mutation_check.py
```
All eight must pass. Run them **before** `git add`, not after — several write
output files, and running them afterwards leaves the tree dirty.

## 8.2 Things that have gone wrong before, and will again

- **A report that is both generated and hand-edited will be regenerated by
  someone who does not know it was edited.** This has happened twice, to
  `ACHIEVABILITY.md` and `DATASET_EXPLORATION.md`. If you hand-write into a
  generated report, move the text into the script that emits it.
- **An artifact made by an undocumented command will not reproduce.** Four were
  found in one afternoon. If you pass a flag, write the flag into
  `research/REPLICATION_GUIDE.md`.
- **A gate whose scope is a hand-maintained list will silently shrink.**
  `69_command_check.py` once passed while checking 19 commands instead of 69.
- **Never put a script filename in backticks unless the file exists.** The
  reproducibility audit checks this, and it has caught dangling references four
  times.

## 8.3 Where everything is

| I need… | Look in |
|---|---|
| What each document is | `research/README.md` |
| Every computational step, with commands | `research/REPLICATION_GUIDE.md` |
| The phase-by-phase procedures | `research/EXPERIMENTAL_PROCEDURES.md` |
| The ISEF submission | `research/RESEARCH_PLAN_2026-09-15.md` |
| What was predicted before the rig existed | `research/RIG_PREREGISTRATION.md` |
| Every headline claim and its check | `reports/CLAIMS_REGISTER.md` |
| Decisions and mistakes, dated | `research/research_log.md` |
| Why the rig is calibrated the way it is | `reports/RIG_DIGITAL_TWIN.md` |
| Why the autocorrelation figures changed | `reports/AUTOCORR_BY_SEVERITY.md` |

## 8.4 The five decisions still outstanding

1. ~~P-R1 and P-R2 retargeting~~ — **done 19 September 2026**, Amendment 1.
2. **The AI disclosure** in the research plan — must be written by you.
3. **Bibliography author lists**, supervision location, category confirmation.
4. **`ISEF_RESEARCH_PLAN.md`** — retire it, or make it the December draft.
5. **Which power-sweep grid the project keeps**
   (`REPLICATION_GUIDE.md`, Procedure 15).

## 8.5 If someone asks the hardest question at the fair

*"Your monitor doesn't work. Why is that worth a prize?"*

Because the project did not set out to build a monitor that works; it set out to
find out whether one can, and to build the test that decides. It answered that
question with a measured limit rather than an opinion, found the reason to three
decimals, and built an instrument that lets anyone else measure the same thing
on their own hardware for $150.

And then, twice, it caught itself being wrong — once when the headline
autocorrelation turned out to be mostly the fault that had been injected, and
once when the rig design turned out to be too easy to mean anything. Both are in
the log, dated, with what changed.

That is what the work is.
