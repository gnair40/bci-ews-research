#!/usr/bin/env python3
"""
monitor.py — the shared machinery every physical-phase analysis uses.

=============================================================================
WHY THERE IS A SHARED FILE AT ALL
=============================================================================
Four different scripts need to answer the same questions about a recording:
what was the decoder's error, what did the monitor think, and when did it warn.
If each of them worked that out for itself, they would drift apart, and two
scripts reporting different numbers from the same recording is the kind of bug
that survives to a science fair poster.

So the work is done once, here, and the analysis scripts import it. This file
is not run directly (except for `--selftest`, below).

=============================================================================
WHAT IT REUSES RATHER THAN REINVENTS
=============================================================================
The monitor itself is **not rewritten for the physical apparatus**. It imports
the exact detector and the exact state machine used on the neural recordings:

    scripts/19_detectors.py        the baseline detectors
    scripts/22_decoder_guard.py    the monitor this project built
    scripts/20_evaluation_harness.py   the WARN state machine and detrending

That is what makes the two halves comparable. If the physical phase used a
differently-tuned monitor, a difference in the result could just as easily be a
difference in the monitor, and the comparison would say nothing. The apparatus
changes; the thing being tested does not.

The window length (30 s) and step (5 s) are the same too, and that is not a
coincidence: the neural recordings are binned at 20 ms, which is 50 bins per
second, and the apparatus runs at 50 frames per second. One camera frame plays
the part of one neural bin exactly.

=============================================================================
THE ONE SCIENTIFIC CHOICE IN THIS FILE, STATED PLAINLY
=============================================================================
**Which data is the decoder fitted on?** Two defensible answers:

*Frozen (the default).* Fit the decoder once, on a set of healthy sessions at
the start, and never refit. Every later session is read with that same decoder.
This is what happens to a real implant: it is calibrated on one day and used on
later ones, and the drift between those days is exactly the problem. It is also
what the computational half does — the neural decoder is fitted on early days
and applied to later ones.

*Per-session.* Refit the decoder at the start of every session. Within-session
degradation still shows up, but drift between sessions becomes invisible,
because each session is read with a decoder tuned to itself.

The default is **frozen**, because the question is about decoders going stale.
Per-session is available as `--decoder per-session` and is worth running as a
check: if a result only appears with a frozen decoder, it is a result about
staleness, and it should be described that way rather than as a result about
degradation.

=============================================================================
TWO DIFFERENT TIMES, AND WHY BOTH ARE REPORTED
=============================================================================
There are two questions that sound the same and are not:

    lead time         How long before the decoder actually became unusable did
                      the monitor warn? This is what decides whether a warning
                      is worth having. Positive means the warning came first.
                      Measured as: when performance crossed its degradation
                      threshold, minus when the monitor warned.

    detection delay   How long after the fault physically began did the monitor
                      notice? Measured as: when the monitor warned, minus the
                      onset that was drawn and checksummed beforehand.

Lead time is defined exactly as in the computational half, so the two can be
compared. **Detection delay is the one this phase adds**, and it cannot be
computed on any archived human recording, because nobody wrote down when the
electrodes started failing. It is the measurement the apparatus exists for.

They can disagree in an interesting way. A monitor can have a long detection
delay (slow to notice) and still a positive lead time, if performance holds up
for a while after the fault starts. It can also warn *before* the onset, which
is not early detection but a false alarm that happened to land in a degraded
session -- those are counted as false alarms, never as detections.

=============================================================================
WHAT COUNTS AS THE SESSION'S "RISK SCORE" AND "PERFORMANCE"
=============================================================================
    performance   the median angular error, in degrees, across the session's
                  windows. Higher means the decoder is reading the direction
                  less accurately. This is the thing that actually matters.

    risk_score    the median of the monitor's per-window risk across the
                  session. Median rather than maximum, because a maximum over
                  55 windows is mostly a measure of the noisiest window.

Both are medians so that one bad window cannot move either of them, and so they
are comparable to each other.

=============================================================================
SELF-TEST
=============================================================================
    python3 physical/code/monitor.py --selftest

This builds a fake recording in memory — one where the answer is known — and
checks that the decoder, the windowing and the monitor all behave. It needs no
camera and no recordings, so it can be run on any computer, and it is the
fastest way to find out whether an installation is broken.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
REPO = HERE.parent.parent

# ---- windowing, identical to the neural harness --------------------------
WINDOW_FRAMES = 1500        # 30 s at 50 fps
STEP_FRAMES = 250           # 5 s -- the resolution of any lead-time claim
FPS = 50

# ---- the operating point -------------------------------------------------
FALSE_ALARM_BUDGET_PER_HOUR = 0.1    # one false WARN per ten healthy hours

RIDGE = 1e-3                # keeps the decoder fit stable on 384 channels


def _load(name: str, filename: str):
    """Import one of the numbered scripts, whose names are not valid modules."""
    spec = importlib.util.spec_from_file_location(
        name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


det = _load("det19", "19_detectors.py")
guard = _load("guard22", "22_decoder_guard.py")
harness = _load("harness20", "20_evaluation_harness.py")

DETECTORS = {
    "decoder_guard": guard.DETECTORS["decoder_guard"],
    "mean_activity": det.MeanActivity,
    "robust_dispersion": det.RobustDispersion,
    "distribution_shift": det.DistributionShift,
}


# ==========================================================================
# LOADING A RECORDING
# ==========================================================================

@dataclass
class Session:
    session: int
    block: int
    X: np.ndarray            # frames x channels, camera
    heading: np.ndarray      # true direction on each of those frames, radians
    t: np.ndarray            # clock time of each frame, seconds from the start
    plan: dict | None
    folder: Path

    @property
    def healthy(self) -> bool:
        return bool(self.plan["healthy"]) if self.plan else True

    @property
    def onset_frame(self) -> int | None:
        return (self.plan or {}).get("onset_frame")

    @property
    def duration_seconds(self) -> float:
        return float(self.t[-1] - self.t[0]) if len(self.t) > 1 else 0.0


def load_session(folder: Path, lag_s: float = 0.0) -> Session:
    """Read one recording and line the camera up with the screen.

    The camera and the screen run as two separate programs, each writing its own
    clock times. They are not in lockstep: the screen puts a frame up, and the
    camera sees it a little later -- the sensor's exposure and the pipeline both
    take time. That delay is `lag_s`, and it is measured once by
    `bench.py lag`. Getting it wrong shifts every direction label by a fixed
    amount, which makes the decoder look worse than it is.
    """
    folder = Path(folder)
    X = np.load(folder / "capture.npy").astype(np.float64)
    tc = np.load(folder / "capture_t.npy").astype(np.float64)

    stim = np.genfromtxt(folder / "stim.csv", delimiter=",", names=True)
    ts, heading = np.asarray(stim["t_unix"]), np.asarray(stim["heading_rad"])

    # For each camera frame, which direction was on the screen when the light
    # that reached the sensor left it? The last stimulus frame at or before
    # (camera time - lag).
    idx = np.searchsorted(ts, tc - lag_s, side="right") - 1
    keep = idx >= 0
    X, tc, idx = X[keep], tc[keep], idx[keep]

    # The plan lives next to the recordings, in a sibling "onsets" folder. That
    # keeps a set of recordings and the plans they were drawn from together, so
    # the dry-run fakes can never accidentally be matched against real plans.
    plan_file = folder.parent.parent / "onsets" / f"{folder.name}.json"
    if not plan_file.exists():
        plan_file = DATA / "onsets" / f"{folder.name}.json"
    plan = json.loads(plan_file.read_text()) if plan_file.exists() else None

    # A P-5 session has no drawn plan -- its fault was caused by hand and its
    # onset was written down afterwards with note_onset.py. It is read here so
    # the same code can score it, and it carries onset_provenance: "stopwatch"
    # so that everything downstream can keep it out of the drawn-onset tables.
    if plan is None:
        noted = folder / "observed_onset.json"
        if noted.exists():
            plan = json.loads(noted.read_text())

    s, b = folder.name.lstrip("s").split("_b")
    return Session(int(s), int(b), X, heading[idx], tc - tc[0], plan, folder)


@dataclass
class SessionInfo:
    """Everything about a recording EXCEPT the recording itself.

    A campaign of 480 five-minute sessions is 22 GB of camera data. Nothing can
    hold that in memory, and nothing needs to: deciding which group a session
    belongs to, how long it was, and what fault it carried takes a few hundred
    bytes of metadata, not 46 MB of frames.

    So the table builder reads this first for every session, works out the
    groups, and only then loads sessions one at a time to score them. Without
    that split the analysis crashes on the fourth night of recording, which is
    the worst possible moment to discover it.
    """
    folder: Path
    session: int
    block: int
    kind: str
    plan: dict | None
    n_frames: int
    duration_seconds: float

    @property
    def healthy(self) -> bool:
        return bool(self.plan["healthy"]) if self.plan else True

    @property
    def name(self) -> str:
        return self.folder.name


def session_info(folder: Path) -> SessionInfo:
    """Read a recording's metadata without touching its camera data."""
    folder = Path(folder)
    # capture_t.npy is one float64 per frame -- 120 KB for a five-minute
    # session, against 46 MB for the frames themselves.
    t = np.load(folder / "capture_t.npy", mmap_mode="r")
    dur = float(t[-1] - t[0]) if len(t) > 1 else 0.0

    j = folder / "session.json"
    kind = json.loads(j.read_text()).get("kind", "experiment") if j.exists() else "experiment"

    plan_file = folder.parent.parent / "onsets" / f"{folder.name}.json"
    if not plan_file.exists():
        plan_file = DATA / "onsets" / f"{folder.name}.json"
    plan = json.loads(plan_file.read_text()) if plan_file.exists() else None
    if plan is None:
        noted = folder / "observed_onset.json"
        if noted.exists():
            plan = json.loads(noted.read_text())

    s, b = folder.name.lstrip("s").split("_b")
    return SessionInfo(folder, int(s), int(b), kind, plan, len(t), dur)


