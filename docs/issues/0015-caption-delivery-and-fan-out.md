# 0015. Caption delivery and fan-out

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M4
- **Opened:** 2026-09-05

## Context

One publisher per lesson, subscriber groups per language, and a replay of
recent segments on connect so a reconnecting client has no gap — ADR 0009
applied to the network rather than just the scrollback.

## What it takes

For lesson 1 this can be one URL per language with an unguessable lesson
id and no picker. Degradation per
[`operations.md`](../operations.md): translation failure falls back to
Italian only.

## Done when

Six clients, three languages, 90 minutes, and a client that drops for a minute returns with no hole.
