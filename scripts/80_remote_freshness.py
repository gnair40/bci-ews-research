#!/usr/bin/env python3
"""
80_remote_freshness.py
======================
Is this working copy's picture of the repository actually current?

WHY THIS EXISTS
---------------
On the night of 24 September 2026 I inspected the `main` branch, found four
files dated 16 August, concluded the repository's default branch did not
contain the project, wrote a warning box into the runbook, changed four
documents and committed the claim.

All of it was wrong. `main` on the server was three hundred commits further on
and worked fine. What I had inspected was the *local* ref `refs/heads/main`,
which had not been fetched since the working copy was created. Git answered the
question I asked, accurately, about a pointer that was five weeks stale.

Every other gate in this repository compares the repository to itself. Not one
of them had any reason to notice, because from the inside a stale ref is
indistinguishable from a current one: `git log main` prints commits either way,
with no indication that the server disagrees.

WHAT IT CHECKS
--------------
1. **Stale local branch refs.** For every local branch with an upstream, is the
   remote ahead of it? A remote-ahead ref is a branch you may reason about and
   be wrong, which is the whole failure above.

2. **Unmerged work**, reported rather than failed. How far the current branch
   is ahead of the default branch. Being ahead is normal — that is what a
   branch is for — but it decides whether a fresh clone of the default branch
   contains what you just wrote, and that is worth printing where somebody
   will see it.

WHAT IT CANNOT DO
-----------------
It needs the network. With no network it **skips and says so** rather than
passing, because "I could not check" and "I checked and it was fine" are
different statements and only one of them is reassuring. That distinction is
the same one this project keeps having to relearn.

It also cannot tell you a stale ref actually misled you — only that it could.

Usage: python3 scripts/80_remote_freshness.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FETCH_TIMEOUT = 60


def git(*args: str, timeout: int = 30) -> tuple[int, str]:
    try:
        r = subprocess.run(("git", "-C", str(REPO)) + args,
                           capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    return r.returncode, (r.stdout or r.stderr).strip()


def default_branch() -> str:
    """Whatever the server says its default is -- never hardcode 'main'."""
    code, out = git("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if code == 0 and out.startswith("refs/remotes/origin/"):
        return out[len("refs/remotes/origin/"):]
    for guess in ("main", "master"):
        if git("rev-parse", "--verify", f"refs/remotes/origin/{guess}")[0] == 0:
            return guess
    return ""


def main() -> int:
    print("=" * 72)
    print("remote freshness — is this working copy's view current?")
    print("=" * 72)

    if git("rev-parse", "--git-dir")[0] != 0:
        print("\nSKIP — not a git repository. Nothing to compare.")
        return 0

    print("\nfetching...")
    code, out = git("fetch", "--quiet", "--all", "--prune", timeout=FETCH_TIMEOUT)
    if code != 0:
        print("\nSKIP — could not reach the remote:")
        for line in out.splitlines()[:4]:
            print(f"       {line}")
        print("\n       This check did NOT pass. It did not run. Re-run it")
        print("       somewhere with network before trusting any statement")
        print("       about what the remote contains.")
        return 0

    problems: list[str] = []

    print("\n1. LOCAL BRANCH REFS — is any of them behind its remote?")
    code, out = git("for-each-ref", "--format=%(refname:short) %(upstream:short)",
                    "refs/heads")
    rows = [l.split() for l in out.splitlines() if len(l.split()) == 2]
    if not rows:
        print("   ok    no local branch tracks a remote; nothing to be stale")
    for branch, upstream in rows:
        # An upstream can vanish -- the remote branch was renamed or deleted,
        # and --prune removed the tracking ref. The first version of this gate
        # printed git's four-line "ambiguous argument" error into the middle of
        # its own output, which is how a check teaches people to ignore it.
        if git("rev-parse", "--verify", "--quiet",
               f"refs/remotes/{upstream}")[0] != 0:
            print(f"   info  {branch} tracks {upstream}, which no longer exists")
            print(f"         on the remote (renamed or deleted). Not stale —")
            print(f"         unmoored. `git branch --unset-upstream {branch}`")
            print(f"         or delete the branch if it is finished with.")
            continue
        code, counts = git("rev-list", "--left-right", "--count",
                           f"{branch}...{upstream}")
        if code != 0:
            print(f"   ?     {branch}: could not compare "
                  f"({counts.splitlines()[0] if counts else 'no output'})")
            continue
        ahead, behind = (int(x) for x in counts.split())
        if behind:
            problems.append(f"{branch} is {behind} commit(s) behind {upstream}")
            print(f"   FAIL  {branch} is {behind} behind {upstream}")
            print(f"         Anything you conclude by reading `{branch}` may be")
            print(f"         about a pointer the server has already moved past.")
        else:
            extra = f", {ahead} ahead" if ahead else ""
            print(f"   ok    {branch} is current with {upstream}{extra}")

    print("\n2. UNMERGED WORK — would a clone of the default branch have this?")
    base = default_branch()
    if not base:
        print("   ?     could not determine the remote's default branch")
    else:
        code, head = git("rev-parse", "--abbrev-ref", "HEAD")
        code, counts = git("rev-list", "--left-right", "--count",
                           f"origin/{base}...HEAD")
        if code != 0:
            print(f"   ?     could not compare against origin/{base}")
        else:
            behind_base, ahead_base = (int(x) for x in counts.split())
            print(f"   info  default branch is origin/{base}")
            if ahead_base:
                print(f"   info  {head} is {ahead_base} commit(s) ahead of it — "
                      f"a fresh clone")
                print(f"         of origin/{base} would NOT contain that work.")
            else:
                print(f"   info  {head} adds nothing origin/{base} lacks")
            if behind_base:
                print(f"   info  origin/{base} has {behind_base} commit(s) this "
                      f"branch lacks")

    print("\n" + "=" * 72)
    if problems:
        print(f"{len(problems)} stale ref(s):")
        for p in problems:
            print(f"  - {p}")
        print("\n`git fetch` fixes the refs. What it cannot fix is a conclusion")
        print("already drawn from one, or a commit that recorded it.")
        return 1
    print("PASS — every local ref is current with its remote.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
