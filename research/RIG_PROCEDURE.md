# Physical rig — step-by-step experimental procedure

**Written:** 6 September 2026.
**Status: PROCEDURE ONLY. NOTHING HAS BEEN BUILT AND NOTHING HAS BEEN MEASURED.**
No number in this document is a result. Every number is either a setting to use,
a target to hit, or a figure quoted from the archived-data study for comparison.

**Derived from:** `research/ORIGINAL_DATA_COLLECTION_DESIGN.md` (the design) and
the audit in `reports/PROJECT_AUDIT_2026-09-06.pdf` §13 (the findings each stage
attacks). Where this document departs from the design, §0.2 says so and why.

**Who this is written for:** somebody who has never built the rig, does not
already know the analysis code, and needs to be able to reproduce every step.
Commands are given in full. Where a command needs explaining, it is explained.

---

## 0. Decisions to make before reading further

### 0.1 Three decisions that are yours, not mine

Nothing below can start until these are answered. They are unchanged from
`ORIGINAL_DATA_COLLECTION_DESIGN.md` §8.

| # | Decision | Why it blocks | If undecided |
|---|---|---|---|
| **D1** | **Your deadline** | Stage 11 (longitudinal) needs 6–10 weeks of wall-clock time and cannot be compressed. Everything else fits in two weekends plus unattended running. | Assume Stage 11 is out and build for Stages 1–10 only. It can be added later if time appears; it cannot be added at the end. |
| **D2** | **Build hardware at all?** | Declining leaves a defensible computational project. Accepting is real work with a real failure mode (a half-built rig producing noisy data is worse than no rig). | Do not start. A partial rig is the one outcome with negative value. |
| **D3** | **Channel count: 384, 192, or both** | 384 matches T11, the participant every day-effect finding rests on. 192 matches T5. | **Recommendation: 384.** All of C07–C10, L03 and the P5 result are T11 findings. Matching T11 makes the comparison direct. 192 can be produced afterwards by pooling adjacent regions in software, at no extra recording cost. |

### 0.2 One change I am proposing to the design, and why

`ORIGINAL_DATA_COLLECTION_DESIGN.md` specifies a **WS2812 addressable LED matrix**
as the stimulus. This procedure uses **a computer monitor or tablet screen**
instead. This is a change to your design and the call is yours; here is the
reasoning both ways.

| | LED matrix (as designed) | Screen (as written here) |
|---|---|---|
| Driver risk | WS2812 timing on a Raspberry Pi needs DMA + PWM on one specific pin and root privileges. On Pi 5 the GPIO hardware changed and the usual library historically did not work. **Verify before buying.** | None. It is a display. |
| Soldering | Possibly, for power injection | None |
| Spatial resolution | 8×8 or 16×16 physical LEDs | Thousands of pixels; 384 regions is trivial |
| Brightness control for the SNR sweep | Per-LED, 8-bit | Per-region, software, continuous |
| Cost | ~$15 | $0 if you have a spare monitor, tablet or old laptop |
| Closer to the written design | **Yes** | No |
| Natural emitter aging for Stage 11 | LED phosphor aging is a plausible 6-week drift source | Backlights age over years, not weeks — so Stage 11 drift must come from optics, dust and temperature instead |

**My recommendation is the screen**, because the only thing the stimulus has to
do is emit a controlled, spatially structured pattern, and a screen does that
with no electronics risk at all. The scientific claim is unaffected: in both
cases the light is real, the optical path is real, the sensor noise is real, and
the degradation is real.

**If you keep the LED matrix**, everything below still applies except §5
(stimulus program), which you would rewrite against your matrix library, and
Stage 11 gains one extra plausible drift source.

### 0.3 One design correction that matters more than the hardware

The design doc says the rig will show *"whether the monitor's failure is a fact
about cortex or about any multichannel array that drifts."* As written, that
experiment can produce an uninterpretable answer, for two reasons. Both are
fixed in this procedure and both are the reason Stages 6 and 8 exist.

**Problem 1 — without a baseline match, a difference means nothing.**
If the rig's *healthy* behaviour does not resemble the neural data's healthy
behaviour before any fault is injected, then a difference afterwards cannot
distinguish *"the failure is neural-specific"* from *"the rig is not a
comparable system."* Stage 6 is a **go/no-go gate** that must be passed before
any fault is injected.

**Problem 2 — on the rig, `r` is a knob you can turn.**
Lag-1 autocorrelation depends on how fast the system drifts relative to the
window length, and on the rig you control both. "I predicted r ≈ 0.99 and got
r ≈ 0.99" would then be worth nothing, because you chose it. Stage 8 therefore
measures **two different things**:

- **8A — the natural value.** Impose no drift at all. Whatever `r` the rig
  produces on its own is a genuine, non-circular measurement.
- **8B — the calibration curve.** Impose a *known* drift time constant, sweep it
  across roughly three orders of magnitude, and plot `r` and effective sample
  size against it. Then mark where the neural value falls on that curve.

8B is a better experiment than the binary prediction in the design doc, and it
changes the shape of the project's answer. Instead of *"monitoring failed"* the
result becomes *"here is the relationship between how fast an array drifts and
whether it can be monitored at all — and cortex sits here on that curve."*

### 0.4 A number to have in front of you

The archived study's central finding, and the thing the rig is compared against.
Regenerated from `data/processed/episode_scores_local.csv` on 6 Sep 2026.

| Window spacing | Data shared between adjacent windows | T11 lag-1 r | T5 lag-1 r |
|---|---|---|---|
| every window (the published figure) | 83% | **0.995** | **0.980** |
| every 3rd window | 50% | 0.964 | 0.917 |
| **every 6th window** | **none** | **0.902** | **0.784** |

