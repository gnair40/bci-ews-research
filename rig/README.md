# Rig programs

The three programs the physical experiment runs on. They are written out in full
in `research/EXPERIMENTAL_PROCEDURES.md`, Phase 8, with the reasoning; these are
the same files, extracted so they can be run and tested.

| File | Runs on | What it does |
|---|---|---|
| `stimulus.py` | The machine driving the screen | Shows a grid of patches whose brightness encodes a heading. Logs the true heading for every frame. |
| `capture.py` | The Raspberry Pi | Records frames and reduces each to one average per image region. Each region average is one channel. |
| `to_mat.py` | Either | Converts a recording plus the stimulus log into the three `.mat` files the analysis already reads. |
| `run_block.py` | The Pi | Records ONE block end to end — stimulus, capture, conversion — and logs every setting to `blocklog.csv`. The command you type most. |
| `run_batch.py` | The Pi | Works through a plan file of many blocks unattended, skipping any already recorded. For the 265-block drift sweep. |
| `bench.py` | Either* | The bench checks from the build manual: `darkframe`, `lag`, `dither`, `margin`. |
| `motor.py` | The Pi | Turns the stage for the rotation fault, in real units. |
| `logtemp.py` | The Pi | Temperature and humidity, so warmth and drift stay separable. Never fatal if the sensor is missing. |

\* `bench.py darkframe` needs the camera; the other three read files already
recorded and run anywhere.

`stimulus.py` needs pygame and a display. `capture.py` needs picamera2 and a
camera, so it only runs on the Pi. Everything else needs only numpy and scipy
and runs anywhere.

**Full documentation, with a fallback for every failure mode and the complete
source inline, is in `research/RIG_CODE.md`.**

**Checked on 14 September 2026, without hardware:** a simulated capture was run
through `to_mat.py` and loaded with the unmodified archived loader. 3,000 bins and
30 trials came back, the MATLAB one-based indices converted correctly, trials
abutted with no gap or overlap, and the heading recovered from the decoder's own
`intended_direction()` matched what the stimulus logged to within float32
precision (2e-6 degrees).

What that check does **not** cover, because it needs hardware: the camera itself,
the display-to-camera lag of Procedure 63, exposure and gain settings, and
anything optical.
