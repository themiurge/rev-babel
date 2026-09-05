# 0004. Audio captured in the browser on the teacher's phone

- **Status:** accepted
- **Date:** 2026-09-05

## Context

The teacher moves around the classroom while speaking rather than standing
at a fixed desktop microphone. A wireless lavalier microphone can pair to a
phone but not conveniently to the desktop server itself.

## Decision

Audio is captured in a browser tab on the teacher's phone, which streams it
to the server. The tab uses a Screen Wake Lock so it keeps capturing when
the phone screen would otherwise sleep.

## Consequences

Easier: no driver installation, works with commodity hardware (a phone plus
a lavalier mic), tolerates the teacher moving around the room. Harder: the
system depends on a phone browser tab staying foregrounded and connected
for the whole lesson — backgrounding it is a known failure mode (see
`docs/operations.md`).
