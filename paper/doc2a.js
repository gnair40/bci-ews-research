// doc2a.js -- Document 2, Parts I to III: the roadmap, the photographs, the data collection.
//
// The manual states procedures. It contains no results. Where it shows a number
// that is not taken from the repository, the number is arithmetic on invented
// inputs and is labelled as an illustration.
const L = require('./lib');
const { P, H3, bullets, numbered, note, code, mtable, mfigure, drawn, F, T, grid, spacer } = L;

const WARN = { bar: 'B24E0A', fill: 'FDF3E9' };

module.exports = function partsOneToThree(t, meta) {
  const { add, part, sec } = t;
  const reds = Object.values(L.state.reds);
  const redIn = (s) => reds.filter((r) => r.section === s).length;

  // =========================================================================
  part('I', 'Completion Roadmap');
  // =========================================================================
  sec('I.1', 'What this manual is for');
  add(P('The working research paper already states everything the project has established. '
    + `It also contains ${reds.length} items in red, each of which waits for something that `
    + 'does not exist yet: a part on the bench, a photograph, a recorded session, a value in a '
    + 'results file. This manual explains how to produce every one of those items and how to '
    + 'put it into the paper. It does not repeat the science. It gives the order of work, the '
    + 'record to keep while doing it, the calculation behind every number, the construction '
    + 'of every graph and the way to write each remaining passage.'));
  add(P('The manual makes no scientific decision. The design, the hypotheses, the predictions '
    + 'and the judging rule were fixed on 24 September 2026 in '
    + '`physical/docs/09_PREREGISTRATION.md`. Where a choice is still open, the manual says so '
    + 'and says that the choice belongs to the researcher.'));
  add(note([
    '**Two kinds of evidence, kept apart throughout.**',
    '**Computational validation: complete.** Faults planted by script in archived, public, '
    + 'de-identified recordings. Results are in `data/processed/` and `reports/`, and are '
    + 'recomputed by `tools/check_all.py`.',
    '**Physical validation: preregistered, not built.** An optical bench. On '
    + `${meta.date} no part had been ordered and nothing had been measured. Files under `
    + '`physical/data/dryrun/` are synthetic rehearsal output. They test that the programs '
    + 'run. They are not evidence, and no value from them may appear in the paper.',
  ]));
  add(P(`This manual was written against the repository \`${meta.repo}\`, branch `
    + `\`${meta.branch}\`, commit \`${meta.commit}\`. File names refer to that version. If a `
    + 'program is changed later, its own printed help and the documents in `physical/docs/` '
    + 'take precedence over this manual.'));

  sec('I.2', 'The roadmap');
  add(mfigure(drawn('d_roadmap'), 'From today\'s documents to the finished paper.',
    'Thirteen stages. Stages 2 to 5 happen at the bench, 6 to 8 on a laptop, 9 to 13 in the '
    + 'paper.'));
  add(mtable('The thirteen stages.', [460, 2000, 3000, 2500, 1400],
    ['No.', 'Stage', 'What is done', 'What it produces', 'Manual'], [
      ['1', 'Existing documentation', 'Nothing. It is finished: plan, preregistration, code, '
        + 'computational results', 'The black text of the paper', 'I.3'],
      ['2', 'Apparatus preparation', 'Order parts, prepare the computer, wire, build and seal '
        + 'the enclosure', 'A built bench; photographs PH-1 to PH-8', 'II, III.3'],
      ['3', 'Acceptance and calibration', 'Run gates G-a to G-e; adjust the modulation depth; '
        + 'fix all settings', 'Gate results; final settings; screenshot SS-2', 'III.3'],
      ['4', 'Physical validation', 'Draw and seal onsets; record P-1, P-2, P-3, P-5, P-7',
        'Raw session folders; the bench logbook', 'III.4'],
      ['5', 'Organising raw data', 'Copy to the USB drive; list exclusions; never edit',
        'A complete, unedited raw set', 'III.1, III.5'],
      ['6', 'Processing', 'Run `make_session_table.py`, twice', '`sessions.csv` and '
        + '`table_meta.json`', 'IV.2'],
      ['7', 'Statistical analysis', 'Run the five analysis programs',
        'One report and one JSON file per experiment', 'IV.3 to IV.9'],
      ['8', 'Graphs', 'Run `figures.py all`; make two graphs in a spreadsheet',
        'Eight graphs for the paper', 'V'],
      ['9', 'Results', 'Fill the pink cells; write the red passages of Section 6',
        'Section 6.2 complete', 'VI.7'],
      ['10', 'Analysis and discussion', 'Decide each prediction by its rule; compare the two '
        + 'validations; interpret', 'Sections 7 and 8 complete', 'IV.10, IV.11, VI.8, VI.9'],
      ['11', 'Conclusion', 'State the verdict by the preregistered rule',
        'Section 11 complete', 'VI.12'],
      ['12', 'Final abstract', 'Rewrite the abstract to the word limit', 'Section 1 complete',
        'VI.2'],
      ['13', 'Completed paper', 'Assemble, check and remove all red', 'The final paper', 'VII'],
    ]));
  add(P('**Stages that cannot be reordered.** The onsets must be sealed before the session '
    + 'they belong to is recorded, and `run_session.py` enforces this. The acceptance gates '
    + 'must pass before any experimental session is recorded. The settings fixed at '
    + 'calibration must not change afterward. No analysis program may be run on experiment '
    + 'P-2 before the decision about its length is final, because the number of fault-free '
    + 'sessions is frozen at 101 and any extension must be written as a dated amendment '
    + 'before the data are seen.'));

  sec('I.3', 'Status of each section of the paper');
  add(mtable('How complete each section is, and what completes it.',
    [2300, 1700, 1000, 2860, 1500],
    ['Section of the paper', 'Status today', 'Red items', 'What it still depends on',
      'Completed at stage'], [
      ['Title page', 'Working title only', String(redIn(0)), 'The researcher\'s final title',
        '13'],
      ['1 Abstract', 'Partially written', String(redIn(1)), 'Bench results and the verdict',
        '12'],
      ['2 Introduction', 'Substantially written', String(redIn(2)), 'Nothing from the bench',
        'final check only'],
      ['3 Hypothesis and Research Questions', 'Substantially written', String(redIn(3)),
        'The three status cells of Table 1', '11'],
      ['4 Materials', 'Partially written', String(redIn(4)), 'Parts received; two '
        + 'photographs; software versions on the bench computer', '2'],
      ['5 Methods', 'Computational part written; physical part written as a plan',
        String(redIn(5)), 'Settings actually used; eight photographs and screenshots; '
        + 'dates; change of tense from future to past', '2 to 4'],
      ['6 Results', '6.1 written; 6.2 dependent on the bench', String(redIn(6)),
        'Every results file and figure of the bench', '9'],
      ['7 Analysis', '7.1 written; 7.2 to 7.4 dependent', String(redIn(7)),
        'Tables 15 to 21 filled', '10'],
      ['8 Discussion', '8.1 and most of 8.4 written; 8.2 and 8.3 dependent', String(redIn(8)),
        'Sections 6.2 and 7 complete', '10'],
      ['9 Future Work', 'Substantially written', String(redIn(9)),
        'Questions raised by the bench', '10'],
      ['10 Sources of Error', 'Partially written', String(redIn(10)),
        'Observed sizes; the list of departures', '10'],
      ['11 Conclusion', 'Partially written', String(redIn(11)), 'The verdict', '11'],
      ['12 References', 'Partially written', String(redIn(12)),
        'Full author lists; one article to confirm; final commit', '13'],
      ['13 Acknowledgments', 'Dependent on the researcher', String(redIn(13)),
        'Written by the researcher alone, including the AI statement', '13'],
    ], { after: 'Red-item counts are produced by the program that builds both documents, so '
      + 'they match the paper. The full list is in Section VII.4.' }));

  sec('I.4', 'The two branches and the decision points');
  add(P(`${F('overview')} of the paper shows the project as two branches that start from one `
    + 'monitor and meet at one comparison. The computational branch is finished, so every '
    + 'decision point that remains is in the physical branch. Each has a response that was '
    + 'fixed in advance.'));
  add(mtable('Decision points in the physical branch.', [2700, 3760, 2900],
    ['If this happens', 'Do this', 'Where it is fixed'], [
      ['A gate from G-a to G-d fails', 'Find the cause using the troubleshooting guide, '
        + 'correct it, run the gate again. Record no experimental session until all pass.',
      '`physical/docs/10_TROUBLESHOOTING.md`'],
      ['Gate G-e cannot be passed (margin not within 6°)', 'Follow the preregistered '
        + 'fallback; record it as a departure in Table 25 of the paper.',
      '`09_PREREGISTRATION.md`, section 7'],
      ['A session goes wrong', 'Record it again under a new block number. List the failed one '
        + 'in `EXCLUSIONS.csv` with the reason. Do not delete it.', 'Section III.5'],
      ['There are no false alarms in P-2', 'Report the upper bound, about 3/H per hour, and '
        + 'the sentence fixed in prediction PP-1. Do not report "zero".', 'Section IV.3'],
      ['Time runs short', 'Cut in the fixed order: P-5, then P-7, then the middle severity of '
        + 'P-3. Never P-2 or P-6.', '`physical/docs/02_EXPERIMENTS.md`'],
      ['More fault-free recording seems desirable', 'Write a dated amendment first, stating '
        + 'whether any data have been seen. Then record.', '`09_PREREGISTRATION.md`, section 9'],
      ['No correlation reaches 0.70', 'The verdict is "inconclusive". Report it as that.',
        'Section IV.7'],
    ]));

  sec('I.5', 'Five rules that hold from start to finish');
  add(numbered([
    '**Raw data are never edited.** Nothing changes a file under `physical/data/raw/`. A bad '
    + 'session is excluded by a line in `EXCLUSIONS.csv`, not by deletion.',
    '**The preregistration is never edited.** `physical/docs/09_PREREGISTRATION.md` is frozen. '
    + 'A change of plan is an amendment appended with its date.',
    '**Reports are never edited by hand.** If a number looks wrong, the program is corrected '
    + 'and run again, and every report it affects is regenerated together.',
    '**Rehearsal output is never evidence.** Run `python3 physical/code/dryrun.py --cleanup` '
    + 'before the first real analysis, so that no synthetic file remains beside real ones.',
    '**Mistakes are written down.** The research log records what went wrong as well as what '
    + 'went right, on the day it happened.',
  ]));
  add(note('**Three lines in one bench document are out of date.** In '
    + '`physical/docs/06_DATA_COLLECTION.md`, the cost table gives 5.2 GB and 18 hours for the '
    + 'whole plan of 337 sessions (those are the figures for 217 sessions; the whole plan is '
    + 'about 8 GB and 28 hours), one heading describes experiment P-2 as four nights while '
    + 'the text beneath it correctly says one night, and the closing section gives the order '
    + 'of cuts as P-5, P-6, P-3. The order fixed in `02_EXPERIMENTS.md` is P-5, P-7, then the '
    + 'middle severity of P-3, and P-6 needs no recording at all. This manual follows the '
    + 'frozen plan. The three lines were found on 14 November 2026 and are recorded in the '
    + 'research log.', WARN));

  // =========================================================================
  part('II', 'Physical Validation Documentation');
  // =========================================================================
  sec('II.1', 'Rules for every photograph');
  add(P('The photographs are evidence that the apparatus existed and was built as described. A '
    + 'reader must be able to check the wiring against the drawing from the photograph alone. '
    + 'The same rules apply to all eight.'));
  add(bullets([
    '**No person appears.** No face, hand or reflection. The project involves no human '
    + 'participants, and its photographs should show none.',
    '**Power is off** whenever the wiring is photographed.',
    '**Light comes from two sides,** or from a window, without flash. Flash produces glare on '
    + 'the circuit board and on the display.',
    '**The camera is square to the subject.** For wiring it is directly above. The '
    + 'photograph is in landscape format and the subject fills most of the frame, with a '
    + 'margin left for labels.',
    '**The focus is on the detail that matters:** the header pins, the connector, the lens. '
    + 'Take three and keep the sharpest.',
    '**A ruler or tape measure is in the frame** wherever size or distance is part of the '
    + 'method.',
    '**The background is plain and matte:** white paper for parts, the bench surface for the '
    + 'apparatus.',
    '**The original file is kept unedited.** Create a folder `paper/photos/original/` and '
    + 'name each file by its code and date, for example `PH-5_2026-12-06.jpg`. Annotated '
    + 'copies go in `paper/photos/annotated/`. Only cropping and labelling are allowed. No '
    + 'retouching, and no generated or stock image, ever stands in for a photograph.',
    '**The date and time are written in the bench logbook** (sheet C) with the code of the '
    + 'photograph.',
  ]));
  add(P('**When to take them.** The enclosure is sealed before gate G-a and is not opened '
    + 'again during a campaign. Photographs of the inside must therefore be taken before '
    + 'sealing. The order is: parts (PH-1, PH-2), wiring (PH-5, PH-7), interior and open '
    + 'apparatus (PH-8, PH-3), then seal, then the sealed apparatus (PH-4). If the enclosure '
    + 'is opened later for any reason, the interior is photographed again and the event is '
    + 'recorded as a departure.'));

  sec('II.2', 'The eight photographs');
  const photo = (codeName, key, rows) => {
    add(H3(`${codeName}: fills ${F(key)} of the paper`));
    add(grid([1900, 7460], ['Item', 'Requirement'], rows), spacer(160));
  };
  photo('PH-1  All parts before assembly', 'ph_parts', [
    ['When', 'When all fourteen items have arrived and before anything is assembled.'],
    ['How', 'Lay the items on white paper in the order of Table 4 of the paper. Put a small '
      + 'numbered paper label beside each. Place a ruler along the bottom edge. Photograph '
      + 'from above.'],
    ['Must be visible', 'All fourteen items; all fourteen numbers; the ruler; the model '
      + 'markings on the Raspberry Pi and the camera where they can be read.'],
    ['Annotation', 'None if the paper labels are legible. Otherwise add the numbers as text.'],
    ['Caption', 'All parts of the bench before assembly, numbered as in Table 4. State any '
      + 'part that differs from the specification.'],
  ]);
  photo('PH-2  Six single components', 'ph_components', [
    ['When', 'Same session as PH-1.'],
    ['How', 'Six separate close photographs on white paper: (a) Raspberry Pi 4, (b) camera '
      + 'module with ribbon, (c) display, (d) stepper motor with driver board, (e) '
      + 'temperature sensor, (f) filter. Arrange them in a grid of two rows by three in a '
      + 'slide or drawing program and letter each.'],
    ['Must be visible', 'For (a) the 40-pin header and the camera connector; for (b) the '
      + 'lens and the ribbon contacts; for (d) the labels IN1 to IN4 on the driver board; '
      + 'for (e) the pin labels on the breakout.'],
    ['Annotation', 'The letters (a) to (f), and an arrow to pin 1 of the header in (a).'],
    ['Caption', 'The six components that carry the signal or are wired, with the model of '
      + 'each as received.'],
  ]);
  photo('PH-3  Complete apparatus, enclosure open', 'ph_open', [
    ['When', 'After wiring and placement, before sealing.'],
    ['How', 'From the front and slightly above, lid open, so that the display, the camera and '
      + 'the computer are all in view. Tape measure along the camera-to-display axis.'],
    ['Must be visible', 'Display; camera on its mount, aimed at the display; Raspberry Pi; '
      + 'stepper motor and driver; temperature sensor; power supply and cable route; black '
      + 'lining.'],
    ['Annotation', 'A label and leader line for each of the seven parts named above.'],
    ['Caption', 'The complete apparatus with the enclosure open, and the measured distance '
      + 'from camera to display.'],
  ]);
  photo('PH-4  Apparatus sealed, as run', 'ph_sealed', [
    ['When', 'After sealing and after gate G-a has passed.'],
    ['How', 'Same viewpoint as PH-3, lid closed.'],
    ['Must be visible', 'Tape along every seam; the slot where cables leave, sealed; nothing '
      + 'resting on the enclosure.'],
    ['Annotation', 'None required.'],
    ['Caption', 'The apparatus as it is during every recording, with the date on which it was '
      + 'sealed.'],
  ]);
  photo('PH-5  Wiring at the header and driver board', 'ph_header', [
    ['When', 'After wiring, power off, before the computer is placed in the enclosure.'],
    ['How', 'Directly above the Raspberry Pi and the driver board. This is the photograph a '
      + 'reader will use to check the wiring, so it must be the sharpest of the set. The '
      + 'design uses jumper wires directly from the header to the boards and has no '
      + 'breadboard. If a breadboard is added, that is a departure from the specification '
      + 'and is recorded in Table 25 of the paper.'],
    ['Must be visible', 'Pin 1 of the header (the corner pin nearest the microSD slot, on the '
      + 'inner row); each of the six stepper wires from end to end; the labels IN1 to IN4.'],
    ['Annotation', 'None on this copy. The annotated copy is PH-6.'],
    ['Caption', 'Wiring of the stepper driver at the 40-pin header, unannotated.'],
  ]);
  photo('PH-6  The same wiring, annotated beside the drawing', 'ph_annotated', [
    ['When', 'Made at a desk from PH-5.'],
    ['How', 'Follow Section II.4. Place the annotated photograph on the left and the '
      + `repository drawing \`physical/figures/wiring-stepper.png\` (${F('wiring_stepper')}) `
      + 'on the right.'],
    ['Must be visible', 'One label per wire, in the form signal, GPIO number, physical pin.'],
    ['Annotation', 'IN1, GPIO 17, pin 11. IN2, GPIO 27, pin 13. IN3, GPIO 22, pin 15. IN4, '
      + 'GPIO 23, pin 16. 5 V, pin 2. Ground, pin 9. These are the values in `rig/motor.py`. '
      + 'If the photograph shows anything else, the wiring is wrong or the departure must be '
      + 'recorded.'],
    ['Caption', 'The wiring as built, labelled, beside the wiring drawing it was built from.'],
  ]);
  photo('PH-7  Temperature sensor and power', 'ph_sensor', [
    ['When', 'Same session as PH-5.'],
    ['How', 'Above the sensor breakout and the header, then a second frame of the power '
      + 'connection. Join the two side by side.'],
    ['Must be visible', 'The three sensor wires from end to end; the official power supply '
      + 'and its connector.'],
    ['Annotation', 'DATA, GPIO 4, pin 7 (set in `rig/logtemp.py`). For supply and ground, '
      + 'label the pins actually used. The documents recommend pin 1 (3.3 V) and pin 9 '
      + '(ground), but no file in the repository fixes them.'],
    ['Caption', 'The temperature sensor and the power connection, with the supply pins used.'],
  ]);
  photo('PH-8  Inside the enclosure', 'ph_inside', [
    ['When', 'Immediately before sealing.'],
    ['How', 'From the open side toward the display, then from above. Use the clearer one.'],
    ['Must be visible', 'The black lining on every inner face; the display; the camera aimed '
      + 'at it; the place where the filter is slid in; a tape measure showing the '
      + 'camera-to-display distance.'],
    ['Annotation', 'The measured distance, in centimetres.'],
    ['Caption', 'The interior before sealing, with the geometry that was then taped in place.'],
  ]);

  sec('II.3', 'The two screenshots');
  add(P('A screenshot is taken with the screenshot tool of whichever computer shows the '
    + 'window. If the Raspberry Pi is controlled from a laptop, the terminal window on the '
    + 'laptop is the one to capture. Before saving, check that the image shows no password, '
    + 'network name or other personal information.'));
  add(H3(`SS-1  The software during a session: fills ${F('ss_session')}`));
  add(grid([1900, 7460], ['Item', 'Requirement'], [
    ['When', 'During a calibration session of P-1, which is attended.'],
    ['How', 'Capture the terminal after `run_session.py` has printed the session it is '
      + 'recording. For the stimulus, photograph the display during the build stage, before '
      + 'sealing, and place it as an inset. The pattern will look like an almost uniform grey '
      + 'grid, because the modulation is deliberately small. Say so in the caption.'],
    ['Must be visible', 'The command typed; the session and block number; the sealed plan '
      + 'that was loaded; the start time printed by the program.'],
    ['Caption', 'Terminal output of `run_session.py` for one calibration session, with the '
      + 'stimulus pattern inset.'],
  ]), spacer(160));
  add(H3(`SS-2  The acceptance gates passing: fills ${F('ss_check')}`));
  add(grid([1900, 7460], ['Item', 'Requirement'], [
    ['When', 'After calibration, when all five gates pass on the same session.'],
    ['How', 'Run the command below and capture its whole output.'],
    ['Must be visible', 'Each gate from G-a to G-e, its measured value and its result; the '
      + 'date.'],
    ['Caption', 'Output of `bench.py check` on the calibration session, all five gates '
      + 'passing.'],
  ]));
  add(code(['python3 physical/code/bench.py check --session 0 --block 1']));

  sec('II.4', 'Annotating a photograph');
  add(numbered([
    'Open a blank slide in PowerPoint or Google Slides and insert a copy of the photograph. '
    + 'Never work on the original file.',
    'For each wire, add a text box with white fill and black text of at least 14 points, and '
    + 'a thin line from the box to the point where the wire meets the header.',
    'Write each label in the same form: signal, GPIO number, physical pin.',
    'Place the repository drawing beside the photograph at the same height.',
    'Select everything, group it, and save the group as a PNG picture.',
    'Check every label against the table of pins in Section 5.3 of the paper before the '
    + 'picture goes in.',
  ]));

  sec('II.5', 'Which photograph fills which figure, and a checklist');
  add(mfigure(drawn('d_photomap'), 'Photographs and screenshots mapped to figures of the paper.',
    'PH is a photograph, SS a screenshot.', { width: 560 }));
  add(mtable('Checklist for the photographic record.', [900, 1300, 2360, 1500, 1800, 1500],
    ['Code', 'Fills', 'Subject', 'Date taken', 'File name', 'Checked against II.2'], [
      ['PH-1', F('ph_parts'), 'All parts', null, null, null],
      ['PH-2', F('ph_components'), 'Six components', null, null, null],
      ['PH-3', F('ph_open'), 'Apparatus open', null, null, null],
      ['PH-4', F('ph_sealed'), 'Apparatus sealed', null, null, null],
      ['PH-5', F('ph_header'), 'Wiring, plain', null, null, null],
      ['PH-6', F('ph_annotated'), 'Wiring, annotated', null, null, null],
      ['PH-7', F('ph_sensor'), 'Sensor and power', null, null, null],
      ['PH-8', F('ph_inside'), 'Interior', null, null, null],
      ['SS-1', F('ss_session'), 'Session terminal', null, null, null],
      ['SS-2', F('ss_check'), 'Gates passing', null, null, null],
    ]));
  add(P('**Putting a picture into the paper.** Click inside the dashed box of the figure, '
    + 'delete the red instruction and the grey heading, and insert the picture in their '
    + 'place (Insert, Pictures). Then remove the dashed border: select the box, open the '
    + 'border settings and choose no border. Keep the caption beneath, and revise it to state '
    + 'what the picture actually shows.'));

  // =========================================================================
  part('III', 'Experimental Data Collection');
  // =========================================================================
  sec('III.1', 'What the programs record without being asked');
  add(P('Most of the data are written by the programs. Nothing in the table below is typed by '
    + 'hand, with one exception that is marked. The researcher\'s task is to keep these files '
    + 'complete and unedited.'));
  add(mtable('Files written during recording and analysis.', [3100, 1900, 2960, 1400],
    ['File or folder', 'Written by', 'Contains', 'In GitHub'], [
      ['`physical/data/onsets/` and `MANIFEST.csv`', '`draw_onset.py`, `run_campaign.py plan`',
        'The sealed plan of every session, with a checksum', 'yes'],
      ['`physical/data/raw/s<session>_b<block>/capture.npy`', '`run_session.py`',
        'The camera frames of one session (about 23 MB)', 'no'],
      ['`.../capture_t.npy`', '`run_session.py`', 'The time of every frame', 'no'],
      ['`.../stim.csv`', '`run_session.py`', 'What was shown in every frame, including the '
        + 'true direction', 'no'],
      ['`.../session.json`', '`run_session.py`', 'Every setting, the temperature, any note',
        'no'],
      ['`physical/data/raw/SESSION_LOG.csv`', '`run_session.py`', 'One line per session with '
        + 'all settings', 'no'],
      ['`physical/data/lag.json`', '`bench.py lag`', 'The measured delay from display to '
        + 'camera', 'yes'],
      ['`physical/data/EXCLUSIONS.csv`', '**by hand**', 'folder, reason, excluded_at: one '
        + 'line per excluded session', 'yes'],
      ['`physical/data/sessions.csv`', '`make_session_table.py`', 'One row per session '
        + '(Section IV.2)', 'yes'],
      ['`physical/data/processed/`', '`make_session_table.py`', 'Window-level scores; '
        + '`table_meta.json`', 'yes'],
      ['`physical/data/results/`', 'the analysis programs', 'One report (.md) and one data '
        + 'file (.json) per experiment', 'yes'],
      ['`physical/data/figures/`', '`figures.py`', 'Six graphs', 'yes'],
      ['`physical/data/dryrun/`', '`dryrun.py`', 'Synthetic rehearsal output. Never evidence.',
        'never'],
    ], { after: 'Raw recordings are too large for GitHub. They are copied to the USB drive as '
      + 'they are made, and the drive is the archive.' }));

  sec('III.2', 'The bench logbook: what is written by hand');
  add(P('The programs record settings. They do not record that a cable was nudged or that a '
    + 'filter was applied four seconds late. Those facts live in the bench logbook, a '
    + 'spreadsheet of five sheets kept beside the bench and filled in at the time. The folder '
    + '`paper/logbook/` in the repository holds one CSV file per sheet with exactly these '
    + 'column headers. Each opens directly in Excel or Google Sheets and can be saved as a '
    + 'sheet of one workbook. An entry is never erased. A correction is a new line that '
    + 'refers to the old one.'));
  const sheet = (name, purpose, cols) => {
    t.sheets.push({ name, cols: cols.map((c) => c[0]) });
    add(H3(name));
    add(P(purpose, { after: 90 }));
    add(grid([2700, 1600, 5060], ['Column', 'Unit or form', 'What to enter'], cols),
      spacer(170));
  };
  sheet('Sheet A: parts received', 'One row per item of Table 4 of the paper. Fills the pink '
    + 'columns of that table.', [
    ['item_no', '1 to 14', 'The number in Table 4'],
    ['item_as_specified', 'text', 'Copied from Table 4'],
    ['item_received', 'text', 'Maker, model and revision as printed on the part'],
    ['supplier', 'text', 'Where it was bought'],
    ['cost_paid', 'USD', 'Price paid, without shipping'],
    ['date_received', 'YYYY-MM-DD', 'Day it arrived'],
    ['differs_from_specification', 'yes or no', 'If yes, describe in the next column'],
    ['note', 'text', 'Any difference, damage or substitution'],
  ]);
  sheet('Sheet B: build and gate record', 'One row per setting or gate result, entered once '
    + 'when it is fixed. Fills R4.1, the red items of Section 5.3 and Table 13 of the paper.', [
    ['date', 'YYYY-MM-DD', 'Day the value was fixed or measured'],
    ['item', 'text', 'One of the items listed in Section III.3'],
    ['value', 'number or text', 'The value, copied exactly from the program output'],
    ['unit', 'text', 'For example: fraction, microseconds, cm, degrees, percent'],
    ['source', 'text', 'The command that printed it, or "measured with tape"'],
    ['pass_or_fail', 'pass, fail or blank', 'For gates only'],
    ['note', 'text', 'Anything unusual; how many attempts were needed'],
  ]);
  sheet('Sheet C: daily record', 'One row per recording day, filled before the first session.',
    [
      ['date', 'YYYY-MM-DD', 'The day'],
      ['start_time', 'HH:MM', 'When the checks began'],
      ['selftest_passed', 'yes or no', 'Result of `monitor.py --selftest`'],
      ['box_closed_and_taped', 'yes or no', 'Checked by eye'],
      ['screen_brightness_as_logged', 'yes or no', 'Unchanged since calibration'],
      ['camera_unmoved', 'yes or no', 'Compared with photograph PH-8'],
      ['free_space', 'GB', 'From `df -h`'],
      ['temperature', '°C', 'Reading of the sensor'],
      ['people_present', 'text', 'Roles only, for example "researcher, adult"'],
      ['experiment_and_blocks', 'text', 'For example "P-3, blocks 1 to 40"'],
      ['note', 'text', 'Anything unusual, including mistakes'],
    ]);
  sheet('Sheet D: attended sessions', 'One row per session in which a fault is applied by hand '
    + '(part of P-3, all of P-5).', [
    ['date', 'YYYY-MM-DD', 'The day'],
    ['experiment', 'P-3 or P-5', 'Which experiment'],
    ['session', 'integer', 'Session number given to the program'],
    ['block', 'integer', 'Block number'],
    ['fault_type', 'text', 'As drawn (P-3) or as intended (P-5)'],
    ['severity', '0.25, 0.5 or 1.0', 'As drawn; blank for P-5'],
    ['sealed_onset', 's', 'From the plan (P-3); blank for P-5'],
    ['clock_time_of_action', 'HH:MM:SS', 'Written while it happens, never afterward'],
    ['applied_late_by', 's', 'Estimated delay; 0 if on the countdown'],
    ['note_given_to_program', 'text', 'The exact text passed with `--note`'],
    ['anything_unusual', 'text', 'For example "touched the mount"'],
  ]);
  sheet('Sheet E: departures and exclusions', 'One row per departure from the plan and per '
    + 'excluded session. Fills Table 25 of the paper.', [
    ['date', 'YYYY-MM-DD', 'Day of the departure'],
    ['what_was_planned', 'text', 'With the document and section that planned it'],
    ['what_was_done', 'text', 'Exactly'],
    ['reason', 'text', 'Why'],
    ['data_seen_before_deciding', 'yes or no', 'Whether any result was known at the time'],
    ['sessions_affected', 'text', 'Session and block numbers'],
    ['possible_effect', 'text', 'Which result could change, and in which direction'],
  ]);

  sec('III.3', 'The build and gate record, step by step');
  add(P('Exact command lines for the build are in `physical/docs/04_BUILD.md` and on the one-page '
    + '`physical/docs/14_BENCH_CARD.md`. The list below says what to write in sheet B at each '
    + 'step and where it goes in the paper.'));
  add(mtable('Entries of sheet B.', [2700, 3460, 3200],
    ['Item to record', 'Where the value comes from', 'Where it goes in the paper'], [
      ['Operating system and library versions', 'On the bench computer: `cat /etc/os-release`, '
        + 'and `python3 -c "import picamera2, pygame, numpy, scipy, pandas; ..."` printing '
        + 'each version', 'Table 3, item R4.1'],
      ['Program self-test', '`python3 physical/code/monitor.py --selftest`', 'Section 5.3, '
        + 'one sentence'],
      ['Stimulus timing', '`python3 physical/code/stimulus.py --benchmark 300`; the share of '
        + 'the 20 ms frame budget used (it must be under 60%)', 'Table 24, late frames'],
      ['Motor test', '`python3 rig/motor.py --degrees 2`, then `--degrees -2`',
        'Sheet B only'],
      ['Sensor test and pins used', '`python3 rig/logtemp.py --once`; the supply and ground '
        + 'pins chosen', 'Section 5.3, item R5.1'],
      ['Camera-to-display distance', 'Tape measure, in cm, before sealing', 'Section 5.3, '
        + 'item R5.2; photograph PH-8'],
      ['Screen brightness setting', 'The display\'s own menu', 'Section 5.3, item R5.2'],
      ['Camera exposure and gain', 'The values passed to the recording program, as printed in '
        + '`session.json`', 'Section 5.3, item R5.2'],
      ['Gate G-a: mean and maximum pixel', '`bench.py darkframe`', 'Table 13'],
      ['Gate G-b: late frames, dead channels, clipped', '`bench.py frames`', 'Table 13'],
      ['Gate G-c: delay in three recordings', '`bench.py lag`, which writes `lag.json`',
        'Table 13'],
      ['Gate G-d: median agreement; share of channels positive', '`bench.py dither`',
        'Table 13'],
      ['Gate G-e: margin', '`bench.py margin` on each calibration session', 'Table 13'],
      ['Each depth tried during calibration', 'One row per attempt, with the margin obtained',
        'Section 5.3, one sentence on how many attempts'],
      ['Final modulation depth', 'The `--depth` of the last calibration session',
        'Section 5.3, item R5.2'],
    ]));
  add(P('Calibration changes one setting at a time. Each attempt is one command and one row of '
    + 'sheet B:'));
  add(code(['python3 physical/code/run_session.py --session 0 --block 1 --calibration --frames 3000',
    'python3 physical/code/bench.py margin        # see 04_BUILD.md for its arguments']));
  add(P('When the margin is within 6° of 36.1°, the depth is written down and is not '
    + 'changed again. Five full calibration sessions are then recorded for experiment P-1.'));

  sec('III.4', 'Recording the experiments');
  add(P('The commands are those of `physical/docs/06_DATA_COLLECTION.md`. Every recording day '
    + 'begins with the checks of sheet C.'));
  add(code(['cd ~/bci-ews-research', 'git pull', 'python3 physical/code/monitor.py --selftest']));
  add(P('**P-2, fault-free, one night, unattended.**'));
  add(code(['python3 physical/code/run_campaign.py plan   --session 10 --healthy 101',
    'python3 physical/code/run_campaign.py record --session 10',
    'python3 physical/code/run_campaign.py status --session 10     # next morning']));
  add(P('**P-3, sealed faults.** Draw all 101 first. `status` lists which blocks need someone '
    + 'in the room. The software faults can be recorded unattended; the filter and tape '
    + 'faults are recorded one block at a time, with a row in sheet D for each.'));
  add(code(['python3 physical/code/run_campaign.py plan   --session 20 --degraded 101',
    'python3 physical/code/run_campaign.py status --session 20',
    'python3 physical/code/run_campaign.py record --session 20 --software-only',
    'python3 physical/code/run_session.py --session 20 --block 7      # one attended block']));
  add(P('**P-5, undesigned faults, by hand.** Start the recording, act, write the clock time '
    + 'while acting, and enter the onset immediately afterward.'));
  add(code(['python3 physical/code/run_session.py --session 30 --block 1 \\',
    '    --undesigned "half-unseated the camera ribbon and re-seated it"',
    'python3 physical/code/note_onset.py --session 30 --block 1 \\',
    '    --at-clock 21:47:12 --fault CONNECTOR']));
  add(P('**P-7, three further configurations.** Forty sessions each in configurations B, C and '
    + 'D. The commands and the settings of each configuration are in '
    + '`physical/docs/02_EXPERIMENTS.md` and `physical/docs/12_RUNBOOK.md`.'));
  add(P('**Safety in P-5.** The warm-air intervention uses the lowest setting, at least 30 cm '
    + 'away, for no more than 60 seconds, with components kept below 50 °C and an adult '
    + 'present. Hands stay clear of the motor while it is powered.'));
  add(mtable('Record of the campaign, to be filled as it proceeds.',
    [1500, 1300, 1400, 1400, 1400, 2360],
    ['Experiment', 'Planned', 'Date started', 'Date finished', 'Sessions recorded',
      'Sheet D rows (attended)'], [
      ['P-1', '5', null, null, null, 'not applicable'],
      ['P-2', '101', null, null, null, 'not applicable'],
      ['P-3', '101', null, null, null, null],
      ['P-5', '10', null, null, null, null],
      ['P-7 B', '40', null, null, null, 'not applicable'],
      ['P-7 C', '40', null, null, null, 'not applicable'],
      ['P-7 D', '40', null, null, null, 'not applicable'],
    ], { after: 'This table supplies item R5.11 and the dates column of Table 14 of the paper.' }));

  sec('III.5', 'Missing, repeated and inconsistent observations');
  add(mtable('What to do when the record is not clean.', [2800, 4060, 2500],
    ['Situation', 'What to do', 'What never to do'], [
      ['A session went wrong (screen slept, cable moved)', 'Record another under a new block '
        + 'number. Add the failed folder to `EXCLUSIONS.csv` with the reason and the time. '
        + 'Add a row to sheet E.', 'Delete or overwrite the failed folder'],
      ['A hand-applied fault was late', 'Record the delay in sheet D and in `--note`. Under '
        + '30 seconds it is smaller than one analysis window and the session stands.',
      'Leave it unrecorded'],
      ['A P-5 onset was not noted', 'The session cannot be analysed. `make_session_table.py` '
        + 'refuses it by name. Exclude it and record another.', 'Reconstruct the time from '
        + 'memory'],
      ['A P-5 onset was noted wrongly', 'Use `note_onset.py --replace` and write in the '
        + 'research log what was wrong and why.', 'Correct it silently'],
      ['An overnight campaign stopped early', 'Run `record` again; it continues where it '
        + 'stopped. Note the gap in sheet C.', 'Start a new plan'],
      ['A recording will not load', '`make_session_table.py` prints its name. Exclude it with '
        + 'the reason "unreadable".', 'Ignore the message'],
      ['The logbook and `SESSION_LOG.csv` disagree', 'For a setting, the automatic log is '
        + 'right. For an event, the logbook is right. Record the disagreement in sheet E.',
      'Edit either to match'],
      ['Fewer sessions than planned', 'Report the number recorded in Table 14 and the reason. '
        + 'Intervals will be wider; that is the honest result.', 'Fill the gap with rehearsal '
        + 'output'],
      ['A value is missing from a results file', 'It means the program could not compute it '
        + '(for example, fewer than three sessions for an interval). Write "not estimable" '
        + 'with the reason.', 'Leave the cell blank or enter zero'],
    ]));

  sec('III.6', 'Departures from the plan');
  add(P('A departure is anything done differently from the frozen plan: a substituted part, a '
    + 'changed setting, a session count that differs, an experiment cut, an analysis added. '
    + 'Each one is entered in sheet E on the day it happens and copied to Table 25 of the '
    + 'paper. The column that matters most is whether any result had been seen when the '
    + 'decision was made, because a change made after seeing the data can favour a result '
    + 'without anyone intending it. An analysis that was not preregistered may still be '
    + 'reported, provided it is labelled exploratory wherever it appears.'));
};
