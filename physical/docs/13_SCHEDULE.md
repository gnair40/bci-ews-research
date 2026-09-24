# The plan, against the calendar

`12_RUNBOOK.md` says what order to do things in. **This says when, how long each
takes, what happens if one slips, and what to cut if you run out of time.**

> **Two dates are assumptions.** This is built against **1 December 2026** for
> the final plan and **1 March 2027** for the regional fair. Replace them with
> your real dates — the arithmetic below shifts with them, and the slack figure
> is the number to watch.

**Written 21 September 2026. Revised 24 September 2026** after the
preregistration was frozen. **68 days to December, 158 to the fair.**

---

## The decision that set the schedule — made 24 September 2026

This was the one open decision. It is now closed and frozen
(`09_PREREGISTRATION.md` §11, call 1, commit `f4dda04`).

| | **101 fault-free sessions — CHOSEN** | ~480 fault-free sessions |
|---|---|---|
| Recording | **1 unattended night** | 4 unattended nights |
| Held-out fault-free hours | **~4** | ~30 |
| What zero false alarms lets you claim | **"bounded at 0.75/hour" — 7× the budget, and PP-1 is reported as untested** | "within the 0.1/hour budget" |
| Calendar cost | **—** | +3 days |

**What choosing 101 costs, in one sentence:** if the monitor turns out to be
quiet, this campaign cannot tell that apart from a monitor that is merely
untested, and the write-up has to say so. If the monitor turns out to be
*noisy* — which is what PP-1 predicts, from 3.41/hour on T11 and 0.225/hour on
T5 — 101 sessions measure it fine. The decision bets on the prediction being
right, and the cost of losing that bet is written into PP-1 in advance.

### The three days it saved are already spent

The schedule was written on 21 September assuming four nights and finishing 31
October. Choosing one night pulls the finish in by three days; freezing three
days later than the schedule assumed pushes it back by three. **Net change:
none. Still 31 October, still 31 days of slack.**

This is worth stating rather than quietly showing a better number. The three
days were real and they were spent on deciding — which is a legitimate use of
them, but not a free one.

### One thing happened out of order, and it is an improvement

The runbook puts the freeze at stage 6, *after* calibration. It happened first
instead. That is the stronger ordering: gate G-e (margin within 6° of 36.1°)
was fixed before anyone knows what margin this box will actually produce, so
the gate cannot drift toward whatever the apparatus happens to do. If the box
cannot meet it, `09_PREREGISTRATION.md` §7 already says what to report, and it
was written before the box existed.

---

## Week by week

| Week | Dates | What happens | Who is needed |
|---|---|---|---|
| — | **24 Sep — done** | **Preregistration frozen** (`f4dda04`), 18 days ahead of checkpoint 1 | — |
| 1 | 24 Sep – 5 Oct | **Order the four critical parts**, wait for shipping. **Read 00 and 01 while waiting.** | nobody |
| 2 | 5 – 8 Oct | Set up the Pi, build the box | you, two afternoons |
| 2–3 | 8 – 12 Oct | Bench checks, then calibrate to 36.1° (P-1) | you, iterative |
| 3 | 12 – 13 Oct | P-2: the fault-free campaign, **one night** | **nobody — it runs while you sleep** |
| 3–4 | 13 – 19 Oct | P-3: 101 degraded sessions | partly attended |
| 4 | 19 – 20 Oct | P-5: the five undesigned faults | you, one hour |
| 4–5 | 20 – 25 Oct | **P-7: three more apparatus configurations** | mostly unattended |
| 5 | 25 – 26 Oct | Analysis and figures | laptop, 20 min |
| 5–6 | 26 – 31 Oct | Write the December section with real numbers | you |

**Finishes 31 October with P-7 included. That leaves 31 days of slack before
1 December.**

**The critical path now runs through the post, not through you.** Every dated
row above is downstream of parts arriving; nothing in the list can start
earlier by working harder. That is the argument for ordering this week.

*(P-7 was added on 21 September and costs about 10 hours of mostly unattended
recording plus three re-calibrations — four days of calendar, and four days of
slack. It is what turns "one apparatus in one room" from an unanswered
objection into a narrowed one.)*

That slack is the whole point of starting now. It absorbs roughly one major
setback — see the risk table — and still lands the December plan with data in
it rather than a promise of data.

---

## Three checkpoints — and what to do if you miss one

Check these dates against reality, not against how it feels.

### Checkpoint 1 — **preregistration frozen by 12 October** — ✅ **met 24 September, 18 days early**

*Why this one:* nothing that counts as data may be recorded before it. Every
day late is a day lost from the end.

Frozen at commit `f4dda04`. Nothing further is needed here, and **the 18 days
are not slack you can spend** — they were always going to be spent waiting for
parts, which is now the only thing on the critical path.

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
2. **P-7** (apparatus variation) — 10 hours, unattended. Cutting it leaves the
   single-apparatus objection unanswered; say so in the limitations.

**P-6 is no longer on the cut list.** It costs no recording at all — it is a
re-scoring of sessions you already have — and since 21 September it is
co-primary with P-2. Cutting it saves analysis time and nothing else.
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

- [x] ~~Decide the fault-free campaign length~~ — **101, frozen 24 Sep**
- [ ] **Order the four critical parts** (~$110, `11_SHOPPING_LIST.md`) — **this
      is now the only thing standing between you and the whole schedule above**
- [ ] Put the two remaining checkpoint dates in your calendar (1 Nov, 20 Nov)

That is the whole of it. Everything after is `12_RUNBOOK.md`, in order.

---

## After the fair

Not needed for December, listed so it is not forgotten:

- The apparatus and the benchmark are reusable by anyone — the onset-drawing,
  the gates and the analysis are not specific to this box.
- `08_WHAT_COMES_AFTER.md` decides what gets built once results exist. Four of
  its six outcomes say *no device*, and that was decided before any data
  existed, on purpose.
