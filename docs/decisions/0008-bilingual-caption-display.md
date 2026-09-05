# 0008. Captions show Italian and the student's language together

- **Status:** accepted
- **Date:** 2026-09-05

## Context

Students' Italian comprehension, while still developing, is reasonable —
replacing the Italian entirely with a translation would work against the
course's own goal of building Italian fluency. Translation can also fail or
be unavailable for a given language.

## Decision

Eco's caption screen shows the Italian transcript together with a
translation into the student's own language underneath, rather than the
translation alone.

## Consequences

Easier: the interface supports the course's language-learning goal rather
than routing around it; a translation failure degrades gracefully to
Italian-only rather than a blank screen (see `docs/operations.md`). Harder:
more information on screen at once, which interacts with the
unverified-reading-fluency open question (see `docs/open-questions.md`).