Quote the **0.902 / 0.784** row when comparing against the rig, not the 0.995.
The published figure is computed on overlapping windows, so part of it is forced
by the window geometry; the no-overlap row is the part that is a property of the
signal. Effective independent measurements per session stay **below 1 at every
spacing**, which is the finding itself and is unaffected.

---

## 1. Materials

Quantities are for one rig. Prices are indicative, September 2026.

### 1.1 Required

| # | Item | Spec | Qty | ~Cost | What it is for |
|---|---|---|---|---|---|
| M1 | Raspberry Pi 4 Model B | 4 GB RAM | 1 | $55 | Runs the capture program and logs data |
| M2 | microSD card | 32 GB, A2/U3 speed class | 1 | $10 | Operating system and recordings |
| M3 | Pi power supply | Official USB-C, 5 V 3 A | 1 | $8 | Under-voltage causes camera dropouts; do not use a phone charger |
| M4 | Raspberry Pi Camera Module 3 | With the 15-pin ribbon it ships with | 1 | $25 | **The sensor array.** Every "channel" is a region of its image |
| M5 | Screen for the stimulus | Any monitor, tablet or old laptop, ≥ 1280×720, brightness adjustable | 1 | $0–40 | Emits the pattern the camera reads |
| M6 | Enclosure | Cardboard box ≥ 40 × 30 × 30 cm, matte black interior (black paper or paint) | 1 | $5 | Excludes ambient light. **Ambient light is the single largest uncontrolled variable** |
| M7 | Camera mount | Small tripod, or a rigid bracket you build | 1 | $8 | The camera must not move between sessions except when you move it |
| M8 | Tape | Black gaffer or electrical tape | 1 roll | $4 | Light-sealing, cable strain relief, and occlusion faults |

**Required subtotal: ≈ $115**, or ≈ $75 if you already have a spare screen.

### 1.2 Required for Stage 9 (undesigned faults) only

| # | Item | Spec | Qty | ~Cost | What it is for |
|---|---|---|---|---|---|
| M9 | Stepper motor + driver | 28BYJ-48 5 V motor with ULN2003 driver board (usually sold together) | 1 | $5 | Physically rotates the camera — the undesigned `GEOMETRY_ROTATION` |
| M10 | Jumper wires | Female-to-female, 20 cm | 6 | $3 | Driver board to Pi GPIO header |
| M11 | Neutral-density filter | Photographic ND gel sheet, ND 0.6 (2 stops) | 1 | $8 | Undesigned `RATE_LOSS` — a real spectral change you did not design |
| M12 | Bracket for the motor shaft | 3D-printed, or layered cardboard and hot glue | 1 | $0–5 | Couples the camera to the 5 mm shaft |

### 1.3 Required for Stage 11 (longitudinal) only

| # | Item | Spec | Qty | ~Cost | What it is for |
|---|---|---|---|---|---|
| M13 | Temperature/humidity sensor | DHT22 / AM2302, **on a breakout board with the pull-up resistor already fitted** | 1 | $5 | Covariates. Without them a 6-week drift has no candidate explanation |
| M14 | External storage | 128 GB USB stick or SSD | 1 | $15 | Six weeks of daily sessions will outgrow the SD card |

### 1.4 Explicitly not required

No soldering iron, no breadboard, no oscilloscope, no mains wiring, no lasers,
no chemicals, no biological material, **and no human participants**. See §2.

---

## 2. Safety and rules compliance

**Procedure S1. Confirm the human-participants position, in writing.**
Nothing in this procedure measures, records, surveys or images a person. The
camera is enclosed and points at a screen. No person is a data source at any
stage, including you. This preserves Amendment 1 (`PROJECT_DEFINITION.md`) and
means ISEF Form 4 is not expected to apply. **Confirm rather than assume**, with
your SRC, before the fair.

**Procedure S2. Confirm the electronics position.**
Everything runs from a 5 V USB supply. There is no mains wiring, no battery
larger than a phone power bank, and no heating element. Low-voltage bench
electronics connected to no person is expected to require no Form 3. Again,
**confirm with your SRC rather than assume** — this is already flagged in
`ISEF_RESEARCH_PLAN.md` §0.

**Procedure S3. Physical hazards, in order of likelihood.**

1. *Pinch injury from the stepper.* The 28BYJ-48 is weak but the bracket edges
   are not. Keep fingers clear while it moves, and never run it with the
   enclosure open and your hand inside.
2. *Bright screen at close range.* Do not sit and stare into the enclosure with
   the stimulus at full brightness. Close the box; that is what it is for.
3. *Heat.* If you warm the camera as an undesigned fault (Stage 9, fault U4),
   use a hair dryer on its lowest setting at a distance of at least 30 cm, in
   short bursts, and **never above 50 °C at the camera board**. The Pi throttles
   at 80 °C; the camera is not rated for anything like that. Do not use a heat
   gun, a hotplate, or an oven.
4. *Ribbon cable.* The camera ribbon is fragile and the connector is easy to
   break. Power the Pi **off** before connecting or disconnecting it, every time.

**Procedure S4. Data safety.**
Recordings go to `data/raw_rig/` and are never edited in place, exactly as
`data/raw/` is treated for the archived data. Everything derived goes to
`data/processed/`. This is the same separation the project already enforces.

---

## 3. Stage 0 — Preregister, before anything is built

**This stage comes first and is not optional.** The design document says so:
*"Nothing is built until a preregistration exists, stating the predictions
derived from the neural findings before a single measurement is taken."* Every
study in this project since Phase 3 has followed this and it is the single
strongest thing the project has.

**Procedure 0.1. Write the preregistration.**
Create `research/RIG_PREREGISTRATION.md`. It must contain, and must not be
changed after Stage 6 begins:

