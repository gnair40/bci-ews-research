# -*- coding: utf-8 -*-
"""Sections 13-15 and Appendix A."""
from kit import *


def section_13():
    s = H1('13. The original data-collection component, derived from the findings',
           'Section 13')
    s += NOTE(B('Status: DESIGN ONLY.') + ' Nothing has been built and nothing has been measured. '
              'No number in this section is a result. The design is recorded in '
              + M('research/ORIGINAL_DATA_COLLECTION_DESIGN.md') + ', committed 5 September 2026.')

    s += H2('13.1 The chain, stated in the required form')
    s += CALLOUT(
        B('The physical experiment is being proposed because') + ' the current research found '
        'that no configuration of a decoder-health monitor passes the five gates on real '
        'intracortical data, and that the reason is a single measured property &#8212; a session '
        'contains roughly one independent measurement (lag-1 r&nbsp;=&nbsp;0.995, effective '
        'n&nbsp;=&nbsp;0.1), ' +
        B('which suggests') + ' that the failure may be a general property of any multichannel '
        'sensor array that drifts slowly, rather than something specific to cortex &#8212; and '
        'that the fault corpus, every episode of which is a mathematical operation on a recorded '
        'array, may not resemble real physical degradation at all, ' +
        B('but the existing data cannot determine') + ' either of these, because nobody controlled '
        'anything in the recordings, only 13 usable sessions exist, five session-level variables '
        'are mutually entangled, and no real hardware fault was ever observed. ' +
        B('Therefore the next experiment will measure') + ' detection AUC, silence-gate pass rate, '
        'lag-1 autocorrelation and severity-ladder validity on a physical multichannel optical '
        'sensor array, ' +
        B('under conditions of') + ' physically realised faults of the same four types at '
        'independently manipulated baseline SNR and task geometry &#8212; plus a parallel arm in '
        'which nothing is injected and the rig is simply left to degrade &#8212; ' +
        B('in order to determine') + ' whether the monitor&#8217;s failure is neural-specific or '
        'array-general, and whether simulated fault injection resembles real degradation.',
        tone='neutral', label='Why a physical experiment, in one sentence')

    s += H2('13.2 The mandatory findings &#8594; experiment table')
    s += P('Every row begins with a finding that exists in this repository, names the file that '
           'establishes it, states what the archived data cannot resolve, and gives the '
           'measurement that would resolve it. ' + B('A row with no repository finding behind it '
           'does not appear.'))
    s += TBL(['Finding in this project', 'Established in', 'What archived data cannot determine',
              'What the experiment measures', 'Prediction, to be preregistered before building'], [
        [B('Lag-1 r&nbsp;=&nbsp;0.995 within a session; effective n&nbsp;=&nbsp;0.1.') + ' This '
         'single number explains why CUSUM cannot help, why longer windows cannot help, and why '
         'the silence gate always fails.',
         M('AGGREGATION_LIMIT') + '<br/>C04',
         'Whether 0.995 is a fact about ' + B('cortex') + ' or about ' + B('any slowly-drifting '
         'multichannel array') + '. There is no second kind of array in the dataset.',
         'Lag-1 autocorrelation of the risk signal within a rig session, at matched window and '
         'step geometry.',
         'Lag-1 r &#8805;&nbsp;0.99 on the rig. If it holds, the negative result generalises to '
         'sensor-array health monitoring; if it does not, the failure is neural-specific.'],
        [B('0 of 48 configurations pass the silence gate.') + ' The binding constraint is '
         'specificity, not detection.',
         M('BENCHMARK_SUMMARY') + '<br/>C03',
         'Whether a monitor could pass if the array&#8217;s drift were slower, or if sessions were '
         'plentiful. 13 usable T11 sessions is the ceiling and it cannot be raised.',
         'Silence-gate pass rate across ' + B('hundreds') + ' of rig sessions &#8212; one '
         'T11-equivalent session takes about 20 minutes and the rig can run unattended.',
         'The silence gate still fails. Session count was never the binding constraint; serial '
         'correlation was.'],
        [B('Five session-level variables are mutually entangled') + ' &#8212; decoder error, trace '
         'noise, spurious crossings, task geometry, margin over chance. Partials are identical in '
         'both directions, which is collinearity, not mediation.',
         M('WHAT_DECODER_') + M('ERROR_MEANS') + '<br/>W02, E01',
         B('Which one causes the accuracy swing.') + ' Separating them requires sessions where one '
         'varies while the others are held fixed. Nobody controlled anything in the original '
         'recordings.',
         'Detection AUC with baseline SNR and task geometry ' + B('independently manipulated') +
         ', each held fixed while the other varies.',
         'Baseline SNR dominates. If task geometry dominates instead, the P5 result (C09) is '
         'about the task, not the signal.'],
        [B('Every injected fault is a mathematical operation on a recorded array.') + ' ' +
         M('GAIN_DRIFT') + ' had to be fixed twice before it was even mean-conserving.',
         'The injector;<br/>' + M('PROJECT_DEFINITION') + ' &#167;5.4',
         'Whether real hardware degradation resembles ' + M('X * (1 - severity*ramp)') + ' at all. '
         'No real fault was ever observed &#8212; ' + B('this is the circularity risk the project '
         'names against itself') + '.',
         'The ' + B('undesigned') + ' arm: physically realised faults whose feature-level '
         'signature emerges from optics and physics rather than from an equation, with onset known '
         'because the experimenter caused it.',
         'Designed and undesigned faults are ' + B('reported separately') + '. Generalisation from '
         'the first to the second is a testable claim, not an assumption.'],
        [B('Angular error saturates near chance, and its saturation point moves per session') +
         ' (each day&#8217;s own chance ranges 47.7&#176;&#8211;102.7&#176;). 6 of 13 T11 sessions '
         'cannot be scored on unambiguous faults at all.',
         M('UNAMBIGUOUS_') + M('EPISODES') + ' (L03);<br/>' + M('WHAT_DECODER_') + M('ERROR_MEANS'),
         'Whether a metric with more dynamic range at the bad end fixes it. The recommendation was '
         'published and ' + B('could not be tested') + ' &#8212; the data has no sessions at '
         'controlled SNR.',
         'Baseline SNR swept continuously across ~20 levels, ~200 short sessions in an afternoon; '
         'measure where angular error saturates and compare candidate replacement metrics.',
         'Angular error saturates well before the signal is exhausted. A replacement metric '
         'recovers measurable range on sessions the current one cannot score.'],
        [B('Severity-ladder validity degrades as baseline error rises') + ' &#8212; monotone in '
         'only 57% (T11) and 67% (T5) of session&#215;mode cells, &#961;&nbsp;=&nbsp;&#8722;0.677 '
         'and &#8722;0.926. This is the only relationship that replicates with the same sign on '
         'both arrays.',
         M('SEVERITY_LADDER_') + M('VALIDITY') + '<br/>L01',
         'Whether the degradation is a property of the ladder or of the sessions it was applied '
         'to. Both vary together and neither can be held fixed.',
         'Ladder monotonicity across the SNR sweep, with severity levels identical throughout.',
         'Monotonicity degrades with baseline error on the rig too, at a comparable slope.'],
        [B('A monitor&#8217;s fit does not go stale over 142 days') + ' (permutation '
         'p&nbsp;=&nbsp;0.128 against a naive 0.003) &#8212; but ' + B('which day you use it on '
         'decides everything') + ' (AUC 0.32&#8211;0.97, I&#178;&nbsp;=&nbsp;0.856).',
         M('STALENESS_AND_') + M('DAY_VARIANCE') + '<br/>C07, C08',
         'Whether natural, uninjected drift produces the same statistical signature as any of the '
         'four injected modes. The archived record has natural drift but no controlled comparison.',
         B('The longitudinal arm:') + ' one session daily for 6&#8211;10 weeks with nothing '
         'injected, logging temperature and humidity as covariates. Dust, LED aging, thermal '
         'cycling and connector oxidation are allowed to happen.',
         'Natural drift matches ' + M('RATE_LOSS') + ' or ' + M('GAIN_DRIFT') + ' most closely. ' +
         B('If it matches none') + ', that is a significant finding about how fault benchmarks are '
         'built &#8212; including this one.'],
    ], [0.205, 0.155, 0.20, 0.22, 0.22], fs=7.3)

    s += H2('13.3 The apparatus')
    s += P('One rig, built once, runs three studies. An N-channel optical sensor array observes a '
           'moving 2D stimulus; a ridge decoder predicts stimulus direction from the array '
           'response. That is ' + B('structurally identical') + ' to predicting intended cursor '
           'direction from firing rates, which is what makes the existing pipeline apply unchanged.')
    s += TBL(['Element', 'Implementation', 'Cost'], [
        ['Stimulus', 'WS2812 addressable LED matrix producing a known 2D direction each frame',
         '~$15'],
        ['Sensor', 'Raspberry Pi camera module; ' + B('N virtual channels') + ' are fixed image '
         'regions, and frame-averaged region intensity is the &#8220;firing rate&#8221;', '~$25'],
        ['Compute', 'Raspberry Pi 4 or 5', '~$60'],
        ['Rotation', '28BYJ-48 stepper and driver, rotating the camera relative to the stimulus',
         '~$5'],
        ['Attenuation', 'Neutral-density filter sheet', '~$8'],
        ['Covariates', 'DHT22 temperature and humidity sensor (longitudinal arm only)', '~$5'],
        ['Enclosure', 'Cardboard or printed mount; ambient light controlled', '&#8212;'],
        [B('Total'), B('No soldering strictly required'), B('&#8776; $115')],
    ], [0.16, 0.66, 0.18], fs=8.2)

    s += H3('How each injected mode becomes a physical event')
    s += TBL(['Corpus mode', 'Physical counterpart', 'Onset known?', 'Signature designed?'], [
        [M('CHANNEL_DROPOUT'), 'Occlude specific image regions', B('Yes'), 'Yes'],
        [M('RATE_LOSS'), 'Neutral-density filter over the whole stimulus', B('Yes'), 'Yes'],
        [M('GAIN_DRIFT'), 'Per-region illumination change', B('Yes'), 'Yes'],
        [M('GEOMETRY_ROTATION'), B('Literally rotate the camera') + ' on the stepper', B('Yes'),
         'Yes'],
        [B('Undesigned faults'), 'Loosen a connector; warm a component for thermal drift; '
         'introduce EMI from a nearby device; let contact impedance drift over hours',
         B('Yes') + ' &#8212; the experimenter did it and logged it',
         B('No') + ' &#8212; it emerges from physics'],
    ], [0.20, 0.46, 0.15, 0.19], fs=8.1,
        caption=B('Known onset with an undesigned signature is the strongest ground truth '
                  'available to this project') + ', and it requires no participants at all. It is '
                'the direct answer to &#8220;your faults are made up.&#8221;')

    s += H2('13.4 Variables for the rig study')
    s += TBL(['Class', 'Variable', 'Levels'], [
        [B('Manipulated'), 'Fault mode', '4, physically realised, plus an undesigned arm and a '
         'no-fault control'],
        ['', 'Severity', '3, matched to the corpus definitions'],
        ['', 'Onset time', 'Randomised and logged before the run, as in the corpus'],
        ['', B('Baseline SNR'), B('Swept independently') + ' &#8212; the manipulation archived '
         'data cannot offer'],
        ['', B('Task geometry'), B('Swept independently') + ' &#8212; likewise'],
        [B('Controlled'), 'Channel count', 'Exactly 384 (matching T11) or 192 (matching T5) '
         '&#8212; ' + B('an open decision')],
        ['', 'Bin width, window geometry', 'Identical to the neural pipeline'],
        ['', 'Decoder', 'Ridge regression, frozen after fitting, as in ' + M('18_reference_decoder.py')],
        [B('Constant'), 'Ambient light', 'Enclosure'],
        ['', 'Stimulus speed distribution, frame rate', 'Fixed'],
        [B('Dependent'), 'Angular error, session-level AUC, silence-gate pass rate, lag-1 '
         'autocorrelation, achieved damage',
         B('Unchanged from the neural study') + ' &#8212; that is the point'],
    ], [0.14, 0.32, 0.54], fs=8.1)
    s += CALLOUT(
        'The analysis code does not change. The injector, the reference decoder, the harness, the '
        'five gates, ' + M('decoder-guard') + ' and the claim verifier all apply unmodified. ' +
        B('The analysis instrument is already written and already validated by 93 checks') +
        ' &#8212; which means the rig&#8217;s results are comparable to the neural results by '
        'construction rather than by argument.',
        tone='good', label='Why this design is cheap in the way that matters')

    s += H2('13.5 The rule that governs what may be simulated')
    s += CALLOUT(
        B('The perturbation may be simulated. The response to it may not.'),
        tone='neutral', label='Stated verbatim in PROJECT_DEFINITION.md §5.5')
    s += TBL(['Legitimately simulated', 'Must be real'], [
        ['The degradation schedule &#8212; which mode, when, how fast',
         'The signal&#8217;s own non-stationarity. Simulating it assumes the answer.'],
        ['Surrogate and permutation null distributions',
         'The human&#8217;s adaptive compensation (in the archived arm)'],
        ['Power analysis and the severity ladder',
         'The decoder&#8217;s adaptive normalisation'],
        ['The sensor-failure ' + B('mechanism') + ' on the rig (switched attenuation)',
         'The analog path it passes through'],
    ], [0.42, 0.58], fs=8.2)
    s += P('The reason this line matters: simulating the thing you are trying to detect is '
           'circular &#8212; you would be measuring your own generative assumptions. That is the '
           'same error, in a different costume, as choosing a deterioration definition after '
           'seeing which one gives the best result. ' + B('This project already refused that once.'))

    s += H2('13.6 Designs considered and rejected')
    s += TBL(['Rejected', 'Reason'], [
        ['EMG, EEG, OpenBCI, Muse &#8212; on anyone, including the researcher',
         B('Human participant research.') + ' Excluded by Amendment 1 and would require SRC/IRB '
         'review. Data collected from oneself still counts.'],
        ['Camera-tracked hand movement as a &#8220;BCI-like&#8221; task',
         'Same &#8212; still human participant research.'],
        ['More neuron simulation in software',
         B('Not data collection.') + ' Redundant: a simulation layer already exists and adding '
         'another closes none of the four gaps.'],
        ['Accelerometer vibration monitoring of a motor',
         'Standard predictive maintenance, researched since the 1980s, and connected to none of '
         'this project&#8217;s specific findings.'],
        ['Robot arm performing a reaching task',
         'Plausible but muddies the decoder/monitor framing, ~10&#215; the cost, and addresses no '
         'documented gap.'],
    ], [0.34, 0.66], fs=8.1)

    s += H2('13.7 Ranking, risks, and what must be decided first')
    s += TBL(['Rank', 'Study', 'Verdict'], [
        ['1', B('Controlled degradation of a physical array'),
         'Best combination of novelty, feasibility and rigour. Attacks the worst gap, reuses '
         '65 verified scripts, ~$115, two weekends to build, no participant paperwork.'],
        ['2', B('Longitudinal natural degradation'),
         B('Highest novelty here') + ', gated on 6+ weeks of calendar time. Costs nothing extra to '
         'run in parallel on the same hardware. ' + B('Start on day one, harvest at the end.')],
        ['3', B('Metric saturation sweep'),
         'Nearly free as a sub-study of #1. ' + B('Not a standalone project.')],
    ], [0.06, 0.28, 0.66], fs=8.2)
    s += H3('Risks, stated plainly')
    s += UL([
        B('Skill gap.') + ' Hardware is a different skill from running scripts, and ' + B('a '
        'half-built rig producing noisy data is worse than no rig') + '. Mitigation: build the '
        'simplest version first &#8212; camera, LED matrix, no motor, 16 channels &#8212; get it '
        'producing data end to end, then scale to 384 channels and add rotation.',
        B('It is not neural.') + ' This is the real weakness and it must be defended as a claim '
        'about ' + B('a class of signal') + ', not as a brain simulation. The claim under test was '
        'always stated at the level of multichannel arrays with slow drift; no claim is made that '
        'a photodiode resembles a neuron.',
        B('Timeline.') + ' The longitudinal arm needs 6+ weeks of wall-clock time and is not '
        'compressible.',
        B('Nothing is built until a preregistration exists') + ' stating the predictions derived '
        'from the neural findings before a single measurement is taken &#8212; the same discipline '
        'every study in this project has followed. The predictions in the last column of '
        '&#167;13.2 are the draft of that document.',
    ])
    s += CALLOUT(
        B('Three decisions belong to the researcher and block the build:') + ' ' +
        B('(1)') + ' the deadline &#8212; it decides whether the 6-week longitudinal arm is in or '
        'out; ' + B('(2)') + ' whether to build hardware at all &#8212; scientifically the right '
        'call, and also real work, with a defensible computational project remaining if the answer '
        'is no; ' + B('(3)') + ' channel count &#8212; 384 to match T11, 192 to match T5, or both.',
        tone='flag', label='Open decisions')

    s += H2('13.8 What the integrated project becomes')
    s += TBL(['Part', 'Source', 'Role'], [
        [B('I. Archived'), 'MINDFUL T11 + T5',
         'The real-world instance. Establishes the failure, measures its cause, ' + B('generates '
         'the predictions') + '.'],
        [B('II. Original'), 'The sensor rig',
         'The controlled instance. Manipulates what cortex will not allow. ' + B('Tests those '
         'predictions') + '.'],
        [B('III. Computational'), 'The existing pipeline',
         'The shared instrument. Identical analysis on both, by construction.'],
    ], [0.18, 0.22, 0.60], fs=8.3)
    s += CALLOUT(
        'The structure that makes this unusual: ' + B('a computational finding is used to make '
        'falsifiable point predictions about a physical system, which is then built.') + ' That '
        'converts the project&#8217;s largest weakness &#8212; two participants and control over '
        'nothing &#8212; into its methodological centrepiece. It is also the only version of the '
        'original-data component that answers the sharpest criticism the project currently faces.',
        tone='good', label='The reason this design is worth the work')
    return s


