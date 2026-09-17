# apps/web

The FastAPI app: serves pages, manages lesson sessions, and fans out
caption updates to connected student browsers over WebSocket.

This is what a student's or teacher's browser talks to directly. It hosts
the avatar picker
([ADR 0010](../../docs/decisions/0010-avatar-picker.md)), receives the
teacher's audio stream, and delivers Eco captions and Play conversation
turns to the right connected clients.

## What belongs here

Routes, session/cookie handling, WebSocket connection management, templates
and static assets for the browser-facing pages.

## What does not belong here

Any model inference (transcription, translation, chat) — those live in
`services/`. This app calls them; it does not implement them.

## Status

A welcome screen (typed name, ADR 0013 — a temporary stand-in for the
avatar picker), a minimal SQLite session store, and three page levels: the
course page (`/course`, just a greeting today), a lesson page listing its
games (`/course/lezione-1`), and a full-window game page
(`/course/lezione-1/<game>`) with the left sidebar, a small top bar (back
link + personal record), and the game filling the rest of the viewport.
Lesson 1's two games (mouse, keyboard) live under
`static/lessons/lezione-1/` as standalone HTML, unchanged except a
`postMessage` on completion; each posts its score to `/api/scores`, which
shows the student's own personal best and last attempt only — no
leaderboard, per `docs/data-and-privacy.md` ("progress is visible to the
teacher only, never to other students"). No avatar picker yet.

**Slide Sync Lite** ([ADR 0014](../../docs/decisions/0014-slide-sync-lite.md))
syncs one integer — the current Google Slides index — from a presenter page
to every connected student over SSE. `/present` and `/admin/api/live/*`
are the teacher surface, gated on the `Host` header being
`mic.emiliovicari.com` with no further auth; `/follow` is the student
surface, behind the same name-capture session as the rest of the course.
Live state lives in `rev_babel_web/live.py`, in one process's memory
(mirrored to `data/live_state.json`), which only works with a single
uvicorn worker.
