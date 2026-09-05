# Operations

The runbook. As designed; the stack does not exist to run yet — this
records intent so operations documentation grows alongside the system
rather than after it.

## Starting and stopping the stack

TODO: exact commands depend on `infra/compose.yaml`, which is currently an
unfilled stub. In outline: services start inside WSL2 on the teacher's
desktop, the Cloudflare Tunnel exposes the web app, and the whole stack
should come up with a single command once implemented.

## Before a lesson

TODO: a pre-lesson checklist (tunnel reachable, GPU free, phone paired and
charged, avatar claims intact) belongs here once the system exists to
check.

## Known failure modes and fallbacks

- **Home internet down** — the tunnel is unreachable from the classroom.
  TODO: no fallback beyond the teaching assistant delivering the lesson
  without Eco/Play is currently defined.
- **PC rebooted mid-lesson** — TODO: recovery procedure not yet defined.
- **GPU out of memory** — with every model sharing one 16 GB card, this is
  a plausible failure once Play's chat model runs alongside Eco's models.
  TODO: which service is shed first is not yet decided.
- **Phone tab backgrounded** — audio capture stops. A Screen Wake Lock is
  used to keep this from happening during normal use
  ([ADR 0004](decisions/0004-phone-as-microphone.md)); TODO: recovery if it
  happens anyway is not yet defined.

## Graceful degradation

- **Translation failure** (a segment or a language fails to translate):
  that student's caption falls back to Italian-only, rather than showing
  nothing ([ADR 0008](decisions/0008-bilingual-caption-display.md)).
- **Total failure** (Eco or Play unreachable): the student-facing screen
  should show an honest message in the student's own language, rather than
  a frozen or blank screen. TODO: the message content and how it is
  translated when the translation service itself is what's down is not yet
  decided.
- **Any system failure during a lesson**: the teaching assistant can
  translate live as a human fallback. This is a deliberate design point,
  not an afterthought — the system is allowed to fail without stopping the
  lesson.
