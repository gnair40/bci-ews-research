#!/usr/bin/env python3
"""
Score the frozen combination study.

Criterion, fixed at `research/COMBINATION_STUDY_FROZEN.json` (commit 7234964)
before any arm was computed:

    an arm must raise session-level AUC by >= 0.05 over decoder_guard v1
    ON BOTH PARTICIPANTS IN THE SAME DIRECTION

and, written down in advance because it is the exception that would be tempting:

    a combined arm landing at +0.04 is NOT grounds for relaxing the threshold.

Intervals bootstrap over episodes, not windows (lag-1 r = 0.995).

Usage: python3 scripts/37_combination_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"
DELTA = 0.05


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


def pools(rows, crossed, crossing):
    E, H = [], []
    for _, r in rows.iterrows():
        y = np.fromstring(r.scores, sep=",")
        ow = int(r.onset_w)
        if not crossed.get(r.episode_id, False):
            H.append(float(np.median(y)))
        else:
            cw = crossing.get(r.episode_id, -1)
            if cw > ow and len(y) >= cw:
                E.append(float(np.median(y[ow:cw])))
    return E, H


def main() -> int:
    frozen = json.loads((REPO / "research" / "COMBINATION_STUDY_FROZEN.json").read_text())
    results = {}
    for P, sfx, base in (("T11", "", "_local"), ("T5", "_T5", "_T5_local")):
        f = OUT / f"combo_scores{sfx}.csv"
        b_path = OUT / f"episode_scores{base}.csv"
        if not f.exists() or not b_path.exists():
            print(f"  {P}: missing inputs, skipping")
            continue
        b = pd.read_csv(b_path); b = b[b.detector == "decoder_guard"]
        crossed = dict(zip(b.episode_id, b.crossed))
        crossing = dict(zip(b.episode_id, b.crossing_w))

        gE, gH = [], []
        for _, r in b.iterrows():
            y = np.fromstring(r.scores, sep=",")
            ow, cw = int(r.onset_w), int(r.crossing_w)
            if not r.crossed:
                gH.append(float(np.median(y)))
            elif cw > ow and len(y) >= cw:
                gE.append(float(np.median(y[ow:cw])))
        res = {"decoder_guard (incumbent)": (auc(gE, gH), boot(gE, gH))}

        df = pd.read_csv(f)
        for arm, rows in df.groupby("arm"):
            E, H = pools(rows, crossed, crossing)
            res[arm] = (auc(E, H), boot(E, H)) if E and H else (np.nan, (np.nan, np.nan))
        results[P] = res

    if len(results) < 2:
        print("need both participants before the criterion can be applied")
        return 1

    L = ["# Combination study — result\n",
         f"**Frozen at** `{frozen['git_commit_at_freeze'][:12]}` before any arm was "
         f"computed. Preregistration SHA-256 `{frozen['preregistration_sha256'][:16]}…`\n",
         "**Faithfulness check** (the study was conditional on it): the generalised "
         "decomposition reproduces `decoder_guard` v1 on the original features at "
         "Spearman ρ = 1.0000 over 6,637 windows. Passed.\n",
         "**Criterion:** ≥ +0.05 session-level AUC over `decoder_guard` v1 on "
         "**both** participants in the same direction. Recorded in advance: *a "
         "combined arm landing at +0.04 is not grounds for relaxing this.*\n",
         "## Session-level AUC in the early-warning window\n",
         "| Arm | " + " | ".join(f"{p} AUC | {p} 95% CI | Δ" for p in results) + " |",
         "|---|" + "---|" * (3 * len(results))]
    A = L.append

    names = ["decoder_guard (incumbent)"] + sorted(
        n for n in next(iter(results.values())) if n.startswith("C"))
    print(f"{'arm':<26}" + "".join(f"{p+' AUC':>11}{'delta':>9}" for p in results))
    verdict = {}
    for n in names:
        cells, ds = [], []
        line = f"{n:<26}"
        for p, r in results.items():
            a, (lo, hi) = r.get(n, (np.nan, (np.nan, np.nan)))
            d = a - r["decoder_guard (incumbent)"][0]
            ds.append(d)
            cells += [f"{a:.3f}", f"{lo:.3f}–{hi:.3f}", f"{d:+.3f}"]
            line += f"{a:>11.3f}{d:>+9.3f}"
        A(f"| `{n}` | " + " | ".join(cells) + " |")
        print(line)
        if n.startswith("C"):
            verdict[n] = (all(d >= DELTA for d in ds), ds)
    A("")

    A("## Verdict against the frozen criterion\n")
    A("| Arm | Cleared +0.05 on both? | |")
    A("|---|---|---|")
    print(f"\n{'arm':<26}{'both?':>10}")
    passed = []
    for n, (ok, ds) in verdict.items():
        helped = [p for p, d in zip(results, ds) if d >= DELTA]
        note = ("**PASSES**" if ok else
                f"null — helped {', '.join(helped)} only" if helped else
                "no improvement on either")
        if ok:
            passed.append(n)
        A(f"| `{n}` | {'yes' if ok else 'no'} | {note} |")
        print(f"{n:<26}{('YES' if ok else 'no'):>10}   {note.replace('**','')}")
    A("")

    if not passed:
        A("### Nothing clears the bar\n")
        A("Better features and a better decomposition were the two ingredients "
          "this project's own results identified, and combining them does not "
          "close the gap either. That closes the last direction the results "
          "themselves suggested.\n")
        A(f"The session-level target remains ≈ 0.93. {frozen['what_this_cannot_settle']}\n")
    else:
        A(f"### {', '.join(passed)} clears the bar\n")
        A("Encouraging, and still n = 2. The gap to the session-level target of "
          "≈ 0.93 is what decides whether it matters in practice.\n")

    (REPORTS / "COMBINATION_STUDY_RESULT.md").write_text("\n".join(L))
    print(f"\nwrote {REPORTS/'COMBINATION_STUDY_RESULT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
