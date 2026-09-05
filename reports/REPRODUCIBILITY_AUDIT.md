# Does any of this actually reproduce?

**Script:** `55_reproducibility_audit.py` (runs last, with the verifier)

Fifty-five scripts written over weeks, nineteen reports, and a claim-verifier
depending on a web of intermediate files. The README asserted the scripts are
"numbered in dependency order". This checks that assertion instead of repeating
it.

## What is checked

| | |
|---|---|
| **Imports** | every third-party module imported anywhere appears in `requirements.txt` |
| **Producers** | every `data/processed` file a script *reads* is *written* by some script |
| **Order** | no script reads a file produced by a higher-numbered script |
| **References** | every script named in a report or the README exists |

Static analysis, so it cannot prove the pipeline runs — but a break in any of
these four is a break in the reproduction path, and none of it needs the 9 GB of
raw data.

## Current status: **PASS**

- 6 third-party imports, all declared
- 35 consumed files, all with a producer
- no ordering inversions
- every script named across 53 documents exists

## What it found the first time

**1. A headline figure that no committed script produced.** The combined sign
test in `reports/WINDOW_OVERLAP.md` — 11 of 13 days improved, p = 0.011 — was
computed in an ad-hoc shell one-liner, and `31_verify_claims.py` was checking a
JSON file nothing in the repository regenerated. A fresh clone would have failed
that claim. The test now lives in `54_window_overlap.py` and produces the same
numbers.

That is precisely the failure this audit exists to catch: a verified claim
resting on an unreproducible file looks exactly like a verified claim.

**2. The "numbered in dependency order" claim was false.**
`31_verify_claims.py` reads output from fifteen higher-numbered scripts, because
it recomputes every headline figure from whatever the pipeline produced. Its
number records when it was written, not where it runs. Renumbering would break
the script names quoted throughout the reports, so the README now says what is
true: **two scripts run last**, the verifier and this audit.

## Two files the audit cannot resolve, verified by hand

`reference_decoder.npz` and `reference_decoder.json` are written by
`18_reference_decoder.py` through `decoder_paths()`, which *returns* the path —
so the filename literal never appears near the `np.savez` / `write_text` that
writes it. Following that needs interprocedural analysis, which is more machinery
than a static audit should carry.

They are named explicitly in `RESOLVED_BY_HAND` with their real producer, so the
check stays a clean gate rather than a permanently-failing one. **Anything not on
that two-item list is a real finding.**

## Three bugs in the audit itself, fixed before its output was trusted

Written down because a tool that reports its own artefacts as findings is worse
than no tool.

1. **f-strings parsed by regex.** `f"calibration_curve{sfx}.csv"` was captured as
   the filename `}.csv`, reported as an orphan read by ten scripts. Fixed by
   flattening `JoinedStr` nodes in the AST.
2. **Filenames held in variables.** `ckpt = OUT / f"staleness{sfx}.csv"` followed
   by `to_csv(ckpt)` twenty lines later looked like a read with no write. Fixed by
   following one level of assignment — not full dataflow, but enough.
3. **The audit as its own producer.** The phrase `-> write_text` inside its own
   allowlist matched the write-call pattern, making it the recorded producer of
   the decoder files. Fixed by excluding the audit from its own scan.

## Limitations

- **Static only.** It cannot detect a script that runs and produces wrong output,
  only one that cannot run at all for want of an input.
- Write/read classification is pattern-based over a few lines of context plus one
  level of assignment. A sufficiently indirect path escapes it — which is exactly
  what the two hand-resolved files demonstrate.
- It does not check that `requirements.txt` pins versions, only that the packages
  are named.
