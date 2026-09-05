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

## 2026-08-26 — Phase 1-2 characterisation complete; what the dataset actually is

Exploratory, run after the confirmatory analysis was reported. Does not revise it.

### The number that explains most of the phase

Mean firing rate falls 56.5% across T11's record, 26.5 to 11.5. Over 142 days
more than half the recorded neural activity disappears.

### The indicator adds nothing beyond firing rate

    indicator vs angle error, raw                  rho +0.858  p < 0.0001
      controlling for mean firing rate             rho +0.260  p = 0.17  (n.s.)
      controlling for elapsed time                 rho +0.105  p = 0.59  (n.s.)
    mean firing rate vs angle error                rho -0.880  p < 0.0001

A linear fit of the indicator on firing rate gives R2 = 0.707. Controlling for
firing rate, the indicator's link to performance is no longer significant.
Controlling for time, nothing remains.

And mean firing rate predicts performance as well as the whole dispersion
pipeline does. A one-line calculation matches a five-dimensional projection with
robust statistics. That is now a comparator any future indicator must beat,
alongside MINDFUL.

### The diagnosis is only partial, and that is stated

Firing rate does NOT explain the within-baseline rise that overturned the
headline. Across the healthy baseline the indicator climbs steeply (tau +0.857,
p 0.0018) while firing rate barely moves (tau -0.286, p 0.40). Something else
drives it and has not been identified; avgOutliers, silent channels and
low-variance channels were all tested and rejected (|rho| < 0.32).

### Five requirements for Phase 3

1. De-trend the block-level indicator series before testing its trend.
2. A prespecified within-baseline SILENCE GATE - the indicator must show no
   significant trend during healthy performance before its pre-transition trend
   may be interpreted. Had this been a gate rather than a footnote, the headline
   would never have been reported as positive.
3. Demonstrate invariance to mean firing rate, on the baseline, rather than
   assert it.
4. Add mean firing rate as a comparator to beat.
5. Control for elapsed time.

### The honest possibility

This dataset may not be able to answer the question, because the array's signal
decline is so large and so entangled with performance that no measure separates
"approaching a transition" from "the electrodes are failing". If Phase 3's gates
are applied and nothing passes, that is itself a publishable methodological
result.

Recorded in research/phase3_design_implications.md, which also lists where a
positive result could still legitimately come from: the residual after removing
firing rate (which is what framing C actually predicts), covariance geometry
rather than scale, and flickering - all requiring preregistration in advance.

## 2026-08-26 — Phases 1 and 2 closed out

### Loose ends tied up

1. Licence resolved: the deposit is CC0-1.0, public domain dedication. No
   restriction on publishing; cite the DOI and paper as good practice.
2. cursorVel units resolved: normalised workspace units per bin. The T5/T11
   range difference is participant-specific GAIN - the Methods state smoothing
   and gain were manually adjusted in the first session and fixed thereafter.
   Not a data problem.
3. The additional T11 cohort (personal_use, random_targets), flagged by the
   literature review as "a free out-of-distribution robustness check sitting in
   the download" and never used, has now been used. See below.
4. DATASET_EXPLORATION sections 6, 9 and 10, deliberately left blank pending
   decisions, are now filled in from what the analysis established.
5. DATASET_README's open questions are all closed, and the new questions the
   analysis raised are recorded in their place.
6. Procedures 32-40 added.
7. reports/PHASE1_2_REPORT.md consolidates everything.

### The out-of-distribution check, and it is decisive

The indicator computed on completely different tasks recorded on the SAME DAY:

    day 658:  cursor task 22.65   free web browsing 24.55   difference  8.4%
    day 665:  cursor task 27.86   random targets    26.21   difference  5.9%

Against a threefold range across the whole record (21.7 to 67.7). So the
indicator is essentially task-invariant: it gives nearly the same value whether
the participant is doing a structured cursor task or browsing the web.

That is a third independent confirmation, alongside the firing-rate correlation
and the participant disagreement, that the indicator tracks the state of the
RECORDING rather than the task or the participant's performance.

### The figure that explains the negative result

reports/figures/11_t11_why_negative.png stacks three quantities on one time
axis: the indicator, task performance, and mean firing rate, with the healthy
baseline shaded. The indicator climbs from 22 to 50 INSIDE the shaded baseline
while performance sits flat at about 20 degrees. That is the whole result in one
picture.

### Still incomplete

The length-scaling run keeps being interrupted by session restarts; it has
completed 2 of 4 rows both times (n=4000 power 0.25, n=8000 power 0.42). The
finding it supports - that power rises with record length, reaching 1.00 at
40000 steps - was already established by the ad-hoc run and is recorded in the
log for 25 August. The scripted version is reproducible via
scripts/07 --length-scaling for anyone who wants the full curve.

### Phase 3 not started

Deliberately. The five requirements are set out in
research/phase3_design_implications.md and section 8 of the Phase 1-2 report.

---

## 26 August 2026 — Session record: Phase 1–2 closeout, and defining the project backward from its final product

This entry records an entire working session, per request, so that nothing
depends on the chat transcript surviving. Everything below is reproducible from
files in this repository.

### Why this entry exists at all

Working sessions are not permanent. The conversation gets summarised when it
grows too long, and the machine the work runs on is temporary — it is reclaimed
after inactivity and the working directory goes with it. Only what is committed
and pushed survives. `data/raw/` (about 9 GB) is deliberately not committed and
must be re-fetched with `scripts/01_download_dataset.py`, which verifies
SHA-256 checksums against the manifest. For a cold start, read
`reports/PHASE1_2_REPORT.md` and then this log.

### Part 1 — Phases 1 and 2 finished

The confirmatory analysis was run once against the design frozen at commit
`20db485` with two recorded amendments, and the result is negative. The full
account is in `reports/EWS_RESULTS.md` and `reports/PHASE1_2_REPORT.md`; the
short version is that the preregistered primary test was significant
(τ = +0.743, p = 0.0002) and is not interpretable as an early warning, because a
limitation recorded *in advance* — that the indicator was not flat across the
healthy baseline — turned out to explain it. The indicator's trend was in fact
steeper inside the healthy baseline (τ = +0.857, p = 0.0018, across blocks where
the participant was at 93–100% correct) than across the whole pre-transition
period.

Three independent lines of evidence converged on the same explanation: the
indicator is largely mean firing rate (R² = 0.707), which falls 56.5% across
T11's record; it is task-invariant (8.4% difference between a structured cursor
task and free web browsing recorded the same day, against a threefold range
overall); and T5 and T11 disagree in sign.

Loose ends tied off in this session: `reports/DATASET_EXPLORATION.md` sections 6,
9 and 10 were filled in from what the analysis established; procedures 32–40 were
added to `research/procedures.md`; `reports/figures/11_t11_why_negative.png` was
produced, stacking indicator, performance, and firing rate on one time axis with
the healthy baseline shaded, which is the entire result in one picture; and
`reports/PHASE1_2_REPORT.md` was written to consolidate all of it.

One thing remains genuinely unexplained and is recorded as such: **what drives
the indicator's rise during the healthy baseline.** Firing rate does not (its
baseline trend is not significant). `avgOutliers`, silent channels, and
low-variance channels were each tested and rejected as explanations. This is an
open question, not a solved one.

The length-scaling sweep has still never completed past 2 of 4 rows, having been
interrupted by session restarts twice. The finding it supports — that detection
power rises with record length, from 0.42 at 8,000 samples to 1.00 at 40,000 —
was established by an earlier ad-hoc run and is recorded in the 25 August entry.
Anyone wanting the full curve can run `scripts/07_ews_power_sweep.py
--length-scaling`.

### Part 2 — Reading the ISEF research plan form

The 2025-26 Research Plan form (aligned to page 2 of Form 1A) was supplied as a
`.docx` and read by unzipping it and stripping the XML, because `pandoc` is not
installed in this container. Its structure is: A Rationale; B Hypotheses /
Research Questions / Engineering Goals / Expected Outcomes; C Research Methods
(Materials, Procedures, Risk and Safety, Data Analysis, and an **Artificial
Intelligence disclosure**); D Bibliography with at least five formal references;
then conditional sections for Human Participants, Vertebrate Animals, Hazardous
Biological Agents, and Hazardous Chemicals/Activities/Devices.

Two things in the form matter more than the rest. It states at the top that
"the presentation of fraudulent data, the evidence of plagiarism, or the
inappropriate use of AI are prohibited and grounds for a project to be
disqualified," and it requires an explicit description of AI use. And the Human
Participants section requires SRC approval **before** experimentation begins,
with the plan fully developed at approval time — meaning the paperwork must start
long before the experiment runs.

### Part 3 — The project, redefined by working backward

The instruction was to determine what the final product actually is before
drafting any section, and explicitly not to assume the current idea was the best
version. That produced `research/PROJECT_DEFINITION.md`. The reasoning:

**The pilot exposed a problem deeper than a negative result.** In observational
data nobody knows when deterioration *began*. Onset is defined by the analyst
after the fact, so lead time is partly an artefact of that definition, and the
false-alarm rate cannot be estimated at all — there is no known-healthy stretch
of controlled length with no impending event. Lead time and false-alarm rate are
the only two numbers that decide whether a warning system is worth deploying, and
neither is measurable observationally.

**This makes the original experiment logically necessary rather than decorative.**
The central claim is uncheckable without a system in which the experimenter
controls and logs the onset of degradation in advance. That is the argument the
project needed, and it came out of the pilot's failure rather than being imposed
on it.

**Four project framings were compared.** The original early-warning-signal
detector came out weakest: its autocorrelation half is unmeasurable on this data
(measured, not assumed), and the mechanism the data actually shows — a monotonic
signal ramp into a saturating adaptive-normalisation compensator — is not a fold
bifurcation and does not generically produce critical slowing down. A broad
failure-prediction framework is better but generic and badly underpowered at
n = 2 participants, and it inherits the same missing ground truth. A multimodal
detector is directly argued against by the finding that mean firing rate alone
matches the full pipeline. The recommendation is the fourth: a **validated
decoder-health monitor plus the experimental system that establishes whether any
such monitor works.**

**The final product is three artefacts.** `decoder-guard`, a real-time monitor
reading the same feature stream the decoder reads, emitting a calibrated risk
score, a discrete state (`NOMINAL`/`WATCH`/`WARN`/`FAIL-LIKELY`), and an
attribution naming which failure mode is responsible — with `TASK-CHANGE` as an
explicit output class, because the pilot found the old indicator could not tell a
cursor task from web browsing. A degradation-controlled corpus recorded from a
closed-loop testbed with injected, pre-logged onsets. And a validation benchmark:
the five gates plus the lead-time/false-alarm curve, with three reference
baselines including MINDFUL, already reproduced exactly at r = 0.985.

**One methodological rule governs what may be simulated:** *the perturbation may
be simulated, the response to it may not.* Simulating the non-stationarity you
are trying to detect measures your own generative assumptions. Simulating the
human's compensation is impossible to do credibly, and that compensation is
precisely what the monitor must see through.

**Success criteria were set now, before anything is built**, and the silence gate
comes first in reporting order: an indicator that is not silent when the system
is healthy is not a detector, whatever its p-value. That sentence is what the
pilot bought.

Four decisions are left open on purpose and belong to the researcher: the signal
source (surface EMG with a human in the loop, versus a hardware replay rig,
versus both); how many failure modes; whether the impact demonstration is in
scope this year; and the performance-threshold rule for the original corpus,
which must be fixed before data collection. None of them should be settled by
asking which choice would look better in the results.

### Part 4 — The ISEF plan draft

`research/ISEF_RESEARCH_PLAN.md` maps the definition onto the form's structure.
It is a draft with every researcher-only field marked, and it flags three things
that need outside confirmation rather than assumption: the Rules Wizard must be
re-run once the signal source is chosen, because Form 3 may be required in
addition to Form 4 when an electronic device is attached to a person; the AI
disclosure must be re-checked against the 2026-27 rules; and whether sustained
muscle contraction counts as physical exertion is a question for the SRC, not one
to answer "no" by default.

The AI disclosure was written honestly and in two parts: AI as a research
assistant used for code, explanation, drafting and design criticism — with the
log, the version-controlled scripts, and the advance freeze offered as the record
that scientific decisions were the researcher's — and machine learning inside
the project's own system, which is an engineered component rather than a tool
used to produce results.

---

## 26 August 2026 (later) — Amendment 1, and the fault injector

### Amendment 1: no human participants

The researcher established that human participants are not available. Recorded
as **Amendment 1** in `research/PROJECT_DEFINITION.md` and
`research/ISEF_RESEARCH_PLAN.md` rather than silently rewritten, so that the
decision and its cost are both recoverable.

Struck: surface EMG (Configuration 2), Stage 3 of the staging table, ISEF Form 4,
SRC participant approval, consent forms, recruitment. The Human Participants
section of the ISEF plan is marked NOT APPLICABLE with a pointer to the commit
that still holds the drafted version.

Survives untouched: the ground truth for onset, which never came from the human —
it comes from the injection log. Also real non-stationarity, a real compensator
(the decoder's adaptive normalisation, which is software), recorded human
compensation already in the dataset, transfer testing, and H4 in offline form.

**The one real loss, now a stated limitation (§5.6):** injected episodes are
evaluated **open-loop**. A recording cannot adapt to a fault the way a live
person would, so the performance measure is the frozen decoder's output error
against the participant's real recorded intended direction, not closed-loop task
success. The two data sources are complementary and neither alone suffices:
recorded sessions have live compensation but unknown onset; injected episodes
have known onset but no compensation. Every claim must say which it rests on.

**What Amendment 1 promotes:** the hardware replay rig, from optional convenience
to the main defence against a specific circularity — if the monitor only ever
meets faults the researcher designed, passing the test partly measures the
researcher's imagination. Real hardware gives faults with **known onset but
undesigned signature** (loosened connector, thermal drift, induced interference).
Designed and undesigned faults are to be reported as separate result classes.
This is now the biggest open decision, replacing the former "EMG / rig / both".

### The fault injector — `scripts/17_fault_injector.py`

725 episodes over 29 T11 blocks. Three subcommands: `plan` draws the onsets and
writes them with a git commit hash and a SHA-256; `apply` can only read that
file; `verify` checks the injector before anything is scored with it. Re-planning
refuses to overwrite without `--amend REASON`, which preserves the superseded
checksum. Same discipline as `scripts/12_freeze_design.py`.

**The four modes were chosen to span one axis: visibility to mean activity.**
Phase 1–2 found mean firing rate alone matched the whole pipeline, so gate S4
("beat the trivial comparator") is only a real test if some faults are invisible
to it. Measured, relative to the untouched control on the same block:

| Mode | Change in mean activity vs control | Clipped |
|---|---|---|
| RATE_LOSS (severe) | **−51.3%** — mean activity sees it | 0% |
| CHANNEL_DROPOUT (severe) | −28.6% — partly visible | 0% |
| GAIN_DRIFT (severe) | **+4.3%** — near-blind, by construction | 0% |
| GEOMETRY_ROTATION (mild / severe) | **−1.1% / +2.8%** — near-blind | 3.1% / 4.7% |

`GAIN_DRIFT` centres its per-channel log-gains to zero mean, so it changes
relative scaling without changing the overall level. `GEOMETRY_ROTATION` uses
Givens rotations on disjoint channel pairs, which preserve the norm exactly —
pairs drawn only *within* a feature group, never across, because T11's matrix
concatenates threshold crossings with spike power and their scales differ by
orders of magnitude.

`clipped` is honest bookkeeping: these features are non-negative, rotation can
drive entries below zero, and flooring them is the physically correct choice. It
is also precisely the amount by which the mode falls short of being exactly
norm-preserving, so it is reported rather than hidden.

### Two things went wrong, both worth recording

**1. The `NONE` control skipped the diagnostics.** `apply_episode` returned early
for the control, so `verify` crashed with a `KeyError`. The crash was the good
outcome; the bad outcome would have been the control being the one episode nobody
checked. Fixed so every mode takes the same path.

**2. The naive diagnostic was contaminated, and the control is what exposed it.**
The first verification table measured "mean after onset vs mean before onset" and
reported **+15.6% for `NONE` — an episode that returns a bit-identical array.**
Nothing was wrong with the injector (the identity invariant passes). The block's
own activity genuinely drifts upward by ~15% within a single block.

That is the same class of error as the headline result of Phase 1–2: a
before/after statistic with a non-zero floor that has nothing to do with the
effect being measured. The fix is to report change **relative to the untouched
control on the same block**, which is what the verifier now does — the raw column
is still printed, labelled *(misleading)*, as a standing reminder.

**Worth carrying forward:** within-block drift of ~15% is a real property of this
data and a floor that any block-level statistic has to clear.

---

## 27 August 2026 — The reference decoder, and four bugs the corpus would have hidden

### The reference decoder — `scripts/18_reference_decoder.py`

The decoder exists only to **grade**: it turns a degraded feature stream into a
performance number, so "the monitor warned before performance fell" becomes
checkable. `decoder-guard` never looks at it. It needs exactly two properties —
better than chance on healthy held-out data, and frozen — and chasing accuracy
beyond that is explicitly not a goal.

It predicts the participant's intended direction (unit vector from cursor to
target) at each 20 ms bin, by ridge regression on the neural features. Fitted on
four healthy blocks (days 658, 665, 670), selected on two held-out healthy blocks
(671, 675). It never sees a degraded block.

