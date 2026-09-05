# 0002. Test the classroom network

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M4
- **Opened:** 2026-09-05

## Context

The only part of the path that cannot be tested from home. Institutional
wifi that blocks WebSockets to an arbitrary host would break Eco entirely,
and it would be discovered at 16:30 on the day.

## What it takes

From the actual room, on the actual machines, open the caption host and
confirm a WebSocket opens and holds. `scratchpad/tunnel_smoke_server.py`
does this without needing any of Eco to exist.

## Done when

A WebSocket holds for several minutes from a classroom machine, ideally the week before lesson 1.
