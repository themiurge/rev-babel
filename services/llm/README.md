# services/llm

The conversational model behind Play. Not needed until later in the course
— see `ROADMAP.md` for why Eco is sequenced first and does not depend
on this service.

## What belongs here

The chat model serving Play's spoken roleplay conversations.

## What does not belong here

Translation (`services/mt`), transcription (`services/asr`).

Lesson 6's tutor chatbot is **not** served from here: it calls a hosted
API (Anthropic) from `apps/web/src/rev_babel_web/tutor.py`, per
[ADR 0018](../../docs/decisions/0018-lesson-6-tutor-chatbot.md). This
service stays reserved for Play's local model.

## Status

Placeholder, week 2+. Model size and quantisation are not yet decided —
see `docs/open-questions.md`.
