# Every piece of code the physical experiment needs

> ## SUPERSEDED 20 September 2026
>
> **This is no longer the code index** for the physical phase. Read **`physical/docs/05_SOFTWARE.md`** instead.
>
> This file is kept because it holds the full source of the `rig/` programs inline, which is a useful fallback if a file is ever lost. The programs it documents still run; they are simply not the ones the current design uses.
>
> **Do not mix the two.** The programs in `rig/` and the programs in
> `physical/code/` each keep their own `preferred_directions.npy` — the file
> that decides which patch on the screen is which channel. Recordings made with
> one set cannot be compared with recordings made with the other, and nothing in
> the data would reveal that they had been mixed. Pick one and stay in it; for
> anything recorded from 20 September 2026 onward, that is `physical/code/`.

---

**Short answer to "will I have to write code?": no.** Everything is written and
in the repository. This file is the index, the reason each program exists, and
the fallback for when it does not behave.

It also contains each program's source inline. That is deliberate redundancy: if
a file is ever lost, corrupted on the SD card, or edited into a state that no
longer runs, it can be retyped from here.

---

## The programs, in the order they get used

| Program | Runs on | What it does | Manual step |
|---|---|---|---|
| `rig/stimulus.py` | Screen machine | Shows the patch grid; logs the true heading every frame | B-3 |
| `rig/capture.py` | The Pi | Records frames, reduces each to one average per channel | B-4 |
| `rig/to_mat.py` | Either | Converts a recording into the `.mat` files the analysis already reads | — |
| **`rig/run_block.py`** | The Pi | **Records ONE block end to end and logs the settings** | B-7 onward |
| **`rig/bench.py`** | Either | **The bench checks: darkframe, lag, dither, margin** | B-2, B-5, B-6, B-7 |
| **`rig/run_batch.py`** | The Pi | **Records many blocks unattended from a plan file** | B-14 |
| **`rig/daily_session.py`** | The Pi | **The natural-drift arm: a few blocks a day for weeks, from cron** | P-R7 |
| **`rig/motor.py`** | The Pi | **Turns the stage, for the rotation fault** | B-10, B-12 |
| **`rig/logtemp.py`** | The Pi | **Temperature and humidity, so drift and warmth stay separable** | every block |
| `scripts/72_rig_digital_twin.py` | Any | Simulates the rig, so the design is checked before it is built | Gate 2 |
| `scripts/73_monitorability_certificate.py` | Any | The instrument's output: the verdict | Part 6 |

The five in bold did not exist when the build manual was first written. The
manual said things like "run the stimulus in one window and the capture in
another" and "cross-correlate on your own computer", which is a description of
work, not a program. Writing them out found four documented commands that were
simply wrong — `rig/capture.py` was documented with positional arguments it
never accepted, and `rig/to_mat.py` was documented twice with flags it does not
have. A reader following the manual literally would have been stopped by all
four.

---

## The one command you will type most

```
python3 rig/run_block.py --session 1 --blocknum 1
```

That starts the stimulus, waits three seconds for the first frame to reach the
screen, starts the camera, waits for both, converts the result, reads the
temperature, and appends every setting to `rig/blocklog.csv`.

Add `--dry-run` to see exactly what it would run without any hardware:

```
python3 rig/run_block.py --session 1 --blocknum 1 --dry-run
```

**Why `rig/blocklog.csv` matters more than it looks.** It records the fault, the
severity, the drift setting, the modulation depth, the temperature and the
timestamp for every block ever recorded. Three weeks later, when a result looks
strange, that file is the only way to find out what the conditions were.
Reconstructing it from memory is not possible.

---

## Typical sessions, as literal commands

**A healthy baseline session, 20 blocks:**
```
for i in $(seq 1 20); do
  python3 rig/run_block.py --session 1 --blocknum $i --lag 0.0
done
```

**A severity ladder for one fault** — the filter has to be moved by hand between
blocks, which is why this is not a loop:
```
python3 rig/run_block.py --session 2 --blocknum 1 --fault RATE_LOSS --severity 0.0
python3 rig/run_block.py --session 2 --blocknum 2 --fault RATE_LOSS --severity 0.25
python3 rig/run_block.py --session 2 --blocknum 3 --fault RATE_LOSS --severity 0.5
python3 rig/run_block.py --session 2 --blocknum 4 --fault RATE_LOSS --severity 1.0
```

**The drift sweep, 265 blocks, unattended:**
```
python3 rig/run_batch.py --make-sweep-plan rig/plans/sweep.txt
python3 rig/run_batch.py --plan rig/plans/sweep.txt
```
If it is interrupted, run the same plan again — blocks already recorded are
skipped, so it picks up where it stopped.

**Starting the natural-drift arm** — six to ten weeks, unattended, nothing touched:
```
crontab -e
```
Add this line, which records four blocks at 03:00 every day:
```
0 3 * * * /usr/bin/python3 /home/pi/bci-ews-research/rig/daily_session.py >> /home/pi/rig_cron.log 2>&1
```
The session number comes from the calendar, not a counter, so a missed night
costs one session and leaves a visible gap instead of silently renumbering
everything after it. **Change nothing while this arm runs** — no cleaning, no
refocusing, no re-seating. If something is changed anyway, write it in the
research log with the date; an undocumented mid-arm intervention cannot be
detected afterwards and makes the whole arm uninterpretable.

**Rotating the stage by two degrees and back:**
```
python3 rig/motor.py --degrees 2
python3 rig/motor.py --degrees -2
```

---

## What to do when something is unexpected

