// doc2b.js -- Document 2, Parts IV to VII: calculations, graphs, writing, final checks.
const L = require('./lib');
const { P, H3, bullets, numbered, note, code, formula, mtable, mfigure, drawn, F, T, grid,
  spacer, picture, caption, D } = L;

const WARN = { bar: 'B24E0A', fill: 'FDF3E9' };
const ILLU = { bar: '6B6B6B', fill: 'F2F2F2' };

module.exports = function partsFourToSeven(t, meta) {
  const { add, part, sec } = t;
  const reds = Object.values(L.state.reds);

  // =========================================================================
  part('IV', 'Data Processing and Quantitative Analysis');
  // =========================================================================
  sec('IV.1', 'How the numbers are produced');
  add(P('Every number in Section 6.2 of the paper is computed by a program in '
    + '`physical/code/`, not by hand. The programs were written and tested before any data '
    + 'existed, so that the method could not be adjusted to the result. This part explains '
    + 'each calculation: its formula, its inputs, what it is for and how to read it. The '
    + 'purpose is that the researcher can explain every number to a judge and can check any '
    + 'one of them independently in a spreadsheet (Section IV.12). The spreadsheet is a '
    + 'check. The program remains the source of the reported value.'));
  add(P('The six commands are run in this order, on a laptop, after the raw sessions have been '
    + 'copied from the bench computer.'));
  add(code(['cd ~/bci-ews-research',
    'python3 physical/code/dryrun.py --cleanup            # remove any rehearsal output first',
    'python3 physical/code/make_session_table.py',
    'python3 physical/code/analyze_falsealarm.py',
    'python3 physical/code/analyze_leadtime.py',
    'python3 physical/code/analyze_leadtime.py --undesigned',
    'python3 physical/code/analyze_correlation.py',
    'python3 physical/code/analyze_decision_rate.py',
    'python3 physical/code/analyze_apparatus.py --configs A,B,C,D',
    'python3 physical/code/figures.py all']));
  add(mfigure(drawn('d_dataflow'), 'Data flow of the physical validation.',
    `The same drawing as ${F('dataflow')} of the paper. Each analysis program reads `
    + '`sessions.csv` and writes one report and one data file.'));
  add(mfigure(drawn('d_stats'), 'The statistical treatment of each measured quantity.',
    `The same drawing as ${F('stats')} of the paper. Sections IV.3 to IV.8 take the rows one `
    + 'at a time.'));

  sec('IV.2', 'The session table');
  add(P('`make_session_table.py` reads every session folder, applies the measured delay from '
    + '`lag.json`, decodes the direction in each 30-second window (1,500 frames, a new window '
    + 'every 250 frames), computes the monitor\'s risk score for each window, and assigns '
    + 'every session to one of three groups that share no session. The ~fit~ group builds the '
    + 'decoder and the monitor. The ~val~ group is used only to choose the warning threshold, '
    + 'as the lowest threshold that keeps false alarms within 0.1 per hour. The ~test~ group '
    + 'is the only one on which results are reported. It writes one row per session to '
    + '`physical/data/sessions.csv`.'));
  add(mtable('Columns of `sessions.csv`.', [2300, 1500, 5560],
    ['Column', 'Unit', 'Meaning'], [
      ['session, block, folder', 'none', 'Which recording the row describes'],
      ['group', 'fit, val, test', 'The group the session was assigned to'],
      ['kind', 'text', 'Calibration, fault-free, degraded or undesigned'],
      ['config', 'A to D', 'Apparatus configuration'],
      ['healthy', 'true or false', 'True if no fault was imposed'],
      ['fault_type, severity', 'text; fraction', 'As drawn in the sealed plan'],
      ['onset_seconds', 's', 'When the fault began'],
      ['onset_provenance', 'text', 'Sealed file, or noted by hand (P-5)'],
      ['duration_seconds, n_windows', 's; count', 'Length of the session'],
      ['risk_score', 'none', 'Median of the monitor\'s risk score over the session'],
      ['performance', 'degrees', 'Median decoding error over the session'],
      ['chance_deg, margin_deg', 'degrees', 'Measured chance level; chance minus error'],
      ['fail_seconds', 's', 'End of the first window in which decoding had failed; blank if '
        + 'it never failed'],
      ['warn_seconds', 's', 'End of the first window in which the monitor warned'],
      ['warned', 'true or false', 'Whether it warned at all'],
      ['warn_before_onset', 'true or false', 'True if the warning window ended before the '
        + 'onset: a false alarm, not a detection'],
      ['lead_seconds', 's', 'fail_seconds minus warn_seconds, for valid warnings only'],
      ['detect_seconds', 's', 'warn_seconds minus onset_seconds, for valid warnings only'],
    ]));
  add(P('**Read the printout before anything else.** It reports four things: the sizes of the '
    + 'groups (a small test group of fault-free sessions weakens every false-alarm figure and '
    + 'only more recording can change that), the margin beside the target of 36.1° (a '
    + 'margin far from the calibration value means the apparatus changed during the '
    + 'campaign), the fault-free hours held out against the hours the budget needs, and the '
    + 'name of any recording that would not load.'));
  add(P('**Run it twice.** The second run refits the decoder in every session. A result that '
    + 'appears with the frozen decoder and disappears with the refitted one is a result about '
    + 'the decoder growing stale, and the paper must call it that.'));
  add(code(['python3 physical/code/make_session_table.py --decoder frozen',
    'python3 physical/code/make_session_table.py --decoder per-session --tag _persession']));
  add(P(`**Filling ${T('b_sessions')} of the paper.** Planned counts are already entered. `
    + '~Recorded~ is the number of session folders for the experiment. ~Excluded~ is the '
    + 'number of its lines in `EXCLUSIONS.csv`. ~Analysed~ is the number of its rows in '
    + '`sessions.csv`, and should equal recorded minus excluded. The dates come from sheet C '
    + 'of the logbook.'));

  sec('IV.3', 'False-alarm rate (experiment P-2)');
  add(P('**Purpose.** To measure how often the monitor warns when nothing is wrong. '
    + '**Inputs.** The fault-free sessions of the test group: the number of warnings k and '
    + 'the hours of recording H. **Calculation.**'));
  add(formula('rate = k / H', 'k = false alarms; H = held-out fault-free hours; the rate is '
    + 'in false alarms per hour'));
  add(P('A count of rare events follows a Poisson distribution, and the program reports the '
    + 'exact 95% interval for the rate:'));
  add(formula('lower = χ²(0.025; 2k) / (2H)'));
  add(formula('upper = χ²(0.975; 2k + 2) / (2H)',
    'χ²(p; d) is the value below which a chi-squared variable with d degrees of '
    + 'freedom falls with probability p'));
  add(P('If k is zero there is no rate to report, only an upper bound, by the rule of three:'));
  add(formula('upper bound ≈ 3 / H', 'so demonstrating a budget b needs about 3 / b '
    + 'hours with no false alarm: 30 hours for b = 0.1 per hour'));
  add(P('**Decision fixed in advance.** The monitor is within budget only if the ~upper~ end '
    + 'of the interval is at or below 0.1 per hour. The frozen plan leaves about four held-out '
    + 'hours, so even with no false alarm the bound is about 0.75 per hour. In that case the '
    + 'preregistered sentence is that the rate is bounded at 0.75 per hour and the campaign '
    + 'cannot distinguish a quiet monitor from a noisy one. It is not that the monitor met '
    + 'the budget.'));
  add(note('**Illustration with invented numbers, not a result.** If k were 2 and H were 4.0 '
    + 'hours, the rate would be 2 / 4.0 = 0.50 per hour, with a 95% interval from 0.06 to '
    + '1.81 per hour. The upper end is above 0.1, so the monitor would be over budget. In a '
    + 'spreadsheet, with k in cell B1 and H in B2: `=B1/B2`, `=CHISQ.INV(0.025,2*B1)/2/B2` '
    + 'and `=CHISQ.INV(0.975,2*(B1+1))/2/B2`.', ILLU));
  add(mtable(`Where each row of ${T('b_fa')} of the paper comes from.`, [4360, 5000],
    ['Row of the table', 'Field of `physical/data/results/false_alarm.json`'], [
      ['Held-out fault-free sessions', '`healthy_test_sessions`'],
      ['Held-out fault-free recording (hours)', '`healthy_test_hours`'],
      ['False alarms, k', '`false_alarms`'],
      ['False-alarm rate', '`false_alarms_per_hour`'],
      ['95% interval of the rate', '`rate_ci95`'],
      ['Upper bound if k = 0', '`zero_event_upper_bound_per_hour`'],
      ['Hours needed to demonstrate the budget', '`hours_needed_for_budget`'],
      ['Within the budget', '`within_budget`'],
      ['Silence gate rows', '`G1_silence`: `fraction_significant`, `median_tau`, `pass`'],
      ['After detrending', '`G5_detrend`'],
    ], { after: 'The second column of the table in the paper uses the same fields from the '
      + 'run made with `--tag _persession`.' }));

  sec('IV.4', 'The silence gate');
  add(P('**Purpose.** To test whether the risk score drifts upward during healthy operation. '
    + 'A drifting score crosses any threshold eventually. **Inputs.** For each fault-free '
    + 'test session, the risk score of every window in order. **Calculation.** Kendall\'s tau '
    + 'between the score and the window number:'));
  add(formula('τ = (C − D) / (n (n − 1) / 2)',
    'over all pairs of windows: C = pairs in which the later window has the higher score; '
    + 'D = pairs in which it has the lower; n = number of windows'));
  add(P('Tau is +1 if the score only rises, −1 if it only falls and near 0 if it has no '
    + 'trend. The program obtains a p value for each session and counts the sessions with '
    + 'p below 0.05. **Decision fixed in advance.** The gate passes if 10% or fewer of the '
    + 'sessions show a significant trend. The calculation is repeated after a straight line '
    + 'has been fitted to each session and subtracted (the detrended gate).'));
  add(mtable('How to read the silence gate.', [2600, 6760], ['Outcome', 'What it supports'], [
    ['Gate passes', 'On an apparatus with no biology in it, the monitor stays flat. The '
      + 'failure seen on archived recordings would then be a property of those recordings.'],
    ['Gate fails', 'The drift appears with no brain and no electrodes. That points at the '
      + 'monitoring approach itself.'],
    ['Fails raw, passes detrended', 'The drift is close to linear. A monitor in use would '
      + 'have to remove it from past windows only, which was not tested.'],
  ]));

  sec('IV.5', 'Lead time and detection (experiment P-3)');
  add(P('**Purpose.** To measure whether the warning comes before decoding fails, and how '
    + 'often a fault is caught at all. **Inputs.** For each degraded test session: the sealed '
    + 'onset, the time decoding failed, and the time of the first warning. All times are '
    + 'taken at the end of the window concerned. **Calculations.**'));
  add(formula('lead time = t(failure) − t(warning)'));
  add(formula('detection delay = t(warning) − t(onset)',
    'both in seconds; a positive lead time means the warning came first'));
  add(formula('detection rate = sessions with a valid warning / degraded sessions'));
  add(P('Two categories are not detections and are counted separately. A warning whose window '
    + 'ended before the onset contains no faulty data: it is a false alarm that happened to '
    + 'fall in a degraded session. A fault that never made decoding fail has no failure to '
    + 'lead, so its lead time is undefined.'));
  add(P('**The median and its interval.** The program reports the median lead time and the '
    + 'median detection delay. The interval is a bootstrap: from the n sessions it draws n '
    + 'sessions at random with replacement, takes their median, repeats this 5,000 times, '
    + 'and reports the range that holds the middle 95% of those medians. With fewer than '
    + 'three sessions no interval is given.'));
  add(P('**An interval for the detection rate.** The report gives the count and the '
    + 'proportion. The tables of the paper also ask for a 95% interval, computed with the '
    + 'Wilson formula, the one `analyze_decision_rate.py` already uses for the same kind of '
    + 'proportion. With x detections in n sessions, p = x / n and z = 1.96:'));
  add(formula('centre = (p + z² / 2n) / (1 + z² / n)',
    'half-width = z √( p (1 − p) / n + z² / 4n² ) / (1 + z² / n); '
    + 'the interval is centre ± half-width'));
  add(note('**Illustration with invented numbers, not a result.** With x = 30 and n = 100, '
    + 'p = 0.30 and the Wilson interval runs from 0.219 to 0.396. In a spreadsheet, with x in '
    + 'B1 and n in B2, put `=B1/B2` in B3 and `=1.96` in B4. Then the centre is '
    + '`=(B3+B4^2/(2*B2))/(1+B4^2/B2)` and the half-width is '
    + '`=B4*SQRT(B3*(1-B3)/B2+B4^2/(4*B2^2))/(1+B4^2/B2)`.', ILLU));
  add(mtable(`Where the columns of ${T('b_lead_type')} and ${T('b_lead_sev')} come from.`,
    [3300, 6060], ['Column', 'Field of `physical/data/results/lead_time.json`'], [
      ['Sessions', '`n_sessions`'],
      ['Detected', '`n_detected`'],
      ['Detection rate', '`detection_rate`; the interval by the Wilson formula above'],
      ['Warned before onset', '`n_warned_before_onset`'],
      ['Median detection delay and interval', '`median_detection_delay_s`, '
        + '`detection_delay_ci95`'],
      ['Median lead time and interval', '`median_lead_s`, `lead_ci95`'],
    ], { after: 'Rows by fault type are under `by_fault_type`, rows by severity under '
      + '`by_severity`, and the row for all types under `overall`. The fields '
      + '`n_with_performance_failure` and `fraction_warned_before_failure` are reported in '
      + 'the text beneath the tables.' }));
  add(P('**The pair rule.** A lead time is never reported without the false-alarm rate at the '
    + 'same threshold. A threshold can always be lowered until the monitor warns constantly, '
    + 'which lengthens the lead time and means nothing.'));

  sec('IV.6', 'Undesigned faults (experiment P-5)');
  add(P('The calculations are those of Section IV.5, run by `analyze_leadtime.py --undesigned` '
    + 'on the ten sessions of P-5. The difference is the origin of the onset: a clock time '
    + 'written by hand, not a sealed file. For that reason the sessions are reported in their '
    + `own table (${T('b_undesigned')}), from \`undesigned_faults.json\`, and are never pooled `
    + 'with P-3. Prediction PP-8 treats a difference of 20 percentage points in detection '
    + 'rate between undesigned and sealed faults as meaningful and predicts no direction. '
    + 'With ten sessions, a smaller difference is reported as not measured.'));

  sec('IV.7', 'Correlation against usability, and the verdict (experiment P-4)');
  add(P('**Purpose.** To compute the kind of evidence the field reports, a correlation between '
    + 'the monitor\'s score and performance, on the same recordings for which lead time and '
    + 'false-alarm rate are now known. **Inputs.** One pair per session, in time order: '
    + '`risk_score` and `performance`. **Calculations.** Three correlations, because both '
    + 'quantities drift with time and any two drifting quantities correlate.'));
  add(bullets([
    '**Raw.** Spearman\'s correlation: replace each value by its rank, then compute the '
    + 'ordinary correlation of the ranks.',
    '**Partial.** Rank both quantities; from each set of ranks subtract the straight-line '
    + 'trend against time order; correlate what remains. This removes what the two share '
    + 'only because both change with time.',
    '**First differences.** Replace each series by the change from one session to the next, '
    + 'then compute Spearman\'s correlation of the changes.',
  ]));
  add(formula('strong  ⇔  max( |raw|, |partial|, |differences| ) ≥ 0.70'));
  add(formula('unusable  ⇔  median lead time ≤ 0   or   upper bound of the false-alarm rate > 0.1 per hour'));
  add(mtable('The judging rule, fixed on 24 September 2026.', [2300, 2300, 4760],
    ['Correlation', 'Monitor', 'Verdict on Hypothesis B'], [
      ['strong', 'unusable', '**Supported.** A strong correlation did not indicate a usable '
        + 'monitor.'],
      ['strong', 'usable on both counts', '**Falsified.** Correlation was adequate evidence '
        + 'here.'],
      ['none reaches 0.70', 'either', '**Inconclusive.** A weakly correlated monitor says '
        + 'nothing about whether correlation is sufficient evidence.'],
    ]));
  add(mtable(`Where each row of ${T('b_corr')} of the paper comes from.`, [4360, 5000],
    ['Row', 'Field of `physical/data/results/correlation_vs_usability.json`'], [
      ['Raw, partial, first differences, with p values', '`correlations`: `raw_r`, `raw_p`, '
        + '`partial_r`, `partial_p`, `diff_r`, `diff_p`'],
      ['Strong, and by which measure', '`correlation_is_strong`, `strong_by`'],
      ['Median lead time; false-alarm rate and bound', '`usability`'],
      ['Unusable', '`lead_time_unusable`, `false_alarm_rate_over_budget`'],
      ['Verdict', '`hypothesis_supported`, read with the table above'],
    ], { after: 'The same file gives `time_vs_score_r` and `time_vs_perf_r`, the correlation '
      + 'of each quantity with time. They explain a gap between the raw and the partial '
      + 'value and belong in the text.' }));

  sec('IV.8', 'Decision rate (experiment P-6)');
  add(P('**Purpose.** To measure whether a monitor that decides less often detects more, at '
    + 'the same false-alarm cost. **Inputs.** The same sessions, re-scored with the windows '
    + 'pooled in groups of m. **Calculations.** With a new window every 5 seconds there are '
    + '720 windows an hour.'));
  add(formula('decisions per hour = 720 / m'));
  add(formula('allowed false-positive rate per decision = budget / decisions per hour',
    'm = windows per decision; budget = 0.1 false alarms per hour'));
  add(P('These two lines are arithmetic and can be checked now: at m = 1 the allowed rate is '
    + '0.1 / 720 = 0.000139, and at one decision per five-minute session (12 an hour) it is '
    + '0.1 / 12 = 0.0083. At each m the program chooses a fresh threshold that meets that '
    + 'allowance on the validation group, then reports the detection rate on the test group '
    + 'with its Wilson interval.'));
  add(formula('change = detection rate (slowest) − detection rate (fastest)'));
  add(mtable('How to read the decision-rate curve.', [2600, 6760], ['Outcome', 'What it supports'],
    [
      ['Rises, intervals separated', 'Deciding less often helps: check on the timescale over '
        + 'which the failure develops.'],
      ['Falls, intervals separated', 'Pooling destroys more than the looser allowance buys. '
        + 'The limit is in what the statistic can see.'],
      ['Intervals overlap', 'Not settled. More degraded sessions would narrow it.'],
    ], { after: `${T('b_rate')} of the paper takes one row per entry of \`curve\` in `
      + '`decision_rate.json` (fields `windows_per_decision`, `decisions_per_hour`, '
      + '`per_decision_fpr_allowed`, `threshold`, `detection_rate`, `detection_ci95`, '
      + '`false_alarms_per_hour`). The change and the separation are in '
      + '`change_slowest_minus_fastest` and `intervals_separated`. Prediction PP-7 holds only '
      + 'if the change is at least 10 percentage points.' }));

  sec('IV.9', 'Four apparatus configurations (experiment P-7)');
  add(P('`analyze_apparatus.py --configs A,B,C,D` repeats the main calculations separately in '
    + 'each configuration and writes `apparatus_variation.json`. Nothing new is calculated. '
    + `The point is the spread. ${T('b_app')} of the paper takes one row per configuration. `
    + 'Two predictions are decided from it. PP-9 holds if the sign of the decision-rate '
    + 'change is the same in all four. PP-10 holds if the median lead times differ by more '
    + 'than 10 seconds or the false-alarm rates by more than a factor of two. The four '
    + 'configurations are reported side by side and are never averaged, because an average '
    + 'would hide exactly what this experiment exists to show.'));

  sec('IV.10', 'Deciding the ten predictions');
  add(P(`Each outcome cell of ${T('predictions')} of the paper takes one of three words. `
    + '~Held~: the data meet the prediction. ~Falsified~: the data meet the falsifying '
    + 'condition in the third column. ~Untested~: the data cannot decide, for example '
    + 'because there were too few sessions or no false alarm occurred. The decision is made '
    + 'from the table named in the fifth column, by the rule written in advance, and by '
    + 'nothing else. A prediction that failed is reported with the same prominence as one '
    + 'that held.'));
  add(mtable('The value that decides each prediction.', [900, 4360, 4100],
    ['Code', 'Read this value', 'From'], [
      ['PP-1', 'Upper end of the false-alarm interval, against 0.1', T('b_fa')],
      ['PP-2', 'Share of fault-free sessions trending, raw, against 10%', T('b_fa')],
      ['PP-3', 'Median lead time and whether its interval excludes 0', T('b_lead_type')],
      ['PP-4', 'Largest magnitude of the three correlations, against 0.70', T('b_corr')],
      ['PP-5', 'Raw magnitude against partial magnitude', T('b_corr')],
      ['PP-6', 'Detection rate at severity 1.0 against 0.25', T('b_lead_sev')],
      ['PP-7', 'Change from fastest to slowest decision rate, against 10 points', T('b_rate')],
      ['PP-8', 'Difference in detection rate, undesigned against sealed; 20 points',
        T('b_undesigned')],
      ['PP-9', 'Sign of the decision-rate change in each configuration', T('b_app')],
      ['PP-10', 'Range of median lead times and of false-alarm rates', T('b_app')],
    ]));

  sec('IV.11', 'Comparing the bench with the archived recordings');
  add(P(`${T('compare')} of the paper already holds the archived values. The bench column is `
    + 'copied from the bench tables. The last column is filled by this rule: write "yes" if '
    + 'the bench result leads to the same statement as the archived result (for example, '
    + 'both median lead times are zero or negative; both false-alarm bounds are above the '
    + 'budget; the silence gate fails on both), and "no" otherwise. Agreement in direction '
    + 'is the claim. Agreement in size is not expected and is not claimed, because the bench '
    + 'is not a model of an implanted array.'));

  sec('IV.12', 'Checking a number by hand');
  add(P('Any reported value can be checked from `sessions.csv` in Excel or Google Sheets. The '
    + 'check for the false-alarm rate shows the method.'));
  add(numbered([
    'Open `physical/data/sessions.csv` (File, Open in Excel; File, Import in Google Sheets). '
    + 'Work on a copy.',
    'Turn on filters for the header row (Data, Filter). Filter `group` to `test` and '
    + '`healthy` to `TRUE`.',
    'Sum `duration_seconds` over the visible rows with `=SUBTOTAL(109, range)` and divide by '
    + '3600. This is H.',
    'Count the visible rows in which `warned` is `TRUE`. This is k.',
    'Compute k / H and the interval with the formulas of Section IV.3.',
    'Compare with `false_alarm.json`. They should agree to the rounding shown.',
  ]));
  add(P('If the two disagree, the cause is found before anything is written: a filter set '
    + 'wrongly, a stale file, or an error in the program. If the program is at fault it is '
    + 'corrected and every report is regenerated. The report is never changed by hand to '
    + 'match the spreadsheet.'));

  // =========================================================================
  part('V', 'Graph and Figure Generation');
  // =========================================================================
  sec('V.1', 'Rules for every graph');
  add(bullets([
    '**Every axis has a name and a unit,** for example "lead time (s)".',
    '**Every interval is drawn** and the caption says what kind it is (bootstrap 95%, Wilson '
    + '95%, exact Poisson 95%).',
    '**Reference lines are drawn and labelled:** zero on a lead-time axis, 0.1 per hour on a '
    + 'false-alarm axis, 0.70 on a correlation axis.',
    '**The caption states the number of sessions** and the file the data came from.',
    '**One quantity keeps one colour and one name** in every graph and in the text.',
    '**No three-dimensional effects, no decorative gridlines,** and no axis cut short to '
    + 'exaggerate a difference.',
    '**No graph is made from rehearsal output.** The templates below are layouts drawn by '
    + '`paper/make_figures.py`. They carry no numbers and are stamped as templates.',
  ]));

  sec('V.2', 'The six graphs written by the analysis software');
  add(P('One command writes all six to `physical/data/figures/`, each as a PNG file at 200 '
    + 'dots per inch. They are inserted into the paper unchanged.'));
  add(code(['python3 physical/code/figures.py all']));
  const tmpl = (a, b) => new D.Table({
    width: { size: L.W, type: D.WidthType.DXA }, columnWidths: [4680, 4680],
    rows: [new D.TableRow({ children: [a, b].map((nm) => new D.TableCell({
      width: { size: 4680, type: D.WidthType.DXA },
      borders: ['top', 'bottom', 'left', 'right'].reduce((o, k) => ({ ...o,
        [k]: { style: D.BorderStyle.NONE, size: 0, color: 'FFFFFF' } }), {}),
      children: [nm ? picture(drawn(nm), 290, `template ${nm}`)
        : new D.Paragraph({ children: [] })],
    })) })],
  });
  const tmplCaption = (text) => { L.state.mFig += 1;
    return caption(`Figure M${L.state.mFig}`, 'Templates.', text); };
  add(tmpl('t_session', 't_fa'), tmpl('t_lead', 't_sev'), tmpl('t_corr', 't_rate'));
  add(tmplCaption('Layouts of the six graphs written by `figures.py`, in the order of the table '
    + 'below. Layout only: no value in them is data.'));
  add(mtable('The six program-made graphs.', [1200, 1900, 2060, 2200, 2000],
    ['Paper figure', 'File', 'Axes', 'Marks and intervals', 'What it shows'], [
      [F('g_session'), '`session_detail.png`', 'x: time in the session (s). y: risk score',
        'One line; vertical marks at onset, failure and warning; the threshold as a '
        + 'horizontal line', 'One session from onset to warning. The caption names the '
        + 'session and the rule that chose it'],
      [F('g_fa'), '`false_alarm_evidence.png`', 'x: held-out fault-free hours. y: upper bound '
        + 'on the rate (per hour)', 'The curve 3 / H; the budget line; the point reached by '
        + 'this campaign', 'How much recording a given bound needs, and where this campaign '
        + 'stands'],
      [F('g_lead'), '`lead_time.png`', 'x: lead time (s). y: sessions',
        'One mark per detected session; a line at 0; the median with its bootstrap interval',
        'Whether warnings come before or after failure'],
      [F('g_sev'), '`severity_response.png`', 'x: severity (0.25, 0.5, 1.0). y: sessions '
        + 'detected (%)', 'One line per fault type, with intervals',
      'The manipulation check: stronger faults should be caught more often'],
      [F('g_corr'), '`correlation_vs_usability.png`', 'Left: correlation magnitude. Right: '
        + 'lead time and false-alarm rate', 'Three bars with the 0.70 line; two values with '
        + 'intervals', 'The evidence the field reports beside the quantities that decide use'],
      [F('g_rate'), '`decision_rate.png`', 'x: decisions per hour, log scale. y: sessions '
        + 'detected (%)', 'One point per rate with its Wilson interval',
      'Whether deciding less often helps'],
    ]));

  sec('V.3', 'Two graphs made in a spreadsheet');
  add(P(`${F('g_app')} and ${F('g_cmp')} of the paper are not written by the software. Each is `
    + 'a small graph of a median with its interval, made from a table of the paper.'));
  add(tmpl('t_app', 't_cmp'));
  add(tmplCaption(`Layouts for ${F('g_app')} (left) and ${F('g_cmp')} (right) of the paper. `
    + 'Layout only: no value in them is data.'));
  add(P('**Step 1. Lay out the data.** In an empty sheet enter one row per point, with these '
    + 'columns. The last two are calculated.'));
  add(grid([1700, 1400, 1400, 1400, 1730, 1730],
    ['label', 'median_s', 'lower_s', 'upper_s', 'err_minus', 'err_plus'], [
      ['A (or T11)', null, null, null, '=B2-C2', '=D2-B2'],
      ['B (or T5)', null, null, null, '=B3-C3', '=D3-B3'],
      ['C (or bench)', null, null, null, '=B4-C4', '=D4-B4'],
      ['D', null, null, null, '=B5-C5', '=D5-B5'],
    ]), spacer(170));
  add(P(`For ${F('g_app')} the values come from ${T('b_app')}. For ${F('g_cmp')} they come from `
    + `${T('compare')} and ${T('r_headline')}; T5 has no interval, so its two error cells are `
    + 'left empty and the caption says why.'));
  add(P('**Step 2, in Excel.**'));
  add(numbered([
    'Select the `label` and `median_s` columns. Choose Insert, Chart, Scatter (markers only).',
    'Click the chart, then Chart Design, Add Chart Element, Error Bars, More Error Bars '
    + 'Options.',
    'Choose vertical error bars, Custom, Specify Value. For the positive value select the '
    + '`err_plus` cells, for the negative value the `err_minus` cells.',
    'Delete the horizontal error bars if Excel adds them.',
    'Add axis titles (Add Chart Element, Axis Titles): "configuration" and "median lead time '
    + '(s)".',
    'Set the vertical axis so that 0 is included, and format the gridline at 0 as a solid '
    + 'dark line.',
    'Right-click the chart, Save as Picture, PNG.',
  ]));
  add(P('**Step 2, in Google Sheets.**'));
  add(numbered([
    'Select the `label` and `median_s` columns. Choose Insert, Chart, and set the chart type '
    + 'to Scatter chart.',
    'In the chart editor open Customize, Series, and tick Error bars. Sheets offers a '
    + 'constant or a percentage only. If the intervals are not symmetric, use a column chart '
    + 'with the interval limits written in the caption, or make the graph in Excel.',
    'Under Chart and axis titles enter both axis titles.',
    'Under Vertical axis set a minimum and maximum that include 0.',
    'Use the three-dot menu of the chart, Download, PNG image.',
  ]));
  add(P('**Step 3. Check.** Read the median and both ends of the interval off the finished '
    + 'graph for one point and compare them with the table. Then insert the picture as '
    + 'described at the end of Section II.5.'));

  sec('V.4', 'Captions');
  add(P('The paper already holds a proposed title and caption for every figure. When the '
    + 'picture goes in, the caption is completed with what only the data can supply: the '
    + 'number of sessions, the session shown, the kind of interval. A caption states what '
    + 'the figure shows. What the figure means belongs in the text.'));

  sec('V.5', 'Cross-reference of every figure in the paper');
  const kinds = {
    overview: ['Drawing', 'present', '`paper/make_figures.py`'],
    drift: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    repo: ['Drawing', 'present', '`paper/make_figures.py`'],
    ph_parts: ['Photograph PH-1', 'to add', 'II.2'],
    ph_components: ['Photographs PH-2', 'to add', 'II.2'],
    comp: ['Drawing', 'present', '`paper/make_figures.py`'],
    monitor: ['Drawing', 'present', '`paper/make_figures.py`'],
    episode: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    chain: ['Design drawing', 'present', '`physical/figures/fig-chain.png`'],
    benchflow: ['Design drawing', 'present', '`physical/figures/fig-workflow.png`'],
    wiring_stepper: ['Wiring drawing', 'present', '`physical/figures/wiring-stepper.png`'],
    wiring_dht22: ['Wiring drawing', 'present', '`physical/figures/wiring-dht22.png`'],
    onset: ['Design drawing', 'present', '`physical/figures/fig-onset.png`'],
    calib: ['Design drawing', 'present', '`physical/figures/fig-calib.png`'],
    ph_open: ['Photograph PH-3', 'to add', 'II.2'],
    ph_sealed: ['Photograph PH-4', 'to add', 'II.2'],
    ph_header: ['Photograph PH-5', 'to add', 'II.2'],
    ph_annotated: ['Photograph PH-6', 'to add', 'II.2, II.4'],
    ph_sensor: ['Photograph PH-7', 'to add', 'II.2'],
    ph_inside: ['Photograph PH-8', 'to add', 'II.2'],
    ss_session: ['Screenshot SS-1', 'to add', 'II.3'],
    ss_check: ['Screenshot SS-2', 'to add', 'II.3'],
    dataflow: ['Drawing', 'present', '`paper/make_figures.py`'],
    stats: ['Drawing', 'present', '`paper/make_figures.py`'],
    lead: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    fa: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    modes: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    dfa: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    gap: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    decision: ['Chart, real data', 'present', '`poster/poster_data.json`'],
    g_session: ['Graph, bench', 'to add', 'V.2: `session_detail.png`'],
    g_fa: ['Graph, bench', 'to add', 'V.2: `false_alarm_evidence.png`'],
    g_lead: ['Graph, bench', 'to add', 'V.2: `lead_time.png`'],
    g_sev: ['Graph, bench', 'to add', 'V.2: `severity_response.png`'],
    g_corr: ['Graph, bench', 'to add', 'V.2: `correlation_vs_usability.png`'],
    g_rate: ['Graph, bench', 'to add', 'V.2: `decision_rate.png`'],
    g_app: ['Graph, spreadsheet', 'to add', 'V.3'],
    g_cmp: ['Graph, spreadsheet', 'to add', 'V.3'],
  };
  const titles = t.figureTitles;
  for (const k of L.REG.figures) {
    if (!kinds[k] || !titles[k]) throw new Error(`figure ${k} missing from the cross-reference`);
  }
  add(mtable('All figures of the paper.', [800, 3660, 1700, 900, 2300],
    ['No.', 'Title', 'Kind', 'Status', 'Source or manual section'],
    L.REG.figures.map((k) => [String(L.figNo(k)), titles[k].replace(/\.$/, ''), ...kinds[k]]),
    { after: 'Charts of real data are drawn by `poster/charts.py` from numbers that '
      + '`poster/build_poster_data.py` recomputes from `data/processed/`. To redraw every '
      + 'present figure: `python3 paper/make_figures.py`, then `node paper/render_svgs.js`.' }));

  // =========================================================================
  part('VI', 'Completing Each Section of the Paper');
  // =========================================================================
  sec('VI.1', 'Observation, interpretation, conclusion');
  add(P('Three kinds of statement appear in a research paper, and each has its own place. '
    + 'Keeping them apart is the main discipline of writing the remaining sections.'));
  add(mtable('Three kinds of statement, with an example from the finished computational work.',
    [1700, 2500, 3360, 1800], ['Kind', 'What it is', 'Example', 'Belongs in'], [
      ['Observation', 'What was measured, with its uncertainty. No "because".',
        'The median lead time on T11 was −20 s (95% interval −25 to −10 s).',
        'Results (6)'],
      ['Interpretation', 'What the observation indicates and why, compared across '
        + 'conditions and with expectation.', 'The score rises with time even without a '
        + 'fault, so a fixed threshold is crossed late.', 'Analysis (7), Discussion (8)'],
      ['Conclusion', 'The answer to the research question, by the rule fixed in advance.',
        'Hypothesis A is rejected.', 'Conclusion (11)'],
    ]));
  add(P('**Turning red into black.** When a red item is completed: write the text, select it, '
    + 'set the font colour to Automatic, remove bold, and delete the square brackets and the '
    + 'code. For a pink cell, type the value and set the cell shading to No Colour. For a '
    + 'dashed box, follow the end of Section II.5. Tick the item in Section VII.4.'));
  add(P('**Changing black text.** The black text was checked against the repository on '
    + `${meta.date}. It is changed only if a fact changes, and then the repository is changed `
    + 'first. The exception is tense: Section 5.3 is written in the future tense and is put '
    + 'into the past tense once the bench work is done, sentence by sentence, changing each '
    + 'one to say what was actually done.'));

  const how = (rows) => { add(grid([2100, 7260], ['Question', 'Answer'], rows), spacer(170)); };
  sec('VI.2', 'Section 1, Abstract');
  how([
    ['Already there', 'Background, purpose, the computational method and its results.'],
    ['Still needed', 'R1.1: the bench results. R1.2: the closing sentence with the verdict. '
      + 'R0.1: the final title (below).'],
    ['Evidence to use', 'Tables 14, 15, 16 and 19 and Section 11 of the paper.'],
    ['How to write it', 'Last of all. Order: purpose, procedure, data, conclusion. Give '
      + 'numbers with units. Then cut the whole abstract to the limit of the fair (often 250 '
      + 'words), shortening the background first and never the results.'],
    ['Errors to avoid', 'New information that is not in the paper; citations; a conclusion '
      + 'stronger than Section 11.'],
  ]);
  add(P('**The title.** The title page of the paper carries a working title, written for the '
    + 'draft, and item R0.1. The title of the research plan submitted on 15 September 2026 is '
    + 'not used. The final title is the researcher\'s. A title for a paper of this kind '
    + 'usually names what was measured, on what, and by what method, and promises nothing the '
    + 'paper does not show. It is settled with the abstract, because both must describe the '
    + 'paper as it finally stands, and the same title then goes on the abstract, the forms and '
    + 'the poster.'));
  sec('VI.3', 'Section 2, Introduction');
  how([
    ['Already there', 'Background, the problem, the gap, the approach.'],
    ['Still needed', 'Nothing from the bench. Read it once more at the end so that it '
      + 'promises only what the paper delivers.'],
    ['Errors to avoid', 'Adding results here; claiming clinical benefit; citing a source '
      + 'that has not been opened.'],
  ]);
  sec('VI.4', 'Section 3, Hypothesis and Research Questions');
  how([
    ['Already there', 'Both research questions, the engineering goal, both hypotheses as '
      + 'frozen, the judging rule.'],
    ['Still needed', 'Three status cells of Table 1 (R3.1 to R3.3).'],
    ['Evidence to use', 'The verdict of Section 7.4.'],
    ['How to write it', 'One or two words per cell: "Supported", "Falsified", '
      + '"Inconclusive"; for the question, "Answered (Section 11)".'],
    ['Errors to avoid', 'Rewording a hypothesis after the result is known. The quoted text is '
      + 'frozen.'],
  ]);
  sec('VI.5', 'Section 4, Materials');
  how([
    ['Already there', 'The archived recordings, the software, the bill of materials as '
      + 'specified.'],
    ['Still needed', 'R4.1 versions on the bench computer; R4.2 the three pink columns of '
      + `Table 4; photographs for ${F('ph_parts')} and ${F('ph_components')}.`],
    ['Evidence to use', 'Logbook sheets A and B; photographs PH-1 and PH-2.'],
    ['How to write it', 'Enter what was received, not what was ordered. Name any '
      + 'substitution in a sentence beneath the table.'],
    ['Errors to avoid', 'Leaving the specification in place of a part that differed.'],
  ]);
  sec('VI.6', 'Section 5, Methods');
  how([
    ['Already there', 'The computational method in full; the physical method as a plan.'],
    ['Still needed', 'R5.1 sensor pins; R5.2 final settings; eight photographs and '
      + 'screenshots; R5.11 the record of the campaign; the change of tense.'],
    ['Evidence to use', 'Logbook sheets B, C and D; `SESSION_LOG.csv`; Part II of this '
      + 'manual.'],
    ['How to write it', 'Past tense, in the order the work was done, with enough detail that '
      + 'someone else could repeat it. Where what was done differs from the plan, say what '
      + 'was done and refer to Table 25.'],
    ['Errors to avoid', 'Describing the plan as if it had been followed when it was not; '
      + 'putting results or reasons for results here.'],
  ]);
  sec('VI.7', 'Section 6, Results');
  how([
    ['Already there', 'Section 6.1 in full.'],
    ['Still needed', 'Every table, graph and passage of Section 6.2.'],
    ['Evidence to use', 'The files in `physical/data/results/` and '
      + '`physical/data/figures/`, by the mappings of Part IV and Part V.'],
    ['How to write it', 'Observations only. One paragraph per experiment: what was '
      + 'measured, the value, its interval, the number of sessions, the table and figure. '
      + 'Report what the preregistration said would be reported, in its order, including '
      + 'results that are unfavourable or unclear.'],
    ['Errors to avoid', 'The word "because"; "zero false alarms" without the bound; a lead '
      + 'time without its false-alarm rate; pooling P-5 with P-3; averaging the four '
      + 'configurations; words such as "significant" without the test and the value.'],
  ]);
  add(P('A sentence pattern that keeps a result an observation: "In [experiment], [quantity] '
    + 'was [value] ([kind of interval], [limits]; n = [sessions]) ([table])." Every bracket '
    + 'is filled from one named file.'));
  sec('VI.8', 'Section 7, Analysis');
  how([
    ['Already there', 'Section 7.1; the predictions table without outcomes; the comparison '
      + 'table without the bench column.'],
    ['Still needed', 'R7.1 the outcomes; R7.2 the bench column; the comparison graph; R7.4 '
      + 'the verdict paragraph.'],
    ['Evidence to use', 'Sections IV.10, IV.11 and IV.7 of this manual.'],
    ['How to write it', 'Apply each rule and state its result. Then describe patterns: '
      + 'which fault types differ, whether stronger faults are caught more often, whether '
      + 'the raw correlation exceeds the partial one and what the time correlations say '
      + 'about that.'],
    ['Errors to avoid', 'Deciding a prediction by a rule other than the written one; '
      + 'calling an untested prediction "held".'],
  ]);
  sec('VI.9', 'Section 8, Discussion');
  how([
    ['Already there', 'Sections 8.1 and 8.4 for the computational work.'],
    ['Still needed', 'R8.1 to R8.5: the meaning of the bench results, alone and beside the '
      + 'archived results.'],
    ['Evidence to use', 'The outcome tables of Sections IV.4, IV.7 and IV.8, which state '
      + 'what each possible outcome supports.'],
    ['How to write it', 'For each main result: state it in one clause, say what it '
      + 'indicates, give the strongest alternative explanation, and say what would '
      + 'distinguish them. Then state the limits.'],
    ['Errors to avoid', 'A claim about implanted arrays from the bench; a causal claim from '
      + 'a correlation; treating agreement with a prediction as proof of the reasoning '
      + 'behind it.'],
  ]);
  add(P('Seven limits apply whatever the results are and are stated every time a bench number '
    + 'is interpreted: one apparatus in one room; a false-alarm rate on the bench is not an '
    + 'estimate for an implanted array; matching the difficulty of decoding does not match '
    + 'the noise or the failure modes; most faults are still designed; P-5 has ten sessions '
    + 'and hand-timed onsets; sessions last five minutes; every number is conditional on the '
    + 'stated budget. The decision-rate question is the exception to the second limit, '
    + 'because it concerns drifting many-channel sensors in general.'));
  sec('VI.10', 'Section 9, Future Work');
  how([
    ['Already there', 'The next step and four extensions that follow from the computational '
      + 'work.'],
    ['Still needed', 'R9.1: questions the bench raised.'],
    ['How to write it', 'Each item as a question with the measurement that would answer it. '
      + 'Remove the first paragraph once the bench work is done.'],
    ['Errors to avoid', 'A list of wishes with no stated measurement; any work on people.'],
  ]);
  sec('VI.11', 'Section 10, Sources of Error');
  how([
    ['Already there', 'Fourteen sources with their controls; the computational sizes.'],
    ['Still needed', 'R10.1 observed sizes on the bench; R10.2 the departures; R10.3 the '
      + 'paragraph on which errors matter.'],
    ['Evidence to use', 'Table 13; `SESSION_LOG.csv` (temperature range); sheets C, D and E '
      + 'of the logbook.'],
    ['How to write it', 'Give each error a size where one exists. For the paragraph, sort '
      + 'the sources into those that could reverse a conclusion and those that could only '
      + 'widen an interval, with the reason.'],
    ['Errors to avoid', 'Listing "human error" without saying which action and how large; '
      + 'omitting a departure because it seems minor.'],
  ]);
  sec('VI.12', 'Section 11, Conclusion');
  how([
    ['Already there', 'The conclusion of the computational validation.'],
    ['Still needed', 'R11.1 the conclusion of the bench; R11.2 the joint statement.'],
    ['Evidence to use', 'Section 7.4 of the paper.'],
    ['How to write it', 'Answer each research question in a sentence, state the verdict on '
      + 'each hypothesis with the rule that produced it, give the main limit, stop.'],
    ['Errors to avoid', 'New results; new arguments; "proved"; a verdict other than the one '
      + 'the rule gives.'],
  ]);
  sec('VI.13', 'Section 12, References');
  how([
    ['Already there', 'Ten entries. One is complete. Nine are marked with a dagger because '
      + 'the project records hold first authors only.'],
    ['Still needed', 'R12.1 complete each entry from the publisher\'s page; R12.2 open '
      + 'Sendelbach and Funk (2013) or cite the report that quoted it; R12.3 the final '
      + 'commit.'],
    ['How to do it', 'Enter each doi at doi.org. Copy authors, year, title, journal, volume, '
      + 'pages. Use one style throughout (the paper uses author and year). Every source '
      + 'cited in the text appears in the list and every entry is cited.'],
    ['Note', 'The bibliography of the submitted plan also lists Swanson (2026), which could '
      + 'not be confirmed on 12 and 13 November 2026. It is not cited in the paper. It is '
      + 'added only if the article is found and read.'],
  ]);
  sec('VI.14', 'Section 13, Acknowledgments and the AI statement');
  how([
    ['Already there', 'One sentence on the origin of the recordings.'],
    ['Still needed', 'R13.1 the acknowledgments; R13.2 the statement on the use of AI.'],
    ['Who writes it', 'The researcher alone. On 8 September 2026 it was decided that the AI '
      + 'statement must not be written by an AI system, because a disclosure that an AI '
      + 'wrote about itself is not a disclosure. This manual therefore gives no wording.'],
    ['Evidence to use', '`research/AI_INVOLVEMENT_RECORD.md` and `research/research_log.md` '
      + 'hold the factual record of what was done with AI assistance and what was checked.'],
    ['What a statement of this kind usually covers', 'Which tools; for which tasks; what the '
      + 'researcher verified and how; which decisions were the researcher\'s. The rules of '
      + 'the fair say whether a particular form is required.'],
  ]);

  // =========================================================================
  part('VII', 'Final Assembly and Quality Control');
  // =========================================================================
  sec('VII.1', 'Order of assembly');
  add(numbered([
    'Fill Tables 4 and 13 and place the eight photographs and two screenshots (stages 2, 3).',
    'Fill Tables 14 to 21 and place the eight graphs (stages 6 to 9).',
    'Write the red passages of Section 6.2.',
    'Fill Tables 22 and 23; write Sections 7.4, 8.2 and 8.3.',
    'Fill Tables 24 and 25; write the paragraph of Section 10.',
    'Write Section 11, then the status cells of Table 1.',
    'Put Section 5.3 into the past tense.',
    'Complete the references; write the acknowledgments and the AI statement.',
    'Write the abstract and cut it to length.',
    'Run the checks of Section VII.2.',
  ]));

  sec('VII.2', 'Checks before the paper is called finished');
  add(bullets([
    '**No red remains.** Search the document for "[R" and for red text (Find, Advanced Find, '
    + 'Format, Font, colour). Search for pink cells by eye, table by table.',
    '**Every number has a source.** For each number in Sections 6 to 8, find it in a results '
    + 'file or in `poster/poster_data.json`. A number that cannot be found is removed or '
    + 'traced.',
    '**Numbers agree with each other.** The same quantity has the same value in the '
    + 'abstract, the results, the comparison table and the conclusion.',
    '**Figures and tables are numbered in order** and each is mentioned in the text before it '
    + 'appears.',
    '**Terms are used with one meaning** (table below).',
    '**The verdict is the one the rule gives.**',
    '**The repository is cited at its final commit,** and `python3 tools/check_all.py` passes '
    + 'at that commit.',
    '**The rules of the fair are met:** length, abstract limit, forms, and the form of the '
    + 'AI statement.',
    '**Someone else has read it.** A reader who does not know the project should be able to '
    + 'say what was measured and what was found.',
  ]));
  add(mtable('Terms used with one meaning in both documents.', [2300, 7060], ['Term', 'Meaning'],
    [
      ['Window', '30 seconds of signal; a new window begins every 5 seconds'],
      ['Episode', 'One archived block with or without a planted fault (computational)'],
      ['Session', 'One five-minute bench recording (physical)'],
      ['Onset', 'The moment a fault begins, fixed before the recording is analysed'],
      ['Failure', 'The first window in which decoding error is 10° or more above its '
        + 'level before the onset'],
      ['Warning', 'The first window in which the risk score is at or above the threshold'],
      ['Lead time', 'Time of failure minus time of warning; positive means warning first'],
      ['Detection delay', 'Time of warning minus time of onset'],
      ['False alarm', 'A warning during fault-free recording, or one whose window ended '
        + 'before the onset'],
      ['Fault-free', 'No fault was planted or imposed'],
      ['Healthy (computational)', 'An episode in which decoding never failed, whether or not '
        + 'a fault was planted'],
      ['Budget', '0.1 false alarms per hour'],
      ['Gate', 'A condition fixed in advance that a result must meet to count'],
      ['Computational validation', 'Planted faults in archived recordings; complete'],
      ['Physical validation', 'Imposed faults on the optical bench; preregistered, not built'],
    ]));

  sec('VII.3', 'Completion checklist');
  add(mtable('Tick each line when it is done.', [6560, 1400, 1400], ['Item', 'Date', 'Done'], [
    ['All fourteen parts received and Table 4 filled', null, null],
    ['Photographs PH-1 to PH-8 taken, checked and placed', null, null],
    ['Five acceptance gates passed; Table 13 filled; SS-2 placed', null, null],
    ['Final settings recorded and entered in Section 5.3', null, null],
    ['P-1, P-2, P-3, P-5, P-7 recorded; Table 14 filled', null, null],
    ['Raw data copied to the USB drive; exclusions listed', null, null],
    ['Rehearsal output removed; session table made twice', null, null],
    ['Five analysis programs run; reports committed together', null, null],
    ['Six program graphs and two spreadsheet graphs placed', null, null],
    ['Tables 15 to 21 filled and one value in each checked by hand', null, null],
    ['Section 6.2 written as observations only', null, null],
    ['Tables 22 and 23 filled; verdict stated by the rule', null, null],
    ['Sections 8.2, 8.3 and the limits written', null, null],
    ['Tables 24 and 25 filled; every departure listed', null, null],
    ['Section 11 written; Table 1 status cells filled', null, null],
    ['Section 5.3 in the past tense', null, null],
    ['References complete and each one opened', null, null],
    ['Acknowledgments and AI statement written by the researcher', null, null],
    ['Abstract rewritten within the word limit', null, null],
    ['No red text, pink cell or dashed box remains', null, null],
    ['`python3 tools/check_all.py` passes at the cited commit', null, null],
  ]));

  sec('VII.4', 'Index of every red item in the paper');
  add(P(`The paper contains ${reds.length} red items. This index is written by the same `
    + 'program that writes the paper, so the two cannot disagree. For each item it gives the '
    + 'instruction as printed, where the missing content comes from, and the section of this '
    + 'manual that explains how to produce it.'));
  const secName = { 0: 'Title page', 1: 'Abstract', 3: 'Hypothesis', 4: 'Materials', 5: 'Methods', 6: 'Results',
    7: 'Analysis', 8: 'Discussion', 9: 'Future Work', 10: 'Sources of Error', 11: 'Conclusion',
    12: 'References', 13: 'Acknowledgments' };
  add(grid([700, 1150, 3300, 3210, 1000],
    ['Code', 'Section', 'What goes there', 'Comes from', 'Explained in'],
    reds.map((r) => [r.id, `${r.section} ${secName[r.section]}`, r.plain, r.from, r.see]),
    { size: 17 }));
};
