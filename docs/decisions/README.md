# Architecture decision records

An ADR records a technical decision, the context that led to it, and its
consequences — so that later, someone (including a future maintainer) can
tell *why* the system looks the way it does, not just *that* it does.

## Format

Each ADR is one file, numbered sequentially, under a page:

```
# NNNN. Title

- **Status:** accepted | superseded | proposed
- **Date:** YYYY-MM-DD

## Context

What situation or constraint made a decision necessary.

## Decision

What was decided, stated plainly.

## Consequences

What this makes easier, harder, or ruled out.
```

## Adding one

New ADRs get the next sequential number and are never renumbered, even if
superseded — add a new ADR that supersedes the old one and update the old
one's status.
