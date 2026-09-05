# 0010. A preset avatar collection, claimed on first use, instead of photos

- **Status:** accepted
- **Date:** 2026-09-05
- **Supersedes:** [ADR 0007](0007-no-login-picker.md)

## Context

[ADR 0007](0007-no-login-picker.md) replaced credentials with a grid of
photo tiles, one per user, because reading and typing cannot be assumed
for this group. The recognition argument holds. The photographs do not:
they are the most sensitive data the system would hold, they require a
photograph of each user to be taken and stored before she can use
anything, and they oblige every future contributor to keep a category of
personal data out of a public repository by discipline alone (see
[`data-and-privacy.md`](../data-and-privacy.md)).

Recognition does not require a photograph. It requires a picture that is
unmistakably *hers*, which a chosen avatar supplies as well as a face
does — and better, in that she chooses it rather than being photographed.

## Decision

The picker shows a preset collection of ready-made avatars, drawn ahead of
time and shipped as static assets in this repository. They depict nobody
real.

On first use a student claims an avatar: she taps one from the unclaimed
pool, and it is hers for the rest of the course. From then on the grid
shows the claimed avatars and she taps her own. A claim is exclusive
within the course, and the teacher can release one if it was made by
mistake.

The avatar *is* the identity. The system stores a user id, the avatar
claimed against it, and that user's language preference. It stores no
name and no photograph, of anyone.

The collection holds meaningfully more avatars than there are users, so
that choosing is a real choice rather than an allocation.

## Consequences

Easier: the system no longer holds a photograph of anyone, so the rule in
`data-and-privacy.md` about photographs becomes a property of the design
rather than a discipline imposed on contributors. Nothing has to be
collected from a student before she can use the system for the first time
— she arrives, taps a picture she likes, and that is the whole enrolment.
Avatar art is not personal data, so it lives in version control like any
other static asset and the picker works on a fresh install with no
server-side setup.

Harder: a student must remember which avatar she chose, where a photograph
of her face needed no remembering. Mitigations: the avatar stays the same
every week, the caption screen shows it so a wrong choice is visible
immediately, tapping the wrong tile costs nothing but the wrong caption
language, and the teacher's control page can correct a claim.

The avatars must therefore be sharply distinguishable at tile size — by
silhouette and by background colour, not by facial detail — for users who
cannot be assumed to read the Latin script that would otherwise label
them. They must also be free of anything that reads as ethnic or religious
caricature; this is a group of migrant women, and a picture that lands
badly is worse than no picture.

Unchanged from ADR 0007: no credentials, no typing, selection stored in a
signed cookie scoped to a lesson id. Still open, as it was there: whether
classroom machines are shared or assigned per student (see
[`open-questions.md`](../open-questions.md)).
