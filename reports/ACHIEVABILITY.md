# Achievability: is the information there at all?

**Reproduce:** `python3 scripts/26_achievability.py`

> Every threshold, state machine, dwell and hysteresis setting is stripped away. This asks only whether a single window's raw score can separate the early-warning interval from healthy recording. AUC 0.50 is chance.


## T11 — calibrate once baseline

| Detector | Early-warning AUC | p | Post-damage AUC | Verdict |
|---|---|---|---|---|
| `decoder_guard` | **0.491** | 0.046 | 0.668 | **at chance — no information** |
| | *by mode:* CHANNEL_DROPOUT 0.56; GAIN_DRIFT 0.53; GEOMETRY_ROTATION 0.50; NONE 0.47; RATE_LOSS 0.39 | | | |
| `distribution_shift` | **0.541** | 6.8e-20 | 0.705 | **at chance — no information** |
| | *by mode:* CHANNEL_DROPOUT 0.59; GAIN_DRIFT 0.51; GEOMETRY_ROTATION 0.43; NONE 0.52; RATE_LOSS 0.62 | | | |
| `mean_activity` | **0.514** | 0.0014 | 0.618 | **at chance — no information** |
| | *by mode:* CHANNEL_DROPOUT 0.54; GAIN_DRIFT 0.52; GEOMETRY_ROTATION 0.48; NONE 0.62; RATE_LOSS 0.51 | | | |
| `robust_dispersion` | **0.465** | 3.4e-15 | 0.487 | **at chance — no information** |
| | *by mode:* CHANNEL_DROPOUT 0.44; GAIN_DRIFT 0.48; GEOMETRY_ROTATION 0.44; NONE 0.47; RATE_LOSS 0.48 | | | |

## T11 — recent normal baseline

| Detector | Early-warning AUC | p | Post-damage AUC | Verdict |
|---|---|---|---|---|
| `decoder_guard` | **0.693** | 0 | 0.808 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.65; GAIN_DRIFT 0.79; GEOMETRY_ROTATION 0.76; NONE 0.36; RATE_LOSS 0.61 | | | |
| `distribution_shift` | **0.666** | 1.2e-303 | 0.775 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.68; GAIN_DRIFT 0.69; GEOMETRY_ROTATION 0.57; NONE 0.44; RATE_LOSS 0.73 | | | |
| `mean_activity` | **0.611** | 2e-137 | 0.688 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.73; GAIN_DRIFT 0.41; GEOMETRY_ROTATION 0.52; NONE 0.36; RATE_LOSS 0.80 | | | |
| `robust_dispersion` | **0.602** | 8.1e-117 | 0.657 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.59; GAIN_DRIFT 0.64; GEOMETRY_ROTATION 0.56; NONE 0.39; RATE_LOSS 0.62 | | | |

## T5 — recent normal baseline

| Detector | Early-warning AUC | p | Post-damage AUC | Verdict |
|---|---|---|---|---|
| `decoder_guard` | **0.707** | 0 | 0.820 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.75; GAIN_DRIFT 0.73; GEOMETRY_ROTATION 0.71; NONE 0.47; RATE_LOSS 0.64 | | | |
| `distribution_shift` | **0.661** | 7.2e-205 | 0.778 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.72; GAIN_DRIFT 0.69; GEOMETRY_ROTATION 0.58; NONE 0.40; RATE_LOSS 0.67 | | | |
| `mean_activity` | **0.612** | 8.5e-100 | 0.682 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.77; GAIN_DRIFT 0.40; GEOMETRY_ROTATION 0.51; NONE 0.45; RATE_LOSS 0.78 | | | |
| `robust_dispersion` | **0.620** | 3.1e-114 | 0.699 | information present |
| | *by mode:* CHANNEL_DROPOUT 0.65; GAIN_DRIFT 0.62; GEOMETRY_ROTATION 0.60; NONE 0.45; RATE_LOSS 0.61 | | | |

## How to read this

- **AUC at 0.50** means the score carries no information about the fault during the early-warning window. No amount of smoothing, thresholding or state machinery can recover information that is not present, so a negative result there is a **bound**, not a shortfall of effort.
- **A high post-damage AUC beside a chance early AUC** means the detector sees damage but cannot anticipate it. That is a *nowcast* — which is what the published instability measure already provides, and precisely what this project set out to improve on.
- **A high early AUC beside a failing benchmark** would mean the information is there and the failure is in the machinery — a fixable engineering problem rather than a limit of the data.