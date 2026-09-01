# Decoder-Guard — monitoring brain-computer interface reliability

A high-school research project (ISEF) on whether the failure of an intracortical
brain-computer interface can be **detected before it costs the user
performance**, and on building an honest test for any system that claims to do
so.

> **No human participants.** Every number here comes from **public,
> de-identified datasets** collected years ago by other researchers under their
> own ethics approval. Nobody is recruited, nobody wears a device, no consent
> forms are collected. Where the documents say "participant" they mean *whose
> published recording a data file contains* — the source researchers' convention,
> labelling their subjects T5, T11, T15.

---

## The problem

People with paralysis can control a computer cursor through an implanted
electrode array and software called a **decoder**. Over months the recording
degrades — electrodes drift, neurons drop out — and the decoder keeps confidently
producing output from a signal that no longer matches what it was trained on.
Eventually it must be retrained, which is slow and disruptive.

The field has spent a decade learning to *correct* that drift and almost no
effort on *noticing it early enough to act*. There is not even a standard way to
test whether such a warning system works.

## The result, in one line

**On this data, at the operating point the design specified, no configuration
works — and the reason is now measured rather than guessed.**

| Finding | |
|---|---|
| The monitor detects faults **counting spikes cannot see** | AUC 0.71–0.79 where the trivial baseline sits at 0.40–0.52. Replicated on two participants. |
| It does **not** mistake a task change for a fault | 15× and 70× separation |
| It **cannot** be deployed at the specified false-alarm rate | 0 of 48 configurations pass the gates |
| Why: **one measurement per session** | Lag-1 autocorrelation 0.995. Effective independent samples per session: 0.1 |
| The target a future attempt must beat | Session-level AUC ≈ **0.99**; achieved **0.67–0.74** |

## Start here

| Read | For |
|---|---|
| [`reports/PHASE3_REPORT.md`](reports/PHASE3_REPORT.md) | **The whole project**, from the ground-truth problem to the bound |
| [`reports/monitor_demo.html`](reports/monitor_demo.html) | The monitor **running** — one fault caught, one missed, one false alarm |
| [`reports/project_guide.html`](reports/project_guide.html) | Plain-language explanation, no background assumed |
| [`research/research_log.md`](research/research_log.md) | Dated record of every step, every mistake, every correction |
| [`reports/PHASE1_2_REPORT.md`](reports/PHASE1_2_REPORT.md) | The earlier phase and its negative result |

## How the argument runs

1. **The original idea was tested and failed.** Early-warning-signal theory,
   under a design frozen in advance. The indicator rose *faster* during healthy
   performance than overall. Reported as negative.
2. **Observational data cannot answer the question.** Nobody recorded when
   deterioration began, so lead time is an artefact of the analyst's own
   definition and the false-alarm rate is not estimable at all.
3. **So the ground truth was built.** 1,850 fault episodes with onsets drawn and
   locked to disk under a checksum *before* any detector existed.
4. **A grading system was built before the monitor**, so the metric could not be
   chosen to flatter it.
5. **The monitor works in the ways that were measurable and fails in the ways
   that were measured**, with the cause identified to three decimal places.

## Reproducing it

```bash
pip install -r requirements.txt
python3 scripts/01_download_dataset.py      # needs DRYAD_CLIENT_ID / _SECRET
python3 scripts/17_fault_injector.py verify
python3 scripts/18_reference_decoder.py fit
python3 scripts/20_evaluation_harness.py run --local
python3 scripts/21_score_report.py --local
python3 scripts/24_benchmark_matrix.py
```

Raw data (~9 GB) is not committed; the download script verifies SHA-256
checksums against a manifest. Scripts are numbered in dependency order.

## Layout

```
scripts/     01-30, numbered in the order they must run
research/    design decisions, preregistrations, the dated log
reports/     results, figures, the demo
data/        raw (gitignored) and processed outputs
```

## Honest limitations

- **Two participants, and they disagree.** They disagreed in Phase 1–2 and again
  on a later prediction. With n = 2 an improvement cannot be told from noise.
  **This is the binding limitation.**
- **Open-loop evaluation.** Injected faults are replayed, so no live person
  adapts. Performance is decoder output error, not task success.
- One fault type stops being a clean test at high severity; attribution names
  only three of its four possible causes. Both are documented where they matter.

## Attribution

Primary dataset: Pun, Khoshnevis, Hosman et al. (2024), *Communications Biology*,
[doi:10.5061/dryad.n2z34tn5s](https://doi.org/10.5061/dryad.n2z34tn5s). Their
published instability result is reproduced exactly (r = 0.985) in
`scripts/09_reproduce_mindful.py` as a check that this pipeline reads their data
correctly.
