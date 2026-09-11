#!/usr/bin/env python3
"""
A linter for the statistical mistakes this project has actually made.

Three error classes have been found here, all by accident, and all by checks
written after the work they caught:

  1. INFERENCE ON POOLED, NON-INDEPENDENT UNITS
     26_achievability.py concatenated every window from every episode and ran a
     Mann-Whitney test on the result. Sample size inflated 26.6x; four p-values
     published as exactly 0; three "significant" results were not real.

  2. A COMPARISON THAT CAN NEVER BE TRUE
     44_day_variance.py tested e.severity -- a float -- against the string
     "high". Always False, so the fault-mix control reported 0.00 for every day
     and looked exactly like a control that passed.

  3. AN ESTIMATOR BIASED BY ITS OWN WEIGHTS
     Inverse-variance weighting of AUC, a bounded statistic whose variance
     shrinks toward 0 and 1, inflated a pooled estimate from 0.675 to 0.836.

Waiting to trip over a fourth is not a strategy. This encodes the three as
static checks and runs them over every script.

A finding here is a PROMPT, not a verdict: each is a pattern that was wrong at
least once in this repository, and each site needs a human decision. Sites already
reviewed are listed in REVIEWED with the reason, so the check stays a clean gate.

Usage: python3 scripts/61_statistical_hygiene.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

TESTS = {"mannwhitneyu", "ttest_ind", "ttest_rel", "spearmanr", "pearsonr",
         "kendalltau", "wilcoxon", "kruskal", "chi2_contingency", "binomtest"}
POOLERS = {"concatenate", "hstack", "ravel", "flatten"}

# (script, line-ish reason) -- sites inspected by hand and deliberately kept.
REVIEWED = {
    ("26_achievability.py", "pooled_inference"):
        "Known and corrected: its p-values are recomputed at episode level by "
        "60_unit_of_analysis.py and ACHIEVABILITY.md carries an inline correction.",
    ("31_verify_claims.py", "pooled_inference"):
        "Reproduces the published window-level figure on purpose, so the register "
        "can record what C02's number actually is. Not an inference claim.",
    ("44_day_variance.py", "inverse_variance"):
        "Kept deliberately, labelled ..._BIASED_DO_NOT_QUOTE, with the bias "
        "measured in the same output. Cochran's Q needs the same weights.",
    ("60_unit_of_analysis.py", "pooled_inference"):
        "Computes the pooled statistic on purpose, to show what it was.",
    ("59_per_mode_detection.py", "pooled_inference"):
        "Computes the window-level AUC deliberately, beside the episode-level "
        "one, so the register can record which quantity C02 is. No p-value.",
    ("23_benchmark_figures.py", "pooled_inference"):
        "A descriptive bar chart with no inference attached -- the p-value is "
        "discarded at the call site. The axis now says 'window-level AUC'.",
}


def literal_strings(node) -> list[str]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def check_file(path: Path) -> list[dict]:
    src = path.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    findings = []

    # ---- 1. inference on pooled units ----------------------------------
    # Local helper functions that themselves run a statistical test. Without
    # this, the check MISSES ITS OWN MOTIVATING EXAMPLE: 26_achievability.py
    # wraps mannwhitneyu inside a local auc(pos, neg), so the pooled variable
    # never appears in the test call's arguments. A linter that cannot catch
    # the case it was written for is worse than no linter.
    test_wrappers: set[str] = set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.FunctionDef):
            continue
        for sub in ast.walk(n):
            if (isinstance(sub, ast.Call)
                    and getattr(sub.func, "attr", getattr(sub.func, "id", ""))
                    in TESTS):
                test_wrappers.add(n.name)
                break

    pooled_vars: dict[str, int] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for sub in ast.walk(n.value):
                if (isinstance(sub, ast.Call)
                        and getattr(sub.func, "attr", "") in POOLERS):
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            pooled_vars[t.id] = n.lineno
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fname = getattr(n.func, "attr", getattr(n.func, "id", ""))
        direct = fname in TESTS
        wrapped = fname in test_wrappers
        if not (direct or wrapped):
            continue
        for a in n.args:
            names = {s.id for s in ast.walk(a) if isinstance(s, ast.Name)}
            hit = names & set(pooled_vars)
            if hit:
                how = "directly" if direct else f"via {fname}()"
                findings.append({
                    "kind": "pooled_inference", "line": n.lineno,
                    "detail": f"statistical test {how} on {sorted(hit)}, "
                              f"pooled at line {pooled_vars[sorted(hit)[0]]}"})
                break

    # ---- 2. a comparison that can never be true -------------------------
    # An attribute compared against a string literal somewhere, and used in
    # arithmetic or float() somewhere else, is the shape of the severity bug.
    numeric_attrs, string_compared = set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "float":
            for a in n.args:
                if isinstance(a, ast.Attribute):
                    numeric_attrs.add(a.attr)
        if isinstance(n, ast.BinOp):
            for side in (n.left, n.right):
                if isinstance(side, ast.Attribute):
                    numeric_attrs.add(side.attr)
        if isinstance(n, ast.Compare) and isinstance(n.left, ast.Attribute):
            for op, cmp in zip(n.ops, n.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and literal_strings(cmp):
                    string_compared[n.left.attr] = n.lineno
    for attr, line in string_compared.items():
        if attr in numeric_attrs:
            findings.append({
                "kind": "impossible_comparison", "line": line,
                "detail": f".{attr} is compared to a string here and used "
                          f"numerically elsewhere in the same file"})

    # ---- 3. inverse-variance weighting ---------------------------------
    for n in ast.walk(tree):
        if not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)):
            continue
        d = n.right
        if isinstance(d, ast.BinOp) and isinstance(d.op, ast.Pow):
            e = d.right
            if isinstance(e, ast.Constant) and e.value == 2:
                txt = ast.unparse(d.left) if hasattr(ast, "unparse") else ""
                if any(k in txt.lower() for k in ("se", "std", "err", "sd", "var")):
                    findings.append({
                        "kind": "inverse_variance", "line": n.lineno,
                        "detail": f"1/{txt}**2 weighting — biased for a bounded "
                                  f"statistic such as AUC"})
    return findings


def main() -> int:
    scripts = sorted(p for p in SCRIPTS.glob("*.py")
                     if p.name[:2].isdigit())
    all_new, all_reviewed = [], []
    for p in scripts:
        for f in check_file(p):
            f["script"] = p.name
            key = (p.name, f["kind"])
            if key in REVIEWED:
                f["reviewed_because"] = REVIEWED[key]
                all_reviewed.append(f)
            else:
                all_new.append(f)

    print(f"statistical hygiene over {len(scripts)} scripts\n")
    kinds = ["pooled_inference", "impossible_comparison", "inverse_variance"]
    for k in kinds:
        n_new = sum(1 for f in all_new if f["kind"] == k)
        n_rev = sum(1 for f in all_reviewed if f["kind"] == k)
        print(f"  {k:<24} {n_new} unreviewed, {n_rev} reviewed")

    if all_reviewed:
        print("\nreviewed and deliberately kept:")
        for f in all_reviewed:
            print(f"  {f['script']}:{f['line']}  {f['kind']}")
            print(f"      {f['reviewed_because']}")

    if all_new:
        print(f"\n{len(all_new)} SITE(S) NEEDING A DECISION:")
        for f in all_new:
            print(f"  {f['script']}:{f['line']}  {f['kind']}")
            print(f"      {f['detail']}")
    else:
        print("\nPASS — no unreviewed sites")

    out = {"n_scripts": len(scripts),
           "n_unreviewed": len(all_new), "n_reviewed": len(all_reviewed),
           "unreviewed": all_new, "reviewed": all_reviewed}
    (REPO / "data" / "processed" / "statistical_hygiene.json").write_text(
        json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
