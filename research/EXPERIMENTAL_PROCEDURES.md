# Experimental Procedures

**Gayathri Nair**

This is my plan for the whole project, written as procedures somebody else could
follow. Phases 1 through 6 are the computational work. Phases 7 through 10 are
the physical experiment.

The computational phases are written at the level I planned them. The physical
phases are written in far more detail, because I have to build that part myself
and I want the instructions to be good enough that I do not have to guess at the
bench. Where something went differently than planned, that is in my research
journal rather than here. This document is the plan.

---

## Phase 0. Setting up so the work is checkable

**1.** Create a version-controlled repository with four separate folders: raw data
that never gets edited, processed data that scripts produce, the scripts
themselves, and written reports. Raw data is the only thing I cannot regenerate
by re-running code, so I keep it read-only and separate from everything else.

**2.** Record every Python library the project needs, with versions, in one file.
If a library quietly updates and a number changes, I want that to be something I
can check rather than something that silently happens.

**3.** Keep a dated research journal in the repository from day one, and write in
it the same day I do the work. The journal is where decisions, dead ends and
mistakes go. This procedures document is the plan; the journal is the record of
what actually happened.

---

## Phase 1. Getting the data

**4.** Choose a dataset of chronic intracortical recordings that spans months, so
that array degradation is actually present in it. I am using the MINDFUL deposit
from Pun et al., which is on Dryad under a CC0 license, was collected by other
researchers under their own approvals, and is de-identified. I recruit nobody and
no human participant is involved at any point in this project.

**5.** Register for Dryad API credentials through ORCID. The public download page
is protected against automated access, and I use the route the repository
supports rather than working around that protection. Supply the credentials as
environment variables so they are never written into a file, and delete the API
account when the download is finished.

**6.** Write a download script that asks the API which files exist, downloads
each one, and verifies its SHA-256 checksum against the value Dryad publishes. A
checksum is a fingerprint that changes completely if even one byte differs. If a
checksum does not match, stop, because nothing built on a corrupt download can be
trusted.

**7.** Write an inspection script that unpacks the archive and records what is
inside it. Doing this with a script rather than by hand means what the archive
contained on the day I opened it is written down in the repository.

**8.** Write a loader that converts the nested MATLAB files into flat tables: one
row per trial, one row per recording block, plus the neural arrays. Keep both the
original MATLAB indices and the converted Python ones, because MATLAB counts from
one and Python counts from zero, and getting that wrong shifts every trial.

**9.** Have the loader do no smoothing, no z-scoring and no outlier removal.
Those are not loading. Each one is a decision that changes what the results mean,
so I make them later where they are visible.

---

## Phase 2. Checking my tools before I trust them

I do not want to find out at the end that a null result came from a broken
detector. So before touching the real question, I test the tools on problems
where I already know the answer.

**10.** Confirm from the data itself that the decoder in the published study was
not being retrained during the recordings, rather than taking the paper's word
for it. My whole analysis assumes that.

**11.** Build two simulated systems: one that genuinely approaches a tipping
point, and one that only drifts steadily. Run my detector on both. It should fire
on the first and stay silent on the second. If it fails either, it is broken and
nothing it says about real data would mean anything.

**12.** Measure how much data the detector needs before it can find an effect
that is really there, by running it at different record lengths.

**13.** Check whether the real recordings are actually that long. If they are not,
that is a limit I need to know about now rather than later.

**14.** Reproduce a published figure from the original paper using my own code.
This is the only check that compares my pipeline against an answer somebody else
produced independently. If it matches, I am reading the data correctly.

**15.** Work out, in advance, the smallest effect I could detect with the amount
of data I have.

---

## Phase 3. Preregistering, then running the first analysis

**16.** Compare the possible definitions of "the decoder deteriorated" using only
task performance data, never the neural signal I will later use to predict it.
Pick one and lock it before going further. Picking after seeing which definition
gives the nicest result is the mistake this is meant to prevent.

**17.** Write the full analysis design to a file: which participant, which
outcome measure, which statistical test, what counts as success, and what result
would make me wrong. Include checksums of the input data files and the
identifier of the commit, so the design provably predates the analysis.

**18.** Require an explicit confirmation step before the design file can be
written, so freezing is something I have to mean to do.

**19.** Choose the neural measurement the indicator is built from, and write down
what I am ruling out and why, before computing anything.

**20.** Run the analysis exactly as frozen. Do not change settings, and do not
re-run it with different options to see what happens. Report the result whichever
way it comes out. A negative result answers the question; a tuned positive does
not.

---

## Phase 4. Building ground truth

In recordings that were only observed, nobody wrote down when the decline began,
so I cannot measure how early a warning arrived or how often it would be wrong.
Both numbers are the whole point. So I build data where I choose the onset.

