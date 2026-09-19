#!/usr/bin/env python3
"""
daily_session.py — the unattended arm: record a few blocks a day, for weeks.

WHAT THIS ARM IS FOR
--------------------
Every fault in this project is something I invented and then applied. Nobody has
checked whether real degradation looks anything like an invented ramp. This arm
answers that by leaving the rig completely alone for six to ten weeks and
recording whatever drift it produces on its own -- dust, thermal cycling,
mechanical creep, LED ageing, whatever the room does to it.

Prediction P-R7 is judged on these recordings: natural drift will resemble at
least one of the four designed fault modes at a rate above chance (25%). A
negative answer there is the more interesting one, because it would say that
1,850 episodes of carefully constructed ground truth do not resemble what
actually goes wrong -- a finding about how fault benchmarks get built, including
this project's own.

RUN IT FROM CRON, NOT BY HAND
-----------------------------
    crontab -e

then add:

    0 3 * * * /usr/bin/python3 /home/pi/bci-ews-research/rig/daily_session.py >> /home/pi/rig_cron.log 2>&1

03:00 is deliberate: ambient conditions are most stable and nobody will open the
box. An arm whose whole point is that nothing was touched is ruined by somebody
tidying up at noon.

THE SESSION NUMBER COMES FROM THE DATE, NOT FROM A COUNTER
----------------------------------------------------------
Session number is days since --start-date. A counter in a file would drift out
of step the first time a run is missed or repeated, and this arm runs unattended
for weeks, so missed runs are certain. Deriving it from the calendar means a
power cut costs one session and nothing else: the gap is visible in the data
instead of silently renumbering everything after it.

THE ONE RULE
------------
Change nothing while this arm is running. No cleaning, no refocusing, no
re-seating the ribbon, no adjusting the screen. If something IS changed, record
it in research/research_log.md with the date -- an undocumented intervention
midway through a six-week drift makes the whole arm uninterpretable, and there
is no way to detect it afterwards.

Usage:
    python3 rig/daily_session.py                      # normal cron use
    python3 rig/daily_session.py --dry-run            # show what it would do
    python3 rig/daily_session.py --blocks 6
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

RIG = Path(__file__).resolve().parent
START_DEFAULT = "2026-10-01"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start-date", default=START_DEFAULT,
                    help="day 1 of the arm, YYYY-MM-DD")
    ap.add_argument("--blocks", type=int, default=4,
                    help="blocks per day; 4 x 5 min = 20 min")
    ap.add_argument("--depth", type=float, default=0.00211,
                    help="MUST match the value B-7 settled on")
    ap.add_argument("--lag", type=float, default=0.0,
                    help="the value B-5 measured")
    ap.add_argument("--root", default="data/raw_rig")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    start = dt.date.fromisoformat(a.start_date)
    today = dt.date.today()
    session = (today - start).days + 1
    if session < 1:
        print(f"{today} is before the start date {start}; nothing to do")
        return 0

    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== {stamp} — natural-drift arm, day {session} "
          f"({a.blocks} blocks) ===")

    ok = failed = 0
    for b in range(1, a.blocks + 1):
        cmd = [sys.executable, str(RIG / "run_block.py"),
               "--session", str(session), "--blocknum", str(b),
               "--depth", str(a.depth), "--lag", str(a.lag),
               "--fault", "NATURAL", "--severity", "0",
               "--note", f"unattended day {session}",
               "--root", a.root]
        if a.dry_run:
            cmd.append("--dry-run")
        if subprocess.run(cmd).returncode == 0:
            ok += 1
        else:
            failed += 1
            # A failed block must not stop the arm. A six-week record with one
            # gap is still a six-week record; a six-week record that stopped
            # silently on day 9 is nine days of data nobody noticed losing.
            print(f"  block {b} FAILED — continuing")

    print(f"day {session}: {ok} recorded, {failed} failed")
    if failed:
        print("Check rig/blocklog.csv and the camera before tomorrow's run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
