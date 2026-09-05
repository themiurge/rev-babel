# data

Gitignored. Runtime and local data live here and are never committed: any
cached audio buffers, model weights, evaluation corpora, per-lesson
runtime state, and `recordings/` — test audio of the maintainer's own
voice, which seeds the read-aloud evaluation corpus that `plans/` calls
for. No student is ever recorded. Avatar art is not personal data and does not live here —
see [ADR 0010](../docs/decisions/0010-avatar-picker.md).

See `docs/data-and-privacy.md` for what is and is not retained, and for how
long.

This README and `.gitkeep` are the only files from this directory ever
tracked in version control — everything else here is excluded by
`.gitignore`.
