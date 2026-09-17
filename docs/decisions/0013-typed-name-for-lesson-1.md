# 0013. A typed name as a temporary stand-in for the avatar picker

- **Status:** accepted
- **Date:** 2026-09-17

## Context

Lesson 1 needs *something* at the door today, and the avatar picker
([ADR 0010](0010-avatar-picker.md)) is weeks out: the avatars themselves
are not drawn yet (issue 0016), and the claim flow is not built (issue
0017). The maintainer chose to ship a typed-name welcome screen today
rather than wait, explicitly as a placeholder to be replaced.

This is a deliberate, acknowledged deviation from ADR 0010, not a
reconsideration of it. ADR 0010's reasoning stands: these students are
learning to use a mouse, reading fluency in Latin script cannot be
assumed, and a name is more sensitive than an avatar choice. Lesson 1's
own content is "La Tastiera e il Mouse" — the keyboard and the mouse —
which makes typing a name at the door a poor fit on usability grounds
alone, before privacy is even considered.

## Decision

For lesson 1 only, `apps/web` asks for a typed name and stores it in a
local SQLite database (`data/rev_babel.db`, gitignored, never committed)
keyed by a random student id held in a signed session cookie. No other
personal data is collected. This is scoped to get one lesson running; it
is not a redesign of identity for the course.

## Consequences

Easier: nothing to draw or build before today's lesson works end to end.

Harder: real names now exist, transiently, on the teacher's machine —
still never committed, but a category of data ADR 0010 specifically
designed the system to avoid holding at all. This must not be treated as
settled: the avatar picker (issues 0016, 0017) supersedes this screen as
soon as it exists, and this ADR's status should move to superseded at
that point, with the `students` table dropped rather than migrated.