def find_sessions(root: Path | None = None) -> list[Path]:
    root = Path(root) if root else DATA / "raw"
    return sorted((p for p in root.glob("s*_b*") if (p / "capture.npy").exists()),
                  key=lambda p: tuple(int(x) for x in p.name.lstrip("s").split("_b")))


# ==========================================================================
# THE DECODER
# ==========================================================================

def fit_decoder(X: np.ndarray, heading: np.ndarray) -> tuple:
    """Learn to read direction out of the channels.

    The decoder is a straight line fit: each channel gets a weight, and the
    weighted sum gives two numbers, which are read as a direction. That is the
    same form as the decoder used on the neural data, on purpose -- a cleverer
    decoder here would make the apparatus easier than the thing it stands in
    for, which is the one property it must not have.

    Returns the weights and the normalisation, which travel together. Applying
    weights without the normalisation they were fitted with gives nonsense.
    """
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std < 1e-12] = 1.0
    Z = np.hstack([(X - mean) / std, np.ones((len(X), 1))])
    Y = np.column_stack([np.cos(heading), np.sin(heading)])
    A = Z.T @ Z + RIDGE * len(Z) * np.eye(Z.shape[1])
    W = np.linalg.solve(A, Z.T @ Y)
    return W, mean, std


def fit_decoder_streaming(folders, lag: float = 0.0) -> tuple:
    """The same decoder, fitted without holding every session in memory.

    `fit_decoder` needs the whole matrix at once, which is fine for one session
    and impossible for fifty. Since more calibration sessions are strictly
    better -- each one is a fault-free session that does NOT have to be spent on
    fitting -- the fit set is the part of a campaign most likely to grow, and it
    is the last place that should have a size limit.

    Two passes, each loading one session at a time:

      1. mean and standard deviation per channel, from running sums.
      2. the normal equations Z'Z and Z'Y, accumulated session by session.

    Peak memory is one session, and the accumulators are 385x385 -- about a
    megabyte -- whatever the campaign size. The result is identical to
    `fit_decoder` on the concatenated data, up to floating-point ordering.
    """
    folders = [Path(f) for f in folders]
    if not folders:
        raise ValueError("no sessions to fit the decoder on")

    # ---- pass 1: per-channel mean and standard deviation -----------------
    n_total = 0
    s1 = s2 = None
    for f in folders:
        X = load_session(f, lag).X
        if s1 is None:
            s1, s2 = np.zeros(X.shape[1]), np.zeros(X.shape[1])
        s1 += X.sum(axis=0)
        s2 += (X * X).sum(axis=0)
        n_total += len(X)
    mean = s1 / n_total
    var = np.maximum(s2 / n_total - mean * mean, 0.0)
    std = np.sqrt(var)
    std[std < 1e-12] = 1.0

    # ---- pass 2: the normal equations ------------------------------------
    d = len(mean) + 1
    A = np.zeros((d, d))
    B = np.zeros((d, 2))
    for f in folders:
        sess = load_session(f, lag)
        Z = np.hstack([(sess.X - mean) / std, np.ones((len(sess.X), 1))])
        Y = np.column_stack([np.cos(sess.heading), np.sin(sess.heading)])
        A += Z.T @ Z
        B += Z.T @ Y
    A += RIDGE * n_total * np.eye(d)
    return np.linalg.solve(A, B), mean, std


