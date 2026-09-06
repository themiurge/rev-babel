# packages/contracts

Shared data shapes passed between services — e.g. a transcribed segment
from `services/asr`, a translated caption from `services/mt` — so that
services agree on shape without importing each other's internals.

## What belongs here

Data shape definitions only (e.g. dataclasses/pydantic models) shared
across two or more of `apps/web`, `services/asr`, `services/mt`,
`services/llm`, `services/encoder`.

## What does not belong here

Any business logic. This package defines shapes, not behaviour.

## Status

`Segment` and `Caption` are defined (pydantic v2), with a JSON Lines codec
and stream validators asserting the ordering guarantees `services/asr` and
`services/mt` must hold. See
[ADR 0012](../../docs/decisions/0012-segment-and-caption-contract.md).
