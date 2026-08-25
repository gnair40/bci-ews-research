# data/processed/ — DERIVED DATA

Anything computed from `../raw/` goes here: cleaned tables, aligned
neural/behavioural time series, rolling-window statistics, and so on.

## Rules

1. Every file here must be **regenerable** by running a script in `scripts/`.
   If you cannot say which script produced a file, it does not belong here.
2. Name files so their origin is obvious (e.g. `T5_trials_aligned.parquet`).
3. Contents are Git-ignored — they are derived, and re-deriving them is the
   point.

## Why separate this from raw/

Splitting "the data as given" from "the data as we transformed it" means you can
always answer the reviewer's question *"what did you do to the data?"* by
pointing at a script, rather than by remembering. It also means a bug in
preprocessing is fixed by deleting this folder and re-running — never by trying
to undo an edit to an irreplaceable file.

Currently empty — no preprocessing has been designed yet, deliberately. We
establish what the dataset contains before deciding how to transform it.
