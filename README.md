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

Scaffolding only. Nothing runs yet — see [`docs/roadmap.md`](docs/roadmap.md)
for the build sequence and [`plans/README.md`](plans/README.md) for the
milestone-by-milestone implementation plan.

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
└── docs/               documentation — start at docs/README.md
```

## Getting started

Nothing runs yet. Once services are implemented:

```sh
make install   # uv sync
make lint      # ruff check
make test      # pytest
```

## Documentation

Start at [`docs/README.md`](docs/README.md) — in particular
[`docs/overview.md`](docs/overview.md) for the teaching context and
[`docs/data-and-privacy.md`](docs/data-and-privacy.md) for what this
repository must never contain.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
