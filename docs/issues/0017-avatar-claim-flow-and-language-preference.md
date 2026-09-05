# 0017. Avatar claim flow and language preference

- **Status:** open
- **Owner:** 💻 code
- **Milestone:** M5
- **Opened:** 2026-09-05

## Context

Identity is the avatar: a user row is an id, an avatar id and a language,
with no name and no photograph. The session cookie stays scoped to a lesson,
so preferences must live server-side or they are forgotten every week.

## What it takes

Unclaimed and claimed grid states; exclusive server-side claims; a "not
me" control; teacher-side release. Needs a decision record covering
identity, preferences and history storage.

## Done when

Two browsers racing for one avatar: exactly one wins. A test asserts the database holds no name and no photograph.