**21.** Write an injector that takes a healthy recording and applies a controlled
degradation to it. Four kinds: overall signal loss, channels dying, channels
drifting apart while the total stays the same, and the pattern across channels
rotating while its size stays the same. The last two matter most, because a
detector that only counts activity should be blind to them.

**22.** For each episode, draw the degradation type, how fast it comes on, how
severe it gets, and the exact moment it starts. Write all of it to a file along
with a checksum of the list and the commit it was made at, before any detector
exists to be tested against it.

**23.** Make the injector refuse to redraw those start times unless I give it a
reason it can record. Ground truth I can quietly adjust is not ground truth.

**24.** Never modify the original data files. Store only the plan, and apply the
degradation in memory when an episode is scored.

**25.** Fit a simple model that predicts intended movement direction from neural
activity, then freeze it. Its only job is grading episodes, never detecting
anything. Measure its chance level by shuffling which neural data goes with which
movement, rather than assuming what chance should be.

**26.** Check the injector's own guarantees: that nothing before the onset differs
from the healthy recording, that the same episode comes out identical every time,
that severity levels are nested so a worse one is genuinely worse, and that the
modes which are supposed to leave overall activity unchanged actually do.

---

## Phase 5. Building the monitor, and the test it has to pass

**27.** Decide what every detector is allowed to see, and write it down. A
detector sees only the neural feature stream. Not the model's output, not the
task, not the performance score, and not any label saying a fault happened. It is
fitted on healthy data only. This is what stops it from learning the answer
instead of the phenomenon.

**28.** Write the grading system and commit it **before** writing my own monitor.
At that point the only detectors that exist are simple baselines I did not
invent, so the grading cannot have been shaped to flatter something that does not
exist yet.

**29.** Define the test a monitor has to pass, in advance, as a set of pass or
fail gates. The first and most important: it has to be quiet when nothing is
wrong. Then: it must not be explained away by overall activity, it must beat
simply counting activity, it must survive controlling for how much time has
passed, and its signal must be de-trended before being tested for a trend.

**30.** Build the monitor. Give it four named parts so that when it warns, it can
say which part produced the warning. A number on its own does not tell a user
what to do.

**31.** Include "the user is doing something different" as an explicit thing the
monitor can report, not as a false alarm. A monitor that cries wolf when somebody
switches application trains its user to ignore it.

**32.** Score every combination of detector, data transformation and baseline
strategy. Report all of them. Do not drop the ones that look bad.

**33.** Report how early a warning arrives and how often it is wrong **as a pair,
always**. Either number alone can be made to look good.

---

## Phase 6. Interrogating the result

Whatever Phase 5 returns, I want to know why, and I want to try to break it.

**34.** Ask whether the information is present at all, with every threshold and
state machine stripped away.

**35.** Ask whether a better decision rule would help, by comparing rules across
their whole range rather than at one setting.

**36.** Ask whether averaging more measurements helps, by measuring how
independent consecutive measurements actually are.

**37.** Ask whether different input measurements would help. Name the candidate
families in advance, close the list, and fix the success criterion before
computing anything. Require an improvement on **both** participants in the same
direction, so that something helping one and hurting the other counts as a null.

**38.** Ask what makes a good session different from a bad one. Commit the
direction I expect each predictor to go before computing it, and correct for
testing several at once.

**39.** Try to break my own headline finding, on purpose, with a preregistered
challenge. If it survives, I trust it more. If it does not, I withdraw it.

**40.** Keep a register of every claim the project makes, with its status:
established, a limitation, withdrawn, unanswerable, or exploratory. Withdrawn
claims stay in the repository marked "do not quote" rather than being deleted.
Write a script that recomputes every number I quote straight from the stored data
files, so a figure that stops matching its source is something I find out about.

---

# The physical experiment

Everything above analyzes recordings somebody else made. The rest of this
document is the part I build.

## What this experiment tests

**The main question: is what I found a fact about brains, or a fact about any
sensor that drifts slowly?**

My computational result rests on one measurement. Within a recording session, my
monitor's readings barely vary independently of each other. A session that looks
like 55 measurements behaves like roughly one measurement taken 55 times. That is
why averaging does not help, why no decision rule rescues it, and why nothing
passes the gates.

But I found that in two electrode arrays, in two people. That is the entire
evidence base. If somebody asks whether it is specific to cortex or just what
happens to any drifting sensor, I cannot answer, because there is no second kind
of system in the dataset to compare against.

**So I build one.** The rig is a completely different physical system, light and
a camera rather than neurons and electrodes, that shares the one property that
might be causing the problem: many channels, drifting slowly. Then I run the
identical analysis on it, with no change to any script.

