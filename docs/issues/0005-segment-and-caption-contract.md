# 0005. Segment and caption contract

- **Status:** done
- **Owner:** 💻 code
- **Milestone:** M1
- **Opened:** 2026-09-05
- **Closed:** 2026-09-06

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

## What happened

`Segment` and `Caption` landed as pydantic v2 models in
`packages/contracts`, with a JSON Lines codec (`dump_jsonl`/`parse_jsonl`)
and two stream validators (`validate_segment_stream`,
`validate_caption_stream`) enforcing gapless, in-order `seq` and the 15 s
segment hard cap. "Committed text, no split words" turned out to not be
independently checkable from the segment alone — recorded as such in
[ADR 0012](../decisions/0012-segment-and-caption-contract.md), which is
`services/asr`'s obligation to keep rather than the contract's to verify.
30 tests, all passing; `make test`/`make lint` clean.
