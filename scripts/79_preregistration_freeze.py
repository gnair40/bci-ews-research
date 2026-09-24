#!/usr/bin/env python3
"""
79_preregistration_freeze.py
============================
Is the frozen preregistration still frozen, and does the rest of the
repository still agree with it?

WHY THIS EXISTS
---------------
`physical/docs/09_PREREGISTRATION.md` was frozen on 24 September 2026 at commit
f4dda04. Its header says "this file must not be edited from here on".

That sentence protects nothing by itself. A file can be edited; a header
saying it should not be is not a lock, and an honest project does not rely on
one. Worse, the failure would be invisible in exactly the way this project has
already been bitten by twice: the preregistration would still *read* as frozen
while saying something different from what it said before the data existed.

So the rule is enforced from outside the file, three ways:

1. **The freeze commit is real.** The hash in the header names a commit that
   exists, that contains this file, and whose copy of it already said FROZEN.

2. **Every post-freeze edit is disclosed.** Git knows exactly which commits
   have touched the file since. §12.1 has a table of them. If the two disagree
   in either direction — an undisclosed edit, or a ledger row for a commit
   that never touched the file — this fails. A non-substantive edit is fine;
   an *unlisted* one is not.

3. **The frozen numbers still match the rest of the repository.** The sample
   sizes and thresholds fixed in §4 and §11 appear in the other documents and
   in the code. Freezing a number in one file while a different number lives
   everywhere else is how a preregistration becomes decorative.

WHAT IT CANNOT DO
-----------------
It cannot tell a substantive edit from a typographical one — that judgement is
in the "Substantive?" column, written by whoever made the edit. What it
guarantees is that the edit is *listed*, so someone reading the ledger sees it
and can run the one-line `git diff` the section gives them. The gate makes
concealment take deliberate effort rather than mere carelessness.

It also cannot run without git history. In a shallow clone or an exported
tarball, check 2 is skipped and says so out loud rather than passing quietly.

Usage: python3 scripts/79_preregistration_freeze.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PREREG = REPO / "physical" / "docs" / "09_PREREGISTRATION.md"
PREREG_REL = "physical/docs/09_PREREGISTRATION.md"

# Numbers fixed by the freeze, and where else in the repository they have to
# agree. Each entry: (label, regex that must match the preregistration,
# expected value, [(file, regex, why it must agree)]).
FROZEN_VALUES = [
    (
        "fault-free campaign length (§4, §11 call 1)",
        r"\|\s*Fault-free \(P-2\)\s*\|\s*\*\*(\d+)\*\*",
        "101",
        [
            ("physical/docs/12_RUNBOOK.md",
             r"run_campaign\.py plan --session 10 --healthy (\d+)",
             "the runbook command that actually draws the arm"),
            ("physical/docs/06_DATA_COLLECTION.md",
             r"run_campaign\.py plan --session 10 --healthy (\d+)",
             "the data-collection command"),
            ("physical/docs/05_SOFTWARE.md",
             r"run_campaign\.py plan   --session 10 --healthy (\d+)",
             "the script index"),
        ],
    ),
    (
        "degraded campaign length (§4)",
        r"\|\s*Degraded \(P-3\)\s*\|\s*\*\*(\d+)\*\*",
        "101",
        [
            ("physical/docs/12_RUNBOOK.md",
             r"run_campaign\.py plan   --session 20 --degraded (\d+)",
             "the runbook command that draws the degraded arm"),
        ],
    ),
    (
        "undesigned-fault arm (§4)",
        r"\|\s*Undesigned \(P-5\)\s*\|\s*\*\*(\d+)\*\*",
        "10",
        [
            ("physical/docs/02_EXPERIMENTS.md",
             r"\|\s*P-5 undesigned faults\s*\|\s*(\d+)\s*\|",
             "the cost table in the experiments document"),
        ],
    ),
]

# Thresholds frozen in §11 that also live in code. A threshold that drifts in
# code while the preregistration still quotes the old one is the worst case:
# the analysis silently answers a different question than the one registered.
FROZEN_CONSTANTS = [
    ("false-alarm budget (§11 call 3)", r"\*\*0\.1/hour\*\*",
     "physical/code/monitor.py", r"FALSE_ALARM_BUDGET_PER_HOUR\s*=\s*([\d.]+)", "0.1"),
    ("silence-gate bar (§11 call 4)", r"\|\s*4\s*\|[^|]*\|\s*\*\*10%\*\*",
     "physical/code/analyze_falsealarm.py", r"SILENCE_BAR\s*=\s*([\d.]+)", "0.1"),
]


def same_number(a: str, b: str) -> bool:
    """0.10 and 0.1 are the same threshold. Text comparison says otherwise."""
    try:
        return float(a) == float(b)
    except ValueError:
        return a == b


def run_git(*args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(("git", "-C", str(REPO)) + args,
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return r.returncode, (r.stdout or r.stderr).strip()


def check_header(text: str) -> tuple[list[str], str | None]:
    print("\n1. THE FREEZE COMMIT")
    problems: list[str] = []

    if "**Status: FROZEN." not in text:
        problems.append("the preregistration no longer declares itself FROZEN")
        print("   FAIL  header does not say 'Status: FROZEN'")
        return problems, None
    print("   ok    header declares the document FROZEN")

    m = re.search(r"\*\*Frozen at commit:\*\*\s*`([0-9a-f]{40})`", text)
    if not m:
        problems.append("no 40-character freeze hash in the header")
        print("   FAIL  header carries no full freeze hash")
        return problems, None
    sha = m.group(1)
    print(f"   ok    header names commit {sha[:12]}")

    code, out = run_git("cat-file", "-t", sha)
    if code or out != "commit":
        problems.append(f"freeze hash {sha[:12]} is not a commit in this history")
        print(f"   FAIL  {sha[:12]} is not a commit here ({out})")
        return problems, None
    print(f"   ok    {sha[:12]} exists in this repository's history")

    code, out = run_git("show", f"{sha}:{PREREG_REL}")
    if code:
        problems.append(f"the freeze commit does not contain {PREREG_REL}")
        print(f"   FAIL  {sha[:12]} does not contain the preregistration")
    elif "**Status: FROZEN." not in out:
        problems.append("the file at the freeze commit did not say FROZEN — "
                        "the header names the wrong commit")
        print(f"   FAIL  the copy at {sha[:12]} does not say FROZEN")
    else:
        print(f"   ok    the copy at {sha[:12]} already said FROZEN")
    return problems, sha


def check_ledger(text: str, sha: str) -> list[str]:
    print("\n2. POST-FREEZE EDITS — git history vs the §12.1 ledger")
    problems: list[str] = []

    code, out = run_git("log", "--format=%h", f"{sha}..HEAD", "--", PREREG_REL)
    if code:
        print("   SKIP  no usable git history (shallow clone or export).")
        print("         This check cannot run here; it is not passing, it is")
        print("         absent. Run it in a full clone before trusting it.")
        return problems
    in_git = {h for h in out.split() if h}

    section = text.split("### 12.1", 1)
    if len(section) != 2:
        problems.append("§12.1, the post-freeze edit ledger, is missing")
        print("   FAIL  no §12.1 ledger to compare against")
        return problems
    ledger = section[1]

    # Rows are keyed on the commit SUBJECT, not the hash, and the reason is
    # not cosmetic. A row keyed on a hash cannot name the commit that adds it:
    # writing the row changes the file, which makes a new commit, which needs
    # a new row, forever. A subject is known before the commit is made, so the
    # commit that adds a row can disclose itself. That closes the loop that
    # would otherwise leave exactly one edit permanently undisclosed.
    subjects = []
    for h in in_git:
        code, subject = run_git("log", "-1", "--format=%s", h)
        subjects.append((h, subject if not code else ""))

    missing = [(h, subj) for h, subj in subjects
               if not subj or subj not in ledger]
    if missing:
        problems.append(f"{len(missing)} commit(s) edited the frozen "
                        f"preregistration without a ledger row: "
                        f"{', '.join(h for h, _ in missing)}")
        print("   FAIL  edited since the freeze but NOT listed in §12.1:")
        for h, subj in missing:
            print(f"           {h}  {subj!r}")
        print("         Add a row to §12.1 quoting that subject exactly,")
        print("         saying what it changed and whether it was substantive.")
        print("         If it WAS substantive, it is an amendment under §9 and")
        print("         belongs in the log above, not in that table.")
    else:
        print(f"   ok    {len(subjects)} post-freeze commit(s), all disclosed "
              f"in §12.1")

    # A row naming a subject no commit ever used means the ledger is describing
    # edits that did not happen, which is its own kind of wrong.
    row_subjects = re.findall(r"^\|\s*`([^`]+)`\s*\|", ledger, re.M)
    known = {subj for _, subj in subjects}
    orphan = [r for r in row_subjects if r not in known]
    if orphan:
        problems.append(f"§12.1 rows name commits that never touched the "
                        f"file: {orphan}")
        print(f"   FAIL  ledger rows with no matching commit: {orphan}")
    return problems


def check_values(text: str) -> list[str]:
    print("\n3. FROZEN NUMBERS — still the same everywhere they appear")
    problems: list[str] = []

    for label, rx, expected, elsewhere in FROZEN_VALUES:
        m = re.search(rx, text)
        if not m:
            problems.append(f"{label}: not found in the preregistration")
            print(f"   FAIL  {label}: the frozen value is no longer stated")
            continue
        got = m.group(1)
        if got != expected:
            problems.append(f"{label}: preregistration says {got}, this gate "
                            f"was written against {expected}")
            print(f"   FAIL  {label}: says {got}, gate expects {expected}")
            print("         If the arm was changed, that is an amendment under")
            print("         §9 — and this gate must be updated in the same commit.")
            continue
        bad = []
        for rel, other_rx, why in elsewhere:
            p = REPO / rel
            if not p.exists():
                bad.append(f"{rel} is missing")
                continue
            hits = set(re.findall(other_rx, p.read_text(errors="replace")))
            if not hits:
                bad.append(f"{rel} no longer contains the command ({why})")
            elif hits != {expected}:
                bad.append(f"{rel} says {sorted(hits)} ({why})")
        if bad:
            problems.append(f"{label}: " + "; ".join(bad))
            print(f"   FAIL  {label} = {expected}, but:")
            for b in bad:
                print(f"           {b}")
        else:
            print(f"   ok    {label} = {expected}, and {len(elsewhere)} other "
                  f"place(s) agree")

    for label, doc_rx, code_rel, code_rx, expected in FROZEN_CONSTANTS:
        if not re.search(doc_rx, text):
            problems.append(f"{label}: no longer stated in the preregistration")
            print(f"   FAIL  {label}: not found in the preregistration")
            continue
        p = REPO / code_rel
        m = re.search(code_rx, p.read_text(errors="replace")) if p.exists() else None
        if not m:
            problems.append(f"{label}: cannot find the constant in {code_rel}")
            print(f"   FAIL  {label}: constant not found in {code_rel}")
        elif not same_number(m.group(1), expected):
            # Compared as numbers, not as text: the first version of this gate
            # failed on 0.10 vs 0.1, which is the same threshold spelled two
            # ways. A gate that cries wolf gets switched off.
            problems.append(f"{label}: {code_rel} says {m.group(1)}, "
                            f"preregistration froze {expected}")
            print(f"   FAIL  {label}: {code_rel} = {m.group(1)}, frozen at {expected}")
        else:
            print(f"   ok    {label} = {expected}, and {code_rel} agrees")

    return problems


def check_no_placeholders(text: str) -> list[str]:
    print("\n4. NOTHING LEFT FOR THE RESEARCHER TO FILL IN")
    problems: list[str] = []
    # The §10 procedure quotes the placeholder names as a record of what was
    # done. Anywhere else, an unfilled placeholder means the freeze is a
    # pretence.
    body = text.split("## 10. Freeze procedure", 1)[0]
    left = re.findall(r"\[\[[^\]]+\]\]", body)
    if left:
        problems.append(f"unfilled placeholder(s) before §10: {left}")
        print(f"   FAIL  still to be filled in: {left}")
    else:
        print("   ok    no unfilled placeholders in the frozen predictions")
    return problems


def main() -> int:
    if not PREREG.exists():
        print(f"FAIL — {PREREG_REL} does not exist.")
        return 1
    text = PREREG.read_text(errors="replace")

    print("=" * 72)
    print("preregistration freeze — is it frozen, and does the repo agree?")
    print("=" * 72)

    problems, sha = check_header(text)
    if sha:
        problems += check_ledger(text, sha)
    else:
        print("\n2. POST-FREEZE EDITS — skipped, no usable freeze commit")
    problems += check_values(text) + check_no_placeholders(text)

    print("\n" + "=" * 72)
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        print("\nA preregistration that has drifted since its timestamp is")
        print("worse than none: it still looks like evidence of foresight.")
        return 1
    print("PASS — the freeze holds, every post-freeze edit is disclosed, and")
    print("       the frozen numbers still match the rest of the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
