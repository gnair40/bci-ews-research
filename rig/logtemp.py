#!/usr/bin/env python3
"""
logtemp.py — read the DHT22 temperature and humidity sensor.

WHY BOTHER
----------
A CMOS sensor's dark current roughly doubles every 6-8 degrees C, so a warm room
looks like a drifting array. If the rig's risk signal rises over an afternoon
and the temperature also rose over that afternoon, there is no way to tell them
apart after the fact. Logging it costs nothing and makes that separable.

run_block.py calls this with --once after every block and writes the result into
rig/blocklog.csv. It is deliberately never fatal: a missing sensor must not stop
a recording.

    python3 rig/logtemp.py --once        # prints "temp_c,humidity"
    python3 rig/logtemp.py --watch 60    # a reading every 60 s to rig/temp.csv

IF YOU DO NOT HAVE THE SENSOR
-----------------------------
Skip it. Everything still runs; the temperature column stays empty. But write in
the log that it is missing, so a future you does not read empty cells as zero.
A phone thermometer photographed at the start and end of each session is a poor
substitute that is still better than nothing.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

RIG = Path(__file__).resolve().parent


def read_once(pin: int) -> tuple[float, float] | None:
    """One reading, or None. The DHT22 fails a fraction of reads by design."""
    try:
        import board
        import adafruit_dht
    except Exception:
        return None
    try:
        dht = adafruit_dht.DHT22(getattr(board, f"D{pin}"))
        for _ in range(5):
            try:
                t, h = dht.temperature, dht.humidity
                if t is not None and h is not None:
                    return float(t), float(h)
            except RuntimeError:
                time.sleep(2.0)     # a failed read is normal; retry
        return None
    except Exception:
        return None
    finally:
        try:
            dht.exit()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin", type=int, default=4, help="BCM pin, GPIO4 = header pin 7")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", type=float, default=0.0, help="seconds between readings")
    ap.add_argument("--out", default=str(RIG / "temp.csv"))
    a = ap.parse_args()

    if a.once or not a.watch:
        r = read_once(a.pin)
        print(f"{r[0]:.1f},{r[1]:.1f}" if r else ",")
        return 0

    new = not Path(a.out).exists()
    with open(a.out, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "temp_c", "humidity"])
        try:
            while True:
                r = read_once(a.pin)
                w.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"),
                            f"{r[0]:.1f}" if r else "", f"{r[1]:.1f}" if r else ""])
                f.flush()
                time.sleep(a.watch)
        except KeyboardInterrupt:
            print(f"\nstopped; wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