1. **The predictions**, one line each, with numbers. Draft set (yours to edit
   before you commit it, not after):
   - **P-R1.** With no imposed drift, the rig's non-overlapping lag-1 r will be
     **≥ 0.70**. *(Neural comparison: 0.902 on T11, 0.784 on T5.)*
   - **P-R2.** Effective independent measurements per rig session will be
     **< 2**. *(Neural: 0.15–0.85 depending on spacing; always below 1.)*
   - **P-R3.** The silence gate will **fail** on the rig — more than 10% of
     healthy rig episodes will show a significant trend.
   - **P-R4.** Severity-ladder monotonicity will **fall as baseline angular
     error rises**, with Spearman ρ **< −0.4**. *(Neural: −0.677 T11,
     −0.926 T5 — the only relationship that replicates with the same sign on
     both arrays.)*
   - **P-R5.** A detector built on permutation-invariant features will be
     **worse** than `decoder_guard` on the rig, as it was on both participants.
2. **The go/no-go criteria for Stage 6**, numerically (§8.3 below).
3. **The stopping rule**: how many sessions will be recorded, decided now.
4. **What would falsify each prediction**, stated explicitly.
5. **A statement that no fault will be injected until Stage 6 passes.**

**Procedure 0.2. Freeze it.**
```
cd ~/bci-ews-research
git add research/RIG_PREREGISTRATION.md
git commit -m "Preregister the rig study before building anything"
git push -u origin claude/isef-research-pipeline-9zt4uq
```
`git add` stages a file for saving; `git commit` saves it with a message; `git
push` uploads it to GitHub. The commit's timestamp is what makes "before" a
checkable fact rather than a claim.

**Procedure 0.3. Record the commit hash in the file itself.**
```
git rev-parse HEAD
```
This prints a long identifier such as `ea6da24...`. Paste it into
`RIG_PREREGISTRATION.md` under a heading `Frozen at commit:` and commit again.
This is the same mechanism `FROZEN_DESIGN.json` uses.

---

## 4. Stage 1 — Software environment on the Pi

**Procedure 1.1. Install the operating system.**
On your normal computer, download and run **Raspberry Pi Imager** from
`raspberrypi.com/software`. Choose:
- Device: Raspberry Pi 4
- OS: **Raspberry Pi OS (64-bit)**, Bookworm or later
- Storage: the microSD card (M2)

In Imager's settings (the gear icon) set a hostname (`rig`), enable **SSH**, set
a username and password, and enter your Wi-Fi details. SSH lets you control the
Pi from your normal computer over the network, so the rig can stay sealed in its
box.

Write the card, put it in the Pi, connect power (M3).

**Procedure 1.2. Connect to the Pi.**
From your normal computer's terminal:
```
ssh yourusername@rig.local
```
If `rig.local` does not resolve, find the Pi's IP address from your router and
use that instead.

**Procedure 1.3. Update and install what is needed.**
```
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 python3-numpy python3-pandas git
```
`sudo` runs a command with administrator rights. `apt` is the software
installer. `picamera2` is the camera library and is preinstalled on Bookworm;
the line above makes sure.

**Procedure 1.4. Verify the camera before building anything around it.**
Connect the camera (M4) to the Pi's CAMERA port **with the Pi powered off**:
lift the black tab on the connector, insert the ribbon with the *blue* side
facing the ethernet port, press the tab down. Power on, then:
```
rpicam-hello --timeout 5000
```
On older releases this command is `libcamera-hello --timeout 5000`. A preview
window (or, over SSH, five seconds of log lines with no error) means the camera
works. **If this fails, stop and fix it. Everything downstream depends on it.**

**Procedure 1.5. Confirm the frame rate you can actually sustain.**
The analysis pipeline uses 20 ms bins — 50 frames per second. Check you can hold
that:
```
rpicam-vid --width 480 --height 320 --framerate 50 --timeout 10000 --codec yuv420 -o /dev/null --info-text "%fps"
```
Read the reported frames per second. **Record the number you actually get.**
- If it holds ~50 fps: use `BIN_S = 0.02` and the analysis constants are
  unchanged from the neural study.
- If it holds only ~30 fps: use `BIN_S = 1/30 = 0.0333`. Keep `WINDOW_BINS =
  1500` and `STEP_BINS = 250` unchanged, so the code is untouched and the
  *number of samples per window matches the neural study exactly*. The
  consequence is that a window is 50 seconds of wall-clock instead of 30.
  **Write this number into your preregistration and report it everywhere.**

---

## 5. Stage 2 — The stimulus program

### 5.1 What the stimulus has to be, and why

This is the part of the design most worth understanding, because a naive choice
here breaks the analogy to neural data.

In the archived data, each channel is an electrode whose firing rate depends on
the **direction the person intends to move**, roughly as a cosine of the angle
between that direction and the channel's own preferred direction. A linear
decoder recovers intended direction from the population.

If the rig simply showed a dot moving around, each image region would light up
when the dot *passed through it* — that is **position** tuning, not direction
tuning, and the decoding problem would be a different one. The comparison would
be loose.

So the stimulus is built to be a **physical realisation of a cosine-tuned
population**. Each of the N image regions is assigned a fixed preferred
direction θ_i, drawn once at random and never changed. On every frame, given the
current heading φ, region i is drawn at brightness

&nbsp;&nbsp;&nbsp;&nbsp;`b_i = 0.5 * (1 + cos(φ − θ_i))`

Region i is therefore brightest when the heading matches its preferred
direction, exactly as a cosine-tuned neuron fires fastest for its preferred
direction. The camera then reads this through real optics with real noise, and
the decoder's job becomes *identical in form* to the neural one.

