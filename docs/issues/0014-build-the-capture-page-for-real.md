# 0014. Build the capture page for real

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M4
- **Opened:** 2026-09-05

## Context

The blueprint in [`scratchpad/`](../../scratchpad/README.md) works and its
shape is proven. The real one needs the parts a smoke test skipped.

## What it takes

Port it into `apps/web`: 500 ms chunks, Wake Lock, reconnect with
backoff, a guard against starting a second capture while one is live, an
honest level meter, and the token check before `accept()`.

## Done when

A phone streams for 90 minutes, survives a dropped connection, and shows the teacher when it has stopped.