Every row has an action. None ends in "stop".

| Symptom | First thing to check | Fallback if that does not fix it |
|---|---|---|
| `bench.py darkframe` fails | Re-tape the cable hole, then the lid, then the screen bezel | Record a dark frame each session and subtract it — and **write it down as a deviation**, because a subtracted offset is not the same as no offset when measuring drift |
| `bench.py dither` fails | Turn off every screen enhancement: dynamic contrast, ambient adjustment, power-saving dimmer | Raise `--exposure` to 16000; then try a different screen; **only then** raise `--depth` fourfold and re-run the digital twin at the new value, stating the mismatch everywhere |
| `bench.py lag` gives an unstable answer | Repeat on two more blocks — the number must agree | Drop both programs to 25 fps; if still unstable, hold each heading 5 s (`--hold 250`) and analyse only the middle 3 s |
| `bench.py margin` too large (rig too easy) | Lower `--depth`; halving it roughly doubles the error | Reduce pixels per channel by lowering the capture size |
| `bench.py margin` too small (rig too hard) | Raise `--depth` | Raise `--exposure`, or raise the capture size toward 96×64 |
| A fault shows no severity ladder | Check the fault is physically present at every level | **Report that mode as unusable.** Do not redefine severity until a ladder appears — that is the "try definitions until one works" pattern this project refuses elsewhere |
| `stimulus.py` says no display | You are on SSH with no screen on the Pi | `export DISPLAY=:0`, or attach a keyboard and screen to the Pi |
| Capture runs slower than the stimulus | Lower `--fps` on **both** to 30 | Only the agreement between the two matters, and that it stays fixed for the whole study |
| The motor stalls or buzzes | Raise `--delay` to 0.003 | Check it is on the 5 V pin, not 3.3 V |
| A block fails mid-batch | `run_batch.py` continues and reports it at the end | Re-run the same plan; only missing blocks are retried |
| The SD card corrupts | Keep a second card imaged | Re-aiming the camera changes the channel mapping, so re-run B-7 and restart that arm |
| `logtemp.py` prints only a comma | No sensor wired; this is never fatal | Skip it, but **write in the log that temperature is missing**, so empty cells are not later read as zero |

---

## Two things about this code that are easy to get wrong

**1. The fault must be physical, not typed.** `--fault RATE_LOSS --severity 0.5`
is a *label* that goes in the block log. It does not dim anything. You dim the
lens with the ND filter. If the label and the filter ever disagree, the dataset
is wrong in a way no analysis can detect, because the label is the ground truth.

**2. Never change `--depth` after B-7.** Every block must share it or the blocks
are not comparable to one another. If it has to change, that is a new session
with a new baseline, recorded and stated as such.

---

# Full source

Everything below is regenerated from the files themselves by
`tools/refresh_rig_code.py`. **Do not edit it here** — edit the file and
re-run that tool. Everything ABOVE this line is hand-written and is never
touched by it.

## `rig/run_block.py`

