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
| **Dryad version number** | **6** (API version record `324345`) | [CODE] verified via API |
| Total size | 392.9 MB — `MINDFUL_Data.zip` 411,951,588 bytes + `README.md` 3.3 KB | [CODE] verified via API |
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
│   ├── 02_inspect_dataset.py  ← inventories whatever is in data/raw/
│   ├── 03_load_dataset.py     ← nested .mat files → tidy pandas tables
│   └── 04_explore_dataset.py  ← descriptive stats + figures → exploration report
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
python3 scripts/03_load_dataset.py --save            # build tidy tables
python3 scripts/04_explore_dataset.py                # explore + write the report
```

The last step writes `reports/DATASET_EXPLORATION.md` and five figures into
`reports/figures/`. Its **Computed** sections are filled in automatically from
the data; its **Requires your judgement** sections are deliberately left blank,
because those are scientific decisions rather than calculations.

The download script writes **`data/raw/download_manifest.json`**, recording the DOI,
the Dryad *version number*, every filename, its size, its MD5 checksum, and the UTC
timestamp. That file is your provenance record — it is what lets you state in a
write-up exactly which version of the data you analysed.

**What an MD5 checksum is:** a short fingerprint computed from a file's contents. If
a download is truncated or corrupted, the fingerprint changes completely. The script
recomputes it locally and compares against Dryad's; a mismatch aborts with an error
rather than letting you analyse a damaged file.

---

## 4. File structure — CONFIRMED

**[VERIFIED]** — the deposit has been downloaded, checksum-verified and opened.
Everything below is now observed fact, not inference.

The download is a single archive, `MINDFUL_Data.zip`, which unpacks with a
**doubled top folder**:

```
data/raw/
├── MINDFUL_Data.zip            ← the download (392.9 MB, SHA-256 verified)
├── README.md                   ← Dryad's README, by the dataset authors
├── download_manifest.json      ← our provenance record
├── _FOLDER_NOTES.md            ← our notes (renamed to avoid collision)
└── extracted/
    └── MINDFUL_Data/
        └── MINDFUL_Data/       ← note: nested twice
            ├── readme.md
            ├── T5/    day_2121 … day_2149     (6 sessions, 21 blocks)
            ├── T11/   day_658  … day_800      (15 sessions, 29 blocks)
            └── T11(additional)/
                ├── personal_use/day_658/      (2 blocks)
                └── random_targets/day_665/    (2 blocks)