def angular_error(X: np.ndarray, heading: np.ndarray, dec) -> np.ndarray:
    """Degrees between the direction the decoder read and the true one."""
    W, mean, std = dec
    Z = np.hstack([(X - mean) / std, np.ones((len(X), 1))])
    pred = Z @ W
    n = np.linalg.norm(pred, axis=1)
    out = np.full(len(X), np.nan)
    ok = n > 1e-12
    cos = (pred[ok, 0] / n[ok]) * np.cos(heading[ok]) + \
          (pred[ok, 1] / n[ok]) * np.sin(heading[ok])
    out[ok] = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    return out


def chance_error(heading: np.ndarray, rng=None) -> float:
    """What the error would be if the decoder knew nothing.

    Measured, not assumed. The textbook answer for guessing uniformly is 90
    degrees, but the directions in a finite recording are not perfectly uniform,
    so the apparatus's own chance level is a few degrees off that. Comparing
    against the textbook number instead of the measured one is how an apparatus
    gets credited with skill it does not have.
    """
    rng = rng or np.random.default_rng(0)
    guess = rng.uniform(0, 2 * np.pi, len(heading))
    d = np.abs(np.angle(np.exp(1j * (guess - heading))))
    return float(np.degrees(d).mean())


# ==========================================================================
# WINDOWS
# ==========================================================================