| If the rig behaves like this | Then the conclusion is |
|---|---|
| About one independent measurement per session, the same as cortex | The problem is not neurons. It is the shape of this kind of measurement problem, and the finding applies to sensor health monitoring in general. |
| Many independent measurements per session | Something specific to cortex causes it, and the next attempt at a neural monitor needs a neural-specific fix rather than better statistics. |
| Cannot be made comparable to cortex at all (Procedure 71) | The analogy has a limit and I found where it is. |

**Both of the first two answers are useful.** That is the test of whether this is
a real experiment rather than a demonstration, and it is why I am willing to
build it before knowing the outcome.

### The strong version of that question

Asking "does the rig match cortex, yes or no" invites the obvious objection that
a camera is not a brain. Procedure 78 asks a better question. Instead of
comparing one system against one other system, I impose a drift speed I control,
sweep it across the range where the measurement still responds — a bit over two
orders of magnitude, worked out in Procedure 78 — and measure monitorability at
each speed.

That produces a curve: **how well can an array be monitored, as a function of how
fast it drifts**, with cortex marked as a single point on it. That is much harder
to argue with than a binary comparison, and it turns a negative result into
something usable. A future array that drifts more slowly, or a different
windowing scheme, can be placed on the same curve and evaluated before anybody
builds it.

Procedure 78 is the centerpiece of this experiment. Everything before it exists
to make its measurement trustworthy.

## Two further questions it answers

**Are my injected degradations realistic?** All 1,850 of them are equations
applied to recorded numbers, and nobody has checked whether real degradation
resembles them. On the rig I can cause real faults, by loosening a connector,
smudging the lens or warming the board, where I know the start time because I
caused it but I did not design what the fault would look like. If those do not
resemble the ones I invented, that is a finding about how fault benchmarks get
built, including mine. Procedure 75.

**Can I separate the session variables?** In the archived data, decoder error,
trace noise, task geometry and several other properties all move together, and I
had to withdraw a claim because I could not tell which one mattered. On the rig I
can hold one fixed and vary the other, which is the manipulation recorded data
cannot offer. Procedure 79.

## The design in one sentence

A camera watches a screen showing a pattern that encodes a known direction, each
region of the camera image acts as one channel, a decoder predicts the direction
from those channels, and then I degrade the system in ways I control and log.

## What I am not claiming

I am not claiming a camera resembles a neuron. The claim under test is about a
class of measurement problem, many channels drifting slowly, and not about
biology. That limitation is real and I state it rather than defend against it.

## What I committed to before building anything

The whole point of writing predictions down first is that testing five things and
reporting the one that worked looks identical on paper to predicting one thing
correctly. `research/RIG_PREREGISTRATION.md` is what keeps those two apart, and
it only works if it is committed to git before the first recording exists. The
predictions are reproduced here so that somebody reading only these procedures
can see what I was on the hook for. **The preregistration is the authority; if
the two ever disagree, that document wins.**

| # | Prediction | Threshold | Falsified if | Measured by |
|---|---|---|---|---|
| P-R1 | With no fault and no imposed drift, the rig's quiet-state serial correlation looks like cortex's | non-overlap lag-1 r **between −0.12 and +0.54** | median r outside that band | `scripts/66_window_spacing.py`, unchanged |
| P-R2 | A monotone fault raises serial correlation on hardware too | faulted r exceeds fault-free r by **≥ 0.20** | the rise is under 0.20, absent or negative | `scripts/70_autocorr_by_severity.py` |
| P-R3 | The silence gate fails on hardware too | **> 10%** of healthy rig episodes show a significant trend | 10% or fewer | Procedure 73 |
| P-R4 | Ladder validity degrades as the baseline drifts, on hardware too | correlation **ρ < −0.4** between baseline error and ladder validity | ρ ≥ −0.4 | Procedure 74 |
| P-R5 | The invariant-feature route fails again | invariant detector scores **worse** than the plain one | invariant scores better | Procedure 76 |
| P-R6 | Faults I cause but did not design are harder than the ones I invented | AUC lower by **≥ 0.03** | gap under 0.03, or the wrong way | Procedure 75 |
| P-R7 | Natural drift resembles at least one designed fault mode | nearest-mode match **above chance (25%)** | at or below chance | Procedure 77 |

Every row has a useful outcome in both directions, which is the test of whether
this is an experiment rather than a demonstration. P-R1 confirmed means the
negative result generalises past cortex to sensor health monitoring in general;
P-R1 falsified means the failure is neural-specific and the next attempt needs a
neural-specific fix. P-R7 falsified is the sharpest of the lot: it would mean
1,850 episodes of carefully built ground truth do not resemble what actually goes
wrong, which belongs in the write-up as a headline rather than a limitation.

