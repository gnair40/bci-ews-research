# Materials and safety

Everything you need to buy, why each item is there, and what the risks are.

---

## 1. What you are building

A sealed dark box with a screen at one end and a camera at the other. The screen
shows a grid of grey patches; the camera watches them. Each small region of the
camera image acts as one "channel", standing in for one electrode in a brain
implant. That is the whole apparatus.

**Nothing on this list is hazardous.** There is no mains wiring, no soldering
required, no chemicals, no heating element, and no part that gets hot.

---

## 2. Materials

### 2.1 Computing

1. **Raspberry Pi 4 Model B, 4 GB RAM** — the small computer that runs the
   camera. *Why this one:* a Pi Zero is too slow to capture 50 frames a second;
   a Pi 5 uses a different camera connector and a different software stack.
2. **microSD card, 32 GB, speed class A2 or U3** — the Pi's hard drive. *Why the
   speed class:* slower cards drop frames during recording.
3. **Official Raspberry Pi USB-C power supply, 5 V 3 A** — *Why the official
   one:* phone chargers often sag under load and the Pi silently throttles,
   which changes the recording rate mid-session.
4. **microSD card reader** — to write the card from your normal computer, if
   your laptop has no SD slot.

### 2.2 The sensor

5. **Raspberry Pi Camera Module 3**, with the ribbon cable it ships with. *Why
   the supplied cable:* the Pi 4's connector is the older wider type, and a
   cable bought separately may be the narrower Pi-5 kind and will not fit.
6. **Display** — any monitor, tablet or old laptop screen, at least 1280 × 720,
   with **manual brightness control**. *Why manual matters:* automatic
   brightness, ambient-light adjustment and power-saving dimmers all silently
   cancel the degradation you are trying to measure.

### 2.3 The enclosure

7. **Cardboard box**, at least 40 × 30 × 30 cm.
8. **Matte black paper or matte black paint**, enough to line the inside
   including the lid. *Why matte:* glossy black reflects, which is the problem
   you are trying to remove.
9. **Camera mount** — a small tripod or any rigid bracket.
10. **Black tape** — gaffer or electrical, one roll.

*Why the box matters more than it looks:* the signal being measured is about
half of one brightness level out of 255. Room light varies with the time of day
and would masquerade as sensor drift.

### 2.4 Degradation tools

11. **Stepper motor and driver**, 28BYJ-48 5 V with a ULN2003 board — rotates
    the stage for the geometric fault, in repeatable units.
12. **Jumper wires**, female-to-female, 20 cm, six of them — to connect the
    motor board to the Pi. No soldering.
13. **Neutral density filter**, photographic ND 0.6 gel sheet — reduces the light
    reaching the camera for the signal-loss fault. Inert plastic.

### 2.5 Monitoring the environment

14. **Temperature and humidity sensor**, DHT22 or AM2302, on a breakout board
    with the pull-up resistor already fitted. *Why:* a camera sensor's noise
    roughly doubles every 6–8 °C. If the risk signal rises over an afternoon and
    so did the room temperature, you cannot tell them apart afterwards unless
    you logged it.
15. **USB flash drive, 128 GB** — recordings fill the SD card quickly.

**Approximate total: $150**, or about $110 if a spare screen is available.

---

## 3. Safety

### 3.1 Human participants — none

**No person is a subject of this research at any stage, including the
researcher.** Nobody is recruited, surveyed, interviewed, photographed, recorded
or measured. The camera is inside a closed box pointing at a screen; no person
is ever in its field of view or a source of data.

The archived neural recordings used in the computational half were collected
years earlier by other researchers under their own institutional approvals, are
de-identified, and are released under a public-domain dedication. Where project
documents say "participant", they mean the label on a published de-identified
recording, following the depositors' convention. It never means a person
recruited here.

### 3.2 Vertebrate animals — none

No animal work of any kind.

### 3.3 Biological agents — none

No biological material of any kind.

### 3.4 Electrical

| Item | Assessment |
|---|---|
| Power | 5 V DC from a regulated USB supply. **No mains wiring, no exposed conductors, no batteries beyond a sealed USB power bank.** |
| Stepper motor | 5 V, low-torque. Operated only with the enclosure closed. Keep hands clear while powered. Connect it to the Pi's **5 V pin, never the 3.3 V pin** — the 3.3 V rail cannot supply it and may be damaged. |
| Display | Standard consumer screen, inside a closed box. Not viewed at close range at high brightness. |

### 3.5 The thermal intervention — the only step needing care

One degradation test warms the circuit board to see whether temperature alone
moves the monitor.

- **Household hair dryer on its lowest heat setting only.** Not a heat gun, not
  a hotplate, not an oven, no open flame.
- **At least 30 cm away**, in bursts of **no more than 60 seconds**.
- **Component temperature must stay below 50 °C** — check with the DHT22 before
  each burst.
- Do this with an adult present.

*Why so cautious about something small:* a Raspberry Pi throttles above about
80 °C and can be damaged above 85 °C. The aim is a few degrees of drift, not
heat.

### 3.6 Tools

Scissors and a craft knife for cardboard, used on a cutting mat. **Soldering is
not required by this design.** If it ever becomes necessary, do it under adult
supervision with eye protection and ventilation.

### 3.7 Waste

No hazardous waste. Electronic parts are kept; cardboard is recycled.

### 3.8 Forms

Form 3 is not expected to be required for low-voltage bench electronics not
connected to any person, and Form 4 is not expected to be required because there
are no human participants. **Confirm both with your Scientific Review Committee
rather than assuming**, and re-run the Rules Wizard once the build is final.

---

## 4. Before you buy anything

Run the pre-build checks in `04_BUILD.md` Part 1. Two of them have already
caught design faults that would have wasted the money:

- the apparatus as first specified decoded **perfectly**, which would have made
  every measurement meaningless;
- the calibrated stimulus asked the screen for **a fraction of a brightness
  level**, which a screen physically cannot display without a technique the
  first design did not include.

Both were found in simulation, in seconds, before any part was ordered.
