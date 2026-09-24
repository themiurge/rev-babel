# Open questions

Unresolved as of this scaffold. Do not invent answers to these — if you
resolve one, replace the entry with a decision (and an ADR, if it's
architectural) rather than deleting it silently.

- **A student's first language** is still not confirmed. Lesson 1 (17
  September 2026) established a *second*-language / support-language
  preference for the three named students — English, Kurdish (assumed
  Sorani, `ckb`), French — recorded in ADR 0015 and issue 0020, but
  whether that equals each student's native tongue is still open, as is
  the Kurdish variant itself (issue 0008).
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