def window_starts(n_frames: int, win: int = WINDOW_FRAMES,
                  step: int = STEP_FRAMES) -> np.ndarray:
    if n_frames < win:
        return np.empty(0, dtype=int)
    return np.arange(0, n_frames - win + 1, step)


def window_error(X, heading, starts, dec, win: int = WINDOW_FRAMES) -> np.ndarray:
    """Median angular error in each window, in degrees."""
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        e = angular_error(X[s:s + win], heading[s:s + win], dec)
        e = e[np.isfinite(e)]
        if len(e):
            out[i] = float(np.median(e))
    return out


def window_means(X, starts, win: int = WINDOW_FRAMES) -> np.ndarray:
    """Per-window, per-channel average. The only thing the monitor ever sees."""
    return det.window_features(X, starts, win)


# ==========================================================================
# THE MONITOR
# ==========================================================================

def fit_detector(name: str, healthy_windows: np.ndarray):
    if name not in DETECTORS:
        raise ValueError(f"unknown detector {name!r}; have {sorted(DETECTORS)}")
    return DETECTORS[name]().fit(healthy_windows)


def choose_threshold(healthy_scores: list[np.ndarray], healthy_hours: float,
                     budget: float = FALSE_ALARM_BUDGET_PER_HOUR) -> float:
    """Pick the WARN threshold: the lowest one that stays inside the budget.

    This is the monitor's ONE free parameter, and it is chosen on healthy
    sessions set aside for the purpose -- never on the sessions the false-alarm
    rate is then reported from. Choosing it on the same data it is scored on
    would mean reporting how well a number fits the data it was fitted to,
    which is not a measurement of anything.

    Lowest-that-fits, rather than highest, because a higher threshold buys
    quiet at the price of lead time, and lead time is what the monitor is for.
    """
    allowed = budget * healthy_hours
    best = float(harness.THRESHOLD_GRID[-1])
    for t in harness.THRESHOLD_GRID:
        n = sum(1 for s in healthy_scores if warn_index(s, float(t)) is not None)
        if n <= allowed:
            best = float(t)
            break
    return best


