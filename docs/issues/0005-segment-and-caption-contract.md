# 0005. Segment and caption contract

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M1
- **Opened:** 2026-09-05

## Context

Everything downstream agrees on two shapes: a transcribed segment and a
translated caption. They are the same shape on stdin, on an asyncio queue,
and on a WebSocket — one contract, three transports.

## What it takes

`Segment` and `Caption` in `packages/contracts`, a JSON Lines codec, and
a validator asserting the characteristics `services/asr` must guarantee
(committed text, no split words, gapless `seq`, in order). Needs a
decision record.

## Done when

Round-trip tests pass; a malformed or out-of-order stream fails loudly rather than silently.