```python
#!/usr/bin/env python3
"""
run_block.py — record ONE block, end to end, with one command.

WHY THIS EXISTS
---------------
The build manual said "run the stimulus in one window and the capture in
another". That works once, by hand. It does not work 265 times, which is what
the drift sweep needs, and every hand-run block is a chance to mistype a setting
or forget which fault was in place.

This starts the stimulus, starts the capture, waits for both, converts the
result into the .mat files the analysis already reads, and writes a record of
every setting used. One command, one block, nothing to remember.

WHAT IT PRODUCES
----------------
    data/raw_rig/RIG/day_<session>/block_<n>/   the three .mat files
    rig/blocklog.csv                            one row per block ever recorded

The block log is the thing that saves you later. It records the fault, the
severity, the drift setting, the modulation depth, the temperature and the
timestamp for every block, so a result can always be traced back to the
conditions that produced it. Recovering that from memory three weeks later is
not possible.

Usage:
    python3 rig/run_block.py --session 1 --blocknum 1
    python3 rig/run_block.py --session 2 --blocknum 7 --fault RATE_LOSS --severity 0.5
    python3 rig/run_block.py --session 3 --blocknum 1 --drift-tau 60 --frames 15000
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

RIG = Path(__file__).resolve().parent
REPO = RIG.parent
LOG = RIG / "blocklog.csv"

FIELDS = ["timestamp", "session", "blocknum", "fault", "severity", "frames",
          "fps", "depth", "brightness", "drift_tau", "drift_depth", "exposure",
          "gain", "lag_s", "temp_c", "humidity", "note", "outdir"]


def read_temp() -> tuple[str, str]:
    """Temperature and humidity, if the sensor is wired. Never fatal."""
    try:
        out = subprocess.run([sys.executable, str(RIG / "logtemp.py"), "--once"],
                             capture_output=True, text=True, timeout=15)
        t, h = out.stdout.strip().split(",")
        return t, h
    except Exception:
        return "", ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--blocknum", type=int, required=True)
    ap.add_argument("--frames", type=int, default=15000)
    ap.add_argument("--fps", type=int, default=50)
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="modulation depth; leave alone unless B-7 says otherwise")
    ap.add_argument("--brightness", type=float, default=1.0)
    ap.add_argument("--drift-tau", type=float, default=0.0,
                    help="seconds; 0 means no imposed drift")
    ap.add_argument("--drift-depth", type=float, default=0.0)
    ap.add_argument("--concentration", type=float, default=0.0)
    ap.add_argument("--exposure", type=int, default=8000)
    ap.add_argument("--gain", type=float, default=2.0)
    ap.add_argument("--lag", type=float, default=0.0,
                    help="seconds, from the B-5 timing measurement")
    ap.add_argument("--fault", default="NONE",
                    help="label only; the fault itself is imposed physically")
    ap.add_argument("--severity", type=float, default=0.0)
    ap.add_argument("--note", default="")
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would run and stop; no hardware needed")
    a = ap.parse_args()

    stim_csv = RIG / f"stim_s{a.session}_b{a.blocknum}.csv"
    cap_npy = RIG / f"cap_s{a.session}_b{a.blocknum}.npy"

    stim_cmd = [sys.executable, str(RIG / "stimulus.py"),
                "--frames", str(a.frames), "--fps", str(a.fps),
                "--depth", str(a.depth), "--brightness", str(a.brightness),
                "--concentration", str(a.concentration),
                "--drift-tau", str(a.drift_tau),
                "--drift-depth", str(a.drift_depth),
                "--out", str(stim_csv)]
    cap_cmd = [sys.executable, str(RIG / "capture.py"),
               "--frames", str(a.frames), "--fps", str(a.fps),
               "--exposure", str(a.exposure), "--gain", str(a.gain),
               "--out", str(cap_npy)]
    conv_cmd = [sys.executable, str(RIG / "to_mat.py"),
                "--block", str(cap_npy), "--stimlog", str(stim_csv),
                "--session", str(a.session), "--blocknum", str(a.blocknum),
                "--lag", str(a.lag), "--root", a.root]

    if a.dry_run:
        for label, c in (("stimulus", stim_cmd), ("capture", cap_cmd),
                         ("convert", conv_cmd)):
            print(f"{label:9} {' '.join(c)}")
        return 0

    # The stimulus is started first and given a moment to put the first frame on
    # the screen. Starting the camera first would record the desktop.
    print(f"--- session {a.session} block {a.blocknum} "
          f"({a.fault} sev {a.severity}) ---")
    stim = subprocess.Popen(stim_cmd)
    time.sleep(3.0)
    cap = subprocess.Popen(cap_cmd)

    cap_rc = cap.wait()
    stim.wait()
    if cap_rc != 0:
        print("capture failed; NOT converting and NOT logging this block")
        return 1

    if subprocess.run(conv_cmd).returncode != 0:
        print("conversion failed")
        return 1

    temp, hum = read_temp()
    outdir = f"{a.root}/RIG/day_{a.session}/block_{a.blocknum}"
    row = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "session": a.session,
           "blocknum": a.blocknum, "fault": a.fault, "severity": a.severity,
           "frames": a.frames, "fps": a.fps, "depth": a.depth,
           "brightness": a.brightness, "drift_tau": a.drift_tau,
           "drift_depth": a.drift_depth, "exposure": a.exposure, "gain": a.gain,
           "lag_s": a.lag, "temp_c": temp, "humidity": hum, "note": a.note,
           "outdir": outdir}
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(f"logged to {LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/bench.py`

