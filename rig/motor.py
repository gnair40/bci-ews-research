#!/usr/bin/env python3
"""
motor.py — turn the 28BYJ-48 stepper, for the GEOMETRY_ROTATION fault.

WHY A MOTOR AND NOT A SOFTWARE ROLL
-----------------------------------
scripts/72_rig_digital_twin.py models rotation by rolling the channel indices
around the grid. That is not what a physical rotation does: a real rotation also
blurs, crops the edges, and moves patches by fractions of a camera pixel. If the
rotation is imposed in software the fault is not a physical fault at all, which
defeats the purpose of having a rig.

So the stage turns. The motor also makes the rotation REPEATABLE and gives it a
severity ladder in real units -- steps -- instead of arbitrary ones.

WIRING (ULN2003 driver board to the Pi's 40-pin header)
    IN1 -> pin 11 (GPIO17)      VCC (5V)  -> pin 2
    IN2 -> pin 13 (GPIO27)      GND       -> pin 9
    IN3 -> pin 15 (GPIO22)
    IN4 -> pin 16 (GPIO23)
Never power the motor from the Pi's 3.3 V rail. Use the 5 V pin.

The 28BYJ-48 is geared 64:1 with 32 steps per motor revolution, so a full turn
of the output shaft is 4096 half-steps: about 0.088 degrees per step.

    python3 rig/motor.py --degrees 2          # rotate 2 degrees
    python3 rig/motor.py --degrees -2         # and back
    python3 rig/motor.py --steps 100 --delay 0.003

ALWAYS RETURN TO ZERO between conditions, and write the cumulative position in
the log. There is no encoder: if you lose count, the only recovery is to re-run
B-7 and re-aim.
"""
from __future__ import annotations

import argparse
import time

PINS = [17, 27, 22, 23]
STEPS_PER_REV = 4096
SEQ = [[1, 0, 0, 1], [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0],
       [0, 1, 1, 0], [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--degrees", type=float)
    g.add_argument("--steps", type=int)
    ap.add_argument("--delay", type=float, default=0.002,
                    help="seconds between half-steps; below ~0.0015 it stalls")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    steps = a.steps if a.steps is not None else \
        int(round(a.degrees * STEPS_PER_REV / 360.0))
    print(f"{steps} half-steps = {steps * 360.0 / STEPS_PER_REV:.3f} degrees")
    if a.dry_run:
        return 0

    try:
        import RPi.GPIO as GPIO
    except Exception:
        print("RPi.GPIO not available — this only runs on the Pi. "
              "Use --dry-run to check the arithmetic anywhere else.")
        return 1

    GPIO.setmode(GPIO.BCM)
    for p in PINS:
        GPIO.setup(p, GPIO.OUT, initial=0)
    try:
        direction = 1 if steps >= 0 else -1
        for i in range(abs(steps)):
            for p, v in zip(PINS, SEQ[(i * direction) % 8]):
                GPIO.output(p, v)
            time.sleep(a.delay)
    finally:
        for p in PINS:      # de-energise, or the coils cook and the stage drifts
            GPIO.output(p, 0)
        GPIO.cleanup()
    print("done; remember to record the cumulative position")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
