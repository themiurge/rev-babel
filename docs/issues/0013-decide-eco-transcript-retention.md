# 0013. Decide Eco transcript retention

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M3
- **Opened:** 2026-09-05

## Context

[`data-and-privacy.md`](../data-and-privacy.md) records the retention
period as undecided. The moment the pipeline runs live it produces a
transcript of the teacher's speech, so it cannot stay undecided.

## What it takes

Proposed default: run logs under gitignored `data/runs/<lesson>/`,
deleted on exit unless explicitly kept. Nothing retained by default;
retention becomes opt-in. Confirm or change, then record it and remove the
TODO rather than leaving both.

## Done when

A decision record, and `data-and-privacy.md` with no TODO on this point.