```python
#!/usr/bin/env python3
"""
bench.py — the bench checks from Part 5 of the build manual, as runnable code.

The manual described these in prose and, for two of them, as a one-line shell
incantation that referenced files from a different test. That is how a checklist
turns into an evening of debugging. Each check is a subcommand here, each prints
PASS or FAIL against the manual's stated condition, and each says what to do
when it fails.

    python3 rig/bench.py darkframe                 # B-2: is the box light-tight?
    python3 rig/bench.py lag --cap C.npy --stim S.csv    # B-5: camera/screen timing
    python3 rig/bench.py dither --cap C.npy --stim S.csv # B-6: sub-level signal
    python3 rig/bench.py margin --cap C.npy --stim S.csv # B-7: difficulty

`darkframe` needs the camera. The other three read files already recorded, so
they run on any computer -- which matters, because the Pi is slow and you will
want to look at these on a laptop.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

RIG = Path(__file__).resolve().parent
NEURAL_MARGIN_T11 = 36.1      # 90.692 chance - 54.554 error, T11


def _load(cap: str, stim: str):
    X = np.load(cap).astype(np.float64)
    s = np.genfromtxt(stim, delimiter=",", names=True)
    n = min(len(X), len(s))
    return X[:n], s["heading_rad"][:n], s["t_unix"][:n]


def _verdict(ok: bool, good: str, bad: str) -> int:
    print(f"\n{'PASS' if ok else 'FAIL'} — {good if ok else bad}")
    return 0 if ok else 1


# --------------------------------------------------------------------- B-2
def darkframe(a) -> int:
    """With the screen OFF and the lid shut, how much light is still there?"""
    from picamera2 import Picamera2
    import time
    c = Picamera2()
    c.configure(c.create_video_configuration(
        main={"size": (a.width, a.height), "format": "RGB888"}))
    c.set_controls({"AeEnable": False, "AwbEnable": False,
                    "ExposureTime": a.exposure, "AnalogueGain": a.gain})
    c.start(); time.sleep(2)
    img = c.capture_array("main")[:, :, 1].astype(float)
    c.stop()
    np.save(RIG / "darkframe.npy", img)
    print(f"mean {img.mean():.2f}   max {img.max():.0f}   sd {img.std():.2f}")
    print(f"saved {RIG / 'darkframe.npy'} — subtract it if you cannot seal the box")
    return _verdict(img.mean() < 2 and img.max() < 5,
                    "the box is dark enough",
                    "light is getting in. Re-tape the cable hole, then the lid, "
                    "then the screen bezel. If you cannot get below it, record a "
                    "dark frame every session and subtract it — and write that "
                    "down as a deviation, because a subtracted offset is not the "
                    "same as no offset when you are measuring drift.")


# --------------------------------------------------------------------- B-5
def lag(a) -> int:
    """How many frames does the camera trail the screen?

    Built from the signal itself rather than from clocks: the predicted tuning
    of every channel is known from the logged heading, so the lag is whichever
    shift makes prediction and measurement agree best.
    """
    X, head, _ = _load(a.cap, a.stim)
    pref = np.load(RIG / "preferred_directions.npy")[:X.shape[1]]
    pred = np.cos(head[:, None] - pref[None, :])

    Xz = (X - X.mean(0)) / (X.std(0) + 1e-9)
    Pz = (pred - pred.mean(0)) / (pred.std(0) + 1e-9)

    shifts = np.arange(-a.max_shift, a.max_shift + 1)
    score = []
    for k in shifts:
        if k >= 0:
            aa, bb = Pz[:len(Pz) - k], Xz[k:]
        else:
            aa, bb = Pz[-k:], Xz[:len(Xz) + k]
        score.append(float(np.mean(aa * bb)))
    best = int(shifts[int(np.argmax(score))])
    print("shift(frames)  agreement")
    for k, v in zip(shifts, score):
        print(f"{k:>10}    {v:+.4f}{'   <-- best' if k == best else ''}")
    print(f"\nbest lag: {best} frames = {best / a.fps:.3f} s")
    print(f"pass this to run_block.py as --lag {best / a.fps:.3f}")
    return _verdict(abs(best) <= 3,
                    "timing is close enough to ignore",
                    f"the camera trails by {best} frames. That is fine IF it is "
                    f"stable: repeat this on two more blocks, and if the answer "
                    f"agrees, pass --lag {best / a.fps:.3f} to run_block.py and "
                    f"record it in the log. If it does NOT agree between blocks, "
                    f"drop to 25 fps, or fall back to B-5b: hold each heading for "
                    f"5 s (--hold 250) and analyse only the middle 3 s.")


# --------------------------------------------------------------------- B-6
def dither(a) -> int:
    """Does a modulation of half a brightness level actually reach the camera?"""
    X, head, _ = _load(a.cap, a.stim)
    pref = np.load(RIG / "preferred_directions.npy")[:X.shape[1]]
    pred = np.cos(head[:, None] - pref[None, :])
    r = np.array([np.corrcoef(pred[:, i], X[:, i])[0, 1]
                  for i in range(X.shape[1])])
    r = r[np.isfinite(r)]
    med = float(np.median(r))
    print(f"channels           {len(r)}")
    print(f"median correlation {med:+.4f}")
    print(f"fraction positive  {float(np.mean(r > 0)):.2f}")
    print(f"observed swing     {X.max() - X.min():.2f} counts")
    print("\nA small number is expected and correct — the whole calibration is "
          "built on a signal of about half a brightness level. What matters is "
          "that it is positive and consistent across channels.")
    return _verdict(med > 0.02 and np.mean(r > 0) > 0.8,
                    "the dither is getting through",
                    "the modulation is being lost. In order of likelihood: (1) the "
                    "screen is applying its own processing — turn off dynamic "
                    "contrast, any 'enhancement', and every power-saving dimmer; "
                    "(2) the exposure is too short to average the dither, so try "
                    "--exposure 16000; (3) the panel is really 6-bit with its own "
                    "dithering, so try a different screen. Only if all three fail, "
                    "raise --depth fourfold AND re-run "
                    "scripts/72_rig_digital_twin.py at the new value, because you "
                    "will no longer be matched to cortex and every comparison must "
                    "say so.")


# --------------------------------------------------------------------- B-7
def margin(a) -> int:
    """Decoding error against measured chance — is the rig as hard as cortex?"""
    X, head, _ = _load(a.cap, a.stim)
    n_fit = int(0.6 * len(X))
    mu, sd = X[:n_fit].mean(0), X[:n_fit].std(0) + 1e-9
    Z = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])
    Y = np.column_stack([np.cos(head), np.sin(head)])
    A = Z[:n_fit].T @ Z[:n_fit] + np.eye(Z.shape[1])
    A[-1, -1] -= 1.0
    W = np.linalg.solve(A, Z[:n_fit].T @ Y[:n_fit])
    P = Z[n_fit:] @ W

    def err(pred, truth):
        ang = np.arctan2(pred[:, 1], pred[:, 0])
        return np.degrees(np.abs(np.arctan2(np.sin(ang - truth),
                                            np.cos(ang - truth))))

    e = float(np.median(err(P, head[n_fit:])))
    rng = np.random.default_rng(0)
    c = float(np.mean([np.median(err(P, rng.permutation(head[n_fit:])))
                       for _ in range(20)]))
    print(f"median error   {e:.1f} deg")
    print(f"measured chance{c:>7.1f} deg   (shuffled, not assumed to be 90)")
    print(f"margin         {c - e:.1f} deg   target {NEURAL_MARGIN_T11:.1f} (T11)")
    return _verdict(abs((c - e) - NEURAL_MARGIN_T11) < 6.0,
                    "the rig is at cortex's operating point",
                    f"margin is {c - e:.1f} against a target of "
                    f"{NEURAL_MARGIN_T11:.1f}. Too LARGE means the rig is too "
                    f"easy: lower --depth (halving it roughly doubles the error). "
                    f"Too SMALL means it is too hard: raise --depth, or raise "
                    f"--exposure, or average more pixels per channel by raising "
                    f"the capture size toward 96x64. Record the final --depth and "
                    f"never change it again.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("darkframe", help="B-2: is the box light-tight?")
    d.add_argument("--width", type=int, default=48)
    d.add_argument("--height", type=int, default=32)
    d.add_argument("--exposure", type=int, default=8000)
    d.add_argument("--gain", type=float, default=2.0)
    d.set_defaults(fn=darkframe)

    for name, fn, helptext in [("lag", lag, "B-5: camera/screen timing"),
                               ("dither", dither, "B-6: sub-level signal"),
                               ("margin", margin, "B-7: difficulty")]:
        q = sub.add_parser(name, help=helptext)
        q.add_argument("--cap", required=True)
        q.add_argument("--stim", required=True)
        q.add_argument("--fps", type=int, default=50)
        if name == "lag":
            q.add_argument("--max-shift", type=int, default=10)
        q.set_defaults(fn=fn)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/run_batch.py`