**P-R2 is not independent of P-R1**, and deliberately so: both read the same
quantity. P-R1 bounds the quiet state, P-R2 tests what a fault does to it. They
are reported as one finding with two parts and never counted as two pieces of
evidence. P-R1 is a wide band and therefore weak — it rules out a rig pinned at
zero or at its ceiling and little else. **P-R2 carries the evidential weight**,
because the fault-driven rise is large (+0.838 on T11, +0.390 on T5), in the
same direction on both participants, and measured on hundreds of episodes
rather than the seventeen behind the fault-free level.

> **P-R1 and P-R2 were retargeted on 19 September 2026.** Both originally took
> their thresholds from claim C18's pooled 0.902 and 0.784, which turned out to
> be raised by the sub-threshold fault ramp injected into those episodes rather
> than measured on fault-free recording. Fault-free, the same measurement gives
> 0.085 on T11 and 0.435 on T5, so the old bar of 0.70 sat *above* both and
> P-R2's "fewer than 2 independent samples" pointed the wrong way entirely
> (fault-free gives 8.44 and 2.75). The amendment, with the original wording
> preserved, is `research/RIG_PREREGISTRATION.md` §12. The rows above are the
> amended versions.

---

## Phase 7. Building the rig

### Materials

| # | Item | Specification | Qty | ~Cost |
|---|---|---|---|---|
| M1 | Raspberry Pi 4 Model B | 4 GB RAM | 1 | $55 |
| M2 | microSD card | 32 GB, A2 or U3 speed class | 1 | $10 |
| M3 | Power supply | Official Raspberry Pi USB-C, 5 V 3 A | 1 | $8 |
| M4 | Raspberry Pi Camera Module 3 | With the 15-pin ribbon it ships with | 1 | $25 |
| M5 | Display | Any monitor, tablet or old laptop, at least 1280x720, brightness adjustable | 1 | $0-40 |
| M6 | Enclosure | Cardboard box at least 40 x 30 x 30 cm | 1 | $5 |
| M7 | Matte black paper or paint | Enough to line the box inside, lid included | 1 | $6 |
| M8 | Camera mount | Small tripod or a rigid bracket | 1 | $8 |
| M9 | Black tape | Gaffer or electrical | 1 roll | $4 |
| M10 | Stepper motor and driver | 28BYJ-48 5 V with ULN2003 board | 1 | $5 |
| M11 | Jumper wires | Female to female, 20 cm | 6 | $3 |
| M12 | Neutral density filter | Photographic ND 0.6 gel sheet | 1 | $8 |
| M13 | Temperature and humidity sensor | DHT22 or AM2302, on a breakout with the pull-up resistor fitted | 1 | $5 |
| M14 | External storage | 128 GB USB stick | 1 | $15 |

Total about $150, or about $110 if I already have a spare screen. Nothing on this
list is hazardous. There is no mains wiring, no soldering required, no chemicals,
and no heating element.

### Safety

**41.** Confirm with my SRC, rather than assume, that no ISEF form is required.
Nothing in this experiment measures, records or images a person, including me.
The camera is inside a closed box pointing at a screen.

**42.** Keep hands clear of the stepper motor while it is powered, and never run
it with the box open and my hand inside. It is a weak motor but the bracket edges
are not soft.

**43.** Do not sit and stare into the enclosure with the screen at full
brightness. Close the box; that is what it is for.

**44.** When warming the camera as one of the degradations, use a hair dryer on
its lowest setting, at least 30 cm away, in bursts of no more than 60 seconds,
and never let the camera board exceed 50 degrees Celsius. No heat gun, no
hotplate, no open flame.

**45.** Power the Pi off every single time before connecting or disconnecting the
camera ribbon. The connector breaks easily.

### Setting up the Pi

**46.** Download Raspberry Pi Imager from raspberrypi.com/software onto my normal
computer. Select Raspberry Pi 4 as the device, Raspberry Pi OS 64-bit as the
operating system, and the microSD card as the target.

**47.** In Imager's settings, which is the gear icon, set the hostname to `rig`,
enable SSH, set a username and password, and enter my Wi-Fi details. SSH lets me
control the Pi over the network so the box can stay closed while it runs.

**48.** Write the card, put it in the Pi, and connect the power supply.

**49.** From my normal computer, connect with:
```
ssh myusername@rig.local
```
If that name does not resolve, find the Pi's address in my router's device list
and use the address instead.

**50.** Install what the project needs:
```
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-picamera2 python3-numpy python3-scipy python3-pygame git
```

**51.** With the Pi powered off, connect the camera. Lift the black tab on the
connector labeled CAMERA, slide the ribbon in with the blue side facing the
ethernet port, and press the tab back down. Power on, then test:
```
rpicam-hello --timeout 5000
```
On older releases this command is called `libcamera-hello`. If this fails, stop
and fix it before doing anything else. Everything after this depends on the
camera working.

