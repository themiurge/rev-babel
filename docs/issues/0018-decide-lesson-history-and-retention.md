# 0018. Decide lesson history and retention

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M5
- **Opened:** 2026-09-05

## Context

Scrollback within a lesson is a client buffer and stores nothing.
"What did we do last week" needs persistence, which
[`data-and-privacy.md`](../data-and-privacy.md) leaves open.

## What it takes

Proposed: teacher's speech retained for the lesson plus 24 hours, purged
by a job, with the teacher able to mark a lesson to keep. Student audio is
never transcribed or stored at all.

## Done when

A decision record, a purge job, and the second retention TODO removed.