```python
#!/usr/bin/env python3
"""
run_batch.py — record many blocks unattended, for the long arms of the study.

The drift sweep needs 5 levels x 53 blocks = 265 blocks, about 22 hours
(reports/DRIFT_SWEEP_DESIGN.md). Nobody is starting those by hand, and a study
run by hand at 2am is a study with a typo in it somewhere.

This reads a plan file -- one line per block, saying what to record -- and works
through it, skipping blocks already present so an interrupted run can simply be
restarted. It never overwrites a finished block.

    python3 rig/run_batch.py --plan rig/plans/sweep.txt
    python3 rig/run_batch.py --plan rig/plans/sweep.txt --dry-run
    python3 rig/run_batch.py --make-sweep-plan rig/plans/sweep.txt

PLAN FILE FORMAT
    One block per line, as arguments to run_block.py. Blank lines and lines
    starting with # are ignored.

        --session 10 --blocknum 1 --drift-tau 4 --drift-depth 0.3
        --session 10 --blocknum 2 --drift-tau 4 --drift-depth 0.3

A PHYSICAL FAULT CANNOT BE AUTOMATED
------------------------------------
Blocks carrying a fault you impose by hand -- the ND filter, tape on the lens, a
fingerprint -- must be run one at a time with run_block.py, because somebody has
to put the filter there. Use this only for the arms where nothing is touched:
healthy blocks, and the imposed-drift sweep, which the stimulus does in software.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RIG = Path(__file__).resolve().parent
REPO = RIG.parent


def sweep_plan(path: Path, session: int, levels, blocks: int, depth: float) -> None:
    """The 5-level drift sweep from reports/DRIFT_SWEEP_DESIGN.md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Drift sweep. Levels and block count computed by",
             "# scripts/71_drift_sweep_design.py -- not guessed.",
             "# Nothing is touched by hand during these, so they can run unattended.",
             ""]
    n = 1
    for tau in levels:
        lines.append(f"# --- tau = {tau:g} s ---")
        for _ in range(blocks):
            lines.append(f"--session {session} --blocknum {n} "
                         f"--drift-tau {tau:g} --drift-depth {depth} "
                         f"--fault IMPOSED_DRIFT --note tau={tau:g}")
            n += 1
        lines.append("")
    path.write_text("\n".join(lines) + "\n")
    total = len(levels) * blocks
    print(f"wrote {path}: {total} blocks, about "
          f"{total * 300 / 3600:.1f} hours of recording")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan")
    ap.add_argument("--make-sweep-plan")
    ap.add_argument("--session", type=int, default=10)
    ap.add_argument("--levels", type=float, nargs="+",
                    default=[4, 13, 42, 140, 811])
    ap.add_argument("--blocks", type=int, default=53)
    ap.add_argument("--drift-depth", type=float, default=0.3)
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.make_sweep_plan:
        sweep_plan(Path(a.make_sweep_plan), a.session, a.levels, a.blocks,
                   a.drift_depth)
        return 0
    if not a.plan:
        ap.error("give --plan, or --make-sweep-plan to create one")

    lines = [l.strip() for l in Path(a.plan).read_text().splitlines()]
    jobs = [l for l in lines if l and not l.startswith("#")]
    print(f"{len(jobs)} blocks in {a.plan}")

    done = failed = skipped = 0
    for i, job in enumerate(jobs, 1):
        parts = job.split()
        try:
            sess = parts[parts.index("--session") + 1]
            blk = parts[parts.index("--blocknum") + 1]
        except ValueError:
            print(f"[{i}] malformed line, no --session/--blocknum: {job}")
            failed += 1
            continue

        out = REPO / a.root / "RIG" / f"day_{sess}" / f"block_{blk}"
        if out.exists():
            skipped += 1
            continue

        cmd = [sys.executable, str(RIG / "run_block.py")] + parts
        if a.dry_run:
            cmd.append("--dry-run")
        print(f"[{i}/{len(jobs)}] session {sess} block {blk}")
        if subprocess.run(cmd).returncode == 0:
            done += 1
        else:
            failed += 1
            print("  FAILED — continuing. Check rig/blocklog.csv before trusting "
                  "this session, and re-run this plan to fill the gap.")

    print(f"\nrecorded {done}, skipped {skipped} already present, {failed} failed")
    if failed:
        print("Re-running the same plan will retry only the missing blocks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/daily_session.py`

