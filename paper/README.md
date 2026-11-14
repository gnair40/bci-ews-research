# The working research paper and its completion manual

Two Word documents, built together by one program on 14 November 2026.

| File | What it is |
|---|---|
| `Working_Research_Paper.docx` | **Document 1.** The research paper in 13 sections. Everything the finished computational work establishes is written out in black. Everything that waits for the physical test bench, and the final title, is one of 59 numbered placeholders in bold red capitals inside square brackets, a pink table cell, or a dashed box reserved for a photograph or graph. |
| `Completion_Manual.docx` | **Document 2.** How to finish: the roadmap, every photograph to take, the record sheets to keep, every calculation with its formula, every graph, how to write each remaining section, and the final checks. Its last section lists every red placeholder of the paper with the file it comes from. |
| `logbook/` | Five empty CSV files, one per sheet of the bench logbook described in Part III of the manual. They open in Excel or Google Sheets. |
| `placeholders.json` | The same list of red placeholders, as data. |

## What is established and what is not

- **Computational validation: complete.** Every number in the black text is
  read by the builder from `poster/poster_data.json` or
  `data/processed/harness_summary*_local.json`. None is typed into the
  documents. Those files are recomputed by the repository's own checks.
- **Physical validation: preregistered, not built.** No part has been ordered
  and nothing has been measured. The paper describes it in the future tense.
  It contains no bench number, no bench photograph and no bench graph. The
  graph layouts in the manual are stamped as templates and carry no values.
  Nothing from `physical/data/dryrun/` is used anywhere.

## How the two documents are kept consistent

`build.js` writes both in one run and stops with an error if

1. a red placeholder names a section of the manual that does not exist,
2. the paper uses its figures or tables in a different order from
   `registry.json`,
3. a table number written inside a red instruction no longer matches,
4. a placeholder code that the manual mentions by name (for example R5.2) no
   longer belongs to the item the manual says it does.

## Rebuilding

```bash
python3 paper/make_figures.py     # draws the charts and diagrams as SVG
node paper/render_svgs.js         # renders them to PNG
node paper/build.js               # writes both .docx files and the logbook sheets
```

| Source file | What it holds |
|---|---|
| `doc1.js` | The text of the paper |
| `doc2.js`, `doc2a.js`, `doc2b.js` | The text of the manual |
| `lib.js` | Layout only: headings, tables, figures, red placeholders, reserved spaces |
| `make_figures.py` | Real charts (drawn by `poster/charts.py` from checked numbers), workflow diagrams, and graph templates without numbers |
| `registry.json` | The order, and so the number, of every figure and table of the paper |

## Once the paper is being edited by hand

The Word file is a living document. After red items start being replaced in
Word, **do not run `build.js` again without saving a copy first**: it writes a
fresh file and would overwrite the edits. From that point the Word file is the
paper and the builder is only the record of how the first draft was made.

## Known limits

- The files were checked with a format validator and by rendering every page
  in LibreOffice. **They were not opened in Microsoft Word**, which this
  environment does not have.
- Nine of the ten references carry first authors only, as in the submitted
  research plan. They are marked with a dagger and have a red instruction.
- The statement on the use of AI is a reserved space. By the decision of
  8 September 2026 it is written by the researcher, so neither document
  suggests its wording.
- The paper's tables ask for a 95% interval on each detection rate by fault
  type and severity. The analysis program reports the count and the
  proportion; the interval is computed with the Wilson formula given in the
  manual. Whether to keep that column is the researcher's decision.
