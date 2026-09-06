# -*- coding: utf-8 -*-
"""Sections 9-12."""
from kit import *


def section_9():
    s = H1('9. Results, reconstructed from the data', 'Section 9')
    s += P('Every number in this section was regenerated during the audit by running '
           + M('scripts/31_verify_claims.py') + ', which recomputes each headline from the stored '
           'data files rather than reading it from a report. All 93 checks matched.')

    s += H2('9.1 Phase 1&#8211;2: the preregistered negative result')
    s += TBL(['Test', 'n', '&#964;', 'p', 'Verdict'], [
        ['Primary &#8212; robust dispersion, pre-transition', '21', '+0.743', '0.0002',
         'Significant'],
        ['Parallel &#8212; trial-to-trial dispersion', '21', '&#8722;0.419', '0.0068',
         'Significant, ' + B('opposite sign')],
        ['Sensitivity &#8212; session level', '11', '+0.745', '0.0012', 'Significant'],
        [B('Limitation check &#8212; healthy baseline only'), '&#8212;', B('+0.857'), '0.0018',
         B('This is what overturns it')],
    ], [0.44, 0.08, 0.13, 0.13, 0.22], fs=8.2,
        caption='The indicator rose <i>more steeply during healthy performance</i> '
                '(&#964;&nbsp;=&nbsp;+0.857) than it did overall (+0.743). The limitation check '
                'was written into the frozen design in advance. Figure: '
                + M('reports/figures/11_t11_why_negative.png') + '.')
    s += H3('What the indicator was actually measuring &#8212; three converging lines')
    s += UL([
        B('Firing rate.') + ' Mean firing rate falls ' + B('56.5%') + ' across T11&#8217;s '
        '142-day record. A linear fit of the indicator on it gives ' + B('R&#178;&nbsp;=&nbsp;0.707') +
        '. Controlling for firing rate, the indicator&#8217;s link to performance goes '
        'non-significant (&#961; 0.858 &#8594; 0.260, p&nbsp;=&nbsp;0.17). Controlling for elapsed '
        'time, essentially nothing remains. And mean firing rate alone predicts performance '
        '(&#961;&nbsp;=&nbsp;&#8722;0.880) ' + B('as well as the full pipeline does') + '.',
        B('Task invariance.') + ' On extra T11 sessions using completely different tasks '
        '&#8212; including free web browsing &#8212; the indicator differs from the same-day '
        'cursor value by only ' + B('5.9&#8211;8.4%') + ', against a threefold range across the '
        'record. It measures ' + B('the recording') + ', not the human&#8211;decoder system.',
        B('Participant disagreement.') + ' In T5 the indicator ' + B('falls') + ' during '
        'degradation, so its reversibility test passes vacuously. No cross-participant generality '
        'was demonstrated.',
    ])
    s += CALLOUT(
        'The design flaw, stated plainly in the project&#8217;s own report: the frozen design ' +
        B('did not require the block-level series to be de-trended before testing it for a '
        'trend') + '. The synthetic controls had already established that de-trending is '
        'necessary &#8212; that is precisely why the detector correctly stayed silent on '
        'monotonic drift in simulation. Its omission is why recording drift produced '
        'p&nbsp;=&nbsp;0.0002. ' + B('This was not corrected retrospectively.') + ' Doing so '
        'after seeing the outcome would have destroyed the preregistration. It defined Phase&nbsp;3 '
        'instead.',
        tone='flag', label='The most important sentence in the Phase 1–2 report')

    s += H2('9.2 Phase 3: the benchmark')
    s += TBL(['Of 48 configurations', 'Count', 'Share'], [
        ['Ran', '48', '&#8212;'],
        ['Found any operating point at all', '47', '98%'],
        ['Achieved a ' + B('positive') + ' median lead time', '10', '21%'],
        ['Met the false-alarm budget (&#8804;&nbsp;0.1/h)', '3', '6%'],
        [B('Passed the silence gate') + ' (&#8804;&nbsp;10% of healthy episodes trend)',
         B('0'), B('0%')],
        [B('Passed all five gates'), B('0'), B('0%')],
    ], [0.62, 0.19, 0.19], fs=8.4,
        caption='The grid is 4 detectors &#215; 4 transforms &#215; 2 baseline strategies on '
                'T11 (32 configurations) plus 4 detectors &#215; 4 transforms &#215; 1 baseline '
                'on T5 (16), for 48 in total &#8212; T5 was never run with the calibrate-once '
                'baseline. Full table in ' + M('reports/BENCHMARK_SUMMARY.md') + '.')
    s += CALLOUT(
        B('The binding constraint is not detection &#8212; it is specificity.') + ' Several '
        'configurations do warn before performance falls. But the risk signal is never quiet '
        'during healthy operation, so any threshold low enough to catch a fault early also fires '
        'constantly on healthy record. On the best T11 configuration the operating point is 50.46, '
        'giving ' + B('3.41 false alarms per hour against a 0.1/h budget') + ' &#8212; missed by '
        '34&#215;.',
        tone='warn', label='Why nothing passes')

    s += H2('9.3 But the information is present')
    s += TBL(['Condition', M('decoder_guard') + ' AUC', 'Reading'], [
        ['Calibrated once, applied months later', B('0.491'),
         B('Chance.') + ' Calibrate-once carries literally no information. This is a bound, not a '
         'shortfall of effort.'],
        ['Re-baselined on recent healthy data, T11', B('0.693') + ' (window) / 0.672 (episode)',
         'Real information'],
        ['Re-baselined on recent healthy data, T5', B('0.707') + ' (window) / 0.742 (episode)',
         'Real information, replicated'],
    ], [0.36, 0.24, 0.40], fs=8.3)

    s += H2('9.4 The monitor beats the trivial comparator, and exactly where it was designed to')
    s += P('Phase 1&#8211;2 found that counting activity matched a five-dimensional pipeline. '
           'This is therefore the comparison that decides whether any of the engineering was '
           'worth doing.')
    s += TBL(['Fault mode', M('decoder-guard') + ' (T11 / T5)', 'Counting activity (T11 / T5)',
              'Verdict'], [
        ['Overall signal loss', '0.61 / 0.64', B('0.80 / 0.78'),
         'Counting wins &#8212; ' + B('correct') + ', this fault <i>is</i> nothing but overall '
         'activity'],
        ['Electrodes dying', '0.65 / 0.75', B('0.73 / 0.77'), 'Counting wins narrowly'],
        [B('Channels drifting apart'), B('0.79 / 0.73'), '0.41 / 0.40',
         'Counting is ' + B('at or below chance') + ' &#8212; as constructed'],
        [B('Signal shape rotating'), B('0.76 / 0.71'), '0.52 / 0.51',
         'Counting is at chance &#8212; as constructed'],
    ], [0.22, 0.22, 0.22, 0.34], fs=8.2,
        caption='Counting activity is at or below chance on both faults that conserve total '
                'activity, while the monitor reaches 0.71&#8211;0.79. ' + B('The pattern '
                'replicates on both participants') + ', who disagreed in Phase 1&#8211;2.')

    s += H2('9.5 The clean positive: task changes are not mistaken for faults')
    s += P('The dataset contains days on which the same participant used the cursor task '
           '<i>and</i> did something entirely different &#8212; including free web browsing '
           '&#8212; through the same electrodes, with nothing wrong.')
    s += TBL(['Day 658', 'Same task', 'Different task', 'Real fault', 'Separation'], [
        [B('decoder-guard'), '11.16', B('8.67'), '135.35', B('15.6&#215;')],
        ['Robust dispersion (the Phase 1&#8211;2 indicator)', '0.14', B('0.46'), '0.29',
         B('Would false-alarm')],
    ], [0.34, 0.15, 0.17, 0.15, 0.19], fs=8.3,
        caption='Day 665 gives 70&#215; separation. Robust dispersion fails in the worst possible '
                'direction &#8212; a <i>healthy task change</i> scored higher than a <i>real '
                'fault</i>. A monitor that alarms when someone switches application trains its '
                'user to ignore it. ' + B('Limitation, stated in the report:') + ' this rests on '
                'two days and four blocks. It is a demonstration, not an estimate, and no '
                'confidence interval is quoted because none would be meaningful.')

    s += H2('9.6 Why nothing can pass: the arithmetic, then the cause')
    s += H3('The arithmetic of the operating point')
    s += TBL(['', 'T11', 'T5'], [
        ['Healthy windows in the test split', '17,014', '17,337'],
        ['Healthy hours', '23.6', '24.1'],
        ['Alarms the 0.1/h budget permits', '2.4', '2.4'],
        [B('Required per-window false-positive rate'), B('1.4e-04'), B('1.4e-04')],
        ['Observed per-window AUC', '0.693', '0.707'],
        [B('Detection achievable at that operating point'), B('0.18%'), B('0.03%')],
        [B('AUC needed for 80% detection there'), B('0.9992'), B('0.9992')],
    ], [0.56, 0.22, 0.22], fs=8.4)
    s += P('An AUC of 0.999 is not a detector that needs tuning &#8212; it is a different '
           'measurement problem. The budget as applied demands near-perfect discrimination on '
           'every one of ' + B('720 decisions an hour') + '.')
    s += H3('The mis-specification, and what it does and does not license')
    s += CALLOUT(
        '0.1 false alarms per hour was set as a usability requirement, and as a requirement on an ' +
        B('alarm') + ' it is sensible. The error was applying it to a system that re-decides every '
        '5 seconds, which quietly converts a mild usability constraint into a demand for 0.9992 '
        'AUC. A deployed monitor need not re-decide every 5 seconds: &#8220;should this session be '
        'flagged for a recalibration check?&#8221; is a ' + B('once-per-session') + ' question. '
        + B('What this does not license:') + ' relaxing a target after failing to meet it is the '
        'classic way to manufacture a success. The argument is <i>not</i> that 0.1/h was too '
        'strict &#8212; the per-hour figure is unchanged. It is that a per-hour alarm budget and a '
        'per-5-second decision rate are different quantities, and the design conflated them. ' +
        B('The honest headline stays: at the operating point the design specified, no '
        'configuration works.'),
        tone='flag', label='A correction that had to be made carefully')
    s += TBL(['The same detector, judged once per session', 'T11', 'T5'], [
        ['Session-level AUC', '0.673', '0.742'],
        ['Detection at a 10% false-flag rate', '14.4%', '30.4%'],
        ['Detection at a 5% false-flag rate', '8.5%', '17.0%'],
        [B('AUC needed for 80% detection at 10%'), B('0.933'), B('0.933')],
    ], [0.56, 0.22, 0.22], fs=8.4,
        caption='Aggregating to session level helps one participant and hurts the other '
                '(T5 0.707&#8594;0.742; T11 0.693&#8594;0.673), so it is ' + B('not') + ' the '
                'rescue either &#8212; the participant disagreement shows up here too. But it '
                'moves the problem from impossible to merely hard: a specific gap of 0.67&#8211;0.74 '
                'achieved against ~0.93 required.')

    s += H3('The cause: a session is one measurement, taken 55 times')
    s += TBL(['', 'T11', 'T5'], [
        ['Windows per session', '55', '42'],
        [B('Lag-1 autocorrelation of the risk signal'), B('0.995'), B('0.980')],
        [B('Effective independent samples per session'), B('0.1'), B('0.4')],
    ], [0.56, 0.22, 0.22], fs=8.5)
    s += P('This single fact explains every negative result in the project:')
    s += UL([
        B('CUSUM cannot help') + ' &#8212; accumulating 55 copies of one measurement adds nothing.',
        B('Longer or more windows cannot help') + ' &#8212; there is no &#8730;N to collect.',
        B('The silence gate always fails') + ' &#8212; a series with r&nbsp;=&nbsp;0.995 '
        '<i>is</i> a trend, so testing it for one will nearly always find one.',
        B('Six aggregators change nothing') + ' &#8212; none beats a plain median; the tail-leaning '
        'ones sit near chance.',
    ])

    s += H2('9.7 The day effect: the finding nobody was looking for')
    s += TBL(['Result', 'Value', 'Status'], [
        ['Monitor accuracy varies by session on T11', '0.319 to ' + B('0.974'), 'ESTABLISHED (C08)'],
        ['Share of that spread that is sampling noise', '25.5% (I&#178;&nbsp;=&nbsp;0.856)',
         'ESTABLISHED'],
        ['Session accuracy vs that session&#8217;s absolute decoder error',
         '&#961;&nbsp;=&nbsp;' + B('&#8722;0.720') + ', p&nbsp;=&nbsp;0.0055',
         'ESTABLISHED (C09) &#8212; ' + B('preregistered, direction committed in advance')],
        ['Controlling for early-warning window length', '&#8722;0.773', 'Strengthens'],
        ['Controlling for achieved fault damage', '&#8722;0.794', 'Strengthens'],
        ['Controlling for trace noise', '&#8722;0.333', B('Collapses') + ' &#8212; this is W02'],
        ['A monitor&#8217;s fit going stale over 142 days',
         'Permutation p&nbsp;=&nbsp;' + B('0.128') + ' (naive test said 0.003)',
         'ESTABLISHED (C07) &#8212; ' + B('no measurable staleness')],
        ['Cost of pooling episodes across sessions', '0.003 AUC',
         'ESTABLISHED (C13) &#8212; pooling is not diluting anything'],
        ['The pattern is shared by distribution-based detectors, absent from scalar ones',
         'guard vs ' + M('distribution_shift') + ': 0.835; vs ' + M('mean_activity') +
         ': &#8722;0.060',
         'ESTABLISHED (C10) &#8212; it belongs to a ' + B('class') + ' of monitor'],
    ], [0.34, 0.28, 0.38], fs=7.9)
    s += CALLOUT(
        B('Ageing does not matter; which day you use the monitor on decides everything.') + ' That '
        'is a deployment-relevant finding, and it inverts the intuition the project started with. '
        'But it also carries its own retraction: ' + B('which property') + ' of a session causes '
        'the swing is ' + B('withdrawn') + ' (W02). Trace noise, decoder error, spurious crossings, '
        'task geometry and margin over chance are all mutually correlated, and the partials are '
        'identical in both directions &#8212; which is collinearity, not mediation. And whether '
        'the effect is failed <i>detection</i> or degraded <i>labels</i> is formally ' +
        B('UNANSWERABLE') + ' with this corpus (U01): filtering to unambiguous faults leaves 7 '
        'sessions, where |&#961;| must reach ~0.79 to clear p&nbsp;&lt;&nbsp;0.05.',
        tone='neutral', label='What the day effect does and does not establish')

    s += H2('9.8 Calibration efficiency &#8212; the first clean, non-null positive')
    s += TBL(['Calibration data', 'T11 AUC', 'T5 AUC', 'Note'], [
        ['10 windows (scattered)', '&#8212;', '&#8212;',
         B('Not a measurement.') + ' The profile covariance is ' + B('singular') + ' below '
         'n&nbsp;=&nbsp;K+1 (minimum eigenvalue 0.000). It is also the highest T11 AUC, and would '
         'have supported a false headline that <i>more</i> calibration data makes the monitor '
         'worse (L04).'],
        ['20 windows (scattered)', '0.653', '0.740', 'Minimum eigenvalue 0.057 &#8212; well posed'],
        ['20 windows (contiguous)', '0.665', '&#8212;', 'Contiguous draw confirms the count '
         'translates into real minutes'],
        ['40 windows (contiguous)', '&#8212;', '0.740', ''],
        [B('The entire healthy record'), B('0.648'), B('0.739'),
         B('About two minutes of healthy recording reaches what the whole record reaches, on '
         'both participants')],
    ], [0.22, 0.13, 0.13, 0.52], fs=8.0)
    s += NOTE(B('Why L04 matters more than C06.') + ' The n&nbsp;=&nbsp;10 point is the most '
              'attractive number in the table and it is not a measurement at all. A project that '
              'reported it would have published a striking, memorable, and entirely spurious '
              'finding. It was caught by checking the conditioning of the covariance matrix rather '
              'than by looking at the AUC.')

    s += H2('9.9 Attribution: a capability that was built, scored, and nearly thrown away')
    s += TBL(['Result', 'T11', 'T5', 'Chance'], [
        ['Overall attribution accuracy', '56.3%', '52.5%', '25% / 33%'],
        [M('GAIN_DRIFT') + ' named correctly', B('99.3%'), '&#8212;', ''],
        [M('GEOMETRY_ROTATION') + ' named correctly', B('0.0%'), B('0.0%'), ''],
    ], [0.40, 0.20, 0.20, 0.20], fs=8.3)
    s += P('The rotation failure is fully diagnosed and the diagnosis retracts the '
           'preregistration. During rotation episodes ' + M('profile') + ' <i>is</i> lit &#8212; '
           'in 80% of them &#8212; but ' + M('dispersion') + ' sits at z&nbsp;=&nbsp;16.5 against ' +
           M('profile') + '&#8217;s 1.92, so a largest-wins rule picks ' + M('dispersion') +
           ' 98% of the time. The cause is definitional: rotation is injected with ' +
           B('norm-preserving') + ' Givens rotations, and ' + M('dispersion') + ' is defined as '
           'channels spreading apart with the total conserved. ' + B('They are the same signature '
           'by definition.') + ' Re-ordering or re-weighting the rule cannot fix it; the '
           'components would have to be redefined.')
    s += NOTE('The register note on C14 is worth quoting: attribution was '
              '&#8220;implemented and scored since the guard was written, printed to stdout and ' +
              B('captured nowhere') + ' until now.&#8221; A real capability existed for a week '
              'without being a result, because nothing wrote it to a file.')

    s += H2('9.10 What the project ruled out, and what remains')
    s += TBL(['Ruled out on evidence', 'The evidence'], [
        ['Better decision rules', 'Three compared by full curve; all 0% inside the budget'],
        ['Longer or more windows', 'Effective n&nbsp;=&nbsp;0.1 &#8212; no independent information '
         'to average'],
        ['Better session-level aggregators', 'Six tried; none beats a median'],
        ['Calibrate-once deployment', 'AUC 0.491 &#8212; literally no information'],
        ['Better features alone', 'F1 and F2 <i>are</i> better features under a matched control '
         '(+0.106/+0.158 and +0.059/+0.095) and it still is not enough: ' + M('decoder_guard') +
         ' beats its own features under that scorer by +0.102/+0.233, so its advantage is ' +
         B('the four-component decomposition') + ', not the per-channel means it consumes'],
        ['A sharper one-class detector on invariant features',
         'Built and measured: worse on both axes (C16)'],
        ['Label-free invariant attribution', 'Built and measured: worse (C17)'],
        ['Abstention', 'Four candidates, two stages, nothing passes stage 2 (C11)'],
    ], [0.30, 0.70], fs=8.0)
    s += P(B('What remains as the only untried direction:') + ' a fundamentally better '
           '<i>measurement</i>, combining better features ' + B('with') + ' the four-component '
           'decomposition rather than substituting for it &#8212; which is a new study needing '
           'its own preregistration, not a change to make on the strength of a post-hoc table. '
           'And, ahead of that in value, ' + B('a third participant') + '.')
    return s


