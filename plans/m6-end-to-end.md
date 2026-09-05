# Milestone 6 — end to end

**Goal.** The stack comes up with one command, survives a lesson, and has
a runbook that someone tired and in a hurry can follow. Nothing new is
built here; what is built is made operable.

## Bringing it up

`infra/compose.yaml` is currently a stub, and containers are not obviously
the right answer: one GPU, one 16 GB budget, one machine, one developer,
and ADR 0002 already puts everything inside WSL2 for exactly the reason
that a single process boundary should own the VRAM. Systemd units inside
WSL2, with the models loaded in one process, is likely simpler and easier
to reason about than containers sharing a card.

Decide it rather than drift into it. → *ADR 0018: how the stack is
supervised (systemd units vs. compose), and what happens to
`infra/compose.yaml`.*

Either way: `make up` starts everything, `make down` stops it, models are
warmed at start so lesson 1 does not spend its first two minutes loading
weights, and `/healthz` says which components are actually up.

## The VRAM budget, with numbers

`docs/architecture.md` describes the budget qualitatively and defers
sizing to `docs/open-questions.md`. By this milestone every Eco model has
been measured (M1 step 7, M2 step 3). Write the numbers into
`architecture.md`: resident footprint per model, load order, and headroom
remaining for Play.

`docs/operations.md` also leaves open which service is shed first on OOM.
With Eco needed every lesson and Play optional, the answer is Play — but
it should be recorded as a decision and implemented as a policy, not left
to whichever allocation happens to fail.

## Filling in the runbook

`docs/operations.md` is a list of TODOs. Each one now has an answer to
write down:

- Starting and stopping the stack — from the supervision decision above.
- **A pre-lesson checklist**: tunnel reachable from outside, GPU free,
  models warm, phone charged and paired, capture page authenticated,
  caption page loads on a classroom machine, avatar claims intact.
  Written
  so it can be run in five minutes before 16:30.
- Home internet down — the TA delivers the lesson without Eco. Already the
  design's standing fallback; state it as the procedure it is.
- PC rebooted mid-lesson — recovery steps, and whether the stack
  auto-starts.
- GPU OOM — the shed policy above.
- Phone tab backgrounded — how it is detected, what the teacher sees, how
  to recover.
- Total failure — the pre-translated honest message from M5.

## Steps

1. Supervision decision and `make up` / `make down`.
2. Model warm-up at start; `/healthz` reporting per component.
3. `.env.example` filled in with the variable names that now exist —
   values empty, per `docs/data-and-privacy.md`.
4. One log stream for the whole stack; a per-lesson metrics summary
   written on stop.
5. `docs/operations.md` rewritten with no TODOs left.
6. `docs/eco.md`, `docs/architecture.md`, `docs/roadmap.md` updated from
   "as designed" to what exists.
7. `docs/open-questions.md` pruned: every entry these milestones resolved
   is replaced by a decision and an ADR, not deleted silently.
8. **Dress rehearsal**: 90 minutes, six clients, three languages, in the
   actual classroom on the actual machines if at all possible, with a
   deliberate failure injected (kill MT, restart the tunnel) to confirm
   the degradation path behaves as documented.

## Acceptance criteria

- Cold boot of the desktop to captions on a classroom machine, with no
  step outside the checklist.
- 90-minute rehearsal with injected failures, no manual recovery beyond
  what the runbook documents.
- Every TODO in `docs/operations.md` resolved or reclassified as a known,
  accepted gap.
- `make lint && make test` green; CI still runs without a GPU.

## After this

Play (`services/llm`) is week 2 or later, and `services/encoder` later
still — `docs/roadmap.md` explains why, and the VRAM numbers recorded here
are what make that sequencing decidable rather than hopeful.
