# 0014. Slide Sync Lite: host-gated, no auth, for lesson 1

- **Status:** accepted
- **Date:** 2026-09-17

## Context

Students need to see whatever slide the teacher is on, on their own screen, with no
projector in the room. The chosen design (see the spec the maintainer supplied) is
minimal: Google Slides serves the deck itself; the app only synchronises one integer,
the current slide index, over SSE. It needs a presenter surface (`/present`,
`/admin/api/live/*`) that only the teacher should be able to drive.

There is no auth system in this app yet — the student flow is just a typed name
(ADR 0013), with no notion of a teacher role. Building real auth (even a shared token)
was more than today's lesson-1 budget justified, and `mic.emiliovicari.com` already
exists as the reserved teacher-only hostname for exactly this kind of surface, per
[ADR 0003](0003-cloudflare-tunnel.md) and `plans/m4-network.md` — currently unprotected,
per issue 0001, which is still open.

## Decision

`/present` and every `/admin/api/live/*` endpoint are served only when the request's
`Host` header equals `ECO_CAPTURE_HOST` (`mic.emiliovicari.com`); everywhere else they
403. No further authentication. This is the same accepted risk as issue 0001, just
extended to cover slide control as well as the microphone capture page.

The live state itself (current slide, deck, status) lives in one process's memory,
mirrored to `data/live_state.json` for restart recovery — which requires the app to
keep running as a single uvicorn worker. It already does; this decision makes that
constraint load-bearing rather than incidental.

## Consequences

Easier: no auth code to write today; reuses the hostname split that already exists for
exactly this purpose.

Harder: anyone who discovers the `mic.emiliovicari.com` URL during lesson 1 could change
the students' slide out from under the teacher, not just eavesdrop passively as the
current capture-host exposure allows. Issue 0001 (protect the capture host) now covers
slightly more surface than it did, and should be treated as more urgent, not deferred
further because "nothing sensitive is behind it" — something is, now.

Sharing the Google Slides deck as "Anyone with the link — Viewer" (required for the
embed to render at all) makes the deck itself readable by anyone who obtains the file
ID, independent of this app's own access control.
