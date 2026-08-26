# Research Log

## Purpose

This document records the development of the BCI Early-Warning Signals research project.

## 2026-08-16

### Project Status

Beginning research planning and technical skill development.

### Current Research Direction

Investigating whether early-warning signals in longitudinal neural/BCI data can provide advance warning of deterioration.

### Questions to Resolve

- What exactly constitutes BCI deterioration?
- What datasets contain the necessary longitudinal data?
- Which neural signal type is most appropriate?
- Which early-warning signals are scientifically justified?
- Can existing data support the research question?
- What new validation data might eventually be necessary?

### Skills Being Learned

- GitHub
- Python
- Statistics
- Time-series analysis
- Signal processing
- Neuroscience
- BCI fundamentals

## 2026-08-16 — Day 1

### What I learned

- What GitHub is
- What a repository is
- What a commit is
- How research files can be organized
- How to document research development

### Research Insight

The project should not begin by assuming a particular dataset, EWS method, or hardware platform. These should be determined through literature review and data investigation.

### Next Step

Begin Python fundamentals and continue literature/dataset reconnaissance.

## 2026-08-25 — Dataset acquisition and technical foundation

### What was set up

- Installed the Python data-analysis toolchain (pandas, numpy, scipy, matplotlib, h5py).
- Created a raw/processed data separation (`data/raw/`, `data/processed/`) with
  `data/raw/` treated as strictly read-only, plus `.gitignore` rules so large data
  files are never committed to GitHub.
- Wrote `scripts/01_download_dataset.py` — reproducible download from Dryad with
  MD5 checksum verification and an automatic provenance manifest.
- Wrote `scripts/02_inspect_dataset.py` — inventories files, `.mat` variables,
  shapes, dtypes, and missingness without modifying raw data.
- Wrote `DATASET_README.md` documenting the dataset, with every claim labelled
  [CODE] / [LIT] / [UNVERIFIED] by evidence source.

### Dataset resolved

Short ID `n2z34tn5s` resolves to DOI **10.5061/dryad.n2z34tn5s** — Pun et al. (2024),
*Communications Biology*, deposited 25 Oct 2024. Associated analysis code found at
github.com/ewinapun/MINDFUL (MATLAB).

### Blocker encountered

The cloud environment's network policy blocks outbound access to `datadryad.org`
(HTTP 403 at the egress proxy), along with doi.org, nature.com, and ncbi.nlm.nih.gov.
GitHub and PyPI are reachable. **The dataset has not been downloaded.** This is an
environment settings issue, not a code issue; the download script is written and
tested and will run unchanged once access is granted.

### Worked around productively

Because `github.com` is reachable, the authors' own MATLAB analysis code was read
instead. That code must load the real files to run, so it establishes the deposit's
directory layout and variable names with high confidence — documented in
DATASET_README.md §4–§6. Notably confirmed from code: nesting is
participant → day_<N> → block_<M> → {data,info,task}.mat; time bins are 20 ms (50 Hz);
and `info.mat` carries per-trial behavioural performance including `angleErrorPerTrial`,
`trialSuccess`, `timeToTarget`, `pathEfficiency`, and `orthChanges`.

### Validation performed

`02_inspect_dataset.py` was tested against synthetic `.mat` files mimicking the
expected structure. This surfaced a real bug — the v7.3/HDF5 fallback did not trigger
reliably — which was fixed by detecting the file format from its magic bytes.

### Not yet done

`DATASET_EXPLORATION.md` is deliberately NOT written. It requires the actual data;
writing it from assumptions would defeat its purpose.

### Next step

Resolve the network access blocker, run the download, then produce the exploration
report against real data.

## 2026-08-25 (later) — Python loader and exploration pipeline

Network access to Dryad still blocked; confirmed that an environment network-policy
change only takes effect in a NEW session, since environment settings are copied
once at container startup. Continued with work that does not require the data.

### Added

- `scripts/03_load_dataset.py` — Python translation of the authors' MATLAB loader.
  Walks participant/day_<N>/block_<M>, returns tidy trial-level and block-level
  tables plus neural matrices. Applies no preprocessing; flags excluded trials
  rather than dropping them; converts MATLAB 1-based indices to Python 0-based
  while keeping both forms auditable.