```python
#!/usr/bin/env python3
"""
daily_session.py — the unattended arm: record a few blocks a day, for weeks.

WHAT THIS ARM IS FOR
--------------------
Every fault in this project is something I invented and then applied. Nobody has
checked whether real degradation looks anything like an invented ramp. This arm
answers that by leaving the rig completely alone for six to ten weeks and
recording whatever drift it produces on its own -- dust, thermal cycling,
mechanical creep, LED ageing, whatever the room does to it.

Prediction P-R7 is judged on these recordings: natural drift will resemble at
least one of the four designed fault modes at a rate above chance (25%). A
negative answer there is the more interesting one, because it would say that
1,850 episodes of carefully constructed ground truth do not resemble what
actually goes wrong -- a finding about how fault benchmarks get built, including
this project's own.

RUN IT FROM CRON, NOT BY HAND
-----------------------------
    crontab -e

then add:

    0 3 * * * /usr/bin/python3 /home/pi/bci-ews-research/rig/daily_session.py >> /home/pi/rig_cron.log 2>&1

03:00 is deliberate: ambient conditions are most stable and nobody will open the
box. An arm whose whole point is that nothing was touched is ruined by somebody
tidying up at noon.

THE SESSION NUMBER COMES FROM THE DATE, NOT FROM A COUNTER
----------------------------------------------------------
Session number is days since --start-date. A counter in a file would drift out
of step the first time a run is missed or repeated, and this arm runs unattended
for weeks, so missed runs are certain. Deriving it from the calendar means a
power cut costs one session and nothing else: the gap is visible in the data
instead of silently renumbering everything after it.

THE ONE RULE
------------
Change nothing while this arm is running. No cleaning, no refocusing, no
re-seating the ribbon, no adjusting the screen. If something IS changed, record
it in research/research_log.md with the date -- an undocumented intervention
midway through a six-week drift makes the whole arm uninterpretable, and there
is no way to detect it afterwards.

Usage:
    python3 rig/daily_session.py                      # normal cron use
    python3 rig/daily_session.py --dry-run            # show what it would do
    python3 rig/daily_session.py --blocks 6
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

RIG = Path(__file__).resolve().parent
START_DEFAULT = "2026-10-01"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start-date", default=START_DEFAULT,
                    help="day 1 of the arm, YYYY-MM-DD")
    ap.add_argument("--blocks", type=int, default=4,
                    help="blocks per day; 4 x 5 min = 20 min")
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="MUST match the value B-7 settled on")
    ap.add_argument("--lag", type=float, default=0.0,
                    help="the value B-5 measured")
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    start = dt.date.fromisoformat(a.start_date)
    today = dt.date.today()
    session = (today - start).days + 1
    if session < 1:
        print(f"{today} is before the start date {start}; nothing to do")
        return 0

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== {stamp} — natural-drift arm, day {session} "
          f"({a.blocks} blocks) ===")

    ok = failed = 0
    for b in range(1, a.blocks + 1):
        cmd = [sys.executable, str(RIG / "run_block.py"),
               "--session", str(session), "--blocknum", str(b),
               "--depth", str(a.depth), "--lag", str(a.lag),
               "--fault", "NATURAL", "--severity", "0",
               "--note", f"unattended day {session}",
               "--root", a.root]
        if a.dry_run:
            cmd.append("--dry-run")
        if subprocess.run(cmd).returncode == 0:
            ok += 1
        else:
            failed += 1
            # A failed block must not stop the arm. A six-week record with one
            # gap is still a six-week record; a six-week record that stopped
            # silently on day 9 is nine days of data nobody noticed losing.
            print(f"  block {b} FAILED — continuing")

    print(f"day {session}: {ok} recorded, {failed} failed")
    if failed:
        print("Check rig/blocklog.csv and the camera before tomorrow's run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/motor.py`

```python
#!/usr/bin/env python3
"""
motor.py — turn the 28BYJ-48 stepper, for the GEOMETRY_ROTATION fault.

WHY A MOTOR AND NOT A SOFTWARE ROLL
-----------------------------------
scripts/72_rig_digital_twin.py models rotation by rolling the channel indices
around the grid. That is not what a physical rotation does: a real rotation also
blurs, crops the edges, and moves patches by fractions of a camera pixel. If the
rotation is imposed in software the fault is not a physical fault at all, which
defeats the purpose of having a rig.

So the stage turns. The motor also makes the rotation REPEATABLE and gives it a
severity ladder in real units -- steps -- instead of arbitrary ones.

WIRING (ULN2003 driver board to the Pi's 40-pin header)
    IN1 -> pin 11 (GPIO17)      VCC (5V)  -> pin 2
    IN2 -> pin 13 (GPIO27)      GND       -> pin 9
    IN3 -> pin 15 (GPIO22)
    IN4 -> pin 16 (GPIO23)
Never power the motor from the Pi's 3.3 V rail. Use the 5 V pin.

The 28BYJ-48 is geared 64:1 with 32 steps per motor revolution, so a full turn
of the output shaft is 4096 half-steps: about 0.088 degrees per step.

    python3 rig/motor.py --degrees 2          # rotate 2 degrees
    python3 rig/motor.py --degrees -2         # and back
    python3 rig/motor.py --steps 100 --delay 0.003

ALWAYS RETURN TO ZERO between conditions, and write the cumulative position in
the log. There is no encoder: if you lose count, the only recovery is to re-run
B-7 and re-aim.
"""
from __future__ import annotations

import argparse
import time

PINS = [17, 27, 22, 23]
STEPS_PER_REV = 4096
SEQ = [[1, 0, 0, 1], [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0],
       [0, 1, 1, 0], [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--degrees", type=float)
    g.add_argument("--steps", type=int)
    ap.add_argument("--delay", type=float, default=0.002,
                    help="seconds between half-steps; below ~0.0015 it stalls")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    steps = a.steps if a.steps is not None else \
        int(round(a.degrees * STEPS_PER_REV / 360.0))
    print(f"{steps} half-steps = {steps * 360.0 / STEPS_PER_REV:.3f} degrees")
    if a.dry_run:
        return 0

    try:
        import RPi.GPIO as GPIO
    except Exception:
        print("RPi.GPIO not available — this only runs on the Pi. "
              "Use --dry-run to check the arithmetic anywhere else.")
        return 1

    GPIO.setmode(GPIO.BCM)
    for p in PINS:
        GPIO.setup(p, GPIO.OUT, initial=0)
    try:
        direction = 1 if steps >= 0 else -1
        for i in range(abs(steps)):
            for p, v in zip(PINS, SEQ[(i * direction) % 8]):
                GPIO.output(p, v)
            time.sleep(a.delay)
    finally:
        for p in PINS:      # de-energise, or the coils cook and the stage drifts
            GPIO.output(p, 0)
        GPIO.cleanup()
    print("done; remember to record the cumulative position")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/logtemp.py`

