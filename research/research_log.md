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