**What is designed and what is physical, stated plainly.** The *encoding* is
designed — it has to be, because you must put a known signal in. The *sensing,
the noise, the optics and every degradation* are physical. This is the project's
own rule from `PROJECT_DEFINITION.md` §5.5 — *"the perturbation may be
simulated, the response to it may not"* — applied correctly. Nobody is
simulating the thing being detected.

**One consequence to expect and to fix in Stage 6:** because the encoding is
generated cleanly, the rig's raw signal-to-noise ratio will start out *far
higher* than cortex. That is the whole reason the baseline-matching gate exists.

### 5.2 The heading sequence

**Procedure 2.1. Generate headings, isotropically by default.**
The heading φ changes every `HOLD` frames (default 100 frames = 2 s at 50 fps),
and each new heading is drawn uniformly from 0 to 360°. Each constant-heading
segment is one **trial**, matching a reach in the neural task.

This matters because of finding **E01**: archived sessions differ by a factor of
fifty in how directionally varied the task was (resultant length 0.01 to 0.68),
and that affects every absolute error number in the project. On the rig you
control it. Default to isotropic, and treat directional concentration as a
manipulable variable in Stage 10.

### 5.3 The program

**Procedure 2.2. Write the stimulus program.**
On the machine driving the screen (this can be the Pi itself with the screen
attached, or a second computer), create `rig/stimulus.py`:

```python
#!/usr/bin/env python3
"""Displays a cosine-tuned brightness field. One patch per channel.

Writes rig/stim_log.csv: one row per frame, with the true heading, so the
ground truth is recorded rather than inferred afterwards.
"""
import csv, json, math, time, sys
import numpy as np
import pygame

N_COLS, N_ROWS = 24, 16          # 24*16 = 384 channels, matching T11
PATCH = 40                        # pixels per patch on screen
FPS = 50                          # must match the camera's actual rate
HOLD = 100                        # frames per trial (2 s at 50 fps)
SEED = 20260826                   # same master seed as the fault corpus
DURATION_FRAMES = 15000           # 5 min at 50 fps ~ one MINDFUL block

rng = np.random.default_rng(SEED)
N = N_COLS * N_ROWS
PREF = rng.uniform(0, 2 * math.pi, N)     # each channel's preferred direction
np.save("rig/preferred_directions.npy", PREF)   # fixed for the rig's lifetime

pygame.init()
screen = pygame.display.set_mode((N_COLS * PATCH, N_ROWS * PATCH))
clock = pygame.time.Clock()

log = open("rig/stim_log.csv", "w", newline="")
w = csv.writer(log); w.writerow(["frame", "t_unix", "heading_rad", "trial"])

heading, trial = rng.uniform(0, 2 * math.pi), 0
for f in range(DURATION_FRAMES):
    if f % HOLD == 0:
        heading = rng.uniform(0, 2 * math.pi); trial = f // HOLD
    b = 0.5 * (1 + np.cos(heading - PREF))          # cosine tuning, 0..1
    b = apply_fault(b, f)                            # Stage 7 hooks in here
    for i in range(N):
        v = int(np.clip(b[i], 0, 1) * 255)
        pygame.draw.rect(screen, (v, v, v),
                         ((i % N_COLS) * PATCH, (i // N_COLS) * PATCH, PATCH, PATCH))
    pygame.display.flip()
    w.writerow([f, time.time(), heading, trial])
    clock.tick(FPS)
log.close(); pygame.quit()
```

Until Stage 7, define `apply_fault` as a function that returns `b` unchanged.

**Procedure 2.3. Install the display library and test.**
```
sudo apt install -y python3-pygame
mkdir -p rig
python3 rig/stimulus.py
```
You should see a grid of grey squares whose brightnesses shift every two
seconds. **Check `rig/stim_log.csv` has one row per frame before continuing.**
The heading in that file is your ground truth; if it is wrong or missing,
nothing downstream can be scored.

---

## 6. Stage 3 — Build the rig

**Procedure 3.1. Prepare the enclosure.**
Line the inside of the box (M6) with black paper or matte black paint,
including the lid. Cut one hole in one end just large enough for the camera
ribbon and the power cables, and one panel at the opposite end sized to the
screen. Tape (M8) every seam and every remaining gap.

*Rationale:* ambient light entering the box is an uncontrolled input that varies
with time of day, weather and room lighting. Over a six-week longitudinal run it
would be indistinguishable from the drift you are trying to measure.

**Procedure 3.2. Mount the screen.**
Fix the screen (M5) facing into the box at one end, so the patch grid fills as
much of the camera's view as possible. It must not move for the life of the
experiment. Tape the frame down; do not rely on a stand.

**Procedure 3.3. Mount the camera.**
Fix the camera (M4) on its mount (M7) at the far end, pointing at the screen,
level and square. Adjust the distance until the patch grid fills roughly 80% of
the frame width, leaving a dark margin on all sides. The margin is deliberate:
it gives you a set of regions that see no stimulus, which is a free
background-noise reference.

**Procedure 3.4. Strain-relieve every cable.**
Tape each cable to the box wall about 5 cm from its connector. A tugged ribbon
that half-unseats itself mid-run produces a fault you did not log, at a time you
do not know. That is the one failure this whole design cannot tolerate.

**Procedure 3.5. Lock the camera settings.**
Automatic exposure and automatic white balance are adaptive compensators — they
are the rig's version of the adaptive normalisation layer this project already
found hiding in the published decoder. Leave them on and the camera will quietly
cancel the degradations you are trying to measure.

Create `rig/capture.py` with fixed settings:

