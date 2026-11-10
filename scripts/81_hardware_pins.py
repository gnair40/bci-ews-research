#!/usr/bin/env python3
"""
81_hardware_pins.py
===================
Do the documents agree with the code about which physical pin each wire goes to?

WHY THIS EXISTS
---------------
On 10 November 2026 the repository contained two different stepper-motor
pinouts:

    physical/docs/04_BUILD.md   IN1-IN4 -> GPIO 6, 13, 19, 26
    rig/motor.py                PINS = [17, 27, 22, 23]

`rig/motor.py` is the only code here that drives the motor, so the build
manual's table was wrong, and anyone who wired the board by it would have had
a motor that never turned — with nothing on screen to say why, because the
code would energise four pins that had nothing attached to them.

All twelve other gates passed with that contradiction sitting in the tree. They
compare numbers to the data they came from, or documents to other documents;
not one of them looks at a GPIO number. This is the same failure this project
has logged repeatedly — a value correct where it was written and wrong where it
was used — but it is the first instance where acting on the wrong value means
rebuilding hardware rather than rerunning a script.

WHAT IT CHECKS
--------------
For each wiring table in the documents, the pin numbers must match the pin
numbers the corresponding program actually drives. The code is the authority:
it is what runs. A document that disagrees is the thing that gets corrected.

It also checks the BCM-to-physical-pin mapping in those tables against the real
Raspberry Pi 40-pin header, because the old table mixed the two numbering
schemes under one heading, and "GPIO 13" and "physical pin 13" are different
holes.

WHAT IT CANNOT DO
-----------------
It cannot tell you the wire is in the right hole. It checks that the
instructions and the program agree, which is the part that can be checked from
here. The soldering-iron end of the problem is what `bench.py` is for.

Usage: python3 scripts/81_hardware_pins.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The Raspberry Pi 40-pin header: BCM GPIO number -> physical pin number.
# Only the GPIOs this project uses need to be here, but the full map is cheap
# and means a future wiring table can be checked without editing this list.
BCM_TO_PHYSICAL = {
    2: 3, 3: 5, 4: 7, 14: 8, 15: 10, 17: 11, 18: 12, 27: 13, 22: 15,
    23: 16, 24: 18, 10: 19, 9: 21, 25: 22, 11: 23, 8: 24, 7: 26,
    5: 29, 6: 31, 12: 32, 13: 33, 19: 35, 16: 36, 26: 37, 20: 38, 21: 40,
}


def code_pins(rel: str, pattern: str) -> list[int] | None:
    """The pin numbers a program actually drives."""
    p = REPO / rel
    if not p.exists():
        return None
    m = re.search(pattern, p.read_text(errors="replace"))
    if not m:
        return None
    return [int(x) for x in re.findall(r"\d+", m.group(1))]


def doc_rows(rel: str, marker: str, n: int) -> list[tuple[int, int]] | None:
    """(BCM, physical) pairs from the wiring table that follows `marker`."""
    p = REPO / rel
    if not p.exists():
        return None
    text = p.read_text(errors="replace")
    i = text.find(marker)
    if i < 0:
        return None
    rows = re.findall(r"\|\s*IN\d\s*\|\s*GPIO\s*(\d+)\s*\|\s*pin\s*(\d+)\s*\|",
                      text[i:i + 2000])
    return [(int(a), int(b)) for a, b in rows[:n]]


def main() -> int:
    print("=" * 72)
    print("hardware pins — do the wiring tables match the code that drives them?")
    print("=" * 72)
    problems: list[str] = []

    # ---- the stepper ------------------------------------------------------
    print("\n1. STEPPER MOTOR — rig/motor.py vs physical/docs/04_BUILD.md")
    pins = code_pins("rig/motor.py", r"PINS\s*=\s*\[([^\]]+)\]")
    rows = doc_rows("physical/docs/04_BUILD.md", "ULN2003", 4)

    if pins is None:
        problems.append("rig/motor.py: could not read PINS")
        print("   FAIL  cannot find PINS = [...] in rig/motor.py")
    elif rows is None:
        problems.append("04_BUILD.md: no stepper wiring table found")
        print("   FAIL  no IN1-IN4 wiring table in 04_BUILD.md")
    elif len(rows) != len(pins):
        problems.append(f"04_BUILD.md lists {len(rows)} motor wires, "
                        f"rig/motor.py drives {len(pins)}")
        print(f"   FAIL  {len(rows)} rows documented, {len(pins)} pins driven")
    else:
        doc_bcm = [a for a, _ in rows]
        if doc_bcm != pins:
            problems.append(f"stepper: 04_BUILD.md says GPIO {doc_bcm}, "
                            f"rig/motor.py drives GPIO {pins}")
            print(f"   FAIL  documented GPIO {doc_bcm}")
            print(f"         code drives   GPIO {pins}")
            print("         The code is what runs. Correct the document, and")
            print("         remember the board has already been wired by it.")
        else:
            print(f"   ok    GPIO {pins} in both")

    # ---- the temperature sensor -------------------------------------------
    print("\n2. TEMPERATURE SENSOR — rig/logtemp.py vs physical/docs/04_BUILD.md")
    dflt = code_pins("rig/logtemp.py", r'"--pin",\s*type=int,\s*default=(\d+)')
    doc = re.search(r"\|\s*DATA\s*/\s*OUT\s*\|\s*GPIO\s*(\d+)\s*\|\s*pin\s*(\d+)\s*\|",
                    (REPO / "physical/docs/04_BUILD.md").read_text(errors="replace"))
    if dflt is None:
        print("   info  no --pin default found in rig/logtemp.py; skipping")
    elif not doc:
        problems.append("04_BUILD.md: no DHT22 DATA row found")
        print("   FAIL  no DHT22 DATA wiring row in 04_BUILD.md")
    elif int(doc.group(1)) != dflt[0]:
        problems.append(f"DHT22: 04_BUILD.md says GPIO {doc.group(1)}, "
                        f"rig/logtemp.py defaults to GPIO {dflt[0]}")
        print(f"   FAIL  documented GPIO {doc.group(1)}, "
              f"code defaults to GPIO {dflt[0]}")
    else:
        print(f"   ok    GPIO {dflt[0]} in both")

    # ---- BCM vs physical, in every table ----------------------------------
    print("\n3. BCM vs PHYSICAL — are the two numbers in each row consistent?")
    # This section keeps its own tally. The first version tested the shared
    # `problems` list, so whenever section 1 failed this section printed
    # nothing at all -- the reader saw a heading with no result under it and
    # no way to tell "checked and fine" from "never ran".
    checked = 0
    here: list[str] = []
    text = (REPO / "physical/docs/04_BUILD.md").read_text(errors="replace")
    for bcm, phys in re.findall(r"\|\s*GPIO\s*(\d+)\s*\|\s*pin\s*(\d+)\s*\|", text):
        bcm, phys = int(bcm), int(phys)
        checked += 1
        want = BCM_TO_PHYSICAL.get(bcm)
        if want is None:
            here.append(f"GPIO {bcm} is not a GPIO on the 40-pin header")
            print(f"   FAIL  GPIO {bcm} is not on the header at all")
        elif want != phys:
            here.append(f"GPIO {bcm} is physical pin {want}, "
                        f"not pin {phys} as documented")
            print(f"   FAIL  GPIO {bcm} is physical pin {want}, documented as {phys}")
    if not checked:
        print("   info  no GPIO/pin pairs found to check")
    elif not here:
        print(f"   ok    {checked} row(s), every GPIO on its real physical pin")
    problems += here

    print("\n" + "=" * 72)
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        print("\nA wrong pin number is not a typo. It is a wire in the wrong")
        print("hole, found hours later, with nothing on screen to explain it.")
        return 1
    print("PASS — every wiring table matches the code that drives it, and")
    print("       every GPIO is on the physical pin the table claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