**52.** Measure the frame rate I can actually hold:
```
rpicam-vid --width 480 --height 320 --framerate 50 --timeout 10000 \
  --codec yuv420 -o /dev/null --info-text "%fps"
```
Write down the number I actually get, not the one I asked for. If it holds near
50, one frame is one 20-millisecond bin and the analysis constants match the
neural data exactly. If it only holds near 30, I use 1/30 second per bin, keep
the same number of bins per window, and report that a window is 50 seconds of
wall clock instead of 30.

### Building the enclosure

**53.** Line the inside of the box with matte black paper or paint, **including
the lid**. Room light changes with the time of day and the weather, and over a
six-week recording that would look exactly like the degradation I am trying to
measure.

**54.** Cut one hole at one end for the cables and one panel at the other end
sized to the screen. Tape every seam and every gap that is left.

**55.** Fix the screen facing into the box at one end. It must not move for the
life of the experiment, so tape the frame down rather than relying on a stand.

**56.** Fix the camera at the other end on its mount, pointing at the screen,
square and level. Set the distance so the pattern fills about 80 percent of the
frame width. Leave the dark margin on purpose: those regions see no signal and
give me a free reference for background noise.

**57.** Tape every cable to the box wall about 5 cm from its connector. If a cable
works itself loose partway through a recording I get a fault I did not log at a
time I do not know, and that is the one thing this design cannot survive.

**58.** Take a photograph of the finished rig, with a ruler in frame for scale,
and put it in the repository. If anything moves later I want to be able to tell.

---

## Phase 8. The stimulus and capture programs

### What the stimulus has to be, and why

A moving dot would make each image region respond to **where** the dot is, which
is position information. Real neural channels respond to **which direction** the
person means to move. So instead I give every region a fixed preferred direction,
drawn once at random, and set its brightness according to how close the current
heading is to that preference. That makes each region behave like a
direction-tuned channel, and the decoding problem becomes the same shape as the
neural one.

The encoding is designed, because I have to put a known signal in. The sensing,
the noise, the optics and every degradation are physical. Nothing about the thing
I am trying to detect is simulated.

**59.** On the machine driving the screen, create a folder called `rig` and save
this as `rig/stimulus.py`:

```python
#!/usr/bin/env python3
"""Shows a grid of patches whose brightness encodes a heading direction.

Each patch has a fixed preferred direction. Its brightness is highest when the
current heading matches that preference, the same way a direction-tuned neuron
fires fastest for its preferred direction.

Writes rig/stim_log.csv, one row per frame, holding the true heading. That file
is the ground truth for the whole experiment, so it is recorded rather than
reconstructed afterwards.
"""
import argparse, csv, math, time
import numpy as np
import pygame

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=24)
ap.add_argument("--rows", type=int, default=16)     # 24 x 16 = 384 channels
ap.add_argument("--patch", type=int, default=40)    # screen pixels per patch
ap.add_argument("--fps", type=int, default=50)      # must match the camera
ap.add_argument("--hold", type=int, default=100)    # frames per heading
ap.add_argument("--frames", type=int, default=15000)  # 5 min at 50 fps
ap.add_argument("--brightness", type=float, default=1.0)  # 0-1, for the SNR sweep
ap.add_argument("--seed", type=int, default=20260826)
ap.add_argument("--concentration", type=float, default=0.0)  # 0 = all directions
ap.add_argument("--out", default="rig/stim_log.csv")
a = ap.parse_args()

N = a.cols * a.rows
rng = np.random.default_rng(a.seed)

# Preferred directions are fixed for the life of the rig. Save them once and
# reuse the saved file, so the channel identities never change between sessions.
try:
    PREF = np.load("rig/preferred_directions.npy")
    assert len(PREF) == N
except Exception:
    PREF = rng.uniform(0, 2 * math.pi, N)
    np.save("rig/preferred_directions.npy", PREF)

pygame.init()
screen = pygame.display.set_mode((a.cols * a.patch, a.rows * a.patch))
clock = pygame.time.Clock()

log = open(a.out, "w", newline="")
w = csv.writer(log)
w.writerow(["frame", "t_unix", "heading_rad", "trial"])

def draw_heading():
    """Uniform over all directions by default. Raising --concentration makes
    headings cluster, which is the task-geometry variable I sweep in Phase 9."""
    if a.concentration <= 0:
        return rng.uniform(0, 2 * math.pi)
    return float(rng.vonmises(0.0, a.concentration))

heading, trial = draw_heading(), 0
try:
    for f in range(a.frames):
        if f % a.hold == 0:
            heading, trial = draw_heading(), f // a.hold
        b = 0.5 * (1 + np.cos(heading - PREF)) * a.brightness
        for i in range(N):
            v = int(np.clip(b[i], 0, 1) * 255)
            pygame.draw.rect(screen, (v, v, v),
                             ((i % a.cols) * a.patch, (i // a.cols) * a.patch,
                              a.patch, a.patch))
        pygame.display.flip()
        w.writerow([f, time.time(), heading, trial])
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise KeyboardInterrupt
        clock.tick(a.fps)
finally:
    log.close()
    pygame.quit()
```

