#!/usr/bin/env python3
"""
77_cross_reference.py
=====================
Do the documents agree with each other, and with the code?

WHY THIS EXISTS
---------------
Twice in one week this project shipped two documents that disagreed about the
same quantity, and no gate noticed:

  * `PHASE3_REPORT` gave the session-level AUC target as 0.990 from 1 September.
    `scripts/28`'s report gave 0.933 from 6 September. They sat in the same
    repository contradicting each other for two weeks.
  * `DATASET_README` said the dataset had never been downloaded. It had — the
    same day that sentence was last edited. It stayed wrong for four weeks.

Neither was caught, and the reason is worth stating: every other gate here
checks that a figure matches **the data file it came from**, and both figures
were perfectly faithful to their own calculation. *Nothing was checking that two
documents agree, or that a sentence which was true when written is still true.*

WHAT IT CHECKS
--------------
1. **Constants in the code match what the documents claim.** The budget, the
   window geometry, the difficulty target, the per-session size. If someone
   changes a constant, the documents quoting it must change too.

2. **Values that must not be quoted as current do not appear unmarked.** Some
   were wrong; some were right for a design since replaced. Either way a reader
   quoting one today is quoting something this project no longer stands behind.
   Each is listed with the wording that legitimises mentioning it — "corrected",
   "superseded", "used to say". A bare 0.933 with no such marker within a few
   hundred characters is a document that did not get the memo.

WHAT IT CANNOT DO
-----------------
It cannot find a contradiction nobody has noticed yet. Row 2 is a list of
mistakes already made, so it prevents recurrence rather than discovery. That
limit is the honest reason this is a gate and not a solution: **when a number
changes, the person changing it has to add a row here.** Nothing enforces that,
and saying so is better than implying the problem is solved.

Usage: python3 scripts/77_cross_reference.py
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Wording that makes mentioning a superseded value legitimate: the document is
# discussing the correction rather than repeating the error.
# Whitespace is \s+ throughout: these markers routinely straddle a line break
# in wrapped prose, and the first version of this regex missed two legitimate
# corrections because "until 20 September" happened to wrap after "until".
MARKERS = re.compile(
    r"corrected|supersed|used\s+to|previously|no\s+longer|instead\s+of|"
    r"until\s+then|until\s+\d|not\s+the\s+budget|earlier\s+version|"
    r"was\s+wrong|predates|historical|amendment|kept\s+as\s+the\s+record|"
    r"old\s+wording|read\s+<em>|this\s+is\s+the\s+record",
    re.I)
CONTEXT = 600      # characters either side to look for a marker


def documents() -> list[Path]:
    """Every document a reader might act on. Discovered, never hardcoded."""
    out = [REPO / "README.md"]
    for d in ("reports", "research", "physical", "physical/docs",
              "physical/data", "rig", "tools/audit_report"):
        out += sorted((REPO / d).glob("*.md"))
        out += sorted((REPO / d).glob("*.html"))
    out += [REPO / "DATASET_README.md"]
    # The log is a dated record of what was believed at the time. Correcting it
    # would destroy the thing it exists for.
    return [p for p in out if p.exists() and p.name != "research_log.md"]


def _mod(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# 1. CONSTANTS: the code is the source of truth, the documents must match
# ---------------------------------------------------------------------------

def check_constants() -> list[str]:
    print("\n1. CONSTANTS — code against documents")
    sys.path.insert(0, str(REPO / "physical" / "code"))
    problems = []
    try:
        M = _mod("physical/code/monitor.py", "xref_monitor")
        B = _mod("physical/code/bench.py", "xref_bench")
        H = _mod("physical/code/health_check.py", "xref_health")
    except Exception as e:
        print(f"   could not import the physical code: {type(e).__name__}: {e}")
        return [f"physical code did not import: {e}"]

    expected = [
        ("false-alarm budget, per hour", M.FALSE_ALARM_BUDGET_PER_HOUR, 0.1),
        ("analysis window, seconds", M.WINDOW_FRAMES / M.FPS, 30.0),
        ("window step, seconds", M.STEP_FRAMES / M.FPS, 5.0),
        ("frames per second", float(M.FPS), 50.0),
        ("neural margin target, degrees", B.NEURAL_MARGIN, 36.1),
        ("margin tolerance, degrees", B.MARGIN_TOLERANCE, 6.0),
        ("bytes per session (health_check)", H.BYTES_PER_SESSION / 1e6, 25.0),
    ]
    for label, actual, documented in expected:
        ok = abs(actual - documented) < max(0.01, 0.06 * abs(documented))
        print(f"   {'ok  ' if ok else 'FAIL'}  {label:<34} "
              f"code {actual:<8.4g} documents {documented}")
        if not ok:
            problems.append(f"{label}: code says {actual}, documents say {documented}")

    # The 30-hour figure is derived, not stored. Check the derivation holds.
    hours = 3.0 / M.FALSE_ALARM_BUDGET_PER_HOUR
    ok = abs(hours - 30.0) < 0.5
    print(f"   {'ok  ' if ok else 'FAIL'}  {'rule of three: 3/budget hours':<34} "
          f"code {hours:<8.4g} documents 30")
    if not ok:
        problems.append(f"rule of three gives {hours} h, documents say 30")
    return problems


# ---------------------------------------------------------------------------
# 2. VALUES THAT MUST NOT BE QUOTED AS CURRENT
# ---------------------------------------------------------------------------
# Not all of these were *wrong*. Some were correct for a design that has since
# been replaced -- the old parts list really did cost $115. What they have in
# common is that a reader who quotes one today is quoting something this
# project no longer stands behind, which is the thing worth preventing.
#
# ADD A ROW HERE WHENEVER A NUMBER IN THIS PROJECT CHANGES. That is the whole
# maintenance burden, and nothing enforces it but this comment.
SUPERSEDED = [
    ("session-level AUC target", r"\b0\.933\b",
     "computed at a 10% false-flag rate, not the 0.1/h budget; it is 0.990"),
    ("decision-rate looseness", r"four orders of magnitude",
     "the looseness is the pooling factor, 55 -- about 1.7 orders"),
    ("claim count", r"\b93 claims\b|ninety-three headline",
     "the verifier now checks 102"),
    ("configuration count", r"\b36 configurations\b",
     "the grid is 48 configurations"),
    ("dataset status", r"Dataset NOT yet downloaded",
     "downloaded 25 August 2026"),
    ("apparatus cost", r"\$115\b",
     "correct for the earlier parts list; the current one is ~$150-250"),
    ("physical code count", r"[Tt]hirteen files in `physical/code/`|"
                            r"[Ee]leven scripts",
     "there are 16"),
]


def check_superseded(docs: list[Path]) -> list[str]:
    print("\n2. SUPERSEDED VALUES — present, and not marked as corrected")
    problems = []
    for label, pattern, why in SUPERSEDED:
        rx = re.compile(pattern)
        unmarked = []
        for p in docs:
            text = p.read_text(errors="replace")
            for m in rx.finditer(text):
                lo = max(0, m.start() - CONTEXT)
                if not MARKERS.search(text[lo:m.end() + CONTEXT]):
                    unmarked.append((p.relative_to(REPO), m.group(0)))
        if unmarked:
            print(f"   FAIL  {label}")
            print(f"         {why}")
            for rel, got in unmarked[:8]:
                print(f"         {rel}  contains {got!r} with no correction nearby")
            problems.append(f"{label}: unmarked in "
                            f"{', '.join(str(r) for r, _ in unmarked[:4])}")
        else:
            print(f"   ok    {label}")
    return problems


def main() -> int:
    docs = documents()
    print("=" * 72)
    print(f"cross-reference — {len(docs)} documents")
    print("=" * 72)
    problems = check_constants() + check_superseded(docs)
    print("\n" + "=" * 72)
    if problems:
        print(f"{len(problems)} disagreement(s):")
        for p in problems:
            print(f"  - {p}")
        print("\nA document disagreeing with the code, or repeating a corrected")
        print("figure without saying it was corrected, is how a reader ends up")
        print("quoting a number this project has already withdrawn.")
        return 1
    print("PASS — documents agree with the code, and no corrected value")
    print("       appears without its correction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
