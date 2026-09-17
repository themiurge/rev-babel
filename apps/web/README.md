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
avatar picker), a minimal SQLite session store, and a course page with a
hardcoded "Lezione 1". Lesson 1 embeds two standalone HTML games (mouse
and keyboard, under `static/lessons/lezione-1/`) in iframes; each posts
its score to `/api/scores` and the page shows the student's own personal
best and last attempt only — no leaderboard, per `docs/data-and-privacy.md`
("progress is visible to the teacher only, never to other students"). No
WebSocket handling, no avatar picker yet.
