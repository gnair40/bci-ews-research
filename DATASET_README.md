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
The archive also carries **17 stray `.DS_Store` files** (macOS folder metadata,
harmless clutter). Any code walking this tree must filter for real block folders
rather than assuming every directory entry is one.
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

### 8.2 Is the decoder fixed? Evidence from the data

The paper's abstract states the participants "used **fixed decoders** to control
a computer cursor". That is an assertion in an abstract. `scripts/05_check_decoder_stability.py`
tests it against the data.

**The logic.** `cursorVel` is the decoder's own output; `nctx` (+ `spikePower`)
are its inputs. If the decoder is a fixed function, the input→output mapping is
the same function in every session. Fitting a linear map per block and comparing
across time distinguishes two cases:

- **Recalibration** replaces the decoder's weights → the estimated map changes
  **discontinuously**, jumping back toward similarity 1.0 with a fresh mapping,
  and performance recovers.
- **A fixed decoder with drifting neural signal** → similarity declines
  **smoothly**, because channels fall silent and contribute less while the
  underlying function is unchanged.

**Result: a smooth decline, no jumps.**

| | Largest single-session *increase* in similarity |
|---|---|
| T11 | **+0.089** (day 692) |
| T5 | **+0.023** (day 2135) |

Cosine similarity to the first session falls monotonically-ish from 1.00 to 0.44
(T11, over 142 days) and 1.00 to 0.62 (T5, over 28 days). Nothing resembling a
recalibration event appears in either participant.

**The most telling detail.** T5's performance *recovers* at day 2149 — from 37%
to 93% correct. If that recovery had come from recalibrating the decoder, the
estimated map would have changed. It did not: cosine similarity is **0.621 at
day 2149 versus 0.620 at day 2135** — unchanged to three decimal places. So
**T5's recovery happened without any change to the decoder.** Whatever restored
performance was in the neural signal or the user, not in the algorithm.

> **How much weight this evidence carries.** It is a diagnostic, not a proof.
> T11's decoder is an LSTM (per the companion paper, Hosman & Pun, *"Months-long
> High-performance Fixed LSTM Decoder for Cursor Control"*), so it has internal
> memory and a memoryless linear fit only approximates it — which is why R² is
> modest (0.29 T11, 0.41 T5) **by construction**. A low R² here is expected and
> means nothing on its own. A recalibration that happened to produce a very
> similar mapping would also be hard to detect this way. **Absence of a
> discontinuity is consistent with a fixed decoder; it is not the authors saying
> so in their Methods.** Read the Methods when you can reach the paper.

**Why this matters to the project.** If it holds, the literature review's central
premise survives: the recalibration that would erase the statistical residue an
early-warning detector needs did not happen here. And T5's decoder-independent
recovery means the coupled human–decoder system can return from a degraded
state — which is directly relevant to framing (C) in the review.

### 8.3 Is the decoder fixed? — ANSWERED from the paper's Methods

