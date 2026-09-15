#!/usr/bin/env python3
"""
69_command_check.py
===================
Does every command written in the documentation actually parse?

WHY
---
`research/RIG_PROCEDURE.md` and the research plan are written so that somebody
who has never seen this project can reproduce it by following them literally. A
command in those documents that the script would reject is not a typo; it is a
replication failure, and the reader has no way to tell the difference between
"I typed it wrong" and "the instructions are wrong".

Written 14 September 2026, after the rig dry run showed the documented rig
commands were wrong in two different ways at once:

    python3 scripts/17_fault_injector.py --participant RIG plan
    python3 scripts/18_reference_decoder.py --participant RIG

The first puts the subcommand after an option that belongs to the subparser, so
argparse rejects it. The second omits the subcommand entirely. Four documented
commands were broken. Nobody had ever run one, because until the dry run there
was no rig data to run them against.

HOW
---
Every ```python3 scripts/...``` line in the documents is extracted and handed to
its own script's argparse, with `parse_args` patched to stop immediately after
parsing. Nothing is executed, no file is read or written, and no analysis runs.
It answers exactly one question: would this command be accepted?

It cannot tell you a command does the right thing. It tells you the reader will
not be stopped at the first line.

Usage: python3 scripts/69_command_check.py
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

DOCS = [
    "research/RIG_PROCEDURE.md",
    "research/RESEARCH_PLAN_2026-09-15.md",
    "research/procedures.md",
    "README.md",
]

# Commands carrying a placeholder rather than a real argument.
PLACEHOLDER = re.compile(r"[\[\]<>{}]|PATH|NAME|\.\.\.")


class _Parsed(Exception):
    """Raised once argparse has accepted the arguments."""


_MODULES: dict[str, object] = {}


def _module(rel: str):
    """Import a numbered script once and cache it.

    Using importlib rather than runpy matters: runpy re-executes the whole file
    for every command, which on this many commands takes minutes. Importing once
    and calling main() with a patched argv is the same test, far faster.
    """
    if rel not in _MODULES:
        name = Path(rel).stem
        spec = importlib.util.spec_from_file_location(name, REPO / rel)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            spec.loader.exec_module(mod)
        _MODULES[rel] = mod
    return _MODULES[rel]


def check(cmd: str) -> tuple[bool, str]:
    parts = cmd.split()
    rel = parts[0]
    if not (REPO / rel).exists():
        return False, f"no such script: {rel}"

    src = (REPO / rel).read_text()
    takes_args = "ArgumentParser" in src

    if not takes_args:
        # No argparse at all. The script accepts nothing, so the only way the
        # command can be wrong is if it was written with arguments. Do NOT call
        # main() here -- for these scripts that would run the whole analysis.
        extra = parts[1:]
        if extra:
            return False, f"script takes no arguments but was given {extra}"
        return True, ""

    try:
        mod = _module(rel)
    except Exception as e:
        return False, f"import failed: {type(e).__name__}: {e}"[:100]
    if not hasattr(mod, "main"):
        return True, "no main(); nothing to parse"

    real = argparse.ArgumentParser.parse_args

    def stop(self, *a, **k):
        real(self, *a, **k)
        raise _Parsed

    argv, err = sys.argv, io.StringIO()
    argparse.ArgumentParser.parse_args = stop
    try:
        sys.argv = parts
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            mod.main()
        return True, "main() never called parse_args"
    except _Parsed:
        return True, ""
    except SystemExit:
        msg = err.getvalue().strip().split("\n")[-1] if err.getvalue() else "rejected"
        return False, msg[:100]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"[:100]
    finally:
        argparse.ArgumentParser.parse_args = real
        sys.argv = argv


def main() -> int:
    found: dict[str, list[str]] = {}
    for doc in DOCS:
        p = REPO / doc
        if not p.exists():
            continue
        for c in re.findall(r"python3 (scripts/\S+\.py[^\n`]*)", p.read_text()):
            # Strip shell continuations and chaining: a documented line like
            # "python3 scripts/61_x.py && \" is one command plus shell syntax.
            c = re.split(r"\s*(?:&&|\|\||;|\|)\s*", c.strip())[0]
            c = re.split(r"\s+#", c)[0]          # drop trailing shell comments
            c = c.rstrip("\\").strip()
            if c:
                found.setdefault(c, []).append(doc)

    checked = skipped = bad = 0
    print(f"{'command':<70} result")
    print("-" * 96)
    for cmd in sorted(found):
        if PLACEHOLDER.search(cmd):
            skipped += 1
            continue
        ok, why = check(cmd)
        checked += 1
        if not ok:
            bad += 1
            print(f"{cmd[:68]:<70} REJECTED")
            print(f"{'':<70} {why}")
            print(f"{'':<70} in {', '.join(found[cmd])}")
    print("-" * 96)
    print(f"{checked} commands checked, {skipped} skipped as templates, {bad} rejected")
    if bad:
        print("\nFAIL — a reader following these documents literally would be "
              "stopped by the command above.")
        return 1
    print("\nPASS — every documented command is accepted by its own script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
