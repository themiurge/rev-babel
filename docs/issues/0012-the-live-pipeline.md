# 0012. The live pipeline

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M3
- **Opened:** 2026-09-05

## Context

Where Eco first exists as a system. The interesting behaviour is not when
it keeps up but when it does not.

## What it takes

`AudioSource` with file, device and websocket backends; bounded queues;
an explicit shedding policy (never drop audio; shed translation per
language, oldest first, emitting degraded captions). A console renderer
that stays as the teacher-side debug view.

## Done when

20 minutes continuous, p50 under 3 s speech-to-console, memory flat, deliberate backlog sheds by the stated policy.
