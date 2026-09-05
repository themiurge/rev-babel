# 0009. Segment audio on voice-activity pauses

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M2
- **Opened:** 2026-09-05

## Context

[ADR 0005](../decisions/0005-segment-level-transcription.md) commits to
whole segments cut on a pause. Real speech measured on 5 September pauses
every 3–4 seconds, which suggests this will produce sensibly-sized
segments — but the parameters still need tuning against real teaching
pace, not a read-aloud.

## What it takes

Silero VAD over decoded 16 kHz mono, min speech 250 ms, min silence
500 ms, pad 200 ms, hard cut at 15 s. Testable with a null transcriber, so
it runs in CI without a GPU.

## Done when

No segment exceeds the cap or splits a word; the same file twice gives identical segments.
