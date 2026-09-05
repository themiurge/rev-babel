# services/asr

Voice activity detection, a speaker gate limiting transcription to the
teacher's voice, and transcription of Italian and English speech into
timestamped segments. See `docs/eco.md` for the pipeline this fits into and
[ADR 0005](../../docs/decisions/0005-segment-level-transcription.md) for
why segments are committed on a voice-activity pause rather than streamed.

## What belongs here

Voice activity detection, speaker gating, transcription (e.g. Whisper),
and language identification between Italian and English.

## What does not belong here

Translation (`services/mt`), the web app's session/WebSocket handling
(`apps/web`), and anything related to Play (`services/llm`).

## Status

Placeholder. No model is loaded, no pipeline runs yet.
