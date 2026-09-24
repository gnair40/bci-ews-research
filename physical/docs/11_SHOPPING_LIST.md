# What to buy, in the order to buy it

`03_MATERIALS_AND_SAFETY.md` says *why* each item is there. This says **what to
type into a search box**, what it roughly costs, and what you can substitute.

Prices are approximate and from autumn 2026 — treat them as a budget, not a
quote. Nothing on this list is hazardous or age-restricted.

---

## Buy these first — nothing can start without them

These four are the critical path. Everything else can arrive later.

| # | Search for | ~Cost | Notes |
|---|---|---|---|
| 1 | **Raspberry Pi 4 Model B 4GB** | $55–65 | **Not a Pi 5** — different camera connector and a different software stack. Not a Pi Zero — too slow for 50 frames a second. |
| 2 | **Raspberry Pi Camera Module 3** | $25–35 | Comes with the right ribbon cable. **Keep that cable** — see below. |
| 3 | **microSD card 32GB A2** (or U3) | $8–12 | The speed class matters: slower cards drop frames during recording, which is the failure that looks like data. 64 GB for a few dollars more is worth it — the full campaign is 11.4 GB of recordings. |
| 4 | **Official Raspberry Pi 27W USB-C power supply** | $8–12 | A phone charger sags under load and the Pi throttles silently, changing the frame rate mid-session. |

**Subtotal: about $100–120.** Order these today; the rest can follow.

> **The single most common mistake at this stage** is buying a camera cable
> separately. The Pi 4 uses the older, wider connector. A cable sold for the Pi
> 5 is narrower and will not fit. Use the one in the camera box.

---

## The enclosure — mostly things you may already have

| # | Search for | ~Cost | Notes |
|---|---|---|---|
| 5 | **Cardboard box, 40×30×30 cm or larger** | $0–8 | A shipping box is ideal. Bigger is easier to work in. |
| 6 | **Matte black poster paper** or **matte black spray paint** | $6–12 | **Matte, not gloss.** Gloss reflects, and a reflection puts a faint copy of the screen onto other channels — two channels that should be independent stop being independent. |
| 7 | **Gaffer tape, black** (electrical tape works) | $6–10 | Gaffer is easier to re-do. You will re-do it. |
| 8 | **Small tabletop tripod** or any rigid bracket | $8–15 | It must not move. A camera that shifts a millimetre between sessions changes which part of the screen each channel sees, and every session after the shift is a different apparatus. |

---

## The display

| # | Search for | ~Cost | Notes |
|---|---|---|---|
| 9 | Any monitor, tablet, or old laptop screen, **1280×720 or better, with manual brightness** | $0–40 | **Use something you already own if you possibly can.** This is the item most likely to already be in a cupboard. |

**What disqualifies a screen:** automatic brightness you cannot turn off,
ambient-light sensing you cannot turn off, or a power-saving dimmer you cannot
disable. Any of those is larger than the signal being measured and will change
during a recording without telling you.

**What to check before committing to a screen:** run the dither check
(`bench.py dither`) on a one-minute recording. Some panels are really 6-bit and
do their own dithering, which fights yours. Better to find out with a screen you
can return.

---

## Degradation tools — needed for P-3 and P-5, not for the build

| # | Search for | ~Cost | Notes |
|---|---|---|---|
| 10 | **Neutral density filter gel sheet, ND 0.6** (photographic) | $8–15 | A sheet cuts into many. Inert plastic. A sheet of "lighting gel sample pack" often works and is cheaper. |
| 11 | **28BYJ-48 stepper motor with ULN2003 driver board** | $6–10 | Usually sold as a pair. Optional — the rotation fault is also available in software. The motor exists so P-5 can impose a *physical* rotation. |
| 12 | **Female-to-female jumper wires, 20 cm** | $5–8 | Six needed. A 40-wire pack costs the same as six. No soldering. |

---

## Environment and storage

| # | Search for | ~Cost | Notes |
|---|---|---|---|
| 13 | **DHT22** or **AM2302 temperature humidity sensor module** | $5–10 | Buy the **module on a breakout board** with the pull-up resistor already fitted, not the bare sensor. |
| 14 | **USB flash drive, 128GB** | $10–15 | Measured: a session is **23.7 MB**, so the 30-hour campaign is **11.4 GB**. That fits on a 32 GB card beside the OS, but not comfortably — and the SD card fills first. |

---

## Totals

| | |
|---|---|
| Critical path (items 1–4) | **~$110** |
| Enclosure (5–8) | ~$20–45 |
| Display (9) | $0–40 |
| Degradation tools (10–12) | ~$20–33 |
| Environment and storage (13–14) | ~$15–25 |
| **Everything** | **~$165–250**, or **~$150** with a screen and box you already have |

---

## What you can do without

| Skip | Consequence |
|---|---|
| Stepper motor (11) and jumpers (12) | The geometric fault is still available in software. You lose one of P-5's five physical interventions. Say so in the write-up. |
| Temperature sensor (13) | You lose the ability to separate room warmth from apparatus drift afterwards. Note in the log that you had no sensor. |
| USB drive (14) | Fine until the SD card fills. `health_check.py` warns you before it does. |
| ND filter (10) | You lose the optical-attenuation fault in both P-3 and P-5. Harder to do without than it sounds — this is the easiest physical fault to impose cleanly. |

**Do not skip:** items 1–9. Below that you do not have an apparatus.

---

## Before you spend anything

Ten minutes, on a laptop, no hardware:

```bash
python3 physical/code/monitor.py --selftest
python3 physical/code/dryrun.py --clean --healthy 12 --degraded 8
python3 physical/code/make_session_table.py --raw physical/data/dryrun/raw --tag _dryrun
python3 physical/code/figures.py all --tag _dryrun
python3 physical/code/dryrun.py --cleanup
```

If that runs and draws six figures, the software side works and the money is
safe to spend. Two design faults have already been caught at this step — an
apparatus that would have decoded perfectly, and a stimulus asking the screen
for a fraction of a brightness level it physically cannot show. Both were found
in seconds, before any part was ordered.

---

## When the parts arrive

Go to `04_BUILD.md` Part 2 and work forward. Do not skip the bench checks in
Part 5; each of them catches a failure that otherwise produces plausible numbers
rather than an obvious error, which is the expensive kind.
