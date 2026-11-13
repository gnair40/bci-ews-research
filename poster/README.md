# The trifold poster

A science-fair trifold: left 12 in, centre 24 in, right 12 in. Drafts 1 to 3
are 36 inches tall. **Drafts 4 and 5 are 48 inches wide by 48 inches tall, and
Draft 5 is the current one.** The canvas holds **five drafts on five pages**,
so the designs can be compared side by side:
<https://claude.ai/artifact/FRdqcb8LDn5hR2nhjJTEy3> (private until shared from
its Share menu).

| Page | What it is | Status |
|---|---|---|
| **Draft 1** | the first design: thirteen figures, a measured chart beside an empty template for each quantity | kept as a record; type too small to read |
| **Draft 2** | "the project in one minute": a dark band in the centre, the method prominent, data at the side | superseded |
| **Draft 3** | the data and its analysis in the centre, the discussion on the right | superseded |
| **Draft 4** | 48 × 48 in. First half: the system and its two validations, each beside its own diagrams, code and photo spaces. Second half: data and analysis, then the discussion | superseded |
| **Draft 5** | Draft 4 with a new title area and, under it, a light-blue introduction in plain language: the problem, why it matters, what this project did and found | **current** |

![Draft 5](preview/draft5.png)

Earlier drafts: [Draft 1](preview/draft1.png), [Draft 2](preview/draft2.png),
[Draft 3](preview/draft3.png), [Draft 4](preview/draft4.png).

---

## How Draft 5 is organised

| Where | Sections | Figures |
|---|---|---|
| **Centre, top** | **Title area** with a drawing of the signal path (electrodes, decoder, cursor, and the monitor watching the recorded activity). Then the **Introduction**, on light blue, in three numbered frames | 1 |
| **Left panel** | Abstract (top-left), Purpose, Hypothesis / Engineering goal, The system, What is measured, **Computational validation** | 2 to 5 |
| **Centre, left half** | **Physical validation** (bench, wiring, photo spaces, acceptance gates), How the bench result will be judged | 6 to 10 |
| **Centre, right half** | **Results and data** (four charts, the data table), **Analysis** | 11 to 16 |
| **Right panel** | **Discussion** with the decision-rate chart, How the two validations relate, Limitations, Broader significance, Future directions, Conclusion, References | 17 to 19 |

### The introduction, frame by frame

Each frame's heading line says how far its claim goes.

| Frame | Heading line | Pictures | What it says |
|---|---|---|---|
| **1** | The problem: *established science* | a schematic of one electrode among neurons, at fitting and weeks later; the real 142-day series (Fig. 1) | a decoder is fitted to one day's recording, the recording keeps changing, and nothing tells the user |
| **2** | Why it matters: *not yet shown* | three timelines of the same repair; the four outcomes of a warning | the repair can be timed by schedule, after failure, or by a warning; a warning only helps if it is trusted |
| **3** | This project: *shown on archived data* | the four headline numbers | what earlier work measured, what this project measured, and what is not shown or claimed |

The opening sentence is the real example: one decoder, left unchanged, worked
for about two months and then failed (Fig. 1). In the stored series the error
stays between 18.5° and 36.2° through day 57, is 64.7° on day 69, 21.8° on
day 93, and 95.7° to 121.4° from day 100. The failure level drawn is 45.3°.

### What moved to make room, and where it went

Draft 4 filled its 48 inches. Nothing was removed from the board.

| From | To |
|---|---|
| Introduction and Why it matters (left panel) | the light-blue introduction |
| the four headline numbers (results) | the light-blue introduction, frame 3 |
| Computational validation (centre) | left panel |
| How the bench result will be judged (right panel) | under Physical validation |
| the decision-rate chart (results) | beside the discussion point that cites it |
| "Also measured" (a caption under the data table) | its own discussion point |

Every section's wording comes from `build_draft4.py`, which `build_draft5.py`
imports, so the text was moved, not retyped. The new sentences are the ones in
the light-blue section.

## How Draft 4 was organised

The centre panel is laid out as two 12 inch columns, so the board reads as
four columns from left to right. Columns 1 and 2 are the first half (what the
system is and how it was tested). Columns 3 and 4 are the second half (what
was found and what it means).

| Column | Where | Sections | Figures |
|---|---|---|---|
| **1** | left panel | Abstract (top-left), Introduction, Why it matters, Purpose, Hypothesis / Engineering goal, The system, What is measured | 1 to 3 |
| **2** | centre, left half | **Computational validation** (workflow, real code, real output), then **Physical validation** (bench drawing, two wiring diagrams, photo spaces, acceptance gates) | 4 to 9 |
| **3** | centre, right half | **Results and data** (four numbers, four charts, the data table), **Analysis** (two charts) | 10 to 16 |
| **4** | right panel | **Discussion**, How the two validations relate, How the bench result will be judged, Limitations, Broader significance, Future directions, Conclusion, References | 17 to 19 |

