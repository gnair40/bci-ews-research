# What the AI assistant did, and what it did not — the factual record

**This document is not the AI disclosure.** It is the evidence the disclosure
is written from.

That distinction is a standing decision in this project, made on 8 September
2026 and restated on 16 September: *"A disclosure that an AI wrote about
itself is not a disclosure."* Section G of the September plan was left blank at
the researcher's request for the same reason. So this file contains **facts
with dates and commits, and no disclosure prose.** The statement that goes on
the ISEF form is Gayathri Nair's to write, in her own words, checked against
the 2026–27 form and with the SRC — the wording of that form changes year to
year and nothing here should be copied into it.

**Compiled 24 September 2026.** Everything below is checkable from this
repository with the commands given.

---

## 1. The shape of it, in numbers

```bash
git log --format='%an' | sort | uniq -c | sort -rn
```

| | |
|---|---|
| Commits in the repository | **187** |
| Authored by the AI assistant (`Claude <noreply@anthropic.com>`) | **181** |
| Authored by the researcher | **6** |
| First commit | 16 August 2026 |
| Lines of Python | ~29,800 across 97 files |
| Lines in the research log | 6,849 |

**The AI wrote essentially all of the code and essentially all of the prose in
this repository.** That is the single most important fact in this file and it
should not be softened. Commit authorship records whose keyboard produced the
text, and it was the assistant's in 181 cases out of 187.

What commit authorship does **not** record is who decided what the work should
be, and that is section 2.

---

## 2. What the researcher decided

These are decisions, not edits. None of them was made by the assistant, and
several were made *against* what the assistant had drafted or suggested.

| Date | Decision | Where it is recorded |
|---|---|---|
| Throughout | **No human participants, at all.** Including the researcher's own data, which the researcher ruled out as human-participant research | standing constraint; `README.md`, `physical/docs/03_MATERIALS_AND_SAFETY.md` |
| Throughout | **No optimising for significance.** No trying several deterioration definitions and keeping the best | standing constraint; enforced by `scripts/61_statistical_hygiene.py` |
| Throughout | Raw data is never modified, and stays separate from processed data | `DATASET_README.md`, `data/` layout |
| Throughout | Everything goes in the log, **including mistakes**, and no entry is ever deleted | `research/research_log.md` — the deletions would be visible in git if they had happened |
| 8 Sep 2026 | The AI disclosure would be written by the researcher, not drafted by the assistant | log, 8 September |
| 21 Sep 2026 | Commissioned a ground-up reassessment with explicit instructions not to assume the existing question, method or novelty was correct | `research/REASSESSMENT_2026-09-21.md` |
| **24 Sep 2026** | **The fault-free campaign is 101 sessions**, accepting in advance that a quiet result is reported as *untested* rather than as passing | `physical/docs/09_PREREGISTRATION.md` §10.1, §11 call 1, frozen at `f4dda04` |
| 24 Sep 2026 | Froze the preregistration, closing all ten judgement calls | same |

---

## 3. What the assistant did

- Wrote the analysis code, the test suite, the gates, the figures, and the
  physical-phase software.
- Wrote the documentation, including the research design, the experiments, the
  build manual, the runbook and the troubleshooting guide.
- **Drafted** the preregistration's predictions and thresholds, each derived
  from a measured number already in the repository, with the derivation cited
  on every line. `09_PREREGISTRATION.md` §0.2 and §11 record which values were
  mechanical derivations and which were judgement calls awaiting the
  researcher.
- Ran the analyses and reported their results, including the ones that went
  against the project's hypothesis.
- Found and reported its own errors. Section 4.

## 4. What the assistant got wrong

This section exists because a record of AI involvement that lists only
successful contributions misrepresents what using an AI assistant is actually
like. Each of these is written up in full in the research log on the date
given, and each was found by running something rather than by reading it.

| Date | The error | How it was caught |
|---|---|---|
| ~1–20 Sep | A session-level AUC target of 0.933 was quoted for two weeks while another report in the same repository gave 0.990. The 0.933 was never derived from the false-alarm budget at all; it has been **corrected** to 0.990 and is now a superseded value the gates refuse to let anyone quote as current | a cross-reference check written *after* the fact, `scripts/77` |
| 13 Sep | `DATASET_README` said the data had never been downloaded. It had been, the same day that sentence was last edited. Wrong for four weeks | the same check |
| 20 Sep | P-5 had no code, and the assistant's own written instruction would have put ten faulty sessions into the fault-free arm | reading the instruction while implementing it |
| 21 Sep | A self-test printed PASS on a `NaN`, because `nan <= x` is False | a deliberately short fake session |
| 21 Sep | `make_session_table` held every session in memory: 22 GB at full campaign size | rehearsing at real scale |
| 21 Sep | The stimulus loop took 6.9 ms against a 20 ms budget and would have silently failed 50 fps on a Pi | benchmarking before building |
| 21 Sep | `analyze_apparatus.py` reported unanimous agreement from **one** observation, and separately dropped a false-alarm rate of 0.0 as falsy — hiding the largest difference it had found and reporting the opposite of the truth | running it on synthetic data |
| 24 Sep | The recording-cost table's total omitted the row directly above it (120 sessions, ~10 h) | changing an unrelated number and re-reading every document that quoted it |
| 24 Sep | The new freeze gate's ledger was keyed on commit hashes, which cannot work — a hash row can never name the commit that adds it | running the gate |

**Both of the 21 September `analyze_apparatus` bugs failed in the reassuring
direction.** A check that wrongly says "fine" is worse than no check, because
it is trusted.

---

## 5. What is verifiable, and how

Anyone — a judge, a reviewer, the SRC — can check every claim above:

```bash
git log --format='%an' | sort | uniq -c        # who authored what
git log --follow physical/docs/09_PREREGISTRATION.md   # when the prereg was written and frozen
git show --stat f4dda04                        # the freeze itself
python3 tools/check_all.py                     # every gate this project runs on itself
```

The research log is append-only by policy and the git history would show any
deletion. That is the mechanism by which "we recorded our mistakes" is a
checkable claim rather than an assertion.

---

## 6. For whoever writes the disclosure

Not wording — just the questions the facts above are an answer to, so that
none is missed:

1. Which parts of the work were produced by an AI system?
2. Which decisions were the researcher's, and can that be shown rather than
   asserted?
3. Was the AI's output checked, and by what?
4. Did the AI make errors, and what happened to them?
5. Does the disclosure match what the 2026–27 form actually asks? **Check the
   current form; do not rely on this file's framing of the question.**
