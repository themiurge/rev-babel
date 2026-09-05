# Roadmap

Sequenced by the course calendar (17 September – 19 November 2026, ten
weekly lessons), not by component.

## Eco first

Eco is needed from lesson 1 (17 September) — students need captions from
the first class. Critically, **Eco depends on neither vLLM nor Triton**,
which is what makes this sequencing workable at all: the models it needs
(voice activity detection, transcription, translation — see `eco.md`) are
comparatively small and can run well within the VRAM budget on their own.

## Play afterwards

Play's chat model is heavier and shares the same GPU. It is scheduled for
week 2 or later in the term (see
[ADR 0006](decisions/0006-dedicated-translation-model.md) for why it is a
separate model from translation, which helps this sequencing rather than
hurts it). Exact model and quantisation: see `open-questions.md`.

## Encoder last

`services/encoder` is a placeholder for later work, not needed for either
Eco or Play as currently designed. Whether it is served through Triton or a
lighter runtime is unresolved — see `open-questions.md`.

## Why this order

Sequencing by calendar rather than by "build the hardest thing first"
matches how the course is actually taught: Eco has to work before there is
a single lesson to use it in, while Play and the encoder have real weeks of
runway. It also keeps the tight VRAM budget manageable by never asking more
than one new, large model to share the card before the previous one is
proven stable.