def warn_index(score: np.ndarray, threshold: float) -> int | None:
    """Index of the first window at WARN, or None. Uses the neural state machine."""
    states = harness.run_state_machine(np.asarray(score, dtype=float), threshold)
    return harness.first_index(states, 2)      # 2 == WARN


def fail_window(error_deg: np.ndarray, onset_window: int | None) -> int | None:
    """The first window where decoding has actually become unusable.

    "Unusable" is defined exactly as it is in the computational half: the
    session's own smoothed error rising more than 10 degrees above its
    pre-onset baseline. That threshold was fixed in `scripts/17_fault_injector.py`
    before any detector existed, and it is imported rather than restated so the
    two halves cannot drift apart.

    Each session is compared against its OWN baseline rather than a fixed
    number of degrees, because sessions differ in how well they decode to begin
    with, and a fixed cutoff would score the good ones as broken and the poor
    ones as fine.
    """
    if onset_window is None:
        return None
    return harness.crossing_window(np.asarray(error_deg, dtype=float),
                                   int(onset_window))


def window_end_seconds(index: int | None, starts: np.ndarray,
                       fps: int = FPS, win: int = WINDOW_FRAMES) -> float:
    """Seconds from the start of the session to the END of a given window."""
    if index is None or not len(starts):
        return float("nan")
    return float((starts[index] + win) / fps)


def detrend(score: np.ndarray, onset_window: int | None) -> np.ndarray:
    """Remove a trend fitted only on windows before the onset. Causal."""
    if onset_window is None:
        return np.asarray(score, dtype=float)
    return harness.causal_detrend(np.asarray(score, dtype=float), int(onset_window))


def onset_window_index(onset_frame: int | None, starts: np.ndarray) -> int | None:
    """The first window that lies ENTIRELY after the onset.

    A window is 30 seconds long, so several windows straddle the onset: part
    healthy, part faulty. Those are neither one thing nor the other. This
    returns the first window that contains no healthy data at all, which is the
    right place to start counting "after".
    """
    if onset_frame is None or not len(starts):
        return None
    after = np.flatnonzero(starts >= onset_frame)
    return int(after[0]) if len(after) else None


def warn_seconds(warn_window: int | None, starts: np.ndarray,
                 fps: int = FPS, win: int = WINDOW_FRAMES) -> float:
    """When the warning could first have been issued, in seconds.

    **This is the END of the first WARN window, not its start**, and the choice
    matters. A window covers 30 seconds of recording, and its risk score cannot
    be computed until the last of those 30 seconds has happened. Timestamping
    the warning at the window's start would credit the monitor with knowing
    something up to 30 seconds before the data existed, which would inflate
    every lead time by up to half a minute.

    There is no version of this that flatters the monitor honestly, and 30
    seconds is a large fraction of the lead times at stake, so it is stated
    here rather than buried in an analysis script.
    """
    return window_end_seconds(warn_window, starts, fps, win)


# ==========================================================================
# SELF-TEST
# ==========================================================================

