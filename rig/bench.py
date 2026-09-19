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
