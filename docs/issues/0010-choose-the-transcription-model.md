# 0010. Choose the transcription model

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M2
- **Opened:** 2026-09-05

## Context

Whisper-class models trade word error against latency and VRAM, and the
budget is shared with translation on one 16 GB card.

## What it takes

Benchmark candidates at a couple of quantisations for WER, real-time
factor and resident VRAM. Measure on the maintainer's read-aloud of the
classroom corpus through the actual lavalier — the public-corpus number is
comparable, but this one is the representative one. Needs a decision record.

## Done when

A decision record with both numbers and the failure cases listed rather than averaged away.
