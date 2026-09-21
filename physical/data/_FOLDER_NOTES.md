# What lives in `physical/data/`

```
physical/data/
  onsets/          the drawn plans and MANIFEST.csv    COMMITTED
  raw/             the camera recordings               NOT committed (large)
  processed/       per-window arrays, table_meta.json  partly committed
  results/         the reports and their JSON          COMMITTED
  preferred_directions.npy   which channel is which    COMMITTED
  lag.json         the camera-behind-screen delay      COMMITTED
  dryrun/          fake recordings for testing         NEVER committed
```

## The rule about raw data

**Nothing ever modifies anything in `raw/`.** It is written once, by
`run_session.py`, and read for the rest of the project. Every analysis writes
to `processed/` or `results/` instead.

This is not bureaucracy. A recording that has been "cleaned up" cannot be
un-cleaned, and a result that depends on a cleaning step nobody wrote down
cannot be reproduced by anyone — including by the person who did it, three
months later.

## Why the plans are committed but the recordings are not

The recordings are hundreds of megabytes and GitHub is for code. The plans in
`onsets/` are a few hundred bytes each, and they are the thing that makes the
lead-time measurement checkable: each one records when the degradation was due
to start, and `MANIFEST.csv` records the checksum of that file and the moment
it was written. Anyone can confirm the plans still match their checksums, and
that they were written before the recordings.

Losing the recordings costs a week of re-recording. Losing the plans would mean
every recording that depends on them is unusable.

## `dryrun/`

Fake recordings, made by `physical/code/dryrun.py`, so that the analysis can be
tested before the apparatus exists. They are in a separate folder, they are
marked `SYNTHETIC` inside, and they are excluded from Git. **No number produced
from them belongs in the write-up.**


## `EXCLUSIONS.csv`

How a session is set aside **without deleting raw data**, which nothing here is
allowed to do.

```
folder,reason,excluded_at
s10_b34,screen slept; dark frames from 40 s onward,2026-10-04
```

`make_session_table.py` reads it and leaves those sessions out of every group
and every number. **A row with no reason is refused outright.** An exclusion
with no recorded reason is indistinguishable from dropping a session because of
how it turned out, and the protocol only permits discards for recorded
mechanical reasons.

It is committed, because which sessions were set aside and why is part of the
result.