**60.** Run it once to check it works:
```
mkdir -p rig
python3 rig/stimulus.py --frames 500
```
I should see a grid of grey squares whose brightnesses shift every two seconds.
Check that `rig/stim_log.csv` has one row per frame before going any further. If
the heading column is missing or wrong, nothing downstream can be scored.

**61.** On the Pi, save this as `rig/capture.py`:

```python
#!/usr/bin/env python3
"""Records frames and reduces each one to N region averages.

Each region average is one channel, the same way each electrode's binned
activity is one channel in the neural data.

Exposure and white balance are FIXED. The automatic versions are compensators:
leave them on and the camera quietly cancels out the very degradation I am
trying to measure.
"""
import argparse, time
import numpy as np
from picamera2 import Picamera2

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=24)
ap.add_argument("--rows", type=int, default=16)
ap.add_argument("--width", type=int, default=480)    # 480/24 = 20 px per region
ap.add_argument("--height", type=int, default=320)   # 320/16 = 20 px per region
ap.add_argument("--fps", type=int, default=50)
ap.add_argument("--frames", type=int, default=15000)
ap.add_argument("--exposure", type=int, default=8000)   # microseconds
ap.add_argument("--gain", type=float, default=2.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

assert a.width % a.cols == 0 and a.height % a.rows == 0, \
    "frame size must divide evenly into the region grid"

cam = Picamera2()
cam.configure(cam.create_video_configuration(
    main={"size": (a.width, a.height), "format": "RGB888"},
    controls={"FrameRate": a.fps}))
cam.set_controls({"AeEnable": False, "AwbEnable": False,
                  "ExposureTime": a.exposure, "AnalogueGain": a.gain})
cam.start()
time.sleep(2)               # let the sensor settle before recording

rows, ts = [], []
try:
    for _ in range(a.frames):
        img = cam.capture_array("main")[:, :, 1].astype(np.float32)  # green
        r = img.reshape(a.rows, a.height // a.rows,
                        a.cols, a.width // a.cols).mean(axis=(1, 3))
        rows.append(r.ravel())
        ts.append(time.time())
finally:
    cam.stop()

np.save(a.out, np.asarray(rows, dtype=np.float32))
np.save(a.out.replace(".npy", "_t.npy"), np.asarray(ts))
print(f"wrote {a.out}  shape={np.asarray(rows).shape}")
```

**62.** Test the whole loop. Start the stimulus on the screen, then on the Pi:
```
python3 rig/capture.py --frames 500 --out rig/test_block.npy
python3 -c "
import numpy as np
x = np.load('rig/test_block.npy')
print('shape', x.shape)
print('per-channel sd: min', round(float(x.std(0).min()),2),
      'median', round(float(np.median(x.std(0))),2),
      'max', round(float(x.std(0).max()),2))
"
```
I want a shape of (500, 384) and a per-channel standard deviation clearly above
zero for the channels that can see the grid. A channel at zero is either in the
dark margin, which is expected, or dead, which is not. If everything is near
zero, the exposure is saturating every pixel or the stimulus is not actually
running.

**63.** Measure the delay between the screen changing and the camera seeing it.
Run a stimulus that goes fully black for one frame in every hundred, record 2000
frames, find the frames where total brightness dips, and compare against the
logged time. Subtract that delay from every recording from now on, and measure it
again if I change the screen, the exposure or the frame rate. An uncorrected
delay rotates every channel's apparent tuning, and the result looks like a
mediocre decoder rather than a timing bug.

**64.** Save this as `rig/to_mat.py`, which converts a recording into the file
layout my analysis already reads, so no analysis code has to change:

