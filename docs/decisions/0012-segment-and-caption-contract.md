# 0012. Segment and Caption as pydantic models over JSON Lines

- **Status:** accepted
- **Date:** 2026-09-06

## Context

`services/asr` (M2) produces transcribed segments; `services/mt` (M1)
consumes them and produces translated captions; `apps/web` (M5) carries
both across a WebSocket. All three need to agree on one shape without
importing each other's internals ([ADR 0001](0001-monorepo-layout.md)),
and the same shape has to survive three different transports: a pipe
between CLI processes, an in-process asyncio queue, and a WebSocket frame.
issue 0005 asked for the shapes, a codec, and a validator that catches a
misbehaving producer rather than passing its output on.

## Decision

`Segment` and `Caption` are pydantic v2 models in `packages/contracts`,
matching the fields already specified in `plans/m1-translation.md`. The
wire format is JSON Lines: one JSON object per line, UTF-8, identical on
stdin/stdout, on the queue, and on the socket.

Two layers of checking, kept separate because they answer different
questions:

- **Shape**, enforced by the models themselves at construction: no blank
  `text`/`lesson_id`/etc., `ended_at_ms` after `started_at_ms`, and a
  `degraded` caption must carry its `source_text` verbatim in `text`
  (`docs/operations.md`'s Italian-only fallback, made structurally
  impossible to violate rather than merely documented).
- **Stream**, enforced by `validate_segment_stream`/`validate_caption_stream`
  as items pass through: `seq` gapless and strictly in order (per
  `target_lang`, for captions, since one segment fans out to several), and
  the 15 s hard cap from `plans/m2-speech-to-text.md`'s VAD design.
  "Committed text, no split words" is not something a validator can check
  from the segment alone — that guarantee is `services/asr`'s to keep, not
  the contract's to verify.

`parse_jsonl` raises `ContractViolation` on the first malformed line or
failed shape check; the stream validators raise the same on the first
ordering violation. Both stop the stream rather than skip, drop, or
reorder — a malformed or out-of-order stream is a bug upstream, and
issue 0005 asked for it to fail loudly.

## Consequences

Easier: three services and three transports share one definition of
correct, checked in one place; a degraded caption cannot accidentally ship
a stale or partial translation, because the model itself refuses to
construct one. Harder: nothing significant — the models are what the plan
already specified, and pydantic is a dependency `apps/web` needs regardless.