```python
#!/usr/bin/env python3
"""
logtemp.py — read the DHT22 temperature and humidity sensor.

WHY BOTHER
----------
A CMOS sensor's dark current roughly doubles every 6-8 degrees C, so a warm room
looks like a drifting array. If the rig's risk signal rises over an afternoon
and the temperature also rose over that afternoon, there is no way to tell them
apart after the fact. Logging it costs nothing and makes that separable.

run_block.py calls this with --once after every block and writes the result into
rig/blocklog.csv. It is deliberately never fatal: a missing sensor must not stop
a recording.

    python3 rig/logtemp.py --once        # prints "temp_c,humidity"
    python3 rig/logtemp.py --watch 60    # a reading every 60 s to rig/temp.csv

IF YOU DO NOT HAVE THE SENSOR
-----------------------------
Skip it. Everything still runs; the temperature column stays empty. But write in
the log that it is missing, so a future you does not read empty cells as zero.
A phone thermometer photographed at the start and end of each session is a poor
substitute that is still better than nothing.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

RIG = Path(__file__).resolve().parent


def read_once(pin: int) -> tuple[float, float] | None:
    """One reading, or None. The DHT22 fails a fraction of reads by design."""
    try:
        import board
        import adafruit_dht
    except Exception:
        return None
    try:
        dht = adafruit_dht.DHT22(getattr(board, f"D{pin}"))
        for _ in range(5):
            try:
                t, h = dht.temperature, dht.humidity
                if t is not None and h is not None:
                    return float(t), float(h)
            except RuntimeError:
                time.sleep(2.0)     # a failed read is normal; retry
        return None
    except Exception:
        return None
    finally:
        try:
            dht.exit()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", type=int, default=4, help="BCM pin, GPIO4 = header pin 7")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", type=float, default=0.0, help="seconds between readings")
    ap.add_argument("--out", default=str(RIG / "temp.csv"))
    a = ap.parse_args()

    if a.once or not a.watch:
        r = read_once(a.pin)
        print(f"{r[0]:.1f},{r[1]:.1f}" if r else ",")
        return 0

    new = not Path(a.out).exists()
    with open(a.out, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "temp_c", "humidity"])
        try:
            while True:
                r = read_once(a.pin)
                w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"),
                            f"{r[0]:.1f}" if r else "", f"{r[1]:.1f}" if r else ""])
                f.flush()
                time.sleep(a.watch)
        except KeyboardInterrupt:
            print(f"\nstopped; wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `rig/stimulus.py`

```python
#!/usr/bin/env python3
"""Shows a grid of patches whose brightness encodes a heading direction.

Each patch has a fixed preferred direction. Its brightness is highest when the
current heading matches that preference, the same way a direction-tuned neuron
fires fastest for its preferred direction.

MODULATION DEPTH IS THE MOST IMPORTANT SETTING IN THIS FILE
-----------------------------------------------------------
A patch sits at --base brightness and swings by --depth with direction:

    patch = base + depth * cos(heading - preferred_direction)

The first version of this file used 0.5 * (1 + cos(...)), a full 100% swing.
Simulated in scripts/72_rig_digital_twin.py, that rig decoded direction to 0.0
degrees of error against an 89 degree chance level, where the neural data sits
at 54.6 against 90.7. Two things followed, both fatal: a comparison between a
perfect decoder and a barely-above-chance one measures difficulty rather than
neurons, and no injected fault could move an error that was already zero, so
there was no severity ladder at all.

Real direction-tuned neurons fire at a substantial baseline and modulate it
modestly, so each channel carries little information and the decoder is limited
by channel quality -- which is what makes degrading a channel matter. The small
default depth below reproduces that, and puts the rig within about a degree of
the neural operating point. Do not raise it to make the picture look nicer on
the screen; the whole comparison depends on it.

THE SCREEN CANNOT SHOW A FRACTION OF A BRIGHTNESS LEVEL, SO IT IS DITHERED
--------------------------------------------------------------------------
The calibrated depth asks each patch to swing by about half of one brightness
level: 126.96 to 128.03 out of 0-255. A display emits whole levels only, so
rounding each patch to an integer would throw the entire signal away and the rig
would record nothing but noise. This is a real hardware limit, not a modelling
detail, and it nearly went unnoticed.

The fix is spatial dithering, which is standard practice in visual
psychophysics. A patch is 40x40 = 1600 screen pixels. To show a mean level of
127.4, set 40% of its pixels to 128 and the rest to 127. The camera's optics and
its 2x2-pixel sampling average over the whole patch, so what it measures is the
fractional mean. Resolution becomes 1/1600 of a level instead of 1, which is
ample.

The dither mask is drawn once and reused every frame rather than redrawn each
time. That is faster, and more importantly it makes the dither a FIXED spatial
pattern instead of a new noise source flickering in every frame.

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
ap.add_argument("--brightness", type=float, default=1.0)  # 0-1, overall dimming
ap.add_argument("--base", type=float, default=0.5)       # DC level of every patch
ap.add_argument("--depth", type=float, default=0.00211)   # direction modulation
# ^ calibrated in reports/RIG_DIGITAL_TWIN.md to match T11's margin over chance.
ap.add_argument("--seed", type=int, default=20260826)
ap.add_argument("--concentration", type=float, default=0.0)  # 0 = all directions
# --- imposed drift, for the sweep in B-14 -----------------------------------
# The whole screen's brightness wanders slowly, as an Ornstein-Uhlenbeck process
# with time constant --drift-tau seconds: a random walk that is pulled back
# toward its mean, which is how you write "drifts slowly but does not wander
# off". This is the controlled degradation the calibration curve sweeps, so the
# realised path is written to the frame log and is not reconstructed afterwards.
ap.add_argument("--drift-tau", type=float, default=0.0)    # seconds; 0 = none
ap.add_argument("--drift-depth", type=float, default=0.0)  # fractional swing
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
w.writerow(["frame", "t_unix", "heading_rad", "trial", "drift_gain"])
# The true heading is logged every frame. It is the ground truth for the whole
# experiment, so it is recorded as it is drawn rather than reconstructed later.

def draw_heading():
    """Uniform over all directions by default. Raising --concentration makes
    headings cluster, which is the task-geometry variable I sweep in Phase 9."""
    if a.concentration <= 0:
        return rng.uniform(0, 2 * math.pi)
    return float(rng.vonmises(0.0, a.concentration))

# Fixed dither mask, drawn once. Comparing each pixel's threshold against a
# patch's fractional part decides whether that pixel shows the lower or the
# higher level, which makes the patch mean land between them.
H, W = a.rows * a.patch, a.cols * a.patch
DITHER = rng.random((W, H)).astype(np.float32)      # pygame is (x, y)
frame = np.empty((W, H, 3), dtype=np.uint8)

def expand(vals):
    """One value per patch -> one value per screen pixel, in pygame (x, y) order."""
    g = vals.reshape(a.rows, a.cols).T              # -> (cols, rows)
    return np.repeat(np.repeat(g, a.patch, 0), a.patch, 1)

# One OU step per frame. a is how much of the previous value survives; s_ou is
# the kick that keeps the stationary spread at 1 regardless of tau.
if a.drift_tau > 0 and a.drift_depth > 0:
    tau_frames = a.drift_tau * a.fps
    ou_a = math.exp(-1.0 / tau_frames)
    ou_s = math.sqrt(1 - ou_a * ou_a)
    ou_x = rng.normal()
else:
    ou_a = ou_s = ou_x = 0.0

heading, trial = draw_heading(), 0
try:
    for f in range(a.frames):
        if f % a.hold == 0:
            heading, trial = draw_heading(), f // a.hold
        if a.drift_tau > 0 and a.drift_depth > 0:
            ou_x = ou_a * ou_x + ou_s * rng.normal()
            gain = max(0.0, 1.0 + a.drift_depth * ou_x)
        else:
            gain = 1.0
        b = (a.base + a.depth * np.cos(heading - PREF)) * a.brightness * gain
        t = np.clip(b, 0, 1) * 255.0
        lo = np.floor(t)
        px = expand(lo) + (DITHER < expand(t - lo))
        v = px.astype(np.uint8)
        frame[:, :, 0] = v; frame[:, :, 1] = v; frame[:, :, 2] = v
        pygame.surfarray.blit_array(screen, frame)
        pygame.display.flip()
        w.writerow([f, time.time(), heading, trial, gain])
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                raise KeyboardInterrupt
        clock.tick(a.fps)
finally:
    log.close()
    pygame.quit()
```

## `rig/capture.py`

```python
#!/usr/bin/env python3
"""Records frames and reduces each one to N region averages.

