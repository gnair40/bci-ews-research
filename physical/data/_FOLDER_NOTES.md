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
