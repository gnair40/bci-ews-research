# Building the apparatus, from nothing

This assumes you have never used a Raspberry Pi, never typed a command into a
terminal, and have never soldered anything. Every step says what to do and what
it is for. Nothing here is dangerous; see `03_MATERIALS_AND_SAFETY.md`.

Read `00_WHY_THIS_PHASE_EXISTS.md` and `01_RESEARCH_DESIGN.md` first if you have
not. Building the box before understanding what it is for is how projects end
up with a device and no result.

**Budget about two afternoons**, plus waiting for parts.

---

## Part 0 — the two words you need

**Terminal.** A window where you type commands instead of clicking. On the
Raspberry Pi, open the menu at the top-left and choose *Accessories → Terminal*.
On a Mac, press ⌘-space and type "Terminal". On Windows, install the Raspberry
Pi Imager and use *PowerShell* for the `ssh` step below.

Commands in this document look like this:

```bash
python3 physical/code/monitor.py --selftest
```

You type that line and press Enter. Capitalisation and spaces matter. The `$` or
`>` your terminal shows at the start of the line is not part of the command.

**Repository.** The folder containing this project, with all its code and
documents. On the Pi you will make a copy of it with `git clone` in Part 2.

---

## Part 1 — before you buy anything

Two design faults in the first version of this apparatus were caught here, in
seconds, on a laptop, before any part was ordered. Both would have wasted the
money and several weeks.

### 1.1 Check the analysis chain runs

On any computer with Python (not the Pi — you do not have it yet):

```bash
python3 physical/code/monitor.py --selftest
```

You should see `PASS — the pipeline is wired up correctly`. This builds a fake
recording in memory, decodes it, degrades it and checks the monitor reacts. If
it fails, the installation is broken, and it is much easier to find that out now
than on a Saturday with a camera in your hands.

If it says a module is missing:

```bash
pip3 install numpy scipy pandas
```

### 1.2 Check this machine can draw the pattern fast enough

```bash
python3 physical/code/stimulus.py --benchmark 300
```

The apparatus assumes the screen shows exactly 50 frames a second. If the
computer driving it cannot keep up, frames arrive late, **every camera frame's
direction label is wrong by an unknown amount, and nothing in the recording
says so.** This runs the real drawing arithmetic with no display attached — so
it works over SSH — and reports what the machine can actually sustain.

It needs no hardware, so run it now. **Then run it again on the Pi** once it is
set up (Part 2), because that is the machine that matters and it is several
times slower than a laptop.

If it fails there, it prints the options in order: move the stimulus to a faster
computer with the screen attached, lower `--patch`, or drop to 25 fps. The
second and third change the apparatus, so each says what to re-check and to
record it in the log.

### 1.3 Run the whole analysis on fake recordings

```bash
python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8
python3 physical/code/make_session_table.py --raw physical/data/dryrun/raw --tag _dryrun
python3 physical/code/analyze_falsealarm.py --tag _dryrun
python3 physical/code/analyze_leadtime.py --tag _dryrun
python3 physical/code/analyze_decision_rate.py --tag _dryrun
```

This manufactures twenty fake recordings and runs the entire analysis on them.
**None of those numbers are results** — they come from a formula someone wrote,
not from an apparatus. The point is only that the chain runs end to end and
produces reports. Delete them — and the reports they wrote — afterwards:

```bash
python3 physical/code/dryrun.py --cleanup
```

Not `rm -rf physical/data/dryrun`: that removes the fake recordings but leaves
the reports they generated sitting in the real results folder under real names.
`--cleanup` removes both, and identifies synthetic files by asking each one what
it is, so it cannot delete a real result.

### 1.4 The two faults this caught

**The apparatus as first specified decoded perfectly.** A simulation
(`scripts/72_rig_digital_twin.py`) put it at 0.0 degrees of error where the real
neural decoder sits at 54.6. An apparatus that good is useless here: degrade it
and almost nothing changes, so there is nothing for a monitor to detect. Two
settings were wrong — the modulation depth and the number of pixels averaged
into each channel — and both are now fixed at calibrated defaults.

**The calibrated stimulus asks for a fraction of a brightness level.** A screen
shows whole levels only, so rounding would have thrown the entire signal away.
The fix is spatial dithering, explained in `physical/code/stimulus.py`.