def section_10():
    s = H1('10. Reproducibility audit', 'Section 10')
    s += P('Reproducibility here is not a claim; it is a gate that runs. This section reports '
           'what that gate covers, what it caught, and what it provably cannot see.')

    s += H2('10.1 What the gate checks, and its state on re-run')
    s += TBL(['Check', 'Rule', 'State at audit'], [
        ['Imports', 'Every third-party module imported anywhere appears in ' +
         M('requirements.txt'), B('PASS') + ' &#8212; 6 imports, all declared'],
        ['Producers', 'Every ' + M('data/processed') + ' file a script <i>reads</i> is '
         '<i>written</i> by some script', B('PASS') + ' &#8212; 35 consumed files, all with a '
         'producer'],
        ['Order', 'No script reads a file produced by a higher-numbered script',
         B('PASS') + ' &#8212; no inversions, with two scripts documented as running last'],
        ['References', 'Every script named in a report or the README exists',
         B('PASS') + ' &#8212; 70 documents scanned at the time of this audit. '
         + B('Minor finding:') + ' the checked-in ' + M('REPRODUCIBILITY_AUDIT.md') + ' still says '
         '53, the count when it was last written by hand around the generated output'],
    ], [0.14, 0.50, 0.36], fs=8.2)

    s += H2('10.2 What the gate caught on its first run')
    s += CALLOUT(
        B('A headline figure that no committed script produced.') + ' The combined sign test in '
        + M('reports/WINDOW_OVERLAP.md') + ' &#8212; 11 of 13 days improved, p&nbsp;=&nbsp;0.011 '
        '&#8212; was computed in an ad-hoc shell one-liner, and ' + M('31_verify_claims.py') +
        ' was checking a JSON file that ' + B('nothing in the repository regenerated') + '. A '
        'fresh clone would have failed that claim. ' + B('This is precisely the failure the audit '
        'exists to catch: a verified claim resting on an unreproducible file looks exactly like a '
        'verified claim.') + ' The test now lives in ' + M('54_window_overlap.py') + ' and '
        'produces the same numbers.',
        tone='warn', label='Finding 1')
    s += CALLOUT(
        B('The README&#8217;s &#8220;numbered in dependency order&#8221; claim was false.') + ' '
        + M('31_verify_claims.py') + ' reads output from fifteen higher-numbered scripts, because '
        'it recomputes every headline from whatever the pipeline produced. Renumbering would break '
        'the script names quoted throughout the reports, so the README now states what is true: ' +
        B('two scripts run last') + ', the verifier and this audit.',
        tone='flag', label='Finding 2')

    s += H2('10.3 The audit&#8217;s own three bugs')
    s += P('Documented in the tool&#8217;s own report, because a tool that reports its own '
           'artefacts as findings is worse than no tool. Its first run reported 27 problems, of '
           'which ' + B('1') + ' was real.')
    s += TBL(['Bug', 'Symptom', 'Fix'], [
        ['f-strings parsed by regex', M('f"calibration_curve{sfx}.csv"') + ' was captured as the '
         'filename ' + M('}.csv') + ', reported as an orphan read by ten scripts',
         'Flatten ' + M('ast.JoinedStr') + ' nodes in the AST'],
        ['Filenames held in variables', M('ckpt = OUT / f"staleness{sfx}.csv"') + ' followed '
         'twenty lines later by ' + M('to_csv(ckpt)') + ' looked like a read with no write',
         'Follow one level of assignment &#8212; not full dataflow, but enough'],
        ['The audit as its own producer', 'The phrase ' + M('-> write_text') + ' inside its own '
         'allowlist matched the write-call pattern, making it the recorded producer of the '
         'decoder files', 'Exclude the audit from its own scan'],
    ], [0.20, 0.50, 0.30], fs=8.0)

    s += H2('10.4 The two files a static audit cannot resolve')
    s += P(M('reference_decoder.npz') + ' and ' + M('reference_decoder.json') + ' are written by '
           + M('18_reference_decoder.py') + ' through a ' + M('decoder_paths()') + ' helper that '
           '<i>returns</i> the path, so the filename literal never appears near the ' +
           M('np.savez') + ' / ' + M('write_text') + ' that writes it. Following that needs '
           'interprocedural analysis. Both are named explicitly in a two-item ' +
           M('RESOLVED_BY_HAND') + ' allowlist with their real producer, ' + B('so the check stays '
           'a clean gate rather than a permanently-failing one. Anything not on that two-item list '
           'is a real finding.'))

    s += H2('10.5 Reproducibility in practice: can a stranger run this?')
    s += TBL(['Requirement', 'State', 'Evidence'], [
        ['Clone and run the verifier without the raw data', B('Yes'),
         'All 136 processed files are tracked since commit ' + M('e421166') + '. Before that '
         'commit the verifier ' + B('could not run on a fresh clone') + ' &#8212; the outputs it '
         'checks were gitignored. Verified by actually cloning.'],
        ['See the figures on GitHub', B('Yes'),
         '17 figures tracked since the same commit. Before it, every image link in every report '
         'was broken on GitHub.'],
        ['Re-download the raw data', B('Yes, parameterised'),
         M('01_download_dataset.py') + ' takes a DOI (commit ' + M('227570d') + '), so a third '
         'participant needs credentials, not a rewrite.'],
        ['Reproduce the raw data byte-for-byte', B('Yes, by checksum'),
         'SHA-256 recorded in the manifest and verified at download time.'],
        ['Reproduce the fault corpus exactly', B('Yes'),
         'Master seed, per-episode seeds, and a SHA-256 of the episode list, all in the injection '
         'plan. Re-drawing is ' + B('refused') + ' without a recorded reason.'],
        ['Reproduce the environment exactly', B('Partly') + ' &#8212; ' + B('gap'),
         'Six packages named with ' + M('&gt;=') + ' lower bounds, not exact pins. The audit&#8217;s '
         'own report flags this. See roadmap R6.'],
        ['Know which script produced which number', B('Yes'),
         'Every report carries a ' + B('Reproduce:') + ' line naming its script; every register '
         'entry names its verifier checks.'],
    ], [0.28, 0.16, 0.56], fs=7.9)

    s += H2('10.6 What reproducibility here does not mean')
    s += CALLOUT(
        'Quoted from the project&#8217;s own report, because the audit agrees with it and cannot '
        'improve on it: &#8220;' + B('Static only.') + ' It cannot detect a script that runs and '
        'produces wrong output, only one that cannot run at all for want of an input.&#8221; '
        'The claim verifier has the matching limit: it checks that reported numbers match stored '
        'files, not that the computation behind those files is right. ' + B('Errors #1, #3 and #4 '
        'in Section&nbsp;3.3 all passed every gate') + ' and were caught by a human noticing that '
        'a number looked wrong.',
        tone='warn', label='The honest ceiling on self-checking')
    return s