```python
#!/usr/bin/env python3
"""Captures frames, reduces each to N region means, writes a channel matrix."""
import numpy as np, time, sys
from picamera2 import Picamera2

N_COLS, N_ROWS = 24, 16
W, H = 480, 320                   # gives exactly 20x20 px per region
FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 15000
OUT = sys.argv[2] if len(sys.argv) > 2 else "rig/block.npy"

cam = Picamera2()
cfg = cam.create_video_configuration(main={"size": (W, H), "format": "RGB888"},
                                     controls={"FrameRate": 50})
cam.configure(cfg)
cam.set_controls({
    "AeEnable": False,            # exposure fixed -- no auto-compensation
    "AwbEnable": False,           # white balance fixed
    "ExposureTime": 8000,         # microseconds; tune in Stage 6
    "AnalogueGain": 2.0,          # tune in Stage 6
})
cam.start(); time.sleep(2)        # let the sensor settle

rows = []
ts = []
for f in range(FRAMES):
    a = cam.capture_array("main")[:, :, 1].astype(np.float32)   # green channel
    r = a.reshape(N_ROWS, H // N_ROWS, N_COLS, W // N_COLS).mean(axis=(1, 3))
    rows.append(r.ravel()); ts.append(time.time())
cam.stop()

np.save(OUT, np.asarray(rows, dtype=np.float32))          # (frames, 384)
np.save(OUT.replace(".npy", "_t.npy"), np.asarray(ts))    # frame timestamps
print(f"wrote {OUT}  shape={np.asarray(rows).shape}")
```

The `reshape(...).mean(axis=(1,3))` line is what turns an image into channels:
it splits the frame into a 16 × 24 grid of 20 × 20-pixel tiles and averages each
tile. Each tile average is one channel, exactly as each electrode's binned spike
count is one channel in the neural data.

**Procedure 3.6. Test the whole loop, briefly.**
Start `stimulus.py` on the screen, then on the Pi:
```
python3 rig/capture.py 500 rig/test_block.npy
```
Then check the data is alive:
```
python3 -c "
import numpy as np
x = np.load('rig/test_block.npy')
print('shape', x.shape)
print('mean', x.mean().round(2), 'sd', x.std().round(2))
print('per-channel sd, min/median/max:',
      x.std(0).min().round(2), np.median(x.std(0)).round(2), x.std(0).max().round(2))
"
```
**What you need to see:** shape `(500, 384)`; a per-channel standard deviation
that is clearly above zero for the channels viewing the grid. A channel with
sd ≈ 0 is either in the dark margin (expected) or dead (a problem).

**If per-channel sd is near zero everywhere, stop.** The camera is not seeing
the stimulus change. Check focus, check the stimulus is actually running, check
exposure is not saturating every pixel to 255.

---

## 7. Stage 4 — Synchronising stimulus and camera

The decoder needs, for every frame of channel data, the heading that produced
it. Two programs running on two clocks will drift apart.

**Procedure 4.1. Align by timestamp.**
Both programs write Unix timestamps (`stim_log.csv` column `t_unix`, and
`*_t.npy` from the capture). For each captured frame, take the heading from the
stimulus row whose timestamp is closest.

**Procedure 4.2. Measure and correct the fixed lag.**
There is a constant delay between the screen changing and the camera recording
it (display latency plus exposure). Measure it once:

1. Run a special stimulus that goes fully black for 1 frame every 100 frames.
2. Capture 2000 frames.
3. Find the captured frames where total brightness dips.
4. The difference between the dip time and the logged black-frame time is the
   lag.

Subtract that lag from every camera timestamp thereafter. **Record the measured
lag in your preregistration file and re-measure it if you change the screen,
the exposure or the frame rate.**

*Rationale:* an uncorrected lag of even a few frames systematically rotates the
apparent tuning of every channel, which would inflate angular error uniformly
and would look exactly like a mediocre decoder.

---

## 8. Stage 5–6 — Emit pipeline-compatible files, then the go/no-go gate

### 8.1 What the existing analysis code needs

This is why the rig can reuse 65 already-verified scripts. The pipeline consumes
three things per block, and nothing else:

| What | Shape | Neural meaning | Rig equivalent |
|---|---|---|---|
| `neural[block_id]` | `(n_bins, n_features)` | binned firing rates | region-mean intensities from `capture.py` |
| `kinematics[block_id]` | dict with `cursorPos`, `targetPos`, each `(n_bins, 2)` | cursor and target positions; the decoder's target is the unit vector from one to the other | `cursorPos` = `(0,0)`; `targetPos` = `(cos φ, sin φ)` for that frame's heading |
| `trials` rows | one per trial | `start_bin`, `stop_bin`, `angle_error_deg` | one per constant-heading segment |

Setting `cursorPos = (0,0)` and `targetPos = (cos φ, sin φ)` makes the pipeline's
`intended_direction()` return exactly the heading unit vector, with no change to
`scripts/18_reference_decoder.py`.

**Procedure 5.1. Write the rig loader.**
Create `scripts/66_load_rig.py`, which walks `data/raw_rig/`, and for each block
folder produces the same `Dataset` object `scripts/03_load_dataset.py` produces:
`trials`, `blocks`, `neural`, `kinematics`. Fill `blocks` columns exactly as the
archived loader does — `participant` becomes `RIG`, `trial_day` becomes the
session number, `block` the block number, `n_features` 384.

**Procedure 5.2. Confirm compatibility before recording anything real.**
```
cd ~/bci-ews-research
python3 scripts/66_load_rig.py --check
```
It must print a `Dataset` summary in the same form the archived loader does. If
it does, every downstream script will run against rig data untouched.

### 8.2 Record the baseline sessions

**Procedure 6.1. Record 20 healthy blocks with no fault of any kind.**
```
for i in $(seq 1 20); do
  python3 rig/capture.py 15000 data/raw_rig/session_001/block_$i.npy
done
```
`for i in $(seq 1 20); do ... done` repeats a command twenty times, with `i`
counting up. 15000 frames is 5 minutes at 50 fps, matching a MINDFUL block
(T11 blocks are ~15,209 bins).