```

Block folders are named **`Block_01`, `Block_05`, `Block_19`…** — capital `B`,
zero-padded, and **not contiguous**: block numbers are the original session
block indices, so gaps are expected (T11 day 672 has `Block_19` and `Block_20`).
Only selected blocks from each session were deposited.

Each block folder contains exactly three files: `data.mat`, `task.mat`, `info.mat`.
All are **pre-v7.3 MATLAB format**, readable with `scipy.io.loadmat`.

### Actual size of the dataset

| Participant | Cohort | Sessions | Blocks | Trials | Bins (20 ms) | Features | Trial days | Span |
|---|---|---|---|---|---|---|---|---|
| **T11** | main | 15 | 29 | 1,839 | 440,045 | 384 | 658 – 800 | **142 days** |
| T11 | personal_use | 1 | 2 | 80 | 60,269 | 384 | 658 | — |
| T11 | random_targets | 1 | 2 | 182 | 30,420 | 384 | 665 | — |
| **T5** | main | 6 | 21 | 1,200 | 251,974 | 192 | 2121 – 2149 | **28 days** |

> ### ⚠️ Correction to the literature review
>
> The literature review states the two participants span *"142 days and 28 days
> respectively"* in an order that reads as T5 = 142, T11 = 28. **It is the other
> way round.** T11 is the longitudinal participant (15 sessions over 142 days);
> T5 has 6 sessions over 28 days. Any plan that treated T5 as the long record
> needs revising — **T11 is the primary participant for a longitudinal analysis.**

### Session spacing — uneven

| Participant | Trial days | Gaps (days) | Min | Median | Max | Evenly spaced? |
|---|---|---|---|---|---|---|
| T11 | 658, 665, 672, 675, 689, 692, 702, 709, 715, 727, 751, 758, 770, 783, 800 | 7, 7, 3, 14, 3, 10, 7, 6, 12, 24, 7, 12, 13, 17 | 3 | 8.5 | 24 | **No** |
| T5 | 2121, 2126, 2128, 2133, 2135, 2149 | 5, 2, 5, 2, 14 | 2 | 5 | 14 | **No** |

**This matters.** Most time-series methods — including the autocorrelation and
variance indicators central to this project — assume evenly spaced samples. At
session level the spacing is not even, so any session-level windowed analysis
must justify how it handles that. Within a block, bins *are* evenly spaced at
20 ms, so bin-level analysis does not have this problem.

---

## 5. Variable dictionary — CONFIRMED

**[VERIFIED]** against the deposit's own `README.md` and against the files.

> ### ⚠️ Correction to an earlier inference
>
> An earlier draft of this document placed `startStops`, `excludeTrials` and
> `moveDirVect` in `data.mat`, inferred from the authors' MATLAB loader. **They
> are in `task.mat`.** The loader reads all three `.mat` files into one
> workspace, so the code alone could not reveal which file each came from. This
> is a concrete example of why the dataset's own documentation must be checked
> rather than inferred from code — the guess was wrong and would have broken the
> loader.

Definitions used below, from the authors' README:
`nStep` = number of 20 ms bins · `nChan` = channels across both arrays ·
`nTrial` = trials, where **a trial spans target cue to target acquisition**.

### 5.1 `data.mat` — neural features and kinematics (per 20 ms bin)

| Variable | Shape | What it is (authors' words) |
|---|---|---|
| `nctx` | [nStep × nChan] | Raw concatenated neural features — **non-causal threshold crossings (RMS < −3.5)** |
| `spikePower` | [nStep × nChan] | Raw concatenated neural features — **spike band power (250–5000 Hz)** |
| `labels` | [nStep × 2] | **Inferred** 2-D cursor-to-target vector [x, y] |
| `cursorVel` | [nStep × 2] | **Decoded** 2-D velocity vector output from the decoder [x, y] |

**Feature counts differ between participants:**

| | `nctx` | `spikePower` | Total features | dtype of `nctx` |
|---|---|---|---|---|
| **T5** | 192 | **absent** | **192** | `uint64` (raw counts) |
| **T11** | 192 | 192 | **384** | `float32` |

This is a real property of the deposit, not an error. Any analysis pooling the
two participants must handle it. `labels` is also absent from the two
`personal_use` blocks (free web browsing has no target, so no cursor-to-target
vector exists).

> **`labels` vs `cursorVel` — the distinction that matters most.** `labels` is
> where the cursor *should* go (inferred intent); `cursorVel` is where the
> decoder actually *drove* it. The angle between them is the angle error. One is
> intent, the other is output — do not conflate them.

### 5.2 `task.mat` — task structure (per trial and per block)

| Variable | Shape | What it is |
|---|---|---|
| `name` | str | Task name — observed values: `'Fitts'`, `'fitts'`, `'circleOfCircles'`, `'Personal use'` (note the inconsistent capitalisation) |
| `nPointsPerBlock` | 1×1 | Number of 20 ms bins in this block |
| `startStops` | [nTrial × 2] | Trial **[start, stop] time indices**, chronological |
| `excludeTrials` | [nTrial × 1] | Bool — **True if the trial is excluded because mean noise exceeded 5% during the trial** |
| `useClick` | [nTrial × 1] | Bool — True if a click was used to select the target |
| `moveDirVect` | [nTrial × 2] | Movement direction vector [x, y] |

**Indexing is 1-based (MATLAB), confirmed empirically.** Across all 54 blocks:
5 have `max(stop) == nPointsPerBlock`, **none** have `max(stop) == nPointsPerBlock − 1`,
none overrun, and the smallest start index anywhere is **88** — never 0.
`nPointsPerBlock` equals the row count of `nctx` in every block.

### 5.3 `info.mat` — performance measures

**Per trial:**

| Variable | What it is | Observed range |
|---|---|---|
| `angleErrorPerTrial` | **Median** angular error for the trial, degrees. *(Note: median, not mean — an earlier draft omitted this.)* | 5.0 – 171.3 |
| `trialSuccess` | Bool — target acquired | 0/1 |
| `timeToTarget` | Time to target, **seconds** | 0.56 – 10.1 |
| `pathEfficiency` | Path directness per trial, higher is better | 0.04 – 0.93 |
| `orthChanges` | Count of orthogonal direction changes | 0 – 16 |

**Per bin:**

| Variable | What it is |
|---|---|
| `angleError` | **Instantaneous** angular error, degrees |
| `targetPos` | Target position [x, y] |
| `cursorPos` | Cursor position [x, y] |
| `magEst` | Adjusted decoded cursor-to-target magnitude |
| `avgOutliers` | Max average outlier across channels per bin |
| `prctOutliers` | Percent of ns5 outliers per channel per bin (sparse; not in every block) |

**Per block:** `percentCorrect` — success rate for the block, as a percentage.

---

## 6. Unit of observation — CONFIRMED

```
participant (2)
  └── session / trial day (21 across both)
        └── block (54)
              └── trial (3,301)
                    └── 20 ms bin (782,708)
