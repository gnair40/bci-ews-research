#!/usr/bin/env python3
"""
health_check.py — is the campaign still sound? Run it every recording day.

=============================================================================
WHY THIS EXISTS
=============================================================================
A campaign runs for days, mostly while you are asleep. Almost everything that
can go wrong with it produces **recordings that look fine**: the screen sleeps
and every session after that is a dark frame; the room warms and every channel
drifts; the disk fills and sessions truncate; a plan file gets touched and the
onset no longer matches its checksum.

None of those announce themselves. This script looks for all of them at once,
and takes about a second.

**Run it every recording day, before you start.** Finding out on day four that
day two was junk costs two days. Finding out on day two costs ten minutes.

=============================================================================
WHAT IT CHECKS
=============================================================================
    checksums     Every drawn plan still matches the SHA-256 recorded in the
                  manifest when it was drawn. **This is the integrity of the
                  whole phase's central claim** — if a plan no longer matches,
                  its onset cannot be trusted and neither can any lead time
                  computed from it.

    completeness  Every drawn plan has a recording, every recording has a plan,
                  every undesigned session has a noted onset, and every folder
                  has all four files it should.

    recording     Frame rate, dropped frames, and truncated sessions.

    drift         Whether the apparatus itself changed during the campaign:
                  overall brightness, channel-to-channel spread, and dead or
                  clipped channels, compared against the first sessions.

    space         Disk headroom, and how many more sessions will fit.

    exclusions    Which sessions have been excluded, and whether each carries
                  a reason.

=============================================================================
HOW TO RUN IT
=============================================================================
    python3 physical/code/health_check.py

    python3 physical/code/health_check.py --raw physical/data/dryrun/raw

Exit code 0 means everything passed. Anything else means read the output.

=============================================================================
WHAT IT DOES NOT DO
=============================================================================
It does not look at any result. It cannot tell you whether the monitor is
working, and it is not allowed to: a check you run daily that could see results
is a check that would slowly teach you to stop the campaign when the numbers
look good. It only asks whether the recordings are what they claim to be.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import monitor as M

DATA = M.DATA
BYTES_PER_SESSION = 25_000_000      # ~25 MB at 15000 frames x 384 channels


def _p(ok: bool, msg: str) -> bool:
    print(f"  {'ok  ' if ok else 'FAIL'}  {msg}")
    return ok


def check_checksums(root: Path) -> bool:
    """Every drawn plan still matches the digest recorded when it was drawn."""
    print("\nCHECKSUMS — the integrity of the phase's central claim")
    man = root.parent / "onsets" / "MANIFEST.csv"
    if not man.exists():
        return _p(False, f"no manifest at {man} — nothing has been drawn yet")

    rows = list(csv.DictReader(man.open()))
    bad, missing = [], []
    for r in rows:
        f = man.parent / r["file"]
        if not f.exists():
            missing.append(r["file"])
            continue
        if hashlib.sha256(f.read_bytes()).hexdigest() != r["sha256"]:
            bad.append(r["file"])

    ok = _p(not bad and not missing,
            f"{len(rows) - len(bad) - len(missing)} of {len(rows)} plans match "
            f"their recorded checksum")
    for f in missing:
        print(f"        MISSING  {f}")
    for f in bad:
        print(f"        CHANGED  {f}")
    if bad:
        print()
        print("  A plan that no longer matches its checksum cannot be used.")
        print("  The onset in it is no longer provably the one drawn before the")
        print("  recording existed, which is the entire basis of the lead-time")
        print("  measurement. Do NOT 'fix' the manifest. Exclude the session")
        print("  (see EXCLUSIONS.csv) and write what happened in the log.")
    return ok


def check_completeness(root: Path) -> bool:
    print("\nCOMPLETENESS — plans, recordings, and the files in each folder")
    onsets = root.parent / "onsets"
    planned = {p.stem for p in onsets.glob("s*_b*.json")} if onsets.exists() else set()
    recorded = {f.name for f in root.glob("s*_b*") if (f / "capture.npy").exists()}

    ok = True
    no_rec = sorted(planned - recorded)
    if no_rec:
        print(f"  note  {len(no_rec)} drawn but not yet recorded "
              f"(that is normal mid-campaign): {', '.join(no_rec[:6])}"
              + (" ..." if len(no_rec) > 6 else ""))

    orphan_needed = []
    for name in sorted(recorded - planned):
        f = root / name
        j = f / "session.json"
        kind = json.loads(j.read_text()).get("kind", "") if j.exists() else ""
        if kind == "calibration":
            continue
        if kind == "undesigned":
            if not (f / "observed_onset.json").exists():
                orphan_needed.append(name)
            continue
        orphan_needed.append(name)
    ok &= _p(not orphan_needed,
             f"{len(recorded)} recordings, every one accounted for"
             if not orphan_needed else
             f"{len(orphan_needed)} recording(s) with no plan and no noted onset")
    for n in orphan_needed:
        print(f"        {n} — cannot be analysed until an onset exists")

    incomplete = []
    for f in sorted(root.glob("s*_b*")):
        need = ["capture.npy", "capture_t.npy", "stim.csv", "session.json"]
        miss = [n for n in need if not (f / n).exists()]
        if miss and (f / "capture.npy").exists():
            incomplete.append((f.name, miss))
    ok &= _p(not incomplete, f"every recording folder has its four files"
             if not incomplete else f"{len(incomplete)} folder(s) incomplete")
    for n, miss in incomplete:
        print(f"        {n} missing {', '.join(miss)}")
    return ok


def check_recording(root: Path) -> bool:
    print("\nRECORDING — frame rate, dropped frames, truncation")
    metas, short = [], []
    for f in sorted(root.glob("s*_b*")):
        m = f / "capture_meta.json"
        if m.exists():
            d = json.loads(m.read_text())
            d["_name"] = f.name
            metas.append(d)
            want, got = d.get("frames_requested"), d.get("frames_recorded")
            if want and got and got < 0.98 * want:
                short.append((f.name, got, want))
    if not metas:
        return _p(True, "no capture metadata yet (nothing recorded)")

    late = [m for m in metas if m.get("long_gap_fraction", 0) > 0.01]
    ok = _p(not late, f"{len(metas)} recordings, none dropped more than 1% of frames"
            if not late else f"{len(late)} recording(s) dropped over 1% of frames")
    for m in late[:8]:
        print(f"        {m['_name']}  {m['long_gap_fraction']:.1%} late")

    ok &= _p(not short, "no truncated recordings"
             if not short else f"{len(short)} recording(s) ended early")
    for n, got, want in short[:8]:
        print(f"        {n}  {got} of {want} frames — power cut, disk full, or "
              f"interrupted")

    fps = [m["fps_measured"] for m in metas if m.get("fps_measured")]
    if fps:
        print(f"  note  frame rate {np.median(fps):.2f} fps "
              f"(range {min(fps):.2f}–{max(fps):.2f})")
    return ok


def check_drift(root: Path, n_ref: int = 5) -> bool:
    """Did the apparatus itself change during the campaign?"""
    print("\nAPPARATUS DRIFT — did the box change while you were not looking?")
    # Fault-free recordings ONLY. The first version of this check compared the
    # earliest five recordings against the latest five, whatever they were, and
    # fired on every campaign that happens to end with degraded sessions -- it
    # was measuring the faults, which are supposed to change the signal. A check
    # that cries wolf on correct behaviour is a check people switch off.
    folders = []
    for f in M.find_sessions(root):
        j = f / "session.json"
        if not j.exists():
            continue
        d = json.loads(j.read_text())
        plan = (f.parent.parent / "onsets" / f"{f.name}.json")
        healthy = d.get("healthy")
        if healthy is None and plan.exists():
            healthy = json.loads(plan.read_text()).get("healthy")
        if d.get("kind") == "calibration" or healthy:
            folders.append(f)
    if len(folders) < n_ref + 2:
        return _p(True, f"only {len(folders)} fault-free recordings — "
                        f"too few to compare yet")

    def stats(f):
        X = np.load(f / "capture.npy").astype(np.float64)
        sd = X.std(axis=0)
        return {"mean": float(X.mean()), "spread": float(np.median(sd)),
                "dead": int((sd < 1e-6).sum()),
                "clipped": int((X.max(axis=0) > 254).sum()),
                "n": X.shape[1]}

    ref = [stats(f) for f in folders[:n_ref]]
    now = [stats(f) for f in folders[-n_ref:]]
    print(f"  note  comparing the first {n_ref} against the last {n_ref} of "
          f"{len(folders)} fault-free recordings")
    rm, nm = np.mean([r["mean"] for r in ref]), np.mean([r["mean"] for r in now])
    rs, ns = np.mean([r["spread"] for r in ref]), np.mean([r["spread"] for r in now])
    dead, clip, nch = now[-1]["dead"], now[-1]["clipped"], now[-1]["n"]

    shift = abs(nm - rm) / max(rm, 1e-9)
    ok = _p(shift < 0.05,
            f"overall brightness {rm:.1f} -> {nm:.1f} ({shift:+.1%})")
    if shift >= 0.05:
        print("        The screen or the light path changed mid-campaign.")
        print("        Sessions before and after are not comparable. Find out")
        print("        what changed, write it in the log with the date, and say")
        print("        so in the write-up — this cannot be detected afterwards.")

    sshift = abs(ns - rs) / max(rs, 1e-9)
    ok &= _p(sshift < 0.25,
             f"channel spread {rs:.2f} -> {ns:.2f} ({sshift:+.1%})")
    ok &= _p(dead <= 0.05 * nch, f"{dead} of {nch} channels never change")
    ok &= _p(clip <= 0.01 * nch, f"{clip} of {nch} channels clipped at full scale")
    return ok


def check_space(root: Path) -> bool:
    print("\nDISK — will the rest of the campaign fit?")
    du = shutil.disk_usage(root if root.exists() else root.parent)
    free_gb = du.free / 1e9
    fits = int(du.free / BYTES_PER_SESSION)
    ok = _p(fits > 20, f"{free_gb:.1f} GB free — room for about {fits} more "
                       f"five-minute sessions")
    if fits <= 20:
        print("        Move completed recordings to the USB drive before")
        print("        starting another campaign. A disk that fills overnight")
        print("        truncates sessions rather than stopping cleanly.")
    return ok


def check_exclusions(root: Path) -> bool:
    print("\nEXCLUSIONS — sessions set aside, and whether each says why")
    f = root.parent / "EXCLUSIONS.csv"
    if not f.exists():
        return _p(True, "no sessions excluded")
    rows = list(csv.DictReader(f.open()))
    bad = [r for r in rows if not (r.get("reason") or "").strip()]
    ok = _p(not bad, f"{len(rows)} excluded, every one with a reason"
            if not bad else f"{len(bad)} exclusion(s) with no reason given")
    for r in rows:
        print(f"        {r.get('folder','?'):<12} {r.get('reason','(none)')}")
    if bad:
        print()
        print("  An exclusion without a recorded reason is indistinguishable")
        print("  from dropping a session because of how it turned out.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()
    root = Path(a.raw) if a.raw else DATA / "raw"
    if not root.exists():
        print(f"No recordings folder at {root}.")
        return 1

    print("=" * 70)
    print(f"campaign health — {root}")
    print("=" * 70)
    results = {
        "checksums": check_checksums(root),
        "completeness": check_completeness(root),
        "recording": check_recording(root),
        "drift": check_drift(root),
        "space": check_space(root),
        "exclusions": check_exclusions(root),
    }
    print("\n" + "=" * 70)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 70)
    if all(results.values()):
        print("Campaign is sound. Carry on.")
        return 0
    print("Fix the failures above before recording more. Every one of them")
    print("produces recordings that look fine and analyse into nonsense.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