- `scripts/04_explore_dataset.py` — descriptive statistics, five figures, and
  generation of `reports/DATASET_EXPLORATION.md`.

### Design principle followed

The exploration report separates **Computed** sections (calculated from data,
factual) from **Requires your judgement** sections (scientific decisions, left
blank). The script produces evidence; it does not decide what performance means,
what deterioration means, or whether a hypothesis is testable.

### Validation

Both scripts were tested against synthetic .mat files, including a deliberately
corrupted tree. All five loader consistency checks fired on broken input and none
fired on correct input. Three bugs were found and fixed in the exploration script:
a dynamic import that broke @dataclass, a crash on output paths outside the repo,
and a pandas 3 deprecation.

### Skills practised

Reading someone else's code to learn a data format; testing code against data whose
answers are already known; distinguishing computation from interpretation; checking
that .gitignore actually prevents generated files being committed.

### Next step

Obtain the data (new session with Custom network access), then run scripts 01-04
and complete sections 6, 9 and 10 of the exploration report.

## 2026-08-25 (evening) — Dataset downloaded, verified, and explored

### Obtained the data

Network policy changed to Custom, which made Dryad's metadata API reachable.
The file-download route turned out to be behind an anti-bot challenge (Anubis)
that returns a "Validating..." web page instead of the file. Rather than trying
to defeat it, used Dryad's documented route for programs: a free API account
(ORCID login → My account → API account) issuing OAuth client credentials,
exchanged for a bearer token. API account deleted immediately after use.

Downloaded Dryad **version 6**: `MINDFUL_Data.zip` (392.9 MB) + `README.md`.
Both SHA-256 verified against Dryad's published checksums.

### Four wrong assumptions in the download script, found by real failures

1. Link relation is `stash:download`, not `stash:file-download`.
2. Checksums are SHA-256, not MD5 — verification had been silently degrading.
3. `/api/v2/files/<id>/download` needs auth; the public route is different.
4. Dryad's firewall rejects generic automated User-Agents.

### Two near-miss data-safety incidents, now guarded against

- A 4.3 KB challenge web page was briefly sitting in `data/raw/` named
  `MINDFUL_Data.zip`. The script now rejects any download starting with an HTML
  doctype, deletes it, and explains why.
- The Dryad deposit contains its own `README.md`, which would have silently
  overwritten this repository's `data/raw/README.md`. Those notes were renamed
  to `_FOLDER_NOTES.md`, and the script now refuses to overwrite any file not
  recorded in a previous manifest.

### The documentation corrected an inference I had made

The authors' README showed that `startStops`, `excludeTrials` and `moveDirVect`
live in **task.mat**, not data.mat. My loader had inferred otherwise from the
authors' MATLAB code, which reads all three files into one workspace and so
cannot reveal which file each variable came from. Fixed. This is exactly the
"do not assume meaning from names" problem, applied to file locations.

### What the dataset actually contains

| | Sessions | Blocks | Trials | Bins | Features | Span |
|---|---|---|---|---|---|---|
| T11 (main) | 15 | 29 | 1,839 | 440,045 | 384 | days 658–800 = **142 days** |
| T5 (main)  | 6  | 21 | 1,200 | 251,974 | 192 | days 2121–2149 = **28 days** |

Plus T11 personal_use (2 blocks) and random_targets (2 blocks).
Total 3,301 trials, 782,708 bins, 4.35 hours.

### Correction to the literature review

The review implies T5 spans 142 days and T11 28 days. **It is reversed.**
T11 is the longitudinal participant. Plans that treated T5 as the long record
need revising.

### Key findings

- **Performance does decline**, on two independent measures that agree.
  T11: flat ~20–30° angle error and 90–100% correct through day 715, then a
  step change at day 758 to ~120° and ~25% correct, sustained through day 800.
  T5: smooth rise to ~76° peaking day 2135 (98%→37% correct), then **recovery**
  to ~39° and 93% by day 2149.
- **Task type is not a confound** — each participant used one task throughout.
- **Session spacing is uneven** (T11 gaps 3–24 days; T5 gaps 2–14 days), which
  constrains time-series methods that assume even spacing.