```python
#!/usr/bin/env python3
"""Turns one recorded block into the three .mat files the loader expects."""
import argparse
from pathlib import Path
import numpy as np
from scipy.io import savemat

ap = argparse.ArgumentParser()
ap.add_argument("--block", required=True)     # rig/xxx.npy from capture.py
ap.add_argument("--stimlog", required=True)   # rig/stim_log.csv
ap.add_argument("--session", type=int, required=True)
ap.add_argument("--blocknum", type=int, required=True)
ap.add_argument("--lag", type=float, default=0.0)   # seconds, from Procedure 63
ap.add_argument("--root", default="data/raw_rig")
a = ap.parse_args()

X = np.load(a.block)
t_cam = np.load(a.block.replace(".npy", "_t.npy")) - a.lag
stim = np.genfromtxt(a.stimlog, delimiter=",", names=True)

# For each captured frame take the heading logged closest in time.
idx = np.searchsorted(stim["t_unix"], t_cam).clip(0, len(stim) - 1)
head = stim["heading_rad"][idx]
trial = stim["trial"][idx].astype(int)

n = len(X)
cursor = np.zeros((n, 2), np.float32)
target = np.stack([np.cos(head), np.sin(head)], 1).astype(np.float32)

# One trial per run of constant heading.
edges = np.flatnonzero(np.diff(trial)) + 1
starts = np.concatenate([[0], edges])
stops = np.concatenate([edges, [n]])
keep = (stops - starts) >= 10
starts, stops = starts[keep], stops[keep]
ntr = len(starts)

bd = Path(a.root) / "RIG" / f"day_{a.session}" / f"block_{a.blocknum}"
bd.mkdir(parents=True, exist_ok=True)
savemat(bd / "data.mat", {"nctx": X.astype(np.float32)})
savemat(bd / "info.mat", {
    "cursorPos": cursor, "targetPos": target,
    "angleErrorPerTrial": np.full(ntr, np.nan),
    "trialSuccess": np.ones(ntr, bool),
    "timeToTarget": np.full(ntr, np.nan),
    "pathEfficiency": np.full(ntr, np.nan),
    "orthChanges": np.zeros(ntr),
    "percentCorrect": np.nan})
savemat(bd / "task.mat", {
    "startStops": np.stack([starts + 1, stops], 1).astype(float),  # MATLAB is 1-based
    "name": "rigCosineField",
    "excludeTrials": np.zeros(ntr, bool),
    "useClick": np.zeros(ntr, bool)})
print(f"wrote {bd}  {n} bins, {ntr} trials")
```

**65.** Confirm the format is right before recording anything real:
```
python3 scripts/67_rig_format_check.py
python3 scripts/68_rig_pipeline_dryrun.py
```
The first checks a rig file loads. The second runs every analysis stage against a
synthetic rig dataset. Both must print PASS. Neither produces data I may cite;
they only answer whether the code runs.

---

## Phase 9. Calibrating, and the gate I have to pass

**66.** Record 20 healthy blocks with nothing degraded, 15000 frames each:
```
for i in $(seq 1 20); do
  python3 rig/run_block.py --session 1 --blocknum $i --lag 0.0
done
```
`run_block.py` starts the stimulus, starts the capture, waits for both, converts
the result, and appends the settings to `rig/blocklog.csv`. Doing those four
steps by hand twenty times is how a typo gets into a dataset. The loop above
originally called `capture.py` and `to_mat.py` directly and got the arguments
wrong in both places.

**67.** Fit the decoder on the rig baseline and measure its chance level:
```
python3 scripts/18_reference_decoder.py fit --participant RIG --raw-root data/raw_rig
```

**68.** Compare the rig's healthy behavior against the neural data's healthy
behavior, and decide whether to continue. The rig must reach:

| | Neural value | Rig must reach |
|---|---|---|
| Decoder skill, chance minus held-out error | 36.1 degrees | 25 to 47 degrees |
| Held-out angular error | 54.6 degrees | 45 to 65 degrees |
| Channel count | 384 | exactly 384 |
| Samples per window | 1500 | exactly 1500 |
| Dead channels outside the dark margin | n/a | under 5 percent |

**69.** Note what is deliberately **not** on that list: autocorrelation, effective
sample size, detection accuracy and silence-gate pass rate. Those are the things
the experiment is testing. If I tuned the rig to match those too, I would be
guaranteeing my own result.

**70.** Expect the rig to start out too good, because the encoding is clean. If
the decoder's error is far below 45 degrees, add noise physically, one variable
at a time, re-running Procedure 67 after each change: lower the screen
brightness, shorten the exposure, raise the gain, then defocus very slightly.
Record every setting I land on. Once the gate passes, those settings are fixed
for the whole study.

**71.** **If the gate cannot be met in either direction, stop here and report
that.** An optical array that cannot be tuned to cortical difficulty is a real
finding about where the comparison breaks down, and it is much better than
introducing faults into a system I never showed was comparable.

---

## Phase 10. Running the experiment

**72.** Before recording a single degraded block, write my predictions with
numbers in them to `research/RIG_PREREGISTRATION.md`, commit it, and paste the
resulting commit identifier back into the file. Building continues only after
that commit exists.

**73.** Draw and lock the degradation schedule:
```
python3 scripts/17_fault_injector.py plan --participant RIG --raw-root data/raw_rig
git add data/processed/injection_plan_RIG.json
git commit -m "Lock the rig injection plan before any fault is recorded"
```

**74.** Record the **designed** degradations by changing what the screen emits,
following the plan exactly. Overall signal loss is a global brightness ramp.
Channels dying is setting a nested set of patches to black. Channels drifting
apart is per-patch brightness multipliers rescaled so the mean is unchanged.
Pattern rotation is rotating which patch shows which preferred direction. Do not
look at a single result until every session in the plan is recorded.

