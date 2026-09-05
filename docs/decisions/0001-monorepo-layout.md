# 0001. Monorepo, Python workspace, one package per service

- **Status:** accepted
- **Date:** 2026-09-05

## Context

rev-babel has one developer and one deployment target (the teacher's
desktop, everything running together). Services (`asr`, `mt`, `llm`,
`encoder`) and the web app are deployed as a unit, not independently
released or scaled.

## Decision

One repository, structured as a Python workspace (via `uv`), with one
package per app/service under `apps/`, `services/`, and `packages/`. Shared
data shapes live in `packages/contracts`.

## Consequences

Easier: single-commit changes across service boundaries, one place to read
the whole system, one CI pipeline. Harder: nothing meaningful, given a
single developer and single deployment target — a polyrepo would add
process overhead with no corresponding benefit here.
