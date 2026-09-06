# -*- coding: utf-8 -*-
"""Sections 5-8."""
from kit import *


def section_5():
    s = H1('5. Dataset audit', 'Section 5')
    s += P('Two datasets exist in this project: one downloaded, one constructed. They are '
           'audited separately because their evidentiary status is completely different.')

    s += H2('5.1 The archived dataset &#8212; provenance')
    s += TBL(['Field', 'Value'], [
        ['Name', 'MINDFUL &#8212; &#8220;Measuring instability in chronic human intracortical '
         'neural recordings towards stable, long-term brain-computer interfaces&#8221;'],
        ['Publication', 'Pun et al. (2024), <i>Communications Biology</i>'],
        ['DOI', M('10.5061/dryad.n2z34tn5s') + ' &#8212; Dryad, version 6'],
        ['Licence', B('CC0-1.0') + ' &#8212; public domain dedication, no restriction on reuse'],
        ['Downloaded', '2026-08-25 18:14:05 UTC, by ' + M('scripts/01_download_dataset.py') +
         ' against ' + M('https://datadryad.org/api/v2')],
        ['Files', '2 &#8212; ' + M('MINDFUL_Data.zip') + ' (411,951,588 bytes) and ' +
         M('README.md') + ' (3,348 bytes)'],
        ['Integrity', B('SHA-256 verified against the digest Dryad reported') + ': ' +
         M('6d12b5dbcf9cac654ff1d0679e9753bf042b56cd5b8852eb31236b3cdecf7332')],
        ['Extracted', '166 files, 825,449,877 bytes &#8212; 162 ' + M('.mat') + ', 3 ' + M('.md') +
         ', 1 ' + M('.zip')],
        ['Ethics', 'Collected years earlier by the depositing researchers under their own '
         'approvals. ' + B('This project recruits nobody.')],
    ], [0.16, 0.84], fs=8.3)
    s += CALLOUT(
        'A terminology hazard that the repository addresses head-on, in commit ' + M('7102ff6') +
        ' (&#8220;Say plainly that &#8216;participant&#8217; never means a recruited '
        'person&#8221;): in this project ' + B('&#8220;participant&#8221; means whose published '
        'recording a data file contains') + ' &#8212; T5, T11, T15 &#8212; using the depositing '
        'authors&#8217; own convention. It does not mean a person this project recruits. '
        '&#8220;Adding a third participant&#8221; means downloading one more public file. '
        'Nobody is recruited, nobody wears anything, no consent form exists, and ISEF Form&nbsp;4 '
        'is not expected to apply.',
        tone='neutral', label='&#8220;Participant&#8221; does not mean what it usually means')

    s += H2('5.2 What is actually in it')
    s += TBL(['', 'T11', 'T5', 'Note'], [
        ['Sessions (trial days)', '15', '6', 'Plus 2 extra T11 sessions on different tasks'],
        ['Blocks used in the corpus', '29', '21', ''],
        ['Trials', '1,839', '1,200', '3,301 in total including the extra sessions'],
        ['Neural features per bin', B('384'), B('192'), 'T5 has no spike-power channels'],
        ['Trial-day span', '658&#8211;800 (' + B('142 days') + ')', '2121&#8211;2149 (' +
         B('28 days') + ')', 'T11 is the longitudinal one'],
        ['Bins at 20&nbsp;ms', '530,734', '251,974', '782,708 total &#8212; ' + B('4.35 hours') +
         ' of recording in all. ' + B('Note:') + ' the bin counts cover every recorded block, '
         'including the two extra T11 sessions, while the trial counts above are the main cohort '
         'only &#8212; 3,301 trials in total'],
    ], [0.26, 0.20, 0.20, 0.34], fs=8.3)
    s += NOTE(B('Recorded correction to the literature review:') + ' it had the two participants '
              'reversed. T11, not T5, is the longitudinal record. Found by inspecting the data '
              'rather than by re-reading the paper.')

    s += H2('5.3 Verification performed on the archived data')
    s += TBL(['Claim checked', 'Method', 'Outcome'], [
        ['The decoder in the published study is fixed',
         'The paper&#8217;s Methods, and independently from the data itself',
         B('Confirmed twice') + ' &#8212; and the Methods reveal more: weights are frozen but an ' +
         B('adaptive normalisation layer runs continuously') + ' (3-minute rolling z-score for '
         'T11; bias correction at rate 0.3 for T5)'],
        ['Performance genuinely degrades',
         'Two independent measures, change-point located by three agreeing methods',
         'T11 steps at trial day 758 (p&nbsp;=&nbsp;0.0018); T5 dips and recovers'],
        ['Task type is not a confound',
         'Task name tabulated by session',
         'One task per participant throughout the main cohort'],
        ['The analysis pipeline is correct',
         'Reproduce the published Figure&nbsp;1b from the raw deposit',
         B('r&nbsp;=&nbsp;0.985 against the published 0.985')],
        ['The EWS detector works at all',
         'Synthetic positive and negative controls with known answers',
         'Fires on a bifurcation, stays silent on monotonic drift'],
        ['The detector has adequate power',
         'Power scaling against record length',
         '0.25 &#8594; 1.00 as records lengthen'],
    ], [0.24, 0.30, 0.46], fs=8.0)

    s += H2('5.4 The constructed dataset &#8212; the fault corpus')
    s += P('This is the project&#8217;s original scientific artefact, and it is the answer to '
           '&#167;4.2. It does not exist anywhere publicly.')
    s += TBL(['Property', 'T11 corpus', 'T5 corpus'], [
        ['Episodes', B('1,073'), B('777')],
        ['Blocks drawn from', '29', '21'],
        ['Design', '4 modes &#215; 3 rates &#215; 3 severities, balanced, plus NONE controls',
         'Identical design'],
        ['Onset window', '0.25&#8211;0.55 of each block, uniformly drawn', 'Identical'],
        ['Ramp', 'Linear; fast&nbsp;=&nbsp;0.10 of block, medium&nbsp;=&nbsp;0.35, '
         'slow&nbsp;=&nbsp;0.80', 'Identical'],
        ['Master seed', M('20260826') + ', with a derived per-episode seed stored per episode',
         'Same master seed'],
        ['Plan created', '2026-08-27 17:48:12 UTC at commit ' + M('6edf505'),
         '2026-08-28 02:14:02 UTC at commit ' + M('f2d6efc')],
        ['Checksum of the episode list', M('37faf7dc71ad43&#8230;'), M('3c96508c1805ec&#8230;')],
        ['Amendments', '1, with its reason recorded in the file', '0'],
        [B('Episodes whose injected fault actually did measurable damage'),
         B('764 of 1,073'), B('369 of 777')],
        ['Split &#8212; ' + B('by block') + ', never by episode',
         'test 851 / fit 148 / validation 74; 586 of the 851 test episodes crossed',
         'test 444; 219 of them crossed'],
    ], [0.24, 0.42, 0.34], fs=8.1)

    s += NOTE(B('A distinction that matters and is easy to misread:') + ' &#8220;crossing&#8221; '
              'is one of the three ' + B('designed') + ' severity levels (348 episodes on T11, '
              '252 on T5), while &#8220;crossed&#8221; above means the fault, once applied, ' +
              B('actually pushed the frozen decoder past its degradation threshold') + ' &#8212; '
              'an outcome, not a setting. On near-chance sessions a crossing-severity fault often '
              'does not cross, which is limitation L03.')
    s += H3('The four injected failure modes, and what each is designed to test')
    s += TBL(['Mode', 'What it does to the feature stream', 'Severities (benign / sub / crossing)',
              'What it tests'], [
        [M('RATE_LOSS'), 'Scales all channels down together', '0.10 / 0.25 / 0.55',
         'The easy case &#8212; total activity falls, so counting spikes should win'],
        [M('CHANNEL_DROPOUT'), 'Zeroes a ' + B('nested') + ' set of channels',
         '0.05 / 0.30 / 0.60',
         'Nested across severities so the ladder is monotone &#8212; it was not, originally'],
        [M('GAIN_DRIFT'), 'Per-channel gain change, ' + B('mean-conserved per bin'),
         '0.20 / 0.50 / 1.20',
         'Channels drift apart with total activity preserved &#8212; counting spikes must fail'],
        [M('GEOMETRY_ROTATION'), 'Norm-preserving Givens rotations of the channel vector',
         '0.15 / 0.45 / 1.20',
         'Shape changes, magnitude does not &#8212; the strongest test of the comparator gate'],
    ], [0.17, 0.28, 0.16, 0.39], fs=7.9)

    s += H3('Four bugs the corpus would have hidden, found before it was used')
    s += TBL(['Bug', 'Why it mattered', 'Fix'], [
        [M('GAIN_DRIFT') + ' was not mean-preserving &#8212; twice',
         'Log-centring preserves the <i>geometric</i> mean, leaving +116% at crossing severity; '
         'pre-onset rescaling still left +20.8%. A mode designed to be invisible to a spike '
         'counter was loudly visible to one.',
         'Conserved per bin: now &#8722;2.4%'],
        [M('CHANNEL_DROPOUT') + '&#8217;s severity ladder ran backwards',
         'Each level drew an independent channel set, so a &#8220;more severe&#8221; level could '
         'remove easier channels.',
         'Nested channel sets; ladder now monotone'],
        ['The pre-onset guarantee held only by floating-point luck',
         'A leak of post-onset data into the pre-onset window would let a detector '
         '&#8220;warn&#8221; off the leak itself &#8212; a perfect self-fulfilling result.',
         'Enforced by construction'],
        ['T5 ran with an empty test set',
         'The harness reported nothing and did not complain.',
         'The harness now refuses to run rather than reporting nothing'],
    ], [0.26, 0.48, 0.26], fs=8.0)

    s += H2('5.5 The corpus&#8217;s own limitations, as measured')
    s += UL([
        B('Severity is only valid in aggregate (L01).') + ' The three levels are correctly '
        'ordered in 57% of session&#215;mode cells on T11 and 67% on T5, and validity degrades '
        'as the session&#8217;s baseline error rises (&#961;&nbsp;=&nbsp;&#8722;0.677 and '
        '&#8722;0.926). This is the only relationship in the project that replicates '
        'significantly with the same sign on both participants.',
        B('Window overlap contaminates the healthy reference (L02).') + ' Windows are 30&nbsp;s '
        'and step 5&nbsp;s, so six windows per episode that <i>start</i> before onset still '
        '<i>span</i> it. Measured cost: every AUC understates by 0.007 (T11) and 0.012 (T5). '
        'The bias is ' + B('conservative') + ' &#8212; it pulls the reference toward the fault '
        '&#8212; and 11 of 13 days improve when it is removed (sign test, p&nbsp;=&nbsp;0.011). '
        'No conclusion changes. The fix for a future run is stated: require ' +
        M('start + window <= onset_bin') + '.',
        B('On bad sessions the ground truth is nearly degenerate (L03).') + ' Where the decoder '
        'is already near chance, an injected fault does almost no measurable damage. ' +
        B('6 of 13 T11 sessions cannot be scored on unambiguous faults at all') + '; day 783 '
        'retains 1 measurable fault of 20, day 672 retains none.',
        M('GEOMETRY_ROTATION') + ' ' + B('at crossing severity clips 17% of entries') + ' and '
        'loses 18% of mean activity, so at that level it stops being a clean test of the '
        'comparator gate.',
        B('Evaluation is open-loop.') + ' An injected episode is a recording; it cannot adapt. '
        'Performance is therefore the frozen decoder&#8217;s angular error against the '
        'participant&#8217;s real recorded intended direction, not closed-loop task success. '
        'This is a direct consequence of Amendment&nbsp;1 and is stated as a limitation, not '
        'discovered later.',
    ])
    s += CALLOUT(
        'The honest pairing, which the project states itself: ' + B('recorded sessions have live '
        'human compensation but unknown onset; injected episodes have known onset but no live '
        'compensation.') + ' Neither alone is sufficient. Every quantitative claim in the project '
        'must say which of the two it rests on &#8212; and the reports do.',
        tone='neutral', label='What the two data sources give between them')
    return s


