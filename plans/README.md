# Plans

Implementation plans for rev-babel, milestone by milestone. A plan here is
a *route*, not a decision: it says what to build, in what order, and how we
will know it works. Where it reaches a fork that a future reader would have
to reverse-engineer, it names the fork and points at the ADR that must
settle it — it does not settle it in passing.

Docs in [`docs/`](../docs/README.md) describe the system as designed. Plans
here describe how it gets built. When a plan's step lands, the
corresponding doc is updated and the plan step is ticked, not deleted.

## Milestones

| # | Plan | Produces | Depends on |
|---|------|----------|------------|
| 1 | [Translation module](m1-translation.md) | segment stream in → captions in en/fr/ar out | — |
| 2 | [Speech to text](m2-speech-to-text.md) | audio file in → segment stream out | contracts from M1 |
| 3 | [Live pipeline](m3-live-pipeline.md) | live audio → transcript → translation → console | M1, M2 |
| 4 | [Network setup](m4-network.md) | phone mic in, caption page out, over the internet | M3 |
| 5 | [Frontend and backend](m5-frontend-backend.md) | picker, per-user language, lesson history | M4 |
| 6 | [End to end](m6-end-to-end.md) | one command, a runbook, a dress rehearsal | all |

## The calendar problem

The course starts **Thursday 17 September 2026** — twelve days from the
date this plan was written (5 September 2026). Ten lessons, Thursdays,
16:30–18:00, through 19 November. Eco is needed from lesson 1
(`docs/roadmap.md`), so the plan below is sequenced against that date, not
against an ideal build order.

Milestones 1–4 are on the critical path for lesson 1. Milestone 5 is not,
in full: lesson 1 can run with a caption page per language at an
unguessable URL, no picker and no stored history, with per-student
identity and preferences arriving in weeks 2–4.

### Cut line — what must be true on 17 September

- Teacher's phone captures audio and it reaches the server (M4).
- Italian speech becomes stable segments within ~3 s (M2, M3).
- Each segment is translated into the languages actually present, with
  Italian shown alongside (M1, ADR 0008).
- Students open a URL on a classroom machine and see captions, with
  scrollback (ADR 0009).
- A translation failure degrades to Italian-only, and total failure shows
  an honest message — the teaching assistant translating live remains the
  standing human fallback (`docs/operations.md`).

Anything past that line — the photo picker, saved language preferences,
cross-lesson history, Play — is week 2 or later.

### Suggested schedule

| Dates | Work |
|-------|------|
| 5 Sep (today) | **Start the external steps in [M4](m4-network.md)** — domain and Cloudflare propagate on their own clock, not ours |
| 5–7 Sep | M1 — translation module |
| 8–9 Sep | M2 — speech to text |
| 10 Sep | M3 — live pipeline and console |
| 11–13 Sep | M4 — tunnel, capture path, caption page over the internet |
| 14–15 Sep | M5 (cut-down) — a caption page good enough to teach with |
| 16 Sep | M6 (cut-down) — start script, pre-lesson checklist, dress rehearsal |
| 17 Sep | **Lesson 1**, TA fallback ready |
| Weeks 2–4 | M5 in full, M6 hardening, then Play |

If a milestone slips, the cut line is what to protect. Shipping M1–M3 and
running lesson 1 from the teacher's own laptop screen in the classroom is
a better outcome than shipping nothing.

## Standing rules for every milestone

- [`docs/data-and-privacy.md`](../docs/data-and-privacy.md) binds every
  step. Test fixtures are invented sentences in a classroom register,
  never anything a real student said. Evaluation corpora that are
  downloaded rather than written live in gitignored `data/`.
- Every milestone must stay runnable in CI on a GPU-less GitHub runner.
  That means every model-backed component has a no-model backend used by
  the tests.
- Each milestone lists the ADRs it obliges. Write them as the decision is
  made, not in a batch at the end (`CONTRIBUTING.md`).
- Each milestone ends with `make lint && make test` green and the relevant
  `docs/` page updated from "as designed" to what actually exists.