Computational material is marked in blue with a "complete" tag. Physical
material is marked in orange with a "preregistered, not built" tag. The two
never share a figure.

What the taller board brought back from earlier drafts: the monitor's four
components, the definition of lead time on a real episode, the real code and
verifier output, the five acceptance gates, the list of seven experiments with
their variables, the secondary hypothesis, and a side-by-side account of what
each validation can and cannot establish.

## How Draft 3 was organised

| Panel | Sections |
|---|---|
| **Left** | Abstract (top-left), Introduction, Why it matters, Purpose, Hypothesis / Engineering goal, Materials and methods |
| **Centre** | Title, The project in one minute, **Results and data**, **Analysis** |
| **Right** | **Discussion**, What is shown and what is not, Conclusion, Next steps, Pictures and hardware, References |

The centre carries six real charts and the four numbers they support. The
method is one compact block on the left. Colour is the first draft's: white,
ink, blue for what was measured, orange for what is still to be measured.
There is no dark band and no yellow.

### Why each draft was replaced

- **Draft 1 to Draft 2.** The type was too small and the board was crowded.
  The size check below counts 625 pieces of text under 24 pt in Draft 1.
- **Draft 2 to Draft 3.** The researcher's review: the method took the centre
  and the data and analysis were pushed to one side, and the navy band and
  yellow highlighter did not fit the rest of the board.
- **Draft 3 to Draft 4.** The researcher's brief: a larger board whose first
  half introduces the system and explains both validations with real project
  material placed beside the explanation it supports, whose second half holds
  the data, results and analysis, and whose right-hand panel is for discussion
  and interpretation. Nothing was to be shortened only to make it fit.
- **Draft 4 to Draft 5.** The researcher's brief: before a judge meets the
  method, the hardware or the data, a prominent light-blue section under the
  title should say what the problem is, why it matters and how the project
  addresses it, as a story with pictures; and the title area, which felt
  empty, should be composed with a meaningful drawing.

## The size rule

**Drafts 2 and 3: nothing is smaller than 24 pt** (32 px at 96 px per inch),
including axis numbers, captions and labels inside diagrams.

**Drafts 4 and 5 have two sizes, both set by the researcher.** Paragraphs and
headings are 24 pt or larger. Small text may go down to **20 pt** (27 px) and
no further. The 20 pt size is used for: figure captions, axis numbers
and labels inside charts and diagrams, table cells, the code and output
blocks, the one-line descriptions under the workflow steps and under the four
large numbers, the pin lists, the reference list, and the one-line note on
when the predictions were frozen. The researcher's answer named "captions and
axis labels"; the rest of that list is an extension of it and is hers to
accept or push back up.

It is checked by program, not by eye:

```
python3 poster/render_check/preview.py
node poster/render_check/measure.js poster/render_check/out draft5
```

The second command renders each panel, measures every piece of text (including
text inside charts, after scaling), and fails if any is under the floor, if a
panel overflows its height, or if anything runs past a panel's right edge. For
Drafts 4 and 5 it also prints how many pieces of text sit between 20 and 24 pt
(410 on Draft 4, 432 on Draft 5). It cannot tell a paragraph from a caption, so the
24 pt rule for paragraphs rests on the builder, which has only two sizes. It
needs Node with Playwright.

The program does not catch labels that collide. Those were found by looking at
the rendered panels at full size, and are listed in the research log.

## What is real and what is not (Draft 5)

Figure numbers are Draft 5's. Draft 4 has the same items under its own numbers.

| On the board | Status |
|---|---|
| Charts (Figs 1, 3, 11 to 14, 16, 17) | **real**, drawn from `data/processed/` by script |
| The four large numbers and the data table (Fig. 15) | **real**, same source |
| The title drawing and the two drawings in the introduction | **schematics**, drawn for the poster. The one of an electrode among neurons is labelled "schematic, not to scale"; it shows the four causes listed in [7] and is not a picture of any recording |
| Code (Fig. 5) | **real**: six lines quoted from `scripts/21_score_report.py`. The build stops if those lines are no longer in that file |
| Output (Fig. 5) | **real**: the last line each of the two named commands prints, re-run and compared on 12 November 2026 |
| Wiring diagrams (Figs 7, 8) | **real**: the repository's own `physical/figures/wiring-stepper.svg` and `wiring-dht22.svg`, with their small labels removed and large ones added. Pin numbers are the ones `rig/motor.py` and `rig/logtemp.py` use |
| Monitor and workflow diagrams (Figs 2, 4) | drawings of what the code does |
| Bench drawing (Fig. 6) | a drawing of a **specification**; nothing is built |
| Three photographs and one screenshot | **grey placeholders**, labelled "to add" |
| Acceptance gates (Fig. 9), the verdict (Fig. 10), the conclusion box | **blanks**; there is no physical measurement |
| Experiment list (Fig. 19) | **planned** sizes from the preregistration; "none recorded yet" |

