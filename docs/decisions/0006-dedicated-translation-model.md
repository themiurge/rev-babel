# 0006. A dedicated translation model, separate from the chat model

- **Status:** accepted
- **Date:** 2026-09-05

## Context

Eco's captions and Play's conversations would otherwise compete for the
same model's attention. If translation queued behind Play's chat
generation, lecture captions could lag during a lesson where both modules
are in use.

## Decision

Translation (`services/mt`) runs as a model dedicated to that purpose,
separate from the chat model backing Play (`services/llm`).

## Consequences

Easier: lecture captions never queue behind student conversations; a
dedicated model can also be chosen for better coverage of the specific,
often lower-resource, student languages in play. Harder: two models share
the VRAM budget instead of one — a cost accepted for the latency and
coverage benefit (see `docs/architecture.md` for the budget).
