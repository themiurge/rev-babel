# 0004. Keep the stack up across a reboot

- **Status:** open
- **Owner:** 🧑 Emilio
- **Milestone:** M6
- **Opened:** 2026-09-05

## Context

WSL2 does not start on Windows boot, so a reboot takes the tunnel down
with it. Windows sleep or fast startup at 17:00 would end a lesson in
progress. Quiet, plausible ways to lose a class.

## What it takes

Disable sleep and fast startup; arrange for WSL2 and the stack to come
up on boot. The supervision mechanism itself is part of milestone 6.

## Done when

Cold boot the desktop, touch nothing, and captions are reachable from outside.