Neither would have been obvious from looking at the box.

---

## Part 2 — set up the Raspberry Pi

### 2.1 Write the SD card

1. On your normal computer, install **Raspberry Pi Imager** from
   `raspberrypi.com/software`.
2. Insert the microSD card.
3. Choose *Raspberry Pi OS (64-bit)*, choose your card, and open the settings
   (the gear icon) before writing:
   - set a hostname, e.g. `bci-rig`
   - **enable SSH** and set a username and password
   - enter your wifi name and password
4. Write the card. This takes a few minutes and erases the card.

*Why enable SSH:* it lets you control the Pi from your laptop over the network.
Once the box is sealed you cannot reach the Pi's own keyboard, and opening the
box to type something means re-taping it.

### 2.2 First boot

Put the card in the Pi, connect the power, and wait two minutes. From your
laptop's terminal:

```bash
ssh yourusername@bci-rig.local
```

Type the password you set. You are now typing commands that run on the Pi.

If `bci-rig.local` is not found, find the Pi's address in your router's
device list and use that instead, e.g. `ssh yourusername@192.168.1.42`.

### 2.3 Install the software

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-pygame python3-numpy python3-scipy python3-pandas git
```

- `picamera2` drives the camera.
- `pygame` draws the moving pattern on the screen.
- `numpy`, `scipy`, `pandas` do the arithmetic.
- `git` fetches this project.

*Why `apt` and not `pip` for these:* on Raspberry Pi OS the camera library is
built against the system, and the `pip` version usually does not work.

### 2.4 Get the project onto the Pi

```bash
git clone https://github.com/gnair40/bci-ews-research.git
cd bci-ews-research
git checkout claude/isef-research-pipeline-9zt4uq
python3 physical/code/monitor.py --selftest
```

**Why the `git checkout` line is there.** `main` works, but as of 24 September 2026 it does not yet carry the **frozen** preregistration — that work is on a branch awaiting merge, and data must not be recorded against an unfrozen preregistration. Delete the line once it is merged. See `physical/docs/12_RUNBOOK.md` step 0.1.

The self-test should pass here too. If it passes on your laptop and fails on the
Pi, something in 2.3 did not install.

### 2.5 Attach the camera

**Power the Pi off first.** Unplug it.

1. Find the camera connector — the thin black slot marked CAMERA, between the
   HDMI ports and the headphone socket.
2. Lift its small plastic tab straight up, gently.
3. Slide the ribbon cable in with the **silver contacts facing the HDMI ports**
   and the blue plastic backing facing the USB ports. Push it fully home.
4. Press the tab back down. Tug the cable very gently; it should not move.
5. Power the Pi back on.

Check it is seen:

```bash
rpicam-hello --list-cameras
```

A camera should be listed. If nothing is, the cable is in backwards or not
fully seated — this is the single most common problem at this stage, and
re-seating the cable fixes it almost every time.

---

## Part 3 — build the box

The screen goes at one end, the camera at the other, and no light gets in.

### 3.1 Line it

Line the **whole inside**, lid included, with matte black paper or paint. Glossy
black reflects; matte does not. Reflections put a faint copy of the screen onto
other parts of the image, which couples channels together — two channels that
should be independent stop being independent, and the monitor sees structure
that is a property of the cardboard.

### 3.2 Mount the screen

Fix the screen at one end, facing inward, filling as much of that end as
possible. On the screen itself:

- turn brightness to a fixed middle setting and **write the number down**
- turn **off** automatic brightness, ambient light sensing, dynamic contrast,
  any "enhancement" or "vivid" mode, and every power-saving dimmer
- set the screen never to sleep

*Why all of it matters:* the signal is about half of one brightness level out of
255. Any automatic adjustment is larger than the signal and will change during a
recording without telling you.

### 3.3 Mount the camera

At the opposite end, on its tripod or bracket, pointing at the screen. It must
be **rigid**. A camera that shifts by a millimetre between sessions changes which
part of the screen each channel is looking at, and every session after the shift
is a different apparatus.

Aim for the screen's grid to fill the camera's view with a small margin. You will
check this properly in Part 4.

### 3.4 Seal it

Bring the power and HDMI cables out through **one** hole, then tape over the hole
around the cables. Tape the lid seams. Tape any seam that shows light.

The test is Part 5's B-2, not your eyes: a dark room still has more light in it
than this box is allowed.

### 3.5 The degradation tools

**Neutral density filter.** Cut a piece large enough to cover the lens. You will
slide it in front of the lens by hand, at a time the software tells you.
Practise the movement: it should take under a second and must not knock the
camera.

**Tape for the dropout fault.** Small pieces of black tape, sized to cover 25%,
50% and 100% of the field. Cut them in advance and keep them somewhere you can
reach in the dark.

**Stepper motor** (optional, for the rotation fault by hand). Connect the ULN2003
driver board to the Pi's pins with the jumper wires:

| Driver board | Raspberry Pi pin |
|---|---|
| IN1 | GPIO 6 (physical pin 31) |
| IN2 | GPIO 13 (physical pin 33) |
| IN3 | GPIO 19 (physical pin 35) |
| IN4 | GPIO 26 (physical pin 37) |
| `-` (ground) | any GND, e.g. physical pin 39 |
| `+` (power) | **5 V, physical pin 2** |

**5 V, not 3.3 V.** The 3.3 V rail cannot supply the motor and may be damaged.
Count pins carefully: physical pin 1 is the corner nearest the SD card slot, and
the odd numbers run down one side.

The rotation fault is also available in software, which needs no motor at all.
The motor exists so that P-5 can impose a *physical* rotation — a fault nobody
designed the equation for.

---

## Part 4 — first light

Record something and look at it.

### 4.1 One short recording

On the Pi, with the box closed:

```bash
cd ~/bci-ews-research
python3 physical/code/run_session.py --session 0 --block 1 --calibration --frames 3000
```

3000 frames is one minute. `--calibration` means "this is for setting the
apparatus up, not for the experiment" — the analysis scripts keep those sessions
out of every result, because an apparatus being adjusted is not an apparatus
being measured.

You will see the stimulus window appear and the capture start. When it finishes
it prints where it wrote the files.

### 4.2 Did it arrive intact?

```bash
python3 physical/code/bench.py frames --session 0 --block 1
```

This is check **B-3/B-4**. It reports the frame rate, how many frames arrived
late, how many channels never change, and whether any are clipped at full
brightness. It tells you what to do about each.

Two failures here look identical from the outside and have different fixes:

- **frames arriving late** — the Pi could not keep up. Lower `--fps`, close
  other programs, or use a faster SD card.
- **dead channels** — the screen does not fill the camera's view, or part of it
  is in shadow. Move the camera or the screen, and record again.

Do not continue until this passes. Everything after it assumes the recording is
real.

---

## Part 5 — the bench checks

Each of these catches a failure that produces **plausible numbers rather than an
obvious error**. That is what makes them worth the hour they take.

| Check | What it asks | Command |
|---|---|---|
| B-0 | Can this machine draw at 50 fps? | `python3 physical/code/stimulus.py --benchmark 300` |
| B-1 | Does the software work at all? | `python3 physical/code/monitor.py --selftest` |
| B-2 | Is the box light-tight? | `python3 physical/code/bench.py darkframe` |
| B-3/4 | Did the recording arrive intact? | `python3 physical/code/bench.py frames --session 0 --block 1` |
| B-5 | How far behind the screen is the camera? | `python3 physical/code/bench.py lag --session 0 --block 1` |
| B-6 | Is the sub-level signal surviving? | `python3 physical/code/bench.py dither --session 0 --block 1` |
| B-7 | Is it as hard as the real thing? | `python3 physical/code/bench.py margin --session 0 --block 1` |

B-3 to B-7 can be run together:

```bash
python3 physical/code/bench.py check --session 0 --block 1
```

### B-2 — darkness

Turn the **screen off**, close the lid, and run:

```bash
python3 physical/code/bench.py darkframe
```

It needs the camera, so it only runs on the Pi. It passes if the average pixel
is below 2 and no pixel exceeds 5, out of 255.

*Why it matters:* room light varies over an afternoon. That variation would
appear as a slow drift in every channel, the monitor would detect it, and the
detection would be correct and completely uninteresting — a result about the
curtains.

If you cannot seal it well enough, the check tells you to record a dark frame
each session and subtract it. **Write that down as a deviation.** A subtracted
offset is not the same as no offset when the quantity being measured is drift.

### B-5 — timing

```bash
python3 physical/code/bench.py lag --session 0 --block 1
```

The screen and the camera are two separate programs. The screen puts up a
direction; the camera sees it slightly later. This measures that delay from the
signal itself — no extra hardware — and writes it to `physical/data/lag.json`,
which every analysis script then reads automatically.

Run it on **two or three different recordings**. If they agree, you are fine. If
they do not, the delay is varying, and no fixed correction can fix a varying
delay: drop to 25 frames per second, or hold each direction for five seconds
(`--hold 250`) and analyse only the middle three.

### B-6 — is the dither getting through?

```bash
python3 physical/code/bench.py dither --session 0 --block 1
```

The apparatus asks the screen for a change of about half of one brightness
level, and gets it by lighting a fraction of each patch's pixels one level
higher — spatial dithering. Some screens quietly destroy that with their own
processing.

**A small number here is correct.** A large agreement would mean the
calibration is wrong. What matters is that it is positive and consistent across
channels. If it fails, the check lists the causes in order of likelihood.

### B-7 — difficulty. This one is experiment P-1

```bash
python3 physical/code/bench.py margin --session 0 --block 1
```

The real neural decoder sits at **54.6° of error against a 90.7° chance level** —
a margin of **36.1°**. The apparatus must be tuned to roughly that before
anything else is recorded.

*Why an easy apparatus is a broken one:* if the direction can be read off
perfectly, degrading the system barely changes anything, so there is nothing for
a monitor to detect. Worse, comparing a system that decodes perfectly against
one that barely beats chance measures **difficulty**, not monitoring.

The knob is modulation depth, `--depth` in `stimulus.py`:

- **margin too large** (apparatus too easy) → lower `--depth`; halving it roughly
  doubles the error
- **margin too small** (too hard) → raise `--depth`, or raise `--exposure`, or
  average more pixels per channel by raising the capture size toward 96×64

Change **one** thing, record another calibration session, run B-7 again.

When it lands within 6° of 36.1:

> **Write the final `--depth` down, in the research log, and never change it
> again.** Every later session must use it. If it changes mid-campaign, sessions
> recorded before and after are not comparable, and nothing in the data will
> reveal that afterwards.

---

## Part 6 — what "ready" means

You are ready to record data when **all of these are true**:

- [ ] B-0 the Pi sustains 50 fps with room to spare
- [ ] B-1 self-test passes
- [ ] B-2 darkness passes with the box sealed
- [ ] B-3/4 frames arrive intact, no dead or clipped channels
- [ ] B-5 lag agrees across three recordings and `physical/data/lag.json` exists
- [ ] B-6 dither is positive and consistent
- [ ] B-7 margin is within 6° of 36.1°, and the depth is written down
- [ ] The screen's brightness setting is written down and every automatic
      adjustment is off
- [ ] The camera cannot move
- [ ] The research log records the date, the settings, and anything unusual

Then go to `06_DATA_COLLECTION.md`.

---

## Part 7 — things that will go wrong, and what they mean

| What you see | Most likely cause | What to do |
|---|---|---|
| `rpicam-hello` lists no camera | ribbon cable backwards or not seated | power off, re-seat with silver contacts toward the HDMI ports |
| Stimulus window does not appear over SSH | there is no screen attached to your SSH session | run it from the Pi's own desktop, or set `export DISPLAY=:0` first |
| Frames arriving late | Pi cannot keep up | run `stimulus.py --benchmark 300` on the Pi; then lower `--fps`, close other programs, faster SD card |
| Many dead channels | screen does not fill the camera's view | move the camera or screen, re-record |
| Channels clipped at 255 | screen too bright or exposure too long | lower `--brightness` or `--exposure` |
| B-6 fails | screen is processing the image | turn off every enhancement and dimmer; then try `--exposure 16000`; then try a different screen |
| B-7 margin far too large | apparatus too easy | lower `--depth` |
| "No space left on device" | recordings filled the SD card | move recordings to the USB drive |
| `run_session.py` refuses to record | no onset has been drawn for that session and block | run `draw_onset.py` first, or pass `--calibration` |

The last row is not a bug. It is the script enforcing the one rule the whole
phase depends on: the onset is decided, and checksummed, **before** the
recording exists.
