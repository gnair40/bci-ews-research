// doc1.js -- Document 1: the working research paper.
//
// Black text states what the repository already establishes. Every number is read
// from poster/poster_data.json or data/processed/harness_summary*_local.json, the
// files the repository's own checks recompute, and is not typed here.
// Red text is a numbered placeholder for something that cannot exist until the
// bench has been built and has recorded. Each is registered with the file it will
// come from and the section of the manual that explains it.
const fs = require('fs');
const path = require('path');
const L = require('./lib');
const { P, H1, H2, H3, bullets, numbered, note, formula, spacer, table, figure, figureSpace,
  writeSpace, red, drawn, bench, F, T, D } = L;

const J = (p) => JSON.parse(fs.readFileSync(path.join(L.REPO, p), 'utf8'));
const PD = J('poster/poster_data.json');
const S = PD.scalars;
const HS = { T11: J('data/processed/harness_summary_local.json').decoder_guard,
  T5: J('data/processed/harness_summary_T5_local.json').decoder_guard };
const LT = PD.lead_time;
const M = PD.fault_mode_auc;
const PAIR = PD.decision_rate.paired.participants;
const SL = S.session_level_correlation_T11;
const EP = PD.median_episode;

const n = (x, d = 0) => Number(x).toFixed(d).replace('-', '−');
const pct = (x, d = 1) => `${(100 * x).toFixed(d)}%`;
const frac = (s) => s.split('/').map(Number);
const N_EP = S.episodes.T11 + S.episodes.T5;
const [det11, deg11] = frac(S.detection_rate.T11);
const [det5, deg5] = frac(S.detection_rate.T5);
const margin11 = S.decoder_chance_deg.T11 - S.decoder_error_deg.T11;
const day0 = Math.min(...SL.series.map((p) => p.trial_day));
const SER = SL.series.map((p) => ({ d: p.trial_day - day0, e: p.median_error_deg }));
const span = Math.max(...SER.map((p) => p.d));
const FAIL = SL.failure_threshold_deg;
// the sessions before the first one above the failure level, and the sessions
// after the last one at or below it
const firstBad = SER.findIndex((p) => p.e > FAIL);
const early = SER.slice(0, firstBad);
const lastGood = SER.map((p) => p.e <= FAIL).lastIndexOf(true);
const late = SER.slice(lastGood + 1);
const SC = PD.session_scatter;
const DFA = PD.detection_vs_fa;
const ff11 = Math.round(S.silence_fault_free_fraction.T11 * S.fault_free_episodes.T11);
const ff5 = Math.round(S.silence_fault_free_fraction.T5 * S.fault_free_episodes.T5);

