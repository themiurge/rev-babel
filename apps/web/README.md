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

A login page (`/`, ADR 0013 for why it's typed names at all, ADR 0015 for
why they're now permanent accounts) shows every roster-visible student as
a one-tap button, plus a name field that only creates a new account if no
case-insensitive match exists. `students.roster_visible` controls who
shows up there — new accounts default to visible; a few pre-existing test
rows (two "Emilio," "Io," "Florencia") were flipped to hidden rather than
deleted, so they're still reachable by retyping the exact name but no
longer clutter the picker. Three page levels follow: the course page
(`/course`, just a greeting today), a lesson page listing its games
(`/course/lezione-1`), and a full-window game page
(`/course/lezione-1/<game>`) with the left sidebar, a small top bar (back
link + personal record), and the game filling the rest of the viewport.
Lesson 1's two games (mouse, keyboard) live under
`static/lessons/lezione-1/` as standalone HTML, unchanged except a
`postMessage` on completion; each posts its score to `/api/scores`, which
shows the student's own personal best and last attempt only — no
leaderboard, per `docs/data-and-privacy.md` ("progress is visible to the
teacher only, never to other students"). No avatar picker yet.

**Language preference and hover translation** (ADR 0015): each student has
a `language` column (`it`/`en`/`fr`/`ckb`/`kmr`/`ar` — both Kurdish
variants are offered since which one a given student actually speaks is
unconfirmed, see issue 0008), changeable from an always-visible dropdown
top right on every page. Every Italian UI label optionally carries a
`title` attribute — a native tooltip — with its translation, looked up in
`rev_babel_web/i18n.py` by the Italian text itself. Machine-translated in
one `agy` CLI batch per language; not yet reviewed by a native speaker of
any of them.

**Slide Sync Lite** ([ADR 0014](../../docs/decisions/0014-slide-sync-lite.md))
syncs one integer — the current slide index — from a presenter page to
every connected student over SSE. `/present` and `/admin/api/live/*`
are the teacher surface, gated on the `Host` header being
`mic.emiliovicari.com` with no further auth; `/follow` is the student
surface, behind the same name-capture session as the rest of the course.
Live state lives in `rev_babel_web/live.py`, in one process's memory
(mirrored to `data/live_state.json`), which only works with a single
uvicorn worker.

**Local HTML slide decks** ([ADR 0016](../../docs/decisions/0016-local-slide-decks-and-split-screen-translation.md))
are a second live-session source alongside Google Slides: JSON files
under `rev_babel_web/decks/*.json`, picked by title on `/present`. A
student following a local deck sees a real split screen — Italian and
their own language, both visible, each boxed at 16:9 — rendered
server-side per slide via `GET /api/live/slide`. A three-slide sample
(`lezione-2-account-demo.json`) exercises the mechanism; it isn't lesson
2's real content yet.