def section_6():
    s = H1('6. Codebase audit', 'Section 6')
    s += P('65 scripts, 17,807 lines. They are numbered in the order they were written, which is '
           'mostly &#8212; but, as the project&#8217;s own audit discovered, not entirely &#8212; '
           'the order they run in.')

    s += H2('6.1 The pipeline, in execution order')
    s += TBL(['Stage', 'Scripts', 'What it does'], [
        [B('Acquire'), '01&#8211;04',
         'Download from Dryad with SHA-256 verification; inspect the archive; load the nested ' +
         M('.mat') + ' tree into tidy tables; produce the exploration report'],
        [B('Validate the method'), '05&#8211;10',
         'Check the decoder is fixed; build synthetic EWS positive/negative controls; power '
         'sweep; record-length check; ' + B('reproduce the published MINDFUL result') +
         ' (r&nbsp;=&nbsp;0.985); design power analysis'],
        [B('Preregister'), '11&#8211;13',
         'Compare six deterioration definitions using performance data only; ' + B('freeze the '
         'design') + ' with data hashes and a git commit; select the observable'],
        [B('Phase 1&#8211;2 analysis'), '14&#8211;16',
         'Run the preregistered analysis; diagnose the drift; synthesise'],
        [B('Build ground truth'), '17&#8211;18',
         'The fault injector (onsets locked under checksum); the frozen reference decoder'],
        [B('Build the grader'), '19&#8211;21',
         'The detector contract; the evaluation harness; the score report. ' + B('Committed '
         'before the monitor existed') + ' &#8212; at that point the only detectors it could '
         'score were three baselines this project did not invent'],
        [B('Build the monitor'), '22&#8211;25',
         M('decoder-guard') + '; benchmark figures; the 48-configuration matrix; the task-change '
         'test'],
        [B('Interrogate'), '26&#8211;30',
         'Achievability; decision rules; the operating-point bound; the aggregation limit; the '
         'demo export'],
        [B('Preregistered follow-ups'), '32&#8211;54',
         'Feature families; combination; transfer; calibration curve; staleness; day variance; '
         'pooling loss; day predictors; mediation; label-free signals; cross-detector day effect; '
         'ceiling challenge; unambiguous episodes; per-day chance; severity ladder; window overlap'],
        [B('Self-audit'), '55&#8211;65',
         'Reproducibility audit; claims register; attribution accuracy; mode separability; '
         'per-mode detection; unit of analysis; hygiene linter; permutation-invariant features; '
         'invariant detector; invariant attribution; log coverage'],
        [B('Runs last'), '31 and 55',
         B('Out of numeric order, and now documented as such') + '. ' + M('31_verify_claims.py') +
         ' reads output from fifteen higher-numbered scripts because it recomputes every headline '
         'from whatever the pipeline produced. Its number records when it was written, not where '
         'it runs.'],
    ], [0.19, 0.13, 0.68], fs=8.0)

    s += H2('6.2 Dependencies and environment')
    s += TBL(['Package', 'Pin', 'Why it is here'], [
        [M('requests'), '&#8805;&nbsp;2.31', 'Downloading from the Dryad API over HTTPS'],
        [M('numpy'), '&#8805;&nbsp;1.26', 'Numerical arrays &#8212; the foundation'],
        [M('pandas'), '&#8805;&nbsp;2.0', 'Named-column tables'],
        [M('scipy'), '&#8805;&nbsp;1.11', 'Scientific computing; ' + M('.mat') + ' reading; the '
         'statistical tests'],
        [M('h5py'), '&#8805;&nbsp;3.10', 'MATLAB v7.3 files, which are HDF5 underneath'],
        [M('matplotlib'), '&#8805;&nbsp;3.8', 'Figures'],
    ], [0.16, 0.14, 0.70], fs=8.3)
    s += NOTE('Python 3.11.15. The reproducibility gate confirms all six third-party imports are '
              'declared. ' + B('Audit finding:') + ' the pins are lower bounds (' + M('&gt;=') +
              '), not exact versions, and the project&#8217;s own audit report says so &#8212; '
              '&#8220;it does not check that ' + M('requirements.txt') + ' pins versions, only '
              'that the packages are named.&#8221; A ' + M('pip freeze') + ' lockfile would close '
              'this. See roadmap item&nbsp;R6.')

    s += H2('6.3 The detector contract &#8212; the design decision that prevents leakage')
    s += CALLOUT(
        'A detector sees ' + B('only the feature stream') + ': channels &#215; binned activity. '
        'It never sees the decoder&#8217;s output, the task, the performance number, or any fault '
        'label. It is fitted on ' + B('healthy windows alone') + ' &#8212; one-class. '
        'Three baselines are held to exactly the same standard.',
        tone='neutral', label='scripts/19_detectors.py')
    s += P('This is not a stylistic choice. A supervised failure-predictor trained on labelled '
           'degradation invites exactly the leakage that would make a positive result worthless: '
           'the model learns the label, not the phenomenon. One-class fitting on healthy data is '
           'what makes the AUCs in Section&nbsp;9 mean something. It is also what makes them low.')

    s += H2('6.4 ' + M('decoder-guard') + ' &#8212; how the monitor is built')
    s += P('Four named components, each calibrated against healthy data, with the largest reported '
           'as the risk score ' + B('and its cause named') + '. The system works in log space, so '
           'a uniform gain change becomes an additive shift and can be separated from a change in '
           'the shape across channels.')
    s += TBL(['Component', 'What it measures', 'Intended fault signature'], [
        [M('level'), 'Overall activity relative to the healthy reference', M('RATE_LOSS')],
        [M('silence'), 'Channels that have gone quiet', M('CHANNEL_DROPOUT')],
        [M('dispersion'), 'Channels spreading apart with the total conserved', M('GAIN_DRIFT')],
        [M('profile'), 'Residual shape across channels after the above', M('GEOMETRY_ROTATION') +
         ' &#8212; ' + B('this mapping was withdrawn, see W04')],
    ], [0.14, 0.46, 0.40], fs=8.3)
    s += P('Interpretability is a stated requirement rather than a bonus: every risk score '
           'decomposes into named, unit-carrying contributions, so &#8220;why is it warning?&#8221; '
           'has a sentence-shaped answer. The output is a risk score (0&#8211;1), a warning state '
           '(NOMINAL / WATCH / WARN / FAIL-LIKELY) with hysteresis and dwell so it cannot chatter, '
           'an attribution, and a confidence &#8212; where low confidence is ' + B('reported, not '
           'hidden') + '.')

    s += H2('6.5 Code-quality findings')
    s += TBL(['Finding', 'Severity', 'Detail'], [
        ['Numbering does not equal execution order', B('Documented, resolved'),
         'Discovered by the project&#8217;s own audit. Renumbering would break the script names '
         'quoted throughout 53 documents, so the README now states the truth: two scripts run '
         'last.'],
        ['Two files the static audit cannot resolve', B('Documented, hand-verified'),
         M('reference_decoder.npz') + ' and ' + M('.json') + ' are written through a ' +
         M('decoder_paths()') + ' helper that <i>returns</i> the path, so the filename literal '
         'never appears near the write. Both are named in a two-item ' + M('RESOLVED_BY_HAND') +
         ' allowlist. ' + B('Anything not on that list is a real finding.')],
        ['Eight deliberate statistical-pattern sites', B('Documented, reviewed'),
         'Six pooled-inference sites and two inverse-variance sites are kept on purpose &#8212; '
         'the pooled ones so the register can record what claim C02&#8217;s window-level number '
         'is, and the inverse-variance ones because Cochran&#8217;s Q requires them and they are '
         'already labelled ' + M('..._BIASED_DO_NOT_QUOTE') + '. Each is listed in a ' +
         M('REVIEWED') + ' dictionary with its reason.'],
        ['No unit tests', B('Real gap'),
         B('Audit judgement.') + ' There is no test suite. Correctness is enforced by five '
         'output-level gates, by synthetic controls with known answers, and by the '
         'reproduce-a-published-result check &#8212; which is a stronger scientific defence than '
         'unit tests would be, but does not catch a silently wrong intermediate function. Errors '
         '#1 and #3 in Section&nbsp;3.3 are exactly what a unit test would have caught.'],
        ['No CI', B('Minor'),
         'The gates are run by hand before each commit. A stop hook caught one instance of them '
         'being run in the wrong order (error #13).'],
    ], [0.22, 0.13, 0.65], fs=8.0)
    return s