def section_11():
    s = H1('11. Scientific rigour audit', 'Section 11')
    s += P('This section assesses the project against the practices that separate a result from '
           'an anecdote. It is organised as a scorecard, then the contradictions and open '
           'methodological problems that the scorecard does not capture.')

    s += H2('11.1 Rigour scorecard')
    s += TBL(['Practice', 'Assessment', 'Evidence'], [
        ['Preregistration', B('Exceptional'),
         'Twelve separate frozen designs or preregistration notes. Each names its criterion and, '
         'in six cases, a prediction &#8212; before the analysis. The Phase 1&#8211;2 freeze '
         'carries a git commit hash and SHA-256 of its inputs.'],
        ['Ground truth', B('Exceptional'),
         'Constructed rather than assumed. Onsets drawn and locked under checksum ' +
         B('before any detector existed') + ', with the grading system committed before the monitor.'],
        ['Controls', B('Strong'),
         'Synthetic positive/negative controls with known answers; a measured chance level by '
         'shuffled pairing (not assumed 90&#176;); a calibrate-once arm that correctly lands at '
         '0.491; a 12-random-channel control for the invariant-feature result; NONE episodes '
         'throughout the corpus.'],
        ['Blinding / leakage control', B('Strong'),
         'The detector contract forbids access to decoder output, task, performance and labels. '
         'One-class fitting on healthy data only. Splits by block. ' + B('Test set read once.')],
        ['Replication', B('Adequate, and honestly bounded'),
         'Every headline is reported on both participants. The comparator result replicates. But ' +
         B('n&nbsp;=&nbsp;2 and they disagree') + ' &#8212; the project names this as its binding '
         'limitation rather than burying it.'],
        ['Correction of errors', B('Exceptional'),
         'Fourteen documented errors, three of which changed a conclusion. Corrections appended ' +
         B('inline') + ' rather than replacing the original text. Five claims formally withdrawn.'],
        ['Statistical practice', B('Good, after a serious lapse'),
         'The unit-of-analysis error was real and affected every p-value in one report. It was '
         'found, measured (26.6&#215;), corrected, published as a correction, and then ' +
         B('encoded as a linter') + ' so the class cannot recur silently.'],
        ['Negative results', B('Exceptional'),
         'The project&#8217;s headline ' + B('is') + ' a negative result, reported as such, with '
         'its cause located to three decimal places. Nulls are published in full: the feature '
         'study, the combination study, abstention, the invariant detector, the invariant '
         'attribution.'],
        ['Reasoning recorded', B('Exceptional'),
         'A 4,050-line research log with 54 dated headings, touched by 58 of 123 commits. Commit '
         'messages state what was invalidated, not just what changed.'],
        ['Unit tests', B('Absent') + ' &#8212; gap',
         'No test suite. Correctness rests on output-level gates and synthetic controls. See '
         'Section 6.5.'],
        ['External review', B('Absent') + ' &#8212; gap',
         B('Audit judgement.') + ' Every check in this project was written by the same author as '
         'the work it checks. That is a structural limit no amount of internal discipline removes.'],
    ], [0.19, 0.20, 0.61], fs=7.9)

    s += H2('11.2 Contradictions and tensions found')
    s += P('Flagged as required, including ones the project has already flagged itself.')
    s += TBL(['#', 'Tension', 'Status'], [
        ['1', B('C02&#8217;s headline number is window-level while the project&#8217;s own C04 '
         'says windows are not independent.'),
         B('Resolved by explicit labelling, not by changing the number.') + ' The register entry '
         'for C02 now carries a note: the 0.693 is window-level, the episode-level equivalents are '
         '0.672 and 0.742, and ' + B('no interval or p-value may be built on the window-level '
         'figure') + '. Both numbers are verified separately.'],
        ['2', B('The 0.1/h budget is called both &#8220;the specified operating point&#8221; and '
         '&#8220;mis-specified&#8221;.'),
         B('Genuine tension, handled carefully.') + ' The report keeps the original headline '
         '(&#8220;at the operating point the design specified, no configuration works&#8221;) ' +
         B('and') + ' explains why a per-session decision rate is a different quantity. It '
         'explicitly refuses to treat this as licence to relax the target.'],
        ['3', B('E04 says the attribution failure is &#8220;a design problem, not missing '
         'information&#8221;; C17 says every label-free attempt to use that information is worse.'),
         B('Resolved by narrowing E04 in place') + ', with a <b>(!)</b> marker: it is evidence the '
         'information exists, ' + B('not') + ' a design for a monitor. A supervised upper bound '
         'is not a capability.'],
        ['4', B('T11 and T5 disagree in sign on the strongest cross-participant relationship '
         'in the project.'),
         B('Unresolved, and correctly reported as such.') + ' Claim C12: mean output speed tracks '
         'decoder error on both participants and clears the threshold on both &#8212; with ' +
         B('opposite signs') + ' (+0.681 vs &#8722;0.943). Any rule tuned on one array runs '
         'backwards on the other.'],
        ['5', B('The day effect is established on T11 but T5 cannot corroborate it.'),
         B('Reported, with the reason.') + ' On T5 the session spread tracks the fault mix each '
         'session happened to draw (&#961;&nbsp;=&nbsp;0.886); on T11 it does not (0.050). So T5 '
         'is confounded for this question. ' + B('This was found only because a comparison bug '
         'was fixed') + ' &#8212; error #1.'],
        ['6', B('The severity ladder is used throughout but is only valid 57&#8211;67% of the '
         'time per cell.'),
         B('Documented as L01, not resolved.') + ' Severity is valid in aggregate only, and its '
         'validity degrades with baseline error. Every result stratified by severity inherits this.'],
    ], [0.045, 0.345, 0.61], fs=7.9)

    s += H2('11.3 Methodological problems that remain open')
    s += TBL(['Problem', 'Why it is not closed', 'Consequence for the claims'], [
        [B('n&nbsp;=&nbsp;2 participants, who disagree'),
         'Only two suitable public records were obtained. A third (T15, Card et al. 2024) is '
         'identified and costed but blocked on Dryad credentials.',
         B('The binding limitation.') + ' With n&nbsp;=&nbsp;2 an improvement cannot be '
         'distinguished from noise, and no cross-participant generality is demonstrated.'],
        [B('Open-loop evaluation'),
         'A direct consequence of Amendment 1. An injected episode is a recording and cannot adapt.',
         'Performance is decoder output error against recorded intended direction, not task '
         'success. The compensation gap can be reasoned about but not newly created.'],
        [B('The corpus is blind where it matters most'),
         'On near-chance sessions a fault does almost no measurable damage.',
         B('6 of 13 T11 sessions cannot be scored on unambiguous faults at all') + '. The '
         'sessions where the monitor performs worst are the sessions whose labels are weakest '
         '&#8212; and disentangling those two is formally UNANSWERABLE here (U01).'],
        [B('Injected faults may not resemble real degradation'),
         'Every fault is a mathematical operation on a recorded array. Nobody has checked whether '
         'real hardware degradation resembles ' + M('X * (1 - severity*ramp)') + '.',
         B('The circularity risk the project names itself:') + ' if the monitor only ever meets '
         'degradations the researcher wrote, passing partly measures the researcher&#8217;s '
         'imagination. This is what Section 13 is designed to attack.'],
        [B('Attribution names only 3 of 4 components'),
         M('GEOMETRY_ROTATION') + ' is definitionally confounded with ' + M('dispersion') + '.',
         'Attribution partly collapses onto whatever is chronically lit. Fixing it requires '
         'redefining the components, not re-weighting the rule.'],
        [B('Every check was written by the author of the work'),
         'No external reviewer, no adversarial collaborator.',
         B('Audit judgement:') + ' this is the largest remaining structural risk, and it is not '
         'fixable by writing a sixth gate. It is fixable by a mentor, a teacher, or a judge '
         'reading the code.'],
    ], [0.22, 0.36, 0.42], fs=7.9)

    s += H2('11.4 What a hostile reviewer would attack, and whether it holds')
    s += TBL(['Attack', 'Does it land?'], [
        ['&#8220;You found a correlation and called it a detector.&#8221;',
         B('No.') + ' The project&#8217;s headline is that its detector ' + B('fails') + ' the '
         'gates, and the gates were fixed in advance. There is no correlation being sold as a '
         'capability.'],
        ['&#8220;You defined the event after seeing the data.&#8221;',
         B('No.') + ' Six deterioration definitions were compared using performance data only, one '
         'frozen in advance with input checksums, and the whole circularity problem is the '
         'project&#8217;s stated reason for building a corpus with known onset.'],
        ['&#8220;You tried features until one worked.&#8221;',
         B('No.') + ' Four families named, list closed, criterion frozen with a checksum, and the '
         'one family that <i>did</i> clear the bar on T11 was reported as a ' + B('null') + ' '
         'because it failed on T5.'],
        ['&#8220;Your p-values are wrong.&#8221;',
         B('They were') + ' &#8212; and the project found it, measured it at 26.6&#215;, corrected '
         'it inline, and built a linter. This attack has already been made and answered from '
         'inside.'],
        ['&#8220;Your faults are made up, so your result is about your own imagination.&#8221;',
         B('This one lands') + ', and the project agrees. It is the single strongest motivation '
         'for the physical experiment in Section 13.'],
        ['&#8220;n&nbsp;=&nbsp;2 is not a study.&#8221;',
         B('This one lands.') + ' The project names it as the binding limitation and ranks a '
         'third participant above any detector improvement. It is blocked on credentials, not on '
         'effort.'],
        ['&#8220;An AI wrote this.&#8221;',
         B('Partly, and it is disclosable.') + ' The commits are AI-authored under the '
         'researcher&#8217;s direction. What the researcher must be able to do is explain the '
         'method, the errors, and why each correction was made &#8212; all of which are documented. '
         'Section 12 flags the missing piece: a written AI-use disclosure.'],
    ], [0.34, 0.66], fs=8.0)
    return s