| | median angular error |
|---|---|
| train | 32.5° |
| **held-out healthy** | **54.6°** |
| chance (shuffled pairing, measured not assumed) | 90.7° |

Better than chance by 36°. Property 1 passes.

**Worth noting for later:** the 22° gap between train and held-out is almost
entirely across-day change, not overfitting — ridge from 1e-1 to 1e4 barely moves
the held-out number. **Moving to a different day costs ~22° with no injected
fault at all.** That is the natural drift floor, and it constrains what
"performance dropped" can mean.

Normalisation is frozen at training. The real system used *adaptive*
normalisation, which Phase 1–2 identified as the compensator that masked
degradation until it saturated; freezing it here isolates degradation from a
compensator fighting it. Re-running with adaptive normalisation is a separate
condition, left as such rather than silently mixed in.

### Calibration: the severities were guesses, and now they are measurements

The design always specified two severity levels spanning a performance threshold
and deliberately declined to guess the numbers. `calibrate` supplies them by
sweeping severity against the frozen decoder.

**The performance threshold is fixed at +10° above an episode's own pre-onset
baseline**, set before any detector exists. Anchored by measurement: healthy
decoding is 54.6° and chance is 90.7°, so +10° consumes 28% of the distance from
healthy to useless, and is ~40× the control's own drift (+0.24°).

Final calibrated levels, with measured degradation vs control:

| Mode | benign | sub | crossing |
|---|---|---|---|
| RATE_LOSS | 0.10 → +0.3° | 0.25 → +5.0° | 0.55 → +24.5° |
| CHANNEL_DROPOUT | 0.05 → +2.7° | 0.30 → +11.1° | 0.60 → +24.1° |
| GAIN_DRIFT | 0.20 → +1.1° | 0.50 → +7.1° | 1.20 → +21.5° |
| GEOMETRY_ROTATION | 0.15 → **−11.0°** | 0.45 → +7.3° | 1.20 → +31.1° |

`benign` is a new level: a real change to the data that does **not** degrade
decoding. A monitor should notice the change but must not call it a failure.
These are false-alarm material alongside `NONE`. The corpus is now 1073 episodes.

**Mild rotation improves decoding by 11°, consistently across seeds.** Mixing
correlated channels appears to average away noise for this heavily-regularised
decoder. It is kept precisely because it is a hard negative — a large, real change
in the neural statistics with no performance cost.

### Four bugs, all found by verification, all of which would have corrupted results

**1. `CHANNEL_DROPOUT`'s severity ladder ran backwards.** Measured damage went
+22.6° at severity 0.15, **−6.2° at 0.30**, +26.8° at 0.60. The cause: each
severity drew a *fresh* random channel set sized by severity, so levels were
independent draws rather than nested — severity 0.30 hit a different set than
0.15, not a superset, and some sets happened to spare channels the decoder leans
on. Fixed by drawing one permutation and taking the first k channels, so a more
severe episode kills a superset. Now monotone.

**2. One seed was never enough.** Averaging over five seeds shows the spread is
enormous: **sd ≈ 13° for `CHANNEL_DROPOUT` at low severity, against a mean of
2.7°.** Losing 5% of channels is harmless or ruinous depending on *which* channels
die. This is realistic — real arrays lose specific units — and it has a design
consequence: severity labels are the *design intent*, and whether a given episode
actually crossed the threshold must be determined per episode by measurement.

**3. `GAIN_DRIFT` was not mean-preserving, twice.** Its whole purpose is to be a
fault that mean activity is blind to, so that gate S4 is a real test. Centring the
*log*-gains preserves the geometric mean; at the severity that actually degrades
decoding, mean activity rose **+116%**. Rescaling by the pre-onset channel profile
fixed most of it but still left **+20.8%**, because the block's own activity
drifts ~15% within a block and a profile measured before onset no longer describes
the data after it. The working fix normalises against the current bin: total
activity per bin is conserved exactly, only the distribution across channels
changes. Now **−2.4%** at crossing severity — a fault that wrecks decoding while
being invisible to counting spikes, which is exactly what S4 needs.

**4. The pre-onset guarantee held only by rounding.** Several modes compute a
scale factor that is algebraically 1.0 before onset but differs in the last bits
of floating point. That surfaced as `pre-onset intact: NO`. It matters more than
it looks: if the ramp leaked backwards at all, a detector could "warn" by sensing
the leak, and the measured lead time would be an artefact of the injector rather
than a property of the detector. Pre-onset rows are now restored exactly, for
every mode, by construction.

### One honest limitation of the corpus

`GEOMETRY_ROTATION` at crossing severity (1.2 rad ≈ 69°) drives **17% of entries
below zero**, which have to be floored because these features are non-negative.
That flooring costs 18% of mean activity, so at the severity where rotation
finally degrades decoding it is **no longer invisible to mean activity**, and
stops being a clean S4 test.

Stated plainly: *on this decoder, a geometry change large enough to hurt
performance is also large enough to change overall activity.* `GAIN_DRIFT` is
therefore the primary S4 mode, and rotation's clipping fraction is reported with
every result rather than hidden.

### Plan status

Three amendments recorded, each with its reason and the superseded checksum. All
three predate any detector — nothing has yet been run against this corpus, which
is the ordering the whole design depends on.

---

## 27–28 August 2026 — The grading system, and the monitor

### Order of construction, on purpose

The grading system was built and committed **before** the monitor existed. If a
detector comes first and the metric second, the metric gets chosen — usually
without anyone noticing — to flatter the detector. Phase 1–2 lost a headline
result to exactly that family of mistake. At the moment `scripts/20` and
`scripts/21` were committed, the only detectors they could score were three
baselines, none of which this project invented.

`scripts/22` (the monitor) was then written and committed **while the baseline
scores were still being computed**, so its design could not be tuned against
numbers it had not seen.

### The detector contract — `scripts/19_detectors.py`

A detector sees only the feature stream. Never the decoder's output, the task,
the performance number, or any degradation label. Fitted on healthy windows
alone. `fit(healthy) → score(windows)`, one number per window, higher = less
healthy. Everything else — calibration, thresholds, states, lead time — belongs
to the harness. Keeping that boundary sharp is what makes baselines and the
monitor comparable: they differ in exactly one function.

Three baselines, implemented to the same standard because "did it beat something
trivial?" is the question that decides whether any of this was worth building:

- **`mean_activity`** — counting spikes. Not a straw man: in Phase 1–2 this
  matched the entire sophisticated pipeline (ρ = −0.880 vs +0.858). It is the
  incumbent.
- **`robust_dispersion`** — the Phase 1–2 indicator, reimplemented at window
  level. A project should be able to say what its own earlier attempt scores
  under its own later test.
- **`distribution_shift`** — distance to a healthy reference, in the spirit of
  the published MINDFUL measure reproduced at r = 0.985 in `scripts/09`.

### The harness — `scripts/20`, `scripts/21`

30-second windows stepped every 5 seconds. Per-window angular error through the
frozen decoder. The performance event stays at +10° above each episode's own
pre-onset baseline, as fixed in `scripts/17` before any detector existed.

A state machine with **dwell and hysteresis**, because a monitor that chatters is
one people learn to ignore — a failure mode that never appears in an accuracy
number. Splits are fit / val / test by block: detectors fitted on healthy windows
from the decoder's training days, the single free parameter (the WARN threshold)
chosen on the held-out healthy days, and the test split read once.

**Lead time and false-alarm rate are always reported as a pair.** A detector that
warns instantly on everything has infinite lead time and is useless; one that
never warns has a perfect false-alarm rate and is useless.

One decision worth recording: **a warning raised before the fault even started is
counted as a false alarm, not as a very early detection.** Counting it the other
way would be the most flattering possible error, and it is the error a careless
harness makes by default.

### The monitor — `scripts/22_decoder_guard.py`

Phase 1–2's failure was that a sophisticated indicator turned out to be 71%
"how much activity is there" — a quantity that falls steadily whether or not
anything is wrong. So the monitor does not produce one opaque number. It computes
four named quantities, calibrates each against healthy data, reports the largest
as the risk, and names which one it was:

| Component | Meaning | Expected to fire on |
|---|---|---|
| `level` | total activity has moved | RATE_LOSS |
| `silence` | individual channels have gone quiet | CHANNEL_DROPOUT |
| `dispersion` | channels drifted apart in gain, total unchanged | GAIN_DRIFT |
| `profile` | the shape across channels changed | GEOMETRY_ROTATION |

**The load-bearing trick is working in logs.** A multiplicative gain change is an
*additive* shift in log space, so subtracting each window's mean log activity
removes any uniform gain change exactly. What survives is a change in the profile
across channels — precisely the part counting spikes cannot see. `level` is kept
as its own component so uniform faults are still caught, but caught *and
labelled* as uniform.

The expected fault → component mapping was written into the file **in advance**,
so attribution accuracy is scored against a stated prediction rather than
whatever mapping happens to fit the results.

### Three bugs in the monitor, all found by smoke-testing before the real run

1. **Risk scores of 3 × 10⁸.** The `silence` component is flat at zero across all
   healthy windows, so its MAD is ~0 and calibration divided by it. Components
   now carry a floor stating what counts as a *meaningful* amount in their own
   units, rather than letting the healthy data's own noise set the unit.
2. **`GAIN_DRIFT` mis-attributed as `CHANNEL_DROPOUT`.** The silence threshold was
   15% of a channel's healthy median, which ordinary gain reduction routinely
   crosses. Tightened to 2% — injected dropout sets channels to exactly zero, and
   reaching 2% by gain drift needs a >3σ excursion.
3. **Attribution collapsed onto the least informative component.** `profile` was a
   *squared* Mahalanobis distance, growing quadratically and swamping everything,
   so `max` always chose it. Now a distance rather than a squared distance — and
   attribution prefers the most **specific** sufficiently-lit component rather
   than the largest. The components form a specificity hierarchy (`silence` has
   essentially one physical cause; `profile` is a residual by design), and
   preferring a named diagnosis over "abnormal findings" when both fit is
   ordinary diagnostic reasoning.

After those fixes, three of four fault types attribute correctly on a synthetic
check. `GEOMETRY_ROTATION` attributes to `dispersion` rather than `profile` —
a genuine physical ambiguity, since mixing channels does spread the log-profile.
**Left uncorrected on purpose**, to be measured on the real corpus rather than
tuned against a synthetic test.

---

## 28 August 2026 — First benchmark results, and they are negative

### Condition A: a reference fitted once and deployed

Detectors fitted on healthy windows from the decoder's own training days
(658, 665, 670), then applied unchanged across the whole record. This is what a
naive monitor does: calibrate at install, then run.

**Every detector fails.**

| Detector | Median lead | Detection | False alarms/h | Budget |
|---|---|---|---|---|
| `decoder_guard` | **−5.0 s** | 175/586 | **18.1** | 0.1 |
| `mean_activity` | **−10.0 s** | 137/586 | **2.4** | 0.1 |
| `robust_dispersion` | **−30.0 s** | 11/586 | 0.20 | 0.1 |
| `distribution_shift` | — | — | — | **no operating point exists at all** |

Negative lead time means the monitor warns *after* performance has already
fallen. That is not an early-warning system; it is a delayed confirmation.

Gates, on healthy test episodes:

| Gate | `decoder_guard` | `mean_activity` | `robust_dispersion` |
|---|---|---|---|
| G1 silence | **FAIL** (87% of healthy episodes trend) | **FAIL** | **FAIL** (85%) |
| G4 elapsed time | **FAIL** (ρ=0.74) | **FAIL** | **FAIL** (ρ=0.73) |
| G2 rate invariance | PASS (ρ=0.40) | n/a | PASS (0.57) |
| G5 detrend | **PASS** (4.5%) | — | FAIL (11.7%) |

### G5 is the diagnosis

`decoder_guard`'s silence-gate failure drops from **87% of healthy episodes to
4.5%** once a linear trend is removed. So the failure is **monotonic drift, not
noise**.

That is the whole explanation. The array genuinely changed over 142 days — Phase
1–2 measured mean firing rate falling 56.5% — so a reference taken on day 658 and
applied on day 800 is measuring *months of real change*, not the injected fault.
The monitor is not broken. It is answering a question nobody asked.

### Attribution collapsed too

Only **two of four** components were ever named, and overall accuracy was 26%
against a 25% chance rate. `dispersion` claimed almost everything, including
145/149 channel-dropout episodes. The reason is the same drift: dispersion is
chronically elevated against an old reference, so the specificity rule keeps
selecting it. **A component that never fires is not a subtle failure** — it means
attribution has collapsed onto whatever is permanently lit.

### Why this is reported rather than quietly replaced

"Calibrate once and deploy" is what a naive monitor does, and showing precisely
how it fails — with the gate that isolates the cause — is worth more than
skipping to the version that works. It also makes the fix principled rather than
convenient: the reference must be **local**, because the question is "has
something changed relative to recent normal", not "does today look like install
day".

