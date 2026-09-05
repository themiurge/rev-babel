# 0002. Run everything inside WSL2, not split across Windows and Linux

- **Status:** accepted
- **Date:** 2026-09-05

## Context

The host is a Windows 11 desktop. vLLM, the intended serving path for
Play's chat model, has no real Windows support. Splitting services across
the Windows host and a WSL2 guest would mean two processes both allocating
from the same single GPU with neither aware of the other's usage.

## Decision

Every service runs inside WSL2 (Ubuntu). Nothing GPU-related runs directly
on Windows.

## Consequences

Easier: one process boundary is responsible for the entire 16 GB VRAM
budget, so allocation across services (`asr`, `mt`, `llm`, `encoder`) can
be reasoned about in one place. Harder: anything that assumes native
Windows GPU access is unavailable — not a real constraint here since
nothing in the design needs it.
