# rev-babel Roadmap

The durable **savepoint** — where the project is right now and how we mean
to get there. Certainty **tapers outward**: the next few days are concrete,
the far end of the course is deliberately rough. Maintained per
[ADR 0011](docs/decisions/0011-roadmap-savepoint.md). Its git history is
its versioning.

## Start here

You are picking up rev-babel. In three lines: it is a self-hosted teaching
aid for one computer-literacy course for adult migrant women in Bologna,
running on the teacher's desktop and reached from the classroom over the
internet; **Eco** captions the lesson live in each student's language,
**Play** is spoken roleplay practice for later in the term. This repository
is public and the users are vulnerable — read
[`docs/data-and-privacy.md`](docs/data-and-privacy.md) before touching
anything.

Read this file, then reach for the rest as needed:
[`docs/README.md`](docs/README.md) (the system as designed) ·
[`plans/README.md`](plans/README.md) (how it gets built, milestone by
milestone) · [`docs/issues/`](docs/issues/README.md) (the atomic backlog) ·
[`docs/decisions/`](docs/decisions/README.md) (why it looks like this) ·
[`scratchpad/`](scratchpad/README.md) (verified blueprints).
**This file plus those is enough to resume.**

## Vision

Five students who cannot follow spoken Italian at teaching pace get the
lesson, live, in their own language and in Italian side by side — on
hardware the teacher already owns, holding no photograph and no name, and
degrading to "the teaching assistant translates" rather than to a blank
screen. Ten lessons, six users, and then it stops. It is not a product and
does not scale past this room; see
[`docs/overview.md`](docs/overview.md).

## Where we are now  *(2026-09-06)*

**Twelve days before lesson 1** (Thursday 17 September 2026). Ten lessons,
Thursdays 16:30–18:00, through 19 November.

