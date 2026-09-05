# 0007. No login — a grid of photo tiles, one per user

- **Status:** accepted
- **Date:** 2026-09-05

## Context

Users are learning to use a mouse, and reading fluency in Latin script
cannot be assumed. A username/password login is a barrier unrelated to the
course content itself.

## Decision

Users select themselves from a grid of photo tiles, one per user, instead
of logging in with credentials. The selection is stored in a signed cookie
scoped to a lesson id, so each lesson starts clean.

## Consequences

Easier: selection requires only recognising a photo and clicking, no
reading or typing. Harder: photos are sensitive data and must never enter
the repository — they live in a gitignored directory on the server only
(see `docs/data-and-privacy.md`). Also open: whether classroom machines are
shared or per-student affects how this picker behaves (see
`docs/open-questions.md`).
