# 0009. Screen keeps a scrollback of recent segments

- **Status:** accepted
- **Date:** 2026-09-05

## Context

Students have young children who may be present, and a student may need to
leave the room for several minutes at a time during a lesson. A caption
display that only ever shows the current segment would lose whatever was
said while she was out.

## Decision

The caption screen keeps a scrollback buffer of recent segments, so a
student can catch up after stepping away, rather than optimising purely
for lowest possible latency on the current segment.

## Consequences

Easier: students who step out don't lose the thread of the lesson. Harder:
the client must retain and render a short history rather than just the
latest line — a small added complexity, accepted because catching up
matters more here than shaving latency further (see
[ADR 0005](0005-segment-level-transcription.md) for the latency this is
layered on top of).