def section_14():
    s = H1('14. Where the project stands, and what to do next', 'Section 14')

    s += H2('14.1 Current state, in one table')
    s += TBL(['Dimension', 'State'], [
        [B('Scientific result'),
         B('Complete and negative, with the cause located.') + ' 0 of 48 configurations pass; the '
         'binding constraint is specificity; the cause is lag-1 r&nbsp;=&nbsp;0.995. Achieved '
         'session-level AUC 0.673 (T11) and 0.742 (T5), against &#8776;&nbsp;0.99 required at the '
         'operating point the design specified and &#8776;&nbsp;0.93 required for 80% detection '
         'at a 10% false-flag rate.'],
        [B('Original artefacts'),
         'Three that did not previously exist: a corpus of 1,850 fault episodes with known onset; '
         'a five-gate validation battery whose first gate would have caught the project&#8217;s own '
         'Phase 1&#8211;2 error; and a replicated demonstration that the monitor detects what '
         'counting spikes cannot.'],
        [B('Clean positives'),
         'Two. Task changes are separated from faults by 15&#215;&#8211;70&#215;. Commissioning '
         'costs about two minutes of healthy recording, on both participants.'],
        [B('Verification'),
         '93 claims recomputed from data files, all matching. Five automated gates, all passing.'],
        [B('Documentation'),
         '4,050-line log with 54 dated headings; 45 reports; 12 preregistrations; a claims register '
         'with 38 entries and 5 statuses.'],
        [B('Binding limitation'),
         B('n&nbsp;=&nbsp;2 participants, and they disagree.') + ' Blocked on Dryad credentials for '
         'a third.'],
        [B('Original data collection'),
         B('Designed, not built.') + ' Three open decisions belong to the researcher.'],
        [B('ISEF paperwork'),
         B('Deferred by the researcher,') + ' twice. The plan exists as a draft with '
         'researcher-only fields left blank.'],
    ], [0.20, 0.80], fs=8.2)

    s += H2('14.2 Prioritised roadmap')
    s += P('Ordered by value per unit of effort, with the reason each sits where it does. '
           'Items R1&#8211;R3 are scientific; R4&#8211;R8 are hygiene that a judge will notice.')
    s += TBL(['#', 'Action', 'Why here', 'Effort', 'Blocked on'], [
        ['R1', B('A third participant &#8212; Card et al. 2024 (T15)'),
         B('Worth more than any detector improvement.') + ' With two participants who disagree, no '
         'generality is demonstrable. And it is cheap: ' + B('even without a decoder, the silence '
         'gate needs only healthy recordings') + ' &#8212; enough to establish whether the failure '
         'belongs to these two arrays or to the approach. DOI ' + M('10.5061/dryad.dncjsxm85') +
         ', 256 electrodes, different task, 11.6&nbsp;GB. The downloader is already parameterised '
         'by DOI.',
         'Low, once unblocked',
         B('Dryad credentials') + ' &#8212; ' + M('DRYAD_CLIENT_ID') + ' and ' +
         M('DRYAD_CLIENT_SECRET') + ' set in the ' + B('environment config, not in chat')],
        ['R2', B('Answer the three open hardware decisions, then preregister the rig study'),
         'Section 13 is a complete design that cannot start. The deadline decides whether the '
         '6-week longitudinal arm exists at all, and that arm is the highest-novelty part.',
         'A conversation, then a document',
         B('The researcher') + ' &#8212; deadline, whether to build at all, channel count'],
        ['R3', B('Re-run the corpus with the window-overlap fix'),
         'L02 measures the bias at 0.007&#8211;0.012 AUC and shows it is conservative, so nothing '
         'changes &#8212; but the fix is one line (' + M('start + window <= onset_bin') + ') and it '
         'removes a standing caveat from every number in the project.',
         'Low &#8212; one condition, one re-run', '&#8212;'],
        ['R4', B('Write the AI-use disclosure'),
         B('The highest-risk gap in the whole project.') + ' AI use is one of three things the ISEF '
         'form names as grounds for disqualification, and the plan carries only a placeholder. The '
         'evidence for an unusually strong disclosure already exists in Section 3 &#8212; fourteen '
         'documented errors caught and corrected.',
         'Low', 'The 2026&#8211;27 form wording; confirm with the SRC'],
        ['R5', B('Commit the literature review, or amend the claim that it is here'),
         B('A factual statement in the ISEF plan that the repository does not support.') + ' The '
         'review is cited and quoted in at least six files and is the origin of the '
         'project&#8217;s framing, its threat model and its comparator choice &#8212; and no '
         'commit ever added it. The bibliography itself is fine: 10 formal citations with DOIs '
         'exist in ' + M('ISEF_RESEARCH_PLAN.md') + ' &#167;D. Either commit the review or say '
         'where it lives.',
         'Low', '&#8212;'],
        ['R6', B('Pin exact package versions'),
         'The six dependencies use ' + M('&gt;=') + ' lower bounds. The reproducibility gate '
         'reports this limit itself. A ' + M('pip freeze') + ' lockfile closes it.',
         'Trivial', '&#8212;'],
        ['R7', B('Tag the pivotal commits'),
         'Nothing is tagged &#8212; not the design freeze, not either phase closeout. Tags make '
         'the preregistration story visible from one command instead of from a JSON field.',
         'Trivial', '&#8212;'],
        ['R8', B('Write the ninety-second version'),
         'The project&#8217;s five-step argument is fully documented across 45 reports and a '
         '4,050-line log. A judge will read three of them. The compressed version does not yet '
         'exist in any file.',
         'Low, and high-value', '&#8212;'],
        ['R9', B('Combine better features WITH the four-component decomposition'),
         'The only remaining scientific direction not ruled out. F1 and F2 ' + B('are') + ' better '
         'features under a matched control, and ' + M('decoder_guard') + '&#8217;s advantage is the '
         'decomposition rather than its inputs &#8212; so the untried thing is the combination. ' +
         B('Needs its own preregistration') + ', not a change made on the strength of a post-hoc '
         'table.',
         'Medium', 'A preregistration'],
    ], [0.04, 0.24, 0.38, 0.14, 0.20], fs=7.6)

    s += H2('14.3 The three most important next steps')
    s += TBL(['', 'Step', 'Why it is in the top three'], [
        [B('1'), B('Unblock the third participant (R1)'),
         'It is the only action that can change the project&#8217;s binding limitation, and it '
         'costs almost nothing once the credentials exist. Every other scientific improvement is '
         'worth less until n&nbsp;&gt;&nbsp;2.'],
        [B('2'), B('Decide the deadline and whether hardware gets built (R2)'),
         'Section 13 is a finished design sitting behind three decisions only the researcher can '
         'make &#8212; and one of them, the deadline, has a hard 6-week floor that gets harder to '
         'meet every day it goes unanswered.'],
        [B('3'), B('Write the AI-use disclosure (R4)'),
         'It is low effort, it is the single highest-risk gap for competition, and the project '
         'has an unusually strong story to tell &#8212; fourteen documented errors, five withdrawn '
         'claims, three corrected p-values, and four debugged checking tools.'],
    ], [0.05, 0.30, 0.65], fs=8.2)
    return s