**Procedure 6.2. Fit a decoder on the rig baseline and measure chance.**
Use the existing script, pointed at the rig:
```
python3 scripts/18_reference_decoder.py --participant RIG
```
It fits ridge regression, freezes the weights, and — importantly — **measures**
the chance level by shuffled pairing rather than assuming 90°. That is the same
procedure that revealed archived per-day chance ranges from 47.7° to 102.7°.

### 8.3 The gate

**Procedure 6.3. Compare the rig's healthy behaviour to the archived healthy
behaviour, and decide go or no-go.**

| Criterion | Archived value | Rig must reach | Why this one |
|---|---|---|---|
| **G1.** Decoder skill: (measured chance) − (held-out error) | T11: 90.7 − 54.6 = **36.1°** | **25° to 47°** — within about ±30% | If the rig's decoder is far better than cortex's, its faults have much further to fall and every comparison is flattered |
| **G2.** Held-out angular error | T11: **54.6°** | **45° to 65°** | Absolute error must be in the same regime, because L03 showed behaviour changes near the chance ceiling |
| **G3.** Channel count | 384 | **exactly 384** | Fixed by D3 |
| **G4.** Samples per window | 1500 | **exactly 1500** | Keeps `WINDOW_BINS` unchanged, so effective-sample-size arithmetic is comparable |
| **G5.** Dead channels | — | **< 5%** of channels with sd ≈ 0 outside the dark margin | A dead channel is an unlogged permanent dropout fault |

**Criteria deliberately NOT on this list: lag-1 autocorrelation, effective
sample size, detection AUC, silence-gate pass rate.** Those are the quantities
being tested. Requiring the rig to match them at baseline would guarantee the
result and make the whole experiment circular. This is the same error as
choosing a deterioration definition after seeing which one performs best — which
this project has already refused once, and must refuse again here.

**How to hit G1 and G2 if you miss them.** You will almost certainly start with
the rig *too good* — very low angular error — because the encoding is clean. Add
noise physically, in this order, one variable at a time, and re-run Procedure 6.2
after each:

1. **Lower the screen brightness** (fewer photons → more shot noise)
2. **Shorten `ExposureTime`** in `capture.py`
3. **Raise `AnalogueGain`** (amplifies sensor noise)
4. **Defocus the lens very slightly** (blurs the channel boundaries)

Record every setting you land on. These become constants for the entire study
and must not be touched again after the gate passes.

> **GATE. If G1–G5 cannot all be met, do not proceed to Stage 7.**
> Report the rig as a failed analogue and say so. That is a legitimate,
> publishable outcome — "an optical array cannot be tuned to match cortical
> decoding difficulty" is a real finding about the limits of the analogy. It is
> far better than injecting faults into a system you have not shown to be
> comparable and reporting a difference you cannot interpret.

---

## 9. Stage 7 — Designed faults (Arm A)

**Procedure 7.1. Draw and lock the injection plan before recording.**
Use the existing injector, which already refuses to re-draw onsets without a
recorded reason:
```
python3 scripts/17_fault_injector.py --participant RIG plan
```
This writes `data/processed/injection_plan_RIG.json` containing every episode's
mode, rate, severity, onset frame, per-episode seed, a SHA-256 checksum of the
episode list, and the git commit it was created at.

```
git add data/processed/injection_plan_RIG.json
git commit -m "Lock the rig injection plan before any fault is recorded"
git push -u origin claude/isef-research-pipeline-9zt4uq
```

**This commit must come before the first fault session is recorded.** It is the
rig's equivalent of the commit that makes the archived corpus's ground truth
credible.

**Procedure 7.2. Implement `apply_fault` in `stimulus.py`.**
The four modes, each realised as a real change in emitted light:

| Mode | What the program does to the brightness vector `b` | Severities (benign / sub / crossing) |
|---|---|---|
| `RATE_LOSS` | Multiply **all** patches by `(1 − s·ramp)` | 0.10 / 0.25 / 0.55 |
| `CHANNEL_DROPOUT` | Set a **nested** set of patches to 0 | 0.05 / 0.30 / 0.60 |
| `GAIN_DRIFT` | Per-patch multipliers, then **rescale so the mean is unchanged** | 0.20 / 0.50 / 1.20 |
| `GEOMETRY_ROTATION` | Rotate the patch→preferred-direction assignment | 0.15 / 0.45 / 1.20 |

Copy the severity values from `data/processed/injection_plan.json` so the ladder
is identical to the archived corpus.

**Two mistakes the archived corpus already made — do not repeat them.**

1. `GAIN_DRIFT` must be **mean-conserved per frame**. In the archived corpus it
   was not, twice: log-centring preserves the *geometric* mean and left +116% at
   crossing severity, and a pre-onset rescale still left +20.8%. Assert it:
   ```python
   assert abs(b_faulted.mean() / b_clean.mean() - 1) < 0.03
   ```
   If this is not conserved, the mode stops being invisible to a brightness
   counter, and the comparator gate — the whole point of the mode — is void.
2. `CHANNEL_DROPOUT` severity levels must be **nested**: the channels killed at
   severity 0.30 must be a superset of those killed at 0.05. Drawing independent
   sets made the archived ladder run *backwards*.

**Procedure 7.3. Record the fault sessions.**
Follow the plan file exactly. One block per episode, 15,000 frames each. Do not
look at any detector output until every session in the plan has been recorded —
that is what makes the test set a test set.

**Procedure 7.4. Verify the pre-onset guarantee by construction.**
In the archived corpus this held "only by floating-point luck" before it was
fixed. Assert it in code, not by inspection:
```python
assert (b_faulted[:onset_frame] == b_clean[:onset_frame]).all()
```
A leak of post-onset data into the pre-onset window would let a detector "warn"
off the leak itself — a perfect self-fulfilling result and the single most
dangerous bug available to this design.