```

- Behavioural performance: **per trial** (and `percentCorrect` per block).
- Neural features and `angleError`: **per 20 ms bin**.
- `startStops` maps trials onto bins (1-based, inclusive).
- **Total recording: 4.35 hours** across both participants.

Trials per block range from 24 to 106 (median ≈ 49 for T5, ≈ 69 for T11).

**Consequence:** observations are nested and not independent. With **n = 2
participants**, no population-level claim is available; any finding is a
within-participant result that either replicates in the second person or does not.

### Data quality — measured, not assumed

| Column | Missing |
|---|---|
| `path_efficiency` | 14.33% |
| `success`, `orth_changes` | 4.70% |
| `angle_error_deg`, `time_to_target`, `excluded` | 2.42% |

Most of the 2.42% is the 80 `personal_use` trials, which have no target and so
no performance metrics at all. Excluded trials: **37 of 2,021 for T11 (1.83%)**,
**0 of 1,200 for T5**.

> ### ⚠️ A defect in the published dataset
>
> In `T11/day_689/Block_14`, `trialSuccess`, `pathEfficiency` and `orthChanges`
> each contain **76 values, but `startStops` defines only 75 trials**.
> `angleErrorPerTrial` has the correct 75. The loader flags this and leaves
> those three columns empty for that block rather than guessing an alignment.
> This is an inconsistency in the deposit itself, not in our code, and it should
> be mentioned in any write-up. Consider contacting the authors.

## 7. Getting the data: network access and Dryad's anti-bot challenge

### 7.1 Network access — RESOLVED

The environment originally used the **Trusted** network access level, whose
allowlist covers package registries, GitHub and cloud SDKs but not Dryad. It was
changed to **Custom** with these domains allowed:

```text
datadryad.org
*.datadryad.org
doi.org
*.amazonaws.com
```

with *"Also include default list of common package managers"* enabled (without it
PyPI is lost and nothing installs). Set this at [claude.ai/code](https://claude.ai/code)
via the **cloud icon above the message box** → **Add cloud environment** / gear icon
→ **Network access: Custom**. The four levels are None / Trusted / Full / Custom.

Dryad's **metadata** API is now reachable, which confirmed the deposit:

| Field | Value |
|---|---|
| Title | *Data from: Measuring instability in chronic human intracortical neural recordings towards stable, long-term brain-computer interfaces* |
| Authors | Tsam Kiu Pun, Mona Khoshnevis, Thomas Hosman, Guy Wilson, Anastasia Kapitonava, Foram Kamdar, Jaimie Henderson, John Simeral, Carlos Vargas-Irwin, Matthew Harrison, Leigh Hochberg |
| **Dryad version** | **6** (API version record `324345`) |
| Files | `MINDFUL_Data.zip` (411,951,588 bytes ≈ 392.9 MB) and `README.md` (3.3 KB) |
| Checksum type | **SHA-256** (`6d12b5db…` for the zip) |

### 7.2 Anti-bot challenge — OPEN

Dryad protects its **file-download** route with an anti-bot challenge (Anubis).
Any script requesting the file receives a 4.3 KB HTML page titled "Validating…"
instead of the data. This was verified thoroughly:

| Route | Result |
|---|---|
| `/api/v2/files/<id>/download` | `401 {"error":"Unauthorized, must have current bearer token"}` |
| `/downloads/file_stream/<id>` with `curl`/`python-requests` User-Agent | `403 Forbidden` |
| `/downloads/file_stream/<id>` with a `Mozilla/5.0 (compatible; …)` User-Agent | `200` — but the body is the challenge page, for every `Accept` header, and repeat requests with cookies do not pass |

The challenge requires executing JavaScript proof-of-work, so a plain HTTP client
cannot pass it. **We do not attempt to defeat it** — Dryad provides a supported
route for programs, so there is no legitimate reason to circumvent one.

### 7.3 The supported programmatic route: a Dryad API account

Dryad's own error message names the answer: *"must have current bearer token."*

1. Sign in at <https://datadryad.org> with an **ORCID iD**
   (free at <https://orcid.org> — and a researcher identifier worth having).
2. Open **My account** → create an **API account**. Dryad issues a
   `client_id` and a `client_secret`.
3. Provide them as environment variables — **never commit them**:

   ```bash
   export DRYAD_CLIENT_ID='...'
   export DRYAD_CLIENT_SECRET='...'
   python3 scripts/01_download_dataset.py
   ```

The script exchanges them for a short-lived access token via OAuth
(`POST https://datadryad.org/oauth/token`, `grant_type=client_credentials`),
then downloads through the authenticated API route, which is not behind the
challenge. Tokens last about 10 hours. The script reads the credentials **only**
from the environment and never writes them to any file, including the manifest.