def section_15():
    s = H1('15. Project memory / master context', 'Section 15')
    s += NOTE('This section is written to be read cold, by someone (or some future session) with '
              'no prior knowledge of the project. It is deliberately self-contained and '
              'deliberately repeats facts stated earlier.')

    s += H2('15.1 What the project is, in five sentences')
    s += P('People with paralysis control a computer cursor through an implanted electrode array '
           'and a ' + B('decoder') + ' that converts neural activity into motion. Over months the '
           'recording drifts and the decoder silently becomes wrong, and the only remedy '
           '&#8212; recalibration &#8212; is scheduled by guesswork. This project set out to build '
           'an early-warning system for that failure, found that ' + B('no observational dataset '
           'can validate such a system') + ' because it cannot say when deterioration began, and '
           'therefore constructed a corpus of 1,850 degradation episodes whose onsets were chosen '
           'and locked before any detector existed. It then built a five-gate validation battery, '
           'built a monitor, and measured that ' + B('no configuration passes') + '. The reason is '
           'a single number: a recording session contains roughly one independent measurement, '
           'taken 55 times.')

    s += H2('15.2 Standing constraints set by the researcher')
    s += P('These govern all future work on this project and are not negotiable by an assistant.')
    s += UL([
        B('No scientific decisions made on the researcher&#8217;s behalf,') + ' and no analysis '
        'generated that the researcher does not understand.',
        B('No assumption of prior knowledge') + ' of Python, pandas, Git, GitHub, or '
        'data-science terminology.',
        B('Errors are never hidden or silently worked around.') + ' They are explained, along with '
        'the fix.',
        B('Raw data stays separate from processed data') + ' and the original files are never '
        'modified.',
        B('Nothing is optimised for statistical significance.') + ' Multiple deterioration '
        'definitions must not be tried and the best-performing one selected.',
        B('The current idea is not assumed to be the best version of the project.'),
        B('Everything is recorded in GitHub,') + ' and the research log captures decisions ' +
        B('and mistakes') + '.',
        B('HARD CONSTRAINT: no human participants.') + ' This includes the researcher &#8212; data '
        'collected from oneself is still human-participant research.',
        B('ISEF paperwork is deferred') + ' until the researcher says otherwise.',
    ])

    s += H2('15.3 The facts a future session must not have to rediscover')
    s += TBL(['Fact', 'Value', 'Where'], [
        ['Repository / branch', M('gnair40/bci-ews-research') + ' / ' +
         M('claude/isef-research-pipeline-9zt4uq'), '&#8212;'],
        ['Dataset', 'MINDFUL, Pun et al. 2024, Dryad ' + M('10.5061/dryad.n2z34tn5s') + ' v6, CC0',
         M('data/raw/download_manifest.json')],
        ['Participants', 'T11 (384 features, 15 sessions, days 658&#8211;800) and T5 (192 features, '
         '6 sessions, days 2121&#8211;2149). ' + B('T11 is the longitudinal one'),
         M('reports/PHASE1_2_REPORT.md')],
        ['Corpus', '1,073 T11 episodes + 777 T5; 4 modes &#215; 3 rates &#215; 3 severities; '
         'master seed ' + M('20260826'), M('data/processed/injection_plan*.json')],
        ['Design freeze', '2026-08-26 01:31:10 UTC at commit ' + M('20db485') + ', with input '
         'SHA-256s and 2 amendments', M('research/FROZEN_DESIGN.json')],
        [B('The headline'), B('0 of 48 configurations pass all five gates'),
         M('reports/BENCHMARK_SUMMARY.md')],
        [B('The explanation'), B('Lag-1 r = 0.995 (T11), 0.980 (T5); effective n = 0.1 and 0.4'),
         M('reports/AGGREGATION_LIMIT.md')],
        [B('The gap'), 'Achieved session-level AUC 0.673 (T11), 0.742 (T5). Needed: '
         '&#8776;&nbsp;0.99 at the 0.1/h budget as specified, or &#8776;&nbsp;0.93 for 80% '
         'detection at a 10% false-flag rate. ' + B('Always say which target is meant'),
         M('reports/OPERATING_POINT_BOUND.md')],
        ['Gate order', B('Silence first') + ', then rate-invariance, comparator, elapsed-time, '
         'detrend', M('research/phase3_design_implications.md')],
        ['Reporting rule', B('Lead time and false-alarm rate are always reported as a pair') +
         ', never singly', M('scripts/20_evaluation_harness.py')],
        ['Unit rule', B('Bootstrap over episodes, never over windows.') + ' Window-level and '
         'episode-level numbers must be labelled as such', M('reports/UNIT_OF_ANALYSIS.md')],
        ['Blocked on', B('Dryad credentials') + ' ' + M('DRYAD_CLIENT_ID') + ' / ' +
         M('DRYAD_CLIENT_SECRET') + ' for T15, Card et al. 2024, ' + M('10.5061/dryad.dncjsxm85') +
         ', 11.6&nbsp;GB &#8212; ' + B('to be set in the environment config, not pasted in chat'),
         M('research/research_log.md') + ', 28 Aug entry'],
    ], [0.17, 0.53, 0.30], fs=7.8)

    s += H2('15.4 Working practices this project follows')
    s += OL([
        B('Preregister before computing.') + ' Every study since Phase 3 has a frozen note or JSON '
        'stating its criterion &#8212; and, where possible, a prediction &#8212; committed before '
        'the analysis runs.',
        B('Build the grader before the thing being graded.') + ' The evaluation harness was '
        'committed when the only detectors it could score were three the project did not invent.',
        B('Correct inline, never in place.') + ' A corrected report carries a <b>(!)</b> block '
        'explaining what was wrong. The original text is not edited away.',
        B('Run the gates, then commit.') + ' Running them afterwards leaves ' +
        M('data/processed/*.json') + ' dirty; a stop hook caught this once.',
        B('Never re-date the log to match the commits.') + ' Reconcile the mismatch in a gate '
        'instead, with the reason recorded.',
        B('A checking tool must be tested against a defect already known to exist') + ' before its '
        'output is trusted. Four tools in this project were wrong before they were useful.',
        B('Use ') + M('git commit -F -') + B(' with a heredoc') + ' &#8212; apostrophes in commit '
        'messages break shell quoting.',
        B('A finding is a prompt, not a verdict.') + ' Linter hits are reviewed individually and '
        'deliberate sites are listed with reasons, so the gate stays clean rather than noisy.',
    ])

    s += H2('15.5 Claims: what may and may not be quoted')
    s += TBL(['Status', 'Count', 'Meaning', 'Examples'], [
        [B('ESTABLISHED'), '17', 'Survived its challenges; backed by a recomputed check',
         'The reference decoder works (C01); 0 of 48 pass (C03); lag-1 r&nbsp;=&nbsp;0.995 (C04); '
         'session accuracy tracks decoder error (C09)'],
        [B('LIMITATION'), '10', 'A measured property of the corpus or method, not a result',
         'Severity valid only in aggregate (L01); window overlap costs 0.007&#8211;0.012 AUC (L02); '
         'pooled p-values (L09)'],
        [B('WITHDRAWN'), '5', B('Retracted on evidence &#8212; do not quote'),
         'W01&#8211;W05, listed in full in Section 8.2'],
        [B('UNANSWERABLE'), '1', 'This data cannot decide it &#8212; ' + B('not the same as no'),
         'Whether the session effect is failed detection or degraded labels (U01)'],
        [B('EXPLORATORY'), '5', 'Not preregistered; hypothesis-generating only',
         'Task directional concentration varies 50-fold (E01); the supervised separability bounds '
         '(E04, E06)'],
    ], [0.14, 0.07, 0.28, 0.51], fs=8.0)
    s += NOTE('38 entries in total, covering 92 of 93 verifier checks. The one uncovered check '
              '(&#8220;hardest mode pair, T11&#8221;) is reported by the register itself as a '
              'coverage gap &#8212; it asks whether the evidence base and the story have drifted '
              'apart, and answers honestly.')

    s += H2('15.6 If the project has to be defended in one paragraph')
    s += CALLOUT(
        'This project asked whether decoder failure can be seen coming. It discovered that the '
        'question cannot be answered honestly with observational data, because lead time depends '
        'on a definition the analyst chooses and false-alarm rate cannot be estimated at all. So '
        'it built the missing ground truth &#8212; 1,850 degradations whose onsets were locked '
        'under checksum before any detector existed &#8212; and a validation standard whose first '
        'gate would have caught its own earlier mistake. Then it measured that no configuration '
        'passes, and found the reason: a recording session contains roughly one independent '
        'measurement, so no amount of averaging, no better decision rule, and no longer window '
        'closes the gap between the 0.67&#8211;0.74 achieved and the ~0.93 a usable operating point would need. ' +
        B('It produced a benchmark that did not previously exist, a test battery, a replicated '
        'demonstration that the monitor sees what counting spikes cannot, one clean '
        'deployment-relevant positive, and a quantified bound on what would have to change.') +
        ' Along the way it withdrew five of its own claims, corrected three published p-values '
        'from significant to null, and debugged four of its own checking tools. That is a more '
        'useful contribution than a fragile positive would have been, and every step of it is '
        'reproducible.',
        tone='good', label='The paragraph')
    return s