function build(meta) {
  const out = [];
  const add = (...xs) => { for (const x of xs) out.push(...(Array.isArray(x) ? x : [x])); };
  const sec = (k, title, first = false) => { L.state.section = k;
    add(H1(`${k}. ${title}`, { breakBefore: !first && [4, 5, 6, 8, 10, 12].includes(k) })); };

  // -------------------------------------------------------------------------
  // title page
  // -------------------------------------------------------------------------
  const tp = (text, size, o = {}) => new D.Paragraph({ alignment: D.AlignmentType.CENTER,
    spacing: { before: o.before || 0, after: o.after ?? 120 },
    children: [new D.TextRun({ text, font: o.font || L.SANS, size, bold: o.bold, color: o.color,
      italics: o.italics })] });
  add(
    tp('WORKING RESEARCH PAPER', 20, { before: 900, bold: true, color: L.GREY, after: 300 }),
    tp('Seeing Failure Before It Shows', 44, { bold: true, color: '12324F', after: 80 }),
    tp('Building and Validating a Decoder-Health Monitor for Neural Interfaces', 28,
      { bold: true, color: '12324F', after: 500 }),
    tp('Gayathri Nair', 26, { after: 60 }),
    tp('Central Bucks High School South', 22, { after: 60 }),
    tp('Adult Sponsor: Michelle Rhodes', 22, { after: 500 }),
    tp(`Draft of ${meta.date}`, 22, { bold: true, after: 60 }),
    tp('Computational validation: complete.  Physical validation: preregistered on '
      + '24 September 2026, not yet built.', 20, { after: 400 }),
  );
  L.state.section = 0;
  add(note([
    '**How to read this draft.** Text in black is established by work that is finished and '
    + 'recorded in the project repository. Text in **bold red capitals inside square brackets** '
    + 'marks something that cannot be written until the physical test bench has been built and '
    + 'has recorded data. Each red item carries a code such as R6.3 (the third item of '
    + 'Section 6). The companion document, the ~Research Completion and Data Analysis Manual~, '
    + 'explains every code: what goes there, which file or photograph it comes from, and how '
    + 'to produce it.',
    'Pink table cells are values still to be entered. Boxes with a dashed red border are '
    + 'spaces reserved for a photograph, a screenshot, a graph or a paragraph. The brackets, '
    + 'the bold capitals and the dashed borders remain visible when the paper is printed '
    + 'without colour.',
    `**Source of every established statement:** the repository \`${meta.repo}\`, branch `
    + `\`${meta.branch}\`, at commit \`${meta.commit}\`. File and folder names in this paper `
    + 'refer to that repository.',
  ]));
  add(H2('Contents'));
  add(bullets(['1. Abstract', '2. Introduction', '3. Hypothesis and Research Questions',
    '4. Materials', '5. Methods', '6. Results', '7. Analysis', '8. Discussion',
    '9. Future Work', '10. Sources of Error', '11. Conclusion', '12. References',
    '13. Acknowledgments']));

  // -------------------------------------------------------------------------
  sec(1, 'Abstract');
  // -------------------------------------------------------------------------
  out[out.length - 1] = H1('1. Abstract', { breakBefore: true });
  add(P('Intracortical brain-computer interfaces let people with paralysis control a cursor '
    + 'by decoding recorded brain activity. The recording drifts, the decoder loses accuracy, '
    + 'and it must be recalibrated. Monitors that read the recorded signal have been proposed '
    + 'for deciding when to recalibrate and are validated by their correlation with task '
    + 'performance. This project measures two quantities that a correlation does not give: '
    + 'how early such a monitor warns, and how often it warns when nothing is wrong. A '
    + 'monitor, decoder-guard, was tested on public, de-identified recordings from two '
    + `research participants (arrays T11 and T5). A script planted ${N_EP.toLocaleString()} `
    + 'faults in those recordings at start times sealed by checksum before any detector '
    + 'existed, and a decoder frozen in advance graded the outcome. At a warning threshold '
    + `chosen on validation data, the monitor detected ${det11} of ${deg11} faults on T11 and `
    + `${det5} of ${deg5} on T5. The median warning came ${n(-S.median_lead_s.T11)} s and `
    + `${n(-S.median_lead_s.T5)} s after decoding had already failed, with `
    + `${n(S.false_alarms_per_hour.T11, 2)} and ${n(S.false_alarms_per_hour.T5, 2)} false `
    + `alarms per hour against a budget of ${S.budget_per_hour}. None of `
    + `${S.funnel.run} detector configurations passed all five preregistered gates, so the `
    + 'original hypothesis was rejected. A physical test bench, preregistered on '
    + '24 September 2026, will repeat the measurement on an optical apparatus with enough '
    + 'fault-free recording to bound the false-alarm rate. '
    + red('Insert the bench results in two or three sentences: the number of sessions '
      + 'recorded and analysed, the false-alarm rate with its 95% upper bound, the median '
      + 'lead time with its 95% interval, and the largest of the three correlations.',
    'Tables 14, 15, 16 and 19 of this paper, once filled', 'VI.2')
    + ' '
    + red('Insert one closing sentence that states the verdict given by the preregistered '
      + 'judging rule (supported, falsified or inconclusive) and what it means.',
    'physical/data/results/correlation_vs_usability.json, field hypothesis_supported; '
      + 'Section 11 of this paper', 'VI.2')));
  add(note('The abstract is finished last. Most fairs limit it to 250 words, so the black text '
    + 'above will need to be shortened when the red sentences are added. The manual, '
    + 'Section VI.2, gives the order in which to do this.'));

  // -------------------------------------------------------------------------
  sec(2, 'Introduction');
  // -------------------------------------------------------------------------
  add(H2('2.1 Background'));
  add(P('A brain-computer interface of the kind studied here lets a person with paralysis move '
    + 'a cursor by intending to move. A grid of small electrodes in the motor cortex records '
    + 'the activity of nearby neurons, and software called a decoder turns that activity into '
    + 'cursor motion (Pun et al., 2024a). Making this work on the first day is no longer the '
    + 'main difficulty. Keeping it working is. The recorded signal keeps changing: the array '
    + 'moves slightly, tissue reacts to it, materials degrade, and the neurons themselves '
    + 'change how they fire (Perge et al., 2013). Long-term studies document how slow and '
    + 'persistent this change is. Barrese et al. (2013) examined how 78 implanted arrays '
    + 'failed, Sponheim et al. (2021) tracked more than six thousand recording sessions over '
    + 'nine years, and Hughes et al. (2021) followed one person\'s array for five years.'));
  add(P('A decoder is fitted to the signal as it was on the day of calibration. When the '
    + 'signal moves away from that pattern, the decoder still produces output, but the output '
    + `matches the person's intention less well. ${F('drift')} shows this on real data: one `
    + `decoder kept unchanged for ${span} days on array T11. Median cursor error stays between `
    + `${n(Math.min(...early.map((p) => p.e)), 1)}\u00B0 and `
    + `${n(Math.max(...early.map((p) => p.e)), 1)}\u00B0 through day `
    + `${early[early.length - 1].d}, first exceeds the failure level of ${n(FAIL, 1)}\u00B0 on `
    + `day ${SER[firstBad].d}, and lies between ${n(Math.min(...late.map((p) => p.e)), 1)}\u00B0 `
    + `and ${n(Math.max(...late.map((p) => p.e)), 1)}\u00B0 in every session from day `
    + `${late[0].d} onward. Nothing in the system tells the user that this is happening.`));
  add(figure('overview', drawn('d_overview'),
    'The research in one picture.',
    'A problem, one monitor, two validations of it, and one rule for judging the outcome. The '
    + 'left branch is finished. The right branch is specified and preregistered but not built.'));
  add(figure('drift', drawn('c_drift'),
    'Decoder error on real recordings when the decoder is never refitted.',
    `Array T11, median cursor error by session, one decoder kept for ${span} days. Data: Pun `
    + 'et al. (2024b). Computed by `scripts/74_session_level_monitor.py`. No fault was planted '
    + 'in these sessions.'));

  add(H2('2.2 The problem'));
  add(P('Two responses to drift exist. The first is to correct it automatically, for example by '
    + 'realigning the underlying activity patterns so that a fixed decoder keeps working '
    + '(Karpowicz et al., 2025; Wilson et al., 2025). The second is recalibration: the user '
    + 'stops, performs a guided block of trials, and the decoder is fitted again. Decoders '
    + 'often need this daily, and the device cannot be used freely while it happens (Wilson '
    + 'et al., 2025). Recalibration currently happens on a schedule, not when there is '
    + 'evidence that it is needed.'));
  add(P('A monitor that warns when the decoder is about to fail would let the repair happen '
    + 'only when needed and before control is lost. Such monitors have been proposed. Pun et '
    + 'al. (2024a) score the change in the recorded signal and report that the score '
    + 'correlates with task performance, r = 0.93 and r = 0.72, and '
    + 'propose the score for deciding when to recalibrate. A correlation shows that the score '
    + 'and the performance move together. It does not show whether a warning would arrive '
    + 'before the failure, or how often the monitor would warn when nothing is wrong. Those '
    + 'two quantities decide whether a warning can be trusted. In hospital monitoring, where '
    + '72 to 99% of alarms have been reported to be false (Sendelbach & Funk, 2013), frequent '
    + 'false alarms lead staff to stop responding to them.'));

  add(H2('2.3 The gap this project addresses'));
  add(P('Lead time and false-alarm rate are missing from the published evidence for a specific '
    + 'reason. In recordings that were only observed, nobody wrote down when the decline '
    + 'began. Whoever analyses the data chooses the starting point afterward, so any statement '
    + 'about how early a warning arrived depends partly on that choice. A false-alarm rate '
    + 'needs a known quantity of recording in which nothing was wrong, and the archived '
    + 'recordings used here contain about 1.4 hours that are fault-free in that strict sense, '
    + 'which cannot bound a rate of one false alarm in ten hours. No published lead time or '
    + 'false-alarm rate for a monitor of this class was found during this project. That is a '
    + 'statement about a search, not a proof that none exists.'));

  add(H2('2.4 Approach'));
  add(P('This project supplies the missing onset by controlling it. In the computational '
    + 'validation, degradations are applied by script to real archived recordings, at start '
    + 'times drawn at random and sealed with a checksum before any detector was written. A '
    + 'decoder that was fitted once and then frozen provides the performance against which a '
    + 'warning is early or late. In the physical validation, the same monitor will read an '
    + 'optical apparatus built for the purpose, where long fault-free recording is cheap and '
    + 'the start of each fault is again fixed in advance. Both validations use the same '
    + '30-second analysis window, the same false-alarm budget of 0.1 per hour, and rules for '
    + `judging the outcome that were written down before the data were read (${F('overview')}).`));
  add(P('The work matters beyond this one monitor because the question is general: whether the '
    + 'usual way of validating a decoder-health monitor, a correlation with performance, is '
    + 'enough to support using it. Nearly 5.4 million people in the United States live with '
    + 'paralysis (Armour et al., 2016), and implanted interfaces are being developed for some '
    + 'of them. This project does not test any device on a person and makes no claim of '
    + 'clinical benefit. It tests a method of evaluation.'));

  // -------------------------------------------------------------------------
  sec(3, 'Hypothesis and Research Questions');
  // -------------------------------------------------------------------------
  add(H2('3.1 Research questions'));
  add(P('**Research question 1 (computational validation, September 2026).** For degradations '
    + 'whose start times are controlled and recorded in advance, does a monitor that reads '
    + 'only the recorded signal warn before task performance crosses a degradation threshold, '
    + 'at a false-alarm rate low enough to be worth having.'));
  add(P('**Research question 2 (physical validation, preregistered 24 September 2026).** How '
    + 'early, and at what cost in false alarms, can a decoder-health monitor warn that a '
    + 'sensor array is degrading, and does the correlation-based validation the field relies '
    + 'on support the claims made from it.'));
  add(H2('3.2 Engineering goal'));
  add(P('To build a monitor that reads only the input signal of a decoder, and a test that '
    + 'measures the monitor\'s lead time and false-alarm rate against failure onsets fixed in '
    + 'advance, so that the result does not depend on a choice made after seeing the data.'));
  add(H2('3.3 Hypotheses'));
  add(P('**Hypothesis A (computational, submitted 15 September 2026).** For degradations whose '
    + 'start times are controlled and recorded in advance, a monitor reading only the input '
    + 'signal will warn before task performance crosses a degradation threshold, at a false '
    + 'alarm rate low enough to be worth having. The conditions for rejection were fixed in the '
    + 'same plan: the hypothesis is rejected if the warning usually arrives at or after the '
    + 'performance drop, or if the false-alarm requirement cannot be met at any operating '
    + 'point.'));
  add(P('**Hypothesis B (physical, frozen 24 September 2026).** The primary hypothesis, quoted '
    + 'from `physical/docs/09_PREREGISTRATION.md`, is that "for a monitor of the class proposed '
    + 'for deciding when to recalibrate, the lead time and false-alarm rate, measured against '
    + 'onsets fixed in advance with enough fault-free recording to bound the rate, fall outside '
    + 'what a deployed system could use." The secondary hypothesis is that "that monitor '
    + 'reaches the correlation the field reports as evidence, while those two measured '
    + 'quantities say it is unusable."'));
  add(P('Hypothesis B is judged by a rule fixed in the same document. The correlation is '
    + '~strong~ if the magnitude of any of three correlations (raw, with the time trend '
    + 'removed, and on changes between sessions) is 0.70 or more. The monitor is ~unusable~ if '
    + 'its median lead time is zero or negative, or if the 95% upper bound on its false-alarm '
    + 'rate is above the budget. The hypothesis is ~supported~ if the correlation is strong '
    + 'and the monitor is unusable, ~falsified~ if the correlation is strong and the monitor '
    + 'is usable on both counts, and ~inconclusive~ if no correlation reaches 0.70. Ten '
    + `specific predictions, PP-1 to PP-10, accompany it and are listed in ${T('predictions')}.`));
  add(table('questions', 'Research questions and hypotheses, with their present status.',
    [1500, 4160, 1900, 1800],
    ['Item', 'Statement in brief', 'Tested by', 'Status'],
    [
      ['Research question 1', 'Does the monitor warn early enough and rarely enough on planted '
        + 'faults in archived recordings', 'Computational validation', 'Answered: no'],
      ['Hypothesis A', 'Warning precedes failure at 0.1 false alarms per hour or fewer',
        'Computational validation', 'Rejected (Section 6.1)'],
      ['Research question 2', 'Lead time and false-alarm cost on a physical sensor array, and '
        + 'whether correlation supports the claims made from it', 'Physical validation',
        red('State answered or not answered', 'Section 11 of this paper', 'VI.4')],
      ['Hypothesis B, primary', 'Lead time and false-alarm rate fall outside what a deployed '
        + 'system could use', 'Experiments P-2 and P-3',
        red('Insert the verdict', 'physical/data/results/correlation_vs_usability.json',
          'IV.7')],
      ['Hypothesis B, secondary', 'The correlation is strong while the monitor is unusable',
        'Experiment P-4', red('Insert the verdict',
          'physical/data/results/correlation_vs_usability.json', 'IV.7')],
    ]));

  // -------------------------------------------------------------------------
  sec(4, 'Materials');
  // -------------------------------------------------------------------------
  add(H2('4.1 Archived recordings'));
  add(P('The computational validation uses the recordings that Pun et al. (2024a) released with '
    + 'their study of signal instability, archived on Dryad under a CC0 public-domain '
    + `dedication (Pun et al., 2024b). ${T('dataset')} summarises them. The files are public `
    + 'and de-identified. This project had no contact with the participants and collected no '
    + 'data from any person.'));
  add(table('dataset', 'The archived recordings.', [2800, 6560], ['Property', 'Value'], [
    ['Name and source', 'MINDFUL dataset, Pun et al. (2024b), Dryad, doi 10.5061/dryad.n2z34tn5s'],
    ['Licence', 'CC0 1.0 public-domain dedication'],
    ['Participants', 'Two BrainGate research participants, designated T11 and T5'],
    ['Time since implant', 'T11 about two years; T5 about six years'],
    ['Extent', '21 trial days, 54 blocks, 3,301 cursor trials; about 393 MB'],
    ['Handling', 'Downloaded once by `scripts/01_download_dataset.py`, with checksums, into '
      + '`data/raw/`, which is never modified'],
  ]));

  add(H2('4.2 Software'));
  add(P(`All analysis is written in Python and kept under version control with Git. `
    + `${T('software')} lists the libraries and the versions with which the repository's checks `
    + `were last run on ${meta.date}. \`requirements.txt\` gives the minimum versions.`));
  add(table('software', 'Software used.', [2600, 1900, 4860], ['Component', 'Version', 'Used for'],
    [
      ['Python', meta.versions.python, 'All scripts'],
      ['NumPy', meta.versions.numpy, 'Arrays and numerical work'],
      ['pandas', meta.versions.pandas, 'Tables of episodes and sessions'],
      ['SciPy', meta.versions.scipy, 'Kendall tau, Spearman correlation, exact intervals'],
      ['h5py', meta.versions.h5py, 'Reading the archived recording files'],
      ['Matplotlib', meta.versions.matplotlib, 'Figures written by the analysis scripts'],
      ['Git and GitHub', 'not applicable', 'Version control; the record of every change'],
      ['Bench computer: Raspberry Pi OS, picamera2, pygame',
        red('Insert the versions installed on the bench computer',
          'bench logbook, sheet B (build record)', 'III.3'),
        'Showing the stimulus and recording the camera (planned)'],
    ]));
  add(figure('repo', drawn('d_repo'), 'How the repository is organised.',
    'Each box is a folder or program that exists in the repository. The dashed box is empty '
    + 'until the bench has recorded.'));

  add(H2('4.3 Materials for the physical test bench'));
  add(P(`${T('bom')} is the bill of materials from \`physical/EXECUTIVE_SUMMARY.md\`. On `
    + `${meta.date} no part had been ordered. The estimated total is about 150 US dollars. `
    + 'Items 1 to 4 are on the critical path, because nothing can be tested without them. The '
    + 'right-hand columns are completed when the parts arrive, since a substituted part is a '
    + 'change to the apparatus that the paper must report.'));
  const bom = [
    ['Raspberry Pi 4 Model B, 4 GB', '55 to 65'],
    ['Raspberry Pi Camera Module 3, with its ribbon cable', '25 to 35'],
    ['microSD card, 32 to 64 GB, A2 or U3', '8 to 12'],
    ['Official USB-C power supply, 5 V 3 A', '8 to 12'],
    ['Display, at least 1280 × 720, with manual brightness', '0 to 40'],
    ['Cardboard box, at least 40 × 30 × 30 cm', '0 to 8'],
    ['Matte black lining for the box', '6 to 12'],
    ['Tripod or rigid bracket for the camera', '8 to 15'],
    ['Black gaffer or electrical tape', '6 to 10'],
    ['Neutral density gel filter, ND 0.6', '8 to 15'],
    ['28BYJ-48 stepper motor with ULN2003 driver board', '6 to 10'],
    ['Six female-to-female jumper wires, 20 cm', '5 to 8'],
    ['DHT22 (AM2302) temperature sensor on a breakout board with pull-up resistor', '5 to 10'],
    ['USB flash drive, 64 GB', '8 to 12'],
  ];
  add(table('bom', 'Bill of materials for the bench.', [460, 3700, 1000, 2000, 1000, 1200],
    ['No.', 'Item as specified', 'Estimate (USD)', 'Item actually used', 'Cost paid',
      'Date received'],
    bom.map(([item, cost], i) => [String(i + 1), item, cost, null, null, null]),
    { after: red('Complete the three pink columns for all fourteen items, and list any part '
      + 'that differs from the specification.', 'bench logbook, sheet B (build record)',
    'III.3') }));
  add(figureSpace('ph_parts', 'PHOTOGRAPH', 'All parts of the bench before assembly.',
    'Each part is labelled with its number in ' + `${T('bom')}.`,
    'All fourteen items laid out on a plain surface, each with a numbered label, a ruler in '
    + 'the frame for scale.', 'photograph PH-1', 'II.2', { height: 2.8 }));
  add(figureSpace('ph_components', 'PHOTOGRAPH',
    'The six components that carry the signal or are wired.',
    '(a) Raspberry Pi 4, (b) Camera Module 3 and ribbon, (c) display, (d) stepper motor and '
    + 'driver board, (e) temperature sensor, (f) neutral density filter.',
    'Six close photographs arranged in a grid of two rows and three columns, each lettered '
    + '(a) to (f).', 'photograph set PH-2', 'II.2', { height: 3.2 }));

  // -------------------------------------------------------------------------
  sec(5, 'Methods');
  // -------------------------------------------------------------------------
  add(H2('5.1 Design'));
  add(P('The same monitor is validated twice. The computational validation, which is complete, '
    + 'plants faults in archived recordings. The physical validation, which is planned, will '
    + 'impose faults on an optical apparatus. In both, the time at which each fault begins is '
    + 'fixed and sealed before the recording is analysed, and the monitor never sees the '
    + `decoder's performance. ${T('variables')} lists the variables. The monitor's settings, `
    + 'the analysis window and the false-alarm budget are identical in the two validations.'));
  add(table('variables', 'Variables.', [760, 2700, 3900, 2000],
    ['Code', 'Variable', 'Values or definition', 'Unit'], [
      ['IV1', 'Onset time of the fault', 'Drawn at random and sealed before recording',
        'seconds from start'],
      ['IV2', 'Fault present or absent', 'Degraded session or fault-free session', 'category'],
      ['IV3', 'Fault type', 'Signal loss, channel dropout, gain drift, rotation', 'category'],
      ['IV4', 'Severity', 'Bench: 0, 0.25, 0.5, 1.0. Archived recordings: three levels',
        'fraction of full fault'],
      ['IV5', 'Decision rate', '720 per hour down to one per session, set in analysis',
        'decisions per hour'],
      ['DV1', 'Lead time', 'Time of performance failure minus time of warning; positive means '
        + 'the warning came first', 'seconds'],
      ['DV2', 'False-alarm rate', 'Warnings during held-out fault-free recording, per hour',
        'per hour'],
      ['DV3', 'Detection rate', 'Degraded sessions warned after onset, out of all degraded '
        + 'sessions', 'percent'],
      ['DV4', 'Silence-gate result', 'Share of fault-free sessions whose risk score trends '
        + 'significantly with time', 'percent'],
      ['DV5', 'Correlation with performance', 'Spearman correlation of risk score with '
        + 'decoding error: raw, partial, first differences', 'none'],
      ['Controlled', 'Analysis window; decoder; camera exposure and gain; screen brightness; '
        + 'modulation depth; ambient light; geometry',
      '30 s window every 5 s; ridge decoder frozen after fitting; the five bench settings '
        + 'fixed after calibration, the box sealed, the geometry taped and photographed',
      'see Section 5.3'],
    ]));

  add(H2('5.2 Computational validation (completed)'));
  add(P(`${F('comp')} shows the procedure. Each step is a script in \`scripts/\` and writes its `
    + 'output to `data/processed/` and a report to `reports/`.'));
  add(figure('comp', drawn('d_comp'), 'The computational workflow.',
    'Numbers are the script numbers in `scripts/`. The order of the commits is part of the '
    + 'method: the fault plan was sealed before any detector existed, and the scoring harness '
    + 'was written before the monitor.'));
  add(P('**Planting the faults.** `scripts/17_fault_injector.py` planned '
    + `${N_EP.toLocaleString()} episodes (${S.episodes.T11.toLocaleString()} on T11 and `
    + `${S.episodes.T5} on T5). Each episode is one recorded block with one fault applied to `
    + `its neural features, or with none. Four fault types were used (${T('faults')}), at `
    + 'three severities and three ramp rates. The onset was drawn uniformly between 25% and '
    + '55% of the way through the episode, and the fault then grew linearly to full strength '
    + 'over 10%, 35% or 80% of the time remaining. All random draws came from one master seed '
    + `(20260826). The plan was written to disk with a SHA-256 checksum and committed (commit `
    + `\`${S.injection_commit}\`) before any detector had been written, so no detector could `
    + 'be tuned to the onsets.'));
  add(table('faults', 'The four fault types and how each is imposed.', [1900, 2760, 2200, 2500],
    ['Fault type', 'What changes in the signal', 'In archived recordings', 'On the bench (planned)'],
    [
      ['RATE_LOSS (signal loss)', 'Activity falls on all channels together',
        'Applied by script', 'By hand: a neutral density filter slid in front of the lens'],
      ['CHANNEL_DROPOUT', 'A subset of channels goes silent', 'Applied by script',
        'By hand: tape placed over part of the field of view'],
      ['GAIN_DRIFT', 'Each channel\'s gain drifts separately; the total is unchanged',
        'Applied by script', 'By software, automatically'],
      ['GEOMETRY_ROTATION', 'The pattern across channels rotates; the total is unchanged',
        'Applied by script', 'By software, automatically'],
    ]));
  add(P('**Measuring performance.** `scripts/18_reference_decoder.py` fits a ridge-regression '
    + 'decoder of intended cursor direction once, on the fitting split, and then freezes it, '
    + 'together with its normalisation. Performance is the angular error between the decoded '
    + 'and the intended direction. On validation data the median error was '
    + `${n(S.decoder_error_deg.T11, 1)}° for T11 and ${n(S.decoder_error_deg.T5, 1)}° `
    + `for T5, against measured chance levels of ${n(S.decoder_chance_deg.T11, 1)}° and `
    + `${n(S.decoder_chance_deg.T5, 1)}°. Within an episode, performance has failed at the `
    + `first window whose error is ${PD.performance_threshold_deg}° or more above the `
    + 'episode\'s own level before the onset.'));
  add(P('**The monitor.** `scripts/22_decoder_guard.py` implements the monitor, decoder-guard '
    + `(${F('monitor')}). It reads the logarithm of the activity on every channel in a window `
    + `of ${PD.window_s} seconds that advances every ${PD.step_s} seconds. It is fitted only on `
    + 'windows from healthy recording. It computes four named components and reports the '
    + 'largest as the risk score, together with the name of the component, so that a warning '
    + 'states what kind of change was seen. It never receives the decoder\'s output or the '
    + 'task performance.'));
  add(figure('monitor', drawn('d_monitor'), 'The monitor, decoder-guard.',
    'Four components, each sensitive to a different kind of change in the recorded signal.',
    { width: 560 }));
  add(P('**Scoring.** `scripts/20_evaluation_harness.py` divides the recorded blocks into three '
    + 'groups that share no block: fitting, validation and test. The harness was committed '
    + 'before the monitor was written. `scripts/21_score_report.py` then chooses one setting, '
    + 'the WARN threshold, as the lowest threshold that keeps false alarms at or below '
    + `${S.budget_per_hour} per hour on the validation group, and applies it unchanged to the `
    + 'test group, which is read once. Lead time is the time of performance failure minus the '
    + 'time of the first warning after onset, so a negative lead time means the warning came '
    + `after the failure. ${F('episode')} shows one episode in full.`));
  add(figure('episode', drawn('c_episode'), 'One planted fault, from onset to warning.',
    `Episode ${EP.id} (${EP.block}, ${EP.mode.replace('_', ' ').toLowerCase()}), chosen by rule `
    + 'as the first test episode whose lead time equals the median. Decoding fails at window '
    + `${EP.crossing_w}; the warning comes at window ${EP.warn_w}, ${n(-EP.lead_s)} s later and `
    + `${n(EP.detection_delay_s)} s after the onset at window ${EP.onset_w}.`));
  add(P(`**Gates.** A result counts only if the monitor also passes five gates fixed in `
    + `advance (${T('gates_comp')}). They exist because a monitor can appear to detect faults `
    + 'while in fact responding to elapsed time or to overall activity.'));
  add(table('gates_comp', 'The five gates of the computational validation.',
    [1500, 3360, 2700, 1800], ['Gate', 'Question', 'Statistic', 'Passes if'], [
      ['G1 Silence', 'Does the risk score stay flat when nothing is wrong',
        'Kendall tau of risk against window number, per healthy episode',
        'fewer than 10% significant at p < 0.05'],
      ['G2 Rate', 'Is the score more than a measure of overall activity',
        'median |Spearman| between risk and mean activity', 'below 0.6'],
      ['G3 Comparator', 'Does it beat the simplest alternative',
        'median lead time against a mean-activity detector at the same false-alarm rate',
        'longer lead time'],
      ['G4 Time', 'Is the score more than a clock',
        'median |Spearman| between risk and window number', 'below 0.5'],
      ['G5 Detrend', 'Does G1 pass once a straight line is removed',
        'G1 repeated after linear detrending', 'fewer than 10% significant'],
    ]));
  add(P('**Statistics.** Medians are reported with 95% bootstrap intervals that resample whole '
    + 'episodes, because the windows inside an episode overlap and are not independent. The '
    + 'dependence is measured by the lag-1 autocorrelation r of the risk score, and the '
    + 'effective number of independent windows among n is'));
  add(formula('n_eff = n (1 − r) / (1 + r)'));
  add(P('**Breadth and verification.** `scripts/24_benchmark_matrix.py` ran '
    + `${S.funnel.run} combinations of participant, reference period, preprocessing and `
    + 'detector, and `reports/BENCHMARK_SUMMARY.md` reports every one. The repository checks '
    + 'itself: `tools/check_all.py` runs 13 checks, among them 50 unit tests and '
    + '`scripts/31_verify_claims.py`, which recomputes 102 headline numbers from the data files '
    + 'and fails if any report disagrees.'));

  add(H2('5.3 Physical validation (planned and preregistered; not yet carried out)'));
  add(note('Everything in this subsection is a plan. It is written in the future tense because '
    + 'none of it has been done. The plan was frozen on 24 September 2026 in '
    + '`physical/docs/09_PREREGISTRATION.md` (commit `f4dda04`) and that file must not be '
    + 'edited. Any departure from the plan will be recorded in Table '
    + `${L.tabNo('deviations')}.`, { bar: 'B24E0A', fill: 'FDF3E9' }));
  add(P(`**Apparatus.** ${F('chain')} shows the signal chain. A display will show 384 patches `
    + '(24 columns by 16 rows, each 40 pixels square) at 50 frames per second. Each patch has '
    + 'its own preferred direction. When the program picks a direction, the patches whose '
    + 'preference matches it become slightly brighter and the others slightly dimmer, in the '
    + 'way that a direction-tuned neuron fires fastest for its preferred direction. Each '
    + 'direction is held for 100 frames, and the program records the true direction of every '
    + 'frame. The change in brightness is deliberately small (a planned modulation depth of '
    + '0.00211 around a base level of 0.5) and is produced by spatial dithering, because a '
    + 'pattern that is easy to decode would leave nothing for a monitor to detect. A camera in a '
    + 'sealed, black-lined box will record the display at 48 by 32 pixels, and the mean of '
    + 'each patch will form one of 384 channels, the same number of features as in the '
    + 'archived recordings. A Raspberry Pi 4 will show the stimulus and record the camera. The '
    + 'same decoder design and the same monitor will then run on the camera channels. The '
    + 'apparatus contains no biological material and involves no human participant.'));
  add(figure('chain', bench('fig-chain'), 'The signal chain of the bench.',
    'Drawing from `physical/figures/`. It is a design drawing, not a photograph of a built '
    + 'apparatus.', { width: 520 }));
  add(figure('benchflow', bench('fig-workflow'), 'The workflow of the physical validation.',
    'Drawing from `physical/figures/`. Build, verify, calibrate, record, analyse.',
    { width: 400 }));
  add(P(`**Wiring.** Two parts will be wired to the Raspberry Pi's 40-pin header with jumper `
    + `wires; the design uses no breadboard. ${F('wiring_stepper')} and ${F('wiring_dht22')} `
    + 'show the connections. The stepper driver inputs IN1 to IN4 will connect to GPIO 17, 27, '
    + '22 and 23 (physical pins 11, 13, 15 and 16), with power from pin 2 (5 V) and ground at '
    + 'pin 9, as set in `rig/motor.py`. The temperature sensor\'s data line will connect to '
    + 'GPIO 4 (pin 7), as set in `rig/logtemp.py`. The supply pins for the sensor (pin 1, '
    + '3.3 V, and pin 9, ground) are a recommendation of the project documents and are not '
    + 'fixed by any file in the repository, so the pins actually used will be recorded: '
    + red('State the supply and ground pins actually used for the temperature sensor.',
      'bench logbook, sheet B (build record)', 'III.3')));
  add(figure('wiring_stepper', bench('wiring-stepper'), 'Wiring of the stepper motor driver.',
    'Drawing from `physical/figures/`, generated from the pin numbers in `rig/motor.py`.'));
  add(figure('wiring_dht22', bench('wiring-dht22'), 'Wiring of the temperature sensor.',
    'Drawing from `physical/figures/`. The data pin is set in `rig/logtemp.py`; the supply '
    + 'pins are a recommendation.'));
  add(P('**Sealing the onsets.** Before any session is recorded, `physical/code/draw_onset.py` '
    + 'will draw whether the session is fault-free or degraded and, if degraded, the fault '
    + 'type, the severity and the onset time, and will write the plan with a checksum to '
    + `\`physical/data/onsets/\` (${F('onset')}). \`run_session.py\` will refuse to record a `
    + 'session that has no sealed plan.'));
  add(figure('onset', bench('fig-onset'), 'How the onset of each fault is fixed before recording.',
    'Drawing from `physical/figures/`.', { width: 520 }));
  add(P(`**Acceptance gates and calibration.** No result will be read until the apparatus has `
    + `passed five gates (${T('gates_bench')}). The last gate sets the difficulty of the `
    + 'decoding task. On T11 the margin between chance and decoding error was '
    + `${n(S.decoder_chance_deg.T11, 1)}° − ${n(S.decoder_error_deg.T11, 1)}° = `
    + `${n(margin11, 1)}°. The modulation depth will be adjusted, one setting at a time, `
    + `until the bench margin is within 6° of that value (${F('calib')}), and will then be `
    + 'fixed for every later session. The planned starting depth is 0.00211. The values '
    + 'actually used will be reported here: '
    + red('Insert the final modulation depth, the camera exposure and gain, the screen '
      + 'brightness setting, and the measured distance from camera to display.',
    'bench logbook, sheet B (build record); physical/data/raw/SESSION_LOG.csv', 'III.3')));
  add(table('gates_bench', 'Acceptance gates for the apparatus.', [800, 2700, 3260, 2600],
    ['Gate', 'What it checks', 'Passes if', 'Program'], [
      ['G-a', 'The box is dark', 'with the display off, mean pixel below 2 and maximum below 5, '
        + 'out of 255', '`bench.py darkframe`'],
      ['G-b', 'Frames and channels are sound', 'fewer than 1% late frames, fewer than 5% dead '
        + 'channels, fewer than 1% clipped', '`bench.py frames`'],
      ['G-c', 'The delay from display to camera is stable', 'the measured delay agrees across '
        + 'three recordings', '`bench.py lag`'],
      ['G-d', 'The camera sees the modulation', 'median agreement above 0.02 and positive on '
        + 'more than 80% of channels', '`bench.py dither`'],
      ['G-e', 'The task is as hard as the neural one', `margin within 6° of `
        + `${n(margin11, 1)}°`, '`bench.py margin`'],
    ]));
  add(figure('calib', bench('fig-calib'), 'The calibration loop that sets the difficulty.',
    'Drawing from `physical/figures/`.', { width: 520 }));
  add(P(`**Experiments.** Seven experiments are planned (${T('experiments')}), 337 sessions of `
    + 'five minutes (15,000 frames) each, about 28 hours of recording and about 8 GB of data. '
    + 'The number of fault-free sessions, 101, is frozen. If time runs short, experiments will '
    + 'be cut in a fixed order (P-5, then P-7, then the middle severity of P-3). P-2 and P-6 '
    + 'will not be cut.'));
  add(table('experiments', 'The seven experiments of the physical validation.',
    [700, 3460, 1000, 1300, 2900],
    ['Code', 'Purpose', 'Sessions', 'Recording', 'How it is carried out'], [
      ['P-1', 'Calibration: set and record the modulation depth', '5', '25 min',
        'Attended; these sessions also fit the decoder and the monitor'],
      ['P-2', 'False-alarm rate and silence gate on fault-free recording', '101', '8.4 h',
        'Unattended, one night'],
      ['P-3', 'Lead time and detection on sealed faults: four types, three severities',
        '101', '8.4 h', 'Software faults unattended; filter and tape faults by hand'],
      ['P-4', 'Correlation against usability: the test of Hypothesis B', '0', 'none',
        'Analysis of the P-2 and P-3 sessions'],
      ['P-5', 'Faults that nobody designed: connector, filter, fingerprint, rotation, heat',
        '10', '50 min', 'By hand; onset noted from a clock; analysed separately'],
      ['P-6', 'Detection against decision rate', '0', 'none', 'Analysis of the same sessions'],
      ['P-7', 'Three further apparatus configurations (B, C, D)', '120', 'about 10 h',
        'Unattended; 40 sessions each'],
    ]));
  add(P('**Photographic record of the apparatus as built.** The following figures will show the '
    + 'apparatus that produced the data. They are photographs and screenshots of the real '
    + 'bench. None exists yet, and none will be replaced by a drawing or a generated image.'));
  add(figureSpace('ph_open', 'PHOTOGRAPH', 'The complete apparatus with the enclosure open.',
    'Labels: display, camera on its mount, Raspberry Pi, stepper motor and driver, '
    + 'temperature sensor, power supply.',
    'The whole bench from the front and slightly above, lid open, every labelled part '
    + 'visible, a ruler or tape measure in the frame.', 'photograph PH-3', 'II.2',
    { height: 3.4 }));
  add(figureSpace('ph_sealed', 'PHOTOGRAPH', 'The apparatus sealed, as it is during recording.',
    'The enclosure closed and taped along every seam.',
    'The same viewpoint as the figure before it, lid closed and taped, cables leaving through '
    + 'the sealed slot.', 'photograph PH-4', 'II.2', { height: 2.6 }));
  add(figureSpace('ph_header', 'PHOTOGRAPH',
    'Close view of the wiring at the Raspberry Pi header and the driver board.',
    'Jumper wires from the header to the stepper driver.',
    'Taken from directly above, in focus, with pin 1 of the header identifiable and every '
    + 'wire traceable from end to end.', 'photograph PH-5', 'II.2', { height: 3.0 }));
  add(figureSpace('ph_annotated', 'PHOTOGRAPH',
    'The same wiring, annotated and set beside the wiring drawing.',
    `Each wire is labelled with its pin number and matches ${F('wiring_stepper')}.`,
    'A copy of the previous photograph with a text label on each wire (signal name, GPIO '
    + 'number, physical pin), placed next to the wiring drawing.',
    'photograph PH-6, made from PH-5', 'II.4', { height: 3.0 }));
  add(figureSpace('ph_sensor', 'PHOTOGRAPH', 'The temperature sensor and the power connections.',
    'Three sensor wires and the official power supply.',
    'The sensor breakout with its three wires traceable to the header, and the power supply '
    + 'connection.', 'photograph PH-7', 'II.2', { height: 2.4 }));
  add(figureSpace('ph_inside', 'PHOTOGRAPH', 'Inside the enclosure.',
    'Black lining, display position, camera mount and the holder for the filter.',
    'The interior before sealing: lining, display, camera aimed at the display, the measured '
    + 'camera-to-display distance shown by a tape measure.', 'photograph PH-8', 'II.2',
    { height: 2.8 }));
  add(figureSpace('ss_session', 'SCREENSHOT', 'The software during a recording session.',
    'The terminal output of `run_session.py` and the stimulus pattern.',
    'The terminal with the session and block number, the sealed plan it loaded and the '
    + 'start time, with the stimulus display visible or inset.', 'screenshot SS-1', 'II.3',
    { height: 2.6 }));
  add(figureSpace('ss_check', 'SCREENSHOT', 'The acceptance gates passing.',
    'Output of `bench.py check` on the calibration session.',
    'The full output listing gates G-a to G-e with the measured value and the word PASS for '
    + 'each, with the date visible.', 'screenshot SS-2', 'II.3', { height: 2.4 }));
  add(P(`**Data flow and analysis.** ${F('dataflow')} shows where every file will go. Raw `
    + 'recordings will be kept in `physical/data/raw/` and never edited. '
    + '`make_session_table.py` will decode and score every session and assign it to one of '
    + 'three groups that share no session: a fitting group, a group used only to choose the '
    + 'warning threshold, and a reporting group. One analysis program per experiment will then '
    + 'write a report and a data file to `physical/data/results/`. The reports will not be '
    + 'edited by hand.'));
  add(figure('dataflow', drawn('d_dataflow'), 'Data flow of the physical validation.',
    'Every box is a program or file named in `physical/code/` or `physical/data/`.'));
  add(P(`${F('stats')} sets out the statistical treatment, which was fixed in the `
    + 'preregistration. The false-alarm rate is k warnings in H held-out fault-free hours, '
    + 'with an exact Poisson 95% interval. If k is zero the result is an upper bound of about '
    + '3/H per hour, not a rate of zero. Lead time is summarised by its median with a '
    + 'bootstrap interval of 5,000 resamples, reported only when at least three sessions '
    + 'contribute. A warning whose window ends before the onset is counted as a false alarm, '
    + 'not as a detection. Detection proportions carry Wilson 95% intervals. The three '
    + 'correlations are Spearman coefficients.'));
  add(figure('stats', drawn('d_stats'), 'Statistical analysis of the physical validation.',
    'Each row runs from a measured quantity to the decision that was fixed in advance.'));
  add(P('**Risk and safety.** The bench runs at 5 V from an official power supply and has no '
    + 'mains wiring made by the student. The stepper motor is small and hands will be kept '
    + 'clear while it is powered. In experiment P-5 one intervention uses a hair dryer on its '
    + 'lowest setting, at least 30 cm away, for no more than 60 seconds, with components kept '
    + 'below 50 °C and an adult present. No human participants, vertebrate animals, '
    + 'hazardous biological agents or hazardous chemicals are involved.'));
  add(P('**Record of the recording campaign.** '
    + red('Insert the dates on which each experiment was recorded, the room, the range of '
      + 'temperature logged, and who was present for the attended sessions.',
    'bench logbook, sheets C and D; physical/data/raw/SESSION_LOG.csv', 'III.4')));

  // -------------------------------------------------------------------------
  sec(6, 'Results');
  // -------------------------------------------------------------------------
  add(H2('6.1 Computational validation'));
  add(P(`${T('r_headline')} gives the main result. At the threshold chosen on validation data, `
    + `the monitor detected ${det11} of ${deg11} test faults on T11 `
    + `(${pct(det11 / deg11)}) and ${det5} of ${deg5} on T5 (${pct(det5 / deg5)}). Where it did `
    + `warn, the median lead time was ${n(S.median_lead_s.T11)} s on T11 (95% interval `
    + `${n(S.lead_ci95_s.T11[0])} to ${n(S.lead_ci95_s.T11[1])} s) and ${n(S.median_lead_s.T5)} `
    + 's on T5, where six detections are too few for an interval. A negative lead time means '
    + 'that the warning arrived after decoding had already failed. The false-alarm rate on '
    + `held-out healthy recording was ${n(S.false_alarms_per_hour.T11, 2)} per hour on T11 and `
    + `${n(S.false_alarms_per_hour.T5, 2)} per hour on T5, against a budget of `
    + `${S.budget_per_hour}.`));
  add(table('r_headline', 'Main result of the computational validation (test split).',
    [3960, 1800, 1800, 1800], ['Quantity', 'T11', 'T5', 'Required'], [
      ['Planted episodes', S.episodes.T11.toLocaleString(), String(S.episodes.T5), 'none'],
      ['Faults detected, test split', `${det11} of ${deg11}`, `${det5} of ${deg5}`, 'none'],
      ['Median lead time (s)', n(S.median_lead_s.T11), n(S.median_lead_s.T5), 'above 0'],
      ['95% interval of the median (s)', `${n(S.lead_ci95_s.T11[0])} to `
        + `${n(S.lead_ci95_s.T11[1])}`, 'too few detections', 'excludes 0'],
      ['False alarms per hour', n(S.false_alarms_per_hour.T11, 2),
        n(S.false_alarms_per_hour.T5, 2), `${S.budget_per_hour} or fewer`],
      ['Healthy test recording (hours)', n(HS.T11.healthy_hours_test, 2),
        n(HS.T5.healthy_hours_test, 2), 'none'],
      ['Gates passed', `${S.gates_passed.T11[0]} of ${S.gates_passed.T11[1]}`,
        `${S.gates_passed.T5[0]} of ${S.gates_passed.T5[1]}`, 'all five'],
    ], { after: 'Source: `data/processed/harness_summary_local.json` and '
      + '`harness_summary_T5_local.json`, detector decoder-guard.' }));
  add(figure('lead', drawn('c_lead'), 'Lead time of every detected fault on T11.',
    `One dot per detection (${det11}). ${pct(LT.T11.fraction_negative)} of warnings came after `
    + `the failure, ${pct(LT.T11.fraction_zero)} in the same window, and `
    + `${pct(LT.T11.fraction_positive)} before it.`));
  add(figure('fa', drawn('c_fa'), 'False alarms and the silence gate.',
    'Measured false-alarm rates against the budget, and the share of episodes with no planted '
    + 'fault whose risk score nevertheless trended with time.'));
  add(P(`**Gates.** ${T('r_gates')} gives the verdict on each gate. The monitor passed two of `
    + 'five on each array. It beat the mean-activity comparator (G3) and passed the silence '
    + 'test once a straight line was removed (G5). It failed the silence gate itself (G1): the '
    + 'risk score rose with time in nearly every episode in which decoding did not fail. '
    + `Restricted to the episodes with no planted fault at all, ${ff11} of `
    + `${S.fault_free_episodes.T11} on T11 and ${ff5} of ${S.fault_free_episodes.T5} on T5 `
    + `showed a significant `
    + 'trend. It also failed G2 and G4: its score followed overall activity and elapsed time '
    + 'more closely than the gates allow.'));
  const g = (p, k, f) => HS[p].gates[k][f];
  add(table('r_gates', 'Gate verdicts for decoder-guard (test split).',
    [1700, 3260, 1500, 1500, 1400], ['Gate', 'Statistic', 'T11', 'T5', 'Verdict'], [
      ['G1 Silence', 'share of healthy episodes with a significant trend',
        pct(g('T11', 'G1_silence', 'fraction_significant')),
        pct(g('T5', 'G1_silence', 'fraction_significant')), 'fail'],
      ['G2 Rate', 'median |Spearman| with mean activity',
        n(g('T11', 'G2_rate_invariance', 'median_abs_rho_vs_mean_activity'), 3),
        n(g('T5', 'G2_rate_invariance', 'median_abs_rho_vs_mean_activity'), 3), 'fail'],
      ['G3 Comparator', 'median lead time; comparator in brackets (s)',
        `${n(g('T11', 'G3_comparator', 'median_lead_s'))} `
        + `(${n(g('T11', 'G3_comparator', 'baseline_lead_s'))})`,
        `${n(g('T5', 'G3_comparator', 'median_lead_s'))} `
        + `(${n(g('T5', 'G3_comparator', 'baseline_lead_s'))})`, 'pass'],
      ['G4 Time', 'median |Spearman| with window number',
        n(g('T11', 'G4_elapsed_time', 'median_abs_rho_vs_time'), 3),
        n(g('T5', 'G4_elapsed_time', 'median_abs_rho_vs_time'), 3), 'fail'],
      ['G5 Detrend', 'share still significant after detrending',
        pct(g('T11', 'G5_detrend', 'fraction_significant_after_detrend')),
        pct(g('T5', 'G5_detrend', 'fraction_significant_after_detrend')), 'pass'],
    ], { after: `Healthy episodes are test episodes in which decoding never failed: `
      + `${g('T11', 'G1_silence', 'n_healthy_episodes')} on T11 and `
      + `${g('T5', 'G1_silence', 'n_healthy_episodes')} on T5.` }));
  add(P(`**By fault type.** ${F('modes')} and ${T('r_modes')} compare decoder-guard with the `
    + 'mean-activity detector for each fault type, using the area under the ROC curve (AUC) '
    + 'for separating faulty from healthy windows, where 0.5 is chance and 1.0 is perfect. '
    + 'Decoder-guard is better on the two faults that leave total activity unchanged (gain '
    + 'drift and rotation), where mean activity is at or below chance. It is worse on plain '
    + 'signal loss, which mean activity detects directly.'));
  add(figure('modes', drawn('c_modes'), 'Detection by fault type.',
    'AUC at the level of single windows, decoder-guard against a detector that uses mean '
    + 'activity alone.'));
  const names = { RATE_LOSS: 'Signal loss', CHANNEL_DROPOUT: 'Channel dropout',
    GAIN_DRIFT: 'Gain drift', GEOMETRY_ROTATION: 'Rotation' };
  add(table('r_modes', 'Window-level AUC by fault type.', [2760, 1650, 1650, 1650, 1650],
    ['Fault type', 'decoder-guard, T11', 'mean activity, T11', 'decoder-guard, T5',
      'mean activity, T5'],
    M.modes.map((m, i) => [names[m], n(M.values.T11.decoder_guard[i], 3),
      n(M.values.T11.mean_activity[i], 3), n(M.values.T5.decoder_guard[i], 3),
      n(M.values.T5.mean_activity[i], 3)]),
    { after: 'Source: `data/processed/episode_scores_local.csv` and '
      + '`episode_scores_T5_local.csv`.' }));
  add(P(`**Across thresholds and configurations.** The result does not depend on the one `
    + `threshold chosen. ${F('dfa')} shows detection against false-alarm rate as the threshold `
    + 'is varied. The budget can be met only by raising the threshold until the monitor '
    + `detects almost nothing: the best detection rate inside the budget was `
    + `${pct(DFA.best_inside_budget_T11)} on T11 and ${pct(DFA.best_inside_budget_T5)} on T5. `
    + 'Of the '
    + `${S.funnel.run} configurations in the benchmark, ${S.funnel.operating_point} had a `
    + `usable operating point, ${S.funnel.positive_lead} had a positive median lead time, `
    + `${S.funnel.met_budget} met the false-alarm budget, ${S.funnel.silence} passed the `
    + `silence gate, and ${S.funnel.all_gates} passed all five gates.`));
  add(figure('dfa', drawn('c_dfa'), 'Detection against false-alarm rate as the threshold varies.',
    'Each curve is one array. The vertical line is the budget of 0.1 false alarms per hour.'));
  add(P('**Why the budget is hard to meet.** A monitor that decides every 5 seconds makes 720 '
    + `decisions an hour. A budget of ${S.budget_per_hour} false alarms per hour then allows a `
    + `false-positive rate of ${S.fpr_per_decision_720.toFixed(6)} per decision. Pooling the `
    + `windows of an episode into one decision (${n(S.windows_per_session.T11)} windows on T11, `
    + `${n(S.windows_per_session.T5)} on T5) loosens this, but the AUC then needed is still `
    + `${n(S.auc_needed_at_budget.T11, 3)} and ${n(S.auc_needed_at_budget.T5, 3)}, against `
    + `${n(S.auc_session.T11, 3)} and ${n(S.auc_session.T5, 3)} achieved (${F('gap')}). `
    + `${F('decision')} shows detection measured directly at each decision rate.`));
  add(figure('gap', drawn('c_gap'), 'Achieved and required discrimination at one decision per episode.',
    'Episode-level AUC achieved by the monitor, and the AUC that the false-alarm budget '
    + 'requires. Source: `reports/OPERATING_POINT_BOUND.md`.'));
  add(figure('decision', drawn('c_decision'), 'Detection against decision rate.',
    'The same recordings re-scored from one decision per window to one per episode, with the '
    + 'threshold chosen afresh at each rate. Source: `reports/DECISION_RATE_CURVE.md`.'));
  add(P('Tested as a paired comparison, deciding less often changed detection by '
    + `${n(100 * PAIR.T11.own_range.change, 1)} percentage points on T11 (95% interval `
    + `${n(100 * PAIR.T11.own_range.ci95[0], 1)} to ${n(100 * PAIR.T11.own_range.ci95[1], 1)}; `
    + 'the interval includes zero, so the change is not established) and by '
    + `${n(100 * PAIR.T5.own_range.change, 1)} points on T5 (interval `
    + `${n(100 * PAIR.T5.own_range.ci95[0], 1)} to ${n(100 * PAIR.T5.own_range.ci95[1], 1)}; `
    + 'a decrease). The two arrays therefore disagree in direction.'));
  add(P('**Dependence between windows.** The lag-1 autocorrelation of the risk score was '
    + `${n(S.lag1_pooled.T11, 4)} on T11 and ${n(S.lag1_pooled.T5, 4)} on T5. By the formula `
    + `in Section 5.2, an episode of ${n(S.windows_per_session.T11)} windows on T11 then holds `
    + `the information of about ${n(S.n_eff_pooled.T11, 2)} independent windows, and an episode `
    + `of ${n(S.windows_per_session.T5)} windows on T5 about ${n(S.n_eff_pooled.T5, 2)}. This `
    + 'is why all intervals in this paper resample whole episodes.'));
  add(P('**Sessions differ.** On T11 the monitor\'s window-level AUC ranged from '
    + `${n(SC.auc_min, 2)} to ${n(SC.auc_max, 2)} across ${SC.n_sessions} sessions, and was `
    + 'lower in sessions where the frozen decoder was already less accurate (Spearman \u03C1 = '
    + `${n(SC.spearman_rho, 3)}, p = ${SC.p.toFixed(4)}; a `
    + 'preregistered test). On the real, unaltered series of '
    + `${SL.n_sessions} sessions in ${F('drift')}, the session-level monitor score and decoder `
    + `error were correlated with magnitude ${n(Math.abs(SL.raw), 2)} raw, `
    + `${n(Math.abs(SL.partial), 2)} with the time trend removed and `
    + `${n(Math.abs(SL.diff), 2)} on session-to-session changes. This last analysis was `
    + 'exploratory and was not preregistered.'));

  add(H2('6.2 Physical validation'));
  add(note('This subsection cannot be written yet. The tables are laid out exactly as the '
    + 'analysis programs will report them, so that each value can be copied from one named '
    + 'file. Values produced by `dryrun.py` are synthetic rehearsal output and must never be '
    + 'entered here.', { bar: 'B24E0A', fill: 'FDF3E9' }));
  add(H3('6.2.1 Apparatus acceptance'));
  add(table('b_gates', 'Results of the five acceptance gates.', [800, 3160, 2400, 1200, 1800],
    ['Gate', 'Criterion', 'Measured value', 'Pass or fail', 'Date'], [
      ['G-a', 'mean pixel below 2, maximum below 5', null, null, null],
      ['G-b', 'late frames below 1%, dead channels below 5%, clipped below 1%', null, null, null],
      ['G-c', 'delay agrees across three recordings', null, null, null],
      ['G-d', 'median agreement above 0.02, positive on more than 80% of channels', null, null,
        null],
      ['G-e', `margin within 6° of ${n(margin11, 1)}°`, null, null, null],
    ], { after: red('Fill the pink cells from the output of the bench check, and state in one '
      + 'sentence whether all five gates passed before any experimental session was recorded.',
    'output of physical/code/bench.py check; physical/data/lag.json; bench logbook, sheet B',
    'III.3') }));
  add(H3('6.2.2 Sessions recorded'));
  add(table('b_sessions', 'Sessions planned, recorded, excluded and analysed.',
    [1560, 1300, 1300, 1300, 1300, 2600],
    ['Experiment', 'Planned', 'Recorded', 'Excluded', 'Analysed', 'Recording dates'], [
      ['P-1 calibration', '5', null, null, null, null],
      ['P-2 fault-free', '101', null, null, null, null],
      ['P-3 sealed faults', '101', null, null, null, null],
      ['P-5 undesigned', '10', null, null, null, null],
      ['P-7 configuration B', '40', null, null, null, null],
      ['P-7 configuration C', '40', null, null, null, null],
      ['P-7 configuration D', '40', null, null, null, null],
      ['Total', '337', null, null, null, null],
    ], { after: red('Fill the pink cells, and give the reason for every excluded session.',
      'physical/data/sessions.csv; physical/data/EXCLUSIONS.csv; '
      + 'physical/data/processed/table_meta.json', 'IV.2') }));
  add(figureSpace('g_session', 'GRAPH', 'One bench session in detail.',
    'Risk score against time for one degraded session, with the sealed onset, the performance '
    + 'failure and the warning marked.',
    'Use the figure written by the analysis software. State in the caption which session it '
    + 'is and the rule by which it was chosen.',
    'physical/data/figures/session_detail.png', 'V.2', { height: 2.6 }));
  add(H3('6.2.3 Experiment P-2: false-alarm rate and silence gate'));
  add(table('b_fa', 'False-alarm rate and silence gate on fault-free bench recording.',
    [4360, 2500, 2500], ['Quantity', 'Frozen decoder', 'Decoder refitted per session'], [
      ['Held-out fault-free sessions', null, null],
      ['Held-out fault-free recording (hours), H', null, null],
      ['False alarms, k', null, null],
      ['False-alarm rate, k / H (per hour)', null, null],
      ['95% interval of the rate (per hour)', null, null],
      ['Upper bound if k = 0 (per hour)', null, null],
      ['Hours needed to demonstrate the budget', null, null],
      ['Within the budget of 0.1 per hour (yes or no)', null, null],
      ['Silence gate: share of sessions trending', null, null],
      ['Silence gate: median Kendall tau', null, null],
      ['Silence gate: pass or fail', null, null],
      ['After detrending: share trending; pass or fail', null, null],
    ], { after: red('Fill the pink cells for both decoders.',
      'physical/data/results/false_alarm.json (frozen) and the same file from the run tagged '
      + '_persession', 'IV.3') }));
  add(...writeSpace(red('Describe the false-alarm result in words. Report the upper end of the '
    + 'interval, not only the rate. If there were no false alarms, report the upper bound and '
    + 'state that the campaign cannot distinguish a quiet monitor from a noisy one. Then '
    + 'state whether the silence gate passed, raw and detrended.',
  'Table 15 of this paper; physical/data/results/P2_FALSE_ALARM_RATE.md', 'VI.7'), 1.5));
  add(figureSpace('g_fa', 'GRAPH', 'False-alarm evidence on the bench.',
    'The upper bound on the false-alarm rate against hours of fault-free recording, with the '
    + 'budget marked.', 'Use the figure written by the analysis software.',
    'physical/data/figures/false_alarm_evidence.png', 'V.2', { height: 2.6 }));
  add(H3('6.2.4 Experiment P-3: lead time and detection'));
  const leadHead = ['Sessions', 'Detected', 'Detection rate (95% interval)',
    'Warned before onset', 'Median detection delay, s (95% interval)',
    'Median lead time, s (95% interval)'];
  const leadW = [1760, 900, 900, 1500, 1000, 1650, 1650];
  add(table('b_lead_type', 'Lead time and detection by fault type.', leadW,
    ['Fault type', ...leadHead],
    ['RATE_LOSS', 'CHANNEL_DROPOUT', 'GAIN_DRIFT', 'GEOMETRY_ROTATION', 'All types']
      .map((r) => [r, null, null, null, null, null, null]),
    { after: red('Fill the pink cells. Report the false-alarm rate from Table 15 in the same '
      + 'sentence as any lead time.', 'physical/data/results/lead_time.json, blocks overall '
      + 'and by_fault_type', 'IV.5') }));
  add(table('b_lead_sev', 'Lead time and detection by severity.', leadW,
    ['Severity', ...leadHead],
    ['0.25', '0.5', '1.0'].map((r) => [r, null, null, null, null, null, null]),
    { after: red('Fill the pink cells.', 'physical/data/results/lead_time.json, block '
      + 'by_severity', 'IV.5') }));
  add(...writeSpace(red('Describe the lead-time result in words: the detection rate, the '
    + 'median lead time and its interval, the median detection delay, how many sessions '
    + 'warned before the onset (these are false alarms), how many faults never caused a '
    + 'failure, and which fault types differed.',
  'Tables 16 and 17 of this paper; physical/data/results/P3_LEAD_TIME.md', 'VI.7'), 1.6));
  add(figureSpace('g_lead', 'GRAPH', 'Lead time of every detected fault on the bench.',
    'One mark per detected session; zero marks the moment of performance failure.',
    'Use the figure written by the analysis software.', 'physical/data/figures/lead_time.png',
    'V.2', { height: 2.6 }));
  add(figureSpace('g_sev', 'GRAPH', 'Detection against severity on the bench.',
    'Detection rate with 95% intervals at severities 0.25, 0.5 and 1.0, by fault type.',
    'Use the figure written by the analysis software.',
    'physical/data/figures/severity_response.png', 'V.2', { height: 2.6 }));
  add(H3('6.2.5 Experiment P-5: faults that nobody designed'));
  add(table('b_undesigned', 'Undesigned faults, with the sealed faults of P-3 for comparison.',
    [2460, 900, 900, 1700, 1700, 1700],
    ['Intervention', 'Sessions', 'Detected', 'Median detection delay (s)', 'Median lead time (s)',
      'Onset source'], [
      ['Connector loosened and re-seated', null, null, null, null, 'clock, by hand'],
      ['Filter slid in front of the lens', null, null, null, null, 'clock, by hand'],
      ['Fingerprint on the lens edge', null, null, null, null, 'clock, by hand'],
      ['Stage rotated by the stepper', null, null, null, null, 'clock, by hand'],
      ['Warm air, 60 s', null, null, null, null, 'clock, by hand'],
      ['All undesigned (P-5)', null, null, null, null, 'clock, by hand'],
      ['All sealed (P-3), for comparison', null, null, null, null, 'sealed file'],
    ], { after: red('Fill the pink cells. Do not pool these sessions with P-3. With ten '
      + 'sessions, describe a small difference as not measured, not as no difference.',
    'physical/data/results/undesigned_faults.json', 'IV.6') }));
  add(H3('6.2.6 Experiment P-4: correlation against usability'));
  add(table('b_corr', 'The correlation the field reports, beside the two quantities that decide '
    + 'usability.', [4360, 2500, 2500], ['Quantity', 'Value', 'p value or interval'], [
    ['Spearman correlation, raw', null, null],
    ['Correlation with the time trend removed (partial)', null, null],
    ['Correlation on first differences', null, null],
    ['Strong: any magnitude 0.70 or more (yes or no; which)', null, 'not applicable'],
    ['Median lead time (s)', null, null],
    ['False-alarm rate (per hour) and its upper bound', null, null],
    ['Unusable: lead time not positive, or upper bound over budget (yes or no)', null,
      'not applicable'],
    ['Verdict by the preregistered rule', null, 'not applicable'],
  ], { after: red('Fill the pink cells. Copy the verdict from the report; do not derive a '
    + 'different one.', 'physical/data/results/correlation_vs_usability.json', 'IV.7') }));
  add(figureSpace('g_corr', 'GRAPH', 'Correlation against usability on the bench.',
    'The three correlations beside the lead time and the false-alarm rate measured on the '
    + 'same recordings.', 'Use the figure written by the analysis software.',
    'physical/data/figures/correlation_vs_usability.png', 'V.2', { height: 2.6 }));
  add(H3('6.2.7 Experiment P-6: decision rate'));
  add(table('b_rate', 'Detection at each decision rate, at equal false-alarm cost.',
    [1500, 1500, 1660, 1300, 1900, 1500],
    ['Windows per decision', 'Decisions per hour', 'Allowed false-positive rate per decision',
      'Threshold', 'Detection rate (95% interval)', 'False alarms per hour'],
    [1, 2, 3, 4, 5, 6].map(() => [null, null, null, null, null, null]),
    { after: red('Enter one row for each decision rate in the report, add rows if needed, and '
      + 'state the change from the fastest to the slowest rate and whether the intervals are '
      + 'separated.', 'physical/data/results/decision_rate.json, blocks curve, '
      + 'change_slowest_minus_fastest and intervals_separated', 'IV.8') }));
  add(figureSpace('g_rate', 'GRAPH', 'Detection against decision rate on the bench.',
    'Detection rate with 95% intervals from one decision per window to one per session.',
    'Use the figure written by the analysis software.',
    'physical/data/figures/decision_rate.png', 'V.2', { height: 2.6 }));
  add(H3('6.2.8 Experiment P-7: four apparatus configurations'));
  add(table('b_app', 'The main quantities in each apparatus configuration.',
    [2560, 900, 1100, 1700, 1700, 1400],
    ['Configuration', 'Sessions', 'Margin (°)', 'Median lead time, s (95% interval)',
      'False alarms per hour (upper bound)', 'Sign of the decision-rate change'], [
      ['A: baseline', null, null, null, null, null],
      ['B: exposure doubled, depth halved', null, null, null, null, null],
      ['C: patch size 24 pixels', null, null, null, null, null],
      ['D: 12 by 8 grid, 96 channels', null, null, null, null, null],
    ], { after: red('Fill the pink cells. Report the spread across the four configurations. Do '
      + 'not average them.', 'physical/data/results/apparatus_variation.json', 'IV.9') }));
  add(figureSpace('g_app', 'GRAPH', 'Median lead time in the four configurations.',
    'One point with its 95% interval for each of configurations A to D.',
    'Make this graph in a spreadsheet from Table 21, following the template in the manual.',
    'Table 21 of this paper; physical/data/results/apparatus_variation.json', 'V.3',
    { height: 2.6 }));

  // -------------------------------------------------------------------------
  sec(7, 'Analysis');
  // -------------------------------------------------------------------------
  add(H2('7.1 Computational validation'));
  add(P('Three separate measurements explain why the monitor could not meet the budget, and '
    + 'each points to a different cause.'));
  add(P('**The score drifts when nothing is wrong.** The silence gate failed on both arrays. A '
    + 'score that rises steadily during healthy recording will cross any fixed threshold '
    + 'eventually, which produces false alarms at a rate set by the length of the recording, '
    + 'not by any fault. Removing a straight line from the score made the gate pass (G5), so '
    + 'the drift is close to linear within an episode. That observation was made with the '
    + 'whole episode in hand. A monitor in use would have to remove the trend from past '
    + 'windows only, which is a harder problem and was not tested.'));
  add(P('**The decision rate sets a requirement the detector does not reach.** At 720 decisions '
    + `per hour the budget allows a false-positive rate of about `
    + `${(S.fpr_per_decision_720 * 100).toFixed(3)}% per decision. Deciding once per episode `
    + `relaxes this, yet the discrimination then required (AUC about `
    + `${n(S.auc_needed_at_budget.T11, 2)}) remains far above what was achieved `
    + `(${n(S.auc_session.T11, 2)} and ${n(S.auc_session.T5, 2)}). Measured directly, deciding `
    + 'less often did not reliably help: the change was not established on T11 and was a '
    + 'decrease on T5. Whether deciding less often helps a monitor of this kind is therefore '
    + 'not settled by the archived recordings.'));
  add(P('**What the monitor detects depends on the fault.** Decoder-guard exceeded the '
    + 'mean-activity detector on faults that leave total activity unchanged and fell below it '
    + 'on plain signal loss. A single pooled detection rate hides this. It also shows that the '
    + 'comparison gate (G3) can be passed by a monitor that is still unusable: beating a '
    + 'simple alternative is not the same as being early enough.'));
  add(P('**Windows are not independent.** With a lag-1 autocorrelation above 0.98, an episode '
    + 'of several dozen windows carries less information than one independent observation. '
    + 'Any analysis that treated windows as independent would overstate its certainty by a '
    + 'large factor. The episode is therefore the unit of analysis throughout.'));

  add(H2('7.2 Physical validation: the ten preregistered predictions'));
  add(P(`${T('predictions')} lists the predictions exactly as frozen on 24 September 2026, with `
    + 'the condition that would falsify each. The outcome column is completed from the '
    + 'results tables and from nothing else. Prediction PP-7 was made against the evidence '
    + 'then available, which is recorded in the preregistration.'));
  const pp = [
    ['PP-1', 'The false-alarm rate is above 0.1 per hour', 'the 95% upper bound is at or below '
      + '0.1; zero events in about 4 hours counts as untested', 'b_fa'],
    ['PP-2', 'The silence gate fails: more than 10% of fault-free sessions trend',
      '10% or fewer trend, raw', 'b_fa'],
    ['PP-3', 'The median lead time is zero or negative',
      'the median is positive and its interval excludes zero', 'b_lead_type'],
    ['PP-4', 'At least one of the three correlations is 0.70 or more in magnitude',
      'none reaches 0.70', 'b_corr'],
    ['PP-5', 'The raw correlation is larger than the partial correlation',
      'the partial is as large or larger', 'b_corr'],
    ['PP-6', 'Detection at severity 1.0 exceeds detection at 0.25 (manipulation check)',
      'it does not', 'b_lead_sev'],
    ['PP-7', 'One decision per session detects at least 10 points more than 720 per hour',
      'the gain is under 10 points or negative', 'b_rate'],
    ['PP-8', 'Undesigned and sealed faults are compared; 20 points is a meaningful difference; '
      + 'no direction predicted', 'not applicable: a measurement, not a directional prediction',
    'b_undesigned'],
    ['PP-9', 'The sign of the decision-rate change is the same in all four configurations',
      'any configuration differs in sign', 'b_app'],
    ['PP-10', 'Across configurations the median lead time differs by more than 10 s or the '
      + 'false-alarm rate by more than a factor of 2',
    'the configurations agree within those limits', 'b_app'],
  ];
  add(table('predictions', 'The ten preregistered predictions and their outcomes.',
    [700, 3260, 2500, 1500, 1400],
    ['Code', 'Prediction', 'Falsified if', 'Outcome', 'Evidence'],
    pp.map(([c, a, b, t]) => [c, a, b, null, T(t)]),
    { after: red('For each prediction enter one of: held, falsified, untested. Use the '
      + 'falsifying condition in the third column and the table named in the fifth.',
    'Tables 15 to 21 of this paper', 'IV.10') }));

  add(H2('7.3 Comparison of the two validations'));
  add(P('The two validations measure the same quantities with the same monitor, window and '
    + `budget, so they can be set side by side (${T('compare')}). The comparison is between `
    + 'directions and orders of magnitude. The bench is not a model of an implanted array, and '
    + 'a rate measured on it is not an estimate of the rate in a person.'));
  add(table('compare', 'The archived recordings and the bench, side by side.',
    [3060, 1500, 1500, 1600, 1700],
    ['Quantity', 'T11, archived', 'T5, archived', 'Bench', 'Same direction (yes or no)'], [
      ['Median lead time (s)', n(S.median_lead_s.T11), n(S.median_lead_s.T5), null, null],
      ['False alarms per hour', n(S.false_alarms_per_hour.T11, 2),
        n(S.false_alarms_per_hour.T5, 2), null, null],
      ['Detection rate', pct(det11 / deg11), pct(det5 / deg5), null, null],
      ['Silence gate, raw', 'fail', 'fail', null, null],
      ['Silence gate, detrended', 'pass', 'pass', null, null],
      ['Decision-rate change (points)', n(100 * PAIR.T11.own_range.change, 1),
        n(100 * PAIR.T5.own_range.change, 1), null, null],
      ['Decoding margin (°)', n(margin11, 1),
        n(S.decoder_chance_deg.T5 - S.decoder_error_deg.T5, 1), null, 'not applicable'],
    ], { after: red('Fill the bench column from Tables 15, 16, 20 and 21, and mark for each row '
      + 'whether the bench result has the same direction as the archived result.',
    'Tables 15, 16, 20 and 21 of this paper', 'IV.11') }));
  add(figureSpace('g_cmp', 'GRAPH', 'Median lead time on the archived recordings and on the bench.',
    'Three points with 95% intervals where available: T11, T5 and the bench.',
    'Make this graph in a spreadsheet from Table 23, following the template in the manual.',
    'Table 23 of this paper', 'V.3', { height: 2.4 }));
  add(H2('7.4 Verdict on Hypothesis B'));
  add(...writeSpace(red('State the verdict given by the judging rule of Section 3.3 in one '
    + 'paragraph: whether the correlation was strong and by which of the three measures, '
    + 'whether the monitor was unusable and on which count, and the resulting verdict '
    + '(supported, falsified or inconclusive). Then state which of the ten predictions held.',
  'Tables 19 and 22 of this paper; physical/data/results/P4_CORRELATION_VS_USABILITY.md',
  'VI.8'), 1.8));

  // -------------------------------------------------------------------------
  sec(8, 'Discussion');
  // -------------------------------------------------------------------------
  add(H2('8.1 What the computational validation shows'));
  add(P('Hypothesis A was rejected on both of its conditions. On real recordings, with faults '
    + 'whose onset was fixed before any detector existed, the warning usually arrived at or '
    + `after the performance drop (${pct(LT.T11.fraction_negative + LT.T11.fraction_zero)} of `
    + 'detections on T11), and the false-alarm requirement could be met only at thresholds '
    + 'where almost no fault was detected. At the threshold chosen in advance, false alarms '
    + 'came at 2 to 34 times the budget. No variation of the detector that was tried changed '
    + 'that conclusion. The '
    + 'result was not expected when the project began, and it changed the project: on '
    + '20 and 21 September 2026 the physical validation was redesigned to ask whether '
    + 'correlation with performance, the evidence usually offered for monitors of this class, '
    + 'is sufficient to support using them.'));
  add(P('The result has clear limits. The faults were equations applied to recorded features, '
    + 'not degradation that occurred in tissue or hardware. Two arrays from one dataset were '
    + 'used. T5 yielded only six detections, too few for an interval. The decoder was frozen, '
    + 'so the performance it reports includes staleness as well as the planted fault. The '
    + 'monitor tested is one member of a class, not the method of any published study, so the '
    + 'result does not show that a published monitor would behave the same way. What the '
    + 'result does establish is that the two quantities can be measured once the onset is '
    + 'controlled, and that for this monitor a correlation would have given no warning of how '
    + 'poor they are.'));
  add(H2('8.2 What the physical validation shows'));
  add(...writeSpace(red('Interpret the false-alarm and silence-gate results. If the silence '
    + 'gate failed on an apparatus with no biology in it, discuss what that implies about the '
    + 'monitoring approach. If it passed, discuss what that implies about the archived '
    + 'recordings. Keep the measured values in Section 6 and the meaning here.',
  'Table 15 and Section 6.2.3 of this paper', 'VI.9'), 1.6));
  add(...writeSpace(red('Interpret the lead-time result and the differences between fault '
    + 'types and between sealed and undesigned faults. State what a designer of a monitor '
    + 'could take from the differences.', 'Tables 16, 17 and 18 of this paper', 'VI.9'), 1.6));
  add(...writeSpace(red('Interpret the verdict on hypothesis B. Explain what it means for '
    + 'validating a monitor by correlation alone, and state plainly what the bench cannot '
    + 'show about implanted arrays.', 'Section 7.4 of this paper', 'VI.9'), 1.6));
  add(H2('8.3 The two validations together'));
  add(...writeSpace(red('Compare the bench with the archived recordings, row by row of '
    + 'Table 23. Where they agree, say what the agreement supports. Where they differ, give '
    + 'the possible reasons without choosing one that the data do not support.',
  'Table 23 of this paper', 'VI.9'), 1.6));
  add(H2('8.4 Relation to published work'));
  add(P('Pun et al. (2024a) report that a score of signal change correlates with performance '
    + 'and propose it for deciding when to recalibrate. This project does not dispute that '
    + 'correlation. It measures different quantities on the same public recordings and finds '
    + 'that, for the monitor built here, they are far from what use would require. Karpowicz '
    + 'et al. (2025) and Wilson et al. (2025) correct drift without first detecting it, which '
    + 'avoids the problem studied here; a reliable warning would still be useful for deciding '
    + 'when correction has stopped working. '
    + red('Add one or two sentences relating the bench results to these studies.',
      'Sections 6.2 and 7.4 of this paper', 'VI.9')));

  // -------------------------------------------------------------------------
  sec(9, 'Future Work');
  // -------------------------------------------------------------------------
  add(P('The immediate next step is the physical validation itself, in the order fixed by the '
    + 'project schedule: obtain the four critical parts, prepare the computer, build and seal '
    + 'the enclosure, pass the five acceptance gates, calibrate, and record the experiments in '
    + 'the order P-1, P-2, P-3, P-5, P-7.'));
  add(P('Beyond the frozen plan, four extensions follow from what the computational validation '
    + 'found.'));
  add(bullets([
    '**Enough fault-free recording to test the budget.** The frozen 101 fault-free sessions '
    + 'leave about four held-out hours, which can bound the false-alarm rate at about 0.75 '
    + 'per hour and no lower. Demonstrating 0.1 per hour would need about 30 held-out hours, '
    + 'roughly 480 sessions. Any extension must be written as a dated amendment before the '
    + 'data are analysed.',
    '**Removing the drift causally.** The silence gate passed only when a straight line was '
    + 'removed with the whole episode in hand. A monitor that subtracts its own trend using '
    + 'past windows only has not been tested.',
    '**Deciding on the timescale of the failure.** The decision-rate result was not settled '
    + 'by the archived recordings. A monitor designed from the start to decide once per '
    + 'session is a different design from one that pools the decisions of a fast monitor.',
    '**More undesigned faults.** Ten sessions can show only a large difference between '
    + 'designed and undesigned faults. A larger set would test whether fault benchmarks built '
    + 'from equations, including this one, are representative.',
  ]));
  add(P('Work on people is outside the scope of this project and will remain so. '
    + red('Add the questions that the bench results raised and that the present design '
      + 'cannot answer, each with the measurement that would answer it.',
    'Sections 7 and 8 of this paper; bench logbook', 'VI.10')));

  // -------------------------------------------------------------------------
  sec(10, 'Sources of Error');
  // -------------------------------------------------------------------------
  add(P(`${T('errors')} lists the sources of error and uncertainty that are known in advance, `
    + 'how each is controlled or bounded, and, for the bench, a column for its observed size. '
    + 'Errors made during the project and then corrected are recorded in '
    + '`research/research_log.md`; one example is an early report that gave the AUC required '
    + 'at one decision per session as 0.933, the figure for a 10% false-flag rate, which was '
    + 'corrected to 0.990 on 20 September 2026.'));
  add(table('errors', 'Sources of error and uncertainty.', [2260, 1500, 3400, 2200],
    ['Source', 'Affects', 'How it is controlled or bounded', 'Observed size'], [
      ['Faults are designed equations', 'All computational results',
        'Four types, three severities, three ramp rates; onsets sealed; experiment P-5 tests '
        + 'undesigned faults on the bench', 'not measurable on archived data'],
      ['Windows overlap and are correlated', 'Every interval',
        'Episode or session is the unit; bootstrap resamples whole episodes',
        `lag-1 r = ${n(S.lag1_pooled.T11, 3)} and ${n(S.lag1_pooled.T5, 3)}`],
      ['Little fault-free archived recording', 'False-alarm rate, silence gate',
        'Reported as measured; the bench exists to supply fault-free hours',
        `${S.fault_free_episodes.T11} and ${S.fault_free_episodes.T5} fault-free test episodes`],
      ['Few detections on T5', 'Lead time on T5', 'No interval is reported',
        `${det5} detections`],
      ['Threshold chosen on one group, applied to another', 'False-alarm rate',
        'Three disjoint groups; test data read once',
        'validation target 0.1 per hour; test result 0.23 to 3.41'],
      ['Frozen decoder ages', 'Performance, lead time',
        'Bench analysis is run twice, frozen and refitted per session', null],
      ['Light leaking into the enclosure', 'Every bench channel', 'Gate G-a; sealed seams',
        null],
      ['Late or dropped frames; dead or clipped channels', 'Bench signal quality', 'Gate G-b',
        null],
      ['Delay between display and camera', 'Alignment of stimulus and recording',
        'Gate G-c; one measured delay used throughout', null],
      ['Temperature of the room and components', 'Camera noise and gain',
        'Logged by the sensor in every session; no adjustment during a campaign', null],
      ['Timing of faults applied by hand', 'Lead time in P-3 (filter, tape)',
        'Countdown on screen; late application written in the log; error is smaller than one '
        + 'window if under 30 s', null],
      ['Onset noted from a clock', 'Experiment P-5', 'Analysed in a separate table, never '
        + 'pooled with P-3', null],
      ['One apparatus in one room', 'Generality of every bench result',
        'Experiment P-7 varies three settings; spread reported, not an average', null],
      ['Five-minute sessions', 'Slow effects', 'Stated as a limit; not controlled',
        'not measurable in this design'],
    ], { after: red('Fill each pink cell with the observed size of the error on the bench '
      + '(for example the measured dark level, the share of late frames, the temperature '
      + 'range, the number of late hand-applied faults), or write "not observed".',
    'Table 13 of this paper; physical/data/raw/SESSION_LOG.csv; bench logbook, sheets C to E',
    'VI.11') }));
  add(P('**Departures from the preregistered plan.** Every departure is listed, including those '
    + 'that seem unimportant, with the date and whether the data had been seen.'));
  add(table('deviations', 'Departures from the preregistered plan.',
    [1200, 2300, 2300, 1860, 1700],
    ['Date', 'What was planned', 'What was done', 'Reason', 'Possible effect on the results'],
    [1, 2, 3, 4].map(() => [null, null, null, null, null]),
    { after: red('Enter every departure from the plan, one per row, or write "none" in the '
      + 'first row if there were none. Add rows if needed.',
    'bench logbook, sheet E (deviations); physical/data/EXCLUSIONS.csv', 'III.6') }));
  add(...writeSpace(red('In one paragraph, state which sources of error could change a '
    + 'conclusion of this paper and which could not, giving the reason for each.',
  'Tables 24 and 25 of this paper', 'VI.11'), 1.4));

  // -------------------------------------------------------------------------
  sec(11, 'Conclusion');
  // -------------------------------------------------------------------------
  add(P('A monitor that reads only the input of a neural decoder was built and tested against '
    + `${N_EP.toLocaleString()} faults planted in public recordings from two implanted arrays, `
    + 'with every onset sealed before any detector existed. The monitor did not provide '
    + `usable warning. Its median warning came ${n(-S.median_lead_s.T11)} s and `
    + `${n(-S.median_lead_s.T5)} s after decoding had failed, its false-alarm rate was `
    + `${n(S.false_alarms_per_hour.T11, 2)} and ${n(S.false_alarms_per_hour.T5, 2)} per hour `
    + `against a budget of ${S.budget_per_hour}, and none of ${S.funnel.run} configurations `
    + 'passed all five gates set in advance. The hypothesis that it would warn early enough '
    + 'and rarely enough was rejected. The project also shows that lead time and false-alarm '
    + 'rate, which had not been found in the published evidence for monitors of this class, '
    + 'become measurable once the onset of the fault is controlled.'));
  add(...writeSpace(red('State the conclusion of the physical validation in one paragraph: '
    + 'the false-alarm rate and its bound, the median lead time, and the verdict on '
    + 'hypothesis B by the preregistered rule. State only what Sections 6 and 7 support.',
  'Sections 6.2 and 7.4 of this paper', 'VI.12'), 1.5));
  add(...writeSpace(red('State in two or three sentences what the two validations together '
    + 'show about validating a decoder-health monitor by correlation, and the main limit on '
    + 'that statement.', 'Sections 7.3 and 8.3 of this paper', 'VI.12'), 1.2));

  // -------------------------------------------------------------------------
  sec(12, 'References');
  // -------------------------------------------------------------------------
  add(P('Entries are listed as they stand in the project records. Entries marked with a dagger '
    + '(†) are carried from the bibliography of the submitted research plan, which gives '
    + 'first authors only. '
    + red('Complete the author list, title and page numbers of every entry marked with a '
      + 'dagger by opening the publisher\'s page for its doi, and put every entry in one '
      + 'citation style.', 'research/RESEARCH_PLAN_2026-09-15.md, bibliography; the '
      + 'publisher\'s page for each doi', 'VI.13')));
  const refs = [
    '† Armour, B. S., et al. (2016). Prevalence and causes of paralysis: United States, '
    + '2013. ~American Journal of Public Health, 106~(10), 1855–1857. '
    + 'doi:10.2105/AJPH.2016.303270',
    '† Barrese, J. C., et al. (2013). ~Journal of Neural Engineering, 10~(6), 066014.',
    '† Hughes, C. L., et al. (2021). ~Journal of Neural Engineering, 18~(4). '
    + 'doi:10.1088/1741-2552/ac1add',
    '† Karpowicz, B. M., et al. (2025). ~Nature Communications, 16~. '
    + 'doi:10.1038/s41467-025-59652-y',
    'Perge, J. A., Homer, M. L., Malik, W. Q., Cash, S., Eskandar, E., Friehs, G., Donoghue, '
    + 'J. P., & Hochberg, L. R. (2013). ~Journal of Neural Engineering, 10~(3), 036004. '
    + 'doi:10.1088/1741-2560/10/3/036004',
    '† Pun, T. K., et al. (2024a). ~Communications Biology, 7~. '
    + 'doi:10.1038/s42003-024-06784-4',
    '† Pun, T. K., et al. (2024b). [Data set]. Dryad. doi:10.5061/dryad.n2z34tn5s',
    '† Sendelbach, S., & Funk, M. (2013). ~AACN Advanced Critical Care, 24~.',
    '† Sponheim, C., et al. (2021). ~Journal of Neural Engineering, 18~(6), 066044.',
    '† Wilson, G. H., et al. (2025). ~Nature Biomedical Engineering~. '
    + 'doi:10.1038/s41551-025-01536-z',
  ];
  for (const r of refs) add(P(r, { indent: { left: 480, hanging: 480 }, after: 110, line: 270 }));
  add(P('Two notes on these entries. The figure of 72 to 99% false alarms attributed to '
    + 'Sendelbach and Funk (2013) was found as reported in a federal patient-safety report; the '
    + 'article itself has not been opened. '
    + red('Open the article by Sendelbach and Funk and confirm the figure, or cite the report '
      + 'in which it was found.', 'poster/README.md, references table', 'VI.13')
    + ' The repository of this project is cited as: Nair, G. (2026). ~bci-ews-research~ '
    + `[Computer software and data]. GitHub. Branch \`${meta.branch}\`, commit `
    + `\`${meta.commit}\`. `
    + red('Replace the commit with the commit of the final version, and add the date of '
      + 'access.', 'git log on the final branch', 'VI.13')));

  // -------------------------------------------------------------------------
  sec(13, 'Acknowledgments');
  // -------------------------------------------------------------------------
  add(P('The recordings analysed in this project exist because two people, the research '
    + 'participants designated T11 and T5, took part in the BrainGate clinical trial, and '
    + 'because Pun and colleagues released the data to the public domain.'));
  add(...writeSpace(red('Write the acknowledgments in your own words: the adult sponsor and '
    + 'what they did, anyone who supplied equipment, space or advice, and anyone who was '
    + 'present for the attended sessions.', 'your own record; bench logbook', 'VI.14'), 1.3));
  add(H2('Statement on the use of artificial intelligence'));
  add(P('By a decision recorded in the research log on 8 September 2026, this statement is '
    + 'written by the researcher and not by an AI system.'));
  add(...writeSpace(red('Write the disclosure of how AI tools were used in this project: '
    + 'which tools, for which tasks (code, analysis, documents, figures, this paper), what '
    + 'you checked yourself and how, and which decisions were yours alone.',
  'research/AI_INVOLVEMENT_RECORD.md; research/research_log.md', 'VI.14'), 2.0));

  return out;
}

module.exports = { build };
