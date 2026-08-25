# DATASET_README — Pun et al. (2024) MINDFUL intracortical BCI dataset

**Maintained by:** Gayathri Nair · ISEF Year 1 project
**Last updated:** 2026-08-25
**Status:** ⚠️ **Dataset NOT yet downloaded.** Network access to Dryad is blocked in
the current environment (see [§7](#7-current-blocker-network-access)). Everything in
this document is sourced from the authors' published analysis code and from the
literature, and is labelled accordingly. **No claim here has been checked against the
actual data files.**

---

## 0. How to read this document

Research documentation is only useful if it distinguishes *what you know* from *what
you assume*. Every factual claim below carries one of three labels:

| Label | Meaning |
|---|---|
| **[CODE]** | Proven by reading the authors' own published analysis code (`github.com/ewinapun/MINDFUL`, commit `1809e13`). This code must load the real files to run, so the file and variable names it references are reliable. |
| **[LIT]** | Reported in the paper / abstract / our literature review. Plausible and citable, but not independently checked by us. |
| **[UNVERIFIED]** | An open question. Must be answered by opening the actual files. |

A claim with no label is a statement about *this repository*, not about the dataset.

---

## 1. Dataset identification

| Field | Value | Source |
|---|---|---|
| Short identifier | `n2z34tn5s` | given in project notes |
| **Full DOI** | **`10.5061/dryad.n2z34tn5s`** | [LIT] |
| Resolver URL | https://doi.org/10.5061/dryad.n2z34tn5s | — |
| Dryad landing page | https://datadryad.org/dataset/doi:10.5061/dryad.n2z34tn5s | [LIT] |
| Dryad publication date | 25 October 2024 | [LIT] |
| Analysis code | https://github.com/ewinapun/MINDFUL | [CODE] |
| Code language | MATLAB (written on R2022b) | [CODE] |
| Dryad version number | [UNVERIFIED] — recorded automatically by our download script |
| Total size | [UNVERIFIED] |
| Licence | [UNVERIFIED] — Dryad deposits are normally CC0, **confirm before publishing** |

### Associated publication

> Pun, T.K., Khoshnevis, M., Hosman, T., et al. (2024).
> *Measuring instability in chronic human intracortical neural recordings towards
> stable, long-term brain–computer interfaces.*
> **Communications Biology** 7. doi:[10.1038/s42003-024-06784-4](https://doi.org/10.1038/s42003-024-06784-4)

Preprint (open access, useful if you hit a paywall):
bioRxiv [10.1101/2024.02.29.582733](https://doi.org/10.1101/2024.02.29.582733)

> **Note on the title.** The preprint says "multi-day"; the journal version says
> "chronic". Same study — do not treat these as two papers. [CODE] (the repo's own
> README cites the preprint title.)

The method introduced is called **MINDFUL** — *Measure Instabilities in Neural Data
for Useful Long-term iBCI*. [CODE]

### Why this dataset (link to the research question)

Per our literature review, this deposit has three properties the project needs:

1. **Fixed decoder** — sessions were run without recalibration, so drift is not
   erased by the experimenters. [LIT]
2. **Paired neural *and* behavioural time series.** [LIT] — and see §5, which
   confirms both exist in the files. [CODE]
3. **Longitudinal** — reported spans of 142 days (T5) and 28 days (T11). [LIT]

---

## 2. What this repository does with the data

```
bci-ews-research/
├── DATASET_README.md          ← you are here
├── scripts/
│   ├── 01_download_dataset.py ← fetches from Dryad + verifies checksums
│   └── 02_inspect_dataset.py  ← inventories whatever is in data/raw/
├── data/
│   ├── raw/                   ← untouched download. READ-ONLY. Git-ignored.
│   └── processed/             ← anything we compute. Regenerable. Git-ignored.
└── reports/                   ← inventory.json and exploration write-ups
```

**The raw/processed split is not bureaucracy.** If analysis code can write into the
folder holding your original data, then one buggy line can silently corrupt the
thing you cannot regenerate, and you may not notice for weeks. Keeping `data/raw/`
strictly read-only means any mistake is always recoverable by re-running the
download. This is standard practice in reproducible research.

**Why the data are not committed to Git.** The files are large and already have a
permanent public home (the DOI). Committing them would bloat the repository without
adding provenance. `scripts/01_download_dataset.py` + `download_manifest.json`
reproduce the exact bytes on any machine — that is what reproducibility requires.

---

## 3. How to download it (reproducibly)

```bash
pip install -r requirements.txt

python3 scripts/01_download_dataset.py --list-only   # preview, downloads nothing
python3 scripts/01_download_dataset.py               # actually download
python3 scripts/02_inspect_dataset.py --extract      # inventory what arrived
```

The download script writes **`data/raw/download_manifest.json`**, recording the DOI,
the Dryad *version number*, every filename, its size, its MD5 checksum, and the UTC
timestamp. That file is your provenance record — it is what lets you state in a
write-up exactly which version of the data you analysed.

**What an MD5 checksum is:** a short fingerprint computed from a file's contents. If
a download is truncated or corrupted, the fingerprint changes completely. The script
recomputes it locally and compares against Dryad's; a mismatch aborts with an error
rather than letting you analyse a damaged file.

---

## 4. Expected file structure

**[CODE]** — reconstructed from `utils/ConcatSavedSessionsData.m`, which is the
function the authors use to load these files. It walks the tree literally, so the
layout below is what the code *requires* the deposit to look like:

```
<dataset root>/
├── T5/
│   ├── day_<N>/                  ← one folder per recording session
│   │   ├── block_<M>/            ← one folder per block within that session
│   │   │   ├── data.mat          ← neural features + kinematics
│   │   │   ├── info.mat          ← behavioural performance metrics
│   │   │   └── task.mat          ← which task was run
│   │   └── block_<M+1>/ ...
│   └── day_<N+1>/ ...
├── T11/
│   └── (same structure)
└── T11(additional)/
    ├── random_targets/           ← ~10 min, random-target task
    └── personal_use/             ← ~16 min, free web browsing
```

Evidence for each part:

- Session folders are named `day_<number>`: the loader does
  `if strcmp(usedSessionList{i}(1:4),'day_')` then `str2double(...(5:end))` to get
  `info.trialDay`. So the number after `day_` is a **trial day** (days since array
  implantation), not a sequential session index. [CODE]
- Block folders start with `block`: the loader does `str2double(block_folder(7:end))`,
  i.e. it reads the number from character 7 onward of e.g. `block_3`. [CODE]
- The three `.mat` filenames are hard-coded: `'task.mat'`, `'info.mat'`, `'data.mat'`. [CODE]
- The two extra T11 folders appear in `examples/fig6_various_reference_tasks.m` as
  `T11(additional)/random_targets` and `T11(additional)/personal_use`. [CODE]
  Our literature review reports these as ~10 min (day 665) and ~16 min (day 658). [LIT]

> **[UNVERIFIED]** The authors' script sets `dirpath = 'Y:\TransferSpace\MINDFUL(2024)'`
> — a path on their own lab machine. The Dryad deposit may be packaged as one or
> more `.zip` archives that unpack into this layout, rather than as loose folders.
> `02_inspect_dataset.py --extract` handles either case.

---

## 5. Variable dictionary

**⚠️ Read this warning first.** The names below are confirmed to exist [CODE], but a
variable's *meaning* is not established by its name. The "interpretation" column is
my reading of how each variable is *used* in the authors' code — it is [UNVERIFIED]
until checked against the paper's Methods and the deposit's own README.

### 5.1 `data.mat` — neural and kinematic time series

| Variable | Used as | Interpretation (**needs confirming**) |
|---|---|---|
| `data` / `feats` / `nctx` | neural feature matrix | Neural features, one row per time bin. The loader accepts three alternative names and, if `nctx` **and** `spikePower` both exist, concatenates them: `data = [nctx spikePower]`. [CODE] That strongly implies two feature families — plausibly threshold-crossing rates and spike-band power — but this is interpretation. |
| `spikePower` | concatenated onto `nctx` | A second neural feature family. [CODE] |
| `labels` | `theta = atan2(labels(:,2), labels(:,1))` in `supp_analysis.m` [CODE] | A 2-D vector per time bin whose angle is meaningful — most likely **intended movement direction** (the decoder's training target). Two columns = x, y. |
| `cursorVel` | `Xhat = extra.cursorVel` [CODE] | **Decoded cursor velocity** — the decoder's *output*. The variable is called `Xhat`, and in statistics a "hat" denotes an estimate. Two columns = x, y velocity. |
| `startStops` | `events.trialStartStop` | Trial boundaries as **row indices into the time-bin series**: column 1 = first bin of the trial, column 2 = last bin. This is the link between trial-level and bin-level data. [CODE] |
| `excludeTrials` | logical mask | Trials the authors flag for exclusion (outliers). `params.excludeNonTrials = 1` is set in most figure scripts, so **the published analyses exclude these**. [CODE] |
| `moveDirVect` | per-trial | A movement-direction vector per trial. [UNVERIFIED] |
| `gestGoalState` | per-trial | Goal state; possibly gesture-related. [UNVERIFIED] |

### 5.2 `info.mat` — behavioural performance (loaded into the `extra` struct)

**This file is the behavioural half of the project.** Everything in it is a
performance measure.

| Variable | Interpretation (**needs confirming**) | Confidence |
|---|---|---|
| `angleErrorPerTrial` | **Angle error, one value per trial, in degrees.** The angle between the direction the cursor was driven and the direction of the target. Range 0–180°: 0° = moving straight at the target, 180° = straight away. **Lower is better.** | [CODE] name + [CODE] usage: `fig1` bins it over `0:4:180` and axis-labels it `0°/90°/180°`. |
| `angleError` | Same quantity **per time bin** rather than per trial. Used as `k.extra.angleError` against bin-indexed data throughout. | [CODE] |
| `trialSuccess` | Logical: did the trial reach its target? Used as `extra.angleErrorPerTrial(extra.trialSuccess)`. | [CODE] |
| `timeToTarget` | Time taken to acquire the target. Lower is better. | [CODE] listed in `fig_supp_performance_comparison.m` |
| `pathEfficiency` | How direct the cursor path was vs. a straight line. Higher is better. | [CODE] same source |
| `orthChanges` | Count of orthogonal direction changes — a measure of jitter/instability in the movement. | [CODE] same source |

> **Why `angleError` matters most.** The headline result of the paper regresses a
> neural-instability measure (KL divergence) against angle error, reporting Pearson
> r = 0.93 (T5) and 0.72 (T11). [LIT] Angle error is therefore the paper's primary
> behavioural performance variable, and the natural quantity for our project to treat
> as "performance" too. But see §8 — whether it is the right variable for an
> *early-warning* analysis is a scientific decision that is yours to make, not mine.

### 5.3 `task.mat`

| Variable | Interpretation | Confidence |
|---|---|---|
| `name` | Task/"game type" identifier, compared as `strcmp(p.useGameTypes, name)`. | [CODE] |

Task names referenced in `fig6_various_reference_tasks.m`: `'center out'`, `'fitts'`,
`'personal use'`, `'mixed tasks'`. [CODE]

### 5.4 Derived/session-level fields (built by the loader, not stored on disk)

These are **computed** by `ConcatSavedSessionsData.m`, so you will not find them as
files — but you will need equivalents in Python: `sessionStartStop`,
`blockStartStop`, `trialStartStop`, `trialsPerBlock`, `trialsPerSession`,
`pointsPerSession`, `sessionNumberPerTrial`, `sessionNumberPerBlock`, `trialDay`. [CODE]

---

## 6. Unit of observation

**This is the single most important structural fact about the dataset**, because it
determines what any statistical test is actually testing.

The data are **nested**, at four levels: [CODE]

```
participant  (T5, T11)
   └── session / trial day        folder  day_<N>
         └── block                folder  block_<M>
               └── trial          rows of startStops
                     └── time bin rows of the data matrix
```

- **The finest unit is the time bin.** One row of `data` = one bin.
- **Bin width = 20 ms (50 Hz).** [CODE] — `MINDFUL.m` line 1213 converts step counts
  to seconds by multiplying by `0.02`, and `BGzscoreNew.m` sets `winFs = 50` Hz.
  This is a solid inference from two independent places in the code, but confirm it
  against the paper's Methods.
- **Trials index into bins** via `startStops`.
- Behavioural metrics in `info.mat` are **per trial**; neural data are **per bin**.
  Any analysis linking them must decide how to align the two, and that decision is
  itself a scientific choice.

**Why nesting matters:** observations within a participant are not independent of one
another. With **n = 2 participants** [LIT], you cannot make population-level claims.
Any result is a within-participant result, replicated (or not) in a second person.
That is a real and reportable limitation, not a flaw to hide.

---

## 7. Current blocker: network access

`scripts/01_download_dataset.py` is written, tested, and works — but **cannot reach
Dryad from this cloud environment.** The failure is reproducible:

```
$ python3 scripts/01_download_dataset.py --list-only
[1/4] Looking up dataset record
      https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.n2z34tn5s
    attempt 1/4 failed (ProxyError); retrying in 2s ...
    ...
ERROR: Gave up fetching ... ProxyError('Unable to connect to proxy',
       OSError('Tunnel connection failed: 403 Forbidden'))
```

The environment's egress proxy reports:

```json
{"kind": "connect_rejected",
 "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
 "host": "datadryad.org:443"}
```

**In plain language:** this container may only contact an approved list of websites.
`datadryad.org` is not on it. Hosts tested:

| Host | Reachable? |
|---|---|
| `github.com`, `raw.githubusercontent.com` | ✅ yes |
| `*.amazonaws.com` (S3) | ✅ yes |
| `pypi.org` (Python packages) | ✅ yes |
| `datadryad.org` | ❌ **blocked** |
| `doi.org`, `api.datacite.org`, `api.crossref.org` | ❌ blocked |
| `nature.com`, `ncbi.nlm.nih.gov`, `zenodo.org` | ❌ blocked |

This is a **settings** problem, not a code problem, and the fix is not something a
script can do — routing around an organisational network policy would be improper
even if it were possible. See the repository's issue notes / ask your session owner
to widen the environment's network policy. Documentation:
https://code.claude.com/docs/en/claude-code-on-the-web

### How to fix it (decided: recreate the environment)

The environment is currently on the **Trusted** network access level, which allows
only an Anthropic-maintained allowlist (package registries, GitHub, cloud SDKs).
Dryad is not on that list. There are four levels:

| Level | Outbound connections |
|---|---|
| **None** | nothing |
| **Trusted** | allowlisted domains only — *this is what we have* |
| **Full** | any domain |
| **Custom** | your own allowlist, optionally plus the defaults |

**Steps — do this at [claude.ai/code](https://claude.ai/code):**

1. In the row **above the message box**, click the **cloud icon** showing the current
   environment's name. (There is no settings page or direct URL for this selector.)
2. Choose **Add cloud environment** — or hover an existing environment and click the
   **gear icon** to edit it.
3. Set **Network access** to **Custom**, and in **Allowed domains** enter one domain
   per line:

   ```text
   datadryad.org
   *.datadryad.org
   doi.org
   *.amazonaws.com
   ```

   Then **tick "Also include default list of common package managers"** — without it
   you lose PyPI and GitHub, and nothing will install.

   > `*.amazonaws.com` is included because Dryad serves large file downloads from
   > Amazon S3 storage, so a download can be redirected there. `doi.org` lets the DOI
   > resolve. Selecting **Full** instead of **Custom** also works and is simpler, but
   > **Custom** is the tighter, better-practice choice.

4. *(Optional but recommended)* In the same dialog, set the **Setup script** to:

   ```bash
   pip install -r requirements.txt
   ```

   This runs automatically before Claude starts, so every future session already has
   pandas, numpy, scipy, h5py and matplotlib installed.

5. Start a **new session** on this repository (branch
   `claude/isef-research-pipeline-9zt4uq`) using that environment, and run:

   ```bash
   pip install -r requirements.txt
   python3 scripts/01_download_dataset.py --list-only
   python3 scripts/01_download_dataset.py
   python3 scripts/02_inspect_dataset.py --extract
   ```

**Alternatives if the above is inconvenient:**

- Run `scripts/01_download_dataset.py` on your own laptop (produces the correct
  manifest with checksums), then copy `data/raw/` across.
- Download manually from the Dryad landing page into `data/raw/`. The inspection
  script still works, but provenance is weaker — record the version number and
  download date by hand.

---

## 8. Open questions to resolve once the data are in hand

Ordered by how much they matter to the research question.

### Structural
1. Confirm the actual top-level layout (loose folders vs. zip archives).
2. **How many sessions, blocks, and trials per participant?** The literature review
   flags actual trial counts as unverified — and this number decides whether a
   rolling-window analysis is possible at all.
3. Confirm bin width is 20 ms from the paper's Methods, not just from the code.
4. How many neural feature columns, and what are they? Confirm the
   threshold-crossing / spike-band-power interpretation of `nctx` + `spikePower`.
5. Are `day_<N>` numbers really days-since-implant? If so, what are the **gaps**
   between consecutive sessions? Irregular sampling is a serious problem for
   time-series methods that assume even spacing.

### Semantic
6. Confirm `angleError` units (degrees) and sign convention from the Methods.
7. What exactly does `excludeTrials` exclude, and on what criterion? Our analysis
   must make the same choice as the paper's, or explicitly justify differing.
8. What is `labels` — intended direction, or something else?
9. Is `cursorVel` the decoder's raw output or post-processed (smoothed, gain-scaled)?

### Directly relevant to the early-warning question
10. **Is the decoder genuinely fixed across all sessions?** The literature review
    calls this "the single most important feature". Verify it in the Methods, and
    check whether any session was a calibration session
    (`p.oneCalBlock` in the loader hints that first-block-per-session calibration
    data may exist [CODE]).
11. **Does performance actually decline?** If angle error never meaningfully worsens,
    there is no "deterioration" to anticipate and the project needs rethinking. This
    is the first thing to plot.
12. Are there enough sessions to resolve a recovery rate? (van der Bolt et al. 2021,
    "No warning for slow transitions" — flagged in the literature review as the paper
    most likely to sink the project.)

---

## 9. Glossary

| Term | Plain-language meaning |
|---|---|
| **iBCI** | *intracortical* brain–computer interface — electrodes implanted in the brain, not on the scalp. |
| **Decoder** | The algorithm converting neural activity into cursor movement. |
| **Fixed decoder** | A decoder left unchanged over time (not retrained). Essential here: recalibration would erase the drift we want to study. |
| **Block** | A continuous run of trials, typically a few minutes. |
| **Trial** | One attempt to move the cursor to one target. |
| **Trial day** | Days elapsed since the electrode array was implanted. |
| **Bin** | A short fixed time window (here 20 ms) over which neural activity is counted/averaged. |
| **Threshold crossings** | A count of how often the voltage on an electrode crossed a threshold — a cheap proxy for neural firing. |
| **Spike-band power** | Signal energy in the frequency band where spikes live. |
| **Angle error** | Degrees between the cursor's actual direction and the direction of the target. Lower = better. |
| **KL divergence** | A number measuring how different two probability distributions are. MINDFUL uses it to quantify how far current neural activity has drifted from a reference period. |
| **z-score** | Rescaling so a variable has mean 0 and standard deviation 1, making differently-scaled channels comparable. |
| **NaN** | "Not a Number" — the standard marker for a missing value. |
| **Checksum / MD5** | A fingerprint of a file's contents, used to prove it downloaded intact. |
| **Provenance** | The documented record of where data came from and how it was obtained. |

---

## 10. Reproducibility record

| Item | Value |
|---|---|
| Environment | Claude Code cloud container, Linux 6.18.44, Python 3.11.15 |
| pandas | 3.0.5 |
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| matplotlib | 3.11.1 |
| h5py | 3.16.0 |
| MINDFUL reference code | `github.com/ewinapun/MINDFUL` @ `1809e132549f3c4b03327e3a14c748927d765e6e` |
| Dataset downloaded? | **No** — blocked, see §7 |

---

## 11. Attribution

The dataset is the work of Pun, Khoshnevis, Hosman and colleagues, and the BrainGate2
consortium. If any of it is used in a project write-up, cite both the paper and the
Dryad DOI, and check the deposit's licence terms (§1). Nothing in this repository
redistributes their data.
