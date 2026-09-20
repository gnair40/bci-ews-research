#!/usr/bin/env python3
"""
bench.py — the checks that must pass before any session counts as data.

=============================================================================
WHY CHECKS COME BEFORE EXPERIMENTS
=============================================================================
Every one of these catches a failure that produces plausible-looking numbers
rather than an obvious error. That is what makes them worth running: a broken
apparatus that crashes costs an afternoon, and a broken apparatus that quietly
returns numbers costs the project.

    darkframe   Is the box actually dark? Stray light adds a slow drift as the
                room changes, and slow drift is exactly what the monitor is
                looking for. It would find it, and it would be right, and the
                result would be about the curtains.

    lag         How far behind the screen is the camera? Every direction label
                is shifted by this amount. Get it wrong and the decoder looks
                worse than it is, uniformly, in every session.

    dither      Is the sub-brightness-level signal surviving to the camera at
                all? The whole apparatus is built on a modulation of about half
                of one brightness level. Screens do their own processing, and
                some of them destroy it. If this fails, nothing downstream
                means anything.

    margin      Is the apparatus as hard as the real thing? A system that
                decodes perfectly has nothing left to lose when it is degraded.
                This is experiment P-1.

    check       Run everything that can be run from recordings already made.

=============================================================================
HOW TO RUN THEM
=============================================================================
Darkness (needs the camera, so run it on the Pi with the lid shut):

    python3 physical/code/bench.py darkframe

The other three read a recording that already exists:

    python3 physical/code/bench.py lag    --session 0 --block 1
    python3 physical/code/bench.py dither --session 0 --block 1
    python3 physical/code/bench.py margin --session 0 --block 1

    python3 physical/code/bench.py check  --session 0 --block 1

Record that first session with:

    python3 physical/code/run_session.py --session 0 --block 1 --calibration

=============================================================================
WHAT THEY PRODUCE
=============================================================================
Each prints PASS or FAIL and, when it fails, what to do about it in order of
likelihood. `lag` also writes `physical/data/lag.json`, which every analysis
script reads, so run it once and the rest of the pipeline picks it up.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import monitor as M

DATA = M.DATA
NEURAL_MARGIN = 36.1          # 90.7 chance - 54.6 error, participant T11
MARGIN_TOLERANCE = 6.0


def _verdict(ok: bool, good: str, bad: str) -> int:
    print(f"\n{'PASS' if ok else 'FAIL'} — {good if ok else bad}")
    return 0 if ok else 1


def _folder(a) -> Path:
    if a.folder:
        return Path(a.folder)
    return DATA / "raw" / f"s{a.session}_b{a.block}"


def _session(a):
    f = _folder(a)
    if not (f / "capture.npy").exists():
        raise SystemExit(
            f"No recording at {f}.\n"
            f"Record one first:\n"
            f"    python3 physical/code/run_session.py --session {a.session} "
            f"--block {a.block} --calibration")
    # Deliberately loaded with zero lag: these checks are what MEASURES the lag,
    # so applying a previously-saved one would hide a change in it.
    return M.load_session(f, 0.0)


def _predicted(s) -> np.ndarray:
    """What each channel should look like, from the logged direction alone."""
    # Next to the recordings first, so a dry run is checked against its own
    # channel definitions rather than the real apparatus's.
    pref_file = s.folder.parent.parent / "preferred_directions.npy"
    if not pref_file.exists():
        pref_file = DATA / "preferred_directions.npy"
    if not pref_file.exists():
        raise SystemExit(
            f"{pref_file} does not exist. It is written the first time "
            f"stimulus.py runs and defines which channel is which. Without it "
            f"there is nothing to compare the recording against.")
    pref = np.load(pref_file)[:s.X.shape[1]]
    return np.cos(s.heading[:, None] - pref[None, :])


# ----------------------------------------------------------------- darkframe
def darkframe(a) -> int:
    try:
        from picamera2 import Picamera2
    except ImportError:
        print("picamera2 is not installed — this check needs the camera, so it")
        print("only runs on the Raspberry Pi.")
        return 1
    import time
    c = Picamera2()
    c.configure(c.create_video_configuration(
        main={"size": (a.width, a.height), "format": "RGB888"}))
    c.set_controls({"AeEnable": False, "AwbEnable": False,
                    "ExposureTime": a.exposure, "AnalogueGain": a.gain})
    c.start()
    time.sleep(2)
    img = c.capture_array("main")[:, :, 1].astype(float)
    c.stop()
    DATA.mkdir(parents=True, exist_ok=True)
    np.save(DATA / "darkframe.npy", img)
    print(f"mean {img.mean():.2f}   max {img.max():.0f}   sd {img.std():.2f}")
    print(f"saved {DATA / 'darkframe.npy'}")
    return _verdict(
        img.mean() < 2 and img.max() < 5,
        "the box is dark enough",
        "light is getting in. Re-tape, in this order: the cable hole, the lid "
        "seam, the screen bezel. If you cannot get below it, record a dark "
        "frame every session and subtract it — and write that down as a "
        "deviation, because a subtracted offset is not the same as no offset "
        "when the thing being measured is drift.")


# ----------------------------------------------------------------------- lag
def lag(a) -> int:
    """Found from the signal itself, not from clocks.

    The direction on the screen is known for every frame, so what each channel
    *should* be doing is known too. The lag is whichever shift lines the
    prediction up with the measurement best. That needs no extra hardware and
    no assumption about how long the camera pipeline takes.
    """
    s = _session(a)
    P = _predicted(s)
    Xz = (s.X - s.X.mean(0)) / (s.X.std(0) + 1e-9)
    Pz = (P - P.mean(0)) / (P.std(0) + 1e-9)

    shifts = np.arange(-a.max_shift, a.max_shift + 1)
    score = []
    for k in shifts:
        if k >= 0:
            p, x = Pz[:len(Pz) - k], Xz[k:]
        else:
            p, x = Pz[-k:], Xz[:len(Xz) + k]
        score.append(float(np.mean(p * x)))
    best = int(shifts[int(np.argmax(score))])
    print("shift (frames)   agreement")
    for k, v in zip(shifts, score):
        print(f"{k:>12}     {v:+.4f}{'   <-- best' if k == best else ''}")
    seconds = best / M.FPS
    print(f"\nbest lag: {best} frames = {seconds:.3f} s")

    if best == shifts[0] or best == shifts[-1]:
        print("\nThe best shift is at the edge of the range searched, which means")
        print("the true lag is probably larger. Re-run with a bigger --max-shift.")
        return 1

    # Written beside the recordings it was measured on. For the real apparatus
    # that is physical/data/lag.json, which the analysis reads by default. For a
    # dry run it lands under physical/data/dryrun/, so a delay measured on fake
    # recordings can never be applied to real ones by accident.
    out = s.folder.parent.parent / "lag.json"
    out.write_text(json.dumps(
        {"lag_seconds": seconds, "lag_frames": best,
         "measured_on": s.folder.name, "fps": M.FPS}, indent=2))
    print(f"wrote {out}")
    if out.parent != DATA:
        print("(beside these recordings, not in physical/data/, because they are")
        print(" not the real apparatus)")
    else:
        print("every analysis script reads it")

    return _verdict(
        abs(best) <= 3,
        "timing is close enough to ignore, and has been saved anyway",
        f"the camera trails by {best} frames. That is workable IF it is stable: "
        f"repeat this on two more recordings. If they agree, carry on — the "
        f"saved value is applied automatically. If they do NOT agree, the delay "
        f"is varying, which no fixed correction can fix: drop to 25 fps, or "
        f"hold each direction for 5 seconds (--hold 250) and analyse only the "
        f"middle 3 seconds of each.")


# -------------------------------------------------------------------- dither
def dither(a) -> int:
    s = _session(a)
    P = _predicted(s)
    r = np.array([np.corrcoef(P[:, i], s.X[:, i])[0, 1]
                  for i in range(s.X.shape[1])])
    r = r[np.isfinite(r)]
    med, pos = float(np.median(r)), float(np.mean(r > 0))
    print(f"channels            {len(r)}")
    print(f"median agreement    {med:+.4f}")
    print(f"fraction positive   {pos:.2f}")
    print(f"observed swing      {s.X.max() - s.X.min():.2f} brightness counts")
    print()
    print("A SMALL number here is expected and correct. The apparatus is")
    print("deliberately built on a modulation of about half of one brightness")
    print("level, so a large agreement would mean the calibration is wrong, not")
    print("that things are going well. What matters is that it is positive and")
    print("consistent across channels.")
    return _verdict(
        med > 0.02 and pos > 0.8,
        "the sub-level signal is reaching the camera",
        "the modulation is being destroyed somewhere between the screen and the "
        "sensor. In order of likelihood: (1) the screen is processing the image "
        "— turn off dynamic contrast, every 'enhancement' setting, and all "
        "power-saving dimmers; (2) the exposure is too short to average the "
        "dither, so try --exposure 16000; (3) the panel is really 6-bit and "
        "dithers on its own, so try a different screen. Only if all three fail, "
        "raise --depth fourfold — and then re-run `margin`, because the "
        "apparatus will no longer be matched to cortex and every comparison "
        "must say so.")


# -------------------------------------------------------------------- margin
def margin(a) -> int:
    """P-1: is the apparatus as hard as the neural recordings?"""
    s = _session(a)
    n_fit = int(0.6 * len(s.X))
    dec = M.fit_decoder(s.X[:n_fit], s.heading[:n_fit])
    e = M.angular_error(s.X[n_fit:], s.heading[n_fit:], dec)
    err = float(np.nanmedian(e))
    # Chance is measured on this apparatus rather than assumed to be 90 degrees.
    # The directions in a finite recording are not perfectly uniform, so the
    # real chance level is a few degrees away from the textbook one, and
    # crediting the difference to the decoder would be inventing skill.
    rng = np.random.default_rng(0)
    ch = float(np.mean([np.nanmedian(M.angular_error(
        s.X[n_fit:], rng.permutation(s.heading[n_fit:]), dec)) for _ in range(20)]))
    m = ch - err
    print(f"median error        {err:6.1f} deg")
    print(f"measured chance     {ch:6.1f} deg   (shuffled, not assumed to be 90)")
    print(f"margin              {m:6.1f} deg   target {NEURAL_MARGIN:.1f} "
          f"(participant T11)")
    return _verdict(
        abs(m - NEURAL_MARGIN) < MARGIN_TOLERANCE,
        f"the apparatus is at the neural operating point. Write the modulation "
        f"depth down and never change it again.",
        f"the margin is {m:.1f} against a target of {NEURAL_MARGIN:.1f}. "
        f"TOO LARGE means the apparatus is too easy — lower --depth (halving it "
        f"roughly doubles the error). TOO SMALL means it is too hard — raise "
        f"--depth, or raise --exposure, or average more pixels per channel by "
        f"raising the capture size toward 96x64. Change ONE of those, record "
        f"another calibration session, and run this again.")


# --------------------------------------------------------------------- check
def check(a) -> int:
    """Everything that can be checked from a recording already made."""
    results = {}
    for name, fn in (("lag", lag), ("dither", dither), ("margin", margin)):
        print("=" * 70)
        print(name)
        print("=" * 70)
        try:
            results[name] = fn(a) == 0
        except SystemExit as e:
            print(e)
            results[name] = False
        print()
    print("=" * 70)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 70)
    if all(results.values()):
        print("Ready to record. Run darkframe on the Pi as well if you have not.")
        return 0
    print("Fix the failures above before recording anything that counts as data.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("darkframe", help="is the box light-tight?")
    d.add_argument("--width", type=int, default=48)
    d.add_argument("--height", type=int, default=32)
    d.add_argument("--exposure", type=int, default=8000)
    d.add_argument("--gain", type=float, default=2.0)
    d.set_defaults(fn=darkframe)

    for name, fn, h in (("lag", lag, "camera/screen timing"),
                        ("dither", dither, "is the sub-level signal surviving?"),
                        ("margin", margin, "P-1: is it as hard as cortex?"),
                        ("check", check, "run all three on one recording")):
        q = sub.add_parser(name, help=h)
        q.add_argument("--session", type=int, default=0)
        q.add_argument("--block", type=int, default=1)
        q.add_argument("--folder", default=None,
                       help="a recording folder, instead of session/block")
        q.add_argument("--max-shift", type=int, default=10)
        q.set_defaults(fn=fn)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