**75.** Record the **undesigned** degradations, where I control and log the
timing but the appearance in the data comes from physics rather than from
anything I designed. Write down the frame number and what I did at the moment I
do it, not afterwards:

| ID | What I do |
|---|---|
| U1 | Rotate the camera 15 degrees on the stepper, mid-block |
| U2 | Slide the ND filter in front of the lens |
| U3 | Unseat the camera ribbon by one notch |
| U4 | Warm the camera with a hair dryer, per Procedure 44 |
| U5 | Place a phone making a call next to the ribbon |
| U6 | Put one fingerprint smudge on a corner of the lens |

**76.** Report designed and undesigned results in **separate tables**. Whether
findings carry from one to the other is a claim I want to test, not assume.

**77.** Measure the natural autocorrelation with no imposed drift at all: 50
healthy blocks across at least five separate days, powering the rig down between
days so thermal state and dust can change. This measurement is the non-circular
one, because I imposed nothing.

**78.** Build the calibration curve. **This is the main measurement of the
experiment.** Impose a slow brightness drift with a known time constant, sweep
that constant, record healthy blocks at each level, then plot autocorrelation and
effective sample size against drift speed and mark where the neural value falls
on that curve. This turns a yes-or-no prediction into a relationship, which is a
better experiment: it says how monitorable an array is as a function of how fast
it drifts, with cortex marked on it.

The numbers to use are **5 levels log-spaced between 4 s and 811 s, with 53
blocks at each** — about 22 hours of recording. Run `python3
scripts/71_drift_sweep_design.py` to regenerate them;
`reports/DRIFT_SWEEP_DESIGN.md` shows the working.

That replaces what this procedure originally said, which was eight levels from
5 s to 2000 s at 10 blocks each. Those were guesses, and working them out
properly found three things worth knowing before any part is bought:

- **Ten blocks per level cannot resolve the curve.** At 300 s per block the
  measured autocorrelation has a 95% half-width of about 0.22 at 10 blocks,
  against a step between adjacent levels of about 0.11. The half-width falls
  only as one over the square root of the block count.
- **Eight levels is not affordable.** Resolving eight levels needs roughly 153
  blocks each, which is about 102 hours of recording. Fewer levels means a
  bigger step, and the cost of resolving a step falls as its square — hence 5.
- **The measurement has a ceiling I cannot design around.** A 300-second block
  gives 10 non-overlapping windows, and the sample autocorrelation is badly
  biased downward at 10 points: a signal whose true correlation is 0.999 reads
  about 0.60. No imposed drift, however slow, pushes one block above that. Any
  value near the ceiling gets reported with the ceiling beside it.

The first two are schedule problems. The third is not, and it applies to the
neural numbers already in this project as well as to the rig — every no-overlap
figure here understates whatever correlation is really there. That direction
makes the negative results look weaker than they are, not stronger.

**79.** Sweep baseline signal quality across about 20 brightness levels, 10 short
blocks each, and find where angular error stops responding. Then sweep heading
concentration across 5 levels using `--concentration`. Then run the two crossed,
4 by 4, 5 blocks per cell. That crossed design is the manipulation the archived
data cannot offer, because it varies one thing while holding the other fixed.

**80.** Start the long-duration arm the same day the rig first passes the gate,
and run it in parallel with everything else. One identical healthy session per
day for six to ten weeks, with nothing introduced, logging temperature and
humidity alongside. Schedule it with:
```
crontab -e
```
and add:
```
0 3 * * * /usr/bin/python3 /home/pi/rig/daily_session.py >> /home/pi/rig/cron.log 2>&1
```
Three in the morning, because conditions are most stable and nobody will open the
box.

**81.** Change nothing during those weeks. If I do touch the rig, write down what
I did and when. An intervention I did not log cannot be told apart from a
finding.

**82.** Analyze everything with the same code, unchanged:
```
python3 scripts/20_evaluation_harness.py run --participant RIG --raw-root data/raw_rig --local
python3 scripts/21_score_report.py --participant RIG
python3 scripts/29_aggregation_limit.py
python3 scripts/66_window_spacing.py
```

**83.** Do not write or modify any analysis code after seeing the rig data. The
analysis was written, frozen and checked before the rig existed, and that is the
answer to anyone who suggests the result was shaped to fit.

**84.** Report the outcome whichever way it goes, and say in advance what each
outcome would mean:

| Outcome | What it means |
|---|---|
| The rig behaves like the neural data | The failure is a property of slowly drifting sensor arrays in general, not of brains |
| The rig behaves differently | The failure is specific to neural recordings, and I can say which way |
| The rig cannot pass the Phase 9 gate | The comparison has a limit and I found where it is |
| Natural drift matches no designed degradation | Fault benchmarks built by writing equations may not resemble real degradation, including mine |