Each region average is one channel, the same way each electrode's binned
activity is one channel in the neural data.

Exposure and white balance are FIXED. The automatic versions are compensators:
leave them on and the camera quietly cancels out the very degradation I am
trying to measure.

PIXELS PER CHANNEL IS THE SECOND CALIBRATION SETTING
----------------------------------------------------
Averaging N pixels into one channel divides that channel's noise by sqrt(N). The
first version of this file captured 480x320 and averaged 20x20 = 400 pixels per
channel, which made every channel twenty times quieter than a single pixel and
was half the reason the simulated rig decoded perfectly (see
scripts/72_rig_digital_twin.py and reports/RIG_DIGITAL_TWIN.md).

The defaults below capture 48x32 so that each channel is a 2x2 = 4 pixel block.
Together with the small modulation depth in stimulus.py this puts the rig at the
neural operating point. Raising the capture size back up will quietly make the
rig too good again.
"""
import argparse, time
import numpy as np
from picamera2 import Picamera2

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=24)
ap.add_argument("--rows", type=int, default=16)
ap.add_argument("--width", type=int, default=48)     # 48/24 = 2 px per side
ap.add_argument("--height", type=int, default=32)    # 32/16 = 2 px per side -> 4 px/channel
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

## `rig/to_mat.py`

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