def appendix_b():
    s = H1('Appendix B &#8212; sources the project cites', 'Appendix B')
    s += P('Transcribed from ' + M('research/ISEF_RESEARCH_PLAN.md') + ' &#167;D, which states '
           'these are the sources the Rationale actually draws on. '
           + B('The same section also states that a 25-source annotated review is in the project '
           'repository. It is not') + ' &#8212; see Section&nbsp;12.3.')
    s += TBL(['#', 'Citation', 'DOI'], [
        ['1', 'Barrese, J. C., Rao, N., Paroo, K., Triebwasser, C., Vargas-Irwin, C., '
         'Franquemont, L., &amp; Donoghue, J. P. (2013). Failure mode analysis of silicon-based '
         'intracortical microelectrode arrays in non-human primates. <i>Journal of Neural '
         'Engineering, 10</i>(6), 066014.', M('10.1088/1741-2560/10/6/066014')],
        ['2', 'Helmich, M. A., Olthof, M., Oldehinkel, A. J., Wichers, M., Bringmann, L. F., &amp; '
         'Smit, A. C. (2024). Slow down and be critical before using early warning signals in '
         'psychopathology. <i>Nature Reviews Psychology, 3</i>, 767&#8211;780.',
         M('10.1038/s44159-024-00369-y')],
        ['3', 'Hughes, C. L., Flesher, S. N., Weiss, J. M., Downey, J. E., Collinger, J. L., &amp; '
         'Gaunt, R. A. (2021). Long-term intracortical microelectrode array performance in a '
         'human: A 5 year retrospective analysis. <i>Journal of Neural Engineering, 18</i>(4).',
         M('10.1088/1741-2552/ac1add')],
        ['4', 'Karpowicz, B. M., et al. (2025). Stabilizing brain-computer interfaces through '
         'alignment of latent dynamics. <i>Nature Communications, 16</i>.',
         M('10.1038/s41467-025-59652-y')],
        ['5', 'Maturana, M. I., Meisel, C., Dell, K., Karoly, P. J., D&#8217;Souza, W., Grayden, '
         'D. B., Burkitt, A. N., Jiruska, P., Kudlacek, J., Hlinka, J., Cook, M. J., Kuhlmann, L., '
         '&amp; Freestone, D. R. (2020). Critical slowing down as a biomarker for seizure '
         'susceptibility. <i>Nature Communications, 11</i>, 2172.',
         M('10.1038/s41467-020-15908-3')],
        ['6', B('Pun, T. K., Khoshnevis, M., Hosman, T., et al. (2024). Measuring instability in '
         'chronic human intracortical neural recordings towards stable, long-term brain-computer '
         'interfaces. <i>Communications Biology, 7</i>.') + ' &#8212; the source of this '
         'project&#8217;s data.',
         M('10.1038/s42003-024-06784-4') + '<br/>Dataset: ' + M('10.5061/dryad.n2z34tn5s')],
        ['7', 'Scheffer, M., Bascompte, J., Brock, W. A., Brovkin, V., Carpenter, S. R., Dakos, '
         'V., Held, H., van Nes, E. H., Rietkerk, M., &amp; Sugihara, G. (2009). Early-warning '
         'signals for critical transitions. <i>Nature, 461</i>, 53&#8211;59.',
         M('10.1038/nature08227')],
        ['8', 'Sponheim, C., Papadourakis, V., Collinger, J. L., Downey, J., Weiss, J., Pentousi, '
         'L., Elliott, K., &amp; Hatsopoulos, N. G. (2021). Longevity and reliability of chronic '
         'unit recordings using the Utah, intracortical multi-electrode arrays. <i>Journal of '
         'Neural Engineering, 18</i>(6), 066044.', M('10.1088/1741-2552/ac3eaf')],
        ['9', 'van der Bolt, B., van Nes, E. H., &amp; Scheffer, M. (2021). No warning for slow '
         'transitions. <i>Journal of the Royal Society Interface, 18</i>(174), 20200935.',
         M('10.1098/rsif.2020.0935')],
        ['10', 'Wilkat, T., Rings, T., &amp; Lehnertz, K. (2019). No evidence for critical slowing '
         'down prior to human epileptic seizures. <i>Chaos, 29</i>(9), 091104.',
         M('10.1063/1.5122759')],
    ], [0.04, 0.66, 0.30], fs=7.8)
    s += NOTE('Two further sources are named elsewhere in the repository and are not in '
              '&#167;D: ' + B('Card et al. (2024)') + ', the T15 dataset identified as the third '
              'participant (' + M('10.5061/dryad.dncjsxm85') + '), and the MINDFUL analysis code '
              'the project reproduced at r&nbsp;=&nbsp;0.985. Both belong in the bibliography if '
              'the plan is finalised.')
    return s


def appendix_a(claims):
    s = H1('Appendix A &#8212; every verified claim, recomputed', 'Appendix A')
    s += P('Regenerated during this audit by ' + M('python3 scripts/31_verify_claims.py') + '. '
           'Each row is recomputed from stored data files rather than read from a report; the '
           '&#8220;claimed&#8221; column is what the reports state and the &#8220;actual&#8221; '
           'column is what the data files give now. ' + B('All 93 matched.'))
    rows = [[str(i + 1), c[0], c[1], c[2], 'ok'] for i, c in enumerate(claims)]
    s += TBL(['#', 'Check', 'Claimed', 'Actual', ''], rows,
             [0.045, 0.615, 0.115, 0.115, 0.11], fs=7.2,
             align={2: 'RIGHT', 3: 'RIGHT', 4: 'CENTER'})
    return s
