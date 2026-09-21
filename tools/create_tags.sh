#!/usr/bin/env bash
# Recreate this project's milestone tags.
#
# WHY THIS FILE EXISTS
# --------------------
# Roadmap item R7 asked for the pivotal commits to be tagged, so that the
# preregistration story is visible from `git tag` rather than only from a field
# inside research/FROZEN_DESIGN.json.
#
# The tags were created on 6 September 2026, but the session that created them
# could not push them: the GitHub credentials available to it accept writes to
# the working branch and refuse `refs/tags/*` with HTTP 403. That is an access
# boundary, not a bug, and it was not worked around.
#
# So the tag definitions live here instead, where they survive. Run this once
# from a clone that has push rights:
#
#     bash tools/create_tags.sh && git push --tags origin
#
# Re-running is safe: existing tags are left alone.

set -euo pipefail

tag() {
  if git rev-parse -q --verify "refs/tags/$1" >/dev/null; then
    echo "  exists, leaving alone: $1"
  else
    git tag -a "$1" "$2" -m "$3"
    echo "  created: $1 -> $2"
  fi
}

tag design-freeze 20db485 \
"Phase 1-2 design frozen: participant, variable, level, method, boundary day 758 (p=0.0018), plus SHA-256 of blocks.csv and trials.csv. Two amendments, both dated before the analysis. This is the commit research/FROZEN_DESIGN.json records inside itself."

tag phase12-closeout 1d0aba9 \
"Phases 1 and 2 closed. Preregistered result negative and overturned by its own prespecified limitation check: the indicator rose faster during health (tau=+0.857) than overall (+0.743)."

tag amendment-1 6edf505 \
"Amendment 1: no human participants. Every configuration involving a person struck, including the researcher. Fault injector built the same day."

tag grader-before-monitor e161594 \
"The grading system, committed BEFORE the monitor existed. At this commit the only detectors the harness could score were three baselines this project did not invent. This ordering is what makes the benchmark credible."

tag decoder-guard bf5e8c0 \
"decoder-guard added, written before the baseline scores were read."

tag phase3-complete 0262b6f \
"Phase 3 consolidated into one report. 0 of 48 configurations pass all five gates; the binding constraint is specificity, not detection."

tag feature-study-frozen 0950c04 \
"Feature study frozen: four families named, list closed, criterion fixed at +0.05 AUC on BOTH participants in the same direction, with a checksum, before anything was computed."

tag audit-2026-09-06 ea6da24 \
"Full technical and scientific audit. 97 claims verified, five gates passing. Found that the cited literature review is not in the repository."

echo
echo "Done. Now: git push --tags origin"
