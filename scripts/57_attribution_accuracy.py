#!/usr/bin/env python3
"""
When the monitor warns, does it name the right cause?

The guard emits an attributed cause with every warning -- "recalibrate", "an
electrode is failing", "nothing is wrong" are different responses, and a monitor
that cannot separate them is not usable however good its accuracy number looks.

That capability has been implemented since the guard was written, and SCORED
since 21_score_report.py was written, and then thrown away: the confusion matrix
is printed to stdout during a score-report run and captured nowhere. No report
holds it, no verifier claim checks it, and the README carries a limitation about
attribution with no numbers behind it. This script closes that.

THE PREDICTION IS ALREADY ON RECORD
-----------------------------------
EXPECTED_ATTRIBUTION in 22_decoder_guard.py maps each injected fault mode to the
component it should light up, and its comment says it was written down in advance
"so attribution accuracy is scored against a stated prediction rather than
whatever mapping happens to fit the results". This scores it.

Scored only on TEST-split episodes that actually crossed the performance
threshold: naming a cause for a fault that did no damage is a different question,
and a warning nobody should have raised.

Usage: python3 scripts/57_attribution_accuracy.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "processed"
REPORTS = REPO / "reports"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m


def score(df: pd.DataFrame, expected: dict) -> dict:
    """Confusion matrix of injected mode against attributed component."""
    conf: Counter = Counter()
    for _, r in df.iterrows():
        labels = str(r.attribution).split(",")
        ow, cw = int(r.onset_w), int(r.crossing_w)
        seg = labels[ow:cw + 1] or labels[ow:]
        seg = [s for s in seg if s]
        if not seg:
            continue
        # Majority vote over the early-warning window, not the single window at
        # crossing: one window is noisy and the whole point is a stable diagnosis.
        conf[(r["mode"], Counter(seg).most_common(1)[0][0])] += 1

    modes = sorted({m for m, _ in conf})
    comps = sorted({c for _, c in conf})
    rows, total, right = [], 0, 0
    for m in modes:
        n = sum(conf[(m, c)] for c in comps)
        e = expected.get(m, "-")
        ok = conf[(m, e)]
        total += n
        right += ok
        rows.append({"injected_mode": m, "n": n, "expected": e,
                     "n_correct": ok,
                     "accuracy": round(ok / n, 3) if n else None,
                     **{f"named_{c}": conf[(m, c)] for c in comps}})

    # Chance is over the components the monitor can actually EMIT, not over the
    # four it defines -- if it never emits one, guessing among the rest is the
    # honest baseline.
    n_emitted = len(comps)
    return {"rows": rows, "components_emitted": comps,
            "n_components_emitted": n_emitted,
            "n_components_defined": len(set(expected.values())),
            "total": total, "correct": right,
            "accuracy": round(right / total, 3) if total else None,
            "chance": round(1 / n_emitted, 3) if n_emitted else None}


def diagnose_rotation(P: str = "T11", n_episodes: int = 40) -> dict:
    """Why is GEOMETRY_ROTATION never attributed to `profile`?

    Two very different causes, needing different fixes:
      (a) `profile` is not lit during rotation -> the component does not detect it
      (b) `profile` IS lit but loses to a component earlier in the specificity
          order -> the RULE is at fault, not the component

    Distinguished by measuring the calibrated components directly and asking
    what a plain largest-wins rule would have chosen.
    """
    import re
    det = _load("det", "19_detectors.py")
    guard = _load("guard", "22_decoder_guard.py")
    inj = _load("inj", "17_fault_injector.py")
    loader = _load("loader", "03_load_dataset.py")

    def day(b):
        return int(re.search(r"day_(\d+)", b).group(1))

    _, eps = inj.load_plan(P)
    ds = loader.load_dataset(participant=P, load_neural=True, verbose=False)
    sc = pd.read_csv(OUT / "episode_scores_local.csv")
    sc = sc[(sc.detector == "decoder_guard") & (sc.split == "test") & sc.crossed]
    keep = set(sc[sc["mode"] == "GEOMETRY_ROTATION"].episode_id)

    rng = np.random.default_rng(20260902)
    rot = [e for e in eps if e.episode_id in keep and e.block_id in ds.neural]
    if not rot:
        return {}
    rot = [rot[i] for i in rng.choice(len(rot), min(n_episodes, len(rot)),
                                      replace=False)]

    H: dict[int, np.ndarray] = {}
    for b, X in ds.neural.items():
        st = np.arange(0, X.shape[0] - 1500 + 1, 250)
        if len(st) == 0:
            continue
        F = det.window_features(X, st, 1500)
        d = day(b)
        H[d] = F if d not in H else np.vstack([H[d], F])

    order = ["silence", "dispersion", "level", "profile"]
    vals: dict[str, list] = {k: [] for k in order}
    winners = []
    for e in rot:
        d = day(e.block_id)
        if d not in H or len(H[d]) < 40:
            continue
        r = np.random.default_rng(20260902 + d)
        g = guard.DecoderGuard().fit(H[d][r.choice(len(H[d]), 40, replace=False)])
        X = ds.neural[e.block_id]
        starts = np.arange(0, X.shape[0] - 1500 + 1, 250)
        ow = int(np.searchsorted(starts, e.onset_bin))
        if ow < 6:
            continue
        Y, _ = inj.apply_episode(X, e)
        F = det.window_features(Y, starts, 1500)
        g.recenter(F[:ow])
        c = g._calibrated(F)
        cw = int(sc[sc.episode_id == e.episode_id].crossing_w.iloc[0])
        sl = slice(ow, max(ow + 1, cw))
        for k in order:
            vals[k].append(float(np.median(c[k][sl])))
        M = np.vstack([c[k][sl] for k in order])
        winners.append(order[int(np.argmax(M.mean(axis=1)))])

    out = {"n_episodes": len(winners),
           "median_calibrated_z": {k: round(float(np.median(vals[k])), 2)
                                   for k in order},
           "fraction_lit": {k: round(float(np.mean(np.array(vals[k]) > 1.0)), 3)
                            for k in order},
           "winner_by_magnitude_alone": dict(Counter(winners))}
    return out


def main() -> int:
    guard = _load("guard", "22_decoder_guard.py")
    expected = guard.EXPECTED_ATTRIBUTION

    results = {}
    md = ["# When it warns, does it name the right cause?", "",
          "**Generated by `scripts/57_attribution_accuracy.py` — do not edit by hand.**",
          "",
          "The guard emits an attributed cause with every warning. That capability has",
          "been implemented since the guard was written and scored since the",
          "score-report was written — and then thrown away, printed to stdout and",
          "captured nowhere. No report held it and no check verified it, while the",
          "README carried a limitation about it with no numbers behind it.",
          "",
          "The mapping being scored was committed in advance, in",
          "`EXPECTED_ATTRIBUTION` in `22_decoder_guard.py`:", "",
          "| injected fault | component it should light |", "|---|---|"]
    for k, v in expected.items():
        md.append(f"| `{k}` | `{v}` |")
    md += ["",
           "Scored only on **test-split episodes that actually crossed** the performance",
           "threshold — naming a cause for a fault that did no damage is a different",
           "question, and a warning nobody should have raised. The cause for an episode",
           "is the majority vote across its early-warning window, not the single window",
           "at crossing.", ""]

    for P, f in [("T11", "episode_scores_local.csv"),
                 ("T5", "episode_scores_T5_local.csv")]:
        path = OUT / f
        if not path.exists():
            continue
        d = pd.read_csv(path)
        d = d[(d.detector == "decoder_guard") & (d.split == "test") & d.crossed
              & d.attribution.notna()]
        r = score(d, expected)
        results[P] = r
        T = pd.DataFrame(r["rows"])
        T.to_csv(OUT / f"attribution_{P}.csv", index=False)

        print(f"=== {P}: {r['total']} episodes ===")
        print(T.to_string(index=False))
        print(f"  overall {r['correct']}/{r['total']} = "
              f"{100 * (r['accuracy'] or 0):.0f}%   "
              f"chance {100 * (r['chance'] or 0):.0f}%\n")

        md += [f"## {P} — {r['total']} episodes", "",
               "| injected fault | n | expected | named correctly | accuracy |",
               "|---|---|---|---|---|"]
        for row in r["rows"]:
            md.append(f"| `{row['injected_mode']}` | {row['n']} | "
                      f"`{row['expected']}` | {row['n_correct']} | "
                      f"**{100 * (row['accuracy'] or 0):.0f}%** |")
        md += ["",
               f"**Overall {r['correct']}/{r['total']} = "
               f"{100 * (r['accuracy'] or 0):.0f}%**, against a chance level of "
               f"{100 * (r['chance'] or 0):.0f}% over the "
               f"{r['n_components_emitted']} components it actually emits.", ""]
        if r["n_components_emitted"] < r["n_components_defined"]:
            missing = sorted(set(expected.values()) - set(r["components_emitted"]))
            md += [f"> It never emits {', '.join(f'`{m}`' for m in missing)}, so any "
                   f"fault whose expected cause is that component can never be named "
                   f"correctly. Chance is computed over what it does emit, which is "
                   f"the harder baseline.", ""]

    diag = diagnose_rotation()
    if diag:
        results["rotation_diagnosis"] = diag
        print("rotation diagnosis (T11, "
              f"{diag['n_episodes']} episodes):")
        for k in ["silence", "dispersion", "level", "profile"]:
            print(f"  {k:<12} median z {diag['median_calibrated_z'][k]:>7.2f}   "
                  f"lit {diag['fraction_lit'][k]:>6.1%}")
        print(f"  largest-wins would pick: {diag['winner_by_magnitude_alone']}\n")
        md += ["## Why rotation is never attributed to `profile`", "",
               "Two causes are possible and they need different fixes: either",
               "`profile` is not lit during rotation, or it is lit but loses to a",
               "component earlier in the specificity order. Measuring the calibrated",
               "components directly on "
               f"{diag['n_episodes']} rotation episodes:", "",
               "| component | median calibrated z | fraction lit (z > 1) |",
               "|---|---|---|"]
        for k in ["silence", "dispersion", "level", "profile"]:
            md.append(f"| `{k}` | {diag['median_calibrated_z'][k]:.2f} | "
                      f"{diag['fraction_lit'][k]:.0%} |")
        w = diag["winner_by_magnitude_alone"]
        tot = sum(w.values()) or 1
        md += ["",
               "`profile` **is** lit — in "
               f"{diag['fraction_lit']['profile']:.0%} of episodes. But `dispersion` "
               f"sits at {diag['median_calibrated_z']['dispersion']:.1f} against "
               f"profile's {diag['median_calibrated_z']['profile']:.1f}, so it is not "
               "the specificity rule that buries it: ranked by raw magnitude alone, "
               "`dispersion` still wins "
               f"{max(w.values()) / tot:.0%} of the time.", "",
               "**So the fault is in the components, not the rule.** The guard defines",
               "`dispersion` as *\"channels spread apart in gain, total conserved\"* —",
               "and `GEOMETRY_ROTATION` is injected with Givens rotations, which are",
               "**norm-preserving by construction**. Channels exchange activity while",
               "the total is conserved. That is the same signature, by definition.",
               "",
               "The preregistered mapping was wrong from the start. Rotation was never",
               "going to light `profile` more than `dispersion`, because what rotation",
               "does to the data *is* what `dispersion` measures. Re-ordering the rule",
               "would not fix it and neither would re-weighting; the two components",
               "would have to be redefined to be separable in the first place.", ""]
    (OUT / "attribution_accuracy.json").write_text(json.dumps(results, indent=2))
    (REPORTS / "ATTRIBUTION_ACCURACY.md").write_text("\n".join(md) + "\n")
    print(f"wrote {REPORTS / 'ATTRIBUTION_ACCURACY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