Condition B (local re-baseline: shape global, centre and scale re-estimated from
each episode's own pre-onset windows, causally) is running next.

### Two report bugs fixed

- NumPy booleans leak through Python's `and`, so the gate results were not
  JSON-serialisable and the summary file never got written.
- Attribution chance was computed over the components that *happened to appear*
  rather than the components the monitor *can emit* — which flattered a
  collapsed attribution into looking like a coin flip instead of chance.

### T5 is ready as a transfer test

T5's reference decoder is fitted (47.9° held-out healthy against 72.7° chance)
and its injection plan is drawn: 777 episodes over 21 blocks, 192 features
against T11's 384. The dimensionality difference is the point — nothing in the
design may assume 384.

**T5's chance level is 72.7°, not 90°**, because its target directions are not
uniformly distributed. Measuring chance rather than assuming it is what caught
that; a hard-coded 90° would have overstated the decoder's margin by 18°.

---

## 28 August 2026 — The full benchmark: 36 configurations, none passes

### What was run

Four detectors × two baseline strategies × three causal transforms × two
participants. Every configuration is in `reports/BENCHMARK_SUMMARY.md`, including
the ones that failed and the fifteen that could not find an operating point at
all.

Reporting the whole grid rather than a best row is the point. A best row selected
after the fact from a grid is not a result — it is the maximum of a set of noisy
numbers.

| | count | of 36 |
|---|---|---|
| Found any operating point at all | 21 | 58% |
| Achieved a **positive** median lead time | 5 | 14% |
| Met the false-alarm budget (≤0.1/h) | 1 | 3% |
| Passed the silence gate | **0** | **0%** |
| **Passed all five gates** | **0** | **0%** |

### The finding, stated precisely

**The binding constraint is not detection.** Five configurations do warn before
performance falls — T5's `robust_dispersion` reaches **+57.5 s median lead
(95% CI 2.5–82.5)**, and T11's `mean_activity` under a trailing reference reaches
+15 s.

**The binding constraint is specificity.** The risk signal is never quiet during
healthy operation. Any threshold low enough to catch a fault early also fires
constantly on healthy record. Only one configuration in 36 met the false-alarm
budget, and it had a *negative* lead time — it was quiet because it barely fired.

The closest approach to the silence gate is **31% of healthy episodes still
trending, against a 10% requirement** (`decoder_guard`, T11, calibrate-once
baseline, trailing transform).

### What the three transforms established

- **none** — 80–98% of healthy episodes trend. Hopeless.
- **detrend** — the prespecified fix, and it **does not work**. On T5 it made the
  silence gate *worse*, 63% → 81%. The reason is instructive: a line fitted on
  pre-onset windows and extrapolated forward accumulates error with distance, so
  on drift that is not exactly linear it *adds* a trend to the far end. Removing
  the trend requires knowing the whole series, which a live monitor cannot do.
- **trailing** — comparing each window against a short sliding reference of the
  recent past is the only transform that helps, roughly halving the failure rate
  (87% → 31%). It is causal and needs no model of how drift should behave. It
  still does not come close to passing.

The prespecified fix failing is recorded as a result, not quietly replaced. It
was written into `phase3_design_implications.md` on 26 August, it was run, and it
failed — that ordering is the whole value of writing it down first.

### Why this is a real result rather than a dead end

The project was designed so that this outcome is reportable, and Phase 1–2 was
the proof that a negative finding would actually be reported. The contribution
here is not a working detector. It is:

1. **A benchmark that did not previously exist** — 1,073 + 777 fault episodes
   with known onset, four fault types spanning visibility to the trivial
   comparator, and a stated performance threshold.
2. **A test battery** — five gates, applied in a fixed order, with silence first.
3. **Systematic evidence** that neural-instability measures — including the
   published MINDFUL-style measure reproduced at r = 0.985, and a purpose-built
   monitor — cannot warn early at a usable false-alarm rate on chronic iBCI data.
4. **A diagnosis of why**: the neural statistics change continuously, at a
   magnitude comparable to the injected faults, for reasons unrelated to failure.
   Within-block drift alone is ~15%; across 142 days mean firing rate falls 56.5%.

### Honest limitations of this benchmark

- **Open-loop.** Injected episodes cannot include a human adapting, so the
  performance measure is decoder output error rather than task success.
- **Two participants.** T5 and T11 disagreed in Phase 1–2 and disagree here.
- **`GEOMETRY_ROTATION` at crossing severity** clips 17% of entries and loses 18%
  of mean activity, so it is not a clean test of the trivial-comparator gate.
  `GAIN_DRIFT` carries that role.
- **Attribution reached 52% against 25% chance on T5**, but only 3 of 4
  components were ever named — the fourth never fires, which means attribution
  is partly collapsing onto whatever is chronically lit.
- **The trailing reference has two unfitted constants** (window length, gap).
  They were set once, not swept, precisely to avoid turning the transform into
  another grid to search.

### Figure

`reports/figures/12_baseline_conditions.png` — three panels sharing a detector
axis: median lead time, false alarms per hour on a log scale, and the fraction of
healthy episodes that trend. No dual axes: lead time and false alarms have
different units and opposite senses of "good", and the tradeoff between them is
the finding, so it stays visible as two panels rather than being collapsed into
one score.

---

## 28 August 2026 — The task-change test, and the first clean positive

### The question no accuracy number answers

A monitor that fires whenever the user switches from a typing app to browsing the
web is **worse than no monitor** — it trains its user to ignore it. Nothing in the
injected-fault corpus tests this, because there the task never changes.

The dataset happens to contain the exact control needed. On two days T11 did the
structured cursor task **and** something completely different, same day, same
array, nothing wrong with the recording:

| Day | Cursor task | Also did |
|---|---|---|
| 658 | circleOfCircles | free personal use — web browsing |
| 665 | circleOfCircles | fitts — random targets |

Three reference points make the answer interpretable: same task healthy (what
normal looks like), **different task healthy** (the thing under test), and same
task with an injected crossing-severity fault taken from the locked plan (what a
real fault looks like). The question is which extreme the middle one resembles.

### Result

**Day 658 — cursor task vs web browsing**

| Detector | same task | different task | real fault | verdict |
|---|---|---|---|---|
| **`decoder_guard`** | 11.16 | **8.67** | 135.35 | healthy — **15.6× separation** |
| `mean_activity` | 1.49 | 1.72 | 3.82 | healthy |
| `robust_dispersion` | 0.14 | **0.46** | 0.29 | **would false-alarm** |

**Day 665 — cursor task vs random targets**

| Detector | same task | different task | real fault | verdict |
|---|---|---|---|---|
| **`decoder_guard`** | 1.14 | **1.98** | 138.00 | healthy — **70× separation** |
| `mean_activity` | 0.52 | 2.05 | 36.06 | healthy |
| `robust_dispersion` | 0.80 | 0.88 | 86.28 | healthy |

**`decoder_guard` separates "the user is doing something different" from "the
hardware is failing" by 15× and 70×.** On day 658 a task change actually scored
*lower* than the same task. This is the first thing in the project that has
cleanly worked.

`robust_dispersion` fails day 658: a healthy task change scored **higher** than a
real fault. A monitor built on it would alarm on app switching and stay quiet on
degradation — precisely inverted.

### Why this matters more than it looks

Phase 1–2 found the old indicator was *task-invariant* — 8.4% difference between
the cursor task and web browsing — and reported that as evidence it tracked the
recording rather than the task. That was the right reading, but it left the
reverse question open: does a monitor sensitive enough to catch faults become
sensitive to behaviour instead? For `decoder_guard`, measured here, it does not.

It also isolates *where* the project's difficulty actually lies. The monitor is
not confused by what the person is doing. It is defeated by **slow drift in the
recording itself** — which is exactly what the 36-configuration benchmark showed
and what the silence gate keeps failing on. Those are different problems, and one
of them is now demonstrably solved.

### Limitations, and they are real

- **Two days, four comparison blocks.** This is a demonstration, not an estimate.
  No confidence interval is quoted because none would be meaningful at this n.
- The fault reference is a *single* crossing-severity episode per block, averaged
  over two rate settings, not a distribution.
- Personal-use blocks have no cursor task, so there is no performance measure to
  cross-check against — only risk.
- Both comparisons are within-day. A task change on a *different* day would
  confound task with drift, which is the very thing the monitor cannot handle.

**Reproduce:** `python3 scripts/25_task_change_test.py`

---

## 28 August 2026 — Achievability: the information IS there, and this reframes everything

### The question a judge would ask

The benchmark says no configuration passes. The obvious challenge: *is early
warning impossible on this data, or did you just fail to find the right
detector?* Those are different claims and the difference is measurable.

Strip away every threshold, state machine, dwell and hysteresis setting. Ask only
whether a single window's raw score can separate **the early-warning interval** —
after a fault started, before performance dropped — from healthy recording. That
is one number: the area under the ROC curve. Chance is 0.50.

### The answer

| Condition | `decoder_guard` early AUC | `mean_activity` | `distribution_shift` |
|---|---|---|---|
| T11, calibrate once | **0.491** *(chance)* | 0.514 | 0.541 |
| **T11, recent normal** | **0.693** | 0.611 | 0.666 |
| **T5, recent normal** | **0.707** | 0.612 | 0.661 |

Two things follow, and both matter.

**1. With a global baseline the information genuinely is not there.** AUC 0.49 —
chance. That is not a shortfall of effort; the drift swamps the fault, and no
threshold scheme can recover what is absent. The earlier framing of that
condition as "calibrate once and deploy fails" is now backed by a bound.

**2. With a local baseline the information IS there.** AUC 0.69–0.71, on both
participants. **So the failure reported in the 36-configuration benchmark is not
a limit of the data — it is in the machinery that turns scores into warnings.**
That is a fixable engineering problem, and saying so is only honest because it
was measured rather than hoped.

I want to be explicit that this **revises the emphasis of the previous entry**.
"The constraint is specificity" remains true of the deployed system. But the
sharper statement is: *the signal carries usable information about the fault
before performance drops; the thresholding and state machinery cannot yet exploit
it without also firing on healthy drift.*

### `decoder_guard` beats every baseline, replicated

0.693 vs 0.611 on T11; 0.707 vs 0.612 on T5. A margin of ~0.09 AUC over counting
activity, in the same direction on two participants who disagreed in Phase 1–2.
**Gate G3 — beat the trivial comparator — is satisfied at the information level**,
even though the deployed benchmark fails.

### And it wins exactly where it was designed to

This is the design rationale made checkable. `decoder_guard` separates a uniform
change in activity from a change in the *shape* of activity, so it should beat
counting on the faults that leave overall activity unchanged, and lose on the
fault that is nothing but overall activity:

| Fault | decoder-guard (T11 / T5) | counting activity (T11 / T5) |
|---|---|---|
| overall signal loss | 0.61 / 0.64 | **0.80 / 0.78** |
| electrodes dying | 0.65 / 0.75 | **0.73 / 0.77** |
| **channels drifting apart** | **0.79 / 0.73** | 0.41 / 0.40 *(below chance)* |
| **signal shape rotating** | **0.76 / 0.71** | 0.52 / 0.51 *(chance)* |

Counting activity is **at or below chance** on both faults that conserve total
activity — exactly as constructed — while the monitor is at 0.71–0.79. The
pattern replicates across participants. `reports/figures/13_auc_by_fault_mode.png`.

This is the strongest evidence the project has that the monitor is doing
something real rather than restating firing rate.

### Caveats

- AUC pools windows, so episodes contribute unequally and windows within an
  episode are correlated. The p-values are therefore not to be read as
  independent evidence; the effect size is the number that matters.
- The early window is defined by the crossing time, which is itself measured, so
  a noisy crossing shifts the boundary. Late AUC (0.81–0.82) is reported beside
  it as the sanity check that damage is easier to see than to anticipate.
- `NONE` episodes that "crossed" score **below** chance (0.36–0.47). These are
  performance excursions with no fault behind them. Small in number, but they are
  a reminder that the performance threshold itself has a false-positive rate.
- Two participants. Replication across two is much better than one, and is still
  two.

**Reproduce:** `python3 scripts/26_achievability.py`

---

## 28 August 2026 — A correction, and the tradeoff made precise

### The correction

The previous entry reported that **15 of 36 configurations could not find a
usable operating point.** That was wrong, and it was a bug in this harness rather
than a property of the detectors.

`THRESHOLD_GRID` stopped at **59**. Observed scores reach **300**
(`decoder_guard`) and **3200** (`distribution_shift`). So "no operating point
exists" actually meant "none exists below a number I chose arbitrarily", and it
was presented as the former.

With the grid spanning the range the scores occupy — fine steps below 10,
log-spaced to 1e4 above — **47 of 48 configurations find an operating point.**
`reports/BENCHMARK_SUMMARY.md` carries the correction inline rather than quietly
displaying different numbers.

**What the correction does not touch, checked rather than assumed:** neither the
silence gate nor the achievability AUCs reference a threshold anywhere in the
code (verified by grep, recorded here). Those results stand exactly as reported.

### The corrected headline

| | count | of 48 |
|---|---|---|
| Found any operating point | 47 | 98% |
| **Positive** median lead time | 10 | 21% |
| Met the false-alarm budget (≤0.1/h) | 3 | 6% |
| **Passed the silence gate** | **0** | **0%** |
| **Passed all five gates** | **0** | **0%** |

The headline is unchanged: nothing passes. What changed is that the failure is
now cleanly attributable to the silence gate rather than partly to an artefact
of my own search.

### The tradeoff, now precise — and a trap in the table

One configuration **meets the false-alarm budget with a positive lead time**:
T5, recent-normal baseline, trailing transform, robust dispersion — **+115 s at
0.075 false alarms per hour.**

It detected **1 fault out of 219.**

That is not a fast detector. It is a near-silent one that happened to fire early
once, and in a table of lead times it would read as the best result in the
project. The summary now marks any lead time computed from fewer than 5% of fault
episodes with a warning symbol, and reports detection rate as its own column,
because the two are otherwise indistinguishable at a glance.

Stated as a rule, which is the actual finding:

> **Across the whole grid a configuration either detects a meaningful share of
> faults and false-alarms far past budget, or meets budget and barely fires at
> all. There is no middle of this curve in the data as it stands.**

T11's best-detecting configurations sit at 275–284 detections out of 586 — but at
15–20 false alarms per hour, 150–200× over budget. The two ends of the curve are
both useless, in opposite directions.

### Why this is consistent with the achievability result rather than contradicting it

The information is present (AUC 0.69–0.71). The curve above is what happens when
information of that strength is pushed through a single global threshold: an AUC
near 0.7 simply does not support a 0.1/h operating point at useful sensitivity.
The two findings agree, and together they say what the next engineering step must
be — **not a better feature, but a decision rule that does not reduce to one
threshold on one number.**

### A fourth transform, and it does not rescue anything

`prez` — express each window in units of the episode's own pre-onset spread —
was added because the achievability result located the failure in the
score-to-warning step, and an absolute threshold against a per-episode-varying
scale is one concrete reason that step fails. It raises detection sharply
(284/586 on T11, the highest in the grid) and raises false alarms with it
(20.3/h). It is reported alongside the others, not instead of them.

---

## 28 August 2026 — A prediction recorded in advance, and falsified

### The diagnosis was right

`decoder_guard` reports the **largest** of its four components as the risk.
Measuring which component gets named, healthy versus during the early-warning
window on T11:

| Component | Healthy | During fault | Ratio |
|---|---|---|---|
| **`profile`** | **40.6%** | **5.4%** | **0.13** |
| `silence` | 7.8% | 13.6% | 1.75 |
| `dispersion` | 33.8% | 56.0% | 1.66 |
| `level` | 17.9% | 25.0% | 1.40 |

A high `profile` reading is evidence **against** a fault. It is the signature of
ordinary drift — which is precisely what a residual catch-all component should
absorb — and the `max` rule scores it as risk anyway. That finding stands.

### The fix, and the trap deliberately avoided

The obvious move is to down-weight `profile` using that table. **That was not
done.** Those numbers come from fault labels, and hand-weighting with them would
quietly convert a one-class detector into a supervised one whose validation stops
meaning anything.

Instead the four components were modelled **jointly** on healthy data alone —
mean and covariance of the log-compressed 4-vector, then Mahalanobis distance.
Healthy drift has a characteristic joint signature, so the model should learn it
as normal without ever seeing a fault.

### The prediction, written down before the results existed

`research/DETECTOR_V2_RECORD.json`, committed at `9c1279e` while both harness
runs were still in flight and the results files untouched:

> *"Modelling the four components jointly, rather than taking their maximum, will
> reduce the false-alarm rate at matched detection, because healthy drift has a
> characteristic joint signature that a max rule cannot represent."*

Falsification criterion, recorded at the same time: *no reduction in false alarms
at matched detection, or a silence gate no better than v1.*

### The result on T5: falsified

| | Detection | False alarms | Silence gate |
|---|---|---|---|
| `decoder_guard` v1 | 6/219 | **3** (0.225/h) | 100% fail |
| `decoder_guard_joint` | 6/219 | **5** (0.376/h) | 98.7% fail |

Detection is **exactly** matched at 6/219, and false alarms went **up**, 3 to 5.
The silence gate moved from 100% to 98.7% of healthy episodes trending, which is
not an improvement in any meaningful sense.

Both halves of the falsification criterion are met on this participant. The
prediction is wrong, and it is recorded as wrong.

### Why it is worth having done anyway

The diagnosis and the remedy are separable, and only the remedy failed. It is
still true that `profile` fires overwhelmingly on healthy record and rarely on
faults. What is now known, and was not before, is that **a joint Gaussian model
of the four components does not capture that structure well enough to exploit
it** — plausibly because with local re-baselining the joint covariance is
estimated from roughly 25 pre-onset windows, or because the healthy-drift
signature is not stable enough from episode to episode to be modelled as a fixed
shape.

That is a more specific negative than "it didn't work", and it points somewhere:
the useful information is in *which* component fires rather than in the joint
geometry of all four, and exploiting that without using labels is the open
problem.

### T11 returned, and it says the opposite

| T11 | Detection | False alarms | Silence gate |
|---|---|---|---|
| `decoder_guard` v1 | 143/586 | 69 (3.407/h) | 98.1% fail |
| `decoder_guard_joint` | **177/586** | **62 (3.061/h)** | 97.4% fail |

On T11 the joint model **detects more faults *and* raises fewer false alarms**.
That is dominance on both axes at its own operating point, which is a stronger
result than the prediction asked for — the prediction only claimed a reduction at
*matched* detection, and this beats it without needing the match.

### The verdict: it does not replicate, so it is not adopted

| | Prediction | Outcome |
|---|---|---|
| **T11** | fewer false alarms at matched detection | **Satisfied, and exceeded** — dominates on both axes |
| **T5** | fewer false alarms at matched detection | **Falsified** — detection exactly matched, false alarms rose 3 → 5 |

**A change that helps one participant and hurts the other is not an improvement,
and `decoder_guard_joint` is therefore not promoted over v1.** Both are kept and
both are reported. Neither passes the silence gate — 97.4% and 98.7% of healthy
episodes still trend — so the headline is untouched either way.

### This is the project's central limitation showing itself again

T5 and T11 disagreed in sign in Phase 1–2. They disagree again here. That is now
a consistent, replicated property of this dataset rather than an oddity of one
analysis, and it is the strongest argument in the project for why **n = 2 is not
enough** and why a third participant is the single most valuable thing that could
be added.

It also means any "improvement" measured on one participant in this dataset
should be treated as unproven until it is shown on the other. That rule is cheap
to state now and would have been expensive to learn later.

### What survives from this episode

1. **The diagnosis**, which is unaffected: `profile` fires 40.6% on healthy
   record and 5.4% during faults. The `max` rule scores drift as risk.
2. **A more specific negative**: a joint Gaussian over the four components
   captures that structure well enough to help on one participant and not the
   other, which places it firmly in "not robust" rather than "wrong".
3. **A method rule**, earned rather than assumed: single-participant improvements
   in this dataset do not count.
4. **A worked example of the full loop** — measure a mechanism, predict, record
   the prediction with a checksum before the results exist, run, report the
   split honestly, and decline to adopt the change.

---

## 28 August 2026 — Attempting a third participant, and what blocks it

### Why this was attempted

The T11/T5 disagreement on the joint detector makes **a third participant the
single most valuable addition available to this project** — more valuable than a
better detector, because with n = 2 an improvement cannot be told from noise.

### What was found

Dryad's **metadata** API is readable without credentials. Two candidates, sizes
confirmed from the live API rather than guessed:

| Deposit | Size | Value |
|---|---|---|
| **Card et al. 2024 — T15, speech neuroprosthesis** `10.5061/dryad.dncjsxm85` | 11.6 GB | **A genuine third participant.** 256 electrodes, 45 sessions Aug 2023 – Apr 2025, a completely different task. Different implant, different task, different feature dimensionality — exactly the generality test the design calls for. |
| Fan et al. 2023 — T5, one year `10.5061/dryad.hqbzkh1p6` | 3.6 GB | Same participant as the existing T5, but **self-recalibrating by design**. A contrast condition, not a new case. |

The T15 neural data is a single 11.05 GB zip and cannot be subset. There are two
small pickles (57.8 MB and 1.1 MB) that were worth probing first.

### What blocks it

**Downloads require OAuth credentials, which did not survive the container
restart.** Both routes were tried and both are closed:

- `api/v2/files/{id}/download` → **HTTP 401**
- `downloads/file_stream/{id}` → HTTP 200 but returns the **anti-bot challenge
  page**, not the file. This is the same Anubis challenge documented in
  `DATASET_README.md` §7 for the primary dataset, and `scripts/01` already
  rejects an HTML doctype for exactly this reason.

No attempt was made to work around the challenge. It is there deliberately, and
Dryad publishes an authenticated API that is the correct route.

### What was done instead

`scripts/01_download_dataset.py` now takes `--doi`, so once
`DRYAD_CLIENT_ID` and `DRYAD_CLIENT_SECRET` are present in the environment, a
third participant is one command:

    python3 scripts/01_download_dataset.py --doi 10.5061/dryad.dncjsxm85

The candidate DOIs and the reasoning above are recorded in the flag's help text,
so the option does not need this log entry to be usable.

### Honest cost estimate before anyone commits to it

- **11.6 GB download**, plus unzip. Free disk was 29 GB at the time of writing,
  so it fits, but not with room to spare.
- **A new loader.** T15's format is unrelated to the `.mat` structure the current
  loader handles, so `scripts/03` will not read it.
- **No cursor task**, therefore no angular error and no reference decoder. Lead
  time as currently defined would not be computable.

**But the silence gate needs none of that.** It requires only healthy neural
recordings and the monitor, and it is the gate every configuration currently
fails. Running it on a third participant with a different implant and a different
task would establish whether that failure is a property of *these two arrays* or
of *the approach*. Those are very different conclusions and the test is cheap
once the data is loadable.

That is the recommended next experiment, and it is now blocked only on
credentials.

---

## 28 August 2026 — The decision rule is not the bottleneck, and here is what is

### A correction to the previous entry

The achievability analysis measured AUC 0.69–0.71 in the early-warning window and
I concluded from it that **"the failure is in the machinery that turns scores
into warnings — a fixable engineering problem."**

**That was wrong.** Testing it refutes it.

### Comparing decision rules by their whole curve, not one operating point

Three rules, sweeping the free parameter and plotting detection against false
alarms — the only honest comparison, because a single operating point can hide
behind a favourable threshold:

- **threshold** — the existing rule
- **CUSUM** — accumulate excess evidence over time, alarm on the total. The
  textbook answer to weak per-sample evidence about a change that persists. Its
  slack `k` is estimated causally per episode rather than searched, so both
  rules expose exactly **one** searched parameter and the comparison is like for
  like.
- **CUSUM + specificity gate** — suppress a warning while the monitor's own
  named cause is `profile`, the residual catch-all.

**Detection achievable inside the false-alarm budget:**

| Rule | T11 | T5 |
|---|---|---|
| threshold | 0.0% | 0.8% |
| cusum | 0.0% | 0.3% |
| cusum+spec | 0.0% | 0.3% |

The rule makes no difference. All three are at zero.

A caution learned here: at its chosen operating point CUSUM detects **221** faults
to the threshold rule's **143**, but shows a *later* median lead time. That looks
like a loss and is not — the extra 78 detections are cases the other rule missed
entirely, and they are the hard, late ones. Adding hard cases drags a median
down. **Single-point comparisons of detectors are actively misleading**; the
curve is the only fair view.

### What the bottleneck actually is — arithmetic, not effort

The budget is 0.1 false alarms **per hour**. The monitor decides every **5
seconds** — 720 decisions an hour.

| | T11 | T5 |
|---|---|---|
| Healthy windows in test | 17,014 | 17,337 |
| Alarms the budget permits | 2.4 | 2.4 |
| **Required per-window false-positive rate** | **1.4 × 10⁻⁴** | 1.4 × 10⁻⁴ |
| Observed per-window AUC | 0.693 | 0.707 |
| **Detection achievable there** | **0.18%** | **0.03%** |
| **AUC needed for 80% detection there** | **0.9992** | 0.9992 |

An AUC of 0.999 is not a detector needing tuning; it is a different measurement
problem. No decision rule closes a gap from 0.70 to 0.9992. **The budget, as
applied, demands near-perfect discrimination on every one of 720 decisions an
hour** — a multiple-comparisons burden, not a detector failure.

### The operating point was mis-specified, and this is why that claim is not a dodge

Relaxing a target after failing to meet it is the standard way to manufacture a
success, so the reasoning matters more than the conclusion.

The argument is **not** that 0.1/h was too strict. As a constraint on an *alarm*
it is sensible — more than one spurious alert per ten hours trains a user to
ignore it. **The error is that a per-hour alarm budget and a per-5-second
decision rate are different quantities, and the design conflated them.** The
per-hour figure is unchanged. What changes is how many decisions it is divided
among.

A real monitor does not re-decide every 5 seconds. *"Should this session be
flagged for a recalibration check?"* is a once-per-session question.

### The same detector, judged once per session

| | T11 | T5 |
|---|---|---|
| Session-level AUC | 0.673 | **0.742** |
| Detection at 10% false-flag rate | 14.4% | **30.4%** |
| Detection at 5% false-flag rate | 8.5% | 17.0% |

Aggregation is **not** the rescue either — it helps T5 and slightly hurts T11, so
the two-participant disagreement appears here too. But it moves the problem from
*impossible* to *hard*.

### The design target that follows

To flag 80% of degrading sessions while wrongly flagging 10% of healthy ones
requires a session-level AUC of about **0.93**. The monitor achieves **0.67–0.74**.

That is a specific, quotable gap. It is the difference between *"this cannot
work"* and *"this needs a measurement about this much better"* — and only the
second is a research programme.

### The headline is unchanged

**On this data, at the operating point the design specified, no configuration
works.** That stands. What is added is *why*, in arithmetic, and what number a
future attempt has to beat.

---

## 28 August 2026 — One measurement per session: the finding that explains everything else

### The puzzle

Per-window AUC is 0.693 (T11). A session holds ~55 windows. If those were
independent, aggregating them would raise discriminability by roughly √55.
Session-level AUC is **0.673** — slightly *worse*.

Which of two explanations holds decides the entire next direction, so it was
measured rather than guessed.

### The measurement

| Participant | Windows/session | Lag-1 autocorrelation | **Effective independent samples** |
|---|---|---|---|
| T11 | 55 | **0.995** | **0.1** |
| T5 | 42 | **0.980** | **0.4** |

**A session does not contain 55 measurements. It contains one measurement taken
55 times.** Consecutive windows are almost perfectly correlated, so the effective
sample size per session is *less than one*.

Confirmed independently by trying six aggregators — none beats the median, and
the ones that lean on the tail are near chance:

| Aggregator | T11 | T5 |
|---|---|---|
| median | 0.684 | 0.736 |
| mean | 0.589 | 0.670 |
| 90th percentile | 0.469 | 0.510 |
| max | 0.457 | 0.487 |
| fraction above own median | 0.436 | 0.322 |

### This is the unifying explanation

Every negative result in this project follows from it:

- **Why CUSUM did not help.** Accumulating evidence works when samples are
  independent. Accumulating 55 copies of the same measurement adds nothing.
- **Why longer windows or more windows are a dead end.** There is no √N to
  collect; N is already 1.
- **Why the silence gate always fails.** The risk score is a slowly-varying
  quantity whose consecutive values are 99.5% correlated. A series like that
  *is* a trend — testing it for a trend will almost always find one.
- **Why aggregation could never rescue the operating point.**

### A correction to my own bound, which does not change the verdict

The previous entry computed the required false-positive rate treating each
5-second window as an independent opportunity to false-alarm. Given r = 0.995
that is wrong: healthy *episodes*, not windows, are the independent unit.
Recomputed properly:

| | T11 | T5 |
|---|---|---|
| Independent healthy units | 309 sessions | 408 sessions |
| Budget permits | 2.4 flags | 2.4 flags |
| Required per-session false-flag rate | 0.76% | 0.59% |
| Session AUC | 0.673 | 0.742 |
| **Detection achievable there** | **0.9%** | **1.8%** |
| **AUC needed for 80% detection** | **0.990** | **0.991** |

The window-based version said 0.18% detection and AUC 0.9992; the corrected
version says 0.9% and 0.990. **Rigorously different, practically identical.**
The verdict is unchanged, and the correction is recorded because the first
calculation was wrong even though it pointed the same way.

### What this rules in and out

**Ruled out**, on evidence rather than preference:

- Better decision rules (measured: all at 0% inside budget)
- Longer or more windows (there is no independent information to average)
- Better session-level aggregators (six tried; none beats a plain median)

**Ruled in**, as the only remaining direction: **a fundamentally better
measurement.** Different features, not more processing of these ones. The
current features are per-channel mean activity in a 30-second window; the
untried directions are per-channel variability, cross-channel covariance
structure, and spectral content.

### The honest position on stopping here

The project now has a complete, quantitative account: a benchmark, a test
battery, a replicated demonstration that the monitor beats the trivial
comparator, one clean positive (task changes are not mistaken for faults), and a
negative result whose cause is measured to three decimal places with a specific
target attached — **AUC 0.99 needed, 0.67–0.74 achieved, and the reason no
amount of averaging closes it.**

Chasing new features from here is open-ended and carries a real risk of fishing:
with two participants who disagree, any feature that helps one can be found by
trying enough of them. **That work should be preregistered before it is run**,
in the same way the Phase 1–2 analysis was, rather than begun opportunistically.

---

## 28 August 2026 — The live demonstration

### What was built

The project's stated deliverable has always been *"a program that runs live"* and
a demonstration a judge can watch. That existed as a description and not as a
thing. It now exists: `reports/monitor_demo.html`, generated from
`scripts/30_export_demo.py`.

It replays three real episodes through the real monitor at its real threshold —
recorded neural data, the frozen decoder, onsets from the locked injection plan.
Nothing is staged or reconstructed.

### The design decision that mattered

The obvious demo replays a fault, shows the state chip turn amber before
performance collapses, and stops. **That demo would be dishonest.** This project
measured that at this operating point the monitor catches 143 of 586 faults and
raises 3.41 false alarms per hour against a 0.1/h budget. A viewer shown only a
success would leave with a false impression of a system that does not work.

So the demo shows **three** episodes, and the viewer picks between them:

| Shown as | What it is |
|---|---|
| **Caught** | A channel-dropout fault the monitor reports. What working looks like. |
| **Missed** | A real rate-loss fault it never reports. The common case. |
| **False alarm** | A healthy recording it alarms on anyway. |

Same monitor, same threshold, same participant. **The ratio is not a
presentation choice** — it is what the measurement found, and the page says so.

### A selection bug worth recording

The first version chose episodes by a rule that sounded reasonable — risk rising
threefold above the episode's own pre-onset baseline. It selected three episodes
that **never came within a factor of five of the actual WARN threshold of 50.5**,
so the "caught" case was not caught and the "false alarm" case raised no alarm.
The demo would have shown three flat traces while claiming to show a detection.

Fixed by selecting against the operating point the benchmark actually used, read
from `harness_summary_local.json` rather than restated. The chosen episodes now
are: EP00019 (fires at window 46, onset 28), EP00003 (never fires), EP00182
(healthy, fires at window 21).

**The lesson generalises:** a plausible-sounding proxy for "the detector fired"
is not the same as the detector firing, and only the real threshold settles it.

### Why this is worth having beyond the demo

It is the first artefact in the project that shows the monitor *operating* rather
than being *scored*. A table of AUCs does not convey that the risk score sits
quietly at 0.1 and then climbs to 288 within a few windows, or that the named
cause switches from `dispersion` to `silence` as channels start dropping. Those
are properties of the system that the summary statistics flatten.

---

## 28 August 2026 — Checking that the documents still match the data

### Why this was needed

This project asserts "reproducible" throughout, and that word is cheap. Across
sixty-odd commits a number quoted in a report and the file it came from can drift
apart in three ways, none dishonest and all corrosive:

- an analysis is re-run with a fix, and prose written earlier still quotes the
  old figure;
- a number is copied between documents by hand and a digit changes;
- a claim is written from memory of a run rather than from its output.

**Phase 3 already produced one instance** — 15 of 36 configurations were
described as having no operating point, a figure that came from a search bounded
at 59. So this is a demonstrated failure mode in this repository, not a
hypothetical one.

### What was built

`scripts/31_verify_claims.py` recomputes twelve headline figures from
`data/processed/` and compares each against the number written in the documents:
both decoders and their measured chance levels, the operating point, the
false-alarm rate, three AUCs, both autocorrelations, the task-change separation,
and the count of configurations passing all five gates.

**All twelve match.** The largest discrepancy is rounding — 54.554 quoted as
54.6.

A mismatch is treated as a *finding*, not a crash: it means a document needs
updating or a number needs re-deriving, and the script names which document to
look at. Referenced from the README, to be run before quoting any figure in a
poster, paper or application.

### The README was badly out of date

It still stated the **abandoned** early-warning-signal question as the research
question, and described the project's status as "research planning and
foundational skill development." That is the first thing anyone opening the
repository sees — a judge, a sponsor, or a future session picking this up cold.

Rewritten to state the actual result, point at the five documents worth reading,
give the reproduction commands in dependency order, and put the
**no-human-participants statement and the terminology note at the very top**,
before anything else, where a reviewer cannot miss them.

---

## 1 September 2026 — Rendering the demo caught two things, one of them serious

### Looking at the output, which I had skipped

The demo was published without ever viewing the rendered page. Rendering it
headless and looking at it found two problems, and the second is a genuine
overclaim.

### 1. The page opened on two empty charts

It loaded at window 0, so a viewer arrived at blank panels and had to work out to
press play before anything appeared. Fixed: the full series now draws faintly and
the played portion draws solid, so the page is informative on arrival. Panel
titles and units were added — previously the only way to tell the traces apart
was the legend.

### 2. The "caught" tab asserted something false

The tab read *"A fault the monitor reports **before** performance collapses."*

The episode behind it warned **35 seconds after** performance had already crossed
the degradation threshold.

Checking the whole distribution rather than that one case:

| Of the 132 faults `decoder_guard` detects on T11 | |
|---|---|
| Warned **before** performance dropped | 63 (48%) |
| Warned **after** — confirmation, not warning | 69 (52%) |
| **Median lead time** | **0 s** |
| Range | −155 s to +135 s |

**Detecting a fault and warning about it early are different things here, and the
difference is close to a coin flip.** A single "caught" tab cannot express that,
and the label I wrote asserted the favourable half as though it were the whole.

Fixed by showing **four** episodes with their real frequencies: *warned early*
(48%), *warned late* (52%), *never reported*, *false alarm*. The page now states
the median lead of 0 s, and says outright that an earlier version made the claim
and what was wrong with it.

This is the failure mode the whole project has been guarding against, appearing
on its most public artefact. It was caught by looking at the thing rather than
by trusting the code that produced it.

### 3. A windowing subtlety this exposed, which affects the benchmark itself

Watching the risk curve leave the floor slightly *before* the injection marker
prompted a check. Windows are 30 s long and step every 5 s, so **six windows
that start before the onset still span it** and contain post-fault data.

The typical episode has 25 pre-onset windows, so **about 24% of the "healthy"
reference used for re-baselining is contaminated with fault data.**

Direction of the bias, which matters: the contaminated reference is pulled
*toward* the fault, which makes the fault look less anomalous and **reduces
sensitivity**. The error is therefore **conservative** — it works against
detection, not for it. Lead time is a difference between two quantities measured
on the same windowing, so the bias largely cancels there.

**Not corrected in the current results**, because doing so means re-running the
whole benchmark, and it would move numbers in the direction of slightly better
detection rather than changing any conclusion. Recorded here and in
`reports/PHASE3_REPORT.md` limitations as a defect to fix in the next full run:
the reference should use only windows that *end* before the onset
(`start + window <= onset_bin`), not merely start before it.

---

## 1 September 2026 — The feature study: the prediction held, and the null result has structure

### The prediction, and the outcome

Before running it I put on record that I expected no family to clear the bar.
**That held.** The frozen criterion — +0.05 session-level AUC over
`decoder_guard` v1, **on both participants in the same direction** — is met by
none of the four.

| Family | T11 Δ | T5 Δ | Verdict |
|---|---|---|---|
| F1 variability | +0.004 | −0.075 | no improvement on either |
| F2 covariance | −0.043 | −0.137 | no improvement on either |
| **F3 spectral** | **+0.078** | **−0.186** | **null — helped T11 only** |
| F4 counts | +0.003 | −0.212 | no improvement on either |

### F3 is exactly the trap the preregistration was written to catch

Spectral content **cleared the bar on T11** (+0.078) and **failed badly on T5**
(−0.186). Had this project had only one participant — or had the both-participants
rule been written after seeing this table rather than before — F3 would have been
reported as the feature that worked.

The rule was frozen at commit `0950c04` with a checksum, and it says a family
helping one participant is a **null result, not a partial success**. So F3 is a
null result. That is the rule doing precisely the job it was written for, on the
one occasion it mattered.

### But the null has structure, and the structure is informative

**This part is post-hoc** — computed after seeing that nothing passed — and is
labelled as such in the report. It is included because it changes what the null
*means*, not because it rescues it.

The frozen criterion compares each family against `decoder_guard` v1, which uses
its own four-component scorer, while the families use a generic one. So a family
could be losing to the **scorer** rather than to the features. `F0` — the current
features through the generic scorer — settles it:

| Family vs the matched control | T11 | T5 | Both ≥ +0.05 |
|---|---|---|---|
| **F1 variability** | **+0.106** | **+0.158** | **yes** |
| **F2 covariance** | **+0.059** | **+0.095** | **yes** |
| F3 spectral | +0.180 | +0.047 | no |
| F4 counts | +0.105 | +0.021 | no |

**Two families are genuinely better features than the ones in use**, on both
participants, in the same direction.

And yet nothing passes, because:

> **`decoder_guard` beats its own features under the generic scorer by +0.102
> (T11) and +0.233 (T5). Its advantage is mostly in the four-component
> decomposition, not in the per-channel means it consumes.**

So the honest reading is: **the new features are better features, and that is not
enough** — the gain does not cover what the purpose-built scorer contributes.

### What this rules in and out

**Ruled out:** the four obvious feature families, as drop-in replacements. That
converts *"a better feature is the remaining direction"* into *"the four obvious
better features were named in advance, tried, and are not sufficient"* — a
stronger statement than the open question it replaces.

**Newly indicated:** combining the better features (F1, F2) **with** the
four-component decomposition, rather than substituting one for the other. That is
a new study and would need its own preregistration. It is not run here, because
running it now on the strength of a post-hoc table is exactly the move the freeze
exists to prevent.

**Unchanged:** n = 2, and the participants disagree — visibly, in the F3 row. A
third dataset is still worth more than any feature.

---

## 2 September 2026 — The combination study, and the finding that was hiding behind every null

### The combination study: null, and the frozen criterion held

Three arms, frozen at commit `7234964` before any was computed. The faithfulness
check the study was conditional on passed exactly (Spearman ρ = 1.0000 over 6,637
windows), so the arms genuinely test *the same decomposition over better
features* rather than something merely similar.

| Arm | T11 Δ | T5 Δ | Verdict |
|---|---|---|---|
| C1 decomposition over F1 | −0.034 | +0.020 | no improvement on either |
| C2 decomposition over F2 | +0.030 | −0.124 | no improvement on either |
| C3 over both | −0.047 | +0.017 | no improvement on either |

Nothing clears +0.05 on both. **Better features and a better decomposition were
the two ingredients this project's own results identified, and combining them
does not close the gap either.**

### The pattern behind every null

Something helping one participant and hurting the other has now been recorded
**four separate times**: Phase 1–2, the joint-detector prediction, the feature
study's F3 row, and all three arms above. Recorded four times, it stops being a
limitation and becomes a result worth measuring directly.

So every candidate this project has evaluated on both participants was pooled and
the question asked once, properly.

| | |
|---|---|
| Candidates improving **both** participants | **0 of 7** |
| Moving in the same direction at all | 1 of 7 — and that one moved *down* on both |
| Correlation between the two columns | r = **−0.630** (p = 0.130) |
| Best on T11 (F3, +0.078) | is the **worst** on T5 (−0.186) |
| Best on T5 (C1, +0.020) | is negative on T11 (−0.034) |

### What can and cannot be claimed, stated carefully

**Can:** across seven candidates spanning four feature families and three
decomposition arms, **none improved both participants.** That count needs no
model and no assumption.

**Cannot:** that the correlation is genuinely negative. r = −0.630 looks striking
but p = 0.130 at n = 7, and the candidates are not fully independent — C1 and C3
share a feature family. **The honest reading is *no evidence of positive
transfer*, not *evidence of negative transfer*.** The distinction matters and the
report states it in those words.

### Why this reframes the whole project

Each study on its own said "this candidate did not work". Together they say
something about **the problem** rather than about any candidate:

> **What improves decoder-health monitoring appears to be participant-specific.**

If that holds, the target changes. A monitor would be fitted per participant and
per array, and the question stops being *"which feature is best?"* and becomes
*"how quickly can a monitor be calibrated for a new user?"* — a different and
more tractable problem, and one this dataset could actually address.

It also explains in one sentence why the two-participant limitation has been so
binding throughout: **there was never a shared effect for the second participant
to confirm.**

### The objection, which stands

Two participants cannot establish that generalisation fails in general; they can
only fail to demonstrate it. A third dataset could show that T5 and T11 are
unusually dissimilar and that transfer is ordinary. That is exactly why a third
dataset has been the top recommendation throughout, and this analysis
**strengthens rather than replaces** it.

---

## 2 September 2026 — Calibration efficiency: the first result that is not a null

Scope was fixed in `research/CALIBRATION_STUDY_NOTE.md` before anything ran. The
question came directly out of the transfer analysis: if a monitor has to be
fitted per person anyway, the useful number is **how much healthy data fitting
one costs**. That is within-participant, so the two-participant limitation that
has blocked everything else does not apply to it.

**Result:** about **20 healthy windows — roughly two minutes of ordinary
recording** — and everything after that is free. Going from 20 windows to the
entire healthy record (221 windows on T11, 211 on T5) changes AUC by −0.0059 and
−0.0008 respectively. Both curves are flat, and on both arrays more data is very
slightly *worse*, not better.

Full report: `reports/CALIBRATION_CURVE.md`. Figure:
`reports/figures/14_calibration_curve.png`.

### Two things I checked before believing it

**1. The n = 10 point is a singular fit, and it nearly produced a false headline.**

The guard's `profile` component is a Mahalanobis distance in a K = 10 dimensional
subspace, so a 10-window fit gives a rank-9 covariance that only the 1e-6 ridge
makes invertible. Measured: at n = 10 the smallest eigenvalue is *exactly* the
ridge and the condition number is 1.8×10⁷, against ~2×10² at every other fit
size.

This mattered because n = 10 is the **highest** AUC on T11 (0.670 against 0.648
for the full record). Taken at face value the curve reads "more calibration data
makes the monitor worse" — a striking claim, and false. The point is not a
measurement; it is the one grid point where the distance being computed is not a
distance. It is plotted in a grey band and excluded from every claim.

I want this recorded as a near-miss rather than as a clean catch. The
conditioning check was run because the two participants' curves *disagreed in
direction*, which prompted me to look at the smallest fits. Had both curves
sloped the same way, I might have written the striking version up.

**2. Does "20 windows" actually mean "two minutes"?**

The frozen protocol drew healthy windows at random from the whole record, so they
were scattered across days. Adjacent windows have lag-1 r = 0.995, so 20
scattered windows could plausibly carry far more information than 20 contiguous
ones — in which case quoting minutes would have been false.

So I added a **contiguous draw** (n consecutive windows from one block, which is
what a real commissioning session collects) and reran the grid. The two agree at
matched counts: T11 0.665 contiguous vs 0.654 scattered at n = 20; T5 0.740 vs
0.740 at n = 40. The concern was reasonable and the data did not support it.

This run was **added after seeing the frozen curve**, and the report says so. It
is a check on what a number means, not a search for a better number, and it is
reported whichever way it came out. The frozen scattered protocol stays primary.

### Deviations from the frozen scope, recorded not buried

- The **n = 5 grid point never ran** — the script skips fits under 8 windows.
  Given the conditioning result nothing is lost, but the frozen grid said 5 and
  it is absent.
- The **contiguous draw stops at 40 windows**: no single healthy block has 80
  consecutive windows. That is itself a finding — past ~40 windows, more
  calibration data *necessarily* means pooling across blocks or days.
- The contiguous draw was **not in the frozen scope at all**.

### Why this is the constructive half of every earlier null

A session's healthy record barely varies within itself. That is what lag-1
r = 0.995 says, and it is why aggregating windows never bought the statistical
power detection needed. The flip side is that the 221st healthy window tells the
fit nothing the 20th had not already said.

> **The property that makes this monitor hard to make sensitive is the same
> property that makes it cheap to commission.**

That is one mechanism explaining both a negative and a positive result, which is
a considerably stronger position than a list of things that did not work.

### What it still cannot say

That two minutes suffices for a **new** participant — that is the transfer
question and still needs a third dataset (Card et al. 2024, T15). And that the
monitor is good enough to *use*: AUC 0.65–0.74 is far short of the ~0.99 the
operating-point analysis showed the false-alarm budget demands. This measures how
fast the monitor reaches **its own** ceiling, not where that ceiling sits.

Verifier extended to 23 claims (`scripts/31_verify_claims.py`); all match.

---

## 2 September 2026 — Staleness, and a finding I was not looking for

Scope fixed in `research/STALENESS_STUDY_NOTE.md` before running, including my
prediction that the effect would be small. Full report:
`reports/STALENESS_AND_DAY_VARIANCE.md`.

### What I asked, and what I got instead

**Asked:** does a monitor's calibration go stale as it ages? **Answer: no
measurable effect over 142 days.** Point estimate −0.012 AUC per 100 days on
T11, permutation p = 0.128. Both participants point the same way — the first
direction they have ever agreed on — and neither is significant. My prediction
was right, which is worth recording mainly because it was written down first.

**Got instead:** the day the episodes come from swings same-day AUC from **0.32
to 0.97** across 13 sessions on T11. Three days sit *below chance*, meaning the
risk score runs backwards on those days. Only 26% of that variance is sampling
noise (I² = 0.86, and the model-free check agrees). This is a bigger effect than
anything the feature or combination studies ever moved, and it was invisible in
every pooled analysis because pooling averages it away.

### Three near-misses, in order of how badly each would have gone

**1. A p-value inflated 43-fold by non-independence.** The naive Spearman on the
staleness trend gives p = 0.003, and I would have reported "monitors go stale"
on the strength of it. But the 95 forward day pairs come from only 15 sessions,
so they share source and target days constantly. Permuting *which calendar date
belongs to which session* — preserving the whole dependency structure, destroying
only the time link — gives p = 0.128 (T11) and 0.080 (T5).

This is the project's recurring failure in a new costume. Within a session,
lag-1 r = 0.995 meant treating windows as independent **overstated** the power
available for detection. Here, treating day pairs as independent **understates** a
p-value by more than fortyfold. Same root cause, opposite direction, and both
directions produce a false claim.

**2. An inverse-variance pooled AUC of 0.836 that is an artefact of my own
weighting.** Against an unweighted mean of 0.675, and I was one paragraph away
from writing "the monitor is substantially better than every earlier report
said." AUC is bounded in [0,1], so its sampling variance shrinks toward the
bounds, so 1/se² weighting over-weights exactly the days with the most extreme
AUCs. Measured: Spearman(|AUC−0.5|, se) = −0.913 on T11, with a 31× spread in
weights. Day 800 (AUC 0.974) got 31× the weight of day 702 (AUC 0.456) purely
because near-perfect AUCs have small standard errors. The field is now named
`inverse_variance_pooled_auc_BIASED_DO_NOT_QUOTE` with the reasoning attached.

Cochran's Q uses the same weights, so its p-value is approximate too. The
conclusion does not rest on it — the unweighted comparison agrees.

**3. A fault-mix control that silently measured nothing.** It tested
`e.severity`, which is the numeric magnitude, against the string `"high"` —
always False, so it reported 0.00 on every day and looked like a clean pass. The
categorical field is `severity_label`. After fixing it the control *changed the
conclusion*: on T5 the day-to-day spread tracks fault mix (ρ = 0.886, p = 0.019),
so **T5 cannot corroborate the T11 effect**. On T11 it does not (ρ = 0.05,
p = 0.87) and the effect stands there.

That one is the most uncomfortable, because a control that returns all-zeros
looks exactly like a control that passed.

### A hypothesis I tested and abandoned

The per-day AUCs looked better than the pooled ones, which suggested that mixing
days dilutes the signal — attractive, with an obvious fix. Refuted: holding fit
and episodes identical and varying only within-day vs across-day, pooling costs
**0.003** AUC on T11 and 0.016 on T5, and per-session normalisation recovers
nothing because there was nothing to recover. The apparent gap was near-miss 2
above. Reported because it was tested.

### Where this points

The project has been searching along "which detector, which feature, which
combination", and every answer was null. The day-variance result suggests that
was the wrong axis. The next question is **"what makes day 800 different from
day 783?"** — answerable with the data already downloaded, and never asked
because the pooled framing hid the variation entirely.

Verifier now at 33 claims; all match.

---

## 2 September 2026 — The first preregistered positive result, and it is bad news

Preregistered in `research/DAY_PREDICTOR_PREREGISTRATION.md`: five predictors,
five signs committed in advance, Bonferroni threshold 0.01, all five reported
whatever they showed. Report: `reports/DAY_PREDICTORS.md`.

### The result

**P5 — that day's frozen-decoder error — predicts the monitor's same-day AUC at
ρ = −0.720, p = 0.0055 on T11.** Correct sign, clears the corrected threshold.
T5 agrees in direction and size (ρ = −0.829) but at 6 days cannot clear it
(p = 0.042). The other four predictors are null.

Day 800: decoder error 42.5°, monitor AUC 0.97. Day 783: decoder error 89.3°
(chance is 90.7°), monitor AUC 0.32.

### It had to survive an obvious artefact, and did

The outcome is *itself defined by decoder performance* — the AUC is measured over
the window from fault onset to the moment decoder error crosses the deterioration
threshold. On a day already near chance, episodes might cross immediately, or the
crossed/not-crossed split might shift, and either would depress AUC for reasons
unrelated to the monitor.

I checked every link in that chain and none of them exists on T11: decoder error
vs fraction crossing ρ = −0.30 (p = 0.32); vs early-warning window length
ρ = +0.15 (p = 0.63); window length vs AUC ρ = +0.20 (p = 0.52). The partial
correlation controlling for window length is **−0.773, p = 0.0032** — stronger
than the raw one.

### Why this is worse news than any of the nulls

Every earlier negative result said *"not sensitive enough yet"*, which is the
kind of problem more work can fix. This one says the failures are **correlated
with the condition the monitor exists to detect**:

> The monitor is least reliable exactly when it would be most needed.

On the worst day measured it is *worse than chance* — its risk score ran
backwards, reading lower during faults than during healthy operation. A monitor
whose errors are independent of the hazard can be improved by making it more
sensitive. A monitor whose errors track the hazard cannot.

I want that recorded plainly rather than softened, because it is the single most
consequential thing this project has found and it argues against the design as
originally conceived.

### But it also points at the one useful thing this system could do now

If a session's difficulty can be recognised at the time, the monitor can
**abstain** — say "today is a day I cannot be trusted" instead of failing
silently. That is a smaller claim than "early warning of decoder failure".

**Correction, made the same day.** I first wrote that decoder error is
"measurable online and without labels, from the decoder's own output". That is
wrong, and it is the kind of wrong that would have propagated into a design.
The angular error used as P5 is measured against the *intended* direction, which
is known here only because these are recorded task blocks with logged targets.
In free use there is no target, so it cannot be computed at all — it is available
during periodic assessment blocks, not continuously.

So abstention rests on a question I had skipped: **is there a label-free signal
that stands in for decoder error?** Tested next rather than assumed.

### The predictor that came out backwards

P4 (within-day drift) was predicted **negative** and came out **+0.582**. It does
not clear the threshold so nothing is claimed, but the sign was committed in
advance and is reported as it fell. This is the value of writing signs down: had
I not, I could have narrated a mechanism for either direction after the fact.

### Honest limits

13 days, one participant confirmed. The preregistration fixed the power limit
before looking — at n = 13, |ρ| must reach ~0.68 — so P5 at −0.720 is *the only
size of effect this design could have found*, and the four nulls mean
underpowered rather than absent. And it is correlational: a common cause (a
session whose recording is simply messier) is at least as likely, and is in fact
the mechanism that was predicted.

Verifier now at 38 claims; all match.

---

## 2–3 September 2026 — Abstention: not supported, and one statistic that explains the whole project

Scope fixed in `research/ABSTENTION_NOTE.md` before running, including the
admission that **no sign was predicted** for the four candidates. Report:
`reports/ABSTENTION.md`.

### The answer is no

Four label-free signals — computed from the decoded velocity stream with no
target, no intent, no label — were tested in two stages: do they stand in for
decoder error, and do they predict whether the monitor will work that day?

**Nothing passes stage 2 on either participant.** No label-free signal predicts
the monitor's per-day AUC, which is the only thing an abstention rule needs.

The scope note said in advance that a null means *"abstention is an untested
proposal, not a capability"*, and that is what is reported.

### The statistic worth keeping

L4 — mean output speed — tracks decoder error on **both** participants and clears
the corrected threshold on **both**: ρ = +0.681 (p = 0.010) on T11 and
ρ = −0.943 (p = 0.005) on T5.

**The signs are opposite.** Faster decoded output means *worse* decoding on T11
and *better* decoding on T5.

This is the strongest cross-participant agreement anywhere in this project, and
it is a contradiction. Any threshold that abstains correctly on one array
abstains backwards on the other. The transfer analysis inferred
participant-specificity from seven candidates failing to replicate; this shows it
in a single number, with both participants individually significant and pointing
opposite ways.

It is also the clearest justification I have for refusing to predict signs for
L1–L4. Had I guessed either sign, one of these two participants would have
"confirmed" it, and I would have had a result.

### Where the project stands after today

Four studies ran today, three of which changed what I think:

1. **Calibration is cheap** — 20 healthy windows, about two minutes. First
   non-null result.
2. **Fits do not go stale** — no measurable ageing over 142 days, once the
   dependency between day pairs is handled properly (a naive p of 0.003 became
   0.128).
3. **Which day you use it on decides almost everything** — AUC 0.32 to 0.97,
   I² = 0.86, and the low days are the days the decoder is already failing
   (ρ = −0.720, preregistered, survives the artefact challenge).
4. **The monitor cannot tell when to abstain** — no label-free signal predicts
   its own reliability.

Taken together these say something the earlier nulls did not. The problem is not
that the monitor is insufficiently sensitive. It is that **its reliability is
governed by session-level properties it cannot observe, and its failures line up
with the hazard it exists to detect.** That is a structural objection to the
design, and it is the honest headline of the project.

Verifier now at 41 claims; all match.

---

## 3 September 2026 — My prediction was wrong, and the answer is better than either option I offered

Prediction committed in the addendum to
`research/DAY_PREDICTOR_PREREGISTRATION.md` before running. Report:
`reports/DAY_EFFECT_ACROSS_DETECTORS.md`.

### What I predicted and what happened

I predicted the day effect would be **shared by all four detectors** at ρ > 0.7,
and stated the alternative: if decoder-guard were uncorrelated with the
baselines, the problem is a design flaw. I set up a two-way question.

The answer was a third thing. The effect is shared by **exactly two** detectors:

| per-day AUC vs decoder-guard, T11 | ρ | p |
|---|---|---|
| `distribution_shift` | **+0.835** | 0.0004 |
| `robust_dispersion` | +0.247 | 0.42 |
| `mean_activity` | −0.060 | 0.84 |

and the P5 relationship splits the same way: `decoder_guard` −0.720,
`distribution_shift` −0.670, `robust_dispersion` −0.368, `mean_activity` +0.220.

### Why the split is the interesting part

The two that share it model the **multivariate distribution** of activity against
a healthy reference. The two that do not reduce a window to a scalar and have no
distributional reference to lose.

That hands P5 a mechanism it did not have. On a day the decoder handles badly the
*structure* of the activity is atypical — which is what a decoder is sensitive to
and what a distribution-based monitor depends on being stable. **A monitor built
on the same kind of information the decoder uses inherits the decoder's bad
days.** Counting spikes does not, because it never depended on that structure —
but counting spikes is also the detector that cannot see most faults, which is
where this whole project started.

So the tension is now explicit and unresolved: **the property that makes a
detector sensitive enough to be useful is the property that makes it fail when
the decoder fails.**

### The confound I cannot rule out

`mean_activity` and `robust_dispersion` are also the weaker detectors. A detector
whose per-day AUC is largely noise correlates weakly with everything, so their
low correlations might reflect noisiness rather than a different mechanism.
Against that, their per-day AUCs are not flat (`mean_activity` ranges 0.35–0.74).
With 13 days I cannot separate the two readings and I am not claiming I can.

### What it does to the headline

Yesterday's conclusion — that the monitor's failures line up with the hazard it
exists to detect — **stands, but should be read more narrowly**. It is an
objection to *distribution-based* decoder-health monitoring as a class, not to
one implementation. A future attempt cannot escape it by rebuilding decoder-guard
differently while keeping the same kind of healthy reference.

I would rather record that my prediction failed than that it succeeded, because
the failure produced a mechanism and a success would only have produced a
confirmation.

Verifier now at 44 claims; all match.

### Plain-language write-up of the five studies

Published as **The Bad-Day Problem** —
<https://claude.ai/code/artifact/3626899e-5714-4a29-861a-5fab36eacf82> — and mirrored
into the repo at `reports/bad_day_problem.html` so the record does not depend on an
external link.

It covers the five studies as the chain they actually were (each question chosen by
what the previous one found), the P5 scatter drawn from the real per-day numbers, the
detector-family split, and the three near-misses. The older
`reports/project_guide.html` still holds — it explains the ground-truth argument and
the fault injector from scratch, which has not changed — but its conclusion predates
all of this, and the new page is where the current headline lives.

---

## 3 September 2026 — I tried to break my own headline. It bent, and I had to retract half of it.

Predictions committed in `research/CEILING_CHALLENGE_NOTE.md` before running,
including that **I expected to find the confound**. Report:
`reports/CEILING_CHALLENGE.md`.

### Why I went looking

Yesterday's P5 result — the monitor fails on days the decoder is already failing
— had survived one artefact challenge. Re-reading the harness I found a second,
more dangerous one that I had missed. An episode counts as deteriorating when its
error exceeds **its own pre-onset baseline + 10°**. Chance on T11 is 90.7°. Day
783's baseline is 87.5°. A fault there has about three degrees of headroom before
the metric saturates.

If faults do less measurable damage on bad days, the ground truth is weaker
there, every detector scores lower, and P5 stops being a statement about the
monitor and becomes one about the measuring instrument.

### The ceiling is real, and it is worse than I guessed

Baseline vs the damage injected faults actually achieved: **ρ = −0.747,
p = 0.0033**. On day 665 (baseline 44.9°) a fault moves the error by +19.8°. On
day 783 (baseline 87.5°) it moves it by **+0.4°**.

That is a genuine limitation of the fault-injection corpus and it stands on its
own, whatever it does to P5: **on high-baseline sessions the ground truth is
nearly degenerate**, because a decoder already at chance cannot be made much
worse in a way this metric can see.

### But it does not explain P5, and two of my three predictions were wrong

- damage vs decoder error, predicted negative → **−0.632, correct**
- damage vs monitor AUC, predicted positive → **+0.181, p = 0.55, wrong**
- P5 after controlling for damage, predicted to weaken → **strengthened**,
  −0.720 → −0.794, p = 0.002, **wrong**

Weaker faults are not what makes the monitor fail on bad days.

### Then day 783 produced a contradiction I had to chase

Median achieved damage +0.4°, yet **78% of its episodes counted as crossing** —
which requires +10°. Both cannot be true unless the crossings are noise.

So I measured how often the +10° threshold is cleared **in the pre-onset windows,
where no fault exists by construction**. It runs from 0.3% on day 675 to
**19.9% on day 783**. One pre-onset window in five clears the deterioration
threshold with nothing wrong at all.

### And that is where I had to retract

That trace noise predicts monitor accuracy **exactly as well as decoder error
does** — both ρ = −0.720, p = 0.0055 — and the two correlate with each other at
ρ = +0.813.

I started writing "trace noise is the real explanation." Then I ran the partial
correlations both ways:

| | ρ | p |
|---|---|---|
| decoder error → AUC, controlling for trace noise | −0.333 | 0.29 |
| trace noise → AUC, controlling for decoder error | −0.333 | 0.29 |

**Identical in both directions.** That is collinearity, not mediation. At 13 days
with predictors correlating at 0.81 this design cannot separate them, and the
symmetry is what stopped me claiming it could. Had I only run the first partial I
would have published "the real cause is noise" with as much confidence as I had
published "the real cause is decoder error" the day before — and both would have
been the same unfounded claim pointing at different words.

### What I changed

- `reports/DAY_PREDICTORS.md` now carries a **partial retraction** at the top of
  its interpretation section. The finding stands; every "because" in it is marked
  unestablished.
- The README headline row is reworded to state the association without the
  mechanism.
- The ground-truth contamination is recorded: spurious crossings correlate with
  monitor AUC at ρ = −0.665, so part of the day-to-day spread is labels rather
  than detection. Not all of it — controlling for it leaves −0.613, p = 0.034.

### What still stands

The monitor's per-day accuracy is strongly predicted by how badly the decoder is
doing that day, and that has now survived **three** separate challenges: short
early-warning windows, a shifted crossed/not-crossed split, and the achievable-
damage ceiling. Day 800: 42.5°, AUC 0.97. Day 783: 89.3°, AUC 0.32. That is what
a user would experience and it has not moved.

What is gone is my explanation of why.

### One honest note about provenance

The ceiling and damage measures were preregistered. **The trace-noise measure was
not** — it was added mid-study once the damage result explained nothing and the
day-783 contradiction needed resolving. It is a control variable rather than an
outcome, and adding a control that weakens my own finding is the conservative
direction, but it was not in the note and the report says so rather than implying
otherwise.

Verifier now at 50 claims; all match.

---

## 3 September 2026 — The corpus is blind on exactly the days that matter

Predictions committed in the addendum to `research/CEILING_CHALLENGE_NOTE.md`
before running. Report: `reports/UNAMBIGUOUS_EPISODES.md`.

### The test

Keep only faulted episodes where the fault demonstrably did real damage — ≥ 10°,
the crossing rule's own threshold — so the ground truth is unambiguous whatever
the day's noise. Then ask whether the bad-day effect is still there.

### The answer is neither yes nor no

**6 of 13 T11 days cannot be scored at all**, and 5 of 6 T5 days. On day 783 — the
worst day the monitor had, and therefore the single most important day to
understand — **one** of twenty injected faults did damage the metric could
unambiguously see. On day 672, **none** did. And how many episodes a day keeps is
itself predicted by how badly the decoder is doing: ρ = −0.604, p = 0.029.

> The question *"does the monitor really fail on bad days, or do the labels just
> get noisy there?"* is **not answerable with this corpus** — not answered no, but
> unanswerable, because the days where it matters are the days where injected
> faults cannot produce measurable ground truth.

That is a limitation of the experimental design, not of the analysis, and it is
the most consequential thing I have found today.

### What the 7 surviving days say

The correlation drops to ρ = −0.536, p = 0.215. **That is not a refutation.** At
n = 7, |ρ| would need to reach about 0.79 to clear p < 0.05 — the filtering
removed the power along with the ambiguity, and I am not going to read a null out
of a test that could not have found anything.

Suggestive but no more: **day 702 stays bad on clean episodes**, 0.456 → 0.467
across its 12 unambiguous ones. Pure label contamination should have rescued it.
Day 715 improves and day 800 goes to 1.000, so the picture is genuinely mixed.

My predictions scored: "weakens but does not vanish" — partly right, though at
n = 7 losing significance is not the same as weakening. "Worst days lose most of
their episodes" — right, and strongly.

### The constructive part, which is the point

This gives a concrete design fix rather than "collect more data".

The performance metric is **angular error against intended direction, and it
saturates**: chance is 90.7°, so a session already at 87.5° has nowhere left to
go. Every fault injected onto such a session is invisible to the ground truth by
construction. **The corpus was built with a metric that cannot see the failures it
was built to study.**

A corpus meant to study monitoring on bad days needs a performance measure with
dynamic range at the bad end — time-to-target, path efficiency, or a decoded-
trajectory measure would all keep resolving where angle flattens out. That is a
specific, actionable change to the fault-injection design, and it is the strongest
recommendation this project has produced for anyone attempting it next.

### Where the day's work leaves the headline

Three states now, and they should not be blurred together:

1. **Established.** The monitor's per-day accuracy is strongly associated with how
   badly the decoder is doing (ρ = −0.720), through three challenges.
2. **Withdrawn.** Any claim about *which* property of the day causes it. Decoder
   error and trace noise are collinear at 0.813 and indistinguishable at n = 13.
3. **Unanswerable here.** Whether the association reflects failed detection or
   degraded labels. The corpus cannot support the question on the relevant days.

Verifier now at 53 claims; all match.

---

## 3 September 2026 — Checking my own recommendation, and finding the check was broken too

**Exploratory, not preregistered** — and labelled that way in the report,
`reports/WHAT_DECODER_ERROR_MEANS.md`.

### Why

I had just published a recommendation: a future corpus needs a performance measure
with dynamic range at the bad end, because angular error saturates near chance.
That is only right **if the decoder still holds usable signal on those days**. If
it is already at chance there is nothing for a fault to destroy and no metric
helps. So I measured each day against its own shuffled-pairing chance level.

### Two things wrong with my own check

**1. A statistic whose stored name inverted it.** `mannwhitneyu` returns U₁, the
count of pairs where x exceeds y, so U₁/(nm) is P(error **exceeds** chance). I
stored it as `prob_better_than_chance`. A decoder 55° better than chance was
recorded as 0.273 and would have been read as its probability of beating chance.
Both directions are now written out so it cannot be misread again.

**2. A per-day chance level that is not what it looks like.** Shuffled chance came
out between **47.7° and 102.7°**, where a chance level should sit near 90°. The
cause is task geometry: if a day's intended movements all point similarly,
shuffling barely changes anything, because pointing the popular way already scores
well.

Measured: **sessions differ by a factor of fifty in directional concentration**
(0.013 on day 675, 0.679 on day 758). That was not known before today and it
affects every absolute error number in this project.

### The finding that fell out of fixing it

Absolute angular error predicts monitor accuracy at −0.720. **Margin over that
day's own chance does not: +0.264, p = 0.38.**

| | error | beats own chance by | monitor AUC |
|---|---|---|---|
| day 800 | 42.5° | P(better) = 0.531 | **0.974** |
| day 783 | 89.3° | P(better) = 0.533 | **0.319** |

Two days that beat their own chance by *almost identical* margins, with monitor
accuracies of 0.97 and 0.32. Whatever separates them, **it is not how much real
signal the decoder retains.**

So the phrase I have been using — "the monitor fails when the decoder is already
failing" — is not supported in the sense it naturally carries. What is supported
is narrower: the monitor's accuracy tracks the day's *absolute* angular error, a
quantity that mixes decoder quality with how directionally varied the task was.
README amended.

### Where I am stopping this line

Five day-level variables now correlate with monitor accuracy at various strengths:
absolute decoder error (−0.720), trace noise (−0.720), spurious-crossing rate
(−0.665), directional concentration (−0.516), margin over own chance (+0.264).
They are mutually entangled — the first two alone correlate at 0.813 — and there
are **thirteen days**.

**This design can establish that sessions differ enormously and that the
differences track "how well things were going that day". It cannot identify which
property is responsible, and no further re-slicing of thirteen numbers will change
that.** Continuing would be generating explanations rather than testing them, so I
am stopping here rather than finding a sixth variable.

What would settle it: sessions that break the entanglement — a decoder inaccurate
but steady, or noisy but accurate, or a task held at constant directional
difficulty. None exist in this data. A prospective recording could fix the task by
design and separate geometry from decoder health at the source.

### A note on the shape of today

Three of today's studies were attacks on my own results, and each one landed:

1. The ceiling challenge → mechanism **withdrawn** (collinearity).
2. The unambiguous-episode test → the question is **unanswerable** on the days
   that matter.
3. This one → the phrase I was using for the finding is **wrong**, and my own
   check contained two errors before it produced anything.

The association at the centre of it has survived every attack. Everything I built
*around* that association has not.

Verifier now at 56 claims; all match.

---

## 3 September 2026 — "Severity" does not mean the same thing on every session

Prediction committed in addendum 2 of `research/CEILING_CHALLENGE_NOTE.md` before
running. Report: `reports/SEVERITY_LADDER_VALIDITY.md`.

### Why I asked

The ceiling result showed achieved damage running from +19.8° on one session to
+0.4° on another. But every benchmark here treats severity as a **controlled
variable** with three ordered levels, calibrated once, globally. If damage
collapses on some sessions, those labels do not describe three ordered things
everywhere — and that assumption has been load-bearing since the corpus was built.

### The answer, and it replicates

A cell is one session × fault mode; monotone means median damage strictly
increases benign → sub → crossing. Every cell had enough episodes; none were
dropped.

| | T11 | T5 |
|---|---|---|
| Monotone / measured | 34 / 60 | 16 / 24 |
| **Monotone fraction** | **0.567** | **0.667** |
| ρ, baseline error vs monotone fraction | **−0.677** (p = 0.0055) | **−0.926** (p = 0.0080) |

**Both participants, same sign, both significant.** That has not happened before
in this project — every previous cross-participant test either disagreed or was
underpowered. It is the most robust finding here, and it is a finding about the
corpus rather than about any detector.

### Prediction scored

**Right on the substance**: the ladder holds on low-baseline sessions (days 665,
658, 692 are monotone in all four modes) and collapses on high-baseline ones.

**Wrong on the specifics**: I named days 783 and 672 as likely worst. Day 672 is
fine at 0.75. The two total failures are days **689 and 758** — and 758 is the
interesting one, because its baseline is only 58.2°, mid-range, so pure headroom
does not explain it. It has the **highest directional concentration of any
session, 0.679**. Baseline and concentration are the same entangled pair from
yesterday, and this study cannot separate them either. The baseline relationship
is the one that replicates, so that is the one I state.

### The fault modes disagree between participants

CHANNEL_DROPOUT is the **worst** mode on T11 (0.467) and **perfect** on T5
(1.000); RATE_LOSS is the best on T11 and the worst on T5. No claim about which
fault type is hardest to calibrate survives both arrays, and none is made.

### What it does and does not invalidate

**Does not:** the headline results. "0 of 48 pass the gates", the AUC figures and
the operating-point bound all pool across sessions and severities, and the global
calibration does hold on average — that is what it was calibrated for.

**Does:** any severity-stratified claim *within* a session. On 43% of T11 cells
the three levels were not correctly ordered. This is an internal-validity limit
that had been assumed away since the corpus was built, and it is now measured and
in the README.

### The second design recommendation

Severity should be calibrated **per session**, against that session's own
achievable damage range, rather than once globally. A fault labelled "crossing"
should cross the threshold *on the session it is injected into*, which means
measuring each session's headroom before choosing its severities instead of after.

That is independent of the first recommendation (a metric with range at the bad
end and robustness to task geometry). Two concrete, testable design changes have
now come out of attacking my own results, which is more than the successful
results produced.

Verifier now at 60 claims; all match.

---

## 3 September 2026 — Closing an open item with a number instead of an argument

Prediction committed in `research/WINDOW_OVERLAP_NOTE.md` before running. Report:
`reports/WINDOW_OVERLAP.md`.

### The item

Windows are 30 s long stepped every 5 s, so a window that *starts* before fault
onset still *extends* past it. Up to six such windows per episode were being
counted as healthy while containing faulted data. I found this during the
benchmark work, argued the bias was conservative, recorded it as a limitation,
and left it unmeasured. It was one of two things I had explicitly deferred.

An argument is not a measurement, so it was overdue.

### Scored against the prediction

| Predicted | Outcome |
|---|---|
| the strict reference **raises** AUC | ✓ both participants |
| the effect is small | ✓ though bigger than the "few thousandths" I guessed |
| ~6 contaminated windows per episode | ✓ **5.99** on T11, **6.00** on T5 |

Mean AUC recovered: **+0.0072** (T11) and **+0.0123** (T5); largest single day
+0.032. Six of nineteen days tie *exactly*, which is why each participant's
Wilcoxon is weak (p = 0.13, 0.125) — the ties eat the power. Since the direction
was committed in advance the right test is a one-sided sign test across both
arrays: **11 of 13 non-tied days improved, p = 0.011**.

### What it means

Every AUC in this project **understates** performance by roughly 0.7–1.2%, worst
case about 3%. No conclusion moves — that is nowhere near the gap between the
0.65–0.74 achieved and the ~0.99 the false-alarm budget demands.

The value is not the correction, it is that **"the bias is conservative" is no
longer an argument in this repository. It is a number.** I had been citing that
phrase in several places on the strength of reasoning alone.

### Why I did not recompute the earlier results

Fixing it would shift every AUC up by under 0.01, change nothing, and invalidate
the frozen records that every preregistration points at. Those frozen numbers are
what was committed to in advance; replacing them for a sub-1% correction would
trade a real methodological guarantee for a cosmetic one. The correction factor
is documented instead, and `54_window_overlap.py` implements the strict reference
for whoever runs the next benchmark.

### Both deferred items are now closed

The two things I had left explicitly open are done: the window-overlap
quantification (here) and the severity-ladder validity check (earlier today).
Neither changed a conclusion; both replaced an assumption with a measurement.

Verifier now at 64 claims; all match.

---

## 3 September 2026 — Auditing whether any of this reproduces

Report: `reports/REPRODUCIBILITY_AUDIT.md`. Tool: `55_reproducibility_audit.py`.

### Why

Fifty-five scripts, nineteen reports, and a verifier depending on a web of
intermediate files. The README asserted the scripts were "numbered in dependency
order" — an assertion I had written and never checked. With everything else
closed, the largest remaining risk in the project was that none of it runs on a
fresh clone.

### It found a claim that could not be reproduced

**The combined sign test in `reports/WINDOW_OVERLAP.md` — 11 of 13 days improved,
p = 0.011 — was computed in an ad-hoc shell one-liner earlier today.**
`31_verify_claims.py` was checking a JSON file that no committed script
regenerated. A fresh clone would have failed that claim, and the verifier passing
on my machine proved nothing about it.

That is exactly the failure this tool exists to catch: **a verified claim resting
on an unreproducible file looks identical to a verified claim.** I had added it to
the verifier the same hour I computed it, which felt rigorous and was not. The
test now lives in `54_window_overlap.py` and produces the same numbers.

### And a false statement in my own README

`31_verify_claims.py` reads output from fifteen higher-numbered scripts — it
recomputes every headline figure from whatever the pipeline produced, so its
number records when it was written, not where it runs. "Numbered in dependency
order" was simply untrue. Renumbering would break the script names quoted
throughout the reports, so the README now states the two exceptions instead.

### Three bugs in the audit itself, before I trusted its output

A tool that reports its own artefacts as findings is worse than no tool, so these
are in the report too:

1. **f-strings parsed by regex** — `f"calibration_curve{sfx}.csv"` was captured as
   the filename `}.csv` and reported as an orphan read by ten scripts. Fixed by
   flattening `JoinedStr` in the AST.
2. **Filenames held in variables** — `ckpt = OUT / f"staleness{sfx}.csv"` then
   `to_csv(ckpt)` twenty lines later looked like a read with no write. Fixed by
   following one level of assignment.
3. **The audit as its own producer** — the phrase `-> write_text` inside its own
   allowlist matched the write-call pattern, making it the recorded producer of
   the decoder files. Fixed by excluding itself from its own scan.

The first pass reported 27 problems. After fixing the tool, 1 was real.

### Where it landed

**PASS.** 6 imports all declared, 35 consumed files all produced, no ordering
inversions, every script named across 53 documents present. Two files
(`reference_decoder.npz/.json`) are reached through a function return and are
named explicitly in `RESOLVED_BY_HAND` with their real producer, so the check is
a clean gate rather than a permanently-failing one.

Verifier still at 64 claims; all match.

---

## 3 September 2026 — One register, checked rather than written

Tool: `56_claims_register.py`. Output: `reports/CLAIMS_REGISTER.md`.

### Why

Nineteen reports and a long log, holding claims in genuinely different
conditions: some survived three attacks, three are retracted, one is
unanswerable with this data. Spread across documents those distinctions blur —
and the blurring always runs one way. **A withdrawn mechanism gets quoted as
though it still stood**, especially by me, weeks later, looking for a sentence.

### What it does

The register is the single source of truth, and it is validated rather than
prose:

1. every claim marked ESTABLISHED must cite a check in `31_verify_claims.py`
2. every cited check must actually exist
3. every cited report must exist on disk
4. any verifier check cited by **nothing** is reported as a coverage gap

Check 4 is the one worth having. It asks whether the evidence base and the story
have drifted apart — whether there are numbers being verified that no longer
support any claim anyone is making, or claims resting on nothing.

### Current state

**27 claims: 13 established, 7 limitations, 3 withdrawn, 1 unanswerable, 3
exploratory. Coverage 64 of 64 checks. PASS.**

Writing it out was itself the exercise. Three findings are now marked WITHDRAWN
with "do not quote" attached, one is marked UNANSWERABLE rather than negative,
and three are marked EXPLORATORY because they were not preregistered — including
the fifty-fold task-geometry variation, which is the most interesting thing found
in two days and is *not* a preregistered result.

Having to assign one of five statuses to every claim is a harder discipline than
writing a summary, because a summary lets a sentence sit between "we found" and
"we suspect". The register does not.

Verifier at 64 claims; audit passes; register passes.

---

## 3 September 2026 — A capability the project had, scored, and threw away

Report: `reports/ATTRIBUTION_ACCURACY.md`. Script: `57_attribution_accuracy.py`.

### The gap

The guard emits an attributed cause with every warning — "recalibrate", "an
electrode is failing", "nothing is wrong" are different responses, and the
docstring says as much. That capability has been implemented since the guard was
written and **scored since `21_score_report.py` was written**, and then thrown
away: the confusion matrix printed to stdout during a score-report run and was
captured nowhere. No report held it, no check verified it — and the README
carried a limitation about attribution with **no numbers behind it**.

I found this by grepping the reports for "attribution" and getting zero hits.

The prediction was already on record: `EXPECTED_ATTRIBUTION` in the guard maps
each fault mode to the component it should light, with a comment saying it was
written in advance "so attribution accuracy is scored against a stated prediction
rather than whatever mapping happens to fit the results". It just was never
scored into anything durable.

### The result

| | T11 | T5 |
|---|---|---|
| Overall | **56%** (chance 25%) | **52%** (chance 33%) |
| `GAIN_DRIFT` | 99.3% | 100% |
| `RATE_LOSS` | 87.1% | 21.2% |
| `CHANNEL_DROPOUT` | 46.3% | 87.7% |
| **`GEOMETRY_ROTATION`** | **0%** | **0%** |

Better than chance, nowhere near usable, and one mode fails **completely on both
arrays** — 200 episodes, not one named correctly. The two middle rows disagree
between participants badly enough that no story about them survives.

### Diagnosing the total failure, and being wrong about it

I expected the specificity-ordering rule to be the culprit: `dispersion` is
checked before `profile`, so a lit dispersion buries it. Measuring the calibrated
components on 40 rotation episodes says otherwise:

| component | median z | fraction lit |
|---|---|---|
| dispersion | **16.51** | 100% |
| profile | 1.92 | 80% |

`profile` **is** lit — in 80% of episodes. But dispersion is nearly nine times
larger, and **ranked by raw magnitude alone dispersion still wins 98% of the
time**. The rule is not what buries it.

**The fault is in the components.** The guard defines `dispersion` as *"channels
spread apart in gain, total conserved"*. `GEOMETRY_ROTATION` is injected with
Givens rotations, which are **norm-preserving by construction** — channels
exchange activity while the total is conserved. That is the same signature, by
definition.

So the preregistered mapping was wrong from the start. Rotation was never going to
light `profile` more than `dispersion`, because what rotation does to the data
*is* what `dispersion` measures. Re-ordering the rule would not fix it and neither
would re-weighting; the components would have to be redefined to be separable.

I did **not** re-tune the ordering to improve the number. The order was fixed in
advance and the failure is reported as it fell.

### A bug in the middle of this

Adding the diagnosis to the script, my edit consumed the line that writes the
JSON — so the diagnosis was computed, printed, and never saved, and the verifier
failed with two KeyErrors. Caught because the verifier failed, which is what it is
for. Restored.

Register now at 29 claims, verifier at 71, coverage 71/71. Audit passes.

---

## 4 September 2026 — The mode it never identifies is the easiest one to identify

Preregistered in `research/MODE_SEPARABILITY_NOTE.md`, prediction included.
Report: `reports/MODE_SEPARABILITY.md`. **Exploratory** — a supervised probe using
labels a monitor never has.

### The question

Attribution names `GEOMETRY_ROTATION` correctly 0% of the time. Two live
explanations with opposite consequences: the four components throw the
information away (fixable design problem), or the modes leave indistinguishable
traces (the capability should be dropped, not improved).

### The answer, and the prediction was met

**Rotation is the most separable mode there is.** Every pair involving it sits at
the top of the table on both participants; every pair without it sits at the
bottom.

| pair | T11 | T5 |
|---|---|---|
| rotation vs rate loss | **0.977** | **0.999** |
| gain drift vs rotation | **0.920** | **0.998** |
| dropout vs rotation | **0.857** | **1.000** |
| gain drift vs rate loss | 0.777 | 0.586 |
| dropout vs gain drift | 0.598 | 0.624 |
| dropout vs rate loss | 0.574 | 0.657 |

The preregistered prediction was gain drift vs rotation above 0.8; it came in at
0.920 and 0.998, by the mechanism stated in advance — gain drift scales channels
independently (a random per-channel pattern), rotation exchanges activity between
specific pairs (a structured one). A signed per-channel vector sees it; the
`dispersion` component, which discards the signs and the pairing, cannot.

> **The mode the monitor gets wrong 100% of the time is the mode most easily
> identified from the very features it is looking at.**

So the attribution failure is definitively a design problem, not missing
information. That resolves the question `ATTRIBUTION_ACCURACY.md` left open.

### But the rest of the table is a real ceiling, and it matters

Dropout, gain drift and rate loss separate from *each other* at only 0.57–0.78 —
two of those three pairs barely above chance, on both participants. That is not
fixable by better components. Those faults genuinely leave similar traces in
per-channel activity, which they should: each reduces or rescales what channels
report, differing mainly in which channels and by how much.

So the guard's 56% attribution is **not** all mechanism failure. The honest split:

- **rotation** — the guard's fault, fixable
- **dropout / gain / rate** — the features' fault, not fixable this way

I would have got this wrong in either direction without the probe. Reading only
the 0% I would have called attribution broken; reading only the 56% I would have
called it a ceiling. It is both, in different places.

### Discipline notes

The probe is an **upper bound**: it fits a discriminant per pair using the
injected labels, so a monitor could not reach these numbers even with perfect
components. λ was fixed at 0.1·trace/p in advance rather than tuned, and
validation is leave-one-**session**-out because episodes from one block are not
independent. Filed EXPLORATORY in the register as committed in advance, because a
supervised probe departs from the one-class discipline the rest of the project
holds to.

T5 has only 3 sessions after filtering to the test split, so its near-1.0 values
mean "clearly separable", not a precise estimate. T11's 12 sessions carry it.

Verifier 74 claims, register 31 claims, coverage 74/74, audit passes.

---

## 4 September 2026 — Is the headline carried by one easy fault mode? No, and I found a labelling error in the process

Preregistered in `research/PER_MODE_DETECTION_NOTE.md` with two predictions.
Report: `reports/PER_MODE_DETECTION.md`.

### Why I asked

`GEOMETRY_ROTATION` moves the `dispersion` component by **z = 16.5**. A fault
that shifts a component by sixteen deviations is not subtle, so the headline
detection number — registered as claim **C02** and quoted throughout — might be a
mixture of one trivially detectable mode and three that are not. If so the honest
claim is "the monitor detects rotation", which is materially different.

### Both predictions were wrong

| | predicted | T11 | T5 |
|---|---|---|---|
| rotation is the highest mode, above 0.8 | yes | highest, but **0.789** — and tied with GAIN_DRIFT at 0.787 | **third**, at 0.749 |
| headline without rotation falls to 0.60–0.65 | yes | **0.636** (drop 0.037) | **0.740** (drop 0.002) |

**The headline is not carried by one easy mode.** C02 stands as registered. On T5,
removing the most distinctive fault changes it by two thousandths.

### Why a 16σ signal gives only middling detection

This is the project's central finding in another costume. The risk score is the
largest of four calibrated components, and **healthy episodes produce large
component values too** — that is precisely why nothing passes the silence gate. A
fault sixteen deviations from the healthy median still overlaps a healthy
distribution that is itself wide and heavy-tailed.

Separability and detectability are different questions. Rotation is the most
*separable* mode (0.86–1.00 against the other modes) and a middling *detectable*
one, because telling two faults apart is easier than telling a fault from healthy
recording.

### The labelling error, which is the real find

My own preregistration, written twenty minutes earlier, called the headline
"session-level AUC". **It is window-level.** `31_verify_claims.py` concatenates
every window from every episode and compares them individually; every
session-level analysis elsewhere takes one median per episode.

Both are now computed side by side. The window-level version reproduces the
register exactly (0.693 and 0.708), which is how I confirmed the diagnosis. The
episode-level equivalents are 0.672 and 0.742 — differing by 0.02–0.03, **in
opposite directions** on the two participants.

The consequence for this study is small. The consequence for the project is not:
**claim C02's headline is a window-level statistic**, and claim C04 says windows
within a session are not independent (lag-1 r = 0.995). The point estimate is
sound; any interval or p-value built on it would not be. Now recorded in C02.

I appended the correction to the preregistration rather than editing it. Silently
fixing a preregistration after seeing results destroys the only thing it is for.

### Two smaller things

`CHANNEL_DROPOUT` is the **worst** mode on T11 (0.560) and the **best** on T5
(0.798) — the same participant disagreement attribution found, and why no per-mode
claim here is stated as general.

The `NONE` controls — no fault injected, crossed by noise — score **below** the
healthy group (0.163 and 0.387). If the pipeline were mislabelling episodes these
would sit with the faults. A sanity check that passes.

Verifier 78 claims, register 32, coverage 78/78, audit passes.

---

## 4 September 2026 — Sweeping for the error I found by accident

Preregistered in `research/UNIT_OF_ANALYSIS_NOTE.md` with three predictions.
Report: `reports/UNIT_OF_ANALYSIS.md`.

### Why sweep

Yesterday's per-mode work turned up, by accident, that claim C02's headline is a
**window-level** statistic while C04 says windows within a session are not
independent. Finding one instance of an error class by accident is not a reason
to fix one instance.

`reports/ACHIEVABILITY.md` carried a whole column of p-values built the same way,
and the reductio was sitting in its first table: `decoder_guard` at AUC **0.491**,
which the report's own verdict column calls *"at chance — no information"*,
carrying **p = 0.046**.

### All three predictions confirmed

| predicted | outcome |
|---|---|
| AUC point estimates barely move (< 0.05) | median shift **0.0202**; largest **0.0545**, slightly over the bound I stated |
| p-values become ordinary numbers | `p = 0` → < 0.001; `1.2e-303` → < 0.001; `2e-137` → 0.004 |
| at least one significant result flips to null, candidate the 0.491 row | **three flipped**, including that row: 0.046 → **0.848** |

Measured sample-size inflation: **26.6×** — 22,590 windows standing in for 850
episodes.

The starkest correction: `robust_dispersion` at the calibrate-once baseline was
published at **p = 3.4×10⁻¹⁵** and is actually **p = 0.144**. Fifteen orders of
magnitude, from an effect that is not there.

### What this does and does not touch

**Does not:** any conclusion. "0 of 48 configurations pass the gates" is a count,
the operating-point bound is arithmetic, and the aggregation limit is itself the
reason the correction was needed. The AUC point estimates and every verdict in
the report stand — an AUC is descriptive and does not assume independence.

**Does:** whether the supporting statistics were stated honestly. They were not.

### How it is recorded

Corrected **inline in `ACHIEVABILITY.md`**, at the top, with the original numbers
left exactly as first computed and a table of what each becomes. Not deleted, not
quietly recomputed. The corrected p-values report a **floor of < 0.001** rather
than an exact value, because a bootstrap cannot resolve a p finer than its own
resolution — which is the same discipline this whole correction is about, and is
precisely what the pooled test forgot when it printed `p = 0`.

One gap stated in the report: the T5 calibrate-once table is not covered, because
`episode_scores_T5.csv` was never produced — that baseline was never run for T5.

Verifier 82 claims, register 33, coverage 82/82.

---

## 4 September 2026 — Encoding my own mistakes as a linter, and it failed its first test

Report: `reports/STATISTICAL_HYGIENE.md`. Tool: `61_statistical_hygiene.py`.

### Why

At the end of the last piece of work I noticed a pattern and said it plainly:
three statistical error classes found in this project, **all by accident**, all
caught by checks written after the work they caught. Noticing that and then
carrying on waiting for the fourth would have been the wrong response to my own
observation.

So the three are now static checks:

1. **Inference on pooled, non-independent units** — cost: 4 p-values published as
   exactly `0`, sample size inflated 26.6×, three "significant" results not real.
2. **A comparison that can never be true** — cost: a fault-mix control that
   measured nothing and looked exactly like one that passed.
3. **An estimator biased by its own weights** — cost: a pooled AUC inflated from
   0.675 to 0.836.

### It missed its own motivating example

The first run flagged one site and **did not flag `26_achievability.py`** — the
code the check was written for. That file wraps `mannwhitneyu` inside a local
`auc(pos, neg)`, so the pooled variable never appears in the test's arguments.

A linter that cannot find the case it was written for is worse than no linter,
because it converts *unchecked* into *checked and clean*. Fixed by detecting local
functions that contain a test call and treating calls to them as test calls. That
took it from 1 site to 9, including all three known-bad lines in script 26.

**This is the fourth time here that a checking tool was itself wrong before it was
useful.** The reproducibility audit first reported 27 problems of which 1 was real;
this one reported 1 while missing the 3 that mattered. Opposite directions, same
mistake — and both were caught only by asking *does it find the thing I already
know is there?* That question is now the first thing I do with any check I write.

### What it found once it worked

Nine sites, eight of them deliberate and now documented with reasons: the pooled
statistics computed on purpose so the register can record what claim C02's number
is, and the inverse-variance weights Cochran's Q requires, already labelled
`..._BIASED_DO_NOT_QUOTE`.

One real change: `23_benchmark_figures.py` pools windows for a descriptive bar
chart with no inference attached — legitimate — but after correcting the same
quantity elsewhere its y-axis now says **"(window-level AUC)"**, so the number is
not mistaken for the episode-level one.

### The honest limit

These are the three mistakes *this project* made. A fourth class will not be
caught until it is found some other way and added. Learning from your own errors
only ever covers your own errors — which is an argument for the checks, not
against them, but not an argument that the checks are sufficient.

Four gates now: verifier (82 claims), reproducibility audit, claims register
(34 claims, 82/82 coverage), statistical hygiene. All pass.

---

## 4 September 2026 — I doubted a line I had already published, and it was wrong

Preregistered in `research/PERMUTATION_INVARIANT_NOTE.md` with the prediction and
its mechanism. Report: `reports/PERMUTATION_INVARIANT.md`.

### What I withdrew

Yesterday's separability probe concluded, and claim E05 recorded:

> rotation — the guard's fault, fixable
> dropout / gain / rate — **the features' fault, not fixable this way**

Re-reading my own method rather than my own conclusion, the second line could not
have been right. The probe fitted a **linear discriminant** — one fixed direction
in 384-dimensional channel space — but **which channels a fault touches is drawn
at random per episode**. `CHANNEL_DROPOUT` silences a random subset; `GAIN_DRIFT`
scales each channel by an independent random factor. No fixed direction identifies
either, so the model was structurally incapable of seeing them, and its failure
said nothing at all about the information.

### The result

Twelve permutation-invariant summaries of the same vector, everything else
identical:

| | per-channel (384-d) | invariant (12-d) |
|---|---|---|
| confusable trio, T11 | 0.650 | **0.987** |
| confusable trio, T5 | 0.623 | **0.998** |
| worst pair anywhere, T11 | 0.574 | **0.929** |
| rotation pairs, T11 | 0.918 | 0.968 |

Prediction met on both halves: the worst pair cleared 0.75 (at 0.929), and
rotation barely moved (+0.009, +0.001) because it was already near ceiling and
does have a genuine fixed-direction component.

### The control I nearly skipped

Twelve features beating 384 has an obvious rival explanation — a 384-feature
discriminant on ~400 episodes is heavily regularised and may just have underfit.
The gain could be **dimensionality**, not invariance, and I would have been making
exactly the kind of unfounded causal claim I have spent two days catching.

So: same pipeline, **12 randomly chosen raw channels**, 20 draws. Confusable trio
mean **0.702** (T11) and 0.756 (T5) — better than 384 channels, confirming the big
model was handicapped, and nowhere near 0.987. **The gain is the representation.**

### What it changes

E05 withdrawn, replaced by E06:

> **The information to identify all four fault modes is present and strong. The
> guard's four scalar components are the entire limitation.**

That is cleaner than what it replaces — the attribution failure is now an
unambiguous design problem rather than part design problem, part information
ceiling. And it produces the third concrete design recommendation of this line of
work: attribution should be built on **permutation-invariant distributional
summaries** of the per-channel change, not on projections onto fixed directions
and not on scalar magnitudes like `dispersion` that discard the shape.

### The habit worth naming

This is the second published conclusion I have withdrawn in two days, both found
the same way: re-reading my own *method* instead of my own *result*. The result
looked fine both times. The method did not survive the question "could this
possibly have detected what I concluded was absent?"

Verifier 86 claims, register 35, coverage 86/86.

---

## 5 September 2026 — I built the sharper detector the evidence pointed to. It was worse.

Preregistered in `research/INVARIANT_DETECTOR_NOTE.md` — one candidate, numeric
criteria, a prediction — all fixed before anything was built. Report:
`reports/INVARIANT_DETECTOR.md`.

### The reasoning that led here

The permutation-invariance result showed the information distinguishing faults
lives in the **shape of the per-channel change distribution**, which
`decoder_guard`'s four scalars discard. The constructive move is obvious: score
the shape instead. So I built exactly that, one-class, with the same structure as
the guard so only the features differ, and the same twelve summaries imported
unchanged rather than re-chosen.

### Both criteria failed and my prediction was wrong in direction

| | required | T11 | T5 |
|---|---|---|---|
| detection | beat 0.672 and 0.742 | **0.617** (−0.055) | **0.680** (−0.062) |
| silence gate | ≤ 10% trending | **98.5%** | **98.7%** |

I predicted +0.02 to +0.08 on both. It fell on both. I predicted the gate would
still fail, which it did — but at 98.5% against a current best of 31%, about
**three times worse than anything in the 48-configuration benchmark**.

Per the preregistration: one candidate. There is no tuned variant and there will
not be one. That constraint was written down precisely so that a failure here
could not turn into a search.

### The check that made it trustworthy

Median τ of 0.735 on healthy episodes is suspiciously strong, and my `score()`
clips at zero — which pins early windows to the floor and could **manufacture**
the trend. So I ran the same gate on the unclipped series: **98.9%**, median τ
**0.716**. The trend survives. The clipping did not cause it.

Without that check I could not have told a finding about invariant features from
a finding about my own scoring convention.

### What it means

> **The shape of the per-channel distribution drifts monotonically through a
> healthy session — and that is the same shape that distinguishes faults.**

A detector sharp enough to see the fault signature is necessarily sharp enough to
see ordinary drift, because they are the same quantity. It also explains the
detection loss: healthy scores climb through the session, inflating their medians
and compressing the gap with faulted episodes. **Sharpening the detector made the
healthy baseline noisier faster than it made the fault stand out.**

### Why this is the most useful failure in the project

The structural objection was previously an **inference** — four detectors, two
sharing a failure pattern, and an argument about what they had in common. This is
a **measurement**: I built the more sensitive detector the evidence pointed to,
committed the criteria in advance, and watched it lose on both axes.

An inference became a demonstration, and it cost one preregistered experiment.

### The recommendation splits

`PERMUTATION_INVARIANT.md` recommended invariant summaries for **attribution**.
That stands — it rests on a supervised probe of telling faults apart, untouched by
this. **It must not be extended to detection**, where the same features are now
actively refuted. The preregistration said those were different problems before
running; the numbers now say it too.

Verifier 90 claims, register 37, coverage 90/90.

---

## 5 September 2026 — The other half of the recommendation fails too

Preregistered in `research/INVARIANT_ATTRIBUTION_NOTE.md` with the mapping, rule,
criteria and prediction fixed before the code existed. Report:
`reports/INVARIANT_ATTRIBUTION.md`.

### Why I tested my own surviving recommendation

`PERMUTATION_INVARIANT.md` recommended invariant summaries for attribution on the
strength of a **supervised** probe. Yesterday the analogous move for detection was
built label-free and failed on both axes. The attribution half sat exposed to the
same risk, untested. Leaving it standing would have been inconsistent with what I
had just demonstrated.

### Both criteria failed, both predictions wrong

| | required | T11 | T5 |
|---|---|---|---|
| overall accuracy | beat 56.3% and 52.5% | **51.1%** (−5.2 pts) | **39.7%** (−12.8 pts) |
| rotation | beat 25% chance | **2.1%** | **6.1%** |

I predicted 70–85% and rotation above 50%. It got worse on both participants.

### The failure is diagnostic, and it is my reasoning that was wrong

**`sd`, assigned to `GAIN_DRIFT`, wins almost everything** — 60 of 89 dropout
episodes, 73 of 95 rotation episodes. Every fault raises the spread of the
per-channel distribution, so a generic spread measure is elevated by all of them
and swamps the specific features.

**This is the `profile` residual problem in a new costume**, and my
preregistration explicitly declined the fix:

> *"No specificity ordering… all four features are equally specific by
> construction."*

That was wrong. I reasoned about how the **faults** differ and never asked how the
**features** overlap. `sd` is not specific to gain drift; it is generic.

Second failure, separate: on T5 `frac_severely_down` never wins once — dropout
scores 0% and that column is empty across the whole table.

### What I am deliberately not doing

The fix is obvious: put a specificity ordering over the four features. **I am not
building it.** One candidate was committed, and a failure is not a licence to keep
going until something works. That constraint exists exactly for this moment — when
the fix looks easy and the temptation is strongest. It is recorded as an untested
hypothesis for a future attempt, not as a result.

### The uncertainty I flagged was moot, and flagging it still paid

The preregistration named `GEOMETRY_ROTATION → skew` as the assignment I was least
sure of, with `kurtosis` as the alternative. Neither would have helped — rotation
is named `GAIN_DRIFT` 73 times out of 95, so the binding failure is `sd`
dominating. Because I wrote the uncertainty down first, I can **rule it out** as
the cause instead of speculating about it now.

### The pattern this completes

Both halves of that recommendation have now been tested label-free. Both fail.

> **A supervised demonstration that information exists has, twice, failed to
> translate into a label-free rule that uses it.**

Twice is not a law. But it is now two independent measurements of a gap I would
otherwise only be able to argue about, and it is the sharpest methodological
finding of this line of work. Separability under a fitted discriminant is a **weak
guarantee** about what an unsupervised monitor can achieve.

`PERMUTATION_INVARIANT.md` is corrected in place: invariant summaries are evidence
the information **exists**, not a demonstrated **design**. E04 is annotated as
narrowed.

### Where the research stands

This was the last question this dataset can answer that I could identify. Every
remaining one — does any of it generalise, is the two-participant disagreement
real, can an ordered rule work — needs the third participant.

Verifier 93 claims, register 38, coverage 93/93.
