# What each document in this folder is

Several documents in here describe the plan, because the plan was written more
than once as the project changed. That is normal, and keeping the older versions
is deliberate — the difference between them is part of the research record. But
it makes it easy to open the wrong one, so this is the map.

## Before anything else: where the physical phase lives

**The physical experiment was redesigned on 20 September 2026 and now lives in
[`physical/`](../physical/README.md), not in this folder.** Start at
`physical/README.md`.

Four documents in here describe the *earlier* physical design. They each carry a
banner saying so and pointing at their replacement, and they are kept because
the route a design took is part of the research record:

| Old (here) | Current (in `physical/`) |
|---|---|
| `BUILD_MANUAL.md` | `physical/docs/04_BUILD.md` |
| `RIG_CODE.md` | `physical/docs/05_SOFTWARE.md` |
| `RIG_PROCEDURE.md` | `physical/docs/06_DATA_COLLECTION.md` |
| `RIG_PREREGISTRATION.md` | `physical/docs/01_RESEARCH_DESIGN.md` and `02_EXPERIMENTS.md` |

`EXPERIMENTAL_PROCEDURES.md` phases 7–10 are superseded the same way; phases 1–6
are not.

**Do not mix `rig/` and `physical/code/`.** They keep separate
`preferred_directions.npy` files — the file that decides which patch on the
screen is which channel — so recordings from one cannot be compared with
recordings from the other, and nothing in the data would show that they had been
mixed.

---

## The submission documents

| File | What it is |
|---|---|
| **`RESEARCH_PLAN_2026-09-15.md`** | **The September 2026 ISEF submission.** Third person, aligned to page 2 of ISEF Form 1A. This is the one that went to the SRC, and it is kept exactly as submitted. |
| **`RESEARCH_PLAN_DECEMBER_DRAFT.md`** | **Draft of the December final plan — Sections B and C only**, rebuilt for the physical design from `physical/docs/`. Not submitted. Lists the six items still open, of which only the campaign length changes what gets recorded. |
| `EXPERIMENTAL_PROCEDURES.md` | The procedures, by phase, in the researcher's own voice. Phases 1–6 are the computational work at plan level. **Phases 7–10 are superseded** by `physical/docs/`. |
| `BUILD_MANUAL.md` | **Superseded** by `physical/docs/04_BUILD.md`. Kept for its extra depth on the Raspberry Pi setup and the enclosure, which build the same apparatus. |
| `RIG_CODE.md` | **Superseded** by `physical/docs/05_SOFTWARE.md`. Kept because it holds the full source of the `rig/` programs inline as a fallback. |
| `REPLICATION_GUIDE.md` | Command-by-command instructions for every computational stage. Was Section C of the research plan until 17 September 2026, when it was moved out so the plan could be read at the level a reviewer reads. |

## The preregistrations

These are the documents whose value comes from their timestamps. Each was
committed before the data it governs existed. They are amended in public, never
edited silently.

| File | Governs |
|---|---|
| `RIG_PREREGISTRATION.md` | The physical rig study. **SUPERSEDED 20 September 2026** (Amendment 3, §14) — the hypothesis was replaced and the live design moved to `physical/`. P-R1 through P-R10 are not carried forward. Kept as the record of how the design got where it did. |
| `FEATURE_STUDY_PREREGISTRATION.md` | The feature-family study. |
| `COMBINATION_STUDY_PREREGISTRATION.md` | The detector-combination study. |
| `DAY_PREDICTOR_PREREGISTRATION.md` | The day-effect predictor study. |

## Earlier plan documents, kept for the record

| File | Status |
|---|---|
| `PROJECT_DEFINITION.md` | Written 26 August 2026, working backward from the final product. The upstream source of the plan's scientific content, and the place to change it. Still current as a statement of what the project is. |
| `ISEF_RESEARCH_PLAN.md` | The earlier full-length draft mapped onto the form. Superseded as the submission document by `RESEARCH_PLAN_2026-09-15.md`, but it carries longer treatments of several sections that the December plan will need. **`[[RESEARCHER — decide whether this is retired or becomes the December draft.]]`** |
| `research_plan.md` | Superseded 26 August 2026. The plan as it stood before any data existed. |
| `procedures.md` | The Phase 1 source record: what was actually done, in order, during dataset acquisition. |
| `ORIGINAL_DATA_COLLECTION_DESIGN.md` | The original design for collecting new data, including the options that were rejected. |

## Working notes

`research_log.md` is the running log, including mistakes. Everything else ending
in `_NOTE.md` is a short record attached to one study, written when that study
ran. `design_decisions.md`, `deterioration_definition.md`,
`observable_selection.md` and `phase3_design_implications.md` record specific
choices and why they were made.
