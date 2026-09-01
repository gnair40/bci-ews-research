#!/usr/bin/env python3
"""
Score the frozen feature study and report all four families, whatever they did.

The criterion, fixed at `research/FEATURE_STUDY_FROZEN.json` before any feature
was computed:

    a family must raise session-level AUC by >= 0.05 over decoder_guard v1
    ON BOTH PARTICIPANTS IN THE SAME DIRECTION

A family that helps one participant and not the other is a **null result**, not a
partial success. That rule was written down in advance precisely because it is
the one that would be tempting to soften afterwards.

Confidence intervals bootstrap over EPISODES. Phase 3 measured lag-1
autocorrelation of 0.995 within a session, so resampling windows would produce
intervals roughly sqrt(55) too narrow and would make everything look significant.

Usage: python3 scripts/34_feature_report.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"
DELTA_REQUIRED = 0.05


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def auc(E, H):
    E, H = np.asarray(E, float), np.asarray(H, float)
    if len(E) < 5 or len(H) < 5:
        return float("nan")
    u, _ = stats.mannwhitneyu(E, H, alternative="two-sided")
    return float(u / (len(E) * len(H)))


def boot(E, H, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    E, H = np.asarray(E, float), np.asarray(H, float)
    v = [auc(rng.choice(E, len(E)), rng.choice(H, len(H))) for _ in range(n)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def session_pools(df, key, col, crossed_map, crossing_map):
    """Median score per episode, split by whether the episode crossed."""
    E, H = [], []
    for _, r in df[df[col] == key].iterrows():
        y = np.fromstring(r.scores, sep=",")
        ow = int(r.onset_w)
        eid = r.episode_id
        if not crossed_map.get(eid, False):
            H.append(float(np.median(y)))
        else:
            cw = crossing_map.get(eid, -1)
            if cw > ow and len(y) >= cw:
                E.append(float(np.median(y[ow:cw])))
    return E, H


def main() -> int:
    frozen = json.loads((REPO / "research" / "FEATURE_STUDY_FROZEN.json").read_text())
    L = ["# Feature study — result\n",
         f"**Frozen at** `{frozen['git_commit_at_freeze'][:12]}` "
         f"({frozen['frozen_utc']}), before any feature was computed. "
         f"Preregistration SHA-256 `{frozen['preregistration_sha256'][:16]}…`\n",
         "**Criterion, fixed in advance:** a family must raise session-level AUC "
         f"by ≥ {DELTA_REQUIRED:.2f} over `decoder_guard` v1 **on both "
         "participants in the same direction**. A family helping only one is a "
         "null result, not a partial success.\n",
         "> `F0_control_mean` is **not a fifth family**. It is the *current* "
         "feature — per-channel mean activity — pushed through the identical "
         "one-class scorer every family uses. Without it, a family beating "
         "`decoder_guard` could be winning on the shared scorer rather than on "
         "its features.\n"]
    A = L.append

    results = {}
    for P, sfx in (("T11", ""), ("T5", "_T5")):
        path = OUT / f"feature_scores{sfx}.csv"
        scored = OUT / f"episode_scores{'_local' if P == 'T11' else '_T5_local'}.csv"
        if not path.exists() or not scored.exists():
            print(f"  {P}: missing inputs, skipping")
            continue
        base = pd.read_csv(scored)
        b = base[base.detector == "decoder_guard"]
        crossed_map = dict(zip(b.episode_id, b.crossed))
        crossing_map = dict(zip(b.episode_id, b.crossing_w))

        # decoder_guard v1, the incumbent, from the benchmark's own scores
        gE, gH = [], []
        for _, r in b.iterrows():
            y = np.fromstring(r.scores, sep=",")
            ow, cw = int(r.onset_w), int(r.crossing_w)
            if not r.crossed:
                gH.append(float(np.median(y)))
            elif cw > ow and len(y) >= cw:
                gE.append(float(np.median(y[ow:cw])))
        incumbent = auc(gE, gH)

        df = pd.read_csv(path)
        res = {"decoder_guard (incumbent)": (incumbent, boot(gE, gH))}
        for name in sorted(df.extractor.unique()):
            E, H = session_pools(df, name, "extractor", crossed_map, crossing_map)
            res[name] = (auc(E, H), boot(E, H)) if E and H else (float("nan"), (np.nan, np.nan))
        results[P] = res

    if not results:
        print("no results yet"); return 1

    names = sorted({n for r in results.values() for n in r})
    names.sort(key=lambda n: (not n.startswith("decoder_guard"), not n.startswith("F0"), n))

    A("## Session-level AUC in the early-warning window\n")
    A("| | " + " | ".join(f"{p} AUC | {p} 95% CI | Δ vs v1" for p in results) + " |")
    A("|---|" + "---|" * (3 * len(results)))
    print(f"{'extractor':<28}" + "".join(f"{p+' AUC':>12}{'delta':>9}" for p in results))
    verdicts = {}
    for n in names:
        cells, deltas = [], []
        line = f"{n:<28}"
        for p, r in results.items():
            if n not in r:
                cells += ["—", "—", "—"]; line += f"{'—':>12}{'—':>9}"; continue
            a, (lo, hi) = r[n]
            d = a - r["decoder_guard (incumbent)"][0]
            deltas.append(d)
            cells += [f"{a:.3f}", f"{lo:.3f}–{hi:.3f}", f"{d:+.3f}"]
            line += f"{a:>12.3f}{d:>+9.3f}"
        A(f"| `{n}` | " + " | ".join(cells) + " |")
        print(line)
        if n.startswith("F") and not n.startswith("F0") and len(deltas) == len(results):
            verdicts[n] = all(d >= DELTA_REQUIRED for d in deltas)
    A("")

    A("## Verdict against the frozen criterion\n")
    A("| Family | Cleared +0.05 on **both**? | |")
    A("|---|---|---|")
    print(f"\n{'family':<28}{'both participants?':>22}")
    any_pass = False
    for n, ok in verdicts.items():
        ds = [results[p][n][0] - results[p]["decoder_guard (incumbent)"][0] for p in results]
        helped = [p for p, d in zip(results, ds) if d >= DELTA_REQUIRED]
        if ok:
            note = "**PASSES**"; any_pass = True
        elif helped:
            note = f"null result — helped {', '.join(helped)} only"
        else:
            note = "no improvement on either"
        A(f"| `{n}` | {'yes' if ok else 'no'} | {note} |")
        print(f"{n:<28}{('YES' if ok else 'no'):>22}   {note.replace('**','')}")
    A("")

    if not any_pass:
        A("### No family clears the bar\n")
        A("That converts *\"a better feature is the remaining direction\"* into "
          "*\"the four obvious better features were specified in advance, tried, "
          "and do not work\"* — a stronger and more useful statement than the "
          "open question it replaces.\n")
        A("It does **not** show that no feature could work. It shows that the "
          "four families a careful reading of the problem suggested do not, on "
          "these two datasets.\n")

    A("## What this cannot settle\n")
    A(f"{frozen['what_this_cannot_settle']}\n")

    (REPORTS / "FEATURE_STUDY_RESULT.md").write_text("\n".join(L))
    print(f"\nwrote {REPORTS/'FEATURE_STUDY_RESULT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
