# Open questions

Unresolved as of this scaffold. Do not invent answers to these — if you
resolve one, replace the entry with a decision (and an ADR, if it's
architectural) rather than deleting it silently.

- **A student's first language** is not yet known; likely Arabic, possibly
  Sorani or Kurmanji Kurdish. To be established in lesson 1 (17 September
  2026).
- **First-language reading fluency** is unverified for every user. If
  captions can't be read, Eco's design assumptions (see `eco.md`,
  `overview.md`) change.
- **Whether classroom machines are shared or assigned per student** —
  affects session/login design beyond what
  [ADR 0010](decisions/0010-avatar-picker.md) already settles.
- **Chat model size and quantisation for Play** — affects whether it fits
  alongside Eco's models in the 16 GB VRAM budget (see `architecture.md`).
- **Whether the encoder is worth serving through Triton**, or whether a
  lighter runtime suffices — see `services/encoder/README.md`.
