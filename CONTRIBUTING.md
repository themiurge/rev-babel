# Contributing

This project currently has a single maintainer working directly on `main`.
The ADR process below isn't a merge gate — it exists so a future reader
(including a future maintainer) can tell *why* the system looks the way it
does, not just *that* it does.

## When to write an ADR

Write one when a change:

- Introduces a new external dependency or service boundary (a new model, a
  new way of exposing the app).
- Changes how or where data is stored or transmitted — anything that
  touches [`docs/data-and-privacy.md`](docs/data-and-privacy.md).
- Reverses or supersedes a decision already recorded in
  [`docs/decisions/`](docs/decisions/README.md).
- Makes a choice that isn't obvious from reading the code, and that a
  future maintainer would otherwise have to reverse-engineer.

Skip it for straightforward bug fixes, refactors that don't change
externally visible behaviour, or anything already covered by an existing
ADR.

## How to write one

See [`docs/decisions/README.md`](docs/decisions/README.md) for the format
and numbering rules. In short: next sequential number (never reused or
renumbered), Context/Decision/Consequences/Status/Date, under a page. If it
supersedes an earlier ADR, add a new one and update the old one's status to
`superseded`, linking to the new one.

## Before you start

Read [`docs/data-and-privacy.md`](docs/data-and-privacy.md) first. Its
rules — no student names, no photographs, no transcripts, no `.env` — apply
to every commit, ADRs included: an ADR's "Context" section should use an
invented scenario, never a real one from a lesson.
