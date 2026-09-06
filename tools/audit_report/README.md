# The audit report generator

Rebuilds `reports/PROJECT_AUDIT_2026-09-06.pdf` from source, so the PDF is a
build artefact rather than a document that exists only as a binary.

```
pip install reportlab
python3 tools/audit_report/build.py reports/PROJECT_AUDIT_2026-09-06.pdf
```

`build.py` runs `scripts/31_verify_claims.py` and parses its output, so
Appendix A is regenerated from the live data files every time the PDF is built.
If a claim stops matching, the appendix changes and the build asserts on the
count.

| File | What it holds |
|---|---|
| `kit.py` | Page template, styles, table and callout helpers |
| `part1.py` | Front matter, Section 0 (audit method and limits), Sections 1–4 |
| `part2.py` | Sections 5–8 |
| `part3.py` | Sections 9–12 |
| `part4.py` | Sections 13–15, Appendix A, Appendix B |
| `build.py` | Assembles the story and builds the PDF |