---

## 10. Stage 8 — The two autocorrelation measurements

This is the stage that answers your actual research question, and it is the one
this procedure adds to the design doc.

### 10.1 Stage 8A — The natural value (non-circular)

**Procedure 8.1.** Record **50 healthy blocks with no imposed drift of any
kind**, spread across at least 5 separate days, powering the rig down between
days. Powering down matters: it allows thermal state, dust and seating to change
between sessions, which is what "different day" means physically.

**Procedure 8.2.** Compute lag-1 autocorrelation at all four window spacings —
every window, every 3rd, every 6th, every 9th — exactly as done for the archived
data in §0.4. Compare the **no-overlap** row against **0.902 (T11) / 0.784 (T5)**.

This measurement is not circular: you imposed nothing, so whatever `r` appears is
a property of a real drifting optical array.

### 10.2 Stage 8B — The calibration curve (the real deliverable)

**Procedure 8.3.** Impose a slow, known brightness drift: a random walk on
overall screen brightness with time constant τ. Sweep τ across **8 levels
spanning 5 s to 2000 s** — roughly `[5, 15, 45, 130, 400, 750, 1200, 2000]`
seconds. Record **10 healthy blocks at each level**, 80 blocks in total.

**Procedure 8.4.** For each τ, compute and plot:
- lag-1 r (no-overlap spacing)
- effective independent samples per session, `n·(1−r)/(1+r)`
- detection AUC on matched fault episodes
- silence-gate pass rate

**Procedure 8.5.** Mark the archived neural values on each plot, and read off
the τ at which the rig reproduces cortex.

**What this produces.** Not a yes/no, but a curve: *how monitorable is an array,
as a function of how fast it drifts?* — with a specific point on it labelled
"human motor cortex, T11." That reframes the project's whole answer. It stops
being "the monitor failed" and becomes "**here is the regime in which
decoder-health monitoring is possible at all, and cortex falls outside it by
this much.**" A future array that drifts more slowly, or a windowing scheme that
buys independent samples, can be placed on the same curve and evaluated before
anyone builds it.

That is a positive result extracted from a negative one, and it is the strongest
thing this experiment can produce.

---

## 11. Stage 9 — Undesigned faults

**The purpose.** Every fault so far has a signature you designed. If the monitor
only ever meets degradations you wrote, passing partly measures your
imagination. Here the **onset is known** (you caused it, and logged it) while the
**signature is not** (it emerges from physics). That combination is the strongest
ground truth this project can obtain, and it needs no participants.

**Procedure 9.1. For each fault below:** start recording, wait a logged number of
frames, apply the intervention, keep recording. Write the intervention frame
number and a description into `data/raw_rig/undesigned_log.csv` **at the moment
you do it**, not afterwards.

| ID | Intervention | How | Expect it to resemble |
|---|---|---|---|
| U1 | Camera rotation | 28BYJ-48 (M9) rotates the camera 15° mid-block | `GEOMETRY_ROTATION` |
| U2 | ND filter | Slide ND 0.6 gel (M11) in front of the lens | `RATE_LOSS` |
| U3 | Connector loosening | Partially unseat the camera ribbon, one notch | Nothing designed — this is the interesting one |
| U4 | Thermal drift | Hair dryer, lowest setting, ≥30 cm, 60 s bursts. **Never above 50 °C.** See S3 | `GAIN_DRIFT`, possibly |
| U5 | Electromagnetic interference | Place a phone making a call next to the ribbon | Nothing designed |
| U6 | Optical contamination | One fingerprint smudge on a corner of the lens | `CHANNEL_DROPOUT`, partially |

**Procedure 9.2. Report designed and undesigned results in separate tables.**
Generalisation from the first to the second is a **testable claim, not an
assumption**, and merging the tables would destroy the only place this
experiment tests it.

**Wiring for U1** (only needed if you do the rotation fault). Pi powered off:

| ULN2003 driver pin | Raspberry Pi pin (physical) | GPIO (BCM) |
|---|---|---|
| IN1 | pin 11 | GPIO 17 |
| IN2 | pin 13 | GPIO 27 |
| IN3 | pin 15 | GPIO 22 |
| IN4 | pin 16 | GPIO 23 |
| `+` (5 V) | pin 2 | — |
| `−` (GND) | pin 6 | — |

Bolt the motor to the box floor, couple its 5 mm shaft to the camera mount with
bracket M12, and check by hand that the camera swings freely before powering the
motor.

---

## 12. Stage 10 — The saturation and geometry sweeps (Arm C)

**Procedure 10.1. Baseline SNR sweep.** Vary screen brightness across ~20 levels
from just-decodable to maximum. Record 10 short blocks (3000 frames) at each,
~200 blocks — one automated afternoon. Measure where angular error saturates
against that level's own measured chance.

*This directly tests a recommendation the project published in
`UNAMBIGUOUS_EPISODES.md` and could not test, because the archived data contains
no sessions at controlled SNR.*

**Procedure 10.2. Directional-concentration sweep.** Repeat at 5 levels of
heading concentration — from isotropic to nearly one-directional — matching the
archived range (resultant length 0.01 to 0.68 from finding E01). Hold brightness
fixed.

**Procedure 10.3. The crossed design.** Run SNR × concentration at 4 × 4 levels,
5 blocks each. This is the manipulation cortex will not allow: **each variable
varies while the other is held fixed.** It is the only way to separate the five
entangled session variables that forced claim W02 to be withdrawn.

---

## 13. Stage 11 — Longitudinal (Arm B) — start on day one

