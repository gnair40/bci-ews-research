# Repository consolidation — 10 November 2026

**What was asked:** review every branch, commit, file and timestamp; find the
most recent and accurate version of everything; resolve outdated or conflicting
information in favour of the latest verified state; and consolidate it into one
branch that is the current, comprehensive version of the project.

**What was found, in one line:** the history needed no merging at all — but the
*content* held one conflict that would have cost a hardware rebuild, and no
gate was looking for it.

---

## 1. The branch audit

Six branches exist on the remote. Every one of them was compared against the
newest commit, `61fd150` (24 September 2026).

| Branch | Last commit | Commits **not** in `61fd150` | Files **not** in `61fd150` |
|---|---|---|---|
| `claude/isef-research-pipeline-9zt4uq` | 2026-09-24 | — (it *is* the tip) | — |
| `claude/research-reassessment` | 2026-09-24 | 0 | 0 |
| `main` | 2026-09-21 | 0 | 0 |
| `physical-validation-phase` | 2026-09-21 | 0 | 0 |
| `research-reassessment` | 2026-09-21 | 0 | 0 |
| `research-pipeline-9zt4uq` | 2026-09-19 | 0 | 0 |

Reproduce it:

```bash
git fetch --all --prune
TIP=origin/claude/isef-research-pipeline-9zt4uq
for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin | grep -v HEAD); do
  echo "$b: $(git rev-list --count $TIP..$b) commits not in tip"
done
```

**Every branch is an ancestor of `61fd150`.** The duplicate-looking names are
the same work under two spellings: the remote renamed three branches when they
were first pushed, leaving `physical-validation-phase` beside
`claude/physical-validation-phase` and so on. Nothing diverged, nothing was
abandoned on a side branch, and no file was deleted along the way — the
file-level check above was run precisely because an ancestor can still contain
a file the descendant dropped, and none did.

**So there was nothing to merge.** Consolidation here means naming the verified
tip clearly and correcting what is *inside* it, not reconciling histories. Any
account of this work that described resolving branch conflicts would be
theatre.

`main` is 10 commits behind and still carries merges of pull requests #1 and
#3–#6, so the repository's established pattern is branch → pull request →
merge. Opening that pull request remains the researcher's to authorise.

---

## 2. The conflict that mattered

Two different stepper-motor pinouts were in the tree at the same time:

| Source | IN1 | IN2 | IN3 | IN4 | Dated |
|---|---|---|---|---|---|
| `rig/motor.py` (`PINS = [17, 27, 22, 23]`) | GPIO 17 | GPIO 27 | GPIO 22 | GPIO 23 | 19 Sep 2026 |
| `research/RIG_CODE.md` | GPIO 17 | GPIO 27 | GPIO 22 | GPIO 23 | — |
| `research/RIG_PROCEDURE.md` | GPIO 17 | GPIO 27 | GPIO 22 | GPIO 23 | — |
| **`physical/docs/04_BUILD.md`** | **GPIO 6** | **GPIO 13** | **GPIO 19** | **GPIO 26** | **20 Sep 2026** |

**Resolved in favour of the code, 17/27/22/23.** `rig/motor.py` is the only
program in this repository that drives the motor; it hardcodes those four pins,
and two other documents already agreed with it. `04_BUILD.md` was the lone
outlier, written fresh on 20 September without checking the code it describes.

This is not a cosmetic disagreement. Wire the board by the old table and the
motor never turns, while the software reports nothing wrong — it would dutifully
energise four pins with nothing attached. The failure appears as "the camera
did not rotate", hours into a P-5 session, with no error message anywhere.

The old table carried a second hazard worth naming: its single column was
headed "Raspberry Pi pin" while holding GPIO numbers, and GPIO 13 and physical
pin 13 are **different holes in the header**. The corrected table states both
numbers on every row, so nothing has to be inferred.

---

## 3. The gap that mattered

`run_session.py` records room temperature into every session row by calling
`rig/logtemp.py`, and `rig/logtemp.py` defaults to `--pin 4`. **No build
document said how to wire the sensor.** A reader following `04_BUILD.md` would
have owned a DHT22 and no instruction for attaching it.

`04_BUILD.md` now documents it: DATA on GPIO 4 (physical pin 7), which is the
value the code actually defaults to. **The power and ground pins in that table
are labelled as a recommendation rather than a repository specification**,
because no file here states them, and inventing a number while claiming it came
from the repository is the error this consolidation exists to remove.

---

## 4. Why no gate caught either one

All twelve gates passed with the contradiction sitting in the tree. They are
thorough about different things: numbers against the data they came from,
documents against other documents, the preregistration against its freeze, the
working copy against its remote. **Not one of them looks at a GPIO number.**

`scripts/81_hardware_pins.py` now does. It checks each wiring table against the
pins its program actually drives, and checks that every GPIO in those tables
sits on the physical pin the table claims, against the real 40-pin header.

It was verified by putting the original wrong pinout back and confirming the
gate goes red — a gate never seen to fail is not known to work. Its own first
version had a defect found the same way: section 3 shared the global problem
list, so whenever section 1 failed, section 3 printed a heading and no result,
leaving no way to tell "checked and fine" from "never ran".

**The pattern, recorded again rather than treated as solved.** This project has
now logged this failure shape repeatedly: *a value correct where it was written
and wrong where it was used, with nothing connecting the two.* Every earlier
instance cost a rerun. This is the first where acting on the wrong value costs a
rebuild, which is a good argument for the gate existing before the parts arrive
rather than after.

---

## 5. Environment note

A fresh container had no Python dependencies, and six gates failed on
`ModuleNotFoundError: No module named 'numpy'`. The cause was not the code:
`pip` on this image resolves to Python 3.13 while `python3` is 3.11, so
`pip install -r requirements.txt` installed into an interpreter the scripts
never use. `python3 -m pip install -r requirements.txt` is the form that works,
plus `python3 -m pip install --upgrade Pillow`, because the system Pillow is
built for 3.13 and matplotlib cannot import it.

All 12 gates passed immediately afterwards. **Nothing was wrong with the
repository** — worth stating, because six simultaneous failures look alarming
and traced to one missing package.

---

## 6. What this branch is

`claude/consolidated-2026-11-10`, branched from the verified tip `61fd150`,
carrying the corrections above. It is the current, comprehensive version of the
project.

Nothing was deleted, no history was rewritten, and no commit was squashed. The
research log keeps every earlier entry, including the wrong ones, which is a
standing rule of this project and not an oversight.