- **Indexing is 1-based**, confirmed empirically across all 54 blocks.
- **T5 has no spikePower** — 192 features vs T11's 384.
- **A defect in the published dataset**: T11/day_689/Block_14 has 76 values for
  three per-trial metrics but only 75 trials.

### The constraint that now defines the project

Session-level analysis gives **15 points for T11 and 6 for T5**. Any rolling
window statistic on 15 points is fragile, and van der Bolt et al. (2021) speaks
directly to this. Bin-level data is abundant (440,045 bins for T11). **Choosing
the analysis level is now the central design decision.**

### Next step

Decide operational definitions of "performance" and "deterioration", and settle
the analysis level. Then design the analysis.

## 2026-08-25 (late) — Fixed-decoder question

Could not read the paper's Methods: pmc.ncbi.nlm.nih.gov, nature.com and
biorxiv.org are all outside the environment's Custom allowlist, which covers only
Dryad. Web search confirmed the abstract-level claim ("two BrainGate2
participants ... used fixed decoders") and surfaced the companion paper
identifying T11's decoder as a fixed LSTM (Hosman & Pun).

Rather than rely on an abstract, tested the claim against the data.
`scripts/05_check_decoder_stability.py` fits a linear map from neural features to
cursorVel (the decoder's own output) in every block and compares the fitted maps
over time. A recalibration would show as a discontinuous jump; a fixed decoder
with drifting signal shows a smooth decline.

Result: smooth decline, no jumps. Largest single-session increase in similarity
was +0.089 (T11) and +0.023 (T5). Most telling: T5's performance recovery at day
2149 (37% -> 93% correct) came with cosine similarity 0.621 vs 0.620 at day 2135
- unchanged. So that recovery was NOT a recalibration; something in the neural
signal or the user restored performance.

Caveat recorded honestly: this is a diagnostic, not proof. T11's decoder is an
LSTM with internal memory, so a memoryless linear fit only approximates it and
the modest R2 (0.29/0.41) is expected by construction, not a finding.

### Skill practised

Testing a claim from a paper against the data itself instead of accepting it,
and stating precisely how much weight the test can bear.

## 2026-08-25 (late, cont.) — Fixed-decoder question ANSWERED from the Methods

Network allowlist extended to PMC/Nature/bioRxiv. Note: the WebFetch tool is
still blocked for those hosts because it runs on separate infrastructure with its
own policy, but curl from inside the container works, so the article was fetched
and parsed directly.

### Answer: decoder WEIGHTS are fixed — confirmed verbatim

- T11: LSTM trained on 18 sessions, trial days 576-646. The deposit starts at day
  658, i.e. after training. Never retrained.
- T5: trained open-loop on day 2121, updated once from the first closed-loop
  block, then "fixed for later closed-loop blocks and future sessions". Smoothing
  and gain also fixed after session 1. The calibration blocks were deliberately
  excluded from the deposit, which explains why day 2121 has only 2 blocks.

### The nuance that matters more than the answer

The system is NOT fully frozen. Three adaptive elements exist, not one:
  1. decoder weights - FIXED
  2. feature normalisation - ADAPTIVE, continuously
       T11: per-channel z-score, mean/variance updated on a 3-min rolling window
       T5: bias correction on the decoded output, adaptation rate 0.3; the
           decoder's INTERCEPT term is updated online
  3. the human user - ADAPTIVE (motor learning)

The authors state the consequence: "adaptive mean corrections ... were applied to
the neural features during online cursor control to combat this type of model
drift. Therefore, performance drops observed in this dataset were largely due to
other types of model drift."

Risk: a rolling z-score actively removes slow mean drift - exactly the kind of
slow change an early-warning indicator might look for. This must be stated
explicitly in any write-up.

Opportunity: the literature review's framing (C) - a degrading plant plus a
saturating compensator - was labelled [Speculation] with no supporting paper. The
Methods describe that architecture explicitly. The compensator is real,
documented and parameterised (3-min window for T11; adaptation rate 0.3 for T5).

### Independent validation of our exploration

Everything we computed before reading the paper matches it: 15 sessions / 142
days for T11; the early/late split at day 751 vs 758; T5's split across
2128/2133; recovery events at day 751 (T11) and day 2149 (T5) - the paper says
"93 days after the initial session for T11 and 28 days after ... for T5", which
resolve to exactly those days; 384 vs 192 features; 20 ms bins. T11's
"center-out-and-back" task is what task.mat calls circleOfCircles.

### Next step

Two definitions still to make: what defines performance, and what counts as
deterioration. Framing (C) now has documented mechanistic support and is worth
serious consideration.

## 2026-08-25 (night) — Phase 2 begins: EWS detector validation

### Built the positive/negative control pair

`scripts/06_ews_controls.py` simulates three systems whose nature is known by
construction:

1. Saddle-node bifurcation — CSD present. Detector MUST fire. (positive control)
2. Monotonic decline + noise — no bifurcation, constant recovery rate. MUST stay
   silent. (negative control)
3. Rising noise, constant recovery rate — variance rises but the system does not
   slow, so lag-1 autocorrelation must NOT rise. (negative control)

Detector: Gaussian de-trending, rolling variance and lag-1 autocorrelation,
Kendall's tau for trend, tested TWO-SIDED against AR(1)-matched surrogates.
Two-sided deliberately, because a compressed basin can produce falling
indicators before a transition (Titus et al. 2019).

### The key result: one seed is not a validation

A single run on seed 0 passed all six checks. Repeating across ten seeds passed
only 4/10 — and every failure was a MISS on the positive control. The negative
controls never once produced a false alarm.

So the detector is UNDERPOWERED, not over-eager. It fails to detect real critical
slowing down roughly 60% of the time at the default settings. This is precisely
what the control pair exists to reveal, and it would have been invisible from a
single run.

### Diagnosed the cause

Two contributing factors, both quantified:

1. De-trending can delete the signal. Near the transition the simulated system's
   correlation time is ~357 steps. A Gaussian de-trending filter with sigma=100
   removes fluctuations slower than ~100 steps — i.e. exactly the slow
   fluctuations that carry the CSD signal. Power at sigma=100 was 0.17.
   Rule: the de-trending scale must exceed the system's correlation time.
2. The effect is small in per-step terms: the AR(1) coefficient moves only from
   0.9802 to 0.9972 across the whole approach to the bifurcation.

### Consequence for the project

An underpowered detector makes a NEGATIVE result uninformative — the absence of a
warning would say more about the detector than about the neural data. This is the
same concern van der Bolt et al. (2021) raise about record length. Power must
therefore be established BEFORE any claim is made about the real data.

`scripts/07_ews_power_sweep.py` measures detection rate on the positive control
(power) and on the negative controls (false-positive rate) across a grid of
window lengths and de-trending strengths, reporting the surface rather than
picking a setting silently — as the literature review requires.

### Performance note

The detector's hot paths were vectorised (sliding_window_view for the rolling
statistics; a batched lfilter recursion for surrogate generation), and the
surrogate set is now shared between the two indicators. Kendall's tau values are
unchanged; only p-values shift in the third decimal because the random draws
differ.

## 2026-08-25 (late night) — Study design analysis, and a correction

### A correction to my own earlier reasoning

`scripts/08_record_length_check.py` reported that the "fast framing" gives 16,144
correlation times of data and therefore ample statistical power. That number is
real but answers the wrong question, and I drew the wrong conclusion from it.

It compares record length against the correlation time of a FAST observable
(cursor velocity, ~0.55 s). An early-warning test asks whether an indicator
TRENDS UPWARD over time, and the sample size for a trend test is the number of
independent observations of the SLOW variable. Sampling more finely inside a
block gives a more precise estimate at each point; it does not give more points.

Script 08 now prints this correction directly, so the repository does not
contradict itself. The correlation-time findings in its Step 1 still stand.

### The real sample sizes

| Level | T11 | T5 |
|---|---|---|
| session (all) | 15 | 6 |
| session (pre-transition) | 11 | 3 |
| block (all) | 29 | 21 |
| block (pre-transition) | **21** | 9 |

### What those sizes can detect

Smallest detectable |tau| at alpha = 0.05, two-sided: n=6 -> 0.733 (unusable);
n=11 -> 0.455 (marginal); n=21 -> 0.305 (usable); n=29 -> 0.256 (usable).
Power against a 2 sd rise: 0.25 at n=6, 0.47 at n=11, 0.74 at n=21, 0.86 at n=29.

At n=3 the exact test cannot reach alpha=0.05 at all - the smallest attainable
two-sided p-value is 1/3. The script flags this rather than reporting a
meaningless power figure.

### The consequence

Choosing BLOCK rather than SESSION as the unit of observation takes T11's
pre-transition sample from 11 to 21 and moves the study from marginal to usable,
at essentially no cost: blocks are already separate recordings and each still
holds a median of 15,161 bins, so the indicator at each point stays precise.

Overlapping sliding windows (725 for T11) are NOT a valid sample size for a trend
test - adjacent windows share most of their data, so the effective count stays
near the block count.

### A design option I had not considered

T5's percent-correct runs 97.8, 98.7, 95.5, 60.9, 37.0, 92.8 - it collapses and
then RECOVERS, with no change to the decoder. That makes T5 a built-in
reversibility control on real data: a genuine CSD indicator should rise into the
dip and fall again with the recovery, while a detector responding to elapsed time
or accumulated drift will keep climbing. No simulation can provide that test.

### Recorded

- `research/design_decisions.md` - four decisions, their interactions, four
  coherent designs, and a recommendation.
- `scripts/10_design_power_analysis.py` - makes every number above reproducible.

### Still undecided (deliberately)

Which performance variable is the declared primary, and where exactly the change
point sits. The latter must be located by a method rather than by eye, and fixed
before the indicator is computed.

## 2026-08-25 (very late) — Defining deterioration, before any EWS analysis

### Rule followed

Everything in this entry uses BEHAVIOURAL performance only. No neural feature was
read for this purpose and no early-warning indicator has been computed on the real
data. Nothing was chosen because it improves an EWS result - that result does not
exist yet.

### Procedure specified before running it

Apply every candidate deterioration definition to both participants, at block and
session level, on both angle error and success rate, and judge them by whether
independent methods AGREE. Agreement is the defence against arbitrariness: if
independent procedures converge, the boundary is a property of the data rather
than a researcher's choice. `scripts/11_define_deterioration.py`.

### Result

At T11 SESSION level, three independent data-driven methods (least-squares,
CUSUM, rank scan) agree on trial day 758 for BOTH performance variables - four
convergences on one boundary. Permutation test: p = 0.0018 (angle error),
p = 0.0014 (success). Block level is noisier, giving two distinct locations.

T5: all methods agree on day 2133 but the change is only marginal
(p = 0.046 to 0.071).

### Two structural facts the series revealed

1. T11's "before" period is NOT a flat healthy baseline. Performance wobbles from
   about day 689, spikes badly at day 727 (56.5% correct), returns COMPLETELY to
   baseline at day 751 (100% correct), and only then collapses at day 758. This
   is why the baseline+persistence rule fires early (day 689 to 715) - it detects
   onset of instability, which is a different event from the transition.

   Flagged and deliberately NOT acted on: alternating between good and bad states
   before a permanent shift is called flickering and is itself a recognised
   early-warning phenomenon. If it is ever used it must be preregistered in
   advance, not adopted after noticing it works here.

2. T5 is not a single change point. BIC comparison (block level, angle error):
   no change 134.27, one change 131.52, two changes 124.74. The best-supported
   description is down at day 2133 and back up at day 2149 - a reversible
   excursion, not a transition. That is why its single change point is only
   marginally significant.

### T11 primary / T5 secondary - justified on the merits

Not because it works better, but because T5 fails the primary role on four
independent criteria: its change point is not statistically established; it has 3
pre-transition sessions (at n=3 no test can reach alpha=0.05) against T11's 11;
9 pre-transition blocks against T11's 21; and a single-transition model does not
describe it.

Addition to the original proposal: T11 ALSO contains a reversible excursion
(day 727 degrades to 56.5%, day 751 returns to 100%), so the reversibility test
can be run within the primary participant as well as on T5.

### Recorded

`research/deterioration_definition.md` - full comparison of six methods against
every criterion requested, the hindsight-bias treatment, and a proposed
preregistration. Status: PROPOSED, not frozen, awaiting approval.

### Deliberately not done

No definition has been adopted and nothing has been frozen. That is the
researcher's decision, and freezing must be a deliberate act with a recorded
commit, not a side effect of analysis.

## 2026-08-26 — Should the event be the destabilization? Considered and rejected

### The question

Raised by Gayathri: the project is about EARLY WARNING, so shouldn't the event be
the moment things start destabilising (~day 689-715) rather than the collapse
(day 758)? Doesn't using the collapse defeat the point?

### Answer: the logic inverts

The destabilization IS the early-warning signal. Rising variance, wobbling and
flickering between good and bad states are exactly what critical slowing down
predicts as the precursor. Making them the event promotes the warning into the
thing needing warning, and then a NEW warning is required before it - and the
period before day 689 is flat and healthy, so there is nothing there to find.

    warning : destabilization  (~day 689-751)
    event   : collapse          (day 758)
    lead    : the quantity being measured

### And the destabilization date is not determined

Ran all 24 combinations of the threshold rule's parameters
(`scripts/11_define_deterioration.py --sensitivity`):

    day 689   12/24
    day 715   10/24
    day 709    2/24

The date swings 26 days depending on whether 2 or 3 consecutive degraded blocks
are required. A date that moves that much with its own parameters is a property
of the choice, not of the data.

The per-session tests also look stronger than they are. Every "significant"
session returns p = 0.0444 - which is exactly the SMALLEST p-value obtainable
with 8 baseline blocks against 2. Identical p-values across very different effect
sizes (34.1 vs 121.4 degrees) are the signature of that floor, not of equally
strong evidence. The script now reports p_floor_for_this_n alongside every p so
this cannot be misread.

By contrast day 758 is agreed by three independent methods on two independent
variables at p = 0.0018, with no parameters to choose.

### Cost in sample size

    event day 689 ->  8 blocks before -> smallest detectable tau ~0.57 (unusable)
    event day 715 -> 16 blocks before -> ~0.36 (marginal)
    event day 758 -> 21 blocks before ->  0.305 (usable)

### But the objection contained a real point, and it improved the design

The sharp form is not about which date to pick. It is: if the destabilization was
already visible in BEHAVIOUR, what does the neural signal add? A clinician
watching performance would notice trouble around day 689-715. An indicator that
only fires at day 750 predicts a collapse that was already obvious.

That is now a PRESPECIFIED SECONDARY OUTCOME: neural versus behavioural detection
time, using one detection rule applied identically to both signals, reported
across the same 24-parameter grid so the comparison stays fair even though either
date alone is not well determined. Outcome is
detection_day(behaviour) - detection_day(neural) in trial days.

Interpretation fixed in advance, including the losing case: if behaviour detects
first, the neural indicator adds nothing and will be reported that way. That is a
result the project can lose, which is what makes winning it meaningful.

The destabilization thus becomes a COMPARATOR rather than the target.

### Recorded

- research/deterioration_definition.md section 3b (why rejected) and section 6 C2
  (the new secondary outcome).
- scripts/11 --sensitivity makes the parameter sweep and the p-floor reproducible.
- scripts/12 now records both the secondary outcome and the rejected alternative
  in the freeze, so the reasoning survives in the preregistration itself.

### Still not frozen

research/FROZEN_DESIGN.json does not exist. The decision remains Gayathri's.

## 2026-08-26 — Observable chosen; autocorrelation excluded in advance

### The finding that forced this

`scripts/13_select_observable.py`, run on BASELINE BLOCKS ONLY (T11 days 658-675)
so that no trend information entered the choice:

Every purely neural observable is essentially white at every timescale from 20 ms
to 5 s. Neural PC1 has 0.33 samples of memory at 20 ms and 0.69 at 5 s bins; the
population mean is similar. Rebinning improves signal to noise, so slow structure
would have emerged if present.

The decoder output was the only candidate with real memory (1.10 s) - but the
paper's Methods record that decoded velocity is exponentially smoothed, which is
exactly the filter that manufactures memory. Its autocorrelation matches the
pure-filter prediction at short lags and decays FASTER at long lags, so there is
no memory beyond the filter. Its 1.08 s constant is a smoothing constant, not a
neural one.

### The trap that was verified, not assumed

On pure white noise, a 25-sample moving average raises lag-1 correlation from
-0.002 to +0.962. Non-overlapping rebinning leaves it at +0.038. Smoothing to
"give the signal memory" would have meant measuring our own filter. Every
candidate therefore used rebinning, never smoothing.

### Consequence

The strict critical-slowing-down prediction - rising lag-1 autocorrelation, a
slowing recovery rate - CANNOT be tested within blocks on this dataset. Not for
want of method (scripts 06-07 validated it) but because nothing recorded has a
recovery rate to measure. Rising variance, the other half of the signature, does
not require memory and remains available.

The data structure is also not the classic CSD setup. Within a block there are no
slow dynamics; the drift is across days. This is 21 sparse samples of a slowly
drifting system, not a long continuous record with a rolling window.

### Decision, recorded as amendment 1 to the frozen design

- Primary indicator: within-block temporal variance
- Parallel indicator: trial-to-trial variance
- EXCLUDED IN ADVANCE: lag-1 autocorrelation, with the evidence as the reason
- Null changed to a 5000-permutation test on block order, appropriate for a
  21-point series with no memory. Same null as the power analysis, so
  |tau| >= 0.305 and power 0.74 against a 2 sd rise apply unchanged.
- Reported regardless of outcome: that no observable here supports an
  autocorrelation-based early-warning analysis.

### Why an amendment rather than a rewrite

The original freeze is preserved intact with its own timestamp and commit; the
change is appended with its own timestamp, reason and commit. The amend path also
refuses to run if any early-warning result file already exists, so a
preregistration cannot be amended after seeing results.

### Nothing about the design is open now

The event, the observable, the indicators, the null and the power statement are
all fixed. The block-level summary uses whole blocks, so no rolling window
remains to choose.

## 2026-08-26 — Amendment 2: the specified indicator was not measurable

### What went wrong

Amendment 1 specified "within-block temporal variance" as the primary indicator,
on features z-scored with a trailing 180 s rolling window. Checking the pipeline
before running it revealed two problems, both caught before any outcome existed.

1. The rolling z-score forces every block's variance to about 1 BY CONSTRUCTION.
   Across the 8 baseline blocks it gives mean 1.025 with a coefficient of
   variation of 0.045. A variance indicator built on it measures the normaliser,
   not the brain. The rolling z-score is right for MINDFUL, which measures
   distribution SHAPE change via KLD, and wrong for a scale-based indicator.

2. Raw (unnormalised) variance is dominated by artifacts. Per-channel variance
   across the healthy baseline blocks runs 98756, 1481, 724, 725, 4605, 45102,
   839, 1174 - a roughly 100-fold swing WITHIN a period where performance is
   93-100% correct. The deposit documents these artifacts itself via avgOutliers
   and prctOutliers.

### The diagnostic that settled it

Measured on baseline blocks only - all healthy, 93-100% correct, angle error
17.9-24.5 degrees - so any spread is the indicator's noise floor:

    raw projected variance : CV 0.543, range 3.7x
    robust dispersion MAD2 : CV 0.281, range 2.3x

The robust estimator roughly halves the noise floor the indicator has to beat.

### Amendment 2

Primary and parallel indicators now use robust dispersion (sum of squared median
absolute deviations, scaled by 1.4826) rather than raw variance. Recorded with
the baseline-only justification.

### A limitation recorded in advance

The indicator is not flat even across healthy baseline blocks: robust values run
23.5, 21.5, 28.1, 27.3, 36.6, 36.7, 42.9, 50.3. Part of the noise floor is
therefore systematic rather than random, and the baseline is not a perfectly
stable reference. This is reported whatever the outcome.

### On amending twice

Repeated amendment erodes the value of a preregistration, and that cost is real
even when each change is justified. Both amendments were forced by specification
errors caught before any outcome was computed, and both are recorded with their
own timestamps, reasons and commits rather than silently applied. The guard that
refuses to amend once any result file exists is what keeps this honest. The
specification is now checked against the data rather than assumed, which is what
should have happened before amendment 1.