**Procedure 11.1. Start this the day the rig first passes Stage 6**, and let it
run in parallel with everything else. It costs nothing extra and it cannot be
compressed later.

**Procedure 11.2.** Automate one identical healthy session per day. On the Pi:
```
crontab -e
```
`crontab` schedules commands to run automatically. Add this line:
```
0 3 * * * /usr/bin/python3 /home/pi/rig/daily_session.py >> /home/pi/rig/cron.log 2>&1
```
This runs `daily_session.py` at 03:00 every day and appends all output to a log
file. 03:00 is deliberate: ambient conditions are most stable and nobody will
open the box.

**Procedure 11.3.** Log temperature and humidity (M13) every minute alongside.
Without covariates a six-week drift has no candidate explanation and the arm
produces an uninterpretable curve.

**Procedure 11.4. Change nothing.** No cleaning, no refocusing, no re-seating
cables, no software changes. **If you touch the rig, log what you did and when.**
An unlogged intervention in a longitudinal arm is indistinguishable from a
finding.

**Procedure 11.5.** After 6–10 weeks, run the archived staleness and day-variance
scripts (39–44) unchanged and ask the question the arm exists for: **does natural
drift resemble any of the four designed modes?** If it matches one, the corpus
gains external validity. **If it matches none, that is a significant finding
about how fault benchmarks are built — including this one.**

---

## 14. Analysis

**Procedure 12.1. Run the existing pipeline, unchanged.**
```
python3 scripts/17_fault_injector.py --participant RIG
python3 scripts/18_reference_decoder.py --participant RIG
python3 scripts/20_evaluation_harness.py --participant RIG --local
python3 scripts/21_score_report.py --participant RIG
python3 scripts/24_benchmark_matrix.py
python3 scripts/29_aggregation_limit.py
```
No analysis code is modified. That is deliberate and it is the strongest defence
against the accusation that the rig result was tuned: **the analysis was written,
frozen and verified by 93 checks before the rig existed.**

**Procedure 12.2. Run all five gates before committing anything.**
```
python3 scripts/31_verify_claims.py
python3 scripts/55_reproducibility_audit.py
python3 scripts/56_claims_register.py
python3 scripts/61_statistical_hygiene.py
python3 scripts/65_log_coverage.py
```
Run these **first, then commit.** Running them afterwards leaves generated files
changed but unsaved — a mistake this project has already made once.

**Procedure 12.3. Report the rig at the episode level.**
Bootstrap over **episodes, never over windows**. Windows within a block are not
independent — that is the finding the rig exists to test, so treating them as
independent while testing it would be self-contradictory. The archived study
inflated its sample size 26.6× this way and published four p-values as exactly
zero, three of which were not real.

**Procedure 12.4. Write it up honestly, whichever way it goes.**

| Outcome | What it means | Is it a result? |
|---|---|---|
| Rig reproduces high `r` and fails the silence gate | The failure is a property of slowly-drifting multichannel arrays, not of cortex. Generalises to sensor-array health monitoring at large. | **Yes, and the stronger one** |
| Rig shows low `r` and passes the gates | The failure is neural-specific. The next BCI attempt needs neural-specific fixes, and you have said which. | **Yes** |
| Rig fails the Stage 6 baseline gate | An optical array cannot be tuned to cortical decoding difficulty. The analogy has a limit and you found where. | **Yes, and it is honest** |
| Natural drift (Arm B) matches no designed mode | Fault benchmarks built by writing equations may not resemble real degradation — including this project's own | **Yes, and it is the most surprising** |

---

## 15. Failure modes, and what to do about each

Recorded in advance, because the project's convention is that mistakes are part
of the record rather than something discovered later.

| # | Symptom | Most likely cause | What to do |
|---|---|---|---|
| F1 | Per-channel sd ≈ 0 across the whole frame | Exposure saturating every pixel, or the stimulus not running | Halve `ExposureTime`; confirm `stim_log.csv` is growing |
| F2 | Frame rate below target, drifting | SD card too slow, or too much per-frame Python work | Use an A2-class card; write `.npy` once at the end, not per frame |
| F3 | Angular error near chance from the start | Sync lag uncorrected (Procedure 4.2), or focus badly off | Re-measure the lag before touching anything else |
| F4 | Angular error implausibly low (< 20°) | Rig is far easier than cortex — **expected at first** | Add noise per §8.3, one variable at a time |
| F5 | `r` near zero at every spacing | No drift present at all; the rig may be *too* stable | This is a **finding**, not a fault. Report it, then run Stage 8B to place cortex on the curve |
| F6 | Results shift mid-study for no logged reason | Something moved, or auto-exposure re-enabled itself | Stop. Check `AeEnable` is still `False`. Treat every session after the last verified one as suspect |
| F7 | Gate G1/G2 unreachable in either direction | The analogy does not hold | **Stop and report it.** See the third row of the table in §14 |

---

## 16. Time and cost summary

| Stage | What | Wall-clock | Attended? |
|---|---|---|---|
| 0 | Preregistration | 2–3 hours | Yes |
| 1–4 | Build and calibrate | Two weekends | Yes |
| 5–6 | Baseline and the gate | 1 day | Mostly |
| 7 | Designed faults, ~200 blocks | 2–3 days | **No — unattended** |
| 8 | Autocorrelation, 130 blocks | 1–2 days | No |
| 9 | Undesigned faults | 1 day | Yes — each is a physical act |
| 10 | Sweeps, ~280 blocks | 2 days | No |
| 11 | Longitudinal | **6–10 weeks, in parallel** | No |
| 12 | Analysis | 1 day | Yes |

**Cost: ≈ $115 required, ≈ $135 with all optional parts, ≈ $75 if a spare screen
already exists.** No consumables, nothing hazardous, nobody recruited.