def section_12():
    s = H1('12. ISEF readiness', 'Section 12')
    s += NOTE('The researcher deferred ISEF paperwork twice. This section is therefore an ' +
              B('assessment of readiness') + ', not paperwork, and it separates what is ready now '
              'from what still requires a decision only the researcher can make.')

    s += H2('12.1 Rules and safety')
    s += TBL(['Requirement', 'Status', 'Basis'], [
        [B('Human participants'), B('None') + ' &#8212; Form 4 not expected',
         'Amendment 1 (26 Aug 2026) removed every configuration involving a person, including '
         'the researcher. Data collected from oneself would still be human-participant research '
         'and is excluded. Commit ' + M('7102ff6') + ' states plainly that '
         '&#8220;participant&#8221; never means a recruited person.'],
        [B('Vertebrate animals'), B('None'), 'No animal work of any kind'],
        [B('Hazardous biological agents'), B('None'), 'None'],
        [B('Hazardous chemicals / devices'), B('None so far'),
         'If the rig in Section 13 is built, it is low-voltage bench electronics connected to no '
         'person. The ISEF plan already flags this: ' + B('confirm rather than assume') + ' that '
         'no Form 3 is needed.'],
        [B('Human data'), B('Public, CC0, de-identified'),
         'The MINDFUL deposit is CC0-1.0 and was collected by other researchers under their own '
         'approvals. Analysis of pre-existing de-identified public data is the standard '
         'exempt case, but ' + B('the SRC should confirm it') + ' rather than the researcher '
         'assuming it.'],
        [B('Rules Wizard'), B('Must be re-run'),
         'The plan says so explicitly, once the hardware decision is made.'],
        [B('AI-use disclosure'), B('GAP &#8212; not written'),
         'The plan carries a &#167;C-AI placeholder and warns that AI-disclosure wording has '
         'moved year to year, and that AI use is one of three things the form lists as grounds '
         'for disqualification. ' + B('The evidence to write an excellent disclosure exists') +
         ' (Section 3); the text does not.'],
    ], [0.22, 0.22, 0.56], fs=7.9)

    s += H2('12.2 Research plan components')
    s += TBL(['Component', 'State', 'Where it lives'], [
        ['Rationale', B('Ready'), M('ISEF_RESEARCH_PLAN.md') + ' &#167;A, derived from ' +
         M('PROJECT_DEFINITION.md') + '; preliminary findings added in commit ' + M('df4a056')],
        ['Research question / engineering goal / hypotheses', B('Ready'),
         'Kept as three separate statements &#8212; see Section 4.3'],
        ['Variables', B('Ready'), 'Independent, dependent, controlled and constant all specified '
         '&#8212; see Section 4.4'],
        ['Procedures', B('Ready'), M('research/procedures.md') + ' &#8212; 40 numbered procedures, '
         'described as methods-section ready'],
        ['Risk and safety', B('Ready for the computational project;') + ' needs a paragraph if '
         'the rig is built', 'Plan &#167;C'],
        ['Data analysis', B('Ready and unusually strong'),
         'Frozen designs, five gates, a claims register, four automated audits'],
        ['Bibliography', B('Present') + ' &#8212; with one unsupported claim',
         B('10 formal citations') + ' in ' + M('ISEF_RESEARCH_PLAN.md') + ' &#167;D, each with a '
         'DOI &#8212; Barrese 2013, Helmich 2024, Hughes 2021, Karpowicz 2025, Maturana 2020, '
         'Pun 2024, Scheffer 2009, Sponheim 2021, van der Bolt 2021, Wilkat 2019. Listed in full '
         'in Appendix&nbsp;B. ' + B('But the section header claims &#8220;the full annotated '
         'review contains 25 and is in the project repository&#8221; &#8212; and it is not.') +
         ' See 12.3.'],
        ['Title', B('Drafted, two options'),
         '&#8220;Decoder-Guard: An Interpretable Real-Time Health Monitor for Brain-Computer '
         'Interface Decoders, Validated Against Degradation of Known Onset&#8221;, or the shorter '
         '&#8220;Seeing Failure Before It Shows&#8221;'],
        ['Researcher-supplied fields', B('Blank by design'),
         'Name, school, adult sponsor are marked ' + M('[[RESEARCHER]]') + ' &#8212; the plan '
         'refuses to invent them'],
    ], [0.24, 0.24, 0.52], fs=7.9)

    s += H2('12.3 One document the project depends on and does not contain')
    s += CALLOUT(
        B('Audit finding, and the most significant omission found in the whole repository.') +
        ' A &#8220;literature review&#8221; is referenced as an existing, decision-shaping '
        'document in at least six places &#8212; ' + M('design_decisions.md') + ' quotes it '
        'directly (&#8220;It&#8217;s just MINDFUL with different statistics&#8221;), ' +
        M('PHASE1_2_REPORT.md') + ' records a correction to it (it had the two participants '
        'reversed), the research log cites its framing (C) as the origin of the '
        'degrading-plant-plus-compensator hypothesis, and ' + M('ISEF_RESEARCH_PLAN.md') +
        ' &#167;D states that it &#8220;contains 25 [sources] and is in the project '
        'repository.&#8221; ' + B('It is not in the repository, and no commit in the entire '
        'history ever added it.') + ' Verified with ' +
        M('git log --all --diff-filter=A --name-only') + '.',
        tone='warn', label='The literature review is cited but absent')
    s += P('Two consequences, and they are different in kind. ' + B('Scientifically') + ', a '
           'reader cannot check the reasoning that led to the project&#8217;s framing, because '
           'the document that carries it is external to the artefact &#8212; this is the largest ' +
           B('UNRECOVERABLE') + ' item in the audit. ' + B('For competition') + ', the ISEF plan '
           'makes a factual statement about the repository&#8217;s contents that the repository '
           'does not support, and a judge who looks will find that out. The fix is one of two '
           'things, and either is fine: commit the review, or amend the sentence to say where it '
           'actually lives. What is not fine is leaving the claim as it stands.')
    s += H2('12.4 How this presents to judges')
    s += TBL(['Judging dimension', 'Assessment'], [
        [B('Originality'), B('High.') + ' The corpus of 1,850 fault episodes with known onset does '
         'not exist publicly, and the five-gate battery is a genuinely missing methodological '
         'product. The framing &#8212; &#8220;you cannot validate an early-warning system without '
         'controlling onset&#8221; &#8212; is a real argument, not a project slogan.'],
        [B('Scientific thought'), B('Very high.') + ' Five withdrawn claims, five of six '
         'preregistered predictions wrong and reported, an unanswerable question labelled as '
         'unanswerable rather than answered no. This is the dimension where the project is '
         'strongest.'],
        [B('Thoroughness'), B('Very high.') + ' 123 commits, 65 scripts, 45 reports, 4,050 lines '
         'of log, 93 automatically verified claims.'],
        [B('Skill'), B('High, with a caveat.') + ' The analysis is sophisticated. The caveat is '
         'that the code was AI-authored, so the researcher must be able to explain the method and '
         'the errors in their own words. The material to do that is all in the log.'],
        [B('Clarity'), B('Good, and improving.') + ' Two rendered HTML write-ups exist, one '
         'published as a shareable artefact. But there are 45 Markdown reports and a judge will '
         'read at most three. See R2.'],
        [B('The hardest question to answer'), '&#8220;What did ' + B('you') + ' do, as opposed to '
         'the assistant?&#8221; This is not a trap, and it has a good answer: the researcher set '
         'the constraints that shaped the entire project &#8212; no human participants, do not '
         'optimise for significance, do not select a deterioration definition after seeing '
         'results, record everything including the mistakes. ' + B('Those constraints are why the '
         'project has a claims register and a linter instead of a fragile positive result.') + ' '
         'That answer needs to be rehearsed, and it needs the AI disclosure in 12.1 written.'],
    ], [0.22, 0.78], fs=8.0)

    s += H2('12.5 The presentation risk nobody has addressed yet')
    s += CALLOUT(
        'The project&#8217;s headline is a ' + B('negative result') + ', and negative results are '
        'harder to present than positive ones &#8212; not because they are worth less, but because '
        'the audience must be walked to the point where they see why the negative is informative. '
        'The chain that has to land in about ninety seconds is: ' +
        B('(1)') + ' decoders silently fail; ' + B('(2)') + ' you cannot validate a warning system '
        'without knowing when the thing being warned about started; ' + B('(3)') + ' so I built '
        '1,850 faults with known onset; ' + B('(4)') + ' no configuration passes; ' + B('(5)') +
        ' and here is the single number that explains why &#8212; a session contains one '
        'measurement taken 55 times. Every one of those five steps is documented. ' +
        B('What does not yet exist is the ninety-second version.'),
        tone='flag', label='Audit judgement on presentation')
    return s
