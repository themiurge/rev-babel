# Overview

## The course

A computer-literacy course for adult migrant women in Bologna, Italy. Ten
weekly lessons, 16:30–18:00, running 17 September to 19 November 2026. Six
users total: five students and a teaching assistant, plus the teacher.

This is a small, closed group, deliberately — rev-babel is scaffolded for
six concurrent users, not a general classroom tool.

## The users, in role terms

- **Teacher** — leads the lesson, speaks in Italian (occasionally English),
  presents at the front of the room.
- **Students** — five adult migrant women. Reading fluency in Latin script,
  and first-language reading fluency generally, cannot be assumed for any of
  them (see `open-questions.md`). They are also learning to use a mouse and
  keyboard alongside the course content itself.
- **Teaching assistant** — supports students during the lesson, and can
  translate live if the system fails (see `operations.md`).

No student's name, photograph, or recorded voice belongs in this repository.
See `data-and-privacy.md`.

## What problem each module solves

**Eco** addresses the gap between spoken Italian at teaching pace and a
student's ability to follow it in real time. Rather than requiring a student
to mentally translate while also trying to catch new vocabulary, her screen
shows the Italian transcript with a translation into her own language
underneath, updating a few seconds behind the teacher's speech.

**Play** gives students a way to rehearse spoken, real-life situations
(asking for directions, a doctor's appointment, a shop transaction) against a
conversational partner that is patient, repeatable, and available outside
class hours if needed. Input is spoken rather than typed, because for this
group typing is itself a barrier separate from the language being practised.

## Why the constraints are what they are

- **No login picker, no typed input for Play** — several students cannot be
  assumed fluent with a mouse, let alone a keyboard, and reading fluency
  cannot be assumed even in their own language. Every interaction is
  designed around recognition (an avatar she chose, a spoken sentence)
  rather than
  typing or reading dense text.
- **Small and self-hosted, not cloud-deployed** — the entire system exists to
  serve one course, on hardware the teacher already owns. It is not built to
  scale past six concurrent users, and doing so is explicitly out of scope.
- **No personal data in the repository** — the users are migrant women and
  their young children, in a repository that is public. This shapes nearly
  every decision recorded in `decisions/` and is stated in full in
  `data-and-privacy.md`.

See `architecture.md` for how these constraints translate into the system's
shape, and `decisions/` for the reasoning behind individual technical
choices.