## Where every number comes from

```
python3 poster/build_poster_data.py
```

recomputes what each chart plots and **refuses to write** if a value disagrees
with the headline the repository already publishes for it (45 checks).

```
python3 poster/build_draft5.py
```

assembles Draft 5 (`build_draft4.py`, `build_draft3.py` and `build_draft2.py`
do the same for theirs). Sentences that need a measured number take it from
`poster_data.json`.

| File | What it is |
|---|---|
| `build_poster_data.py` | recomputes and checks every plotted value |
| `poster_data.json` | the checked values, each with the file it came from |
| `charts.py` | the charts |
| `build_draft5.py` | Draft 5: the title area, the introduction, and the new arrangement |
| `build_draft4.py` | Draft 4, and every section's wording, which Draft 5 reuses |
| `build_draft3.py` | Draft 3 |
| `build_draft2.py` | Draft 2, and the components Drafts 2 and 3 share |
| `assets/`, `assets.json` | the two relabel-ready wiring drawings, and where they live on the canvas |
| `canvas/project/` | every artboard exactly as published, and the canvas index |
| `render_check/` | the fit-and-size check |
| `preview/` | one picture per draft |

Draft 1 has no builder here. Its three files in `canvas/project/` (`D1-*`) are
the first design exactly as published, restored from the commit that recorded
it (`68f2f30`), where its builder can also be found.

## What other people's work is cited, and what was checked

Each statement about outside work was looked up on 12 November 2026.

| Ref | Used for | Checked |
|---|---|---|
| [1] Pun et al., *Communications Biology* 7 (2024) | the dataset; a decoder left fixed for 142 days; the correlations r = 0.93 and 0.72 | found; abstract confirms both correlations |
| [2] Wilson et al., *Nature Biomedical Engineering* (2025) | decoders often need daily recalibration; the device cannot be used freely during it; automatic correction | found; wording taken from the paper |
| [3] Armour et al., *Am. J. Public Health* 106 (2016) | nearly 5.4 million people in the United States live with paralysis | found |
| [4] Sendelbach & Funk, *AACN Adv. Crit. Care* 24 (2013) | 72 to 99% of hospital monitor alarms are false | found **as reported** in a federal patient-safety report; the paper itself was not opened |
| [5] Ahrens, *Smoke Alarms in U.S. Home Fires*, NFPA (2015) | nuisance alarms are the leading reason smoke alarms are disconnected | found in the NFPA fact sheet |
| [6] Karpowicz et al., *Nature Communications* 16 (2025) | automatic correction of drift | found |
| [7] Perge et al., *J. Neural Eng.* 10, 036004 (2013) | why recordings change: array movement, tissue reaction, material degradation, and changes in the neurons' own firing | **read** on 12 November 2026 in the open-access copy. The introduction lists the first three (and external connector problems, not drawn); the abstract attributes 85% of within-day rate changes to physiological mechanisms. The study is about changes within a day |

**Three things that could not be confirmed, and so are not on the board:**

- *That home fires are about half as deadly where a smoke alarm works.* A
  search summary attributes this to editions of the NFPA report cited as [5],
  but the report itself could not be opened from here (the sites are outside
  what this session may reach). It would have been a good example of an early
  warning that works, and it is left off until someone reads the report.
- *Swanson et al. (2026)*, the recalibration review in the September
  bibliography. A web search did not find it. Its DOI does resolve to the
  publisher's site, but the page could not be opened from here, so its title
  and authors are unconfirmed. **Check it before the December plan.**
- The claim that many potential users would not accept daily retraining. It is
  repeated in the literature, but the survey it is attributed to could not be
  confirmed to contain it.

**"No published lead time or false-alarm rate was found."** That sentence is a
statement about a search, not a proof of absence. A targeted search for a
decoder-health monitor reporting either number returned none; the closest
work, [1], says such a monitor would be useful and reports a correlation.

## Why "early warning" is argued the way it is

