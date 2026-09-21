# Window-overlap contamination — quantifying a limitation I recorded and left open

**Written before running.**

## The defect

Windows are 1500 bins (30 s) long, stepped every 250 bins (5 s). Local
re-baselining takes an episode's "pre-onset" windows as `F[:ow]`, where
`ow = searchsorted(starts, onset_bin)` — the first window whose *start* is at or
after onset.

But a window that *starts* before onset still extends 1500 bins past its start.
Any window with `start + 1500 > onset_bin` therefore **contains post-onset,
faulted data while being counted as healthy**. That is up to
1500 / 250 = **6 windows**, previously estimated at roughly a quarter of a typical
episode's healthy reference.

This was found during the benchmark work, recorded as a limitation on the grounds
that its bias is *conservative*, and never measured. It is one of two open items
I left explicitly unresolved.

## Why the bias should be conservative

Contaminating the healthy reference with faulted data drags the reference toward
the fault, so the fault looks *less* anomalous and detection gets *harder*. The
recorded results should therefore understate performance rather than overstate it.

**That is an argument, not a measurement**, which is why it needs one.

## Prediction, committed

**Removing the contaminated windows should raise AUC slightly, on both
participants.** If it *lowers* AUC, my reasoning about the direction of the bias
was wrong and every place I cited "the bias is conservative" needs correcting.

I expect the effect to be **small** — a few thousandths of AUC — because local
re-baselining uses a median over the pre-onset windows, and a median is not moved
much by contaminating a quarter of its inputs.

## Fixed in advance

| | |
|---|---|
| Strict reference | only windows with `start + WINDOW_BINS <= onset_bin` |
| Minimum | an episode needs ≥ 3 strictly-clean windows, else it is excluded from **both** arms so the comparison stays paired |
| Everything else | identical — same days, same episodes, same 40-window same-day fits |
| Reported | per-day and pooled AUC under both references, both participants, whatever the sign |
