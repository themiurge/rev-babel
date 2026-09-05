# 0019. Make the stack operable

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M6
- **Opened:** 2026-09-05

## Context

`infra/compose.yaml` is a stub, and containers are not obviously right:
one GPU, one budget, one machine. [ADR 0002](../decisions/0002-run-everything-in-wsl2.md)
already puts one process boundary in charge of the VRAM.

## What it takes

Decide supervision (systemd units vs compose) and record it. `make up`,
model warm-up at start, `/healthz`, one log stream. Then fill every TODO in
[`operations.md`](../operations.md), including the pre-lesson checklist and
which service is shed on OOM.

## Done when

Cold boot to captions with no step outside the checklist, and a 90-minute rehearsal with injected failures.