The intuitive argument is that preventing a failure beats repairing one. The
evidence supports something narrower. In fields that rely on alarms, a warning
that is late or often wrong is not merely less useful, it gets ignored or
switched off [4, 5]. So the case for a decoder-health monitor cannot rest on
"prevention is better". It has to rest on two measured numbers: how early, and
how often wrong. That is the gap the project addresses, and its own result so
far is that the monitor does not pass.

Draft 5 draws this as three ways to time the same repair. **On a schedule:**
recalibrate every day, which is often done now and pauses use [2]. **After
failure:** control is lost first. **When warned:** repair only when needed and
before control is lost. A warning does not stop the drift. It changes when the
repair happens. The third way is the goal and is marked "not yet shown".

The first plan for that drawing had only two rows, "today: the repair follows
the failure" and "with a warning". That is not what the literature describes:
decoders are often recalibrated daily whether or not it is needed [2], and
running a fixed decoder until it fails is the other case (Fig. 1). The drawing
was built with all three rows.

## Things on the poster that are the researcher's to confirm

- **The title**, from the September research plan, and the subtitle.
- **The category and fair name**, shown as `[CATEGORY]` and `[FAIR AND YEAR]`.
- **The board size**, 48 × 48 inches. Check the fair's display rules for the
  largest board it allows before buying one; that was not looked up here.
- **The title is smaller on Draft 5** (78 pt, was 104 pt on Draft 4) so that
  the drawing fits beside it on one line.
- **Everything in the light-blue introduction**: the opening sentence, the
  three frame headings, the "three ways to time the repair" framing, and the
  heading lines that say "established science", "not yet shown" and "shown on
  archived data". These are the first words a judge reads.
- **"In research trials"** was added to the sentence about steering a cursor,
  because the devices are investigational.
- **Which charts** sit in the results column, their order, and the sentence
  over each one. Those sentences are claims about the data and should be
  checked against it.
- **What is set at 20 pt**, listed under "The size rule".
- **The abstract.** A draft of about 110 words, not a fair's official form.
- **The wording of the discussion, the limitations, the broader significance
  and the conclusion.** These are interpretation, and interpretation is the
  researcher's.
- **Which code excerpt is shown.** The one on the board is the rule that a
  warning raised before the fault began counts as a false alarm.
- **Type.** Source Serif 4 headings, IBM Plex Sans text.

## What is not on Drafts 4 and 5

Still in the repository, and on the earlier drafts: the empty "awaiting
measurement" chart templates and the chart of accuracy against decoder error
by session (Draft 1); the thin "project in one minute" row (Draft 3).

Changed on the way from Draft 4 to Draft 5:

- The four outcomes of a warning are now a small grid of names. Their one-line
  explanations are in the sentence under the grid and in the numbers beside
  it, except "the failure has already happened" under "Too late", which was
  dropped.
- The descriptions under the four large numbers are shorter, and no longer say
  "on faults" or "acceptance" gates.
- The caption of the 142-day chart no longer says "archived data"; it says
  "real data [1]".
- "Often need daily recalibration, and the device cannot be used freely while
  that happens [2]" is now the label "on a schedule: every day, pausing use
  [2]".
- Two charts are slightly shorter: the episode chart (Fig. 3) and the
  decision-rate chart (Fig. 17).

Shortened while fitting Draft 4, with where the information still is:

- The decoder's error and chance level left the data table. Both are in step 3
  of the workflow (Fig. 4).
- "0.5 is a coin flip" left the first large number. Chance is marked on the
  chart directly under it (Fig. 10).
- "About 1.4 h" of fault-free recording left the caption of Fig. 12. It is in
  Fig. 17 and in the limitations.
- The fifth workflow step no longer says the silence gate is applied first.
  The discussion says silence is the binding problem.
- The acceptance-gate rows are worded more briefly than in the
  preregistration (G-d, for example, leaves out its "median agreement above
  0.02" condition). The preregistration remains the authority:
  `physical/docs/09_PREREGISTRATION.md`.

## Known limits

- Checked by rendering locally, not on paper. Print one panel at full size
  before printing the board.
- The code excerpt wraps: at 20 pt a 12 inch column holds about 63 characters
  and the source lines are longer.
- The bench drawing shows the computer outside the enclosure. The repository
  does not fix where it sits.
- The two wiring diagrams are not on the same scale as each other.
- References are abbreviated to the first author.
- **The size check does not catch labels that collide.** Twice now a chart was
  shortened to save height, passed the check, and was unreadable when looked
  at. Any change to a chart's height has to be followed by looking at it.