def _fake_session(n_frames=12000, n_ch=384, depth=0.02, onset=None,
                  severity=0.0, seed=0):
    """A recording with a known answer, built in memory.

    Not a substitute for real data. It exists to check that the pipeline is
    wired up correctly -- that the decoder learns something, that degrading the
    signal raises the error and the risk. It cannot tell you anything about the
    apparatus, because there is no apparatus in it.
    """
    rng = np.random.default_rng(seed)
    pref = rng.uniform(0, 2 * np.pi, n_ch)
    heading = np.repeat(rng.uniform(0, 2 * np.pi, n_frames // 100 + 1), 100)[:n_frames]
    X = 128.0 + depth * 128.0 * np.cos(heading[:, None] - pref[None, :])
    X += rng.normal(0, 1.0, X.shape)
    if onset is not None and severity:
        g = np.clip(1.0 + severity * rng.normal(0, 0.5, n_ch), 0.05, None)
        X[onset:] *= g
    return X, heading


def selftest() -> int:
    print("physical-phase self-test — no camera or recordings needed\n")
    ok = True

    def fail(msg: str):
        nonlocal ok
        print(f"    FAIL — {msg}")
        ok = False

    N = 12000                      # 45 windows, enough to have some after a fault
    X, h = _fake_session(N)
    half = N // 2
    dec = fit_decoder(X[:half], h[:half])
    err = float(np.median(angular_error(X[half:], h[half:], dec)))
    ch = chance_error(h)
    print(f"  decoder error {err:.1f} deg vs chance {ch:.1f} deg")
    # The fake data is deliberately easy, so a large margin here says the wiring
    # works, not that the apparatus is good. The real difficulty check is P-1.
    if not np.isfinite(err) or err >= ch - 5:
        fail("the decoder learned nothing on data where it should have")

    starts = window_starts(len(X))
    F = window_means(X, starts)
    print(f"  {len(starts)} windows x {F.shape[1]} channels")
    if F.shape != (len(starts), X.shape[1]):
        fail("windowing produced the wrong shape")
    if not np.isfinite(F).all():
        fail("windowing produced non-numbers")

    d = fit_detector("decoder_guard", F[:20])
    s_healthy = d.score(F)

    onset = half
    # Same seed as the healthy run, so the channels have the same tuning and
    # the same noise: the ONLY difference is the fault. With a different seed
    # the detector would flag the new run as anomalous from its first window,
    # which is a property of the fake data rather than of the monitor.
    Xb, hb = _fake_session(N, onset=onset, severity=1.0, seed=0)
    sb = window_starts(len(Xb))
    s_bad = d.score(window_means(Xb, sb))
    ow = onset_window_index(onset, sb)
    # Only windows lying entirely after the onset are "after the fault"; a
    # window straddling it is part healthy and would understate the effect.
    after = s_bad[ow + WINDOW_FRAMES // STEP_FRAMES:]
    if not len(after):
        fail("the fake session is too short to have any post-fault windows")
    m_healthy, m_after = float(np.median(s_healthy)), float(np.median(after))
    print(f"  risk on healthy {m_healthy:.2f}, after a severe fault {m_after:.2f}")
    if not np.isfinite(m_healthy) or not np.isfinite(m_after):
        fail("the risk score came out as a non-number")
    elif m_after <= m_healthy:
        fail("a severe fault did not raise the risk")

    t = choose_threshold([s_healthy], healthy_hours=1.0)
    w_bad = warn_index(s_bad, t)
    w_ok = warn_index(s_healthy, t)
    print(f"  threshold {t:.2f}; first WARN on the faulty run at window {w_bad}, "
          f"on the healthy run {w_ok}")
    if w_bad is None:
        fail("the monitor never warned on a severely faulty run")
    elif sb[w_bad] + WINDOW_FRAMES <= onset:
        # Windows straddling the onset are already part-faulty, so warning on
        # one of those is legitimate. Warning on a window that ENDS before the
        # fault means information travelled backwards in time.
        fail(f"the monitor warned on a window ending at frame "
             f"{sb[w_bad] + WINDOW_FRAMES}, entirely before the fault at "
             f"{onset} — that is not early detection, it is a bug")
    else:
        print(f"  warning timestamped at "
              f"{warn_seconds(w_bad, sb):.0f} s, fault at {onset / FPS:.0f} s")

    print("\n" + ("PASS — the pipeline is wired up correctly"
                  if ok else "FAIL — see above"))
    return 0 if ok else 1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="check the pipeline works; needs no camera or recordings")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    print(__doc__)
    print("This file is imported by the analysis scripts, not run directly.")
    print("Run  python3 physical/code/monitor.py --selftest  to check it works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
