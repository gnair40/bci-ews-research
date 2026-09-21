#!/usr/bin/env python3
"""Records frames and reduces each one to N region averages.

Each region average is one channel, the same way each electrode's binned
activity is one channel in the neural data.

Exposure and white balance are FIXED. The automatic versions are compensators:
leave them on and the camera quietly cancels out the very degradation I am
trying to measure.

PIXELS PER CHANNEL IS THE SECOND CALIBRATION SETTING
----------------------------------------------------
Averaging N pixels into one channel divides that channel's noise by sqrt(N). The
first version of this file captured 480x320 and averaged 20x20 = 400 pixels per
channel, which made every channel twenty times quieter than a single pixel and
was half the reason the simulated rig decoded perfectly (see
scripts/72_rig_digital_twin.py and reports/RIG_DIGITAL_TWIN.md).

The defaults below capture 48x32 so that each channel is a 2x2 = 4 pixel block.
Together with the small modulation depth in stimulus.py this puts the rig at the
neural operating point. Raising the capture size back up will quietly make the
rig too good again.
"""
import argparse, time
import numpy as np
from picamera2 import Picamera2

ap = argparse.ArgumentParser()
ap.add_argument("--cols", type=int, default=24)
ap.add_argument("--rows", type=int, default=16)
ap.add_argument("--width", type=int, default=48)     # 48/24 = 2 px per side
ap.add_argument("--height", type=int, default=32)    # 32/16 = 2 px per side -> 4 px/channel
ap.add_argument("--fps", type=int, default=50)
ap.add_argument("--frames", type=int, default=15000)
ap.add_argument("--exposure", type=int, default=8000)   # microseconds
ap.add_argument("--gain", type=float, default=2.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

assert a.width % a.cols == 0 and a.height % a.rows == 0, \
    "frame size must divide evenly into the region grid"

cam = Picamera2()
cam.configure(cam.create_video_configuration(
    main={"size": (a.width, a.height), "format": "RGB888"},
    controls={"FrameRate": a.fps}))
cam.set_controls({"AeEnable": False, "AwbEnable": False,
                  "ExposureTime": a.exposure, "AnalogueGain": a.gain})
cam.start()
time.sleep(2)               # let the sensor settle before recording

rows, ts = [], []
try:
    for _ in range(a.frames):
        img = cam.capture_array("main")[:, :, 1].astype(np.float32)  # green
        r = img.reshape(a.rows, a.height // a.rows,
                        a.cols, a.width // a.cols).mean(axis=(1, 3))
        rows.append(r.ravel())
        ts.append(time.time())
finally:
    cam.stop()

np.save(a.out, np.asarray(rows, dtype=np.float32))
np.save(a.out.replace(".npy", "_t.npy"), np.asarray(ts))
print(f"wrote {a.out}  shape={np.asarray(rows).shape}")
