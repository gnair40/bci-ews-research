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