def section_7():
    s = H1('7. Analysis and statistics audit', 'Section 7')
    s += P('This is the section where a research project usually breaks. It is examined against '
           'the specific failure modes that make published results wrong: unit-of-analysis errors, '
           'multiplicity, post-hoc selection, biased estimators, and inference on non-independent '
           'observations.')

    s += H2('7.1 Statistical methods used, and where')
    s += TBL(['Method', 'Where', 'Audit note'], [
        ['Kendall&#8217;s &#964;', 'The preregistered Phase 1&#8211;2 trend test',
         'Rank-based &#8212; appropriate for a short, non-normal series'],
        ['Permutation test (5,000)', 'The change-point locating deterioration',
         'The boundary at day 758, p&nbsp;=&nbsp;0.0018, agreed by three methods and two variables'],
        ['Permutation on ' + B('day labels'), 'The staleness test',
         B('The important one.') + ' A naive test said p&nbsp;=&nbsp;0.003; permuting day labels '
         'gives ' + B('0.128') + '. The naive test was measuring day-to-day variation, not '
         'staleness.'],
        ['Mann&#8211;Whitney U / AUC', 'Every detection headline',
         'Point estimates survive pooling; ' + B('p-values do not') + ' &#8212; see 7.2'],
        ['Bootstrap over ' + B('episodes'), 'All corrected confidence intervals',
         'Episodes, not windows. 2,000 resamples, so the floor is p&nbsp;=&nbsp;0.0010 and it is ' +
         B('reported as a floor') + ', not as zero'],
        ['Spearman &#961; and partial &#961;', 'The day-predictor studies',
         'Bonferroni-corrected at 0.01 for five preregistered predictors'],
        ['Cochran&#8217;s Q and I&#178;', 'Day-to-day heterogeneity',
         'I&#178;&nbsp;=&nbsp;0.856 &#8212; only about a quarter of the day-to-day AUC spread is '
         'sampling noise'],
        ['Sign test', 'Combining the window-overlap result across arrays',
         '11 of 13 days improve; p&nbsp;=&nbsp;0.011 one-sided'],
        ['Lag-1 autocorrelation and effective n', 'The aggregation limit',
         'The single most consequential number in the project'],
    ], [0.22, 0.30, 0.48], fs=8.0)

    s += H2('7.2 The unit-of-analysis error, in full')
    s += P('This is the project&#8217;s largest statistical failure and its most instructive '
           'correction. It is presented in detail because a judge who understands it will trust '
           'everything else more.')
    s += CALLOUT(
        M('26_achievability.py') + ' pooled every 5-second window from every episode and ran a '
        'Mann&#8211;Whitney test on the result. But claim C04 establishes that windows within a '
        'session are ' + B('not independent') + ' &#8212; lag-1&nbsp;r&nbsp;=&nbsp;0.995. Pooling '
        'them inflates the apparent sample size by a measured ' + B('26.6&#215;') + ' (22,590 '
        'windows against 850 episodes). An AUC point estimate survives that; a p-value does not.',
        tone='warn', label='What went wrong')
    s += TBL(['Participant / baseline / detector', 'AUC (window)', 'AUC (episode)',
              'p published', 'p corrected'], [
        ['T11 &#183; calibrate once &#183; ' + M('decoder_guard'), '0.491', '0.504', '0.0464',
         B('0.8480') + ' <b>(!)</b>'],
        ['T11 &#183; calibrate once &#183; ' + M('distribution_shift'), '0.541', '0.558',
         '6.85e-20', '0.0030'],
        ['T11 &#183; calibrate once &#183; ' + M('mean_activity'), '0.514', '0.527', '0.00138',
         B('0.2170') + ' <b>(!)</b>'],
        ['T11 &#183; calibrate once &#183; ' + M('robust_dispersion'), '0.465', '0.470',
         '3.38e-15', B('0.1440') + ' <b>(!)</b>'],
        ['T11 &#183; recent normal &#183; ' + M('decoder_guard'), '0.693', '0.672', '0', '0.0010'],
        ['T11 &#183; recent normal &#183; ' + M('distribution_shift'), '0.666', '0.646',
         '1.17e-303', '0.0010'],
        ['T11 &#183; recent normal &#183; ' + M('mean_activity'), '0.611', '0.557', '2.03e-137',
         '0.0040'],
        ['T11 &#183; recent normal &#183; ' + M('robust_dispersion'), '0.602', '0.578',
         '8.05e-117', '0.0010'],
        ['T5 &#183; recent normal &#183; ' + M('decoder_guard'), '0.708', '0.742', '0', '0.0010'],
        ['T5 &#183; recent normal &#183; ' + M('distribution_shift'), '0.661', '0.661',
         '7.23e-205', '0.0010'],
        ['T5 &#183; recent normal &#183; ' + M('mean_activity'), '0.612', '0.589', '8.5e-100',
         '0.0010'],
        ['T5 &#183; recent normal &#183; ' + M('robust_dispersion'), '0.620', '0.642', '3.12e-114',
         '0.0010'],
    ], [0.36, 0.15, 0.15, 0.17, 0.17], fs=7.8,
        caption='<b>(!)</b>&nbsp;=&nbsp;significant as published, not significant at the episode '
                'level. Regenerated by ' + M('scripts/60_unit_of_analysis.py') + '. Two rows '
                '(' + M('decoder_guard_joint') + ') omitted here for width; the full table is in ' +
                M('reports/UNIT_OF_ANALYSIS.md') + '.')
    s += UL([
        B('AUC point estimates barely moved:') + ' median shift 0.0202, largest 0.0545. Pooling '
        'affects variance, not location.',
        B('Four statistics were published as exactly &#8220;p&nbsp;=&nbsp;0&#8221;') + ' and ten '
        'below 1e-20. All are ordinary numbers at the episode level.',
        B('Three results significant as published are not significant now.') + ' The starkest: ' +
        M('robust_dispersion') + ' at the calibrate-once baseline was published at '
        'p&nbsp;=&nbsp;3.4e-15 and is actually ' + B('p&nbsp;=&nbsp;0.144') + '. Fifteen orders '
        'of magnitude, from an effect that is not there.',
        B('No conclusion of the project rests on these p-values.') + ' &#8220;0 of 48 '
        'configurations pass the gates&#8221; is a count; the operating-point bound is arithmetic; '
        'the aggregation limit is itself the reason the correction was needed. What changed is '
        'whether the supporting statistics are stated honestly.',
        B('The correction is inline.') + ' ' + M('ACHIEVABILITY.md') + ' carries a <b>(!)</b> '
        'correction block rather than having its numbers silently replaced.',
    ])

    s += H2('7.3 The three error classes, now encoded as a linter')
    s += TBL(['Error class', 'How it was found', 'What it cost', 'Now checked by'], [
        ['Inference on pooled, non-independent units', 'Noticed while decomposing a headline',
         '4 p-values published as 0; 26.6&#215; inflation; 3 false positives',
         M('pooled_inference') + ' &#8212; 0 unreviewed sites, 6 deliberate'],
        ['A comparison that can never be true', 'Noticed because every day reported exactly 0.00',
         'A control that measured nothing looked like a control that passed',
         M('impossible_comparison') + ' &#8212; 0 sites'],
        ['An estimator biased by its own weights', 'Noticed because the number was implausibly good',
         'A pooled AUC inflated 0.675 &#8594; 0.836',
         M('inverse_variance') + ' &#8212; 0 unreviewed, 2 deliberate'],
    ], [0.24, 0.24, 0.26, 0.26], fs=7.9)
    s += P(B('The linter failed its own first test.') + ' Its first version flagged one site and '
           'did ' + B('not') + ' flag ' + M('26_achievability.py') + ' &#8212; the very file it '
           'was written for &#8212; because that file wraps ' + M('mannwhitneyu') + ' in a local ' +
           M('auc(pos, neg)') + ' helper, so the pooled variable never appears in the test&#8217;s '
           'arguments. Fixing it (by detecting local functions that contain a test call) took the '
           'count from 1 site to 9, including all three known-bad lines. ' + B('A linter that '
           'cannot catch the case it was written for is worse than no linter, because it converts '
           '&#8220;unchecked&#8221; into &#8220;checked and clean.&#8221;'))
    s += NOTE(B('Stated limits of the linter, from its own report:') + ' it is static, so it finds '
              'shapes rather than wrong answers; it knows three patterns, which are the three this '
              'project made; and ' + M('impossible_comparison') + ' is a heuristic that would miss '
              'a numeric field never used arithmetically in the same file. &#8220;A fourth error '
              'class will not be caught until it is found some other way &#8212; which is the '
              'honest limit of learning from your own mistakes.&#8221;')

    s += H2('7.4 Multiplicity, and the discipline that governs it')
    s += TBL(['Risk', 'How the project handles it', 'Audit verdict'], [
        ['Trying many deterioration definitions and picking the best',
         'Six definitions compared using ' + B('performance data only') + ', before any indicator '
         'existed; one frozen in advance in ' + M('deterioration_definition.md') + '.',
         B('Handled') + ' &#8212; and this was an explicit standing instruction from the researcher'],
        ['Trying many features until one works',
         'Four families ' + B('named in advance, list closed') + ', criterion frozen at commit ' +
         M('0950c04') + ' with a checksum: +0.05 AUC ' + B('on both participants in the same '
         'direction') + '.',
         B('Handled, and it bit') + ' &#8212; F3 spectral cleared the bar on T11 (0.750) and '
         'failed badly on T5 (0.556). With one participant, or with the rule written afterwards, '
         'it would have been &#8220;the feature that worked.&#8221;'],
        ['Five day-predictors tested at once',
         'Bonferroni threshold set at 0.01; direction of each predictor committed in advance',
         B('Handled') + '. P5 survives at p&nbsp;=&nbsp;0.0055. P4 came out with the ' + B('wrong '
         'sign') + ' (+0.582 against a predicted negative) and is reported as such, claiming nothing'],
        ['48 benchmark configurations',
         'No selection at all &#8212; every configuration is reported, and the headline is a ' +
         B('count') + ' over all of them',
         B('Handled')],
        ['Post-hoc structure in a null result',
         'The F1/F2 finding in the feature study is labelled ' + B('post-hoc') + ' in the report '
         'itself and in the register (status EXPLORATORY)',
         B('Handled by labelling')],
    ], [0.20, 0.42, 0.38], fs=7.9)
    s += CALLOUT(
        'The both-participants rule deserves particular notice. It was written ' + B('before') +
        ' the feature study and it is the reason the study returned a null. A weaker project would '
        'have reported F3 as a success on T11 and mentioned T5 in a limitations paragraph. This '
        'one recorded the criterion first and then obeyed it.',
        tone='good', label='The single strongest piece of statistical discipline here')
    return s