Source: Pun et al. 2024, *Communications Biology*, Methods
([PMC11494208](https://pmc.ncbi.nlm.nih.gov/articles/PMC11494208/)). Quotations verbatim.

**Decoder weights: fixed. Confirmed.**

- **T11** — *"The LSTM decoder was trained and validated on closed-loop
  point-and-click cursor tasks from the 18 most recent sessions of T11, spanning
  70 days from trial day 576 to 646."* The deposit begins at trial day 658, i.e.
  **after** training ended. *"Neural features were decoded into cursor velocities
  by a real-time LSTM decoder."*
- **T5** — *"An initial decoder was trained based on T5's neural activity while he
  engaged in an open-loop block on day 0 (trial day 2121). This decoder was then
  used to drive closed-loop control in a subsequent block. The final decoder
  parameters were then updated based on the first closed-loop block, **and they
  were fixed for later closed-loop blocks and future sessions**."* Also
  *"Smoothing and gain were manually adjusted during the first session and fixed
  on subsequent days"*, and *"Training blocks for calibrating the decoder on trial
  day 2121 were not included in this study"* — so the calibration blocks are
  **absent from the deposit**, which is why T5's day 2121 has only 2 blocks.

The Results section is headed *"Fixed decoders result in initially stable and
then unstable performance across months."*

### ⚠️ 8.4 But the loop is NOT fully frozen — and this changes the project

The abstract says "fixed decoders". The Methods say something more precise:

> *"To accommodate for session-to-session variability in recordings, we applied
> **per-channel z-scoring at every time bin for T11** and a **bias correction for
> T5**. For T11, mean and variance were initialized from the previous block and
> **adaptively updated using a 3-min rolling window**. … For T5, a bias correction
> was applied to mitigate mean shifts in the decoded output by subtracting a
> running estimate of the decoder bias from the velocity outputs (**with an
> adaptation rate of 0.3**). … **The intercept term in the decoder is then updated**
> to the negative resulting bias vector."*

So there are **three** adaptive elements in this loop, not one:

| Element | Fixed or adaptive? |
|---|---|
| Decoder weights | **Fixed** |
| Feature normalisation (T11: rolling z-score; T5: bias correction) | **Adaptive, continuously** |
| The human user | **Adaptive** (motor learning) |

**For T5 the decoder's intercept term is literally updated online.** The weights
are frozen; the offset is not.

And the authors state the consequence outright:

> *"It should be noted that our method did not track mean firing rate shifts which
> are known to correlate with declines in decoder performance. In our datasets,
> adaptive mean corrections such as z-scoring or bias correction were applied to
> the neural features during online cursor control to combat this type of model
> drift. **Therefore, performance drops observed in this dataset were largely due
> to other types of model drift.**"*

**Two consequences for this project, and they cut in opposite directions:**

1. **A risk.** "Fixed decoder" is not "frozen system". A rolling 3-minute z-score
   actively removes slow mean drift from the neural features — which is
   *precisely* the kind of slow change an early-warning indicator might look for.
   Any claim about detecting drift must account for the fact that one class of
   drift has already been subtracted out before the data were recorded. This
   should be stated explicitly in the write-up rather than discovered by a judge.
2. **An opportunity, and arguably the more interesting one.** The literature
   review's framing (C) — *"a monotonically degrading plant plus a saturating
   compensator"* — was labelled **[Speculation]**, with no paper stating it. The
   Methods describe **exactly that architecture**: an adaptive normalisation layer
   whose job is to absorb drift, running continuously, on top of a fixed decoder.
   Performance holds flat while the compensator absorbs drift; when the drift
   exceeds what a mean correction can absorb, performance falls. **The compensator
   in framing (C) is not hypothetical — it is a documented, parameterised
   component of this system** (T11: 3-minute rolling window; T5: adaptation rate
   0.3).

### 8.5 The paper's own numbers match our independent exploration

Reassuring cross-check — we computed these before reading the paper:

| Quantity | Paper | Our exploration |
|---|---|---|
| T11 sessions / span | 15 sessions, 142 days | 15 sessions, days 658–800 = 142 days ✓ |
| T11 early vs late AE | days 658–751: 26.8° ± 22.6°; days 758–800: 88.4° ± 46.1° | step change located between day 751 and 758 ✓ |
| T5 early vs late AE | days 2121–2128: 39.6° ± 23.9°; days 2133–2149: 58.8° ± 31.7° | rise across the same boundary ✓ |
| Recovery events | *"Brief recovery … 93 days after the initial session for T11 and 28 days after … for T5"* → **day 751** and **day 2149** | both identified independently ✓ |
| Features | T11 threshold-crossing rate **and** spike power; T5 spike rate only; 20 ms non-overlapping bins | 384 vs 192 features, 20 ms ✓ |
| T11 task | "center-out-and-back" | `circleOfCircles` in `task.mat` — same task, different name |

The authors also note *"fixed decoders may not necessarily result in a steady
decline in cursor control over time"* — consistent with our finding (§8.2) that
T5's day-2149 recovery involved no change in the decoder map.

**Additional context from the paper:** 154 of 384 features (T11) and 85 of 192
(T5) had significant directional tuning in at least half of sessions. Variance
accounted for by the top two direction-dependent components: T11 50.0% on day 0;
T5 42.2% on day 0, dropping to 2.9% and recovering to 11.3% on the last session.

### Status of the remaining questions — CLOSED by Phases 1–2

| Question | Answer |
|---|---|
| Is the decoder genuinely fixed? | **Yes.** Confirmed from the Methods and independently from the data (§8.2–8.3). Weights fixed; an adaptive normalisation layer remains (§8.4). |
| Is 15 sessions enough? | **At session level, marginal.** Detects only \|τ\| ≥ 0.455. **Block level gives 21 pre-transition observations and \|τ\| ≥ 0.305**, which is usable. See `research/design_decisions.md`. |
| What is the pre-transition window? | **21 blocks over 11 sessions, trial days 658–751.** Frozen in `research/FROZEN_DESIGN.json`. Note it is *not* a flat healthy baseline — it contains the day-727 excursion and day-751 recovery. |
| Units/scaling of `cursorVel`? | Normalised workspace units per bin. The T5/T11 difference is participant-specific **gain**: the Methods state "smoothing and gain were manually adjusted during the first session and fixed on subsequent days." Not a data problem. |
| Use `personal_use` / `random_targets`? | **Yes, and done** (`scripts/16`). They gave the decisive out-of-distribution result: the indicator differs by only 5.9–8.4% between completely different tasks on the same day, against a 3× range across the record — so it tracks the recording, not the task. |
| Licence terms? | **CC0-1.0** (public domain dedication), confirmed from the Dryad API. No restriction on publishing; cite the DOI and paper as a matter of good practice. |

### New questions raised by Phases 1–2

1. **What drives the within-baseline rise in the indicator?** Firing rate does not
   explain it (τ = −0.286, n.s. across baseline, while the indicator runs
   τ = +0.857). `avgOutliers`, silent channels and low-variance channels were
   tested and rejected. **Unidentified.**
2. Does anything survive after regressing out firing rate *and* de-trending?
   That is the Phase 3 question.
3. Is the day-689→751 flickering (degrade, recover, collapse) a real
   early-warning phenomenon here, or noise? It would need preregistering.


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
