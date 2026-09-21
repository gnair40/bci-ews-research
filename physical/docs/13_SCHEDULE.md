# The plan, against the calendar

`12_RUNBOOK.md` says what order to do things in. **This says when, how long each
takes, what happens if one slips, and what to cut if you run out of time.**

> **Two dates are assumptions.** This is built against **1 December 2026** for
> the final plan and **1 March 2027** for the regional fair. Replace them with
> your real dates — the arithmetic below shifts with them, and the slack figure
> is the number to watch.

**Written 21 September 2026.** 71 days to December, 161 to the fair.

---

## The decision that sets the schedule

Everything else is fixed. This one is yours, and it changes the calendar by
about three days.

| | 101 fault-free sessions | ~360 fault-free sessions |
|---|---|---|
| Recording | 1 unattended night | 4 unattended nights |
| Held-out fault-free hours | ~4 | ~30 |
| What you can claim with zero false alarms | "probably below 0.75/hour" — **7× the budget** | "**within the 0.1/hour budget**" |
| Calendar cost | — | **+3 days** |

**Three days buys the difference between "we could not measure it precisely
enough" and the measurement the whole phase exists for.** The schedule below
assumes the longer campaign.

---

## Week by week

| Week | Dates | What happens | Who is needed |
|---|---|---|---|
| 1 | 21 Sep – 2 Oct | Order parts, wait for shipping. **Read 00 and 01 while waiting.** | nobody |
| 2 | 2 – 5 Oct | Set up the Pi, build the box | you, two afternoons |
| 2–3 | 5 – 8 Oct | Bench checks, then calibrate to 36.1° (P-1) | you, iterative |
| 3 | 8 – 9 Oct | **Freeze the preregistration** | you, 30 min |
| 3–4 | 9 – 15 Oct | P-2: the fault-free campaign, 4 nights | **nobody — it runs while you sleep** |
| 4–5 | 15 – 20 Oct | P-3: 101 degraded sessions | partly attended |
| 5 | 20 – 21 Oct | P-5: the five undesigned faults | you, one hour |
| 5 | 21 – 22 Oct | Analysis and figures | laptop, 20 min |
| 6 | 22 – 27 Oct | Write the December section with real numbers | you |

**Finishes 27 October. That leaves 35 days of slack before 1 December.**

That slack is the whole point of starting now. It absorbs roughly one major
setback — see the risk table — and still lands the December plan with data in
it rather than a promise of data.

---

## Three checkpoints — and what to do if you miss one

Check these dates against reality, not against how it feels.

### Checkpoint 1 — **preregistration frozen by 12 October**

*Why this one:* nothing that counts as data may be recorded before it. Every
day late is a day lost from the end.

**If you miss it:** you are not in trouble yet. Freeze it the day you can and
carry on; the slack absorbs about two weeks here.

### Checkpoint 2 — **all recording done by 1 November**

*Why this one:* analysis is fast, but writing with real numbers is not.

**If you miss it:** cut in the order below, starting with P-5. Do **not**
shorten P-2 to catch up — it is the measurement nobody else can make, and it is
the one that runs while you sleep, so it costs you calendar but not effort.

### Checkpoint 3 — **December section drafted by 20 November**

*Why this one:* it needs to be read by someone else before it is submitted.

**If you miss it:** submit the December plan with the data you have and say
explicitly what is still being collected. A plan that reports 60 fault-free
hours and says so is stronger than one that implies a completed campaign.

---

## What could go wrong, what it costs, what to do

Ordered by how likely it is to actually happen.

| Risk | Cost | What to do |
|---|---|---|
| **Wrong camera cable** — bought separately, Pi 5 type, does not fit | +1 week | Use the cable that came with the camera. This is the most common build failure. |
| **The Pi cannot hold 50 fps** (B-0 fails) | +2 days, or a design change | `stimulus.py --benchmark 300` on the Pi **before you build**. It prints three options and what each costs. |
| **Calibration will not converge** to 36.1° ± 6° | +3 to 7 days | Change **one** setting at a time. `10_TROUBLESHOOTING.md` Part B has the order to try them in. |
| **The screen destroys the dither** (B-6 fails) | +3 days to 2 weeks | Try the settings first, then the exposure, then a different screen. Test with a screen you can return. |
| **Screen sleeps mid-campaign** | +1 night each time | Disable blanking in `raspi-config` **and** on the display. `health_check.py` catches it next morning. |
| **Disk fills overnight** | +1 night | `health_check.py` tells you how many sessions will fit **before** you start. |
| **Box not light-tight** | +1 day | Re-tape in order: cable hole, lid seam, bezel. |
| **Parts delayed** | +1 to 2 weeks | The reason to order this week rather than next. |

**Worst realistic stack-up: about four weeks.** That still finishes in late
November — inside the December deadline, with no room to spare. Which is the
argument for ordering parts now rather than after the next thing on your list.

---

## If you fall behind, cut in this order

From `02_EXPERIMENTS.md`, decided before any of this started:

1. **P-5** (undesigned faults) — 1 hour. Losing it costs you the check on
   whether real faults resemble designed ones. Say so in the limitations.
2. **P-6** (decision rate) — 0 hours of recording; it is pure analysis. Only
   cut it if you run out of *writing* time.
3. **P-3 severities** — record 1.0 and 0.25 only, dropping 0.5. Halves the
   degraded campaign. You lose resolution on the severity ladder, which is
   preregistered prediction PP-6.

**Never cut P-2.** It is the measurement that does not exist anywhere else, it
runs while you sleep, and every other result is reported against the threshold
it produces.

---

## What "good to go" means, today

Before you spend money, all four of these:

- [ ] `python3 physical/code/monitor.py --selftest` → PASS
- [ ] `python3 physical/code/stimulus.py --benchmark 300` → PASS on your laptop
- [ ] The dry run in `12_RUNBOOK.md` step 0.4 produces six figures you have
      looked at
- [ ] You have read `00_WHY_THIS_PHASE_EXISTS.md` and can say in your own words
      why lead time and false-alarm rate are not measurable on archived
      recordings

Then:

- [ ] **Order the four critical parts** (~$110, `11_SHOPPING_LIST.md`)
- [ ] **Decide 101 or ~360** fault-free sessions
- [ ] Put the three checkpoint dates in your calendar

That is the whole of it. Everything after is `12_RUNBOOK.md`, in order.

---

## After the fair

Not needed for December, listed so it is not forgotten:

- The apparatus and the benchmark are reusable by anyone — the onset-drawing,
  the gates and the analysis are not specific to this box.
- `08_WHAT_COMES_AFTER.md` decides what gets built once results exist. Four of
  its six outcomes say *no device*, and that was decided before any data
  existed, on purpose.