def section_8():
    s = H1('8. Failed approaches and abandoned directions', 'Section 8')
    s += P('These are preserved because they are evidence. A project that shows only what worked '
           'is indistinguishable from a project that tried many things and reported one.')

    s += H2('8.1 Directions abandoned, with the evidence that closed each')
    s += TBL(['Direction', 'Why it was tried', 'What closed it'], [
        [B('Critical slowing down as the mechanism'),
         'The literature&#8217;s standard early-warning theory: rising variance and rising '
         'autocorrelation before a bifurcation',
         B('Closed empirically, not by preference.') + ' No observable in the data has measurable '
         'memory (0.3&#8211;0.7 samples across 20&nbsp;ms&#8211;5&nbsp;s), so the autocorrelation '
         'half ' + B('cannot be tested at all') + '. And the premise is doubtful: the data show a '
         'monotonic 56.5% firing-rate decline into a saturating compensator, which is a ramp, not '
         'a fold bifurcation.'],
        [B('Predicting time-to-recalibration'),
         'Drops the CSD commitment, which is correct',
         'Generic and underpowered: 2 participants, ~40 sessions, high leakage exposure. And it ' +
         B('inherits the same circularity') + ' &#8212; still no ground truth for onset.'],
        [B('Combining many indicators'),
         'Multimodality usually helps',
         'Mean firing rate alone already matched the whole five-dimensional pipeline. Combining '
         'confounded measures does not decontaminate them.'],
        [B('Better decision rules'),
         'After finding the information was present (AUC 0.69&#8211;0.71), the natural conclusion '
         'was that the failure was in the machinery converting scores to warnings',
         B('Refuted by measurement.') + ' Three rules compared by their ' + B('full curve') +
         ', not one operating point: threshold, CUSUM, and CUSUM with a specificity gate. '
         'Detection inside the budget: ' + B('0.0%') + ' for all three on T11.'],
        [B('Longer or more windows'),
         'The obvious way to buy precision',
         'There is no &#8730;N to collect. Effective independent samples per session: ' +
         B('0.1') + ' (T11), 0.4 (T5).'],
        [B('Better session-level aggregators'),
         'If per-window AUC is 0.70 and a session holds 55 windows, aggregation should help',
         'Six tried &#8212; median, mean, 90th percentile, max, top-decile mean, fraction above '
         'own median. ' + B('None beats a plain median') + ', and the tail-leaning ones are near '
         'chance (0.44&#8211;0.47).'],
        [B('Calibrate-once deployment'),
         'The deployment model everyone would want',
         B('Carries literally no information') + ': AUC 0.491 when a monitor calibrated once is '
         'applied months later. That is a bound, not a shortfall of effort.'],
        [B('Abstention (&#8220;the monitor says when not to trust it&#8221;)'),
         'A natural response to the finding that accuracy varies enormously by session',
         'Four label-free candidates, two stages. ' + B('Nothing passes stage 2.') + ' Abstention '
         'is an untested proposal, not a capability.'],
        [B('EMG, EEG, consumer neuro-headsets, camera-tracked hand movement'),
         'Original data collection with a human in the loop',
         B('Ruled out by Amendment 1') + ' (26 Aug 2026): no human participants, and data '
         'collected from oneself still counts as human-participant research.'],
    ], [0.20, 0.30, 0.50], fs=7.9)

    s += H2('8.2 The five withdrawn claims')
    s += P('Each of these was asserted, then retracted on evidence. The register marks them ' +
           B('WITHDRAWN &#8212; do not quote') + ', and they remain in the repository.')
    s += TBL(['ID', 'What was claimed', 'What refuted it'], [
        ['W01', 'The monitor fails because the decoder has lost its signal',
         'Margin over a session&#8217;s ' + B('own') + ' chance level does not predict monitor '
         'accuracy (+0.264, p&nbsp;=&nbsp;0.38). Days 800 and 783 beat their own chance by '
         'near-identical margins with accuracies of ' + B('0.974 and 0.319') + '.'],
        ['W02', 'A specific session property causes the accuracy swing',
         'Trace noise predicts identically (&#8722;0.720) and correlates with decoder error at '
         '0.813; the partials are identical in both directions (&#8722;0.333). ' +
         B('Identical partials both ways is collinearity, not mediation.')],
        ['W03', 'Weaker faults on bad sessions explain the swing',
         'Achieved damage barely relates to monitor accuracy (+0.181, p&nbsp;=&nbsp;0.55). '
         'This confound was ' + B('predicted to hold') + ' and did not.'],
        ['W04', 'The preregistered mapping ' + M('GEOMETRY_ROTATION') + ' &#8594; ' + M('profile'),
         'Rotation is injected with ' + B('norm-preserving') + ' Givens rotations, and ' +
         M('dispersion') + ' is defined as channels spreading apart with the total conserved '
         '&#8212; the same signature ' + B('by definition') + '. The mapping was wrong from the '
         'start; re-ordering the rule cannot fix it.'],
        ['W05', 'Dropout, gain drift and rate loss face an information ceiling',
         B('That was the linear model&#8217;s limit, not the features&#8217;.') + ' With '
         'permutation-invariant summaries the confusable trio rises from 0.650 to ' + B('0.987') +
         ' on T11 and 0.623 to ' + B('0.998') + ' on T5. A 12-random-channel control reaches only '
         '0.702, so the gain is representation, not dimension count.'],
    ], [0.05, 0.31, 0.64], fs=7.9)

    s += H2('8.3 Predictions recorded in advance, and how they turned out')
    s += P('Six predictions were committed to the repository before the analysis that would test '
           'them. This is the sharpest available evidence that results were not reverse-engineered.')
    s += TBL(['Prediction', 'Recorded at', 'Outcome'], [
        ['Detector v2 will improve on the benchmark', M('4cf5f57') + ', while the results files '
         'were untouched',
         B('Split') + ' &#8212; satisfied on T11, falsified on T5. ' + B('The change was not '
         'adopted.')],
        ['The day effect will be shared by all four detectors', M('63d6d9a'),
         B('Wrong.') + ' It belongs to distribution-based detectors and is absent from scalar '
         'ones &#8212; a better answer than either option offered.'],
        ['The achievable-damage ceiling confounds P5', M('f86f73e'),
         B('Wrong') + ' (W03). The confound does not hold; P5 ' + B('strengthens') + ' when '
         'controlled for damage (&#8722;0.794).'],
        ['Removing ' + M('GEOMETRY_ROTATION') + ' will drop the headline to 0.60&#8211;0.65',
         M('660620a'),
         B('Wrong on both counts.') + ' It moves by 0.037 (T11) and 0.002 (T5).'],
        ['A one-class detector on invariant features will detect better', M('f8e27d2'),
         B('Wrong.') + ' Worse on both axes: AUC 0.617/0.680 against 0.672/0.742, and 98.5% of '
         'healthy episodes trending against a 31% best.'],
        ['Label-free invariant attribution will beat the current rule', M('3f658dd'),
         B('Wrong.') + ' 51.1%/39.7% against 56.3%/52.5%; rotation at 2.1% against 25% chance.'],
    ], [0.32, 0.20, 0.48], fs=7.9)
    s += CALLOUT(
        B('Five of six preregistered predictions were wrong.') + ' That is not a weakness of the '
        'project &#8212; it is the strongest single piece of evidence that the predictions were '
        'genuinely made in advance. A researcher who writes predictions after seeing results does '
        'not record a 1-in-6 hit rate.',
        tone='good', label='Read this line carefully')

    s += H2('8.4 One approach that failed and is preserved as a bound')
    s += P('The invariant-features line is worth separating out, because it is the clearest '
           'example of a result that is genuinely informative ' + B('and') + ' genuinely negative.')
    s += OL([
        B('A supervised probe showed the information is there.') + ' Permutation-invariant '
        'distributional summaries separate all four fault modes near-perfectly (the confusable '
        'trio at 0.987 on T11, 0.998 on T5). That withdrew W05 and looked like a clear route '
        'forward.',
        B('Building the detector that recommendation implied made things worse.') + ' The '
        'one-class invariant detector scored 0.617/0.680 against the guard&#8217;s 0.672/0.742, '
        'and 98.5% of healthy episodes trended &#8212; against a 31% best elsewhere. The trend '
        'survives unclipping, so it is not a scoring artefact.',
        B('The other half of the recommendation failed too.') + ' Label-free attribution on the '
        'same features: 51.1%/39.7% against 56.3%/52.5%, with rotation named correctly ' +
        B('2.1%') + ' of the time against 25% chance.',
        B('The diagnosis is specific.') + ' ' + M('sd') + ' is a generic spread measure that every '
        'fault elevates, so it swamps the specific features &#8212; which is the ' + M('profile') +
        ' residual problem again, in new clothes. The preregistration for that study explicitly '
        'declined a specificity ordering, on reasoning the result showed to be wrong.',
    ])
    s += CALLOUT(
        'The general lesson, and it is a real methodological finding: ' + B('a supervised '
        'demonstration that information exists has now twice failed to translate into a '
        'label-free rule that uses it.') + ' An upper bound computed with labels is not a design '
        'for a monitor that never sees them. Claim E04 was ' + B('narrowed in place') + ' to say '
        'so, with a <b>(!)</b> marker, rather than being quietly deleted.',
        tone='flag', label='Why this failure is worth more than the success would have been')
    return s
