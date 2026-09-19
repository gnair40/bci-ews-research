# What each document in this folder is

Several documents in here describe the plan, because the plan was written more
than once as the project changed. That is normal, and keeping the older versions
is deliberate — the difference between them is part of the research record. But
it makes it easy to open the wrong one, so this is the map.

## The submission documents

| File | What it is |
|---|---|
| **`RESEARCH_PLAN_2026-09-15.md`** | **The September 2026 ISEF submission.** Third person, aligned to page 2 of ISEF Form 1A. This is the one that goes to the SRC. |
| `EXPERIMENTAL_PROCEDURES.md` | The procedures, by phase, in the researcher's own voice. Phases 1–6 are the computational work at plan level; phases 7–10 are the physical build in full detail, because that part still has to be done. |
| **`BUILD_MANUAL.md`** | **The complete build-and-test manual for the physical rig**, from unboxing a Raspberry Pi to the finished instrument. Written to be followed with no prior hardware experience and no further help. Start at Part 0. |
| **`RIG_CODE.md`** | **Every program the physical experiment needs**: what each is for, the commands for a typical session, a fallback table, and the full source inline. Read this to answer "do I have to write any code?" — no. |
| `REPLICATION_GUIDE.md` | Command-by-command instructions for every computational stage. Was Section C of the research plan until 17 September 2026, when it was moved out so the plan could be read at the level a reviewer reads. |

## The preregistrations

These are the documents whose value comes from their timestamps. Each was
committed before the data it governs existed. They are amended in public, never
edited silently.

| File | Governs |
|---|---|
| `RIG_PREREGISTRATION.md` | The physical rig study. **DRAFT, not frozen** — and currently BLOCKED on an open decision recorded in its §11. |
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
