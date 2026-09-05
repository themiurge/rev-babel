# 0005. Transcribe whole segments on a voice-activity pause, not streaming

- **Status:** accepted
- **Date:** 2026-09-05

## Context

Streaming transcription re-decodes as more audio arrives, so partial text
on screen visibly rewrites itself — confusing on a caption display meant
for students who cannot be assumed fluent readers to begin with.

## Decision

Audio is buffered and transcribed in whole segments, committed on a
voice-activity pause, rather than transcribed as a continuous stream.

## Consequences

Easier: captions are stable text once shown, never rewriting themselves.
Harder: adds latency versus true streaming — roughly 2–3 seconds from
speech to caption, which is accepted as a reasonable trade for stability.