> **What "OAuth client credentials" means:** it is how a *program* authenticates,
> as opposed to a person typing a password. You trade a long-lived id+secret for
> a short-lived token, so if the token leaks it expires quickly. It is the
> standard pattern for machine-to-machine API access.

### 7.4 Alternative: download manually

Open <https://datadryad.org/dataset/doi:10.5061/dryad.n2z34tn5s> in a browser
(which passes the challenge normally), download `MINDFUL_Data.zip`, and place it
in `data/raw/`. Everything downstream works unchanged. Provenance is weaker —
no automatic manifest — so record the version number (**6**) and the download
date by hand. The SHA-256 above can still be checked with `sha256sum`.

### 7.5 Two safeguards added after real failures

Both of these were written in response to problems that actually occurred:

- **The script refuses to accept an HTML page as data.** It inspects the first
  bytes of every download; if they begin `<!doctype html`, it deletes the file
  and explains that the challenge was hit. Without this, a 4.3 KB web page would
  have been sitting in `data/raw/` named `MINDFUL_Data.zip`.
- **The script refuses to overwrite files it did not download.** The Dryad
  deposit contains a file named `README.md`, and this folder originally had its
  own `README.md` — downloading would have silently destroyed it. The folder's
  notes were renamed to `_FOLDER_NOTES.md`, and the script now checks each
  destination against the previous manifest and aborts rather than clobbering
  anything unrecognised.

## 8. Open questions — status after opening the data

### ✅ Answered

