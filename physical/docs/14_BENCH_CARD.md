# Bench card — print this and keep it with the box

One page. Everything you need at the bench, and nothing you don't.
Full detail is in `12_RUNBOOK.md`; when something breaks, `10_TROUBLESHOOTING.md`.

---

## Every recording day, before anything else

```bash
cd ~/bci-ews-research
python3 physical/code/health_check.py
```

**PASS → carry on. FAIL → fix it before recording.** Every check in it catches a
failure that otherwise produces recordings that look fine and analyse into
nonsense.

Then, by eye:

- [ ] Box closed and taped
- [ ] Screen on, at the brightness in the log, all automatic adjustment still off
- [ ] Camera has not moved
- [ ] Temperature noted

---

## The commands

| I want to… | Type this |
|---|---|
| Check the software works | `python3 physical/code/monitor.py --selftest` |
| Check this machine can draw at 50 fps | `python3 physical/code/stimulus.py --benchmark 300` |
| Check the campaign is sound | `python3 physical/code/health_check.py` |
| Check the box (needs a recording) | `python3 physical/code/bench.py check --session 0 --block 1` |
| Check darkness (Pi, screen off) | `python3 physical/code/bench.py darkframe` |
| Record one calibration session | `python3 physical/code/run_session.py --session 0 --block 1 --calibration` |
| Draw a batch of sessions | `python3 physical/code/run_campaign.py plan --session 10 --healthy 101` |
| Record everything not yet recorded | `python3 physical/code/run_campaign.py record --session 10` |
| See what is left | `python3 physical/code/run_campaign.py status --session 10` |
| Record one drawn session | `python3 physical/code/run_session.py --session 20 --block 7` |
| Record a fault you cause by hand | `python3 physical/code/run_session.py --session 30 --block 1 --undesigned "what you did"` |
| Write down when you caused it | `python3 physical/code/note_onset.py --session 30 --block 1 --at-clock HH:MM:SS` |
| Turn recordings into results | `python3 physical/code/make_session_table.py` |
| Draw every figure | `python3 physical/code/figures.py all` |

**Stimulus window won't open over SSH:** `export DISPLAY=:0` first.

---

## The five rules

1. **Draw before you record.** Every session's plan is decided and checksummed
   before the recording exists. The script refuses otherwise.
2. **Change nothing mid-campaign.** No cleaning, no refocusing, no re-seating.
   If something changes anyway, **write it in the log with the date.**
3. **Never edit a recording.** Wrong session → record another under a new block
   number and note why.
4. **Log the mistakes too.** A log that records only successes is not a record
   of the research.
5. **Stop at the count that was frozen.** 101 fault-free, 101 degraded, 10
   undesigned. Recording *more* after seeing a result is the same mistake as
   stopping early because of one. If you decide to extend, write the amendment
   in `09_PREREGISTRATION.md` §9 **first**, before running any analysis — that
   is allowed and disclosed; the other order is not.

---

## Imposing a fault by hand

The stimulus counts down **60 · 30 · 10 · 5 · 0** seconds.

| Fault | What you do |
|---|---|
| `RATE_LOSS` | Slide the ND filter in front of the lens |
| `CHANNEL_DROPOUT` | Tape over the drawn fraction of the field |

Have it in your hand **before** you start. Under a second, and do not knock the
camera.

**Mistimed it?** Say so — a late fault is not a ruined session, a *silently*
late one is:

```bash
python3 physical/code/run_session.py --session 20 --block 7 --note "filter applied ~4 s late"
```

---

## Excluding a bad session

Never delete a recording. Add a line to `physical/data/EXCLUSIONS.csv`:

```
folder,reason,excluded_at
s10_b34,screen slept; dark frames from 40 s onward,2026-10-04
```

**A row with no reason is refused.** An unexplained exclusion cannot be told
apart from dropping a session because of how it turned out.

---

## Session log template

Copy this into your research log for anything non-routine.

```
### <date>  session <n>, blocks <a>-<b>

Temperature:
What was drawn:
Anything unusual:
Mistakes:
What I changed, if anything:
```

The last two lines are the ones that matter. Three weeks from now they are the
only thing that will explain an odd result.

---

## If it breaks and it is not in the troubleshooting guide

1. **Write down what you saw before you change anything.** Fixing it destroys
   the evidence.
2. Change one thing.
3. Re-run the relevant check, not the whole campaign.
4. Write down what fixed it — including what did not.
