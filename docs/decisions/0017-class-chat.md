# 0017. A class chat, in memory, with the account name

- **Status:** accepted
- **Date:** 2026-10-29

## Context

The maintainer asked for a live-chat interface (Discord / YouTube Live style)
showing who wrote what. ADR 0015 already gives every student a permanent
named account chosen at login, so a name is not a new category of data. Free
text typed by a student is: [`data-and-privacy.md`](../data-and-privacy.md)
had no such thing before.

## Decision

`/chat` shows one class-wide room. The author shown is the account name
chosen at login. Messages are held in the web process's memory
(`rev_babel_web/chat.py`), expire 24 hours after they are sent, are capped
at 500 messages and 500 characters each, and are never written to disk or to
the database. A restart empties the room. Delivery is SSE plus a POST, the
same shape as Slide Sync Lite (ADR 0014), and likewise needs a single
uvicorn worker. Messages are rendered with `textContent`, never as HTML.

## Consequences

Students' free text now exists on the teacher's machine for up to a day. It
must never reach the repository, logs, or fixtures; tests use role labels.
No moderation, mute, or teacher-side view yet (the teacher has no account
on this host); the teacher can clear the room by restarting the service.
Messages are not translated.
