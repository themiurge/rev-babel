# services/mt

Translation of Eco's transcribed segments into each student's language, run
as a model dedicated to this purpose rather than shared with Play's chat
model — see
[ADR 0006](../../docs/decisions/0006-dedicated-translation-model.md).

## What belongs here

Translation from Italian (and English) into each distinct student language
present in a lesson.

## What does not belong here

Transcription (`services/asr`), chat generation for Play (`services/llm`).

## Status

Placeholder. No model is loaded, no translation runs yet.