| Question | Answer |
|---|---|
| Layout: loose folders or archives? | One `.zip`, unpacking to a doubly-nested `MINDFUL_Data/MINDFUL_Data/` |
| How many sessions, blocks, trials? | 21 sessions, 54 blocks, 3,301 trials, 782,708 bins, 4.35 hours |
| Bin width 20 ms? | **Yes** — authors' README: "nStep: number of 20 ms steps (bins)" |
| What are the neural features? | `nctx` = threshold crossings (RMS < −3.5); `spikePower` = spike band power 250–5000 Hz. The earlier guess was right. |
| How many channels? | 192 per feature type. T5 has `nctx` only (192); T11 has both (384) |
| Are `day_<N>` days since implant? | Consistent with it — T5 ≈ day 2121–2149, T11 ≈ 658–800, i.e. years and months post-implant |
| Gaps between sessions? | **Uneven.** T11: 3–24 days (median 8.5). T5: 2–14 days (median 5) |
| What criterion produced `excludeTrials`? | **Mean noise exceeding 5% during the trial** |
| `angleError` units and convention? | Degrees, 0–180, lower is better. `angleErrorPerTrial` is the **median** over the trial |
| What is `labels`? | The *inferred* cursor-to-target vector — intent, not decoder output |
| Is `cursorVel` raw decoder output? | Yes — "Decoded 2-D velocity vector output from the decoder" |
| Is the index base 1 or 0? | **1-based**, confirmed empirically across all 54 blocks |
| Does performance actually decline? | **Yes, substantially** — see §8.1 |
| Is task type a confound? | **No.** Each participant used one task throughout (T11 `circleOfCircles`, T5 `Fitts`) |

### 8.1 Performance does decline — and the two participants differ in kind

Two independent measures agree, which is a useful cross-check:

**T11** (median angle error per session, and block `percentCorrect`):
roughly flat at 20–30° and 90–100% correct through day 715; a spike at day 727;
back to baseline at day 751; then a **step change** at day 758 to ~120° and
~25% correct, staying degraded through day 800.

**T5**: a smoother rise from ~30° to ~76° peaking at day 2135 (percentCorrect
falling 98% → 37%), then **recovery** to ~39° and 93% by day 2149.

> **These are different phenomena.** T11 looks like a sustained transition to a
> degraded state; T5 looks like a transient excursion that recovered. Whether
> either qualifies as a "critical transition" is a scientific question, not
> something the data answer on their own — but the *shapes* differ, and any
> hypothesis should account for both rather than only the convenient one.

### ⚠️ Still open — and these constrain the project

1. **Is the decoder genuinely fixed across all sessions?** Still the single most
   important unverified claim. Nothing in the deposit's files states it; it must
   come from the paper's Methods. If any session was recalibrated, the drift
   structure changes meaning.
2. **Is 15 sessions enough?** This is the hard one. T11 has **15 session-level
   observations**, T5 has **6**. Any session-level rolling-window statistic
   (variance, lag-1 autocorrelation, Kendall's τ) computed on 15 points is
   fragile, and van der Bolt et al. (2021) is directly about this. Bin-level
   data is plentiful (440,045 bins for T11) — so **the choice of analysis level
   is now the central design decision**, not a detail.
3. **What is the pre-transition window?** For T11 the change is between day 751
   and 758 — one 7-day gap, with 11 sessions before it. Whether 11 points can
   support an early-warning claim is exactly the question to answer honestly.
4. What are the units/scaling of `cursorVel` (range ≈ ±0.03 for T5, ±0.006 for
   T11 — very different, suggesting per-participant scaling)?
5. Should `personal_use` and `random_targets` blocks be used as the
   out-of-distribution robustness check the literature review mentions?
6. Licence terms of the deposit — check before publishing.

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
| Dataset downloaded? | **Yes** — 2026-08-25, Dryad version 6 |
| Zip SHA-256 | `6d12b5dbcf9cac654ff1d0679e9753bf042b56cd5b8852eb31236b3cdecf7332` (verified) |
| README SHA-256 | `00fc1f8d6852058f…` (verified) |
| Download route | Dryad API account, OAuth client-credentials bearer token |

---

## 11. Attribution

The dataset is the work of Pun, Khoshnevis, Hosman and colleagues, and the BrainGate2
consortium. If any of it is used in a project write-up, cite both the paper and the
Dryad DOI, and check the deposit's licence terms (§1). Nothing in this repository
redistributes their data.
