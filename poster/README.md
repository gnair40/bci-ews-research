# The trifold poster

**Draft of 12 November 2026.** A 48 × 36 inch science-fair trifold in three
panels: left 12 in, centre 24 in, right 12 in.

![The three panels side by side](preview/trifold.png)

The editable poster lives on a design canvas:
<https://claude.ai/artifact/FRdqcb8LDn5hR2nhjJTEy3> (private until shared from
its Share menu). Everything needed to rebuild it is in this folder.

---

## What is on it, and what is not

The poster presents two validations of one monitor, and neither is secondary.

| | Computational validation | Physical validation |
|---|---|---|
| Status | complete | specified, coded, preregistered; **not built** |
| What the poster shows | charts drawn from stored results | the same charts, **empty** |
| Colour | blue, solid | orange, hatched, dashed edge |

**There is no physical measurement anywhere on this poster, because none
exists.** Every chart of the physical phase carries the words *awaiting
measurement* on its face and contains only things fixed before any recording:
the zero line, the 0.1-per-hour budget, the severity levels, the decision
rates, the planned sample sizes. The one curve drawn inside a planned chart
(Fig. 6, right) is the rule of three, `3 ÷ hours`, which is arithmetic and not
a result.

Grey dashed boxes with a camera glyph are slots for photographs that have not
been taken. They are grey on purpose, so a photo slot cannot be mistaken for
either kind of chart.

## The three visual states

| State | Looks like | Means |
|---|---|---|
| **Measured** | solid blue marks | drawn from `data/processed/` by script |
| **Planned** | orange hatch, dashed edge, "awaiting measurement" | axes and reference lines from the frozen preregistration; no data |
| **Photo slot** | grey dashed box with a camera | a photograph to take after the build |

## Where every number comes from

Nothing on the computational charts is typed.

```
python3 poster/build_poster_data.py
```

reads the stored results, recomputes what each chart plots, and **refuses to
write** if a recomputed value disagrees with the headline the repository
already publishes for it. It prints one line per check; all of them must say
`ok`. Its output is `poster_data.json`.

```
python3 poster/build_poster.py
```

assembles the three panels from that file into `canvas/project/`. Sentences
that need a measured number take it from `poster_data.json`, so the text cannot
drift away from the data it summarises.

Numbers fixed by the preregistration (0.1 per hour, 101 sessions, 36.1°) are
design constants and are written in place.

| File | What it is |
|---|---|
| `build_poster_data.py` | recomputes and checks every plotted value |
| `poster_data.json` | the checked values, each with the file it came from |
| `charts.py` | the charts, each in a measured and a planned form |
| `build_poster.py` | the words, tables, diagrams and layout |
| `canvas/project/` | the built panels, exactly as published to the canvas |
| `preview/` | pictures of the panels, for reading without the canvas |

## The figures

| Fig. | Shows | State |
|---|---|---|
| 1 | one archived episode with onset, failure and warning marked | measured |
| 2 | the monitor's four named components | diagram |
| 3 | the two validations side by side: inputs, outputs, what each establishes | diagram |
| 4 | the apparatus signal chain | diagram of a specification |
| 5 | lead time | measured, and planned |
| 6 | false-alarm rate and the silence gate | measured, and planned |
| 7 | detection against false alarms per hour | measured, and planned |
| 8 | detection by fault type, and by type and severity | measured, and planned |
| 9 | monitor score against decoding performance | measured, and planned |
| 10 | how often the monitor decides | measured, and planned |
| 11 | the apparatus, side view | diagram of a specification |
| 12 | the experimental workflow, with what is done and what is not | diagram |
| 13 | apparatus configurations (P-7) | planned |

Fig. 1 shows the first test episode whose lead time equals the median. It was
chosen by that rule and not by eye, because the typical case is a late warning
and a hand-picked example would have been an early one.

## When physical results exist

This part is **not yet automatic**, and that is deliberate.

Each planned chart has a measured twin in `charts.py` (`lead_dots`,
`fa_measured`, `dfa_measured`, `scatter_measured`, `decision_measured`). Turning
a planned chart into a measured one means reading the real results from
`physical/data/results/` and passing them to the matching function. That small
adapter has not been written, because its inputs do not exist, and writing it
against the synthetic dry-run output would leave fake numbers one command away
from a poster.

Until then there are two honest ways to fill a slot:

1. drop the figure that `physical/code/figures.py` produces from real
   recordings into the slot on the canvas, or
2. ask for the adapter to be written once the first real results are in.

Either way, **a chart produced by `dryrun.py` must never go on the poster.**
Those figures carry a "NOT DATA" watermark for exactly this reason.

## Things on the poster that are the researcher's to confirm

These were chosen so that a draft could exist. None is settled.

- **The title.** Taken from the September research plan.
- **The category and fair name**, shown as `[CATEGORY]` and `[FAIR AND YEAR]`.
- **The board size**, 48 × 36 inches. A different board changes the layout.
- **Which six quantities** form the measured-and-planned wall, and their order.
- **The wording of the conclusions**, including the computational one.
- **Type and colour.** Source Serif 4 for headings, IBM Plex Sans for text.
  The physical-phase document was set in Times New Roman at the researcher's
  request; the poster uses a sans-serif body for reading at a distance.

## Known limits of this draft

- The panels were checked by rendering them locally with the same fonts. They
  were not checked on a printed sheet, and small type (13 pt inside charts)
  should be judged on paper before printing.
- The apparatus drawing (Fig. 11) shows the computer outside the enclosure. The
  repository does not fix where it sits, or the display-to-camera distance, and
  the caption says so.
- Reference author lists are abbreviated to the first author, as in the
  September plan.
