# rev-babel

A self-hosted teaching aid built for a single computer-literacy course for
adult migrant women in Bologna, Italy. It runs on the teacher's home desktop
and is reached from the classroom over the internet. It is purpose-built for
this one course, not a general-purpose product.

## Modules

- **Eco** — while the teacher speaks, each student's screen shows the Italian
  transcript with a translation into her own language underneath, in
  near-real-time.
- **Play** — students practise real-life situations in spoken conversation
  with a language model.

## Status

Scaffolding only. The network layer is built and verified; Eco itself is
not. [`ROADMAP.md`](ROADMAP.md) is the savepoint — where the project is
right now, what is in flight, and what is next.

## Repository layout

```
rev-babel/
├── apps/web/           FastAPI app: pages, sessions, WebSocket fan-out
├── services/asr/       voice activity detection, speaker gate, transcription
├── services/mt/        translation
├── services/llm/       chat model for Play (placeholder, week 2+)
├── services/encoder/   placeholder, later
├── packages/contracts/ shared data shapes passed between services
├── infra/              deployment configuration (compose, tunnel)
├── scripts/            operational scripts
├── plans/              implementation plans — start at plans/README.md
├── scratchpad/         verified blueprints from throwaway experiments
├── docs/               documentation — start at docs/README.md
│   ├── decisions/      architecture decision records
│   └── issues/         the atomic backlog, one file per issue
└── ROADMAP.md          the savepoint — where the project is right now
```

## Getting started

Nothing runs yet. Once services are implemented:

```sh
make install   # uv sync
make lint      # ruff check
make test      # pytest
```

## Documentation

Start at [`ROADMAP.md`](ROADMAP.md) if you are resuming after a gap: it
says where the project is right now, what is in flight and what is next.
Otherwise start at [`docs/README.md`](docs/README.md) — in particular
[`docs/overview.md`](docs/overview.md) for the teaching context and
[`docs/data-and-privacy.md`](docs/data-and-privacy.md) for what this
repository must never contain.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
