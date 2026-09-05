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

Placeholder. No routes, no WebSocket handling, no templates beyond this
README exist yet.
