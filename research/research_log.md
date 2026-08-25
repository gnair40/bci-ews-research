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
