#!/usr/bin/env python3
"""
Does the test suite actually catch anything?

WHY THIS EXISTS
---------------
This project has a standing rule, learned the hard way four times: a checking
tool is not trusted until it has been shown to catch a defect known to exist.
The reproducibility audit first reported 27 problems of which 1 was real. The
statistical hygiene linter missed the very file it was written for. A test suite
that passes on its first run has demonstrated nothing at all.

So this reintroduces each historical bug into the real source, one at a time,
runs the test class that is supposed to notice, and restores the file. A test
that does not fail against its own motivating defect is not a test.

Every mutant below is a bug this project actually had, except where marked.

    python3 tools/mutation_check.py

Exit code 0 if every live mutant was caught, 1 otherwise.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def gain_drift_unconserved(s: str) -> str:
    return re.sub(
        r'(def apply_gain_drift.*?\n)(.*?)(\n\ndef )',
        lambda m: m.group(1)
        + '    """mutant: per-channel gain with no mean conservation"""\n'
          '    g = 1.0 + ep.severity * f[:, None] * _rng(ep).normal(0, 1, (1, X.shape[1]))\n'
          '    return X * np.abs(g)\n' + m.group(3),
        s, flags=re.S)


#  description, file, mutation, test class, expected-inert
MUTANTS = [
    ("window means off by one window, the classic cumulative-sum slip",
     "scripts/71_drift_sweep_design.py",
     lambda s: s.replace(
         "    return (c[:, starts + WINDOW_BINS] - c[:, starts]) / WINDOW_BINS",
         "    return (c[:, starts + WINDOW_BINS - 1] - c[:, starts]) / WINDOW_BINS"),
     "WindowMeansByCumsum", False),

    ("OU paths started at zero instead of in equilibrium, so every simulated "
     "block carries a warm-up transient",
     "scripts/71_drift_sweep_design.py",
     lambda s: s.replace(
         "    zi = (rng.normal(size=(reps, 1)) * a)",
         "    zi = np.zeros((reps, 1))"),
     "OrnsteinUhlenbeck", False),

    ("the tau inversion clamping to the ends of the curve instead of refusing, "
     "which is what would have hidden the NaN that exposed C18's ceiling",
     "scripts/71_drift_sweep_design.py",
     lambda s: s.replace(
         "    if not np.isfinite(target) or target < mono[0] or target > mono[-1]:\n"
         "        return float(\"nan\")",
         "    if not np.isfinite(target):\n"
         "        return float(\"nan\")\n"
         "    target = min(max(target, mono[0]), mono[-1])"),
     "InversionRefusesOffCurve", False),

    ("GAIN_DRIFT not mean-conserving (the +116% and +20.8% bugs)",
     "scripts/17_fault_injector.py", gain_drift_unconserved,
     "GainDriftConserved", False),

    ("CHANNEL_DROPOUT drawing independent channel sets per severity "
     "(what made the ladder run backwards)",
     "scripts/17_fault_injector.py",
     lambda s: s.replace(
         "def _rng(ep: Episode) -> np.random.Generator:\n"
         "    return np.random.default_rng(ep.seed)",
         "def _rng(ep: Episode) -> np.random.Generator:\n"
         "    return np.random.default_rng(ep.seed + int(ep.severity * 1000))"),
     "DropoutNested", False),

    ("onset arithmetic off by 5 bins, so the ramp starts before its onset",
     "scripts/17_fault_injector.py",
     lambda s: s.replace(
         "    t = np.arange(n_bins, dtype=np.float64) - onset_bin",
         "    t = np.arange(n_bins, dtype=np.float64) - onset_bin + 5"),
     "PreOnsetClean", False),

    ("widened `live` window: INERT since 13 Sep 2026, when the exp branch got "
     "the clip the linear branch already had. Kept as a regression check -- if "
     "this starts being caught, a clip was removed.",
     "scripts/17_fault_injector.py",
     lambda s: s.replace("    live = t >= 0", "    live = t >= -3"),
     "PreOnsetClean", True),

    ("an injector mutating its input array in place",
     "scripts/17_fault_injector.py",
     lambda s: s.replace(
         "    return X * (1.0 - ep.severity * f)[:, None]",
         "    X *= (1.0 - ep.severity * f)[:, None]\n    return X"),
     "PreOnsetClean", False),

    ("lag1 returning 0.0 instead of nan on a flat series",
     "scripts/66_window_spacing.py",
     lambda s: s.replace(
         "    if a.std() < 1e-12 or b.std() < 1e-12:\n        return np.nan",
         "    if a.std() < 1e-12 or b.std() < 1e-12:\n        return 0.0"),
     "Autocorrelation", False),

    ("n_eff inverted to (1+r)/(1-r)",
     "scripts/66_window_spacing.py",
     lambda s: s.replace("return n * (1 - r) / (1 + r)",
                         "return n * (1 + r) / (1 - r)"),
     "EffectiveSampleSize", False),

    ("overlap_fraction not clamped at zero",
     "scripts/66_window_spacing.py",
     lambda s: s.replace("shared = max(0, WINDOW_BINS - k * STEP_BINS)",
                         "shared = WINDOW_BINS - k * STEP_BINS"),
     "WindowOverlap", False),

    ("intended_direction not masking cursor-on-target bins",
     "scripts/18_reference_decoder.py",
     lambda s: s.replace("ok = np.isfinite(dist) & (dist > MIN_TARGET_DIST)",
                         "ok = np.isfinite(dist) & (dist >= 0.0)"),
     "IntendedDirection", False),

    ("loader using 0-based MATLAB indices (the off-by-one trap)",
     "scripts/03_load_dataset.py",
     lambda s: s.replace("    starts_py = starts_m - index_base",
                         "    starts_py = starts_m"),
     "MatlabIndexing", False),

    ("loader leaving the stop index inclusive instead of exclusive",
     "scripts/03_load_dataset.py",
     lambda s: s.replace("    stops_py = stops_m - index_base + 1",
                         "    stops_py = stops_m - index_base"),
     "MatlabIndexing", False),

    ("a documented rig command with the subcommand after the option -- the real "
     "bug the dry run found on 14 Sep 2026",
     "research/RIG_PROCEDURE.md",
     lambda s: s.replace(
         "python3 scripts/17_fault_injector.py plan --participant RIG "
         "--raw-root data/raw_rig",
         "python3 scripts/17_fault_injector.py --participant RIG plan", 1),
     "__command_check__", False),

    ("angular error dropping the arccos, so it reports cosine not degrees",
     "scripts/18_reference_decoder.py",
     lambda s: s.replace("np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))",
                         "np.clip(cos, -1.0, 1.0)"),
     "IntendedDirection", False),
]


def main() -> int:
    print(f"{'mutant':<64} {'test class':<22} result")
    print("-" * 104)
    missed, unexpected = 0, 0
    for desc, relpath, mutate, testclass, inert in MUTANTS:
        target = REPO / relpath
        backup = target.read_text()
        try:
            mutated = mutate(backup)
            if mutated == backup:
                print(f"{desc[:62]:<64} {testclass:<22} MUTATION DID NOT APPLY")
                missed += 1
                continue
            target.write_text(mutated)
            cmd = ([sys.executable, "scripts/69_command_check.py"]
                   if testclass == "__command_check__" else
                   [sys.executable, "-m", "unittest",
                    f"tests.test_core_numerics.{testclass}"])
            r = subprocess.run(cmd, cwd=REPO, capture_output=True,
                               text=True, timeout=900)
            caught = r.returncode != 0
        finally:
            target.write_text(backup)

        if inert:
            ok = not caught
            print(f"{desc[:62]:<64} {testclass:<22} "
                  f"{'inert, as expected' if ok else 'CAUGHT -- a clip was removed'}")
            if not ok:
                unexpected += 1
        else:
            print(f"{desc[:62]:<64} {testclass:<22} "
                  f"{'caught' if caught else '*** MISSED ***'}")
            if not caught:
                missed += 1

    print("-" * 104)
    if missed or unexpected:
        print(f"FAIL — {missed} live mutant(s) not caught, "
              f"{unexpected} inert mutant(s) unexpectedly caught")
        return 1
    live = sum(1 for m in MUTANTS if not m[4])
    print(f"PASS — all {live} live mutants caught; "
          f"{len(MUTANTS) - live} inert mutant(s) stayed inert")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