- **The network layer is done and proved, ahead of everything else.**
  `emiliovicari.com` registered at Cloudflare Registrar; a
  dashboard-managed tunnel routes `rev-babel.emiliovicari.com` (students)
  and `mic.emiliovicari.com` (the teacher's capture page) to
  `http://127.0.0.1:8000`. Verified live from outside the house, not
  assumed: HTTPS on both names, `Host` header intact so one app on one port
  can separate the two roles, `CF-Connecting-IP` preserved, and — the
  result that could have sunk the design — **WebSockets open and hold
  through the tunnel**. Recurring cost is the domain alone, ~$10.44/year;
  tunnel, DNS, TLS and Zero Trust Access under fifty users are free.
- **A phone browser can capture and stream audio, end to end.** 500 ms
  chunks over `wss://` with a Screen Wake Lock held, token-gated at the
  handshake. The phone produces **WebM/Opus, 48 kHz mono, ~32 kbps** — one
  clean ffmpeg path for the decode step. From cellular data in *poor*
  reception: round trip median 250 ms, max 650 ms, no drops. Against a
  budget that already accepts 2–3 s
  ([ADR 0005](docs/decisions/0005-segment-level-transcription.md)) the
  phone leg is noise, not a component. Blueprints in
  [`scratchpad/`](scratchpad/README.md); measurements in
  [`plans/m4-network.md`](plans/m4-network.md).
- **Real speech pauses every 3–4 seconds.** Measured on 51 s of the
  maintainer's own audio through the real path. This is direct evidence
  *against* the main risk flagged for milestone 2 — that teaching pace
  would defeat voice-activity segmentation — and suggests segments will
  land comfortably inside the 15 s cap. Not yet confirmed at teaching pace
  with an audience, which is a different thing from reading aloud.
- **Eco's first piece exists: the segment/caption contract.** `Segment` and
  `Caption` are real pydantic v2 models in `packages/contracts` now, not a
  placeholder — a JSON Lines codec and stream validators enforcing gapless,
  in-order `seq` and the 15 s segment cap, 30 tests passing. `services/asr`,
  `services/mt`, `services/llm`, `services/encoder` and `apps/web` are
  otherwise still placeholders. No model has been downloaded, no segment
  has been transcribed, no word has been translated. The tunnel currently
  answers only when something is put behind it by hand.
- **Twelve decisions recorded**, of which one is superseded:
  [ADR 0010](docs/decisions/0010-avatar-picker.md) replaced login
  photographs with a preset avatar collection claimed on first use, which
  removed the only category of personal data the system held. A user row is
  an id, an avatar id and a language preference — no name, no photograph.
- **Two privacy TODOs are still open** and both are load-bearing: how long
  Eco transcripts are kept (issue 0013) and whether lesson history is
  stored at all (issue 0018). Neither can stay open once the pipeline runs.
- **The capture host is currently unprotected** (issue 0001). Found live
  the same evening. Harmless today because nothing is behind it; not
  harmless the moment it opens a microphone.

## Dependency map

```
contract (0005) ──▶ translation (0007) ──┐
                                          ├──▶ live pipeline (0012) ──▶ capture page (0014)
VAD (0009) ──▶ transcription (0010) ─────┘                    │              │
                                                               ▼              ▼
                                              caption delivery (0015) ──▶ lesson 1
avatars (0016) ──needs-human──▶ claim flow (0017) ──▶ history (0018)   [after lesson 1]
classroom network (0002) ──needs-onsite──▶ any confidence at all
```

Edge types: `needs-human` (only Emilio can do it — an account, a purchase,
a room, a judgement) · `needs-onsite` (must happen in the classroom) ·
`needs-model` (a model must be chosen and measured first) · plain arrows
are ordinary code dependencies.

## Now — in flight  *(priority order — start at the top)*

- 🧑 **[0002](docs/issues/0002-test-the-classroom-network.md) Test the
  classroom network.** The only part of the path untestable from home, and
  the one that would break everything on the day. Wants doing the week
  before, not the morning of. `scratchpad/tunnel_smoke_server.py` does it
  without any of Eco existing.
- ✅ ~~[0005](docs/issues/0005-segment-and-caption-contract.md) The segment
  and caption contract~~ — done 2026-09-06.
- 💻 **[0006](docs/issues/0006-the-invented-classroom-corpus.md) The
  invented classroom corpus.** Milestone 1's highest-value artefact: real
  transcripts can never be used, and public benchmarks look nothing like a
  lesson.
- 💻 **[0007](docs/issues/0007-choose-the-translation-model.md) Choose the
  translation model**, with
  **[0008](docs/issues/0008-check-coverage-for-sorani-and-kurmanji.md)**
  run alongside so that either answer in lesson 1 is survivable.
- 🧑 **[0001](docs/issues/0001-protect-the-capture-host.md) Protect the
  capture host.** Cheap, and it stops being optional the moment issue 0014
  lands.
- 🧑 **[0003](docs/issues/0003-lavalier-pairing-pickup-and-90-minutes.md)
  The lavalier**, which is also the speaker gate (issue 0011). Its pickup
  pattern is a privacy control, not just an audio quality question.

## Next — near-term

- 💻 [0009](docs/issues/0009-segment-audio-on-voice-activity-pauses.md) and
  [0010](docs/issues/0010-choose-the-transcription-model.md) — milestone 2.
  The 3–4 second pause cadence measured on 5 September is the starting
  point for tuning.
- 💻 [0012](docs/issues/0012-the-live-pipeline.md) — milestone 3, where Eco
  first exists as a system rather than two programs.
- 🧑 [0013](docs/issues/0013-decide-eco-transcript-retention.md) — forced by
  0012: the moment the pipeline runs live it produces a transcript.
- 💻 [0014](docs/issues/0014-build-the-capture-page-for-real.md) and
  [0015](docs/issues/0015-caption-delivery-and-fan-out.md) — the cut line
  for lesson 1.
- 🧑 [0004](docs/issues/0004-keep-the-stack-up-across-a-reboot.md) — before
  the dress rehearsal, not after.

## Horizon — later  *(rough; refine as we approach)*

- The full picker: avatars ([0016](docs/issues/0016-draw-the-avatars.md)),
  claim flow and language preference
  ([0017](docs/issues/0017-avatar-claim-flow-and-language-preference.md)),
  history ([0018](docs/issues/0018-decide-lesson-history-and-retention.md))
  — weeks 2–4, not lesson 1.
- [0019](docs/issues/0019-make-the-stack-operable.md) — supervision, the
  runbook's open TODOs, the VRAM budget written down with real numbers, and
  a dress rehearsal with deliberate failures injected.
- **Play** (`services/llm`) — week 2 or later. Heavier, shares the same
  card, and needs Eco's measured VRAM footprint before its own size can be
  chosen. See [`docs/play.md`](docs/play.md). The sequencing works at all
  because **Eco depends on neither vLLM nor Triton**: its models are small
  enough to run inside the budget alone, so no second large model has to
  share the card before the first is proven stable.
- `services/encoder` — last, and possibly never; whether it is served at
  all is unresolved.
- Retuning after lesson 1 against what actually happens: pause cadence at
  teaching pace, whether captions are read at all
  ([0021](docs/issues/0021-verify-first-language-reading-fluency.md)),
  whether the room is audible on the lavalier.

## External & on-site  *(🧑 Emilio — nobody else can do these)*

Lead times and physical presence, which is why they are listed apart.

- **Done:** domain registered, tunnel created and routed, both hostnames
  live, phone capture proven from cellular.
- **The classroom**, once: network test (0002), whether machines are shared
  or per-student (0022), and what the room does to a lavalier (0003).
- **The hardware**: lavalier pairing and battery over 90 minutes, the phone
  on power, the desktop not sleeping (0004).
- **The avatars** (0016), drawn outside this repository — needed for week
  2, not for lesson 1.
- **Two privacy calls** that are the maintainer's alone: transcript
  retention (0013) and lesson history (0018).
- **Lesson 1 itself** answers three questions nothing else can: the
  students' first languages (0020), whether captions can be read (0021),
  and what the room is actually like (0022).

## Operating rules  *(mirror of [ADR 0011](docs/decisions/0011-roadmap-savepoint.md) — that record is the authority)*

- **This file is a whiteboard, not a contract.** Bookkeeping — status,
  reordering within decided strategy, refreshing "where we are" — is an
  ordinary commit. Anything that *decides* something load-bearing goes into
  [`docs/decisions/`](docs/decisions/README.md) first; this file only
  reflects it.
- **Session-end ritual.** Every working session closes by refreshing
  **Where we are now** and adding a **revision log** entry. A session that
  changed nothing still says so.
- **Honest status only.** Record what was verified and how, and keep the
  distinction between "configured" and "confirmed working" visible. A
  measurement taken under bad conditions is worth more than an optimistic
  one, and gets kept as the baseline.
- **Issues are files** ([`docs/issues/`](docs/issues/README.md)), numbered
  sequentially, never renumbered. Closing one updates this file in the same
  commit.
- **The cut line governs when time is short.** If a milestone slips, ship
  what lesson 1 needs and say plainly what was left out — see
  [`plans/README.md`](plans/README.md).

## Revision log

- **v0.2 — 2026-09-06** — Closed issue 0005: `Segment` and `Caption` land in
  `packages/contracts` as pydantic v2 models, with a JSON Lines codec and
  stream validators for gapless/in-order `seq` and the 15 s segment cap.
  Recorded as [ADR 0012](docs/decisions/0012-segment-and-caption-contract.md).
  Milestone 1's next item is issue 0006, the invented classroom corpus.
- **v0.1 — 2026-09-05** — Initial savepoint. Adopts the roadmap convention
  from a sibling project of the maintainer's per ADR 0011, with issues as
  markdown files rather than a tracker and no autonomous implementing
  agents. Seeded current
  state: scaffolding and eleven ADRs in place; the six-milestone plan
  written; the network layer built and verified live (tunnel, both
  hostnames, WebSockets, phone capture from cellular); Eco itself entirely
  unbuilt. Twenty-two issues filed, five of them in flight.
